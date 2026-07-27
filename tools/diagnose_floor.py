"""
diagnose_floor.py
Hangi hücrelerin ulaşılamaz olduğunu ve hangi karakterlere ait
olduklarını gösterir. Belirli bir katı analiz eder.
"""

import sys
from pathlib import Path
from collections import deque, Counter

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from data.building_data import build_campus_map

campus_map = build_campus_map()

FLOOR_NAMES = ["Lower Ground", "Ground", "First", "Second", "Third", "Fourth"]
ALL_DIR = [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1)]
VERTICAL = {'E', 'S', 'A'}

def find_start(campus_map):
    for f, floor in enumerate(campus_map):
        for y, row in enumerate(floor):
            for x, ch in enumerate(row):
                if ch == 'N':
                    return (f, x, y)
    # fallback
    for y, row in enumerate(campus_map[0]):
        for x, ch in enumerate(row):
            if ch != '#':
                return (0, x, y)

def bfs_all(campus_map, start):
    n_floors = len(campus_map)
    n_rows   = len(campus_map[0])
    n_cols   = len(campus_map[0][0])

    visited  = {start}
    frontier = deque([start])

    while frontier:
        f, x, y = frontier.popleft()
        for dx, dy in ALL_DIR:
            nx, ny = x+dx, y+dy
            if 0<=f<n_floors and 0<=nx<n_cols and 0<=ny<n_rows:
                if campus_map[f][ny][nx] != '#':
                    s = (f, nx, ny)
                    if s not in visited:
                        visited.add(s)
                        frontier.append(s)
        ch = campus_map[f][y][x]
        if ch in VERTICAL:
            for df in (+1, -1):
                nf = f + df
                if 0 <= nf < n_floors and campus_map[nf][y][x] != '#':
                    s = (nf, x, y)
                    if s not in visited:
                        visited.add(s)
                        frontier.append(s)

    return visited

# BFS
start   = find_start(campus_map)
visited = bfs_all(campus_map, start)

# 4. kat analizi (index 5)
TARGET_FLOOR = 1
floor        = campus_map[TARGET_FLOOR]
n_rows       = len(floor)
n_cols       = len(floor[0])

unreachable = []
for y in range(n_rows):
    for x in range(n_cols):
        ch = floor[y][x]
        if ch != '#' and (TARGET_FLOOR, x, y) not in visited:
            unreachable.append((x, y, ch))

print(f"\n{FLOOR_NAMES[TARGET_FLOOR]} Kat — Ulaşılamaz Hücreler")
print(f"Toplam ulaşılamaz: {len(unreachable)}\n")

# Hangi karakterler?
char_counts = Counter(ch for _,_,ch in unreachable)
print("Karakter dağılımı:")
NAMES = {
    ' ':'Koridor','S':'Merdiven','E':'Asansör','A':'Engelli asansörü',
    'O':'Ofis','P':'Destek lab','K':'EP testing','B':'Breakout',
    'J':'Bio lab','Q':'Atrium terası','D':'Teras','F':'Kafe',
    'W':'Atölye','L':'Paylaşımlı lab','I':'Görüntüleme',
    'U':'Tahsis edilmemiş','M':'Seminer','C':'Bilgisayar lab',
    'H':'Amfi','G':'Öğretim lab','Z':'Çalışma','Y':'Herbaryum',
    'R':'Resepsiyon','q':'Sera','j':'Yemekhane','z':'Tesisat odası',
    'e':'Konferans','N':'Ana giriş','X':'Yangın çıkışı',
    'V':'Avlu','T':'Tuvalet',
}
for ch, cnt in char_counts.most_common():
    print(f"  '{ch}' ({NAMES.get(ch,'?'):<20}) → {cnt} hücre")

# X koordinat aralığı (sol/sağ bölge analizi)
if unreachable:
    xs = [x for x,y,ch in unreachable]
    ys = [y for x,y,ch in unreachable]
    print(f"\nKoordinat aralığı:")
    print(f"  X: {min(xs)} → {max(xs)}")
    print(f"  Y: {min(ys)} → {max(ys)}")
    print(f"\nBu bölge haritanın {'sol' if max(xs) < n_cols//2 else 'sağ' if min(xs) > n_cols//2 else 'orta/tüm'} kısmında.")

# Ulaşılabilir merdiven/asansör var mı 4. katta?
print(f"\n{FLOOR_NAMES[TARGET_FLOOR]} Kattaki dikey geçiş noktaları:")
for y in range(n_rows):
    for x in range(n_cols):
        ch = floor[y][x]
        if ch in VERTICAL:
            reachable = (TARGET_FLOOR, x, y) in visited
            status = "✅ ulaşılabilir" if reachable else "❌ ulaşılamaz"
            print(f"  '{ch}' at ({x},{y}) → {status}")
