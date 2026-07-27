"""
navigator.py
─────────────────────────────────────────────────────────────
Main orchestrator for the BuildingPath navigation system.

Pipeline:
  1. LLM parses natural language query
  2. QueryResolver maps destination → POI coordinates
  3. BuildingProblem + A* finds optimal route (profile-aware)
  4. LLM formats route into natural language

Usage:
    from navigator import Navigator
    nav = Navigator()
    print(nav.navigate("Prof. Whitfield'a gitmek istiyorum"))
"""

import math
import os

from data.building_data        import build_campus_map
from poi.poi_index             import build_poi_index
from poi.poi_label_loader      import load_poi_labels
from poi.query_resolver        import QueryResolver
from poi.user_profile          import get_profile
from pathfinding.indoor_search import BuildingProblem
from pathfinding.heuristics    import make_heuristic
from pathfinding.astar         import astar_search
from pathfinding.common        import failure, path_states, path_actions
from pathfinding.costs         import path_duration, route_breakdown

from .llm_client      import LLMClient
from .query_parser    import QueryParser
from .route_formatter import RouteFormatter

FLOOR_NAMES = ["Lower Ground","Ground","First","Second","Third","Fourth"]


class Navigator:
    def __init__(self, start_state: tuple = None, api_key: str = None):
        # Build map and index
        self.campus_map = build_campus_map()
        self.index      = build_poi_index(self.campus_map)
        self.index.load_labels(self.campus_map)

        # Default start: main entrance
        from pathfinding.indoor_search import find_cells
        entrances = find_cells(self.campus_map, 'N')
        self.start = start_state or (entrances[0] if entrances else (0, 187, 75))

        # LLM components
        key = api_key or os.environ.get("GROQ_API_KEY", "")
        self.llm       = LLMClient(api_key=key)
        self.parser    = QueryParser(self.llm)
        self.resolver  = QueryResolver(self.index)
        self.formatter = RouteFormatter(self.llm)

    def navigate(self, query: str, verbose: bool = False) -> str:
        """
        Full navigation pipeline from natural language query to response.
        """
        # ── 1. Parse ─────────────────────────────────────────
        parsed = self.parser.parse(query)

        if verbose:
            print(f"\n  [Parse]  destination='{parsed.destination}'  "
                  f"profile='{parsed.profile}'  floor={parsed.floor}  "
                  f"lang='{parsed.language}'")

        # ── 2. Resolve destination ───────────────────────────
        result = self.resolver.resolve(parsed.destination)

        if verbose:
            print(f"  [Resolve] confidence='{result.confidence}'  "
                  f"char={result.char}  name='{result.name_en}'")

        if result.confidence == "failed":
            if parsed.language == "tr":
                return f"'{parsed.destination}' bulunamadı. Lütfen farklı bir ifadeyle deneyin."
            return f"Could not find '{parsed.destination}'. Please try a different description."

        if result.confidence == "ambiguous":
            if parsed.language == "tr":
                return f"Belirsiz: {result.note}"
            return f"Ambiguous: {result.note}"

        # ── 3. Build goal set ────────────────────────────────
        if result.confidence == "named":
            # Named instances: alternatives hold specific (floor,x,y) states
            goals = [s for s in result.alternatives if isinstance(s, tuple)]
        else:
            goals = self.index.cells(result.char)

        # Floor filter
        if parsed.floor is not None:
            goals = [(f, x, y) for (f, x, y) in goals if f == parsed.floor]
            if not goals:
                if parsed.language == "tr":
                    fn = FLOOR_NAMES[parsed.floor] if parsed.floor < len(FLOOR_NAMES) else str(parsed.floor)
                    return f"Bu katta ({fn}) '{result.name_en}' bulunamadı."
                return f"No '{result.name_en}' found on that floor."

        # Cap goals for performance
        sf, sx, sy = self.start
        if len(goals) > 50:
            goals = sorted(goals,
                key=lambda g: math.sqrt((g[1]-sx)**2 + (g[2]-sy)**2))[:50]

        # ── 4. Pathfind ──────────────────────────────────────
        profile = get_profile(parsed.profile)
        prob    = BuildingProblem(self.start, self.campus_map,
                                goals=goals, profile=profile)
        h       = make_heuristic(goals, self.campus_map)
        node, stats = astar_search(prob, h)

        if node is failure:
            if parsed.language == "tr":
                return "Bu hedefe ulaşılabilir bir rota bulunamadı."
            return "No reachable route found to this destination."

        if verbose:
            print(f"  [Search] expanded={stats['nodes_expanded']:,}  "
                  f"cost={node.path_cost:.1f}")

        # ── 5. Build route ───────────────────────────────────
        states   = path_states(node)
        acts     = path_actions(node)
        duration = path_duration(states, acts)
        segments = route_breakdown(states, acts)
        dest_name = result.name_en or parsed.destination

        # ── 6. Format ────────────────────────────────────────
        return self.formatter.format(segments, duration,
                                     dest_name, parsed.language)
