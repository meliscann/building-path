"""
floor_configs.py
─────────────────────────────────────────────────────────────
Tüm kat renk eşlemeleri ve yapılandırmaları.

Yapı:
  - GLOBAL_COLORS   : Tüm katlarda aynı anlama gelen renkler
  - FLOOR_CONFIGS   : Her kata özgü renkler + görsel yolu
  - get_color_map() : Birleşik renk haritasını döndürür
"""

# ─────────────────────────────────────────────────────────────
# KARAKTER REHBERİ
# ─────────────────────────────────────────────────────────────
# #  → Duvar / erişime kapalı alan
# '.'→ Koridor (nokta)
# S  → Merdiven (Stairs)
# E  → Asansör (Elevator)
# A  → Grup çalışma odası (Group study room)
# N  → Ana giriş (Main entrance)
# X  → Yangın çıkışı (Fire exit)
# V  → Avlu (Courtyard)
# T  → Tuvalet & duş (Toilets & showers)
# O  → Ofis (Office)
# P  → Destek laboratuvarı (Support laboratories)
# K  → EP testing
# W  → Atölye (Workshops)
# L  → Paylaşımlı laboratuvar (Shared laboratory)
# I  → Görüntüleme odası (Imaging suite)
# U  → Kütüphane (Library)
# M  → Seminer odası (Seminar room)
# C  → Bilgisayar laboratuvarı (Computer laboratories)
# H  → Amfi (Lecture theatre)
# B  → Dinlenme alanı (Breakout space)
# G  → Öğretim laboratuvarı (Teaching lab)
# Z  → Çalışma alanı (Study space)
# Y  → Herbaryum (Herbarium)
# F  → Kafe (Cafe)
# R  → Resepsiyon (Reception)
# J  → Biyoloji laboratuvarı (Biology labs)
# Q  → Atrium terası (Atrium terrace)
# D  → Teras (Terrace)
# q  → Seralar (Glasshouses)
# j  → Yemekhane (Dining hall)
# z  → Tesisat odası (Plant room)
# e  → Konferans odası (Conference room)
# ─────────────────────────────────────────────────────────────


def hex_to_rgb(hex_str):
    """'ff0000' → (255, 0, 0)"""
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ─────────────────────────────────────────────────────────────
# GLOBAL: Tüm katlarda aynı renk = aynı anlam
# ─────────────────────────────────────────────────────────────
GLOBAL_COLORS = [
    {"hex": "000000", "rgb": hex_to_rgb("000000"), "char": "#",  "name": "Wall"},
    {"hex": "ffecb3", "rgb": hex_to_rgb("ffecb3"), "char": ".",  "name": "Corridor"},
    {"hex": "ffc107", "rgb": hex_to_rgb("ffc107"), "char": "S",  "name": "Stairs"},
    {"hex": "76ff03", "rgb": hex_to_rgb("76ff03"), "char": "E",  "name": "Elevator"},
    {"hex": "464646", "rgb": hex_to_rgb("464646"), "char": "V",  "name": "Courtyard"},
    {"hex": "9e9e9e", "rgb": hex_to_rgb("9e9e9e"), "char": "T",  "name": "Toilets & Showers"},
    {"hex": "03a9f4", "rgb": hex_to_rgb("03a9f4"), "char": "O",  "name": "Offices"},
    {"hex": "d500f9", "rgb": hex_to_rgb("d500f9"), "char": "P",  "name": "Support Laboratories"},
    {"hex": "e91e63", "rgb": hex_to_rgb("e91e63"), "char": "K",  "name": "EP Testing"},
    {"hex": "9e9d24", "rgb": hex_to_rgb("9e9d24"), "char": "B",  "name": "Breakout Space"},
    {"hex": "ed9dce", "rgb": hex_to_rgb("ed9dce"), "char": "J",  "name": "Biology Laboratories"},
    {"hex": "dce775", "rgb": hex_to_rgb("dce775"), "char": "Q",  "name": "Atrium Terrace"},
    {"hex": "ff8135", "rgb": hex_to_rgb("ff8135"), "char": "D",  "name": "Terrace"},
    {"hex": "928fb8", "rgb": hex_to_rgb("928fb8"), "char": "F",  "name": "Cafe"},
    {"hex": "d50000", "rgb": hex_to_rgb("d50000"), "char": "N",  "name": "Main Entrance"},
    {"hex": "e65100", "rgb": hex_to_rgb("e65100"), "char": "X",  "name": "Fire Exit"},
    {"hex": "8d6e63", "rgb": hex_to_rgb("8d6e63"), "char": "A",  "name": "Group Study Room"},
]

