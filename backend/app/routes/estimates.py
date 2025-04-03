from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai
import json
import re

load_dotenv(dotenv_path="./backend/.env")


client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()

class KeywordEstimateRequest(BaseModel):
    keywords: list[str]
    location: str  # Required

class KeywordEstimate(BaseModel):
    keyword: str
    volume: str
    competition: str
    intent: str

@router.post("/keyword-estimates", response_model=list[KeywordEstimate])
def estimate_keywords(data: KeywordEstimateRequest):
    try:
        keyword_list = "\n".join(f"- {kw}" for kw in data.keywords)

        prompt = f"""
You are an SEO keyword analyst with access to public search trends, industry data, and geo-specific behaviour patterns.

Please provide **estimated keyword data for the following location**: {data.location}

For each keyword below, return:
- Monthly Search Volume Range (e.g. "100–1,000")
- Competition Level (low, medium, high)
- Search Intent Type (informational, transactional, commercial, navigational)

Only use the exact keywords provided. Return strict valid JSON in this format:

[
  {{
    "keyword": "...",
    "volume": "...",
    "competition": "...",
    "intent": "..."
  }},
  ...
]

Keywords:
{keyword_list}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise SEO keyword analyst. Return only valid JSON with no commentary."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        raw = response.choices[0].message.content.strip()
        json_match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not json_match:
            raise ValueError("OpenAI response did not contain valid JSON.")

        return json.loads(json_match.group(0))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
