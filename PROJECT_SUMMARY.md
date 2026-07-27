# LaMB Navigator — Proje Özeti

> Oxford Life and Mind Building için çok katlı kapalı-alan navigasyon sistemi.  
> Flask web arayüzü + A* tabanlı yol bulma + POI yönetimi.

---

## 1. Projeye Genel Bakış

LaMB Navigator, Oxford Üniversitesi'nin Life and Mind Building (LaMB) binasını ASCII-grid haritası üzerinde temsil ederek kullanıcılara gerçek zamanlı navigasyon ve bina bilgisi sunan bir web uygulamasıdır. Proje hem pratik bir navigasyon aracı hem de arama algoritmalarının karşılaştırmalı analizine yönelik bir araştırma platformu olarak tasarlanmıştır.

### Temel Özellikler

- 6 katlı bina: Alt Zemin, Zemin, Birinci, İkinci, Üçüncü, Dördüncü
- Her kat 230×128 grid hücresi (1 hücre ≈ 0.32 m)
- 3 navigasyon profili: En Hızlı, En Az Efor, Engelsiz
- 168 isimlendirilmiş POI (İlgi Noktası)
- Çift dil desteği: Türkçe / İngilizce
- Harita üzerinde POI etiketleriyle görsel rota gösterimi

---

## 2. Proje Dosya Yapısı

```
analyzer/
├── app.py                          # Flask sunucusu (ana uygulama)
├── navigate.py                     # CLI navigasyon aracı
│
├── data/
│   ├── building_data.py            # build_campus_map() → 6 katlı 3D grid
│   ├── floor_configs.py            # Her katın PNG-to-grid renk eşlemeleri
│   └── manual_overrides.py         # Otomatik dönüşüm hatalarının manuel düzeltmeleri
│
├── pathfinding/
│   ├── common.py                   # Problem, Node, best_first_search (AIMA 4e)
│   ├── campus_search.py            # CampusProblem: durum uzayı + eylem modeli
│   ├── astar.py                    # A*, Ağırlıklı A*, UCS
│   ├── bfs.py                      # Genişlik Öncelikli Arama
│   ├── bidirectional_astar.py      # Çift Yönlü A*
│   ├── idastar.py                  # Yinelemeli Derinleşen A* (IDA*)
│   ├── theta_star.py               # Theta* (herhangi-açı yol planlaması)
│   ├── heuristics.py               # Kabul edilebilir sezgisel fonksiyonlar
│   ├── costs.py                    # Eylem maliyet modeli + gerçek dünya dönüşümü
│   └── main_search.py              # Algoritma karşılaştırma çerçevesi
│
├── poi/
│   ├── poi_index.py                # POIType, POI_REGISTRY, POIIndex, build_poi_index()
│   ├── poi_label_loader.py         # LabeledPOI, load_poi_labels()
│   ├── poi_labels.json             # 168 isimlendirilmiş POI tanımı
│   ├── query_resolver.py           # Metin sorgusundan POI'ya çözümleme
│   └── user_profile.py             # UserProfile: yasak eylemler + maliyet çarpanları
│
├── static/
│   ├── app.js                      # Vanilla JS SPA (durum makinesi)
│   └── style.css                   # Oxford Mavi temalı CSS
│
├── templates/
│   └── index.html                  # Tek sayfa HTML şablonu
│
├── tools/
│   ├── label_map.py                # 6 katlı etiketlenmiş PNG oluşturucu
│   ├── grid_visualizer.py          # Grid görselleştirme
│   ├── find_poi_coords.py          # POI koordinat bulucu
│   ├── pixel_analyzer.py           # PNG piksel renk analizi
│   ├── pixel_converter.py          # Piksel → grid koordinat dönüştürücü
│   ├── diagnose_floor.py           # Kat grid teşhis aracı
│   └── validate_map.py             # Harita tutarlılık doğrulama
│
├── maps/                           # Orijinal 230×128 PNG kat planları (koordinat kaynağı)
├── archive/old-maps/               # Arayüzde görüntülenen PNG'ler + arşiv algoritmalar
├── grid_visuals/                   # Renklendirilmiş grid görselleri
├── labeled_maps/                   # tools/label_map.py çıktısı (etiketli PNG'ler)
│
└── tests/
    ├── test_poi_index.py
    ├── test_profiles.py
    └── test_query_resolver.py
```

