"""
llm_client.py
─────────────────────────────────────────────────────────────
Groq API wrapper for the BuildingPath navigation system.

Reads GROQ_API_KEY from environment.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()  # .env dosyasını otomatik yükler


class LLMClient:
    def __init__(self, api_key: str = None,
                 model: str = "llama-3.3-70b-versatile"):
        self.model  = model
        self.client = Groq(api_key=api_key or os.environ["GROQ_API_KEY"])

    def chat(self, messages: list,
             temperature: float = 0.1,
             max_tokens: int = 512) -> str:
        """Send a chat request and return the response text."""
        response = self.client.chat.completions.create(
            model       = self.model,
            messages    = messages,
            temperature = temperature,
            max_tokens  = max_tokens,
        )
        return response.choices[0].message.content.strip()

    def json_chat(self, messages: list,
                  temperature: float = 0.1,
                  max_tokens: int = 256) -> dict:
        """
        Send a chat request expecting a JSON response.
        Strips markdown fences and parses. Returns {} on failure.
        """
        raw = self.chat(messages, temperature, max_tokens)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
