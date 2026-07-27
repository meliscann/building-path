"""
poi_index.py
─────────────────────────────────────────────────────────────
POI (Point of Interest) registry for the Oxford LaMB building.

Builds a structured index from the campus grid once at startup,
then provides fast lookup without repeated full-grid scans.

Each POI type has:
  - character code  (as used in the ASCII grid)
  - display name    (English)
  - display name TR (Turkish)
  - floor presence  (which floors it appears on)
  - cell list       (all (floor, x, y) positions)
  - access level    ("public" | "restricted" | "accessible_only")

Access levels
-------------
public            Anyone can be routed to this POI.
restricted        Requires staff/student ID — excluded from public routing.
                  (Reserved for future use; no POIs currently restricted.)
accessible_only   Reserved for users with mobility needs (e.g. accessible lift).
                  Standard users are not routed to these cells.

Usage
-----
    from poi_index import build_poi_index, POIIndex

    index = build_poi_index(campus_map)

    # All office cells
    offices = index.cells("O")

    # All toilets on floor 1
    toilets_f1 = index.cells_on_floor("T", floor=1)

    # Summary table
    index.print_summary()
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .poi_label_loader import LabeledPOI


# ─────────────────────────────────────────────────────────────
# POI METADATA REGISTRY
# ─────────────────────────────────────────────────────────────

@dataclass
class POIType:
    """Static metadata for one POI category."""
    char         : str
    name_en      : str
    name_tr      : str
    access_level : str = "public"    # "public" | "restricted" | "accessible_only"
    icon         : str = "map-pin"


# Master list of all POI types in the LaMB building
POI_REGISTRY: Dict[str, POIType] = {

    # ── Infrastructure ────────────────────────────────────────
    ".": POIType(".", "Corridor",          "Koridor",           icon="footprints"),
    "N": POIType("N", "Main entrance",     "Ana giriş",         icon="door-open"),
    "X": POIType("X", "Fire exit",         "Yangın çıkışı",     icon="flame"),
    "T": POIType("T", "Toilets",           "Tuvalet",           icon="droplets"),
    "V": POIType("V", "Courtyard",         "Avlu",              icon="trees"),

    # ── Vertical circulation ──────────────────────────────────
    "S": POIType("S", "Stairs",            "Merdiven",          icon="trending-up"),
    "E": POIType("E", "Elevator",          "Asansör",           icon="arrow-up-down"),

    # ── Study & work spaces ───────────────────────────────────
    "O": POIType("O", "Office",            "Ofis",              icon="briefcase"),
    "B": POIType("B", "Breakout space",    "Dinlenme alanı",    icon="armchair"),
    "Z": POIType("Z", "Study space",       "Çalışma alanı",     icon="book-open"),
    "A": POIType("A", "Group study room",  "Grup çalışma odası",icon="users"),

    # ── Teaching & learning ───────────────────────────────────
    "H": POIType("H", "Lecture theatre",   "Amfi",              icon="presentation"),
    "M": POIType("M", "Seminar room",      "Seminer odası",     icon="users-round"),
    "G": POIType("G", "Teaching lab",      "Öğretim lab",       icon="flask-conical"),
    "C": POIType("C", "Computer lab",      "Bilgisayar lab",    icon="monitor"),
    "e": POIType("e", "Conference room",   "Konferans odası",   icon="video"),

    # ── Research labs ─────────────────────────────────────────
    "J": POIType("J", "Biology lab",       "Biyoloji lab",      icon="dna"),
    "P": POIType("P", "Support lab",       "Destek lab",        icon="test-tube"),
    "K": POIType("K", "EP testing",        "EP test odası",     icon="activity"),
    "L": POIType("L", "Shared lab",        "Paylaşımlı lab",    icon="microscope"),
    "I": POIType("I", "Imaging suite",     "Görüntüleme birimi",icon="scan"),
    "W": POIType("W", "Workshop",          "Atölye",            icon="wrench"),

    # ── Specialist spaces ─────────────────────────────────────
    "Y": POIType("Y", "Herbarium",         "Herbaryum",         icon="leaf"),
    "q": POIType("q", "Glasshouse",        "Sera",              icon="sun"),
    "z": POIType("z", "Plant room",        "Tesisat odası",     icon="settings-2"),

    # ── Public amenities ──────────────────────────────────────
    "F": POIType("F", "Cafe",              "Kafe",              icon="coffee"),
    "R": POIType("R", "Reception",         "Resepsiyon",        icon="bell-ring"),

    # ── Outdoor / special ────────────────────────────────────
    "Q": POIType("Q", "Atrium terrace",    "Atrium terası",     icon="sun"),
    "D": POIType("D", "Terrace",           "Teras",             icon="cloud-sun"),

    # ── Library ───────────────────────────────────────────────
    "U": POIType("U", "Library",           "Kütüphane",         icon="book-marked"),

    # ── Dining ────────────────────────────────────────────────
    "j": POIType("j", "Dining hall",       "Yemekhane",         icon="utensils"),
}


# ─────────────────────────────────────────────────────────────
# POI INDEX
# ─────────────────────────────────────────────────────────────

@dataclass
class POIIndex:
    """
    Runtime index of all POI cells in the campus grid.

    Built once from the campus map by build_poi_index().
    Labeled instances (from poi_labels.json) stored in _labeled.
    """
    _cells  : Dict[str, List[Tuple[int, int, int]]] = field(default_factory=dict)
    _labeled: list = field(default_factory=list)   # List[LabeledPOI]

    def load_labels(self, campus_map) -> None:
        """Load poi_labels.json and attach named instances."""
        from .poi_label_loader import load_poi_labels
        self._labeled = load_poi_labels(campus_map)

    def labeled(self):
        """All named POI instances."""
        return list(self._labeled)

    def search_labeled(self, query: str):
        """Search named instances by name, Turkish name, or tag."""
        return [p for p in self._labeled if p.matches_query(query)]

    def labeled_by_char(self, char: str):
        """All named instances of a specific POI type."""
        return [p for p in self._labeled if p.char == char]

    def cells(self, char: str) -> List[Tuple[int, int, int]]:
        """All cells of the given POI type across all floors."""
        return self._cells.get(char, [])

    def cells_on_floor(self, char: str, floor: int
                       ) -> List[Tuple[int, int, int]]:
        """Cells of a POI type on a specific floor."""
        return [(f, x, y) for (f, x, y) in self.cells(char) if f == floor]

    def all_chars(self) -> List[str]:
        """All POI characters present in the map."""
        return [c for c in self._cells if self._cells[c]]

    def poi_type(self, char: str) -> Optional[POIType]:
        """Return POIType metadata for a character code, or None."""
        return POI_REGISTRY.get(char)

    def public_chars(self) -> List[str]:
        """POI characters accessible to all users (access_level == 'public')."""
        return [c for c in self.all_chars()
                if POI_REGISTRY.get(c, POIType(c, c, c)).access_level == "public"]

    def restricted_chars(self) -> List[str]:
        """POI characters with restricted access."""
        return [c for c in self.all_chars()
                if POI_REGISTRY.get(c, POIType(c, c, c)).access_level
                   in ("restricted", "accessible_only")]

    def print_summary(self, floor_names=None):
        """Print a formatted table of POI counts per floor."""
        n_floors = max(
            (f for cells in self._cells.values() for (f, _, _) in cells),
            default=0
        ) + 1

        if floor_names is None:
            floor_names = [f"F{i}" for i in range(n_floors)]

        chars = sorted(self.all_chars(), key=lambda c: c if c != " " else "~")

        # Header
        floor_cols = "  ".join(f"{floor_names[f][:6]:>6}" for f in range(n_floors))
        print(f"\n  {'Ch':<4} {'Name':<22} {'Access':<16} {floor_cols}  {'Total':>6}")
        print("  " + "─" * (4 + 22 + 16 + n_floors * 8 + 8))

        for char in chars:
            poi = POI_REGISTRY.get(char)
            name   = poi.name_en if poi else f"[{char}]"
            access = poi.access_level if poi else "unknown"
            total  = len(self._cells.get(char, []))
            by_floor = "  ".join(
                f"{len(self.cells_on_floor(char, f)):>6}"
                for f in range(n_floors)
            )
            flag = " ⚠️" if access != "public" else ""
            print(f"  {repr(char):<4} {name:<22} {access:<16} {by_floor}  {total:>6}{flag}")

        print()


# ─────────────────────────────────────────────────────────────
# BUILDER
# ─────────────────────────────────────────────────────────────

def build_poi_index(campus_map) -> POIIndex:
    """
    Scan the campus grid once and return a populated POIIndex.

    Parameters
    ----------
    campus_map : list[list[list[str]]]
        3-D grid: campus_map[floor][y][x]

    Returns
    -------
    POIIndex
    """
    cells: Dict[str, List[Tuple[int, int, int]]] = {}

    for f, floor in enumerate(campus_map):
        for y, row in enumerate(floor):
            for x, ch in enumerate(row):
                if ch == "#":
                    continue   # walls never indexed
                cells.setdefault(ch, []).append((f, x, y))

    return POIIndex(_cells=cells)