---

## 3. Veri Modeli

### 3.1 Grid Temsili

Binanın her katı `campus_map[floor][y][x]` biçiminde 3-boyutlu bir listede saklanır. Her hücre tek bir ASCII karakteriyle temsil edilir:

| Karakter | Alan | Kategori |
|----------|------|----------|
| `#` | Duvar | Altyapı |
| `.` | Koridor | Altyapı |
| `N` | Ana Giriş | Giriş/Çıkış |
| `X` | Yangın Çıkışı | Giriş/Çıkış |
| `S` | Merdiven | Dikey Dolaşım |
| `E` | Asansör | Dikey Dolaşım |
| `A` | Erişilebilir Lift | Dikey Dolaşım |
| `O` | Ofis | Çalışma |
| `B` | Dinlenme Alanı | Çalışma |
| `Z` | Çalışma Alanı | Çalışma |
| `r` | Grup Çalışma | Çalışma |
| `H` | Amfi | Eğitim |
| `M` | Seminer Odası | Eğitim |
| `G` | Öğretim Lab | Eğitim |
| `C` | Bilgisayar Lab | Eğitim |
| `e` | Konferans Odası | Eğitim |
| `J` | Biyoloji Lab | Araştırma |
| `P` | Destek Lab | Araştırma |
| `K` | EP Test Odası | Araştırma |
| `L` | Paylaşımlı Lab | Araştırma |
| `I` | Görüntüleme Birimi | Araştırma |
| `W` | Atölye | Araştırma |
| `F` | Kafe | Tesis |
| `T` | Tuvalet | Tesis |
| `a` | Engelli Tuvaleti | Tesis |
| `R` | Resepsiyon | Tesis |
| `Y` | Herbaryum | Özel |
| `V` | Avlu | Özel |
| `Q` | Atrium Terası | Özel |
| `D` | Teras | Özel |
| `q` | Sera | Özel |
| `z` | Tesisat Odası | Özel |

### 3.2 Kat Bazlı İçerik

| Kat | İndeks | Başlıca Alanlar |
|-----|--------|-----------------|
| Alt Zemin | 0 | Amfi, Seminer Odaları, Lab'lar, Avlu, Ana Giriş |
| Zemin | 1 | Kafe, Resepsiyon, Öğretim Lab'ları, Herbaryum, Yangın Çıkışları |
| Birinci | 2 | Biyoloji Lab'ları, Ofisler, Teras |
| İkinci | 3 | Biyoloji Lab'ları, Ofisler, Teras |
| Üçüncü | 4 | Ofisler, Araştırma Lab'ları, Teras |
| Dördüncü | 5 | Ofisler, Sera, Tesisat Odası |

### 3.3 Koordinat Sistemi

- Orijinal PNG: 230×128 piksel → her piksel = 1 grid hücresi
- `MAP_SCALE = 5`: arayüzde 1150×640 piksele büyütülür
- Koordinatlar: `(floor, x, y)` — x: yatay (0=sol), y: dikey (0=üst)
- Mesafe dönüşümü: 1 hücre = 0.32 metre
- Yürüyüş hızı: 1.4 m/s (ortalama yetişkin)

---

## 4. POI Sistemi

### 4.1 POIType ve POI_REGISTRY

Her POI türü `poi/poi_index.py` içindeki `POI_REGISTRY` sözlüğünde tanımlıdır:

```python
@dataclass
class POIType:
    char         : str    # ASCII grid karakteri
    name_en      : str    # İngilizce ad
    name_tr      : str    # Türkçe ad
    access_level : str    # "public" | "restricted" | "accessible_only"
    icon         : str    # UI emoji
```

Erişim seviyeleri:
- `public`: Herkes yönlendirilebilir
- `restricted`: Gelecekte personel/öğrenci kısıtlaması için (şu an kullanılmıyor)
- `accessible_only`: Yalnızca tekerlekli sandalye rotaları için (Erişilebilir Lift `A`)

### 4.2 LabeledPOI (poi_labels.json)

168 özel isimlendirilmiş POI örneği `poi/poi_labels.json` dosyasında saklanır. Her kayıt:

