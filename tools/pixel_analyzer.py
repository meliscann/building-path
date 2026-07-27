"""
Harita görselindeki her rengin piksel sayısını analiz eder.
Manuel override gerekip gerekmediğini söyler.
"""

from PIL import Image
import numpy as np
from collections import Counter
import sys
from pathlib import Path

# Görsellerin bulunduğu klasör (proje kökündeki maps/ dizini)
_ROOT    = Path(__file__).resolve().parent.parent
MAPS_DIR = _ROOT / "maps"

# ─── Eşik değerleri ───────────────────────────────────────────
MANUAL_THRESHOLD   = 6   # Bu değerin ALTINDA → kesinlikle manuel
WARNING_THRESHOLD  = 15  # Bu değerin altında → riskli, kontrol et
# ──────────────────────────────────────────────────────────────

# Bilinen renk eşlemesi (hex → kategori adı)
KNOWN_COLORS = {
    "000000": "Wall",
    "ffecb3": "Corridor",
    "ffc107": "Stairs",
    "76ff03": "Elevator",
    "880e4f": "Accessible Lift",
    "d50000": "Main Entrance",
    "e65100": "Fire Exit",
    "464646": "Courtyard",
    "9e9e9e": "Toilets & Showers",
    "03a9f4": "Office",
    "d500f9": "Support Laboratories",
    "e91e63": "EP Testing",
    "e57373": "Workshops",
    "f48fb1": "Shared Laboratory",
    "b388ff": "Imaging Suite",
    "5d4037": "Unallocated Space",
    "009688": "Seminar Room",
    "69f0ae": "Computer Laboratories",
    "1b5e20": "Lecture Theatre",
    "9e9d24": "Breakout Space",
    "3f51b5": "Teaching Lab",
    "004d40": "Study Space",
    "b2ebf2": "Herbarium",
    "928fb8": "Cafe",
    "ffab91": "Reception",
    "ed9dce": "Biology Laboratories",
    "dce775": "Atrium Terrace",
    "ff8135": "Terrace",
    "ff4f9b": "Glasshouses",
    "429058": "Dining Hall",
    "9ed795": "Plant Room",
    "6200ea": "Conference Room",
    "ffff00": "Accessible Toilet",
    "8d6e63": "Group Study Room",
}

def rgb_to_hex(r, g, b):
    return f"{r:02x}{g:02x}{b:02x}"

def analyze(image_path):
    img = Image.open(image_path).convert("RGB")
    pixels = np.array(img).reshape(-1, 3)
    
    total_pixels = len(pixels)
    print(f"\n{'─'*60}")
    print(f"  Görsel: {image_path}")
    print(f"  Boyut: {img.width}x{img.height} = {total_pixels} piksel")
    print(f"{'─'*60}")
    
    # Piksel sayısını say
    counter = Counter(map(tuple, pixels))
    
    manual   = []
    warning  = []
    safe     = []
    unknown  = []
    
    for (r, g, b), count in sorted(counter.items(), key=lambda x: x[1]):
        hex_code = rgb_to_hex(r, g, b)
        name = KNOWN_COLORS.get(hex_code, None)
        pct = count / total_pixels * 100
        
        entry = (hex_code, name or "???", count, pct)
        
        if name is None:
            unknown.append(entry)
        elif count < MANUAL_THRESHOLD:
            manual.append(entry)
        elif count < WARNING_THRESHOLD:
            warning.append(entry)
        else:
            safe.append(entry)
    
    # ── Manuel override gerekli ──
    if manual:
        print(f"\n🔴 MANUEL OVERRIDE GEREKLİ (< {MANUAL_THRESHOLD} piksel):")
        for hex_code, name, count, pct in manual:
            print(f"   #{hex_code}  {name:<25} → {count} piksel")
    
    # ── Riskli ──
    if warning:
        print(f"\n🟡 RİSKLİ - Kontrol Et ({MANUAL_THRESHOLD}-{WARNING_THRESHOLD} piksel):")
        for hex_code, name, count, pct in warning:
            print(f"   #{hex_code}  {name:<25} → {count} piksel")
    
    # ── Güvenli ──
    print(f"\n✅ OTOMATİK GÜVENLİ (>= {WARNING_THRESHOLD} piksel):")
    for hex_code, name, count, pct in safe:
        print(f"   #{hex_code}  {name:<25} → {count:>6} piksel  ({pct:.1f}%)")
    
    # ── Bilinmeyen renkler ──
    if unknown:
        print(f"\n⚪ BİLİNMEYEN RENKLER (color map'e ekle):")
        for hex_code, name, count, pct in unknown:
            print(f"   #{hex_code}  {count:>6} piksel  ({pct:.1f}%)")
    
    print(f"\n{'─'*60}\n")
    
    return {
        "manual": manual,
        "warning": warning,
        "safe": safe,
        "unknown": unknown
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Argüman verilmezse maps/ klasöründeki tüm PNG'leri tara
        images = sorted(MAPS_DIR.glob("*.png"))
        if not images:
            print(f"maps/ klasöründe PNG görsel bulunamadı: {MAPS_DIR}")
            sys.exit(1)
        print(f"maps/ klasöründe {len(images)} görsel bulundu, analiz ediliyor...\n")
        for path in images:
            analyze(path)
    else:
        # Argüman verilirse: önce doğrudan dene, bulamazsan maps/ içinde ara
        for arg in sys.argv[1:]:
            path = Path(arg)
            if not path.exists():
                path = MAPS_DIR / arg
            if not path.exists():
                print(f"Görsel bulunamadı: {arg}")
                sys.exit(1)
            analyze(path)

