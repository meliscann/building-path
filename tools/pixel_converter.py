"""
pixel_converter.py
─────────────────────────────────────────────────────────────
Piksel haritalarını ASCII grid'e dönüştürür.

Kullanım:
    python pixel_converter.py                        # Tüm katlar
    python pixel_converter.py lower_ground ground    # Seçili katlar

Çıktı:
    building_data.py ← ASCII grid verileri
    conversion_log.txt ← Eşleşemeyen pikseller
"""

import sys
import math
from pathlib import Path
from PIL import Image

# Proje kökünü sys.path'e ekle (doğrudan çalıştırma için)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.floor_configs    import FLOOR_CONFIGS, get_color_map
from tools.manual_overrides import MANUAL_OVERRIDES

# Görsellerin bulunduğu klasör (proje kökündeki maps/ dizini)
MAPS_DIR = _ROOT / "maps"

# ─────────────────────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────────────────────
TOLERANCE       = 35    # RGB Öklid mesafesi eşiği
FALLBACK_CHAR   = "#"   # Eşleşmeyen piksel → duvar say
LOG_UNKNOWNS    = True  # Bilinmeyen renkleri logla
# ─────────────────────────────────────────────────────────────


def rgb_distance(c1, c2):
    """İki RGB tuple arasındaki Öklid mesafesi."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def match_pixel(pixel_rgb, color_map):
    """
    Pikseli renk haritasındaki en yakın renge eşler.
    Mesafe TOLERANCE'ı aşarsa FALLBACK_CHAR döner.
    """
    best_char = FALLBACK_CHAR
    best_dist = float("inf")

    for entry in color_map:
        dist = rgb_distance(pixel_rgb, entry["rgb"])
        if dist < best_dist:
            best_dist = dist
            best_char = entry["char"]

    if best_dist > TOLERANCE:
        return FALLBACK_CHAR, best_dist, True   # (char, dist, is_unknown)
    return best_char, best_dist, False


def convert_floor(floor_name, image_dir=None):
    """
    Tek bir katı dönüştürür.
    Döndürür: (grid: list[str], unknown_pixels: list[dict])
    """
    cfg       = FLOOR_CONFIGS[floor_name]
    base_dir  = Path(image_dir) if image_dir is not None else MAPS_DIR
    img_path  = base_dir / cfg["image"]
    color_map = get_color_map(floor_name)

    if not img_path.exists():
        print(f"  [HATA] Görsel bulunamadı: {img_path}")
        return None, []

    img    = Image.open(img_path).convert("RGB")
    width  = img.width
    height = img.height
    pixels = img.load()

    print(f"  Boyut: {width}x{height}")

    grid          = []
    unknown_pixels = []

    for y in range(height):
        row = []
        for x in range(width):
            pixel_rgb          = pixels[x, y]
            char, dist, is_unk = match_pixel(pixel_rgb, color_map)
            row.append(char)

            if is_unk and LOG_UNKNOWNS:
                unknown_pixels.append({
                    "floor": floor_name,
                    "x": x, "y": y,
                    "rgb": pixel_rgb,
                    "hex": "#{:02x}{:02x}{:02x}".format(*pixel_rgb),
                    "dist": round(dist, 1),
                })
        grid.append("".join(row))

    # Manuel override uygula
    overrides = MANUAL_OVERRIDES.get(floor_name, [])
    grid_list = [list(row) for row in grid]  # düzenlenebilir

    for ov in overrides:
        x, y = ov["x"], ov["y"]
        if 0 <= y < height and 0 <= x < width:
            grid_list[y][x] = ov["char"]
            print(f"  Override: ({x},{y}) → '{ov['char']}' ({ov['name']})")
        else:
            print(f"  [UYARI] Override koordinatı sınır dışı: ({x},{y}) — {ov['name']}")

    grid = ["".join(row) for row in grid_list]

    print(f"  Satır sayısı: {len(grid)}, Sütun sayısı: {len(grid[0]) if grid else 0}")
    if overrides:
        print(f"  {len(overrides)} manuel override uygulandı.")
    if unknown_pixels:
        print(f"  ⚠️  {len(unknown_pixels)} bilinmeyen piksel → '{FALLBACK_CHAR}' (duvar) sayıldı.")

    return grid, unknown_pixels


def write_building_data(all_grids, output_path="building_data.py"):
    """Tüm kat gridlerini building_data.py olarak yazar."""

    floor_var_names = {
        "lower_ground": "LOWER_GROUND",
        "ground":       "GROUND",
        "first":        "FIRST",
        "second":       "SECOND",
        "third":        "THIRD",
        "fourth":       "FOURTH",
    }

    lines = [
        '"""',
        "building_data.py",
        "─" * 60,
        "Piksel haritalarından otomatik üretilmiş ASCII grid verileri.",
        "",
        "KARAKTERLERİN ANLAMI:",
        "  #  → Duvar / erişime kapalı alan",
        "  '.'→ Koridor",
        "  S  → Merdiven          E  → Asansör",
        "  A  → Grup çalışma odası  N  → Ana giriş",
        "  X  → Yangın çıkışı     V  → Avlu",
        "  T  → Tuvalet           O  → Ofis",
        "  P  → Destek lab        K  → EP testing",
        "  W  → Atölye            L  → Paylaşımlı lab",
        "  I  → Görüntüleme       U  → Kütüphane",
        "  M  → Seminer           C  → Bilgisayar lab",
        "  H  → Amfi              B  → Dinlenme alanı",
        "  G  → Öğretim lab       Z  → Çalışma alanı",
        "  Y  → Herbaryum         F  → Kafe",
        "  R  → Resepsiyon        J  → Biyoloji lab",
        "  Q  → Atrium terası     D  → Teras",
        "  q  → Seralar           j  → Yemekhane",
        "  z  → Tesisat odası     e  → Konferans odası",
        '"""',
        "",
    ]

    var_list = []

    for floor_name, grid in all_grids.items():
        var_name = floor_var_names.get(floor_name, floor_name.upper())
        var_list.append(var_name)

        lines.append(f"{var_name} = [")
        for row in grid:
            escaped = row.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'    "{escaped}",')
        lines.append("]")
        lines.append("")

    # build_campus_map() fonksiyonu
    lines.append("")
    lines.append("def build_floor_from_strings(lines):")
    lines.append("    return [list(row) for row in lines]")
    lines.append("")
    lines.append("")
    lines.append("def build_campus_map():")
    floors_str = ", ".join(var_list)
    lines.append(f"    floors = [{floors_str}]")
    lines.append("    return [build_floor_from_strings(f) for f in floors]")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ '{output_path}' yazıldı ({len(all_grids)} kat).")


