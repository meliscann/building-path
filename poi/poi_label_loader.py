"""
poi_label_loader.py
─────────────────────────────────────────────────────────────
poi_labels.json dosyasını okur, koordinatları haritaya göre
doğrular ve LabeledPOI nesneleri üretir.

Kullanım:
    from poi_label_loader import load_poi_labels, LabeledPOI

    labels = load_poi_labels(campus_map)
    for poi in labels:
        print(poi.name, poi.state)   # (floor, x, y)
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

LABELS_FILE = os.path.join(os.path.dirname(__file__), "poi_labels.json")


# ─────────────────────────────────────────────────────────────
# DATA CLASS
# ─────────────────────────────────────────────────────────────

@dataclass
class LabeledPOI:
    """
    Tek bir isimlendirilmiş POI örneği.

    Attributes
    ----------
    state       : (floor, x, y) — haritadaki koordinat
    char        : grid karakteri ('O', 'H', ...)
    name        : İngilizce görünen isim ("Prof. Smith's Office")
    name_tr     : Türkçe görünen isim ("Prof. Smith'in Ofisi")
    tags        : arama etiketleri ["biology", "staff"]
    capacity    : kapasite (opsiyonel, amfiler için)
    description : kısa açıklama (opsiyonel)
    """
    state       : Tuple[int, int, int]
    char        : str
    name        : str
    name_tr     : str                   = ""
    tags        : List[str]             = field(default_factory=list)
    capacity    : Optional[int]         = None
    description    : str                = ""
    description_tr : str                = ""
    open_hours     : str                = ""

    @property
    def floor(self) -> int:   return self.state[0]
    @property
    def x(self)     -> int:   return self.state[1]
    @property
    def y(self)     -> int:   return self.state[2]

    def matches_query(self, query: str) -> bool:
        """
        Sorgu bu POI'nin adıyla, Türkçe adıyla veya etiketleriyle
        eşleşiyor mu? Büyük/küçük harf duyarsız.
        """
        q = query.lower()
        if q in self.name.lower():
            return True
        if self.name_tr and q in self.name_tr.lower():
            return True
        if any(q in tag.lower() for tag in self.tags):
            return True
        return False


# ─────────────────────────────────────────────────────────────
# LOADER
# ─────────────────────────────────────────────────────────────

class LabelValidationError(Exception):
    pass


def load_poi_labels(campus_map,
                    path: str = LABELS_FILE,
                    strict: bool = False) -> List[LabeledPOI]:
    """
    JSON dosyasını okur ve doğrulanmış LabeledPOI listesi döndürür.

    Parameters
    ----------
    campus_map : 3-D grid
    path       : poi_labels.json dosyasının yolu
    strict     : True → geçersiz giriş exception fırlatır
                 False → geçersiz girişi atlar, uyarı basar (varsayılan)

    Returns
    -------
    List[LabeledPOI]
        Geçerli ve haritada bulunan tüm etiketlenmiş POI'lar.
    """
    if not os.path.exists(path):
        return []

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    n_floors = len(campus_map)
    n_rows   = len(campus_map[0])
    n_cols   = len(campus_map[0][0])

    labeled = []
    errors  = []

    for entry in data.get("pois", []):
        # Zorunlu alanlar
        try:
            floor = int(entry["floor"])
            x     = int(entry["x"])
            y     = int(entry["y"])
            char  = str(entry["char"])
            name  = str(entry["name"])
        except (KeyError, ValueError) as e:
            msg = f"Eksik/hatalı alan: {entry} → {e}"
            errors.append(msg)
            if strict:
                raise LabelValidationError(msg)
            print(f"  ⚠️  [poi_labels] {msg}")
            continue

        # Sınır kontrolü
        if not (0 <= floor < n_floors and
                0 <= x    < n_cols  and
                0 <= y    < n_rows):
            msg = (f"'{name}': koordinat ({floor},{x},{y}) harita sınırları dışında "
                   f"(floors={n_floors}, cols={n_cols}, rows={n_rows})")
            errors.append(msg)
            if strict:
                raise LabelValidationError(msg)
            print(f"  ⚠️  [poi_labels] {msg}")
            continue

        labeled.append(LabeledPOI(
            state       = (floor, x, y),
            char        = char,
            name        = name,
            name_tr     = entry.get("name_tr", ""),
            tags        = entry.get("tags", []),
            capacity    = entry.get("capacity"),
            description    = entry.get("description", ""),
            description_tr = entry.get("description_tr", ""),
            open_hours     = entry.get("open_hours", "") or "",
        ))

    return labeled


# ─────────────────────────────────────────────────────────────
# QUICK SUMMARY
# ─────────────────────────────────────────────────────────────

def print_label_summary(labels: List[LabeledPOI]):
    """Yüklenmiş etiketlerin özet tablosunu yazdırır."""
    if not labels:
        print("  (Etiketlenmiş POI bulunamadı)")
        return

    FLOOR_NAMES = ["Lower Ground", "Ground", "First",
                   "Second", "Third", "Fourth"]

    print(f"\n  {'Char':<6} {'Kat':<15} {'Koordinat':<12} {'İsim'}")
    print("  " + "─" * 65)
    for poi in labels:
        fname = FLOOR_NAMES[poi.floor] if poi.floor < len(FLOOR_NAMES) else f"F{poi.floor}"
        cap   = f" (cap:{poi.capacity})" if poi.capacity else ""
        print(f"  '{poi.char}'   {fname:<15} ({poi.x:>3},{poi.y:>3})       {poi.name}{cap}")
    print()
