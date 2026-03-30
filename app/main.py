"""
AI Lead Qualification Agent - FastAPI Backend
Uses OpenRouter for AI-powered lead scoring and outreach generation.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = os.getenv("MODEL", "anthropic/claude-3-haiku")

# Database setup
DB_PATH = Path(__file__).parent / "leads.db"


def get_db():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db_cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            company TEXT,
            website TEXT,
            industry TEXT,
            notes TEXT,
            score TEXT,
            confidence TEXT,
            reasoning TEXT,
            outreach_message TEXT,
            website_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)


def scrape_website_text(url: str) -> str:
    """Scrape text content from a website for lead enrichment."""
    if not url:
        return ""

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())

        return text[:3000]  # keep it short for model input
    except Exception:
        return ""


app = FastAPI(title="AI Lead Qualification Agent")

# Mount static files and templates
BASE_DIR = Path(__file__).parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class Lead(BaseModel):
    name: str
    company: str
    website: str = ""
    industry: str = ""
    notes: str = ""


class LeadResponse(BaseModel):
    id: int
    name: str
    company: str
    website: str | None
    industry: str | None
    notes: str | None
    score: str | None
    confidence: str | None
    reasoning: str | None
    outreach_message: str | None
    website_summary: str | None
    created_at: str


def summarize_website(website_text: str) -> str:
    """Summarize raw website text into key business info for lead scoring."""
    if not website_text:
        return "No website summary available."

    summary_prompt = f"""Summarize this company in 3-4 short lines based on the website content.

Focus on:
- what the company does
- who it serves
- signs of growth or scale
- whether it may benefit from automation or AI

Return plain text only.

Website content:
{website_text}
"""

    try:
        summary_response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=[
                {"role": "user", "content": summary_prompt}
            ]
        )
        website_summary = summary_response.choices[0].message.content.strip()
        return website_summary if website_summary else "No website summary available."
    except Exception:
        return "No website summary available."


def qualify_lead_with_ai(name: str, company: str, website: str, website_summary: str, industry: str, notes: str) -> dict:
    """
    Use AI to qualify a lead and generate personalized outreach.
    Returns score, reasoning, and outreach message.
    """
    qualification_prompt = f"""You are a B2B sales lead qualification expert.

Score the lead based on:
1. Industry demand
2. Implied business size
3. Likelihood they need automation or AI
4. Buying intent signals from the notes and website summary

Return ONLY valid JSON in this format:
{{
  "score": "HOT | WARM | COLD",
  "confidence": "HIGH | MEDIUM | LOW",
  "reasoning": "2-3 short sentences, sharp and business-focused",
  "outreach_message": "1-2 short sentences, personalized and persuasive"
}}

Scoring rules:
- HOT = strong fit, likely to benefit now, signs of urgency or active growth
- WARM = decent fit, some need, but unclear urgency or budget
- COLD = weak fit, low need, or not enough buying signals

Confidence rules:
- HIGH = strong website + notes signal
- MEDIUM = some signal but missing clarity
- LOW = weak or incomplete data

Lead details:
Name: {name}
Company: {company}
Website: {website}
Industry: {industry}
Notes: {notes}

Website summary:
{website_summary}
"""

    try:
        chat_completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert sales lead qualification assistant. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": qualification_prompt
                }
            ],
            temperature=0.3,
            max_tokens=300,
        )

        import json
        response_text = chat_completion.choices[0].message.content.strip()

        # Clean up potential markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        elif response_text.startswith("```json"):
            response_text = response_text[7:]

        result = json.loads(response_text.strip())

        score = result.get("score", "COLD").upper().strip()
        confidence = result.get("confidence", "MEDIUM").upper().strip()

        if score not in ["HOT", "WARM", "COLD"]:
            score = "COLD"
        if confidence not in ["HIGH", "MEDIUM", "LOW"]:
            confidence = "MEDIUM"

        result["score"] = score
        result["confidence"] = confidence

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI qualification failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main page."""
    with open(BASE_DIR / "templates" / "index.html", "r") as f:
        return f.read()


@app.post("/lead/qualify")
async def qualify_lead(lead: Lead):
    """
    Qualify a lead using AI.
    Returns the qualification result and saves to database.
    """
    if not lead.name.strip() or not lead.company.strip():
        raise HTTPException(status_code=400, detail="Name and company are required")

    website_text = scrape_website_text(lead.website)
    website_summary = summarize_website(website_text)

    # Get AI qualification
    ai_result = qualify_lead_with_ai(lead.name, lead.company, lead.website, website_summary, lead.industry, lead.notes)

    # Save to database
    with get_db_cursor() as cursor:
        cursor.execute("""
        INSERT INTO leads (
            name, company, website, industry, notes,
            score, confidence, reasoning, outreach_message, website_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.name,
            lead.company,
            lead.website,
            lead.industry,
            lead.notes,
            ai_result["score"],
            ai_result.get("confidence", "MEDIUM"),
            ai_result["reasoning"],
            ai_result["outreach_message"],
            website_summary
        ))
        lead_id = cursor.lastrowid

    return {
        "score": ai_result["score"],
        "confidence": ai_result.get("confidence", "MEDIUM"),
        "reasoning": ai_result["reasoning"],
        "outreach_message": ai_result["outreach_message"],
        "website_summary": website_summary
    }


@app.get("/leads", response_model=list[LeadResponse])
async def get_leads():
    """Get all leads from the database."""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, company, website, industry, notes, score, confidence, reasoning, outreach_message, website_summary, created_at
            FROM leads
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

    return [
        LeadResponse(
            id=row["id"],
            name=row["name"],
            company=row["company"],
            website=row["website"],
            industry=row["industry"],
            notes=row["notes"],
            score=row["score"],
            confidence=row["confidence"],
            reasoning=row["reasoning"],
            outreach_message=row["outreach_message"],
            website_summary=row["website_summary"],
            created_at=row["created_at"]
        )
        for row in rows
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
