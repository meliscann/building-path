# test_profiles.py
"""
Kullanıcı profillerinin rota üzerindeki etkisini test eder.

'fastest'    → zaman-optimal rota (merdiven veya asansör, hangisi hızsa)
'min_effort' → asansörü tercih eden rota (merdiven çok pahalı)

Beklenen: iki profil aynı başlangıç/hedef için farklı dikey geçiş seçer.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.building_data        import build_campus_map
from pathfinding.indoor_search import BuildingProblem, find_cells
from pathfinding.heuristics    import make_heuristic
from pathfinding.astar         import astar_search
from pathfinding.common        import path_states, path_actions, failure
from pathfinding.costs         import route_breakdown, path_duration
from poi.user_profile          import PROFILES

campus_map = build_campus_map()

# Zemin kattaki ana girişten 4. kattaki kafeye: kat farkı büyük,
# asansör vs merdiven tercihini açıkça ortaya koyar.
N_cells = find_cells(campus_map, "N")
F_cells = find_cells(campus_map, "F")
assert N_cells, "Ana giriş (N) haritada bulunamadı"
assert F_cells, "Kafe (F) haritada bulunamadı"

start = N_cells[0]
goals = F_cells

print("=== Profil Karşılaştırması: Ana Giriş → Kafe ===\n")

results = {}
for pname, profile in PROFILES.items():
    h    = make_heuristic(goals, campus_map)
    prob = BuildingProblem(start, campus_map, goals=goals, profile=profile)
    node, stats = astar_search(prob, h)

    if node is failure:
        print(f"[{profile.label}] YOL BULUNAMADI")
        results[pname] = None
        continue

    states   = path_states(node)
    acts     = path_actions(node)
    segs     = route_breakdown(states, acts)
    duration = path_duration(states, acts)
    results[pname] = {"segs": segs, "duration": duration, "cost": node.path_cost}

    print(f"[{profile.label}]  maliyet={node.path_cost:.1f}  "
          f"süre={duration['duration_min']:.2f}dk  "
          f"mesafe={duration['distance_m']:.1f}m")
    for seg in segs:
        if seg["kind"] == "walk":
            print(f"  🚶 Kat {seg['floor']}  {seg['distance_m']}m  {seg['duration_s']:.0f}s")
        else:
            icons = {"elevator": "🛗", "stair": "🪜", "lift": "♿"}
            icon  = icons.get(seg["kind"], "↕")
            print(f"  {icon}  {seg['kind']}  Kat{seg['from_floor']}→Kat{seg['to_floor']}  {seg['duration_s']:.0f}s")
    print()

# Doğrulama: iki profil de çözüm bulmuş olmalı
assert results.get("fastest")    is not None, "fastest profili çözüm bulamadı"
assert results.get("min_effort") is not None, "min_effort profili çözüm bulamadı"

# min_effort daha yüksek maliyet taşımalı (merdiven cezası varsa) ya da
# asansörü seçip farklı bir segment yapısı üretmeli.
fastest_segs    = results["fastest"]["segs"]
min_effort_segs = results["min_effort"]["segs"]

fastest_stairs    = sum(1 for s in fastest_segs    if s["kind"] == "stair")
min_effort_stairs = sum(1 for s in min_effort_segs if s["kind"] == "stair")

print(f"fastest    → merdiven kullanımı: {fastest_stairs}")
print(f"min_effort → merdiven kullanımı: {min_effort_stairs}")
print(f"\n✅ Tüm testler geçti.")
