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

class RewriteRequest(BaseModel):
    original_content: str
    primary_keyword: str
    secondary_keyword: str = None  # Optional

class RewriteResponse(BaseModel):
    rewritten_content: str
    meta_title: str
    meta_description: str
    url_slug_suggestion: str
    seo_score: int
    optimization_suggestions: list[str]

@router.post("/rewrite-content", response_model=RewriteResponse)
def rewrite_content(data: RewriteRequest):
    try:
        prompt = f"""
You are an expert SEO content strategist and copywriter. Rewrite the following content to be fully SEO-optimised while preserving its original tone.

✅ Use British English  
✅ Optimise for the PRIMARY keyword: "{data.primary_keyword}"
{"✅ Include the SECONDARY keyword: " + data.secondary_keyword if data.secondary_keyword else ""}
✅ Maintain ~3% primary keyword density  
✅ Structure content with appropriate headings (H1, H2, H3) using keywords where relevant  
✅ Improve readability with short paragraphs, lists, and formatting  
✅ Ensure the content is thorough, addresses user intent, and covers the topic in depth  
✅ Incorporate E-E-A-T principles: demonstrate expertise, cite trusted sources, and enhance credibility  
✅ Do NOT generate placeholder images, but assume the user may insert them later  
✅ Do NOT include commentary outside the JSON response

Once rewritten, provide a response in this **strict JSON format** only:

{{
  "rewritten_content": "...",  // Markdown-formatted
  "meta_title": "...",         // Max 60 characters
  "meta_description": "...",   // Max 155 characters
  "url_slug_suggestion": "...", // Based on the primary keyword
  "seo_score": 0-100,           // Estimate of SEO strength
  "optimization_suggestions": [ // Only if score < 100
    "Add 2 relevant images with alt text.",
    "Include links to authoritative sources."
  ]
}}

OR leave suggestions empty if score is 100.
Content:
\"\"\"
{data.original_content}
\"\"\"
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert SEO writer and strategist. Return only valid JSON. No intro text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5
        )

        raw = response.choices[0].message.content.strip()

        # Extract JSON block from response
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("OpenAI did not return valid JSON.")

        result = json.loads(json_match.group(0))

        return RewriteResponse(
            rewritten_content=result["rewritten_content"],
            meta_title=result["meta_title"],
            meta_description=result["meta_description"],
            url_slug_suggestion=result["url_slug_suggestion"],
            seo_score=result["seo_score"],
            optimization_suggestions=result["optimization_suggestions"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
