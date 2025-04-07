# app/routes/analyze.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv
import json
import re
import requests

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()

class AnalyzeRequest(BaseModel):
    content: str
    location: str

class AnalyzeResponse(BaseModel):
    intent: str
    primary_keywords: list[str]
    secondary_keywords: list[str]
    seo_score: int
    initial_optimization_suggestions: list[str]
    keyword_data: list[dict]

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_content(data: AnalyzeRequest):
    try:
        prompt = f"""
You are an expert SEO specialist and content strategist with over 10 years of experience. You are also an experienced copywriter who understands how to influence human decision-making through emotion, storytelling, and persuasive language.

Your task is to analyze the provided content and determine:
- What type of content it is (e.g., blog post, product page, service landing page, etc.)
- The primary topic and themes of the content
- The most relevant and strategic keywords the content should target to rank well in search engines

Note:
- The keywords do *not* need to appear in the content. Use your expertise to infer the best terms based on search intent, content context, and what the ideal user would be searching for.
- Think like an SEO specialist and a search engine—evaluate both topical relevance and user intent.

Return your analysis in **strict, valid JSON only**. Do not add any commentary. Format:

{{
  "intent": "informational" | "transactional" | "commercial" | "navigational",
  "primary_keywords": ["...", "...", "...", "...", "..."],
  "secondary_keywords": ["...", "...", "...", "...", "..."],
  "seo_score": 0-100,
  "initial_optimization_suggestions": ["..."]
}}

Content:
\"\"\"
{data.content}
\"\"\"
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a helpful SEO tool. Respond ONLY in strict JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        raw = response.choices[0].message.content.strip()
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("Invalid JSON from OpenAI")

        result = json.loads(json_match.group(0))
        keywords = result["primary_keywords"] + result["secondary_keywords"]

        # Get keyword estimates
        estimate_res = requests.post(
            "http://localhost:8000/keyword-estimates",
            json={"keywords": keywords, "location": data.location}
        )

        if estimate_res.status_code != 200:
            raise ValueError("Keyword estimate API failed")

        keyword_data = estimate_res.json()

        return {
            **result,
            "keyword_data": keyword_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
