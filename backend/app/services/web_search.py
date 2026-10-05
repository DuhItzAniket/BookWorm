from __future__ import annotations
import httpx
from app.core.config import settings
from app.services.pdf_service import _strip_html
from app.services.qa_service import Passage


def search_web(question: str) -> list[Passage]:
    if not settings.brave_search_api_key:
        raise RuntimeError("Web search is not configured. Set BRAVE_SEARCH_API_KEY on the backend.")
    with httpx.Client(timeout=15) as client:
        response = client.get("https://api.search.brave.com/res/v1/web/search",
                              params={"q": question, "count": 5, "extra_snippets": "true"},
                              headers={"X-Subscription-Token": settings.brave_search_api_key})
        response.raise_for_status()
    passages = []
    for item in response.json().get("web", {}).get("results", [])[:5]:
        url = item.get("url", "")
        if not url.startswith(("https://", "http://")):
            continue
        snippets = list(dict.fromkeys([item.get("description", ""), *item.get("extra_snippets", [])]))
        text = _strip_html(" ".join(snippets))[:6000]
        if text:
            passages.append(Passage(text, title=item.get("title", url), url=url))
    return passages
