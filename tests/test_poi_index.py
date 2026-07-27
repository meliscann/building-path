# test_poi_index.py
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.building_data import build_campus_map
from poi.poi_index import build_poi_index

campus_map = build_campus_map()
index = build_poi_index(campus_map)

index.print_summary(floor_names=["LG", "GF", "F1", "F2", "F3", "F4"])

# Belirli sorgular
print("Ofis hücreleri (toplam):", len(index.cells("O")))
print("2. kattaki ofisler:", len(index.cells_on_floor("O", floor=2)))
print("Erişilebilir lift hücreleri:", len(index.cells("A")))
print("Kısıtlı POI'lar:", index.restricted_chars())