```json
{
  "char": "O",
  "name": "Prof. Jane Smith's Office",
  "name_tr": "Prof. Jane Smith Ofisi",
  "floor": 2, "x": 145, "y": 30,
  "tags": ["professor", "neuroscience"],
  "description": "..."
}
```

**Karakter başına etiket dağılımı:**

| Char | Tür | Etiket Sayısı |
|------|-----|---------------|
| O | Ofis | 72 |
| P | Destek Lab | 29 |
| r | Grup Çalışma | 16 |
| L | Paylaşımlı Lab | 7 |
| M | Seminer Odası | 6 |
| G | Öğretim Lab | 9 |
| I | Görüntüleme | 3 |
| K | EP Test | 3 |
| Z | Çalışma Alanı | 3 |
| V | Avlu | 3 |
| X | Yangın Çıkışı | 5 |
| Diğerleri | — | 16 |
| **Toplam** | | **168** |

### 4.3 Çok Kapılı POI Deduplication

Büyük alanların birden fazla kapısı olabilir (örn. Büyük Seminer Odası: 3 kapı). `_dedup_labeled()` fonksiyonu:
1. Aynı `(name, floor)` grubundaki tüm hücreleri birleştirir
2. Centroid'e en yakın hücreyi UI temsilcisi seçer
3. A* için tüm kapı hücrelerini `all_states` listesinde saklar → çok hedefli A*

### 4.4 BFS Bileşen Analizi

Özel etiket verilmemiş POI türleri için `_floor_components()` ile BFS bağlı bileşen analizi yapılır. Her bileşen için centroid'e en yakın hücre seçilir; numaralandırılmış seçenekler sunulur (Tuvalet 1, Tuvalet 2, ...).

---

## 5. Pathfinding (Yol Bulma)

### 5.1 Durum Uzayı

- **Durum:** `(floor, x, y)` — 3-tuple
- **Başlangıç:** Kullanıcının seçtiği konum
- **Hedef:** Tek hücre veya çok kapılı POI hücre listesi
- **Eylemler:**
  - Yatay: `MOVE_N/S/E/W` (kardinal, maliyet=1) + `MOVE_NE/NW/SE/SW` (diyagonal, maliyet=√2)
  - Dikey: `ELEVATOR_UP/DOWN` (maliyet=2), `STAIR_UP` (12), `STAIR_DOWN` (6), `LIFT_UP/DOWN` (3)

### 5.2 Maliyet Modeli

```
Kardinal hareket:        1 birim  (0.32 m)
Diyagonal hareket:    √2 birim  (0.45 m)
Asansör (her kat):       2 birim  + 20 s zaman cezası
Merdiven yukarı:        12 birim  + 15 s zaman cezası
Merdiven aşağı:          6 birim  + 15 s zaman cezası
Erişilebilir lift:       3 birim  + 25 s zaman cezası
```

### 5.3 Sezgisel Fonksiyon (Heuristic)

`make_heuristic()` → admissible + consistent:

```
h(n) = min_{hedef g} {
    if floor(n) == floor(g):
        2D_euclidean(n, g)
    else:
        2D_euclidean(n, en_yakın_dikey) + dikey_maliyet × |floor_farkı| + 2D_euclidean(dikey, g)
}
```

### 5.4 Navigasyon Profilleri

| Profil | Yasak Eylemler | Maliyet Çarpanları |
|--------|---------------|-------------------|
| **En Hızlı** (`fastest`) | LIFT_UP/DOWN | — |
| **En Az Efor** (`least_effort`) | LIFT_UP/DOWN | STAIR_UP×30, STAIR_DOWN×15 |
| **Engelsiz** (`accessible`) | STAIR_UP/DOWN | LIFT_UP/DOWN×0.8 |

### 5.5 Uygulanan Algoritmalar

| Algoritma | Dosya | Özellik |
|-----------|-------|---------|
| **A\*** | `pathfinding/astar.py` | Optimal, admissible heuristic ile |
| **Ağırlıklı A\*** | `pathfinding/astar.py` | f(n) = g(n) + w·h(n), w-admissible |
| **UCS** (Dijkstra) | `pathfinding/astar.py` | f(n) = g(n), heuristicsiz optimal |
| **BFS** | `pathfinding/bfs.py` | Adım sayısı optimal, maliyet körü |
| **Çift Yönlü A\*** | `pathfinding/bidirectional_astar.py` | İki sınır buluşma noktasında birleşir |
| **IDA\*** | `pathfinding/idastar.py` | O(d) bellek, iteratif derinleşme |
| **Theta\*** | `pathfinding/theta_star.py` | Herhangi-açı (Bresenham LoS) |

