"""
query_parser.py
─────────────────────────────────────────────────────────────
LLM-powered natural language parser for navigation queries.

Extracts from free-text input:
  - destination : what the user wants to find
  - profile     : accessibility profile
  - floor       : specific floor (index 0-5), or null
  - language    : "tr" or "en"
"""

from dataclasses import dataclass
from typing import Optional
from .llm_client import LLMClient


SYSTEM_PROMPT = """\
You are a BuildingPath indoor navigation assistant.
Your job is to extract structured information from a user's navigation query.

If the conversation history is provided, use it to resolve any pronoun or vague reference
in the current query (e.g. "bu" / "this", "o" / "that", "orası" / "there", "bu yer", "bu lab").
Always return the fully resolved place name — never a pronoun.

The building has 6 floors (index 0-5):
  0 = Lower Ground, 1 = Ground, 2 = First, 3 = Second, 4 = Third, 5 = Fourth

Extract the following and return ONLY a valid JSON object, no explanation:

{
  "destination": "<fully resolved place name — no pronouns>",
  "profile": "<standard | wheelchair | mobility>",
  "floor": <floor index 0-5, or null if not specified>,
  "language": "<tr | en>"
}

Rules:
- destination: Resolve pronouns using history. If query says "bu lab" and history shows "bilgisayar lab",
  destination must be "bilgisayar laboratuvarı". If no pronoun, extract the place as stated.
  Examples: "Prof. Whitfield ofisi", "büyük amfi", "en yakın tuvalet", "bilgisayar laboratuvarı"
- profile:
    "min_effort" if user mentions effort, fatigue, stairs difficulty, az efor, yorgunluk, merdiven zorluğu
    "standard"   otherwise (default)
- floor: only set if user explicitly mentions a floor (e.g. "2. katta", "ground floor", "first floor")
  Use the index (0-5), not the name.
- language: "tr" if query is in Turkish, "en" if in English

Return ONLY the JSON. No markdown, no explanation."""


@dataclass
class ParsedQuery:
    destination : str
    profile     : str           # "standard" | "wheelchair" | "mobility"
    floor       : Optional[int] # floor index or None
    language    : str           # "tr" | "en"
    raw_query   : str


class QueryParser:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def parse(self, query: str, history: list = None) -> ParsedQuery:
        """
        Parse a free-text navigation query.
        history: previous [{role, content}] turns — used to resolve pronoun references.
        Falls back to safe defaults if LLM fails.
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            # Include previous turns (exclude last item = current query) for context
            messages.extend(history[:-1])
        messages.append({"role": "user", "content": query})

        data = self.llm.json_chat(messages)

        return ParsedQuery(
            destination = data.get("destination", query),
            profile     = data.get("profile", "standard"),
            floor       = data.get("floor"),
            language    = data.get("language", "tr"),
            raw_query   = query,
        )
