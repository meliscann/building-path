"""
app.py
──────────────────────────────────────────────────────────────
BuildingPath – Flask web interface.

Usage:
    python app.py
    # Open http://localhost:5001
"""

import sys, os, math, base64, io
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from collections import deque
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from PIL import Image, ImageDraw, ImageFont

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from data.building_data        import build_campus_map
from poi.poi_index             import build_poi_index, POI_REGISTRY
from poi.query_resolver        import QueryResolver
from poi.user_profile          import UserProfile
from pathfinding.indoor_search import BuildingProblem, find_cells
from pathfinding.heuristics    import make_heuristic
from pathfinding.astar         import astar_search
from pathfinding.common        import failure, path_states, path_actions
from pathfinding.costs         import path_duration, route_breakdown

app = Flask(__name__)

# ── Build navigation infrastructure ──────────────────────────────────────────
print("🗺  BuildingPath – loading map …", end=" ", flush=True)
_map = build_campus_map()
_index = build_poi_index(_map)
_index.load_labels(_map)
_res = QueryResolver(_index)
_n_cells = find_cells(_map, 'N')
DEFAULT_START = _n_cells[0] if _n_cells else (1, 187, 75)
print("ready.")

# ── Constants ─────────────────────────────────────────────────────────────────

FLOOR_TR = ["Alt Zemin", "Zemin", "Birinci", "İkinci", "Üçüncü", "Dördüncü"]
FLOOR_EN = ["Lower Ground", "Ground", "First", "Second", "Third", "Fourth"]

MAPS_DIR = _ROOT / "static" / "maps"
MAP_FILES = {
    0: "lower-ground-floor.png",
    1: "ground-floor.png",
    2: "first-floor.png",
    3: "second-floor.png",
    4: "third-floor.png",
    5: "fourth-floor.png",
}
MAP_SCALE = 10   # each grid cell → 5×5 pixels

# Chars that should NOT get a room label on the map
_LABEL_SKIP = {'#', '.', 'S', 'E'}

_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
try:
    _label_font_specific = ImageFont.truetype(_FONT_PATH, size=15)
    _label_font_general  = ImageFont.truetype(_FONT_PATH, size=13)
except Exception:
    _label_font_specific = ImageFont.load_default()
    _label_font_general  = ImageFont.load_default()

# ── Route profiles ────────────────────────────────────────────────────────────

_PROFILES = {
    "fastest": UserProfile(
        name="fastest", label="En Hızlı",
        forbidden_actions=set(),
        cost_multipliers={},
    ),
    "least_effort": UserProfile(
        name="least_effort", label="En Az Efor",
        forbidden_actions=set(),
        cost_multipliers={"STAIR_UP": 3.0, "STAIR_DOWN": 2.0},
    ),
}

ROUTE_META = {
    "fastest": {
        "id": "fastest",
        "label_tr": "En Hızlı",       "label_en": "Fastest",
        "desc_tr":  "En kısa sürede varmanızı sağlayan standart rota",
        "desc_en":  "Standard route optimised for minimum travel time",
        "icon": "zap", "color": "#1565C0",
    },
    "least_effort": {
        "id": "least_effort",
        "label_tr": "En Az Efor",     "label_en": "Least Effort",
        "desc_tr":  "Merdiveni minimumda tutan, asansörü tercih eden rota",
        "desc_en":  "Minimises stairs, strongly prefers elevators",
        "icon": "accessibility", "color": "#2E7D32",
    },
}

# ── POI categories for the UI ─────────────────────────────────────────────────

