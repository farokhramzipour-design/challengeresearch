from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


EXTRACTION_PROMPT = """
You are an information extraction model. From the provided page text, extract DISTINCT trade challenges relevant to the UK and/or EU. Output ONLY JSON.

Rules:
- Only include challenges supported by the text. Do not guess.
- Each challenge must clearly connect to UK/EU trade (direct or indirect).
- Provide 1-3 short evidence quotes (<=25 words each) from the text that support the challenge.
- Do not include personal data.
- If the text is not about trade challenges, return {"items":[]}.

Output JSON format:
{
  "items":[
    {
      "title":"...",
      "summary":"2-4 neutral sentences",
      "challenge_type":"Regulatory|Logistics|Geopolitics|Tariffs|Sanctions|Customs|FX/Payments|Energy|SupplyChain|ESG/CBAM|Tech/ExportControls|Labor|Maritime|Insurance|Other",
      "impact_area":["imports","exports","transit","services_trade","manufacturing"],
      "severity":"low|medium|high",
      "time_horizon":"now|0-3m|3-12m|12m+",
      "uk_relevance":"direct|indirect",
      "eu_relevance":"direct|indirect",
      "affected_sectors":["automotive","agri-food","steel","chemicals","pharma","electronics","energy","shipping","retail","other"],
      "evidence_quotes":["...","..."],
      "confidence":0.0
    }
  ]
}

Context metadata:
- URL: {{URL}}
- Title: {{TITLE}}
- Published_at: {{PUBLISHED_AT_OR_NULL}}

TEXT START
{{ARTICLE_TEXT}}
TEXT END
""".strip()


SYNTHESIS_PROMPT = """
You are a synthesis model. You receive many extracted challenge candidates from multiple sources. Your job is to:
- Merge duplicates and near-duplicates.
- Keep 10-25 distinct challenges.
- For each item, attach the best 1-3 evidence sources (source_name, url, published_at, quote <=25 words).
- Ensure each item is UK/EU relevant.
- Do not invent facts or dates.
- Output ONLY valid JSON in the schema below. No markdown.

Schema:
{
  "run_id":"<iso8601>",
  "scope":{"regions":["UK","EU"],"topic":"global trade challenges","languages":["en"]},
  "items":[
    {
      "title":"<short>",
      "summary":"<2-4 sentences>",
      "challenge_type":"Regulatory|Logistics|Geopolitics|Tariffs|Sanctions|Customs|FX/Payments|Energy|SupplyChain|ESG/CBAM|Tech/ExportControls|Labor|Maritime|Insurance|Other",
      "impact_area":["imports","exports","transit","services_trade","manufacturing"],
      "severity":"low|medium|high",
      "time_horizon":"now|0-3m|3-12m|12m+",
      "uk_relevance":"direct|indirect",
      "eu_relevance":"direct|indirect",
      "affected_sectors":["automotive","agri-food","steel","chemicals","pharma","electronics","energy","shipping","retail","other"],
      "evidence":[
        {"source_name":"...","url":"...","published_at":"YYYY-MM-DD or null","quote":"<=25 words","credibility":"high|medium|low"}
      ],
      "confidence":0.0,
      "dedupe_key":"<stable>"
    }
  ],
  "stats":{"found":0,"kept":0,"duplicates_removed":0}
}

Input candidates JSON:
{{CANDIDATES_JSON}}
""".strip()


class OpenAIClient:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=settings.openai_api_key)

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "output_text"):
            return response.output_text
        try:
            return response.output[0].content[0].text
        except Exception:
            try:
                return response.choices[0].message.content
            except Exception:
                return ""

    def _create_response(self, prompt: str) -> Any:
        if hasattr(self.client, "responses"):
            return self.client.responses.create(
                model=settings.openai_model,
                input=prompt,
                temperature=0,
            )
        return self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
    def extract_candidates(self, text: str, url: str, title: str, published_at: Optional[str]) -> Dict[str, Any]:
        prompt = EXTRACTION_PROMPT.replace("{{URL}}", url).replace("{{TITLE}}", title).replace(
            "{{PUBLISHED_AT_OR_NULL}}", published_at or "null"
        ).replace("{{ARTICLE_TEXT}}", text)

        response = self._create_response(prompt)
        raw = self._extract_text(response)
        return self._load_json(raw)

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
    def synthesize(self, candidates_json: Dict[str, Any]) -> Dict[str, Any]:
        prompt = SYNTHESIS_PROMPT.replace("{{CANDIDATES_JSON}}", json.dumps(candidates_json, ensure_ascii=True))
        response = self._create_response(prompt)
        raw = self._extract_text(response)
        return self._load_json(raw)

    @retry(stop=stop_after_attempt(settings.max_retries), wait=wait_exponential(min=1, max=10))
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def _load_json(self, raw: str) -> Dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            fix_prompt = f"Return ONLY valid JSON. Fix this:\n{raw}"
            response = self._create_response(fix_prompt)
            return json.loads(self._extract_text(response))
