"""
manual_overrides.py
─────────────────────────────────────────────────────────────
Otomatik renk tespitinin güvenilir olmadığı küçük POI'lar
için manuel koordinat tanımları.

Koordinatlar orijinal piksel haritasındaki (x, y) değerleridir.
Görselini editörde açıp üzerine gidince koordinatı görebilirsin.

Ekleme formatı:
    {"x": <piksel_x>, "y": <piksel_y>, "char": "<harf>", "name": "<isim>"}
"""

MANUAL_OVERRIDES = {
    "lower_ground": [],
    "ground": [],
    "first": [],
    "second": [],
    "third": [],
    "fourth": [],
}