# ─────────────────────────────────────────────────────────────
# KAT-SPESİFİK RENKLER
# ─────────────────────────────────────────────────────────────
_LOWER_GROUND_COLORS = [
    {"hex": "e57373", "rgb": hex_to_rgb("e57373"), "char": "W",  "name": "Workshops"},
    {"hex": "f48fb1", "rgb": hex_to_rgb("f48fb1"), "char": "L",  "name": "Shared Laboratory"},
    {"hex": "b388ff", "rgb": hex_to_rgb("b388ff"), "char": "I",  "name": "Imaging Suite"},
    {"hex": "5d4037", "rgb": hex_to_rgb("5d4037"), "char": "U",  "name": "Library"},
    {"hex": "009688", "rgb": hex_to_rgb("009688"), "char": "M",  "name": "Seminar Room"},
    {"hex": "69f0ae", "rgb": hex_to_rgb("69f0ae"), "char": "C",  "name": "Computer Laboratories"},
    {"hex": "1b5e20", "rgb": hex_to_rgb("1b5e20"), "char": "H",  "name": "Lecture Theatre"},
]

_GROUND_COLORS = [
    {"hex": "3f51b5", "rgb": hex_to_rgb("3f51b5"), "char": "G",  "name": "Teaching Lab"},
    {"hex": "004d40", "rgb": hex_to_rgb("004d40"), "char": "Z",  "name": "Study Space"},
    {"hex": "b2ebf2", "rgb": hex_to_rgb("b2ebf2"), "char": "Y",  "name": "Herbarium"},
    {"hex": "ffab91", "rgb": hex_to_rgb("ffab91"), "char": "R",  "name": "Reception"},
    # Cafe (928fb8) zaten global'de
]

_FIRST_FLOOR_COLORS = [
    {"hex": "5d4037", "rgb": hex_to_rgb("5d4037"), "char": "U",  "name": "Library"},
    # Biology labs, Atrium terrace, EP testing, vb. global'de
]

_SECOND_FLOOR_COLORS = [
    # Tüm renkler global veya önceki katlarda tanımlı
]

_THIRD_FLOOR_COLORS = [
    # Terrace (ff8135) global'de
]

_FOURTH_FLOOR_COLORS = [
    {"hex": "ff4f9b", "rgb": hex_to_rgb("ff4f9b"), "char": "q",  "name": "Glasshouses"},
    {"hex": "429058", "rgb": hex_to_rgb("429058"), "char": "j",  "name": "Dining Hall"},
    {"hex": "9ed795", "rgb": hex_to_rgb("9ed795"), "char": "z",  "name": "Plant Room"},
    {"hex": "6200ea", "rgb": hex_to_rgb("6200ea"), "char": "e",  "name": "Conference Room"},
]

# ─────────────────────────────────────────────────────────────
# KAT YAPILANDIRMALARI
# ─────────────────────────────────────────────────────────────
FLOOR_CONFIGS = {
    "lower_ground": {
        "image":        "lower-ground-floor.png",
        "floor_index":  0,
        "extra_colors": _LOWER_GROUND_COLORS,
    },
    "ground": {
        "image":        "ground-floor.png",
        "floor_index":  1,
        "extra_colors": _GROUND_COLORS,
    },
    "first": {
        "image":        "first-floor.png",
        "floor_index":  2,
        "extra_colors": _FIRST_FLOOR_COLORS,
    },
    "second": {
        "image":        "second-floor.png",
        "floor_index":  3,
        "extra_colors": _SECOND_FLOOR_COLORS,
    },
    "third": {
        "image":        "third-floor.png",
        "floor_index":  4,
        "extra_colors": _THIRD_FLOOR_COLORS,
    },
    "fourth": {
        "image":        "fourth-floor.png",
        "floor_index":  5,
        "extra_colors": _FOURTH_FLOOR_COLORS,
    },
}


def get_color_map(floor_name):
    """
    Belirtilen kat için birleşik renk haritası döndürür.
    Global renkler her zaman önce gelir — çakışma durumunda
    global renk önceliklidir.
    """
    floor_cfg = FLOOR_CONFIGS[floor_name]
    return GLOBAL_COLORS + floor_cfg["extra_colors"]