> **Not:** Mevcut arayüz yalnızca A\* kullanmaktadır. Diğer algoritmalar karşılaştırma analizi için mevcuttur ve `pathfinding/main_search.py` üzerinden çalıştırılabilir.

---

## 6. Flask Web Arayüzü

### 6.1 Çalıştırma

```bash
cd /Users/meliscan/Downloads/analyzer
python app.py
# → http://localhost:5001
```

### 6.2 API Uç Noktaları

| Metot | Uç Nokta | Açıklama |
|-------|----------|---------|
| `GET` | `/` | SPA ana sayfası |
| `GET` | `/api/pois` | Tüm POI kategorileri, türleri, etiketleri |
| `POST` | `/api/resolve` | Metin sorgusunu POI'ya çöz |
| `POST` | `/api/navigate` | 3 profil için rota hesapla |
| `POST` | `/api/map-image` | Rota + etiketli kat planı → base64 PNG |
| `GET` | `/api/explore` | Hiyerarşik POI ağacı (Keşfet sekmesi) |
| `POST` | `/api/info` | Metin sorgusuna konum+yakın landmark cevabı |

#### `/api/navigate` İstek Şeması

```json
{
  "start": { "floor": 1, "x": 187, "y": 75, "name_tr": "...", "name_en": "..." },
  "destination": {
    "char": "M",
    "state": { "floor": 0, "x": 100, "y": 50 },
    "all_states": [{ "floor": 0, "x": 98, "y": 50 }, ...],
    "name_tr": "Büyük Seminer Odası",
    "name_en": "Large Seminar Room"
  }
}
```

#### `/api/navigate` Yanıt Şeması (her rota için)

```json
{
  "id": "fastest",
  "available": true,
  "duration_min": 2.3,
  "distance_m": 145.0,
  "floors_visited": [0, 1],
  "path_by_floor": { "0": [[x,y], ...], "1": [[x,y], ...] },
  "trans_points": { "1": [[x,y]] },
  "start_state": [1, 187, 75],
  "end_state": [0, 100, 50],
  "segments": [...],
  "stats": { "nodes_expanded": 3421, "cost": 187.4 }
}
```

### 6.3 Harita Görüntü Oluşturma (`_draw_route`)

Her rota görüntüsü istek anında oluşturulur:

1. `archive/old-maps/` içindeki PNG açılır
2. `MAP_SCALE=5` ile 1150×640'a büyütülür
3. **POI etiketleri çizilir** (beyaz metin + siyah gölge, her kata 30–40 etiket)
4. Rota polyline çizilir (renkli + siyah gölge, genişlik=5)
5. Geçiş noktaları sarı, başlangıç yeşil, bitiş kırmızı nokta olarak işaretlenir
6. Base64 PNG olarak döndürülür

