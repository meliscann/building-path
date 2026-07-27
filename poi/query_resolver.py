"""
query_resolver.py
─────────────────────────────────────────────────────────────
Maps natural language queries to POI character codes.

Supports Turkish and English, common abbreviations, and
partial matches. Designed to be called by the LLM layer
(Phase 5) or directly from a CLI / web interface.

Usage
-----
    from query_resolver import QueryResolver
    from poi_index import build_poi_index
    from building_data import build_campus_map

    campus_map = build_campus_map()
    index      = build_poi_index(campus_map)
    resolver   = QueryResolver(index)

    result = resolver.resolve("en yakın tuvalet")
    # ResolveResult(char='T', name_en='Toilets', confidence='exact')

    result = resolver.resolve("wc")
    # ResolveResult(char='T', name_en='Toilets', confidence='alias')

    result = resolver.resolve("cafe nerede")
    # ResolveResult(char='F', name_en='Cafe', confidence='exact')
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from .poi_index import POIIndex, POI_REGISTRY


# ─────────────────────────────────────────────────────────────
# ALIAS TABLE
# ─────────────────────────────────────────────────────────────
# Maps every known synonym / abbreviation to a POI character.
# Keys are lowercase, stripped strings.

ALIASES: Dict[str, str] = {

    # ── Toilets ──────────────────────────────────────────────
    "tuvalet"            : "T",
    "tuvaletler"         : "T",
    "wc"                 : "T",
    "toilet"             : "T",
    "toilets"            : "T",
    "restroom"           : "T",
    "bathroom"           : "T",
    "lavatory"           : "T",

    # ── Cafe ──────────────────────────────────────────────────
    "kafe"               : "F",
    "kafeterya"          : "F",
    "cafe"               : "F",
    "cafeteria"          : "F",
    "coffee"             : "F",
    "kahve"              : "F",

    # ── Dining hall ───────────────────────────────────────────
    "yemekhane"          : "j",
    "yemek salonu"       : "j",
    "dining hall"        : "j",
    "dining room"        : "j",
    "canteen"            : "j",
    "yemek"              : "j",
    "food"               : "j",

    # ── Reception ─────────────────────────────────────────────
    "resepsiyon"         : "R",
    "reception"          : "R",
    "desk"               : "R",
    "info"               : "R",
    "information"        : "R",
    "danışma"            : "R",

    # ── Office ────────────────────────────────────────────────
    "ofis"               : "O",
    "office"             : "O",
    "offices"            : "O",

    # ── Lecture theatre ───────────────────────────────────────
    "amfi"               : "H",
    "amfitiyatro"        : "H",
    "lecture theatre"    : "H",
    "lecture theater"    : "H",
    "auditorium"         : "H",
    "theatre"            : "H",
    "theater"            : "H",
    "konferans salonu"   : "H",

    # ── Seminar room ──────────────────────────────────────────
    "seminer"            : "M",
    "seminer odası"      : "M",
    "seminar"            : "M",
    "seminar room"       : "M",
    "meeting room"       : "M",
    "toplantı odası"     : "M",

    # ── Computer lab ──────────────────────────────────────────
    "bilgisayar lab"     : "C",
    "bilgisayar laboratuvarı": "C",
    "computer lab"       : "C",
    "computer laboratory": "C",
    "pc lab"             : "C",
    "it lab"             : "C",

    # ── Teaching lab ──────────────────────────────────────────
    "öğretim lab"        : "G",
    "teaching lab"       : "G",
    "teaching laboratory": "G",

    # ── Biology lab ───────────────────────────────────────────
    "biyoloji lab"       : "J",
    "biyoloji laboratuvarı": "J",
    "biology lab"        : "J",
    "biology laboratory" : "J",
    "bio lab"            : "J",

    # ── Shared lab ────────────────────────────────────────────
    "paylaşımlı lab"     : "L",
    "shared lab"         : "L",
    "shared laboratory"  : "L",

    # ── Support lab ───────────────────────────────────────────
    "destek lab"         : "P",
    "support lab"        : "P",
    "support laboratory" : "P",

    # ── Imaging suite ─────────────────────────────────────────
    "görüntüleme"        : "I",
    "görüntüleme birimi" : "I",
    "imaging"            : "I",
    "imaging suite"      : "I",
    "scanner"            : "I",

    # ── EP testing ────────────────────────────────────────────
    "ep"                 : "K",
    "ep test"            : "K",
    "ep testing"         : "K",
    "ep odası"           : "K",
    "ep suite"           : "K",
    "ep lab"             : "K",

    # ── Workshop ──────────────────────────────────────────────
    "atölye"             : "W",
    "workshop"           : "W",
    "workshops"          : "W",
    "atölyeler"          : "W",

    # ── Breakout space ────────────────────────────────────────
    "breakout"           : "B",
    "breakout space"     : "B",
    "dinlenme"           : "B",
    "dinlenme alanı"     : "B",
    "lounge"             : "B",

    # ── Study space ───────────────────────────────────────────
    "çalışma alanı"      : "Z",
    "study space"        : "Z",
    "study area"         : "Z",
    "study"              : "Z",

    # ── Group study room ──────────────────────────────────────
    "grup çalışma"       : "A",
    "grup odası"         : "A",
    "group study"        : "A",
    "group study room"   : "A",
    "group room"         : "A",

    # ── Conference room ───────────────────────────────────────
    "konferans odası"    : "e",
    "conference room"    : "e",
    "conference"         : "e",

    # ── Herbarium ────────────────────────────────────────────
    "herbaryum"          : "Y",
    "herbarium"          : "Y",

    # ── Glasshouse / greenhouse ───────────────────────────────
    "sera"               : "q",
    "glasshouse"         : "q",
    "greenhouse"         : "q",

    # ── Stairs ────────────────────────────────────────────────
    "merdiven"           : "S",
    "stairs"             : "S",
    "staircase"          : "S",
    "stairwell"          : "S",

    # ── Elevator ──────────────────────────────────────────────
    "asansör"            : "E",
    "elevator"           : "E",
    "lift"               : "E",

    # ── Main entrance ─────────────────────────────────────────
    "ana giriş"          : "N",
    "giriş"              : "N",
    "main entrance"      : "N",
    "entrance"           : "N",

    # ── Fire exit ─────────────────────────────────────────────
    "yangın çıkışı"      : "X",
    "fire exit"          : "X",
    "emergency exit"     : "X",
    "acil çıkış"         : "X",

    # ── Terrace / atrium ──────────────────────────────────────
    "teras"              : "D",
    "terrace"            : "D",
    "atrium teras"       : "Q",
    "atrium terrace"     : "Q",
    "atrium"             : "Q",

    # ── Courtyard ─────────────────────────────────────────────
    "avlu"               : "V",
    "courtyard"          : "V",

    # ── Library ───────────────────────────────────────────────
    "kütüphane"          : "U",
    "library"            : "U",
}

# Words stripped from queries before lookup (common navigation phrases)
STRIP_WORDS = {
    # Turkish
    "en", "yakın", "nerede", "nereye", "nasıl", "gidebilirim",
    "gidelim", "götür", "bana", "beni", "var", "mı", "mı?",
    "bir", "the",
    # English
    "nearest", "closest", "find", "where", "is", "the",
    "a", "an", "me", "to", "go", "take", "show", "get",
    "how", "do", "i", "reach", "navigate",
}


# ─────────────────────────────────────────────────────────────
# RESOLVE RESULT
# ─────────────────────────────────────────────────────────────

@dataclass
class ResolveResult:
    """Outcome of a query resolution attempt."""
    char        : Optional[str]         # POI character code, or None if failed/ambiguous
    name_en     : Optional[str]         # English display name
    name_tr     : Optional[str]         # Turkish display name
    confidence  : str                   # "exact" | "partial" | "ambiguous" | "failed"
    input_query : str                   # original query string
    note        : str = ""              # optional explanation
    alternatives: List[str] = field(default_factory=list)  # chars when ambiguous

    @property
    def is_ambiguous(self) -> bool:
        return self.confidence == "ambiguous"

    @property
    def is_resolved(self) -> bool:
        return self.char is not None and self.confidence != "ambiguous"


# ─────────────────────────────────────────────────────────────
# QUERY RESOLVER
# ─────────────────────────────────────────────────────────────

class QueryResolver:
    """
    Resolves natural-language POI queries to character codes.

    Resolution strategy (in order):
      1. Exact alias match (stripped, lowercased query)
      2. Partial alias match (query is a substring of an alias key,
         or vice versa)
      3. Direct character code lookup (e.g. user typed "O" or "H")
      4. Failure

    Parameters
    ----------
    index : POIIndex
        Built from the live campus map; used to confirm that
        a matched POI actually exists in the building.
    """

    def __init__(self, index: POIIndex):
        self.index = index

    def _strip_query(self, text: str) -> str:
        """Lowercase, strip filler words, collapse whitespace."""
        words = text.lower().split()
        words = [w.strip(".,?!") for w in words if w not in STRIP_WORDS]
        return " ".join(words).strip()

    def _make_result(self, char: str, confidence: str,
                     query: str, note: str = "") -> ResolveResult:
        poi = POI_REGISTRY.get(char)
        return ResolveResult(
            char        = char,
            name_en     = poi.name_en if poi else char,
            name_tr     = poi.name_tr if poi else char,
            confidence  = confidence,
            input_query = query,
            note        = note,
        )

    def _make_labeled_result(self, labeled_poi, query: str) -> ResolveResult:
        """Create a ResolveResult that points to a specific named instance."""
        poi = POI_REGISTRY.get(labeled_poi.char)
        return ResolveResult(
            char        = labeled_poi.char,
            name_en     = labeled_poi.name,
            name_tr     = labeled_poi.name_tr or (poi.name_tr if poi else ""),
            confidence  = "named",
            input_query = query,
            note        = f"named instance @ floor={labeled_poi.floor} ({labeled_poi.x},{labeled_poi.y})",
            alternatives= [labeled_poi.state],   # specific coordinate
        )

    @staticmethod
    def _tokenize(text: str) -> set:
        """Lowercase, split, normalise punctuation and possessives from each token."""
        tokens = set()
        for w in text.lower().split():
            w = w.strip(".,?!\"")
            # remove possessive 's so "Whitfield's" → "whitfield"
            if w.endswith("'s"):
                w = w[:-2]
            elif w.endswith("'"):
                w = w[:-1]
            if w:
                tokens.add(w)
        return tokens

    def _search_ranked(self, clean: str) -> list:
        """
        Return labeled POI matches using three priority tiers.

        Tier 1 — exact name match (punctuation-normalised)
        Tier 2 — every query token appears as a whole word in the name
        Tier 3 — query is a substring of the name (fallback)

        Only the highest non-empty tier is returned.
        """
        q_tokens = self._tokenize(clean)

        tier1: list = []
        tier2: list = []
        tier3: list = []

        for lp in self.index.labeled():
            name_lo    = lp.name.lower()
            name_tr_lo = (lp.name_tr or "").lower()

            # Tier 1: normalised exact match
            if clean == name_lo or (name_tr_lo and clean == name_tr_lo):
                tier1.append(lp)
                continue

            # Tier 2: all query tokens found as whole words (punct-stripped)
            name_tokens    = self._tokenize(name_lo)
            name_tr_tokens = self._tokenize(name_tr_lo) if name_tr_lo else set()
            if q_tokens and (q_tokens.issubset(name_tokens) or
                             q_tokens.issubset(name_tr_tokens)):
                tier2.append(lp)
                continue

            # Tier 3: substring
            if clean in name_lo or (name_tr_lo and clean in name_tr_lo):
                tier3.append(lp)

        if tier1:
            return tier1
        if tier2:
            return tier2
        return tier3

    def resolve(self, query: str) -> ResolveResult:
        """
        Resolve a query string to a POI character or named instance.

        Resolution order:
          0. Exact alias match  — prevents POI-name labels from shadowing
             common room-type keywords (e.g. "sera" → Glasshouse, not
             "Sera Araştırma Koordinatörü Ofisi")
          1. Named instance match  (poi_labels.json) — tiered ranking
          2. Partial alias match (ambiguous if multiple chars tie)
          3. Direct character code
          4. Failure

        Returns a ResolveResult; check result.char for None on failure.
        When confidence == 'named', result.alternatives[0] is the
        specific (floor, x, y) state to navigate to.
        """
        clean = self._strip_query(query)

        # 0. Exact alias match (checked first so generic room-type keywords
        #    are not shadowed by labeled POI names that contain the same word)
        if clean in ALIASES:
            char = ALIASES[clean]
            if self.index.cells(char):
                return self._make_result(char, "exact", query)

        # 1. Named instance match (from poi_labels.json) — ranked tiers
        matches = self._search_ranked(clean)
        if len(matches) == 1:
            return self._make_labeled_result(matches[0], query)
        elif len(matches) > 1:
            unique_chars = set(p.char for p in matches)
            if len(unique_chars) == 1:
                # All matches are the same POI type (same char) — numbered instances
                # or multiple entrances of the same space.  Return all states so the
                # pathfinder picks the nearest one automatically.
                poi = POI_REGISTRY.get(matches[0].char)
                unique_names = set(p.name for p in matches)
                rep_name    = matches[0].name if len(unique_names) == 1 else (poi.name_en if poi else matches[0].name)
                rep_name_tr = (matches[0].name_tr if len(unique_names) == 1
                               else (poi.name_tr if poi else ""))
                return ResolveResult(
                    char        = matches[0].char,
                    name_en     = rep_name,
                    name_tr     = rep_name_tr or (poi.name_tr if poi else ""),
                    confidence  = "named",
                    input_query = query,
                    note        = f"{len(matches)} instances — nearest will be selected",
                    alternatives= [p.state for p in matches],
                )
            else:
                # Genuinely different POI types — ambiguous
                unique = []
                seen   = set()
                for p in matches:
                    if p.name not in seen:
                        unique.append(p.name)
                        seen.add(p.name)
                names = ", ".join(unique)
                return ResolveResult(
                    char        = None,
                    name_en     = None,
                    name_tr     = None,
                    confidence  = "ambiguous",
                    input_query = query,
                    note        = f"Hangi birini kastettiniz? {names}",
                    alternatives= [p.state for p in matches],
                )

        # 2. Partial alias match
        candidates: List[tuple] = []
        seen_chars = {}   # char -> best (score, alias)
        for alias, char in ALIASES.items():
            if clean in alias or alias in clean:
                if self.index.cells(char):
                    score = len(set(clean.split()) & set(alias.split()))
                    if char not in seen_chars or score > seen_chars[char][0]:
                        seen_chars[char] = (score, alias)

        if seen_chars:
            # Sort distinct POI types by score descending
            ranked = sorted(seen_chars.items(),
                            key=lambda kv: kv[1][0], reverse=True)
            best_score = ranked[0][1][0]

            # Collect all chars that share the top score
            top_chars = [ch for ch, (sc, _) in ranked if sc == best_score]

            if len(top_chars) == 1:
                # Unambiguous partial match
                char, (_, matched_alias) = ranked[0]
                return self._make_result(
                    char, "partial", query,
                    note=f"matched via '{matched_alias}'"
                )
            else:
                # Multiple POI types equally match — ambiguous
                poi_list = ", ".join(
                    f"{ch} ({POI_REGISTRY[ch].name_en})"
                    if ch in POI_REGISTRY else ch
                    for ch in top_chars
                )
                poi = POI_REGISTRY.get(top_chars[0])
                return ResolveResult(
                    char         = None,
                    name_en      = None,
                    name_tr      = None,
                    confidence   = "ambiguous",
                    input_query  = query,
                    note         = f"Did you mean: {poi_list}?",
                    alternatives = top_chars,
                )

        # 3. Direct character code
        if len(query.strip()) == 1:
            char = query.strip()
            if self.index.cells(char):
                return self._make_result(char, "exact", query,
                                         note="direct character input")

        # 4. Failure
        return ResolveResult(
            char        = None,
            name_en     = None,
            name_tr     = None,
            confidence  = "failed",
            input_query = query,
            note        = f"No POI matched for '{clean}'",
        )

    def suggest(self, query: str, max_results: int = 3) -> List[ResolveResult]:
        """
        Return up to `max_results` candidate POIs for a query.
        Useful for disambiguation when confidence is low.
        """
        clean = self._strip_query(query)
        seen  = set()
        results = []

        for alias, char in ALIASES.items():
            if (clean in alias or alias in clean) and char not in seen:
                if self.index.cells(char):
                    seen.add(char)
                    results.append(self._make_result(char, "partial", query,
                                                     note=f"via '{alias}'"))
                if len(results) >= max_results:
                    break

        return results
