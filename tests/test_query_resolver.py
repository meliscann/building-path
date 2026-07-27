# test_query_resolver.py
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.building_data import build_campus_map
from poi.poi_index      import build_poi_index
from poi.query_resolver import QueryResolver

index    = build_poi_index(build_campus_map())
resolver = QueryResolver(index)

test_queries = [
    # Türkçe
    "tuvalet", "en yakın tuvalet", "wc",
    "kafe", "en yakın kafe",
    "amfi", "seminer odası",
    "bilgisayar lab", "engelli asansörü",
    # İngilizce
    "toilet", "nearest toilet",
    "cafe", "lecture theatre",
    "computer lab",
    # Kısmi eşleşme
    "lab", "asansör",
    # Başarısız olması gereken
    "xyz", "bilinmeyen bir yer",
]

for q in test_queries:
    r = resolver.resolve(q)
    status = "✅" if r.char else "❌"
    print(f"{status} '{q}' → {r.char} ({r.name_en}) [{r.confidence}]")