**Etiket verisi (`_floor_label_data`):** Uygulama başlangıcında hesaplanır. Her kat için:
- `poi_labels.json` kayıtlarından → özel isimler (centroid koordinatında)
- Etiketlenmemiş POI türleri için → genel tür adı (BFS bileşen centroid'inde)
- Atlanan karakterler: `#`, `.`, `S`, `E`, `A`, `j`, `N`

### 6.4 Uygulama Başlangıç Sırası

```
build_campus_map()      # 6 katlı 3D grid (PNG'lerden)
build_poi_index()       # POI hücre indeksi
_index.load_labels()    # poi_labels.json yükleme
QueryResolver()         # Metin çözümleme motoru
find_cells('N')         # Varsayılan başlangıç (Ana Giriş)
_compute_floor_labels() # Her kat için etiket listesi (harita çizimi için)
```

---

## 7. Ön Yüz (Frontend)

### 7.1 Teknoloji Yığını

- Vanilla JavaScript (ES2020+), async/await
- CSS: Oxford Mavi (#002147) temalı, flex/grid layout
- Build araçları yok — tek HTML dosyası + iki statik dosya
- Haritalar: `<img>` etiketiyle base64 PNG, URL önbellekleme

### 7.2 Uygulama Durumu

```javascript
const S = {
  lang: 'tr',           // Aktif dil
  poiData: null,        // /api/pois verisi
  start: null,          // Başlangıç konumu nesnesi
  dest: null,           // Hedef konumu nesnesi
  routes: null,         // /api/navigate yanıtı
  activeRouteId: null,  // Seçili rota profili
  activeFloor: null,    // Görüntülenen kat
  mapCache: {},         // floor → base64 PNG önbelleği
  inputCtx: null,       // 'start' | 'dest'
  mode: 'nav',          // 'nav' | 'explore'
  exploreData: null,    // /api/explore verisi
  pendingDest: null,    // Keşfet→Navigasyon geçişi bekleyen hedef
};
```

### 7.3 Navigasyon Akışı

```
1. Başlangıç Seç  →  Kategori > Tür > [Kat] > Örnek
2. Hedef Seç      →  (aynı hiyerarşi)
3. Rota Hesapla   →  POST /api/navigate
4. Profil Seç     →  En Hızlı / En Az Efor / Engelsiz
5. Kat Görüntüle  →  POST /api/map-image (kat sırası yön-duyarlı)
```

**Kat Sekmeleri Sıralaması:** Başlangıç < Bitiş ise artan, aksi hâlde azalan sıra.

### 7.4 Konum Seçim Hiyerarşisi

- **Çok katlı türler:** Önce kat seçimi gösterilir, sonra o kata ait örnekler
- **Tek katlı türler:** Doğrudan örnekler listelenir
- **Etiketli örnekler:** `poi_labels.json`'dan isimle listelenir
- **Etiketlenmemiş çok bileşenli türler:** BFS ile numaralandırılır (örn. "Tuvalet 1", "Tuvalet 2")
- **Çok kapılı tek POI:** UI'da tek seçenek, A* hedef listesinde tüm kapılar (`all_states`)

### 7.5 Keşfet Sekmesi

Hiyerarşik POI tarama ağacı:

```
Kategori (Giriş/Çıkışlar, Ofisler, ...)
  └─ Tür (Yangın Çıkışı, ...)
       └─ Grup (Profesör Ofisleri, Araştırmacı Ofisleri, ...)
            └─ Örnek (Prof. Smith Ofisi — İkinci Kat)
                  └─ [Navigasyona Başla] butonu
```

**Ofis Gruplandırması** — isim kalıplarına göre otomatik:

| Grup | Kural |
|------|-------|
| Profesör Ofisleri | `Prof.` ile başlıyorsa |
| Araştırmacı Ofisleri | `Dr.` ile başlıyorsa |
| Postdok | `postdoctoral` içeriyorsa |
| Doktora Öğrencisi | `phd student` içeriyorsa |
| Misafir Araştırmacı | `visiting researcher` içeriyorsa |
| İdari | manager/coordinator/administrator/... |
| Diğer | Eşleşmeyen |

**Bilgi Chatbotu (`/api/info`):**
- Doğal dil sorgusu → QueryResolver → POI eşleşmesi
- Her konum için yakın landmark tespiti (≤40 Manhattan mesafe)
- Yanıt: "Zemin katında, Kafe ve Resepsiyon yakınında"
- Kendini landmark olarak saymaz (`skip_char` parametresi)

---

## 8. Araç Betikleri (tools/)

| Betik | Açıklama |
|-------|---------|
| `label_map.py` | 6 kata etiketli PNG oluşturur (`labeled_maps/`). `--scale` ve `--floor` argümanları. |
| `grid_visualizer.py` | ASCII grid'i renkli PNG'ye dönüştürür |
| `find_poi_coords.py` | Belirli bir POI karakterinin tüm koordinatlarını listeler |
| `pixel_analyzer.py` | PNG piksel renklerini analiz eder |
| `pixel_converter.py` | Piksel → grid koordinat dönüştürücü |
| `diagnose_floor.py` | Belirli bir katın grid içeriğini teşhis eder |
| `validate_map.py` | Harita tutarlılığını doğrular (duvar/yürünebilir bölge kontrolleri) |

### tools/label_map.py Kullanımı

```bash
python tools/label_map.py              # Tüm katlar, scale=8
python tools/label_map.py --scale 6   # Daha küçük çıktı
python tools/label_map.py --floor 2   # Sadece Birinci Kat
```

Çıktılar: `labeled_maps/{kat-adı}_labeled.png`

---

## 9. Önemli Tasarım Kararları

### 9.1 Çok Kapılı POI Sorunu

**Problem:** Büyük alanların birden fazla kapısı vardır; her kapı ayrı bir grid hücresidir. Naif yaklaşım aynı alanı N kez listeler.

**Çözüm:**
- `_dedup_labeled()`: UI için `(name, floor)` bazında gruplayıp tek temsil hücresi seçer
- `all_states`: A* için tüm kapı hücreleri hedef listesine eklenir → gerçek en kısa yol bulunur

### 9.2 Yangın Çıkışları Kat Koordinatı Sorunu

**Problem:** `first_cell` tüm katlar arasından seçiliyordu; zemin kattaki yangın çıkışı alt zemin koordinatıyla eşleşiyordu.

**Çözüm:** `first_cell_by_floor` dict'i her kat için ayrı ayrı ilk hücreyi saklar. JS bu dict'ten kat-spesifik koordinat okur.

### 9.3 Harita Dosyaları Ayrımı

- `maps/`: Koordinat referansı — orijinal yüksek kaliteli PNG'ler
- `archive/old-maps/`: Arayüzde görüntülenen PNG'ler — renk şeması farklı

### 9.4 Rota Profilleri Neden Benzer Sonuç Verir?

Merdiven ve asansörler fiziksel olarak birbirine yakın konumlanmıştır. Aynı katta navigasyonda hiçbir dikey geçiş olmadığı için 3 profil özdeş rota üretir. Profil farklılıkları yalnızca kat geçişlerinde belirginleşir. Algoritma karşılaştırma analizi için `pathfinding/main_search.py` kullanılabilir.

---

## 10. Tez Taslağı

```
Bölüm 1 – Giriş
  1.1 Motivasyon ve Problem Tanımı
  1.2 Katkılar

Bölüm 2 – İlgili Çalışmalar
  2.1 Kapalı Alan Navigasyon Sistemleri
  2.2 Grid Tabanlı Yol Bulma
  2.3 Erişilebilirlik Odaklı Navigasyon

Bölüm 3 – Sistem Tasarımı
  3.1 Bina Veri Modeli (ASCII Grid)
  3.2 POI Sistemi ve Etiketleme
  3.3 Kullanıcı Profili ve Erişilebilirlik

Bölüm 4 – Arama Algoritmaları
  4.1 Teorik Çerçeve (AIMA 4e)
  4.2 A*, Ağırlıklı A*, UCS
  4.3 Çift Yönlü A*
  4.4 IDA*
  4.5 Theta* (Herhangi-Açı)
  4.6 Heuristic Tasarımı

Bölüm 5 – Web Arayüzü Uygulaması
  5.1 Flask Backend Mimarisi
  5.2 Vanilla JS SPA Tasarımı
  5.3 Görsel Rota Sunumu

Bölüm 6 – Değerlendirme
  6.1 Algoritma Karşılaştırması (süre, genişletilen düğüm, maliyet)
  6.2 Profil Etkinliği
  6.3 Kullanıcı Deneyimi Değerlendirmesi

Bölüm 7 – Sonuç ve Gelecek Çalışmalar
```

---

## 11. Bilinen Sınırlılıklar ve Gelecek Çalışmalar

| Konu | Durum |
|------|-------|
| 3 rota profili neredeyse her zaman aynı yolu veriyor | Fiziksel kısıt; algoritmik karşılaştırma analizi eksik |
| Birleştirilmeyi bekleyen POI'lar var | Kullanıcı tarafından eklenecek |
| Algoritma karşılaştırma arayüzü | Planlandı, henüz eklenmedi |
| LLM destekli doğal dil sorgusu | `llm/` klasörü mevcut, arayüze entegre edilmedi |
| Gerçek zamanlı kalabalık/kapasite verisi | Kapsam dışı |

---

*Oluşturulma tarihi: 2026-06-01 · LaMB Navigator v2.0*
