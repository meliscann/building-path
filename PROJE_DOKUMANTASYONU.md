# BuildingPath — Çok Katlı İç Mekan Navigasyon Sistemi
## Lisans Bitirme Projesi — Teknik Dokümantasyon

---

## İçindekiler

1. [Proje Özeti](#1-proje-özeti)
2. [Sistem Mimarisi](#2-sistem-mimarisi)
3. [Teknoloji Yığını](#3-teknoloji-yığını)
4. [Harita Verisi ve ASCII Grid Temsili](#4-harita-verisi-ve-ascii-grid-temsili)
5. [Arama Algoritmaları](#5-arama-algoritmaları)
6. [Maliyet Modeli](#6-maliyet-modeli)
7. [Sezgisel Fonksiyonlar (Heuristics)](#7-sezgisel-fonksiyonlar-heuristics)
8. [POI (İlgi Noktası) Sistemi](#8-poi-i̇lgi-noktası-sistemi)
9. [Kullanıcı Profili ve Erişilebilirlik](#9-kullanıcı-profili-ve-erişilebilirlik)
10. [LLM Entegrasyonu (Groq/LLaMA)](#10-llm-entegrasyonu-groqllama)
11. [Web Arayüzü (Flask + SPA)](#11-web-arayüzü-flask--spa)
12. [CLI Arayüzü](#12-cli-arayüzü)
13. [Dosya Yapısı ve Modüler Mimari](#13-dosya-yapısı-ve-modüler-mimari)
14. [Her Dosyanın Ayrıntılı Açıklaması](#14-her-dosyanın-ayrıntılı-açıklaması)
15. [Test Senaryoları ve Algoritma Karşılaştırması](#15-test-senaryoları-ve-algoritma-karşılaştırması)
16. [Test Scriptleri](#16-test-scriptleri)
17. [Araçlar ve Veri Hazırlama](#17-araçlar-ve-veri-hazırlama)
18. [Sistem Akışı: Uçtan Uca Navigasyon](#18-sistem-akışı-uçtan-uca-navigasyon)
19. [Önemli Tasarım Kararları](#19-önemli-tasarım-kararları)

---

## 1. Proje Özeti

**BuildingPath**, Oxford Üniversitesi'nin LaMB (Life and Mind Building) binası için geliştirilmiş, çok katlı, erişilebilirlik destekli, doğal dil arabirimi olan akıllı bir iç mekan navigasyon sistemidir. 

Sistem şu temel bileşenlerden oluşur:
- **6 katlı ASCII grid haritası** (kaynak: binanın PNG kat planlarından otomatik türetilmiş)
- **7 arama algoritması** uygulaması (BFS, UCS, A\*, Ağırlıklı A\*, Çift Yönlü A\*, IDA\*, Theta\*)
- **Erişilebilirlik profilleri** (en hızlı, en az efor)
- **LLM destekli doğal dil arayüzü** (Groq API üzerinden LLaMA-3.3-70B)
- **Flask tabanlı web SPA** (koyu mod temalı chatbot + harita görselleştirme, 3 mod: Navigasyon / Keşfet / Kat Planları)
- **CLI modu** (terminal üzerinden sorgu yapılabilir)

Proje, Russell & Norvig'in *Artificial Intelligence: A Modern Approach* (AIMA 4. baskı) çerçevesini referans alarak uygulanmıştır.

---

## 2. Sistem Mimarisi

```
Kullanıcı Girişi (Doğal Dil)
         │
         ▼
┌─────────────────────┐
│   LLM (Groq/LLaMA)  │  ← query_parser.py
│  NL → yapılandırılmış│     {destination, profile, floor, lang}
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   QueryResolver     │  ← query_resolver.py
│  Metin → POI kodu   │     alias tablosu + etiketli örnekler
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   POI Index         │  ← poi_index.py
│  POI kodu → (f,x,y) │     O(1) karakter arama
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  BuildingProblem    │  ← indoor_search.py
│  A* için problem    │     durum: (floor, x, y)
│  tanımı             │     eylemler: 8 yön + dikey geçiş
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Arama Algoritması  │  ← astar.py vb.
│  A*, Theta*, vb.    │     g(n) + h(n) optimizasyonu
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  RouteFormatter     │  ← route_formatter.py
│  Rota → Doğal Dil   │     LLM ile yol tarifi üretme
└─────────────────────┘
         │
         ▼
    Kullanıcı Yanıtı
```

---

## 3. Teknoloji Yığını

| Bileşen | Teknoloji |
|---|---|
| Programlama Dili | Python 3.10+ |
| Web Framework | Flask 3.x |
| LLM API | Groq (LLaMA-3.3-70B-versatile) |
| Harita Görüntüleme | Pillow (PIL) — ImageDraw |
| Veri Formatı | ASCII grid (`.py`) + JSON |
| Frontend | Vanilla JS (ES2022), CSS3 |
| İkon Seti | Lucide Icons |
| Test | Dahili test scriptleri |

---

## 4. Harita Verisi ve ASCII Grid Temsili

### 4.1 Kaynak: PNG Kat Planları

Binanın 6 katına ait PNG formatındaki mimari kat planları (`maps/` klasörü) `tools/pixel_converter.py` aracıyla işlenerek ASCII grid'e dönüştürülmüştür. Her piksel bir grid hücresi olur.

Oxford binası sadece uygulamanın gerçek bir bina üzerinde yapılması için kullanılmıştır. Bu proje herhangi bir binada da kullanılabilir. yani projenin olayı oxford binası değil. ayrıca binanın haritalarının kullanımı için gerekli izinler alınmıştır ve haritalarda projeye uygulanabilirlik için bazı küçük değişiklikler yapılmıştır. 

**Ölçek:** 1 piksel = 0.32 metre  
**Grid boyutu:** 230 × 128 hücre (her kat için)  
**Bina derinliği:** 128 × 0.32 m ≈ 41 metre

### 4.2 Karakter Kodu Tablosu

`data/building_data.py` dosyasındaki grid içinde her hücre bir karakterle temsil edilir:

| Karakter | Türkçe Anlam | Kategori |
|---|---|---|
| `#` | Duvar / Erişime kapalı | Altyapı |
| `.` | Koridor | Altyapı |
| `S` | Merdiven | Dikey Dolaşım |
| `E` | Asansör | Dikey Dolaşım |
| `N` | Ana Giriş | Giriş |
| `X` | Yangın Çıkışı | Giriş |
| `R` | Resepsiyon | Giriş |
| `T` | Tuvalet | Tesis |
| `F` | Kafe | Yiyecek/İçecek |
| `j` | Yemekhane | Yiyecek/İçecek |
| `H` | Amfi | Eğitim |
| `M` | Seminer Odası | Eğitim |
| `G` | Öğretim Laboratuvarı | Eğitim |
| `C` | Bilgisayar Laboratuvarı | Eğitim |
| `e` | Konferans Odası | Eğitim |
| `O` | Ofis | Çalışma |
| `B` | Dinlenme Alanı | Çalışma |
| `Z` | Çalışma Alanı | Çalışma |
| `A` | Grup Çalışma Odası | Çalışma |
| `J` | Biyoloji Laboratuvarı | Araştırma |
| `L` | Paylaşımlı Laboratuvar | Araştırma |
| `P` | Destek Laboratuvarı | Araştırma |
| `I` | Görüntüleme Birimi | Araştırma |
| `K` | EP Test Odası | Araştırma |
| `W` | Atölye | Araştırma |
| `Y` | Herbaryum | Özel |
| `q` | Sera | Özel |
| `U` | Kütüphane | Kütüphane |
| `V` | Avlu | Açık Alan |
| `Q` | Atrium Terası | Açık Alan |
| `D` | Teras | Açık Alan |

### 4.3 Kat İndeksleri

| İndeks | İngilizce | Türkçe |
|---|---|---|
| 0 | Lower Ground | Alt Zemin |
| 1 | Ground | Zemin |
| 2 | First | Birinci |
| 3 | Second | İkinci |
| 4 | Third | Üçüncü |
| 5 | Fourth | Dördüncü |

### 4.4 Durum Uzayı

Bir konum üçlü olarak temsil edilir: `(floor, x, y)` — örneğin `(1, 187, 75)` Zemin kattaki ana girişi işaret eder.

---

## 5. Arama Algoritmaları

Tüm algoritmalar AIMA 4. baskı çerçevesini temel alır. Ortak altyapı `pathfinding/common.py` içindedir.

### 5.1 Temel Veri Yapıları (`pathfinding/common.py`)

#### Problem Sınıfı
```
Problem(initial, goal)
    actions(state) → eylemler listesi
    result(state, action) → yeni durum
    action_cost(s, a, s1) → maliyet (varsayılan: 1)
    is_goal(state) → bool
    h(node) → sezgisel değer (varsayılan: 0)
```

#### Node Sınıfı
```
Node(state, parent, action, path_cost)
    state      : (floor, x, y)
    parent     : üst Node
    action     : uygulanmış eylem
    path_cost  : köke kadar birikimli g(n)
```

#### PriorityQueue
- `heapq` ile desteklenen min-yığın
- `key` parametresi: her düğüm için önceliği hesaplar
- `add(item)` → O(log n), `pop()` → O(log n)

#### `best_first_search(problem, f)`
Tüm en-iyi-önce arama varyantlarının (UCS, A\*, GBFS) paylaştığı temel algoritma:
- `f = g` → UCS
- `f = g + h` → A\*
- `f = h` → GBFS

### 5.2 Genişlik Öncelikli Arama — BFS (`pathfinding/bfs.py`)

**Referans:** AIMA 4e Şekil 3.9

**Özellikler:**
- Tam (finite grafta)
- Optimal — minimum adım sayısı (maliyet değil)
- Zaman karmaşıklığı: O(b^d)
- Alan karmaşıklığı: O(b^d) — tüm sınır bellekte tutulur

**Uygulama detayları:**
- FIFO kuyruğu (`collections.deque`)
- Kökte erken hedef testi
- Genişletmede erken hedef testi (iyileşme)
- Ziyaret edilen durumları `reached` kümesinde tutar (grafik araması)

**Ne zaman kullanılır:** Tüm eylem maliyetleri eşit olduğunda en iyi seçimdir. Bu projede maliyet farklı olduğundan (kat geçişlerinde merdiven ve asansör farklı maliyetlere sahip), BFS referans algoritma olarak kullanılmıştır.

### 5.3 Tekdüze Maliyet Araması — UCS (`pathfinding/astar.py`)

**Referans:** AIMA 4e Şekil 3.14

`f(n) = g(n)` — yalnızca birikimli maliyet

**Özellikler:**
- Tam ve maliyet-optimal
- Heuristik gerekmez
- Dijkstra algoritmasının arama grafındaki karşılığı

```python
def uniform_cost_search(problem):
    return best_first_search(problem, f=g)
```

### 5.4 A\* Araması (`pathfinding/astar.py`)

**Referans:** AIMA 4e Bölüm 3.5.2

`f(n) = g(n) + h(n)`

- `g(n)`: başlangıçtan n'e birikimli maliyet
- `h(n)`: n'den hedeflere sezgisel tahmin

**Özellikler:**
- Tam ve maliyet-optimal (h kabul edilebilir olduğunda)
- UCS'den daha hızlı (sezgisel sayesinde daha az düğüm genişletir)
- Bellekte tüm `reached` tablosu tutulur

```python
def astar_search(problem, h=None):
    h = h or problem.h
    return best_first_search(problem, f=lambda n: g(n) + h(n))
```

**Bu projede A\* kullanımı:**  
Hem CLI (`navigator.py`) hem de web (`app.py`) arayüzünde ana navigasyon algoritması A\*'dır. Heuristik olarak `make_heuristic()` kullanılır.

### 5.5 Ağırlıklı A\* (`pathfinding/astar.py`)

`f(n) = g(n) + w · h(n)`, w ≥ 1

**Özellikler:**
- Tam
- w-kabul edilebilir: çözüm maliyeti ≤ w × optimal maliyet
- Daha az düğüm genişletilir → daha hızlı
- `w = 1.0` → standart A\*
- Bu projede `w = 1.5`

```python
def weighted_astar_search(problem, h=None, weight=1.5):
    h = h or problem.h
    return best_first_search(problem, f=lambda n: g(n) + weight * h(n))
```

**Ne zaman kullanılır:** Büyük haritalarda hız/optimallık dengesi gereken durumlarda.

### 5.6 Çift Yönlü A\* (`pathfinding/bidirectional_astar.py`)

**Referans:** Kaindl & Kainz (1997), "Bidirectional Heuristic Search Reconsidered"

**Temel fikir:** Başlangıçtan ileri, hedeften geri olmak üzere iki eş zamanlı arama yapılır. Sınırlar kesiştiğinde durur.

**Sonlandırma koşulu:**
```
çözüm.path_cost ≤ g(öne_en_iyi) + g(geri_en_iyi)
```

**Hangi sınır genişletilir:** `f` değeri daha küçük olan sınır seçilir.

**Geri arama için simetri:**
- Yatay hareketler simetriktir
- Merdiven maliyetleri asimetriktir (YUKARI=22sn, AŞAĞI=16sn) — geri aramada tersine çevrilir:
  ```python
  def _reversed_action_cost(action):
      if action == "STAIR_UP":   return COST_STAIR_DOWN  # geriye gidilince iniş
      if action == "STAIR_DOWN": return COST_STAIR_UP    # geriye gidilince çıkış
  ```

**Yol birleştirme:** `_join_nodes(nf, nb)` — ileri ve geri yolları birleştirerek tek bir `Node` zinciri oluşturur.

**Avantaj:** Teorik olarak A\*'dan çok daha az düğüm genişletir (b^(d/2) yerine b^d).

**Kısıt:** Bu uygulamada tek hedef gerektirir.

### 5.7 IDA\* — Yinelemeli Derinleştirme A\* (`pathfinding/idastar.py`)

**Referans:** Korf, R.E. (1985), "Depth-first iterative-deepening"

**Temel fikir:** Her iterasyonda, mevcut `bound` değerini aşmayan tüm düğümleri DFS ile tarar. `bound` her iterasyonda `f > bound` olan en küçük `f` değerine yükseltilir.

```
bound = h(kök)
iterasyon:
    bound aşılırsa: yeni_bound = min(aşılan f değerleri)
    hedefe ulaşırsa: çözüm döndür
```

**Özellikler:**
- Tam ve optimal (h kabul edilebilir olduğunda)
- **Bellek:** O(d) — yalnızca mevcut yol tutulur (A\*'ın O(n)'ine karşı)
- **Zaman:** A\* ile aynı asimptotik karmaşıklık ama daha fazla sabit faktör

**Döngü önleme:** `_on_path()` fonksiyonu, bir düğümün kendi atalarında aynı durumu kontrol eder.

**Ne zaman kullanılır:** Bellek kısıtlı ortamlarda veya çok büyük grafiklerde.

### 5.8 Theta\* — Herhangi Açılı Yol Planlama (`pathfinding/theta_star.py`)

**Referans:** Daniel et al. (2010), "Theta*: Any-Angle Path Planning on Grids", JAIR 39.

**Temel sorun:** Standart A\* yalnızca grid kenarları boyunca hareket eder; gerçek yoldan daha uzun "merdiven basamağı" rotalar üretir.

**Theta\* çözümü:** Bir düğüm ile büyükbabası arasında **görüş hattı** (Line of Sight) varsa, büyükbabayı direkt ebeveyn yap — herhangi bir açıda kısayol izin ver.

```
update_vertex(s, s'):
    eğer LoS(büyükbaba(s), s') var ise:
        Path 2: büyükbaba → s' (Öklid mesafesi)
    değilse:
        Path 1: standart A* genişlemesi
```

**Görüş Hattı Algoritması (Bresenham'ın Çizgi Algoritması):**

`line_of_sight(harita, kat, x0, y0, x1, y1)`:
- İki nokta arasındaki her grid hücresini tarar
- Herhangi bir duvar (`#`) varsa `False` döndürür
- Tüm hücreler geçilebilirse `True` döndürür

```python
dx, dy = abs(x1-x0), abs(y1-y0)
err = dx - dy
while (cx,cy) != (x1,y1):
    e2 = 2 * err
    if e2 > -dy: err -= dy; cx += sx
    if e2 < dx:  err += dx; cy += sy
```

**Çok katlı not:** LoS yalnızca aynı katta anlamlıdır. Farklı katlarda Path 1'e (standart A\*) geri düşülür.

**Özellikler:**
- Tam
- Yaklaşık optimal (gerçek Öklid en kısa yolundan küçük sapmalar olabilir)
- A\*'dan daha kısa ve pürüzsüz rotalar üretir
- Zaman: O(n log n), alan: O(n)
- Her düğüm için LoS kontrolü: O(max(w, h))

### Algoritma Karşılaştırması

| Algoritma | Optimal | Bellek | Heuristik | Açıklama |
|---|---|---|---|---|
| BFS | Adım sayısı | O(b^d) | Hayır | Eşit maliyetlerde iyi |
| UCS | Maliyet | O(b^d) | Hayır | Dijkstra'ya eşdeğer |
| A\* | Maliyet | O(n) | Evet | Bu projenin ana algoritması |
| Ağırlıklı A\* | w-yaklaşık | O(n) | Evet | Hız/optimal dengesi |
| Çift Yönlü A\* | Maliyet | O(√n) | Evet | İki taraflı arama |
| IDA\* | Maliyet | O(d) | Evet | Bellek-verimli |
| Theta\* | Yaklaşık | O(n) | Evet | Herhangi açılı, pürüzsüz |

---

## 6. Maliyet Modeli

**Kaynak:** `pathfinding/costs.py`

### 6.1 Ölçek Faktörü

```
1 piksel = 0.32 metre  (128 piksel yükseklik = ~41 m bina derinliği)
Yürüme hızı = 1.4 m/s  (ortalama yetişkin yayası)
```

### 6.2 Eylem Maliyetleri (Soyut Birimler)

| Eylem | Maliyet | Gerçek Zaman |
|---|---|---|
| Cardinal hareket (N/S/E/W) | 1.0 | ~0.23 sn |
| Çapraz hareket (NE/NW/SE/SW) | √2 ≈ 1.414 | ~0.32 sn |
| Asansöre biniş (MOVE → `'E'` hücresi) | 1 + 109.2 = **110.2** | tek seferlik bekleme |
| Asansör kat değişimi (ELEVATOR_UP/DOWN) | **21.9**/kat | ~5 sn/kat |
| Merdiven yukarı | 96.2 | ~22 sn/kat |
| Merdiven aşağı | 70.0 | ~16 sn/kat |
| Erişilebilir asansör | 218.7 | ~50 sn |

> **Biniş modeli:** Asansör biniş maliyeti (`COST_ELEVATOR_ENTRY = 109.2`), koridordan asansör hücresine (`'E'`) adım atan MOVE eyleminde **tek seferlik** olarak eklenir. Sonraki her `ELEVATOR_UP/DOWN` eylemi yalnızca kat başı maliyeti öder (21.9). Böylece 5 katlık bir asansör yolculuğu ≈ 110.2 + 21.9 × 4 = 197.8 birim tutar; bu gerçek dünya süresiyle (~50 sn) tutarlıdır.

**Merdiven vs Asansör — `fastest` profili:**
| Kat sayısı | Merdiven aşağı | Asansör | Tercih |
|---|---|---|---|
| 1 kat | 70.0 | ~132 | Merdiven |
| 2 kat | 140.0 | ~154 | Merdiven |
| 3 kat | 210.0 | ~175 | **Asansör** |
| 5 kat | 350.0 | ~198 | **Asansör** |

- `min_effort`: merdiven ×2 (aşağı=140/kat) veya ×3 (yukarı=289/kat) → asansör (~132 ilk kat) her zaman daha ucuz

### 6.3 Zaman Hesaplama

`path_duration(path, actions)`:
1. Her adım için Öklid piksel mesafesi hesapla
2. Metre'ye çevir: `pixels × 0.32`
3. Saniye'ye çevir: `metres / 1.4`
4. Kat geçiş sürelerini ekle (asansör, merdiven, erişilebilir asansör)
5. Asansöre biniş maliyeti yalnızca bir kez eklenir (çok katlı yolculuk için)

### 6.4 Rota Kırılımı

`route_breakdown(path, actions)` — rotayı insan okunabilir segmentlere ayırır:

```json
[
  {"kind": "walk", "floor": 1, "distance_m": 45.2, "duration_s": 32.3},
  {"kind": "elevator", "from_floor": 1, "to_floor": 3, "direction": "up", "duration_s": 35},
  {"kind": "walk", "floor": 3, "distance_m": 28.1, "duration_s": 20.1}
]
```

---

## 7. Sezgisel Fonksiyonlar (Heuristics)

**Kaynak:** `pathfinding/heuristics.py`

### 7.1 Temel 2-D Mesafe Fonksiyonları

**Manhattan mesafesi** — 4 yönlü hareket için:
```
h(n) = |x0 - x1| + |y0 - y1|
```

**Öklid mesafesi** — 8 yönlü hareket için:
```
h(n) = √((x0-x1)² + (y0-y1)²)
```

**Chebyshev mesafesi** — 8 yönlü birim maliyetli grid için:
```
h(n) = max(|x0-x1|, |y0-y1|)
```

### 7.2 Çok Katlı Maliyet-Bilinçli Sezgisel: `make_heuristic()`

Bu projede kullanılan ana sezgisel fonksiyon. Birden fazla hedef ve çok katlı haritayı destekler.

**Kabul edilebilirlik garantisi:** Gerçek maliyeti hiçbir zaman aşmaz (alt sınır verir).

**Algoritma:**

```python
def h(node):
    f, x, y = node.state
    d_vert = distance_to_nearest_vertical_cell(f, x, y)
    best = inf

    for (gf, gx, gy) in goals:
        d_xy = euclidean(x, y, gx, gy)
        df   = abs(f - gf)

        if df == 0:
            cost_lb = d_xy           # aynı katta: düz mesafe
        else:
            # farklı katta: merkeze git + kat geç + hedefe git
            cost_lb = d_xy + d_vert + min_vertical_cost * df

        best = min(best, cost_lb)
    return best
```

**Dikey indeks:** Her kat için asansör ve merdiven hücrelerinin konumları önceden hesaplanır.

**`min_vertical_cost = 21.9`:** Asansör biniş modeli sayesinde her kat değişiminin minimum maliyeti `COST_ELEVATOR_FLOOR = 21.9`'dur (asansördeyken ek maliyet sadece bu). Heuristiğin **kabul edilebilir** (admissible) kalması için bu değeri aşmamak zorunludur; 21.9'u aşan bir değer asansör rotalarını fazla tahmin ederek A\*'ın optimal yolu kaçırmasına yol açar. Profil çarpanları heuristic'e yansımaz — bu, merdiven cezalı `min_effort` profilinde heuristiğin daha az bilgilendirici olması anlamına gelir.

### 7.3 Theta\* için Öklid Sezgisel: `make_euclidean_heuristic()`

Daha hafif bir versiyondur; kat geçiş detaylarını yok sayar. Theta\* için uygundur çünkü LoS zaten mesafe hesabını iyileştirir. `min_vertical_cost = 21.9` kullanır.

---

## 8. POI (İlgi Noktası) Sistemi

### 8.1 POI Kayıt Defteri (`pathfinding/poi_index.py`)

`POI_REGISTRY` — 31 POI türünü tanımlar. Her tür:
- `char`: ASCII grid karakteri
- `name_en`, `name_tr`: İngilizce ve Türkçe isim
- `access_level`: "public" | "restricted" | "accessible_only"
- `icon`: Lucide ikon adı (UI için)

### 8.2 POI İndeksi (`poi/poi_index.py`)

Başlangıçta harita bir kez taranarak `POIIndex` nesnesi oluşturulur:

```python
index = build_poi_index(campus_map)
# Kullanım:
offices = index.cells("O")            # tüm ofis hücreleri
toilets_f1 = index.cells_on_floor("T", floor=1)
```

**Karmaşıklık:** O(1) arama (sözlük tabanlı)  
**Oluşturma:** O(F × W × H) — harita boyutu

### 8.3 Etiketli POI'lar (`poi/poi_labels.json`)

168 adlandırılmış POI örneği içerir. Tüm koordinatlar `building_data.py` grid'iyle doğrulanmıştır; her kayıt gerçek bir `char` hücresine denk gelir. Her giriş:

```json
{
  "floor": 0,
  "x": 148, "y": 11,
  "char": "L",
  "name": "Small Shared Lab Space 1",
  "name_tr": "Küçük Paylaşımlı Lab Alanı 1",
  "description": "...",
  "description_tr": "...",
  "open_hours": "Mon-Fri 08:00-18:00"
}
```

**Dağılım (önemli kategoriler):**
- Ofisler (`O`): 72 örneklem (profesör, araştırmacı, postdok, doktora öğrenci, akademik destek, misafir, idari)
- Destek laboratuvarları (`P`): 29
- Grup çalışma odaları (`A`): 18
- Öğretim laboratuvarları (`G`): 9
- Seminer odaları (`M`): 6

### 8.4 Sorgu Çözücü (`poi/query_resolver.py`)

Doğal dil sorgularını POI karakter kodlarına çevirir.

**Çözüm sırası:**
1. **Kesin alias eşleşmesi** — "tuvalet" → "T"
2. **Etiketli örnek eşleşmesi** (3 katmanlı sıralama):
   - Katman 1: tam isim eşleşmesi
   - Katman 2: tüm sorgu tokenleri isimde var
   - Katman 3: alt string
3. **Kısmi alias eşleşmesi** — kelime örtüşme skoru
4. **Doğrudan karakter kodu** — "O" yazan kullanıcı için
5. **Başarısız** — `confidence="failed"`

**Sonuç türleri:**
- `"exact"` — tam eşleşme
- `"partial"` — kısmi eşleşme
- `"named"` — belirli bir örnekle eşleşme (koordinatlar dahil)
- `"ambiguous"` — birden fazla eşleşme
- `"failed"` — eşleşme bulunamadı

**Türkçe ve İngilizce destek:** Alias tablosunda her iki dilde kelimeler bulunur.

---

## 9. Kullanıcı Profili ve Erişilebilirlik

**Kaynak:** `poi/user_profile.py`

### 9.1 Profil Yapısı

```python
@dataclass
class UserProfile:
    name: str
    label: str
    forbidden_actions: Set[str]    # bu eylemler hiç üretilmez
    cost_multipliers: Dict[str, float]  # maliyet çarpanları
```

### 9.2 Tanımlı Profiller

**`fastest` (En Hızlı)**
- Tüm eylemlere izin var
- Maliyetler zaten zaman-kalibreli; algoritma doğal olarak en hızlı dikey seçeneği tercih eder

**`min_effort` (En Az Efor)**
- MET (Metabolik Eşdeğer) tabanlı cezalar:
  - Merdiven yukarı: ×3.0 (MET oranı ≈ 8/1.5)
  - Merdiven aşağı: ×2.0 (MET oranı ≈ 3/1.5)
- Asansör tercih edilir ancak yasaklanmaz

**Web arayüzünde ek profil (`app.py` içinde):**

| Profil | `STAIR_UP` çarpanı | `STAIR_DOWN` çarpanı | Asansör |
|---|---|---|---|
| fastest | 1.0 | 1.0 | 1.0 |
| least_effort | 30.0 | 15.0 | 0.5 |

### 9.3 BuildingProblem'e Entegrasyon

`action_cost()` her eylem için profil çarpanını uygular. Asansör biniş maliyeti MOVE eyleminde, kat değişim maliyeti ELEVATOR eyleminde ayrı ayrı uygulanır:

```python
def action_cost(self, s, action, s1):
    multiplier = self.profile.action_cost_multiplier(action)

    if action in ("ELEVATOR_UP", "ELEVATOR_DOWN"):
        return COST_ELEVATOR_FLOOR * multiplier   # sadece kat maliyeti

    base = base_cost(action)

    if action in ALL_MOVES:  # koridordan 'E' hücresine adım → tek seferlik biniş
        if cell(s1) == 'E' and cell(s) != 'E':
            elev_mult = profile.action_cost_multiplier("ELEVATOR_UP")
            return base + COST_ELEVATOR_ENTRY * elev_mult

    return base * multiplier
```

Yasak eylemler `actions()` fonksiyonunda filtrelenir:
```python
if not self.profile.allows_action(act):
    continue
```

---

## 10. LLM Entegrasyonu (Groq/LLaMA)

### 10.1 LLM İstemcisi (`llm/llm_client.py`)

```python
class LLMClient:
    model = "llama-3.3-70b-versatile"
    
    def chat(messages, temperature=0.1, max_tokens=512) → str
    def json_chat(messages, ...) → dict  # JSON yanıtı ayrıştırır
```

Groq API üzerinden `llama-3.3-70b-versatile` modelini kullanır. JSON yanıtlarında markdown çit (`\`\`\`json`) temizleme yapılır.

### 10.2 Sorgu Ayrıştırıcı (`llm/query_parser.py`)

Doğal dil sorgusunu yapılandırılmış veriye çevirir:

```python
@dataclass
class ParsedQuery:
    destination: str   # "Prof. Whitfield's office", "en yakın tuvalet"
    profile: str       # "standard" | "wheelchair" | "mobility"
    floor: Optional[int]  # 0-5 veya None
    language: str      # "tr" | "en"
```

**Sistem promptu** (kısaltılmış):
```
BuildingPath iç mekan navigasyon asistanısın.
6 kat (0=Alt Zemin … 5=Dördüncü).
Konuşma geçmişi varsa zamirleri çöz ("bu lab" → "bilgisayar laboratuvarı").
Yalnızca JSON döndür: {destination, profile, floor, language}
```

### 10.3 Web Arayüzü LLM Kullanımı (`app.py`)

Web arayüzünde LLM üç yerde kullanılır:

1. **`_llm_normalise(query)`** — sorguyu aranamaz forma dönüştürür  
   `"Prof. Whitfield'a gidebilir miyim" → "Prof. Whitfield"`

2. **`api_ask` uç noktası** — chatbot yanıtı:
   - Belirsiz eşleşmede konuşma geçmişi ile bağlamı anlar
   - Başarısız aramada bina bilgisiyle yönlendirir
   - Başarılı aramalarda lokasyon verisiyle özelleştirilmiş yanıt üretir

3. **Sistem mesajları** hem Türkçe hem İngilizce, `lang` parametresine göre seçilir.

### 10.4 Rota Biçimlendirici (`llm/route_formatter.py`)

Rota segmentlerini LLM ile doğal dil yol tarifine dönüştürür. CLI modunda kullanılır.

### 10.5 Ana Orkestratör — CLI (`llm/navigator.py`)

```
1. query_parser.parse(sorgu) → ParsedQuery
2. resolver.resolve(destination) → ResolveResult
3. A* → Node (çözüm)
4. route_formatter.format(segments, duration, ...) → Metin yanıt
```

---

## 11. Web Arayüzü (Flask + SPA)

**Kaynak:** `app.py`, `templates/index.html`, `static/style.css`, `static/app.js`

### 11.1 Flask Sunucusu

```bash
python app.py
# → http://localhost:5001
```

Başlangıçta şunlar yapılır:
1. `build_campus_map()` — harita yüklenir
2. `build_poi_index(_map)` — POI indeksi oluşturulur
3. `_index.load_labels(_map)` — JSON etiketler yüklenir
4. `_try_init_llm()` — Groq API bağlantısı kurulur (GROQ_API_KEY varsa)
5. `_compute_floor_labels()` — her kat için metin etiketi önişlemi yapılır

### 11.2 API Uç Noktaları

| Uç Nokta | Yöntem | Açıklama |
|---|---|---|
| `GET /` | GET | Ana HTML sayfası (SPA) |
| `/api/pois` | GET | Tüm POI'lar kategorilere göre |
| `/api/resolve` | POST | Metin sorgusunu POI'a çöz (LLM normalizer + QueryResolver) |
| `/api/navigate` | POST | A\* ile rota hesapla |
| `/api/map-image` | POST | Rota çizili harita görüntüsü (base64 PNG) |
| `/api/ask` | POST | LLM destekli chatbot yanıtı — erişilebilirlik sorularında A\* doğrulaması içerir |
| `/api/info` | POST | POI bilgisi sorgula |
| `/api/explore` | GET | Tüm POI'ları kategorilere göre listele |
| `/api/floor-map/<int>` | GET | Belirtilen katın harita görüntüsü |

#### `/api/ask` — Erişilebilirlik Doğrulaması

`api_ask()` sorguda `asansör`, `merdiven`, `tekerlekli`, `elevator` gibi anahtar kelimeler tespit ettiğinde iki ek A\* testi çalıştırır:

- **`elevator_only`** profili (merdiven yasak) → hedefe yalnızca asansörle ulaşılabiliyor mu?
- **`stair_only`** profili (asansör yasak) → hedefe yalnızca merdivenle ulaşılabiliyor mu?

Sonuç LLM bağlamının başına faktüel bir not olarak eklenir; böylece LLM bina topolojisini yanlış yorumlayarak hatalı erişilebilirlik bilgisi veremez.

```
⚠ Erişilebilirlik (pathfinding doğruladı): Yalnızca merdivenle ulaşılabilir — asansörle ULAŞILAMAZ.
```

### 11.3 Koordinat Sistemi

```
Orijinal PNG:  230 × 128 piksel
MAP_SCALE = 10
Ölçeklenmiş:   2300 × 1280 piksel
```

Her grid hücresi ekranda 10×10 piksel alana karşılık gelir. Rota çizimi Pillow `ImageDraw` ile yapılır.

### 11.4 Harita Görselleştirme

`_draw_route(floor_idx, path_pts, color, start_pt, end_pt, trans_pts)`:
1. PNG kat planını yükle ve ölçekle
2. POI metin etiketlerini çiz (gölgeli beyaz metin)
3. Rota çizgisini çiz (gölge + renk)
4. Kat geçiş noktaları — sarı daire
5. Başlangıç noktası — yeşil daire
6. Bitiş noktası — kırmızı daire
7. base64 PNG olarak döndür

### 11.5 Rota Profilleri

| Profil | Açıklama | Merdiven Maliyeti | Asansör Maliyeti |
|---|---|---|---|
| `fastest` | Standart rota | 1× | 1× |
| `least_effort` | Asansörü tercih eder | YUKARI ×30, AŞAĞI ×15 | 0.5× |

### 11.6 Frontend (SPA)

#### Tema ve Görsel Tasarım

`static/style.css` — koyu mod (dark mode) teması. CSS değişkenleri (`--bg-deep`, `--accent`, `--rose`) ile merkezi renk sistemi:

| Değişken | Renk | Kullanım |
|---|---|---|
| `--bg-deep` | `#0A0D12` | En derin arka plan (header, map) |
| `--bg-main` | `#0F1117` | Ana uygulama arka planı |
| `--bg-card` | `#14171F` | Kart ve baloncuk arka planı |
| `--accent` | `#4CFFBF` | Birincil vurgu rengi (mint) |
| `--rose` | `#FF8DB5` | İkincil vurgu rengi (rose/pembe) |
| `--fastest` | `#1565C0` | Harita üzerinde "en hızlı" rota çizgisi |
| `--effort` | `#2E7D32` | Harita üzerinde "en az efor" rota çizgisi |

**Font:** DM Sans (Google Fonts, 400/500/600 ağırlık)

`#1565C0` yalnızca harita üzerindeki rota çizgi renginde kullanılır; arayüz temasıyla ilgisi yoktur.

#### Uygulama Yapısı

Sayfa üç katmandan oluşur:

1. **Landing page** (`#landing-page`) — Animasyonlu izometrik bina SVG görseli, "build your path." sloganı ve launch butonu. Butona basınca sayfa yukarı kayarak (CSS `translateY(-100vh)`) ana uygulamayı açar.

2. **Onboarding modalı** (`#onboarding-overlay`) — Landing page animasyonu bittikten sonra (900 ms) otomatik açılır. Arka plan `backdrop-filter: blur(3px)` ile hafifçe karartılır. Üç modu tanıtan kart içerikli bilgilendirme kutusu gösterir; "Başlayalım →" butonu veya overlay dışına tıklamayla kapanır. İçerik `[data-tr]/[data-en]` atribütleriyle iki dilli, Lucide ikonlu.

3. **Ana uygulama** (`#main-app`) — Üç modlu SPA:

| Mod | Tab | Açıklama |
|---|---|---|
| `nav` | Navigasyon (Compass) | Chatbot + harita görselleştirme |
| `explore` | Keşfet (Building-2) | POI ağaç listesi + bilgi chatbotu |
| `plans` | Kat Planları (Layers) | Harita görüntüleyici, yan kat seçici |

Her mod kendi `#mode-*` div'i içinde yaşar; aktif olmayan modlar `.hidden` ile gizlenir.

#### Navigasyon Chatbot Akışı

Kullanıcı önce hedefini seçer, ardından konumunu belirtir:

```
1. "Nereye gitmek istiyorsunuz?"  ← hedef önce sorulur (askDest)
2. Kullanıcı hedef seçer
3. "Peki, şu an neredesiniz?
   Yakınınızda bir yeri seçerek konumunuzu belirleyebilirsiniz."  ← yakın yer ipucu
4. Kullanıcı konum seçer → doNavigate()
```

`askDest()` → `selectLoc('dest')` → `askStart()` → `selectLoc('start')` → `doNavigate()` zinciri.

#### `static/app.js`

Saf JavaScript (ES2022), herhangi bir framework kullanılmaz:
- Async/await ile tüm API çağrıları
- Konuşma geçmişi yönetimi (son 10 mesaj, `api/ask` için LLM bağlamı)
- `setLang('tr'|'en')` — tüm `data-tr` / `data-en` atribütlerini günceller; onboarding modalını da kapsar
- `switchMode('nav'|'explore'|'plans')` — mod geçişi
- `showOnboarding()` — landing page → onboarding geçişini tetikler
- `resetNav()` — "Yeni Arama" butonunda çalışır; tüm navigasyon durumunu (`start`, `dest`, `routes`, `mapCache`) sıfırlar, sohbeti temizler, haritayı karşılama ekranına döndürür ve `askDest()` ile yeni akışı başlatır. Sayfa yeniden yüklenmez, landing page ve onboarding modal tekrar gösterilmez.
- Rota kartları (`route-card`) tıklandığında haritayı günceller
- `image-rendering: pixelated` — ölçeklenmiş kat planlarının piksel netliğini korur

---

## 12. CLI Arayüzü

**Kaynak:** `navigate.py`

```bash
# Tek sorgu
python navigate.py "büyük amfiye nasıl giderim"
python navigate.py "Prof. Whitfield's office" --verbose

# İnteraktif mod
python navigate.py
```

Verbose modunda LLM çıktısı, POI çözümü ve A\* istatistikleri görüntülenir.

---

## 13. Dosya Yapısı ve Modüler Mimari

```
analyzer/
├── navigate.py              ← CLI giriş noktası
├── app.py                   ← Flask web sunucusu
├── .env                     ← GROQ_API_KEY
├── logo.png                 ← Uygulama logosu (web arayüzü için)
│
├── data/                    ← Harita verisi
│   ├── __init__.py
│   └── building_data.py     ← 6 katlık ASCII grid (~3000 satır, otomatik üretilmiş)
│
├── pathfinding/             ← Arama algoritmaları
│   ├── __init__.py
│   ├── common.py            ← Problem, Node, PriorityQueue, best_first_search
│   ├── costs.py             ← Maliyet sabitleri + mesafe/süre hesabı
│   ├── heuristics.py        ← Kabul edilebilir sezgisel fonksiyonlar
│   ├── indoor_search.py     ← BuildingProblem (profil destekli)
│   ├── astar.py             ← UCS, A*, Ağırlıklı A*
│   ├── bfs.py               ← Genişlik Öncelikli Arama
│   ├── bidirectional_astar.py ← Çift Yönlü A*
│   ├── idastar.py           ← IDA*
│   ├── theta_star.py        ← Theta* (herhangi açılı)
│   └── main_search.py       ← Algoritma karşılaştırma koşucusu
│
├── poi/                     ← İlgi Noktası sistemi
│   ├── __init__.py
│   ├── user_profile.py      ← Erişilebilirlik profilleri
│   ├── poi_index.py         ← POI kayıt defteri + O(1) arama indeksi
│   ├── poi_label_loader.py  ← poi_labels.json okuyucu
│   ├── query_resolver.py    ← Doğal dil → POI koordinatı
│   └── poi_labels.json      ← 168 etiketlenmiş POI örneği
│
├── llm/                     ← LLM boru hattı
│   ├── __init__.py
│   ├── llm_client.py        ← Groq API sarmalayıcı
│   ├── query_parser.py      ← NL → {destination, profile, floor, language}
│   ├── route_formatter.py   ← Rota segmentleri → doğal dil tarifi
│   └── navigator.py         ← CLI için ana orkestratör
│
├── tools/                   ← Veri hazırlama araçları
│   ├── __init__.py
│   ├── pixel_converter.py   ← PNG → ASCII grid dönüştürücü
│   ├── pixel_analyzer.py    ← Piksel renk analizi
│   ├── floor_configs.py     ← 35 renk → karakter eşlemesi
│   ├── manual_overrides.py  ← Piksel bazlı düzeltmeler
│   ├── validate_map.py      ← Grid doğrulama + BFS erişilebilirlik
│   ├── grid_visualizer.py   ← ASCII → PNG görselleştirme
│   ├── diagnose_floor.py    ← Ulaşılamaz hücre analizi
│   ├── find_poi_coords.py   ← POI koordinat bulma
│   └── thesis_figures.py    ← Tez figürleri üretimi
│
├── tests/                   ← Test scriptleri
│   ├── __init__.py
│   ├── test_poi_index.py
│   ├── test_profiles.py
│   ├── test_query_resolver.py
│   └── test_costs_validation.py
│
├── maps/                    ← Kaynak PNG kat planları
│   ├── lower-ground-floor.png
│   ├── ground-floor.png
│   ├── first-floor.png
│   ├── second-floor.png
│   ├── third-floor.png
│   └── fourth-floor.png
│
├── static/                  ← Web statik dosyaları
│   ├── app.js               ← Frontend SPA (Vanilla JS, durum makinesi)
│   ├── style.css            ← Koyu mod, mint (#4CFFBF) + rose (#FF8DB5) tema
│   └── maps/                ← Web'de gösterilen kat planı PNG'leri
│
├── templates/
│   └── index.html           ← SPA şablonu
│
└── grid_visuals/            ← grid_visualizer çıktıları
```

---

## 14. Her Dosyanın Ayrıntılı Açıklaması

### `navigate.py` — CLI Giriş Noktası

Komut satırı argümanlarını işler, `Navigator` nesnesini başlatır, tek sorgu veya interaktif döngü çalıştırır. `--verbose` bayrağı ara adımları gösterir.

---

### `app.py` — Flask Web Sunucusu

En büyük ve en karmaşık dosyadır. Başlangıçta tüm navigasyon altyapısını yükler. 9 Flask rotası tanımlar. Yardımcı fonksiyonlar:

- `_dedup_labeled(lps, poi)`: Aynı (isim, kat) grubundaki POI'ları birleştirip merkeze en yakın temsilciyi seçer
- `_floor_components(floor_cells)`: BFS ile bir kattaki hücreleri bağlı bileşenlere ayırır
- `_draw_text_label(draw, text, cx, cy, font)`: Gölgeli ortalanmış metin etiketi çizer
- `_compute_floor_labels()`: Başlangıçta her kat için etiket verisi hesaplar
- `_run_route(start, goals, profile_id)`: Bir profil için A\* çalıştırır, serileştirilebilir sözlük döndürür
- `_draw_route(floor_idx, ...)`: PIL ile rota görselleştirmesi, base64 PNG döndürür
- `_nearby_description(floor, cx, cy, lang)`: Bir hücreye en yakın landmark'ı açıklar
- `_office_group_key(name)`: Ofis ismine göre grup sınıflandırması
- `_has_access_query(query)`: Sorguda erişilebilirlik anahtar kelimesi (`asansör`, `merdiven`, `tekerlekli` vb.) algılar
- `_access_note(char, lang)`: İki A\* testi çalıştırır (`elevator_only` / `stair_only`) ve LLM bağlamına faktüel erişilebilirlik notu ekler

---

### `data/building_data.py` — Bina Harita Verisi

`pixel_converter.py` tarafından otomatik oluşturulmuştur. Her kat için bir string listesi içerir. `build_campus_map()` fonksiyonu 6 katı birleştirerek 3-D liste döndürür: `map[floor][y][x]`.

---

### `pathfinding/common.py` — AIMA Temel Altyapısı

Tüm arama algoritmalarının üzerine inşa edildiği temel sınıflar:
- `Problem`: Soyut problem sınıfı
- `Node`: Arama ağacındaki bir düğüm
- `PriorityQueue`: Heap tabanlı öncelik kuyruğu
- `best_first_search()`: En-iyi-önce arama (UCS, A\*, GBFS için ortak)
- `expand()`, `path_states()`, `path_actions()`, `is_cycle()`: Yardımcı fonksiyonlar
- `failure`, `cutoff`: Sentinel düğümler (AIMA sözleşmesi)

---

### `pathfinding/indoor_search.py` — BuildingProblem

`Problem` sınıfının çok katlı iç mekan navigasyonu için somutlaştırması:
- Durum: `(floor, x, y)`
- Eylemler: 8 yönlü hareket + dikey geçişler (asansör, merdiven)
- `actions()`: Profil filtresi + sınır kontrolü
- `result()`: Yeni durum hesaplama
- `action_cost()`: Profil çarpanlı maliyet; asansör biniş maliyeti (`COST_ELEVATOR_ENTRY`) koridordan `'E'` hücresine adım atan MOVE eyleminde tek seferlik uygulanır, `ELEVATOR_UP/DOWN` eylemleri yalnızca `COST_ELEVATOR_FLOOR` öder
- `find_cells(map, char)`: Haritada belirli bir karakterin tüm konumlarını döndürür

---

### `pathfinding/costs.py` — Maliyet Modeli

Gerçek dünya ölçeği ve zaman tahminleri. `path_duration()` ve `route_breakdown()` fonksiyonları A\* çıktısını insan okunabilir bilgiye çevirir.

---

### `pathfinding/heuristics.py` — Sezgisel Fonksiyonlar

Kabul edilebilir ve tutarlı sezgisel fonksiyonlar:
- `manhattan_2d`, `euclidean_2d`, `chebyshev_2d`: Temel 2D mesafeler
- `build_vertical_index()`: Dikey geçiş hücrelerini önceden indeksler
- `make_heuristic()`: Çok katlı, çok hedefli ana sezgisel
- `make_euclidean_heuristic()`: Theta\* için hafif versiyon

---

### `pathfinding/astar.py` — A\*, UCS, Ağırlıklı A\*

Üç algoritma `best_first_search()` üzerine ince sarmalayıcılar olarak uygulanır.

---

### `pathfinding/bfs.py` — Genişlik Öncelikli Arama

AIMA 4e referans uygulaması. FIFO kuyruğu ile minimal adımlı yolu bulur.

---

### `pathfinding/bidirectional_astar.py` — Çift Yönlü A\*

İleri ve geri aramayı eşzamanlı çalıştırır. Asimetrik merdiven maliyetleri için tersine çevirme mantığı içerir. `_join_nodes()` ile iki yolu birleştirir.

---

### `pathfinding/idastar.py` — IDA\*

Yinelemeli derinleştirme ile bellek-verimli optimal arama. `_on_path()` döngü tespiti yapar.

---

### `pathfinding/theta_star.py` — Theta\*

Bresenham görüş hattı algoritması ile herhangi açılı yol planlaması. `line_of_sight()` fonksiyonu temel LoS kontrolü sağlar.

---

### `pathfinding/main_search.py` — Algoritma Karşılaştırma Koşucusu

4 senaryo ve 2 profil kombinasyonunda UCS, A\*, Ağırlıklı A\*, Theta\* karşılaştırır. Tablo çıktısı: maliyet, adım sayısı, mesafe, süre, genişletilen düğüm sayısı, hesaplama zamanı.

---

### `poi/user_profile.py` — Kullanıcı Profilleri

`UserProfile` dataclass ile erişilebilirlik profilleri. MET tabanlı merdiven maliyet çarpanları. `resolve_profile()` Türkçe ve İngilizce metin girişini profile çevirir.

---

### `poi/poi_index.py` — POI İndeksi

31 POI türünü kapsayan `POI_REGISTRY`. `build_poi_index()` ile O(1) arama için harita taranır. `labeled_by_char()`, `cells()`, `cells_on_floor()` ile hızlı erişim.

---

### `poi/query_resolver.py` — Sorgu Çözücü

180+ alias ile Türkçe/İngilizce doğal dil desteği. 3 katmanlı isim arama, skor tabanlı kısmi eşleşme. `ResolveResult` dataclass ile sonuç döndürür.

---

### `poi/poi_labels.json` — Etiketlenmiş POI Veritabanı

168 adlandırılmış POI örneği. Koordinat, kat, İngilizce/Türkçe isim, açıklama ve çalışma saatleri içerir. 72 ofis örneği profesör, araştırmacı, postdok, doktora öğrencisi ve idari personel olarak ayrıntılandırılmıştır.

---

### `llm/llm_client.py` — Groq API İstemcisi

`LLMClient` sınıfı: `chat()` ve `json_chat()` metotları. JSON yanıtlarında markdown çit temizleme.

---

### `llm/query_parser.py` — LLM Sorgu Ayrıştırıcı

`QueryParser.parse()` — doğal dil → `{destination, profile, floor, language}`. Konuşma geçmişi ile zamir çözümleme destekler.

---

### `llm/navigator.py` — CLI Orkestratörü

CLI için 4 adımlı boru hattı: LLM ayrıştırma → POI çözümleme → A\* → doğal dil biçimlendirme.

---

### `tools/pixel_converter.py` — PNG → ASCII Dönüştürücü

Kat planı PNG'lerini renk eşleme (`floor_configs.py`) ve piksel bazlı düzeltmeler (`manual_overrides.py`) kullanarak ASCII grid'e dönüştürür. Çıktı doğrudan `data/building_data.py`'dır.

---

### `tools/validate_map.py` — Harita Doğrulama

Her katı BFS ile tarayarak erişilebilirlik kontrolü yapar. İzole bileşenler ve bağlantı sorunlarını raporlar.

---

### `tools/grid_visualizer.py` — ASCII → PNG Görselleştirici

Renklendirilmiş ASCII grid PNG çıktısı üretir. POI türleri için renk paleti içerir.

---

## 15. Test Senaryoları ve Algoritma Karşılaştırması

**Kaynak:** `pathfinding/main_search.py`

### Senaryo 1 — Aynı Katta, Açık Alan

- **Başlangıç:** Kütüphane 2 (Alt Zemin, 203,27)
- **Hedef:** Küçük Amfi (Alt Zemin, 86,94)
- **Not:** Açık düzende Theta\* vs A\* görüş hattı avantajı

### Senaryo 2 — Aynı Katta, Dar Koridorlar

- **Başlangıç:** EP Test Odası (Alt Zemin, 41,108)
- **Hedef:** Küçük Paylaşımlı Lab 1 (Alt Zemin, 148,11)
- **Not:** Görüş hattı duvarlarla engellendiğinde Theta\* ≈ A\*

### Senaryo 3 — Maksimum Kat Farkı

- **Başlangıç:** Sera (4. Kat)
- **Hedef:** Amfi (Alt Zemin)
- **Rota:** Merdiven (5→4, bina geometrisi gereği zorunlu) + Asansör (4→0)
- **Not:** UCS vs A\* düğüm genişletme; heuristik sıkılığı profil maliyet ölçeğine bağlı

### Senaryo 4 — Aynı Katta, Maksimum Ofis Mesafesi

- **Başlangıç:** EP Test Lab Müdürü Ofisi (2. Kat, 64,117)
- **Hedef:** Biyoloji Lab Müdürü Ofisi (2. Kat, 215,6)
- **Not:** Geniş katta Ağırlıklı A\* hız/optimallık dengesi

### Karşılaştırma Metrikleri

- Maliyet (soyut birimler)
- Adım sayısı
- Mesafe (metre)
- Süre (dakika)
- Genişletilen düğüm sayısı
- Üretilen düğüm sayısı
- Hesaplama süresi (saniye)

---

## 16. Test Scriptleri

Tüm testler `tests/` klasöründe yer alır ve proje kökünden doğrudan çalıştırılır.

### `tests/test_poi_index.py` — POI İndeks Testi

POI kayıt defterinin ve indeks arama fonksiyonlarının doğruluğunu test eder. Tüm POI karakterlerinin haritada var olduğunu, `cells()` ve `cells_on_floor()` sorgularının beklenen sonuçları döndürdüğünü kontrol eder. İndeks özet tablosunu yazdırır.

```bash
python3 tests/test_poi_index.py
```

---

### `tests/test_profiles.py` — Profil Karşılaştırma Testi

`fastest` ve `min_effort` profillerinin rota kararları üzerindeki etkisini somutlaştırır.

**Senaryo:** Ana giriş (`N`, Alt Zemin) → Kafe (`F`, Zemin Kat)

**Test akışı:**
1. Her profil için `BuildingProblem` + A\* çalıştırılır
2. Rota segmentleri (`route_breakdown`) hesaplanır
3. Her iki profilin de çözüm bulduğu assert edilir
4. Merdiven kullanım sayısı karşılaştırılır

**Beklenen davranış:**
- `fastest`: merdiven yukarı (96.2) < asansör biniş+1kat (~132) → merdiveni tercih eder
- `min_effort`: merdiven ×3 ceza (288.6) > asansör (~132) → asansörü tercih eder

**Örnek çıktı:**
```
[Fastest Route]  maliyet=184.0  süre=0.70dk  mesafe=28.1m
  🚶 Kat 0  11.5m   8s
  🪜  stair  Kat0→Kat1  22s
  🚶 Kat 1  16.6m  12s

[Minimum Effort]  maliyet=289.6  süre=1.10dk  mesafe=50.7m
  🚶 Kat 0  25.9m  18s
  🛗  elevator  Kat0→Kat1  30s
  🚶 Kat 1  24.8m  18s
```

```bash
python3 tests/test_profiles.py
```

---

### `tests/test_query_resolver.py` — Sorgu Çözücü Testi

`QueryResolver`'ın Türkçe ve İngilizce alias'ları, kısmi eşleşmeleri ve başarısız sorguları doğru işlediğini doğrular. "tuvalet", "wc", "en yakın kafe", "engelli asansörü" gibi sorguların beklenen POI karakterini döndürdüğünü test eder.

```bash
python3 tests/test_query_resolver.py
```

---

### `tests/test_costs_validation.py` — Maliyet Modeli Testi

Maliyet sabitlerinin gerçek dünya sezgisiyle uyumlu olduğunu doğrular:
- `FLOOR_CHANGE_SECONDS` anahtarlarının eksiksizliği
- Tek katta merdiven çıkışının asansör binişinden hızlı olduğu (beklendiği üzere)
- İki kattan itibaren asansörün merdiveni geçtiği (başabaş noktası hesabı)
- Asansör giriş maliyetinin dahil edildiği hesaplamanın doğruluğu

```bash
python3 tests/test_costs_validation.py
```

---

## 17. Araçlar ve Veri Hazırlama  

### PNG → ASCII Dönüştürme Süreci

1. `tools/pixel_converter.py`: Her piksel rengi `tools/floor_configs.py` ile karaktere eşlenir
2. `tools/manual_overrides.py`: Otomatik eşlemede hatalı piksel düzeltmeleri
3. `tools/validate_map.py`: Üretilen grid'in bağlantı analizi
4. `tools/diagnose_floor.py`: Ulaşılamaz bölgelerin tanılanması

### POI Etiketi Ekleme

`tools/find_poi_coords.py` ile koordinat bulunup `poi/poi_labels.json`'a eklenir.

### Görselleştirme

`tools/grid_visualizer.py` — Her kat için renklendirilmiş PNG üretir, `grid_visuals/` klasörüne kaydeder.

---

## 18. Sistem Akışı: Uçtan Uca Navigasyon

### Web Arayüzü Akışı

```
1. Kullanıcı chatbot'a yazar: "Prof. Smith'in ofisine gitmek istiyorum"
   
2. POST /api/ask
   ├── LLM query_parser → "Prof. Smith office"
   ├── QueryResolver → char='O', confidence='named', 
   │   alternatives=[(3, 64, 117)]
   └── Lokasyon listesi oluşturulur
   
3. Kullanıcı profil seçer → "fastest"

4. POST /api/navigate
   ├── start = (1, 187, 75)  [Ana Giriş]
   ├── goals = [(3, 64, 117)]
   ├── BuildingProblem oluşturulur
   ├── make_heuristic(goals, map) → h fonksiyonu
   ├── astar_search(problem, h) → çözüm düğümü
   ├── path_states(node) → [(1,187,75), ..., (3,64,117)]
   ├── route_breakdown → [walk, elevator, walk]
   └── {duration_min, distance_m, segments, path_by_floor}

5. POST /api/map-image (her kat için)
   ├── _draw_route(floor_idx, path_pts, color)
   └── base64 PNG döndürür

6. Kullanıcı haritada animasyonlu rotayı görür
```

### CLI Akışı

```
python navigate.py "tekerlekli sandalyeyle kafeteryaya gidebilir miyim?"

1. QueryParser (LLM) → {destination: "cafe", profile: "wheelchair", lang: "tr"}
2. QueryResolver → char='F', confidence='exact'
3. POI Index → tüm kafe hücreleri
4. BuildingProblem(profile=wheelchair) — merdiven yasak
5. A* → asansörle rota
6. RouteFormatter (LLM) → Türkçe yol tarifi
```

---

## 19. Önemli Tasarım Kararları

### 1. ASCII Grid Harita Temsili
PNG yerine ASCII grid kullanımı arama algoritmalarını basitleştirir; her hücre doğrudan bir durum uzayı düğümüne karşılık gelir. Bellek etkin ve algoritmik olarak temizdir.

### 2. AIMA 4e Çerçevesi
`Problem`, `Node`, `PriorityQueue` ve `best_first_search` abstraction'ları, farklı algoritmaların minimum kod tekrarıyla uygulanmasını sağlar. UCS, A\* ve Ağırlıklı A\* yalnızca `f` fonksiyonuyla ayrışır.

### 3. Profil Destekli Maliyet Modeli
Erişilebilirlik yasakların yanı sıra **maliyet çarpanları** ile de sağlanır. Bu, "merdiveni kullanma" yerine "merdiveni çok pahalı yap" yaklaşımıyla algoritmayı doğal bir şekilde asansörü tercih ettirmeye yönlendirir.

### 4. Çok Hedefli A\*
`BuildingProblem` bir hedef seti (`goals`) destekler. `is_goal(state) = state in goals` yaklaşımı, "en yakın tuvalet" gibi sorgularda bütün tuvalet hücrelerini hedef olarak verip algoritmanın doğal olarak en yakınına gitmesini sağlar.

### 5. Zaman-Kalibreli Maliyetler
Soyut maliyet birimleri gerçek saniyeye kalibre edilmiştir (1 birim ≈ 0.23 sn). Bu, merdiven ve asansör maliyetlerini gerçekçi zaman tahminleriyle ifade etmeyi mümkün kılar.

### 6. LLM + Sembolik Arama Hibriti
LLM, sorgu anlama (NL → yapılandırılmış veri) ve yanıt üretme için kullanılır; navigasyon hesaplaması deterministik sembolik algoritmalarla yapılır. Bu, güvenilirlik ve açıklanabilirlik sağlar.

### 7. Yedekli LLM Mimarisi
LLM mevcut değilse (GROQ_API_KEY yoksa) tüm sistem kural tabanlı modda çalışır. Her LLM çağrısı try/except ile sarmalanmıştır.

### 8. Önişlemli Etiket Veritabanı
`_compute_floor_labels()` sunucu başlangıcında bir kez çalışır; her API isteğinde harita taramayı önler.

---

## Kurulum ve Çalıştırma

```bash
# Bağımlılıkları yükle
pip install flask pillow groq python-dotenv

# API anahtarı ayarla
echo "GROQ_API_KEY=your_key_here" > .env

# Web arayüzü başlat
python app.py
# → http://localhost:5001

# CLI modu
python navigate.py "en yakın tuvalet nerede"

# Algoritma karşılaştırması
python pathfinding/main_search.py
python pathfinding/main_search.py --scenario 3
```

---

*Bu dokümantasyon lisans bitirme tezi kapsamında BuildingPath navigasyon sisteminin tüm teknik bileşenlerini açıklamak amacıyla hazırlanmıştır.*
