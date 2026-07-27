"""
find_poi_coords.py
─────────────────────────────────────────────────────────────
Belirli bir POI türünün tüm hücrelerini listeler.

Grid visualizer'da PNG açıp koordinatı bulmak için:
  1. PNG'yi bir görüntü editöründe aç
  2. Fareyle istediğin hücrenin üstüne gel
  3. Editörün gösterdiği piksel koordinatını CELL_SIZE'a (4) böl
     → grid x = piksel_x / 4
     → grid y = piksel_y / 4

Kullanım:
    python find_poi_coords.py O            # tüm ofisler
    python find_poi_coords.py H            # tüm amfiler
    python find_poi_coords.py O --floor 1  # 1. kattaki ofisler
    python find_poi_coords.py O --floor 1 --region 40 80 20 50
        # x: 40-80, y: 20-50 arasındaki ofisler
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.building_data import build_campus_map

FLOOR_NAMES = ["Lower Ground", "Ground", "First", "Second", "Third", "Fourth"]
CELL_SIZE   = 4   # grid_visualizer.py'deki varsayılan ölçek


def find_poi_coords(campus_map, char, floor_filter=None,
                    x_min=None, x_max=None, y_min=None, y_max=None):
    results = []
    for f, floor in enumerate(campus_map):
        if floor_filter is not None and f != floor_filter:
            continue
        for y, row in enumerate(floor):
            for x, cell in enumerate(row):
                if cell != char:
                    continue
                if x_min is not None and not (x_min <= x <= x_max):
                    continue
                if y_min is not None and not (y_min <= y <= y_max):
                    continue
                # PNG piksel koordinatı (CELL_SIZE varsayılanıyla)
                px = x * CELL_SIZE
                py = y * CELL_SIZE
                results.append((f, x, y, px, py))
    return results


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return

    char         = args[0]
    floor_filter = None
    x_min = x_max = y_min = y_max = None

    if "--floor" in args:
        i = args.index("--floor")
        floor_filter = int(args[i + 1])

    if "--region" in args:
        i = args.index("--region")
        x_min, x_max, y_min, y_max = (int(args[i+1]), int(args[i+2]),
                                       int(args[i+3]), int(args[i+4]))

    campus_map = build_campus_map()
    results    = find_poi_coords(campus_map, char, floor_filter,
                                 x_min, x_max, y_min, y_max)

    if not results:
        print(f"'{char}' karakteri bulunamadı.")
        return

    fname = f"Floor filter: {FLOOR_NAMES[floor_filter]}" if floor_filter is not None else "Tüm katlar"
    print(f"\nPOI: '{char}'  |  {fname}  |  {len(results)} hücre bulundu")
    print()
    print(f"  {'Kat':<16} {'Grid (x,y)':<14} {'PNG piksel (x,y)':<18} JSON girişi")
    print("  " + "─" * 75)

    for f, x, y, px, py in results:
        floor_name = FLOOR_NAMES[f] if f < len(FLOOR_NAMES) else f"Floor {f}"
        json_entry = f'{{"floor":{f},"x":{x},"y":{y},"char":"{char}","name":"..."}}'
        print(f"  {floor_name:<16} ({x:>3},{y:>3})       PNG: ({px:>4},{py:>4})     {json_entry}")

    print()
    print("💡 PNG'de koordinat bulmak için:")
    print("   Piksel koordinatını 4'e böl → grid koordinatı")
    print("   Örnek: PNG (120, 80) → grid x=30, y=20")


if __name__ == "__main__":
    main()
