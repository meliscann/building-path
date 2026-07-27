"""
route_formatter.py
─────────────────────────────────────────────────────────────
LLM-powered route description formatter.

Takes route segments and duration, returns a natural language
description in the user's language.
"""

from .llm_client import LLMClient

FLOOR_NAMES = {
    0: ("Lower Ground", "Alt Zemin"),
    1: ("Ground",       "Zemin"),
    2: ("First",        "Birinci"),
    3: ("Second",       "İkinci"),
    4: ("Third",        "Üçüncü"),
    5: ("Fourth",       "Dördüncü"),
}

TRANSITION_LABELS = {
    "elevator": ("elevator", "asansör"),
    "stair":    ("stairs",   "merdiven"),
    "lift":     ("accessible lift", "engelli lifti"),
}


def segments_to_text(segments: list, language: str) -> str:
    """Convert route segments to a simple text description."""
    lang_idx = 0 if language == "en" else 1
    lines = []

    for seg in segments:
        if seg["kind"] == "walk":
            fname = FLOOR_NAMES.get(seg["floor"], (f"Floor {seg['floor']}",) * 2)[lang_idx]
            if language == "en":
                lines.append(f"Walk {seg['distance_m']} m on {fname} floor ({seg['duration_s']:.0f}s)")
            else:
                lines.append(f"{fname} katta {seg['distance_m']} m yürü ({seg['duration_s']:.0f}s)")
        else:
            kind_label = TRANSITION_LABELS.get(seg["kind"], (seg["kind"],) * 2)[lang_idx]
            f_from = FLOOR_NAMES.get(seg["from_floor"], (str(seg["from_floor"]),) * 2)[lang_idx]
            f_to   = FLOOR_NAMES.get(seg["to_floor"],   (str(seg["to_floor"]),) * 2)[lang_idx]
            arrow  = "↑" if seg["direction"] == "up" else "↓"
            if language == "en":
                lines.append(f"Take {kind_label} from {f_from} to {f_to} {arrow} ({seg['duration_s']:.0f}s)")
            else:
                lines.append(f"{kind_label.capitalize()} ile {f_from}'dan {f_to}'a geç {arrow} ({seg['duration_s']:.0f}s)")

    return "\n".join(f"  {i+1}. {l}" for i, l in enumerate(lines))


FORMAT_SYSTEM_EN = """\
You are a friendly BuildingPath indoor navigation assistant.
Given a structured route, write a clear, concise, natural-sounding directions in English.
Keep it brief (3-5 sentences). Use natural language, not bullet points.
End with an encouraging closing line."""

FORMAT_SYSTEM_TR = """\
BuildingPath için samimi bir iç mekan navigasyon asistanısın.
Verilen yapılandırılmış rotayı kısa, net ve doğal bir Türkçeyle anlat.
Özlü tut (3-5 cümle). Madde işareti kullanma, doğal dil kullan.
Son cümlede teşvik edici bir kapanış yap."""


class RouteFormatter:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def format(self, segments: list, duration: dict,
               destination_name: str, language: str) -> str:
        """
        Format route segments into a natural language description.
        """
        route_text = segments_to_text(segments, language)
        total_dist = duration.get("distance_m", 0)
        total_min  = duration.get("duration_min", 0)

        if language == "en":
            system = FORMAT_SYSTEM_EN
            user_msg = (
                f"Destination: {destination_name}\n"
                f"Total: {total_dist} m, ~{total_min} min\n\n"
                f"Route steps:\n{route_text}"
            )
        else:
            system = FORMAT_SYSTEM_TR
            user_msg = (
                f"Hedef: {destination_name}\n"
                f"Toplam: {total_dist} m, ~{total_min} dk\n\n"
                f"Rota adımları:\n{route_text}"
            )

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_msg},
        ]

        return self.llm.chat(messages, temperature=0.4, max_tokens=300)