CATEGORIES = [
    {
        "id": "entrance",
        "name_tr": "Girişler & Resepsiyon",
        "name_en": "Entrances & Reception",
        "icon": "door-open",
        "chars": ["N", "X", "R"]
    },
    {
        "id": "food",
        "name_tr": "Yiyecek & İçecek",
        "name_en": "Food & Drink",
        "icon": "coffee",
        "chars": ["F", "j"]
    },
    {
        "id": "amenity",
        "name_tr": "Tuvaletler",
        "name_en": "Toilets",
        "icon": "droplets",
        "chars": ["T"]
    },
    {
        "id": "teaching",
        "name_tr": "Eğitim & Öğretim",
        "name_en": "Teaching & Learning",
        "icon": "graduation-cap",
        "chars": ["H", "M", "G", "C", "e"]
    },
    {
        "id": "labs",
        "name_tr": "Laboratuvarlar",
        "name_en": "Laboratories",
        "icon": "flask-conical",
        "chars": ["J", "L", "P", "I", "K", "W"]
    },
    {
        "id": "offices",
        "name_tr": "Ofisler",
        "name_en": "Offices",
        "icon": "briefcase",
        "chars": ["O"]
    },
    {
        "id": "library",
        "name_tr": "Kütüphane",
        "name_en": "Library",
        "icon": "book-marked",
        "chars": ["U"]
    },
    {
        "id": "study",
        "name_tr": "Çalışma Alanları",
        "name_en": "Study Spaces",
        "icon": "book-open",
        "chars": ["B", "Z", "A"]
    },
    {
        "id": "special",
        "name_tr": "Özel & Açık Alanlar",
        "name_en": "Special & Open Areas",
        "icon": "leaf",
        "chars": ["V", "Q", "D", "q", "Y", "z"]
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dedup_labeled(lps, poi):
    """Aynı (isim, kat) grubundaki etiketleri birleştir; centroid'e en yakın hücreyi seç."""
    groups = {}
    for lp in lps:
        groups.setdefault((lp.name, lp.floor), []).append(lp)
    result = []
    for (name, f), group in sorted(groups.items(), key=lambda kv: (kv[0][1], kv[0][0] or "")):
        mx  = sum(lp.x for lp in group) // len(group)
        my  = sum(lp.y for lp in group) // len(group)
        rep = min(group, key=lambda lp: (lp.x - mx)**2 + (lp.y - my)**2)
        result.append({
            "id":          f"{rep.char}_{f}_{rep.x}_{rep.y}",
            "name":        rep.name,
            "name_tr":     rep.name_tr or (poi.name_tr if poi else ""),
            "floor":       f,
            "floor_tr":    _fname(f, "tr"),
            "floor_en":    _fname(f, "en"),
            "x":           rep.x,
            "y":           rep.y,
            "description":    rep.description or "",
            "description_tr": rep.description_tr or "",
            "open_hours":     rep.open_hours or "",
            "all_states":  [{"floor": lp.floor, "x": lp.x, "y": lp.y} for lp in group],
        })
    return result


def _filter_lps(lps, res):
    """If resolver found specific named instances, keep only those cells."""
    if res.alternatives:
        alt_set = set(res.alternatives)
        filtered = [p for p in lps if (p.floor, p.x, p.y) in alt_set]
        if filtered:
            return filtered
    return lps


def _floor_components(floor_cells):
    """BFS: kattaki hücreleri bağlı bileşenlere ayırır. Her bileşen için centroid'e en yakın hücreyi döndürür."""
    cell_set = {(x, y) for _, x, y in floor_cells}
    visited  = set()
    result   = []
    for (x, y) in sorted(cell_set):
        if (x, y) in visited:
            continue
        comp = []
        q = deque([(x, y)])
        visited.add((x, y))
        while q:
            cx, cy = q.popleft()
            comp.append((cx, cy))
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = cx+dx, cy+dy
                if (nx, ny) in cell_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    q.append((nx, ny))
        mx  = sum(c[0] for c in comp) // len(comp)
        my  = sum(c[1] for c in comp) // len(comp)
        rep = min(comp, key=lambda c: (c[0]-mx)**2 + (c[1]-my)**2)
        result.append({"x": rep[0], "y": rep[1], "size": len(comp)})
    return result


def _draw_text_label(draw, text, cx, cy, font, max_chars=16):
    """Draw centered text with shadow at pixel coords (cx, cy)."""
    words = text.split()
    lines, cur, cur_len = [], [], 0
    for w in words:
        if cur_len + len(w) + len(cur) > max_chars and cur:
            lines.append(" ".join(cur))
            cur, cur_len = [w], len(w)
        else:
            cur.append(w)
            cur_len += len(w)
    if cur:
        lines.append(" ".join(cur))

    try:
        lh = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 2
    except Exception:
        lh = 10

    y0 = cy - (lh * len(lines)) // 2
    for line in lines:
        try:
            bx = font.getbbox(line)
            tw = bx[2] - bx[0]
        except Exception:
            tw = len(line) * 6
        x0 = cx - tw // 2
        for ox, oy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            draw.text((x0 + ox, y0 + oy), line, font=font, fill=(0, 0, 0))
        draw.text((x0, y0), line, font=font, fill=(255, 255, 255))
        y0 += lh


# Pre-computed per-floor label list: floor_idx → [{x, y, text, specific}]
_floor_label_data: dict = {}


def _compute_floor_labels():
    for floor_idx in range(6):
        entries: list = []
        grid = _map[floor_idx]
        rows = len(grid)
        cols = len(grid[0]) if rows else 0

        # 1. Labeled POIs (from poi_labels.json), deduped by (name, floor)
        labeled_chars: set = set()
        for char in list(POI_REGISTRY):
            if char in _LABEL_SKIP:
                continue
            lps = _index.labeled_by_char(char)
            if not lps:
                continue
            poi   = POI_REGISTRY[char]
            for inst in _dedup_labeled(lps, poi):
                if inst["floor"] == floor_idx:
                    entries.append({"x": inst["x"], "y": inst["y"],
                                    "text": inst["name"], "specific": True})
                    labeled_chars.add(char)

        # 2. Unlabeled POI types – general name at each BFS component centroid
        seen: set = set()
        for ry in range(rows):
            for rx in range(cols):
                c = grid[ry][rx]
                if c not in seen and c not in _LABEL_SKIP and c in POI_REGISTRY:
                    seen.add(c)

        for char in seen:
            if char in labeled_chars:
                continue  # specific labels already cover this type
            floor_cells = [(f, x, y) for f, x, y in _index.cells(char) if f == floor_idx]
            if not floor_cells:
                continue
            poi   = POI_REGISTRY[char]
            for comp in _floor_components(floor_cells):
                if comp["size"] < 2:
                    continue
                entries.append({"x": comp["x"], "y": comp["y"],
                                 "text": poi.name_en, "specific": False})

        _floor_label_data[floor_idx] = entries


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _fname(f, lang="tr"):
    names = FLOOR_TR if lang == "tr" else FLOOR_EN
    return names[f] if f < len(names) else str(f)


def _run_route(start, goals, profile_id):
    """Run A* for one route variant. Returns serialisable dict or None."""
    profile = _PROFILES[profile_id]
    sf, sx, sy = start

    if len(goals) > 50:
        goals = sorted(goals, key=lambda g: math.sqrt((g[1]-sx)**2 + (g[2]-sy)**2))[:50]
    if not goals:
        return None

    prob = BuildingProblem(start, _map, goals=goals, profile=profile)
    h    = make_heuristic(goals, _map)
    node, stats = astar_search(prob, h)
    if node is failure:
        return None

    states   = path_states(node)
    acts     = path_actions(node)
    duration = path_duration(states, acts)
    segs     = route_breakdown(states, acts)

    # path_by_floor  : str(floor) → [[x,y], …]
    # trans_points   : str(floor) → [[x,y], …]  (where floor change happens)
    path_by_floor = {}
    trans_points  = {}

    for (f, x, y) in states:
        path_by_floor.setdefault(str(f), []).append([x, y])

    for i in range(len(states) - 1):
        f0, x0, y0 = states[i]
        f1, x1, y1 = states[i + 1]
        if f0 != f1:
            trans_points.setdefault(str(f0), []).append([x0, y0])
            trans_points.setdefault(str(f1), []).append([x1, y1])

    floors_visited = sorted(set(f for f, x, y in states))

    serial_segs = []
    for seg in segs:
        if seg["kind"] == "walk":
            serial_segs.append({
                "kind":       "walk",
                "floor":      seg["floor"],
                "floor_tr":   _fname(seg["floor"], "tr"),
                "floor_en":   _fname(seg["floor"], "en"),
                "distance_m": seg["distance_m"],
                "duration_s": seg["duration_s"],
            })
        else:
            serial_segs.append({
                "kind":       seg["kind"],
                "from_floor": seg["from_floor"],
                "to_floor":   seg["to_floor"],
                "direction":  seg["direction"],
                "duration_s": seg["duration_s"],
                "from_tr":    _fname(seg["from_floor"], "tr"),
                "from_en":    _fname(seg["from_floor"], "en"),
                "to_tr":      _fname(seg["to_floor"],   "tr"),
                "to_en":      _fname(seg["to_floor"],   "en"),
            })

    meta = ROUTE_META[profile_id]
    return {
        **meta,
        "available":        True,
        "duration_min":     duration["duration_min"],
        "duration_s":       duration["duration_s"],
        "distance_m":       duration["distance_m"],
        "floors_visited":   floors_visited,
        "segments":         serial_segs,
        "path_by_floor":    path_by_floor,
        "trans_points":     trans_points,
        "start_state":      list(states[0]),
        "end_state":        list(states[-1]),
        "stats": {
            "nodes_expanded": stats.get("nodes_expanded", 0),
            "cost":           round(node.path_cost, 2),
        },
    }


def _draw_route(floor_idx, path_pts, color,
                start_pt=None, end_pt=None, trans_pts=None):
    """Draw route overlay on a floor-plan PNG. Returns base-64 string."""
    fname = MAP_FILES.get(floor_idx, "")
    fpath = MAPS_DIR / fname
    if fname and fpath.exists():
        img = Image.open(fpath).convert("RGB")
        img = img.resize((img.width * MAP_SCALE, img.height * MAP_SCALE),
                         Image.NEAREST)
    else:
        img = Image.new("RGB", (230 * MAP_SCALE, 128 * MAP_SCALE), (160, 160, 160))

    draw = ImageDraw.Draw(img)
    rgb  = _hex_rgb(color)
    s    = MAP_SCALE

    def px(x): return x * s + s // 2
    def py(y): return y * s + s // 2

    # POI labels (drawn under the route)
    for lbl in _floor_label_data.get(floor_idx, []):
        font = _label_font_specific if lbl["specific"] else _label_font_general
        _draw_text_label(draw, lbl["text"], px(lbl["x"]), py(lbl["y"]), font)

    # Route polyline (shadow + colour)
    if len(path_pts) > 1:
        pts = [(px(x), py(y)) for x, y in path_pts]
        draw.line(pts, fill=(0, 0, 0),  width=s + 2)
        draw.line(pts, fill=rgb,        width=s)

    # Transition dots (floor change) – yellow
    for x, y in (trans_pts or []):
        r = s + 1
        draw.ellipse([px(x)-r, py(y)-r, px(x)+r, py(y)+r],
                     fill=(255, 193, 7), outline=(0, 0, 0), width=1)

    # Start dot – green
    if start_pt:
        x, y = start_pt
        r = s + 3
        draw.ellipse([px(x)-r, py(y)-r, px(x)+r, py(y)+r],
                     fill=(56, 142, 60), outline=(255, 255, 255), width=2)

    # End dot – red
    if end_pt:
        x, y = end_pt
        r = s + 3
        draw.ellipse([px(x)-r, py(y)-r, px(x)+r, py(y)+r],
                     fill=(211, 47, 47), outline=(255, 255, 255), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ── Accessibility check helpers ──────────────────────────────────────────────

_ACCESS_KW = {
    "asansör", "asansörle", "asansörden", "elevator", "lift",
    "merdiven", "merdivenle", "stairs", "stair",
    "tekerlekli", "wheelchair", "engelli", "erişilebilir",
    "çıkabilir", "inebilir", "ulaşabilir", "accessible",
}


def _has_access_query(query: str) -> bool:
    return any(kw in query.lower() for kw in _ACCESS_KW)


def _access_note(char: str, lang: str) -> str:
    """
    Run two quick A* checks (elevator-only, stair-only) from DEFAULT_START
    to the given POI. Returns a factual note for the LLM context so it
    cannot hallucinate reachability claims.
    """
    from poi.user_profile import UserProfile

    cells = list(_index.cells(char))
    if not cells:
        return ""
    goals = set(cells[:50])

    def _reachable(forbidden):
        profile = UserProfile("_test", "", forbidden_actions=forbidden,
                              cost_multipliers={})
        try:
            prob = BuildingProblem(DEFAULT_START, _map, goals=goals,
                                   profile=profile)
            h    = make_heuristic(list(goals), _map)
            node, _ = astar_search(prob, h)
            return node is not failure
        except Exception:
            return False

    elev_ok  = _reachable({"STAIR_UP", "STAIR_DOWN"})
    stair_ok = _reachable({"ELEVATOR_UP", "ELEVATOR_DOWN"})

    if lang == "tr":
        if elev_ok and stair_ok:
            return "✓ Erişilebilirlik (pathfinding doğruladı): Hem asansör hem merdiven kullanılarak ulaşılabilir."
        elif elev_ok:
            return "✓ Erişilebilirlik (pathfinding doğruladı): Yalnızca asansörle ulaşılabilir, merdiven gerekmez."
        elif stair_ok:
            return "⚠ Erişilebilirlik (pathfinding doğruladı): Yalnızca merdivenle ulaşılabilir — asansörle ULAŞILAMAZ."
        else:
            return "⚠ Erişilebilirlik (pathfinding doğruladı): Bu mekana ne yalnızca asansör ne de yalnızca merdivenle ulaşılamaz; her ikisi de gereklidir."
    else:
        if elev_ok and stair_ok:
            return "✓ Accessibility (pathfinding verified): Reachable by both elevator and stairs."
        elif elev_ok:
            return "✓ Accessibility (pathfinding verified): Reachable by elevator alone, no stairs required."
        elif stair_ok:
            return "⚠ Accessibility (pathfinding verified): Reachable by stairs only — elevator route does NOT exist."
        else:
            return "⚠ Accessibility (pathfinding verified): Requires both elevator and stairs; neither alone is sufficient."


# ── Optional LLM (Groq) ──────────────────────────────────────────────────────

_llm_ready   = False
_llm_client  = None
_llm_parser  = None


def _try_init_llm():
    global _llm_ready, _llm_client, _llm_parser
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return
    try:
        from llm.llm_client   import LLMClient
        from llm.query_parser import QueryParser
        _llm_client = LLMClient(api_key=key)
        _llm_parser = QueryParser(_llm_client)
        _llm_ready  = True
        print("LLM (Groq) ready.")
    except Exception as e:
        print(f"LLM init skipped: {e}")


_try_init_llm()

print("Computing floor label data …", end=" ", flush=True)
_compute_floor_labels()
print("done.")

# ── Flask routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/pois")
def api_pois():
    cats = []
    for cat in CATEGORIES:
        types = []
        for char in cat["chars"]:
            cells = _index.cells(char)
            if not cells:
                continue
            poi = POI_REGISTRY.get(char)
            if not poi:
                continue

            labeled = _dedup_labeled(_index.labeled_by_char(char), poi)

            floors = sorted(set(f for f, x, y in cells))
            cells_by_floor = {}
            for f, x, y in cells:
                cells_by_floor.setdefault(f, []).append((f, x, y))
            first_cell_by_floor  = {}
            components_by_floor  = {}
            for f, fcells in cells_by_floor.items():
                comps = _floor_components(fcells)
                first_cell_by_floor[f] = {"floor": f, "x": comps[0]["x"], "y": comps[0]["y"]}
                if len(comps) > 1:
                    components_by_floor[str(f)] = comps
            types.append({
                "char":                char,
                "name_tr":             poi.name_tr,
                "name_en":             poi.name_en,
                "icon":                poi.icon,
                "count":               len(cells),
                "floors":              floors,
                "floors_tr":           [_fname(f, "tr") for f in floors],
                "floors_en":           [_fname(f, "en") for f in floors],
                "labeled":             labeled,
                "first_cell":          {"floor": cells[0][0], "x": cells[0][1], "y": cells[0][2]},
                "first_cell_by_floor": first_cell_by_floor,
                "components_by_floor": components_by_floor,
            })

        if types:
            cats.append({**cat, "types": types})

    ds = DEFAULT_START
    return jsonify({
        "categories":    cats,
        "default_start": {
            "floor": ds[0], "x": ds[1], "y": ds[2],
            "name_tr": "Ana Giriş", "name_en": "Main Entrance", "char": "N",
        },
        "floor_tr": FLOOR_TR,
        "floor_en": FLOOR_EN,
    })


_RESOLVE_SYSTEM = """\
You are a search assistant for an Oxford university building navigation system.
The building contains: offices (Prof./Dr./staff), labs, lecture theatres, seminar rooms,
cafes, dining halls, toilets, libraries, study spaces, glasshouse, herbarium,
EP testing suites (abbreviation: EP), imaging suites, workshops, and more.

Given the user's query (Turkish or English), output ONLY this JSON:
{"destination": "<most specific searchable name>"}

Rules:
- "EP" or "ep" always means "EP testing" (electrophysiology testing suite) — never herbarium
- People: use the name as it appears in a staff directory — "Prof. Whitfield", "Dr. Hassan"
- Room types: standard English name — "lecture theatre", "seminar room", "support lab", "cafe"
- Keep numbers/identifiers: "support lab 2", "seminar room 3"
- Correct typos: "biologi" → "biology", "semimer" → "seminar"
- Strip navigation phrases: "nereye", "nasıl giderim", "götür beni", "where is", "go to"
- Return ONLY the JSON, no explanation, no markdown."""


def _resolve_labeled(lbs, cells, char, poi, ctx: str = "dest"):
    """
    Build the labeled list for api_resolve.
    Named instances → return deduped list (same for both ctx values).
    Unlabeled multi-floor type:
      ctx='dest'  → one entry per floor, all_states = all components on that floor
      ctx='start' → one entry per BFS component with nearby-landmark description
    """
    deduped = _dedup_labeled(lbs, poi)
    if deduped:
        return deduped
    if not cells:
        return []
    fc: dict = {}
    for (f, x, y) in cells:
        fc.setdefault(f, []).append((x, y))
    if len(fc) <= 1:
        return []   # single floor — no disambiguation needed

    result = []
    if ctx == "start":
        for f in sorted(fc):
            floor_cells = [(f, x, y) for (x, y) in fc[f]]
            # Build per-component entries, then merge same-description ones so
            # the user never sees two identical option labels.
            by_desc: dict = {}
            for comp in _floor_components(floor_cells):
                cx, cy = comp["x"], comp["y"]
                desc_en = _nearby_description(f, cx, cy, "en", skip_char=char)
                desc_tr = _nearby_description(f, cx, cy, "tr", skip_char=char)
                key = desc_en
                if key not in by_desc:
                    by_desc[key] = {
                        "cx": cx, "cy": cy,
                        "desc_en": desc_en, "desc_tr": desc_tr,
                        "all_states": [],
                    }
                by_desc[key]["all_states"].append({"floor": f, "x": cx, "y": cy})
            for entry in by_desc.values():
                cx, cy = entry["cx"], entry["cy"]
                result.append({
                    "id":             f"{char}_{f}_{cx}_{cy}",
                    "name":           poi.name_en if poi else char,
                    "name_tr":        poi.name_tr if poi else char,
                    "floor":          f,
                    "floor_tr":       _fname(f, "tr"),
                    "floor_en":       _fname(f, "en"),
                    "x":              cx,
                    "y":              cy,
                    "description":    entry["desc_en"],
                    "description_tr": entry["desc_tr"],
                    "all_states":     entry["all_states"],
                })
    else:
        for f in sorted(fc):
            floor_cells = [(f, x, y) for (x, y) in fc[f]]
            components  = _floor_components(floor_cells)
            rep = max(components, key=lambda c: c["size"])
            result.append({
                "id":             f"{char}_{f}_{rep['x']}_{rep['y']}",
                "name":           poi.name_en if poi else char,
                "name_tr":        poi.name_tr if poi else char,
                "floor":          f,
                "floor_tr":       _fname(f, "tr"),
                "floor_en":       _fname(f, "en"),
                "x":              rep["x"],
                "y":              rep["y"],
                "description":    "",
                "description_tr": "",
                "all_states":     [{"floor": f, "x": c["x"], "y": c["y"]}
                                   for c in components],
            })
    return result


def _llm_normalise(query: str) -> str:
    """Use LLM to extract a clean, searchable destination name from a free-text query.
    Returns the normalised string, or the original query on any failure."""
    if not (_llm_ready and _llm_client):
        return query
    try:
        data = _llm_client.json_chat([
            {"role": "system", "content": _RESOLVE_SYSTEM},
            {"role": "user",   "content": query},
        ], max_tokens=64)
        dest = (data.get("destination") or "").strip()
        return dest if dest else query
    except Exception:
        return query


@app.route("/api/resolve", methods=["POST"])
def api_resolve():
    body  = request.json or {}
    query = body.get("query", "").strip()
    ctx   = body.get("ctx", "dest")   # 'start' | 'dest'
    if not query:
        return jsonify({"ok": False, "error": "empty"})

    # LLM normalises the query → canonical searchable name
    resolve_query = _llm_normalise(query)

    res = _res.resolve(resolve_query)

    # If LLM output didn't resolve, also try the raw query as fallback
    if res.confidence == "failed" and resolve_query != query:
        res = _res.resolve(query)

    if res.confidence == "failed":
        return jsonify({"ok": False, "failed": True, "query": query})

    if res.confidence == "ambiguous":
        sug = _res.suggest(resolve_query, 5)
        return jsonify({
            "ok": False, "ambiguous": True,
            "suggestions": [
                {"char": s.char, "name_tr": s.name_tr, "name_en": s.name_en,
                 "icon": POI_REGISTRY[s.char].icon if s.char in POI_REGISTRY else "map-pin"}
                for s in sug if s.char
            ],
        })

    char  = res.char
    poi   = POI_REGISTRY.get(char)
    cells = _index.cells(char)
    lbs   = _index.labeled_by_char(char)

    # When resolver matched a specific named instance, narrow lbs to only
    # those states so the caller doesn't see all instances of that type.
    if res.confidence == "named" and res.alternatives:
        alt_set = set(res.alternatives)
        lbs_for_response = [lp for lp in lbs if lp.state in alt_set]
        if not lbs_for_response:
            lbs_for_response = lbs  # fallback — should not happen
    else:
        lbs_for_response = lbs

    # Representative state
    if res.confidence == "named" and res.alternatives:
        rep = res.alternatives[0]
    elif cells:
        sf, sx, sy = DEFAULT_START
        rep = min(cells,
                  key=lambda g: math.sqrt((g[1]-sx)**2 + (g[2]-sy)**2) + abs(g[0]-sf) * 100)
    else:
        rep = None

    return jsonify({
        "ok":      True,
        "char":    char,
        "name_tr": res.name_tr,
        "name_en": res.name_en,
        "icon":    poi.icon if poi else "map-pin",
        "state":   {"floor": rep[0], "x": rep[1], "y": rep[2]} if rep else None,
        "labeled": _resolve_labeled(lbs_for_response, cells, char, poi, ctx),
    })


@app.route("/api/navigate", methods=["POST"])
def api_navigate():
    data = request.json or {}

    # ── Start ───────────────────────────────────────────────────────────────
    s = data.get("start") or {}
    raw_sf = s.get("floor", DEFAULT_START[0])
    raw_sx = s.get("x",     DEFAULT_START[1])
    raw_sy = s.get("y",     DEFAULT_START[2])
    start_char = s.get("char")

    # Snap start to nearest actual map cell if labeled position is off-map.
    # Search same floor first; if empty (e.g. char only exists on other floors),
    # fall back to all floors with a large floor-distance penalty.
    if start_char:
        all_char_cells = list(_index.cells(start_char))
        same_floor = [(f, x, y) for (f, x, y) in all_char_cells if f == raw_sf]
        raw_start = (raw_sf, raw_sx, raw_sy)
        if same_floor and raw_start in set(same_floor):
            start = raw_start          # already on a valid cell
        elif same_floor:
            start = min(same_floor,
                        key=lambda c: (c[1]-raw_sx)**2 + (c[2]-raw_sy)**2)
        elif all_char_cells:
            # POI doesn't exist on the default floor — pick nearest across all floors
            start = min(all_char_cells,
                        key=lambda c: (c[1]-raw_sx)**2 + (c[2]-raw_sy)**2 + abs(c[0]-raw_sf)*10000)
        else:
            start = raw_start
    else:
        start = (raw_sf, raw_sx, raw_sy)

    start_name_tr = s.get("name_tr", "Ana Giriş")
    start_name_en = s.get("name_en", "Main Entrance")

    # ── Destination ─────────────────────────────────────────────────────────
    d = data.get("destination") or {}
    if not d:
        return jsonify({"ok": False, "error": "no destination"})

    dest_char       = d.get("char")
    dest_state      = d.get("state")       # {floor, x, y}
    dest_all_states = d.get("all_states")  # [{floor, x, y}, …] – çok kapılı POI
    dest_tr         = d.get("name_tr", "Hedef")
    dest_en         = d.get("name_en", "Destination")

    if dest_all_states:
        raw_goals = [(s["floor"], s["x"], s["y"]) for s in dest_all_states]
    elif dest_state:
        raw_goals = [(dest_state["floor"], dest_state["x"], dest_state["y"])]
    elif dest_char:
        goals = _index.cells(dest_char)
        raw_goals = None
    else:
        return jsonify({"ok": False, "error": "no destination char or state"})

    # Snap labeled coordinates to actual walkable map cells.
    # poi_labels.json positions may sit just outside the POI boundary — if so,
    # fall back to all real map cells of dest_char on those same floors.
    if raw_goals is not None:
        if dest_char:
            requested_floors = {g[0] for g in raw_goals}
            actual = [(f, x, y) for (f, x, y) in _index.cells(dest_char)
                      if f in requested_floors]
            goals = actual if actual else raw_goals
        else:
            goals = raw_goals

    if not goals:
        return jsonify({"ok": False,
                        "error_tr": "Hedef bina içinde bulunamadı.",
                        "error_en": "Destination not found in building."})

    # ── Compute route (fastest profile, fixed) ───────────────────────────────
    pid = data.get("profile", "fastest")
    if pid not in _PROFILES:
        pid = "fastest"
    routes = []
    try:
        r = _run_route(start, list(goals), pid)
        if r:
            routes.append(r)
        else:
            routes.append({**ROUTE_META[pid], "available": False,
                           "reason_tr": "Rota bulunamadı.",
                           "reason_en": "No route found."})
    except Exception as e:
        routes.append({**ROUTE_META[pid], "available": False,
                       "reason_tr": f"Hata: {e}", "reason_en": f"Error: {e}"})

    return jsonify({
        "ok": True,
        "start":       {"floor": start[0], "x": start[1], "y": start[2],
                        "name_tr": start_name_tr, "name_en": start_name_en},
        "destination": {"name_tr": dest_tr, "name_en": dest_en},
        "routes":      routes,
    })


# ── Explore endpoint helpers ──────────────────────────────────────────────────

_OFFICE_GROUPS = [
    ("professor",  {"tr": "Profesör Ofisleri",        "en": "Professor Offices"}),
    ("researcher", {"tr": "Araştırmacı Ofisleri",     "en": "Researcher Offices"}),
    ("postdoc",    {"tr": "Postdok Araştırmacılar",   "en": "Postdoctoral Researchers"}),
    ("phd",        {"tr": "Doktora Öğrenci Ofisleri", "en": "PhD Student Offices"}),
    ("academic",   {"tr": "Akademik Destek",          "en": "Academic Support"}),
    ("visitor",    {"tr": "Misafir Araştırmacılar",   "en": "Visiting Researchers"}),
    ("admin",      {"tr": "İdari Ofisler",            "en": "Administrative Offices"}),
]

# Named group for each POI char in multi-char categories.
# Single-char categories (T, U, O) are handled separately.
_CHAR_GROUPS: dict = {
    "N": ("main_entrance", {"tr": "Ana Girişler",           "en": "Main Entrances"}),
    "X": ("fire_exit",     {"tr": "Yangın Çıkışları",       "en": "Fire Exits"}),
    "R": ("reception",     {"tr": "Resepsiyon",             "en": "Reception"}),
    "F": ("cafe",          {"tr": "Kafeler",                "en": "Cafes"}),
    "j": ("dining_hall",   {"tr": "Yemekhaneler",           "en": "Dining Halls"}),
    "H": ("lecture",       {"tr": "Amfiler",                "en": "Lecture Theatres"}),
    "M": ("seminar",       {"tr": "Seminer Odaları",        "en": "Seminar Rooms"}),
    "G": ("teaching_lab",  {"tr": "Öğretim Labları",        "en": "Teaching Labs"}),
    "C": ("computer_lab",  {"tr": "Bilgisayar Labları",     "en": "Computer Labs"}),
    "e": ("conference",    {"tr": "Konferans Odaları",      "en": "Conference Rooms"}),
    "J": ("bio_lab",       {"tr": "Biyoloji Labları",       "en": "Biology Labs"}),
    "L": ("shared_lab",    {"tr": "Paylaşımlı Lablar",      "en": "Shared Labs"}),
    "P": ("support_lab",   {"tr": "Destek Labları",         "en": "Support Labs"}),
    "I": ("imaging",       {"tr": "Görüntüleme Birimleri",  "en": "Imaging Suites"}),
    "K": ("ep_testing",    {"tr": "EP Test Odaları",        "en": "EP Testing Rooms"}),
    "W": ("workshop",      {"tr": "Atölyeler",              "en": "Workshops"}),
    "B": ("breakout",      {"tr": "Dinlenme Alanları",      "en": "Breakout Spaces"}),
    "Z": ("study_space",   {"tr": "Çalışma Alanları",       "en": "Study Spaces"}),
    "A": ("group_study",   {"tr": "Grup Çalışma Odaları",   "en": "Group Study Rooms"}),
    "V": ("courtyard",     {"tr": "Avlular",                "en": "Courtyards"}),
    "Q": ("atrium",        {"tr": "Atrium Terasları",       "en": "Atrium Terraces"}),
    "D": ("terrace",       {"tr": "Teraslar",               "en": "Terraces"}),
    "q": ("glasshouse",    {"tr": "Seralar",                "en": "Glasshouses"}),
    "Y": ("herbarium",     {"tr": "Herbaryum",              "en": "Herbarium"}),
    "z": ("plant_room",    {"tr": "Tesisat Odaları",        "en": "Plant Rooms"}),
}


_ADMIN_KEYWORDS = {"manager", "coordinator", "administrator", "security",
                   "ethics", "compliance", "data office"}


def _office_group_key(name: str) -> str:
    nl = name.lower()
    if nl.startswith("prof."):
        return "professor"
    if nl.startswith("dr."):
        return "researcher"
    if "postdoctoral" in nl:
        return "postdoc"
    if "phd student" in nl:
        return "phd"
    if "supervisor" in nl or "mentor" in nl:
        return "academic"
    if "visiting researcher" in nl:
        return "visitor"
    if any(kw in nl for kw in _ADMIN_KEYWORDS):
        return "admin"
    return "_other"



@app.route("/api/explore")
def api_explore():
    cats_out = []
    for cat in CATEGORIES:
        types_out = []
        for char in cat["chars"]:
            poi = POI_REGISTRY.get(char)
            if not poi:
                continue
            lps     = _index.labeled_by_char(char)
            deduped = _dedup_labeled(lps, poi)
            if not deduped:
                # No labeled instances — one synthetic entry per floor from raw cells
                raw = _index.cells(char)
                if not raw:
                    continue
                fc: dict = {}
                for (f, x, y) in raw:
                    fc.setdefault(f, []).append((x, y))
                for f in sorted(fc):
                    coords = fc[f]
                    mx = sum(c[0] for c in coords) // len(coords)
                    my = sum(c[1] for c in coords) // len(coords)
                    rx, ry = min(coords, key=lambda c: (c[0]-mx)**2 + (c[1]-my)**2)
                    deduped.append({
                        "id":          f"{char}_{f}_{rx}_{ry}",
                        "name":        poi.name_en,
                        "name_tr":     poi.name_tr,
                        "floor":       f,
                        "floor_tr":    _fname(f, "tr"),
                        "floor_en":    _fname(f, "en"),
                        "x":           rx,
                        "y":           ry,
                        "description": "",
                        "all_states":  [{"floor": f, "x": rx, "y": ry}],
                    })

            is_office = (char == "O")

            # Build groups
            if is_office:
                named_keys = {key for key, _ in _OFFICE_GROUPS}
                group_map  = {key: [] for key, _ in _OFFICE_GROUPS}
                ungrouped  = []
                for inst in deduped:
                    gk = _office_group_key(inst["name"])
                    if gk in named_keys:
                        group_map[gk].append(inst)
                    else:
                        ungrouped.append(inst)

                groups_out = []
                if ungrouped:
                    groups_out.append({
                        "key": "_all", "name_tr": "", "name_en": "",
                        "instances": ungrouped,
                    })
                for key, labels in _OFFICE_GROUPS:
                    instances = group_map.get(key, [])
                    if not instances:
                        continue
                    groups_out.append({
                        "key":       key,
                        "name_tr":   labels["tr"],
                        "name_en":   labels["en"],
                        "instances": instances,
                    })

            elif char in _CHAR_GROUPS:
                gk, labels = _CHAR_GROUPS[char]
                groups_out = [{
                    "key":       gk,
                    "name_tr":   labels["tr"],
                    "name_en":   labels["en"],
                    "instances": deduped,
                }]

            else:
                groups_out = [{
                    "key":       "_all",
                    "name_tr":   poi.name_tr,
                    "name_en":   poi.name_en,
                    "instances": deduped,
                }]

            types_out.append({
                "char":    char,
                "icon":    poi.icon,
                "name_tr": poi.name_tr,
                "name_en": poi.name_en,
                "groups":  groups_out,
            })

        if types_out:
            cats_out.append({
                "id":      cat["id"],
                "icon":    cat["icon"],
                "name_tr": cat["name_tr"],
                "name_en": cat["name_en"],
                "types":   types_out,
            })

    return jsonify({
        "categories": cats_out,
        "floor_tr":   FLOOR_TR,
        "floor_en":   FLOOR_EN,
    })


# ── Info endpoint helpers ─────────────────────────────────────────────────────

_LANDMARKS = {
    'N': {'tr': 'Ana Giriş',     'en': 'Main Entrance'},
    'R': {'tr': 'Resepsiyon',    'en': 'Reception'},
    'F': {'tr': 'Kafe',          'en': 'Cafe'},
    'H': {'tr': 'Amfi',          'en': 'Lecture Theatre'},
    'M': {'tr': 'Seminer Odası', 'en': 'Seminar Room'},
    'Y': {'tr': 'Herbaryum',     'en': 'Herbarium'},
    'q': {'tr': 'Sera',          'en': 'Glasshouse'},
}

_MAX_LANDMARK_DIST = 40


def _quadrant_desc(cx: int, cy: int, n_cols: int, n_rows: int, lang: str) -> str:
    """Always returns one of four compass labels based on floor halves (always unique per quadrant)."""
    h = ("batı",  "west")  if cx < n_cols // 2 else ("doğu",  "east")
    v = ("kuzey", "north") if cy < n_rows // 2 else ("güney", "south")
    return f"{v[0]}-{h[0]} tarafında" if lang == "tr" else f"{v[1]}-{h[1]} side"


def _nearby_description(floor: int, cx: int, cy: int, lang: str, skip_char: str = "") -> str:
    """Return a human-readable nearby-landmark phrase for a given cell."""
    floor_name = _fname(floor, lang)
    grid = _map[floor]
    n_rows = len(grid)
    n_cols = len(grid[0]) if n_rows else 0

    # Scan for landmark chars, track min distance per char
    min_dist: dict = {}
    for y in range(n_rows):
        for x in range(n_cols):
            ch = grid[y][x]
            if ch in _LANDMARKS and ch != skip_char:
                d = abs(x - cx) + abs(y - cy)
                if d <= _MAX_LANDMARK_DIST:
                    if ch not in min_dist or d < min_dist[ch][0]:
                        min_dist[ch] = (d, x, y)

    # Sort by distance, take top 2
    closest = sorted(min_dist.items(), key=lambda kv: kv[1][0])[:2]

    quad = _quadrant_desc(cx, cy, n_cols, n_rows, lang)

    if not closest:
        if lang == "tr":
            return f"{floor_name} katında, {quad}"
        else:
            return f"On the {floor_name} floor, {quad}"

    landmark_names = [_LANDMARKS[ch][lang] for ch, _ in closest]

    if lang == "tr":
        joined = " ve ".join(landmark_names) if len(landmark_names) <= 2 \
            else ", ".join(landmark_names[:-1]) + " ve " + landmark_names[-1]
        return f"{floor_name} katında, {joined} yakınında ({quad})"
    else:
        joined = " and ".join(landmark_names) if len(landmark_names) <= 2 \
            else ", ".join(landmark_names[:-1]) + " and " + landmark_names[-1]
        return f"On the {floor_name} floor, near the {joined} ({quad})"


@app.route("/api/info", methods=["POST"])
def api_info():
    body  = request.json or {}
    query = body.get("query", "").strip()
    lang  = body.get("lang", "tr")

    if not query:
        return jsonify({"ok": False, "failed": True})

    res = _res.resolve(query)

    if res.confidence == "failed":
        return jsonify({"ok": False, "failed": True})

    char = res.char
    poi  = POI_REGISTRY.get(char)
    lps  = _filter_lps(_index.labeled_by_char(char), res)

    locations = []

    if lps:
        deduped = _dedup_labeled(lps, poi)
        for inst in deduped:
            f, x, y = inst["floor"], inst["x"], inst["y"]
            locations.append({
                "name":        inst["name"],
                "name_tr":     inst["name_tr"],
                "floor":       f,
                "floor_tr":    inst["floor_tr"],
                "floor_en":    inst["floor_en"],
                "char":        char,
                "x":           x,
                "y":           y,
                "nearby_tr":   _nearby_description(f, x, y, "tr", skip_char=char),
                "nearby_en":   _nearby_description(f, x, y, "en", skip_char=char),
                "description": inst["description"],
                "open_hours":  inst.get("open_hours", ""),
                "all_states":  inst["all_states"],
            })
    else:
        # Unlabeled – one entry per floor (first cell on that floor)
        cells = _index.cells(char)
        floors_seen = {}
        for (f, x, y) in cells:
            if f not in floors_seen:
                floors_seen[f] = (x, y)
        for f in sorted(floors_seen):
            x, y = floors_seen[f]
            locations.append({
                "name":        poi.name_en if poi else char,
                "name_tr":     poi.name_tr if poi else char,
                "floor":       f,
                "floor_tr":    _fname(f, "tr"),
                "floor_en":    _fname(f, "en"),
                "char":        char,
                "x":           x,
                "y":           y,
                "nearby_tr":   _nearby_description(f, x, y, "tr", skip_char=char),
                "nearby_en":   _nearby_description(f, x, y, "en", skip_char=char),
                "description": "",
                "all_states":  [{"floor": f, "x": x, "y": y}],
            })

    return jsonify({
        "ok":      True,
        "char":    char,
        "name_tr": res.name_tr,
        "name_en": res.name_en,
        "icon":    poi.icon if poi else "map-pin",
        "locations": locations,
    })


@app.route("/api/ask", methods=["POST"])
def api_ask():
    """LLM-destekli (yoksa kural tabanlı) chatbot endpoint'i."""
    body    = request.json or {}
    query   = body.get("query", "").strip()
    lang    = body.get("lang", "tr")
    history = body.get("history", [])   # [{role, content}, ...]
    # Sanitize: keep only valid roles, cap at last 10 messages
    history = [m for m in history if m.get("role") in ("user", "assistant") and m.get("content")][-10:]

    if not query:
        return jsonify({"ok": False, "text": ""})

    # ── Hedef çözümle (LLM varsa daha iyi anlama) ───────────────
    dest_query = query
    if _llm_ready and _llm_parser:
        try:
            parsed = _llm_parser.parse(query, history=history)
            dest_query = parsed.destination or query
        except Exception:
            pass

    res = _res.resolve(dest_query)
    if res.confidence == "failed" and dest_query != query:
        res = _res.resolve(query)   # orijinal sorguyla tekrar dene

    # ── Belirsiz eşleşme ─────────────────────────────────────────
    if res.confidence == "ambiguous":
        # History varsa LLM bağlamı anlasın; yoksa soru sor
        if _llm_ready and _llm_client and history:
            if lang == "tr":
                sys_msg = (
                    "BuildingPath bina rehber asistanısın. "
                    "Kullanıcı konuşma geçmişine bakarak sorusunu yorumla ve yardımcı ol. "
                    "Eğer kastettiği yer belirsizse nazikçe hangi yeri kastettiğini sor. "
                    "Uydurma, sadece bağlamdan çıkarabildiğin bilgileri kullan. Kısa yanıtla."
                )
            else:
                sys_msg = (
                    "You are a BuildingPath building guide assistant. "
                    "Interpret the user's question using the conversation history and help them. "
                    "If what they mean is still unclear, politely ask which place they mean. "
                    "Do not invent details. Keep it brief."
                )
            try:
                messages = [{"role": "system", "content": sys_msg}]
                messages += history[:-1]
                messages.append({"role": "user", "content": query})
                text = _llm_client.chat(messages, temperature=0.4, max_tokens=200)
                return jsonify({"ok": True, "text": text, "locations": [], "llm_used": True})
            except Exception:
                pass
        note = res.note or ""
        text = (f"Birden fazla farklı yer eşleşti. Hangisini kastettiniz? {note}"
                if lang == "tr" else
                f"Multiple places matched. Which did you mean? {note}")
        return jsonify({"ok": True, "text": text, "locations": []})

    # ── Eşleşme bulunamadı ───────────────────────────────────────
    if res.confidence == "failed":
        if _llm_ready and _llm_client:
            _building_summary_tr = (
                "Bina 6 kattan oluşuyor: Alt Zemin (0), Zemin (1), 1. Kat (2), 2. Kat (3), 3. Kat (4), 4. Kat (5). "
                "Binada şunlar bulunuyor: ofisler (profesör, araştırmacı, postdok, doktora öğrenci, akademik destek, "
                "misafir araştırmacı, idari ofisler), derslikler/amfiler, seminer odaları, bilgisayar labları, "
                "öğretim labları, biyoloji labları, resepsiyon, kafe, yemekhane, tuvaletler, çalışma alanları, "
                "konferans odaları, atölyeler."
            )
            _building_summary_en = (
                "The building has 6 floors: Lower Ground (0), Ground (1), First (2), Second (3), Third (4), Fourth (5). "
                "It contains: offices (professor, researcher, postdoc, PhD student, academic support, "
                "visiting researcher, administrative), lecture theatres, seminar rooms, computer labs, "
                "teaching labs, biology labs, reception, cafe, dining hall, toilets, study spaces, "
                "conference rooms, workshops."
            )
            sys_msg = (
                "BuildingPath bina rehber asistanısın. "
                "Kullanıcının niyetini anlayarak, aşağıdaki bina bilgilerini kullanarak yönlendir. "
                "Kesin bilmiyorsan açıkça belirt, uydurma. Kısa yanıtla.\n\n"
                f"Bina bilgisi: {_building_summary_tr}"
                if lang == "tr" else
                "You are a BuildingPath building guide assistant. "
                "Understand the user's intent and guide them using the building information below. "
                "If you don't know something for certain, say so — do not invent details. Keep it brief.\n\n"
                f"Building info: {_building_summary_en}"
            )
            try:
                messages = [{"role": "system", "content": sys_msg}]
                messages += history[:-1]   # önceki alışverişler (son user hariç)
                messages.append({"role": "user", "content": query})
                text = _llm_client.chat(messages, temperature=0.4, max_tokens=200)
                return jsonify({"ok": True, "text": text, "locations": [], "llm_used": True})
            except Exception:
                pass
        fail = (f"'{query}' bulunamadı. Başka bir ifadeyle deneyin."
                if lang == "tr" else
                f"Could not find '{query}'. Please try a different phrase.")
        return jsonify({"ok": False, "text": fail})

    # ── Konum listesi ────────────────────────────────────────────
    char = res.char
    poi  = POI_REGISTRY.get(char)
    lps  = _filter_lps(_index.labeled_by_char(char), res)

    locations = []
    if lps:
        for inst in _dedup_labeled(lps, poi):
            f, x, y = inst["floor"], inst["x"], inst["y"]
            locations.append({
                "name":        inst["name"],
                "name_tr":     inst["name_tr"],
                "floor":       f,
                "floor_tr":    inst["floor_tr"],
                "floor_en":    inst["floor_en"],
                "char":        char,
                "x": x, "y": y,
                "nearby_tr":   _nearby_description(f, x, y, "tr", skip_char=char),
                "nearby_en":   _nearby_description(f, x, y, "en", skip_char=char),
                "description": inst["description"],
                "open_hours":  inst.get("open_hours", ""),
                "all_states":  inst["all_states"],
            })
    else:
        seen = {}
        for (f, x, y) in _index.cells(char):
            seen.setdefault(f, (x, y))
        for f in sorted(seen):
            x, y = seen[f]
            locations.append({
                "name":        poi.name_en if poi else char,
                "name_tr":     poi.name_tr if poi else char,
                "floor":       f,
                "floor_tr":    _fname(f, "tr"),
                "floor_en":    _fname(f, "en"),
                "char":        char,
                "x": x, "y": y,
                "nearby_tr":   _nearby_description(f, x, y, "tr", skip_char=char),
                "nearby_en":   _nearby_description(f, x, y, "en", skip_char=char),
                "description": "",
                "all_states":  [{"floor": f, "x": x, "y": y}],
            })

    # ── Erişilebilirlik notu (asansör/merdiven sorgusu için) ─────────
    access_prefix = ""
    if _has_access_query(query) and char:
        access_prefix = _access_note(char, lang) + "\n\n"

    # ── Yanıt metni ──────────────────────────────────────────────
    poi_name = res.name_tr if lang == "tr" else res.name_en

    if _llm_ready and _llm_client and locations:
        # Build location text for LLM.
        # Offices: group by type so LLM can match the user's role/need.
        # Other large sets: floor-level summary so LLM sees ALL floors.
        if len(locations) > 3 and char == "O":
            # Group office locations by type (postdoc, professor, phd, etc.)
            type_floors: dict = {}   # group_key -> [floor_name, ...]
            type_labels: dict = {}   # group_key -> display label
            for loc in locations:
                gk = _office_group_key(loc["name"])
                fname = loc["floor_tr"] if lang == "tr" else loc["floor_en"]
                if gk not in type_floors:
                    type_floors[gk] = []
                    for key, labels in _OFFICE_GROUPS:
                        if key == gk:
                            type_labels[gk] = labels["tr"] if lang == "tr" else labels["en"]
                            break
                    else:
                        type_labels[gk] = loc["name_tr"] if lang == "tr" else loc["name"]
                if fname not in type_floors[gk]:
                    type_floors[gk].append(fname)
            header = "Binadaki ofis türleri ve bulundukları katlar:" if lang == "tr" else "Office types in the building and their floors:"
            loc_lines = [f"- {type_labels[gk]}: {', '.join(type_floors[gk])}"
                         for gk in type_floors]
            loc_text = header + "\n" + "\n".join(loc_lines)
        elif len(locations) > 3:
            floor_counts: dict = {}
            for loc in locations:
                fname = loc["floor_tr"] if lang == "tr" else loc["floor_en"]
                floor_counts[fname] = floor_counts.get(fname, 0) + 1
            unit = "yer" if lang == "tr" else "room(s)"
            loc_lines = [f"- {fname}: {cnt} {unit}"
                         for fname, cnt in floor_counts.items()]
            # Derive specific label when named instances are filtered
            if res.alternatives and locations:
                first = locations[0]["name_tr"] if lang == "tr" else locations[0]["name"]
                parts = first.rsplit(' ', 1)
                type_label = parts[0] if len(parts) == 2 and parts[1].isdigit() else poi_name
            else:
                type_label = (res.name_tr if lang == "tr" else res.name_en) or poi_name
            loc_text = f"{type_label}:\n" + "\n".join(loc_lines)
        else:
            loc_lines = []
            for loc in locations:
                n = loc["name_tr"] if lang == "tr" else loc["name"]
                floor = loc["floor_tr"] if lang == "tr" else loc["floor_en"]
                nearby = loc["nearby_tr"] if lang == "tr" else loc["nearby_en"]
                hours = loc.get("open_hours", "")
                desc = loc.get("description", "")
                line = f"- {n} ({floor}): {nearby}"
                if hours:
                    line += f"\n  Saatler: {hours}" if lang == "tr" else f"\n  Hours: {hours}"
                if desc:
                    line += f"\n  Açıklama: {desc}" if lang == "tr" else f"\n  Info: {desc}"
                loc_lines.append(line)
            loc_text = "\n".join(loc_lines)

        if lang == "tr":
            sys_msg = (
                "BuildingPath bina rehber asistanısın. "
                "Kullanıcının kim olduğunu (öğrenci, araştırmacı, akademisyen vb.) ve "
                "ne yapmak istediğini anlayarak, verilen konum bilgilerinden en uygun seçeneği öner. "
                "Açık saatler veya müsaitlik sorulursa doğrudan 'Saatler' verisinden yanıtla. "
                "Sadece verilen bilgileri kullan, uydurma. "
                "Belirsizse birden fazla seçenek sun. "
                "Kısa ve samimi Türkçeyle yanıtla, 2-3 cümle yeter."
            )
            user_msg = f"Soru: {query}\n\n{access_prefix}Konum bilgileri:\n{loc_text}"
        else:
            sys_msg = (
                "You are a BuildingPath building guide assistant. "
                "Understand the user's role (student, researcher, academic, etc.) and intent, "
                "then recommend the most relevant specific location from the data below. "
                "If the user asks about open hours or availability, answer directly from the 'Hours' field. "
                "Use ONLY the provided data — do not invent details. "
                "If uncertain, list the relevant options. 2-3 sentences is enough."
            )
            user_msg = f"Question: {query}\n\n{access_prefix}Location data:\n{loc_text}"
        try:
            messages = [{"role": "system", "content": sys_msg}]
            messages += history[:-1]   # önceki alışverişler (son user hariç)
            messages.append({"role": "user", "content": user_msg})
            text = _llm_client.chat(messages, temperature=0.4, max_tokens=200)
            return jsonify({"ok": True, "text": text, "locations": locations,
                            "char": char, "llm_used": True})
        except Exception:
            pass

    # Kural tabanlı yanıt
    icon = poi.icon if poi else "map-pin"

    # Derive specific display name from filtered instance names
    # Only strip trailing number when names follow "Type N" pattern (e.g., "Biyoloji Destek Lab 1")
    if res.alternatives and locations:
        _fname_first = locations[0]["name_tr"] if lang == "tr" else locations[0]["name"]
        _fp = _fname_first.rsplit(' ', 1)
        display_name = _fp[0] if len(_fp) == 2 and _fp[1].isdigit() else poi_name
    else:
        display_name = poi_name

    generic_name_tr = (res.name_tr or "").lower()
    generic_name_en = (res.name_en or "").lower()

    def _loc_label(loc):
        if lang == "tr":
            n = loc["name_tr"]
            return n if n and n.lower() != generic_name_tr else ""
        else:
            n = loc["name"]
            return n if n and n.lower() != generic_name_en else ""

    if len(locations) == 1:
        loc = locations[0]
        label = _loc_label(loc) or display_name
        near = loc["nearby_tr"] if lang == "tr" else loc["nearby_en"]
        text = f"{icon} <strong>{label}</strong>: {near}"

    elif len(locations) <= 5:
        suffix = "konumda" if lang == "tr" else "location(s)"
        header = f"{icon} <strong>{display_name}</strong> — {len(locations)} {suffix}:"
        lines = [header]
        for loc in locations:
            n = _loc_label(loc)
            near = loc["nearby_tr"] if lang == "tr" else loc["nearby_en"]
            prefix = f"<strong>{n}</strong>: " if n else ""
            lines.append(f"• {prefix}{near}")
        text = "<br>".join(lines)

    else:
        # Floor count summary for many locations
        fc: dict = {}
        for loc in locations:
            fname = loc["floor_tr"] if lang == "tr" else loc["floor_en"]
            fc[fname] = fc.get(fname, 0) + 1
        total = len(locations)
        if lang == "tr":
            header = f"{icon} <strong>{display_name}</strong> — toplam {total} yer:"
            lines = [header] + [f"• {fname}: {cnt} yer" for fname, cnt in fc.items()]
        else:
            header = f"{icon} <strong>{display_name}</strong> — {total} location(s):"
            lines = [header] + [f"• {fname}: {cnt} {'room' if cnt == 1 else 'rooms'}"
                                 for fname, cnt in fc.items()]
        text = "<br>".join(lines)

    return jsonify({"ok": True, "text": text, "locations": locations,
                    "char": char, "llm_used": False})


@app.route("/api/floor-map/<int:floor>")
def api_floor_map(floor):
    """Return a labeled base map (no route) for the given floor."""
    img_b64 = _draw_route(floor, [], "#1565C0")
    return jsonify({"ok": True, "image": img_b64})


@app.route("/api/map-image", methods=["POST"])
def api_map_image():
    d         = request.json or {}
    floor_idx = d.get("floor", 1)
    path_pts  = d.get("path_points", [])
    color     = d.get("color", "#1565C0")
    start_pt  = d.get("start_point")
    end_pt    = d.get("end_point")
    trans_pts = d.get("transition_points", [])

    img_b64 = _draw_route(floor_idx, path_pts, color,
                          start_pt=start_pt, end_pt=end_pt, trans_pts=trans_pts)
    return jsonify({"ok": True, "image": img_b64})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\n  → Open  http://localhost:{port}\n")
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