def write_log(all_unknowns, log_path="conversion_log.txt"):
    """Bilinmeyen pikselleri log dosyasına yazar."""
    if not any(all_unknowns.values()):
        print("✅ Bilinmeyen piksel yok, log dosyası oluşturulmadı.")
        return

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("DÖNÜŞTÜRME LOGU — Bilinmeyen Pikseller\n")
        f.write("=" * 60 + "\n\n")
        for floor_name, unknowns in all_unknowns.items():
            if not unknowns:
                continue
            f.write(f"[{floor_name.upper()}] — {len(unknowns)} piksel\n")
            f.write("-" * 40 + "\n")
            for u in unknowns:
                f.write(
                    f"  ({u['x']:>3},{u['y']:>3})  {u['hex']}  "
                    f"RGB{u['rgb']}  dist={u['dist']}\n"
                )
            f.write("\n")

    print(f"📋 Log: '{log_path}'")


def main():
    # Hangi katlar dönüştürülecek?
    valid_floors = list(FLOOR_CONFIGS.keys())
    if len(sys.argv) > 1:
        selected = [f for f in sys.argv[1:] if f in valid_floors]
        invalid  = [f for f in sys.argv[1:] if f not in valid_floors]
        if invalid:
            print(f"[UYARI] Tanımsız kat isimleri yok sayıldı: {invalid}")
            print(f"Geçerli isimler: {valid_floors}")
    else:
        selected = valid_floors

    print(f"\nDönüştürülecek katlar: {selected}\n")

    all_grids    = {}
    all_unknowns = {}

    for floor_name in selected:
        print(f"► {floor_name.upper()}")
        grid, unknowns = convert_floor(floor_name)
        if grid:
            all_grids[floor_name]    = grid
            all_unknowns[floor_name] = unknowns
        print()

    if all_grids:
        output_path = str(_ROOT / "data" / "building_data.py")
        log_path    = str(_ROOT / "conversion_log.txt")
        write_building_data(all_grids, output_path)
        write_log(all_unknowns, log_path)
    else:
        print("Hiçbir kat dönüştürülemedi.")


if __name__ == "__main__":
    main()
