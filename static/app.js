/* ═══════════════════════════════════════════════════════════
   BuildingPath – app.js
   ═══════════════════════════════════════════════════════════ */

/* ── Translations ─────────────────────────────────────────── */

const TR = {
  tr: {
    welcome:         'Merhaba! BuildingPath navigasyon sistemine hoş geldiniz.',
    whereGoTo:       '<strong>Nereye gitmek istiyorsunuz?</strong>',
    whereAreYou:     'Peki, şu an <strong>neredesiniz?</strong><br><small style="opacity:.65;font-size:.88em">Yakınınızda bir yeri seçerek konumunuzu belirleyebilirsiniz.</small>',
    mainEntrance:    '<i data-lucide="door-open"></i> Ana Giriş (Varsayılan)',
    typeLocation:    '<i data-lucide="keyboard"></i> Metin ile girin',
    browseCategories:'<i data-lucide="folder-open"></i> Kategori seç',
    nearestOf:       n => `<i data-lucide="crosshair"></i> En yakın: <strong>${n}</strong>`,
    computing:       'Rota hesaplanıyor…',
    routesReady:     'Rotanız hazır!',
    routeReady:      'Rotanız hazır',
    showOnMap:       '↗ Rota haritada görüntüleniyor',
    noRoute:         'Uygun rota bulunamadı.',
    sendBtn:         '→',
    placeholder:     'Yer adı yazın…',
    notFound:        q => `"${q}" bulunamadı. Farklı bir ifadeyle deneyin.`,
    ambiguous:       'Birden fazla eşleşme bulundu. Hangisini kastettiniz?',
    tryAgain:        '↩ Tekrar dene',
    backCats:        '← Kategorilere dön',
    backTypes:       '← Geri',
    atLoc:           n => `<i data-lucide="map-pin"></i> ${n}`,
    toLoc:           n => `<i data-lucide="navigation"></i> ${n}`,
    orType:          '— ya da metin ile girin —',
    newSearch:       '<i data-lucide="refresh-cw"></i> Yeni Arama',
    minutes:         'dk',
    meters:          'm',
    floorCount:      n => `${n} kat`,
    viewMap:         'Haritada Gör →',
    routeSteps:      'Rota Adımları',
    walk:            (f,d,t) => `<i data-lucide="footprints"></i> ${f} — ${d}m (~${Math.round(t)}s)`,
    elev:            (a,b,d) => `<i data-lucide="arrow-up-down"></i> Asansör: ${a} ${d==='up'?'↑':'↓'} ${b}`,
    stair:           (a,b,d) => `<i data-lucide="trending-up"></i> Merdiven: ${a} ${d==='up'?'↑':'↓'} ${b}`,
    lift:            (a,b,d) => `<i data-lucide="accessibility"></i> Lift: ${a} ${d==='up'?'↑':'↓'} ${b}`,
    exploreGreet:    'Bina hakkında bir şeyler sorun. Örn: "Kafe nerede?", "Prof. Tanaka\'nın ofisi hangi katta?"',
    expNotFound:     q => `"${q}" için bilgi bulunamadı.`,
    expOn:           f => `${f} katında`,
    expNavigate:     'Git →',
  },
  en: {
    welcome:         'Hello! Welcome to BuildingPath.',
    whereGoTo:       '<strong>Where would you like to go?</strong>',
    whereAreYou:     'And where are you <strong>now?</strong><br><small style="opacity:.65;font-size:.88em">Select a nearby place to set your current location.</small>',
    mainEntrance:    '<i data-lucide="door-open"></i> Main Entrance (Default)',
    typeLocation:    '<i data-lucide="keyboard"></i> Type a location',
    browseCategories:'<i data-lucide="folder-open"></i> Browse categories',
    nearestOf:       n => `<i data-lucide="crosshair"></i> Nearest: <strong>${n}</strong>`,
    computing:       'Computing route…',
    routesReady:     'Your route is ready!',
    routeReady:      'Your route is ready',
    showOnMap:       '↗ Route shown on the map',
    noRoute:         'No route found.',
    sendBtn:         '→',
    placeholder:     'Type a location…',
    notFound:        q => `"${q}" not found. Please try a different description.`,
    ambiguous:       'Multiple matches found. Which did you mean?',
    tryAgain:        '↩ Try again',
    backCats:        '← Back to categories',
    backTypes:       '← Back',
    atLoc:           n => `<i data-lucide="map-pin"></i> ${n}`,
    toLoc:           n => `<i data-lucide="navigation"></i> ${n}`,
    orType:          '— or type a location —',
    newSearch:       '<i data-lucide="refresh-cw"></i> New Search',
    minutes:         'min',
    meters:          'm',
    floorCount:      n => `${n} floor${n!==1?'s':''}`,
    viewMap:         'View on Map →',
    routeSteps:      'Route Steps',
    walk:            (f,d,t) => `<i data-lucide="footprints"></i> ${f} — ${d}m (~${Math.round(t)}s)`,
    elev:            (a,b,d) => `<i data-lucide="arrow-up-down"></i> Elevator: ${a} ${d==='up'?'↑':'↓'} ${b}`,
    stair:           (a,b,d) => `<i data-lucide="trending-up"></i> Stairs: ${a} ${d==='up'?'↑':'↓'} ${b}`,
    lift:            (a,b,d) => `<i data-lucide="accessibility"></i> Lift: ${a} ${d==='up'?'↑':'↓'} ${b}`,
    exploreGreet:    'Ask anything about the building. E.g. "Where is the café?", "Which floor is Prof. Tanaka\'s office?"',
    expNotFound:     q => `No information found for "${q}".`,
    expOn:           f => `On the ${f} floor`,
    expNavigate:     'Go →',
  },
};

function T(key, ...a) {
  const v = TR[S.lang][key];
  if (v == null) return key;
  return typeof v === 'function' ? v(...a) : v;
}

function translateHours(hours) {
  if (!hours || S.lang === 'en') return hours;
  return hours
    .replace(/\bMon\b/g, 'Pzt').replace(/\bTue\b/g, 'Sal').replace(/\bWed\b/g, 'Çar')
    .replace(/\bThu\b/g, 'Per').replace(/\bFri\b/g, 'Cum')
    .replace(/\bSat\b/g, 'Cmt').replace(/\bSun\b/g, 'Paz')
    .replace(/\bappointment required\b/gi, 'randevu gerekli');
}

/* ── State ────────────────────────────────────────────────── */

const S = {
  lang:          'en',
  poiData:       null,
  start:         null,   // {floor, x, y, name_tr, name_en, char?}
  dest:          null,   // {char?, state?: {floor,x,y}, name_tr, name_en}
  routes:        null,
  activeRouteId: null,
  activeFloor:   null,
  mapCache:      {},     // `${routeId}_${floor}` → base64
  inputCtx:      null,   // 'start' | 'dest'
  mode:          'nav',
  exploreData:   null,
  expHistory:    [],     // [{role:'user'|'assistant', content:string}]
  pendingDest:   null,
  plansLoaded:   false,
  plansFloor:    1,
};

/* ── DOM helpers ──────────────────────────────────────────── */

function el(id) { return document.getElementById(id); }

function scrollDown() {
  const m = el('messages');
  requestAnimationFrame(() => { m.scrollTop = m.scrollHeight; });
}

/* Add a chat bubble (role = 'bot' | 'user') */
function addBubble(role, html) {
  const row = document.createElement('div');
  row.className = `msg ${role}`;
  const bub = document.createElement('div');
  bub.className = `bubble ${role}-bubble`;
  bub.innerHTML = html;
  row.appendChild(bub);
  el('messages').appendChild(row);
  scrollDown();
  lucide.createIcons();
  return bub;
}
const botMsg  = html => addBubble('bot',  html);
const userMsg = html => addBubble('user', html);

/* Add a group of pill-style option buttons */
function addOptions(items) {
  const wrap = document.createElement('div');
  wrap.className = 'options-wrap';
  items.forEach(item => {
    const btn = document.createElement('button');
    btn.className = `opt-btn${item.primary ? ' primary' : ''}`;
    btn.innerHTML = item.label;
    btn.addEventListener('click', () => {
      wrap.querySelectorAll('button').forEach(b => {
        b.disabled = true;
        b.classList.add('used');
      });
      item.action();
    });
    wrap.appendChild(btn);
  });
  el('messages').appendChild(wrap);
  scrollDown();
  lucide.createIcons();
  return wrap;
}

/* Add a CSS-grid of cards */
function addGrid(items, cols = 4) {
  const wrap = document.createElement('div');
  wrap.className = `grid-wrap cols-${cols}`;
  items.forEach(item => {
    const btn = document.createElement('button');
    btn.className = 'grid-card';
    btn.innerHTML =
      `<span class="gc-icon"><i data-lucide="${item.icon || 'circle'}"></i></span>` +
      `<span class="gc-label">${item.label}</span>` +
      (item.sub ? `<span class="gc-sub">${item.sub}</span>` : '');
    btn.addEventListener('click', () => {
      wrap.querySelectorAll('button').forEach(b => {
        b.disabled = true;
        b.classList.add('used');
      });
      item.action();
    });
    wrap.appendChild(btn);
  });
  el('messages').appendChild(wrap);
  scrollDown();
  lucide.createIcons();
  return wrap;
}

/* Loading spinner inside a bubble */
let _spinnerRow = null;
function showSpinner(text) {
  const row = document.createElement('div');
  row.className = 'msg bot';
  row.innerHTML =
    `<div class="bubble bot-bubble spinner-bubble">` +
    `<span class="spinner"></span>${text}</div>`;
  el('messages').appendChild(row);
  _spinnerRow = row;
  scrollDown();
}
function hideSpinner() {
  if (_spinnerRow) { _spinnerRow.remove(); _spinnerRow = null; }
}

/* ── Language ─────────────────────────────────────────────── */

function setLang(lang) {
  S.lang = lang;
  el('lang-tr').classList.toggle('active', lang === 'tr');
  el('lang-en').classList.toggle('active', lang === 'en');
  // Swap [data-tr] / [data-en] elements
  document.querySelectorAll('[data-tr]').forEach(node => {
    node.innerHTML = lang === 'tr' ? node.dataset.tr : node.dataset.en;
  });
  el('text-input').placeholder = T('placeholder');
  // Update explore input placeholders
  const expInput = el('exp-input');
  if (expInput) expInput.placeholder = lang === 'tr' ? 'Soru sorun…' : 'Ask a question…';
  const expSearch = el('exp-search');
  if (expSearch) expSearch.placeholder = lang === 'tr' ? 'Ara…' : 'Search…';
  // Update floor filter "All Floors" option text
  const expFloor = el('exp-floor-filter');
  if (expFloor && expFloor.options.length > 0) {
    expFloor.options[0].text = lang === 'tr' ? 'Tüm Katlar' : 'All Floors';
  }
  // Re-render explore tree with current filters if active
  if (S.exploreData) {
    renderExploreTree(
      el('exp-floor-filter') ? el('exp-floor-filter').value : '',
      el('exp-search') ? el('exp-search').value : ''
    );
  }
  // Refresh explore chat greeting
  const expMsgs = el('exp-messages');
  if (expMsgs && expMsgs.children.length > 0) {
    expMsgs.innerHTML = '';
    addExpBubble('bot', T('exploreGreet'));
  }
  // Rebuild plans floor tabs with new language
  if (S.plansLoaded && S.poiData) {
    S.plansLoaded = false;
    initPlansView();
  }
  // If user hasn't made any selection yet, restart chat in new language
  if (!S.start && !S.dest && S.poiData) {
    el('messages').innerHTML = '';
    botMsg(T('welcome'));
    askDest();
  }
}

/* ── Initialise ───────────────────────────────────────────── */

async function init() {
  setLang(S.lang);
  try {
    const r = await fetch('/api/pois');
    S.poiData = await r.json();
  } catch (e) {
    botMsg('<i data-lucide="triangle-alert"></i> Could not load building data. Please refresh the page.');
    return;
  }

  botMsg(T('welcome'));
  askDest();
}

/* ── Main chat flow ───────────────────────────────────────── */

function resetNav() {
  S.start         = null;
  S.dest          = null;
  S.routes        = null;
  S.activeRouteId = null;
  S.activeFloor   = null;
  S.mapCache      = {};
  S.inputCtx      = null;
  S.pendingDest   = null;
  el('messages').innerHTML = '';
  el('input-bar').classList.add('hidden');
  el('map-view').classList.add('hidden');
  el('map-welcome').classList.remove('hidden');
  askDest();
}

function askStart() {
  S.inputCtx = 'start';
  botMsg(T('whereAreYou'));
  showLocOptions('start');
}

function askDest() {
  if (S.pendingDest) {
    const pd = S.pendingDest;
    S.pendingDest = null;
    selectLoc('dest', pd);
    return;
  }
  S.inputCtx = 'dest';
  botMsg(T('whereGoTo'));
  showLocOptions('dest');
}

function showLocOptions(ctx) {
  const opts = [];
  if (ctx === 'start') {
    opts.push({
      label:   T('mainEntrance'),
      primary: true,
      action:  () => selectLoc(ctx, {
        ...S.poiData.default_start,
        name_tr: 'Ana Giriş',
        name_en: 'Main Entrance',
      }),
    });
  }
  opts.push(
    { label: T('typeLocation'),     action: () => showTextInput(ctx) },
    { label: T('browseCategories'), action: () => showCategories(ctx) },
  );
  addOptions(opts);
}

/* Commit a location selection (start or dest). */
function selectLoc(ctx, loc) {
  const name = S.lang === 'tr'
    ? (loc.name_tr || loc.name_en || '')
    : (loc.name_en || loc.name_tr || '');

  if (ctx === 'dest') {
    userMsg(T('toLoc', name));
    S.dest = loc;
    askStart();
  } else {
    userMsg(T('atLoc', name));
    S.start = loc;
    doNavigate();
  }
}

/* ── Text input ───────────────────────────────────────────── */

function showTextInput(ctx) {
  S.inputCtx = ctx;
  el('input-bar').classList.remove('hidden');
  el('text-input').focus();
}

async function submitText() {
  const q = el('text-input').value.trim();
  if (!q) return;
  el('text-input').value = '';
  el('input-bar').classList.add('hidden');
  userMsg(q);

  const resp = await fetch('/api/resolve', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ query: q, ctx: S.inputCtx }),
  });
  const data = await resp.json();

  if (!data.ok) {
    if (data.ambiguous && data.suggestions?.length) {
      botMsg(T('ambiguous'));
      addOptions(data.suggestions.map(s => ({
        label:  `<i data-lucide="${s.icon}"></i> ${S.lang === 'tr' ? s.name_tr : s.name_en}`,
        action: async () => {
          // Re-resolve to get actual floor/coordinate data for the chosen type
          try {
            const r2 = await fetch('/api/resolve', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ query: s.name_en, ctx: S.inputCtx }),
            });
            const d2 = await r2.json();
            if (d2.ok) {
              const loc = {
                char:    d2.char    || s.char,
                name_tr: d2.name_tr || s.name_tr,
                name_en: d2.name_en || s.name_en,
                ...(d2.state ? { state: d2.state } : {}),
              };
              // If multiple labeled instances, let the normal flow handle them
              if (d2.labeled && d2.labeled.length > 1) {
                // Inject the resolved data and re-run the normal multi-instance path
                handleResolveData(d2, S.inputCtx);
              } else if (d2.labeled && d2.labeled.length === 1) {
                const lp = d2.labeled[0];
                selectLoc(S.inputCtx, { ...loc, state: { floor: lp.floor, x: lp.x, y: lp.y }, all_states: lp.all_states || null, name_tr: lp.name_tr || lp.name, name_en: lp.name });
              } else {
                selectLoc(S.inputCtx, loc);
              }
              return;
            }
          } catch (_) {}
          // Fallback: use char-only (backend will snap)
          selectLoc(S.inputCtx, { char: s.char, name_tr: s.name_tr, name_en: s.name_en });
        },
      })));
    } else {
      botMsg(T('notFound', q));
      addOptions([
        { label: T('tryAgain'),        action: () => showTextInput(S.inputCtx) },
        { label: T('browseCategories'),action: () => showCategories(S.inputCtx) },
      ]);
    }
    return;
  }

  handleResolveData(data, S.inputCtx);
}

/* Shared handler for resolve API response — used by submitText and ambiguous re-resolve */
function handleResolveData(data, ctx) {
  const baseLoc = {
    char:    data.char,
    name_tr: data.name_tr,
    name_en: data.name_en,
    ...(data.state ? { state: data.state } : {}),
  };

  if (data.labeled && data.labeled.length > 1) {
    const typeName = S.lang === 'tr' ? data.name_tr : data.name_en;
    botMsg(
      S.lang === 'tr'
        ? `"${typeName}" için birden fazla konum var. Hangisi?`
        : `Multiple locations for "${typeName}". Which one?`
    );

    // Unified flat list for both 'start' and 'dest' contexts.
    // Label: "Room Name (Floor)" — no descriptions, no wrapping.
    const items = [];

    if (ctx === 'dest') {
      items.push({
        label:   T('nearestOf', typeName),
        primary: true,
        action:  () => selectLoc(ctx, baseLoc),
      });
    }

    data.labeled.forEach(lp => {
      const name  = S.lang === 'tr' ? (lp.name_tr || lp.name) : lp.name;
      const floor = S.lang === 'tr' ? lp.floor_tr : lp.floor_en;
      items.push({
        label: `${name} <small>(${floor})</small>`,
        action: () => selectLoc(ctx, {
          ...baseLoc,
          state:      { floor: lp.floor, x: lp.x, y: lp.y },
          all_states: lp.all_states || null,
          name_tr:    lp.name_tr || lp.name,
          name_en:    lp.name,
        }),
      });
    });

    addOptions(items);

  } else if (data.labeled && data.labeled.length === 1) {
    const lp = data.labeled[0];
    selectLoc(ctx, {
      ...baseLoc,
      state:      { floor: lp.floor, x: lp.x, y: lp.y },
      all_states: lp.all_states || null,
      name_tr:    lp.name_tr || lp.name,
      name_en:    lp.name,
    });

  } else {
    selectLoc(ctx, baseLoc);
  }
}

/* ── Category browser ─────────────────────────────────────── */

function showCategories(ctx) {
  addGrid(
    S.poiData.categories.map(cat => ({
      icon:   resolveIcon(cat),
      label:  S.lang === 'tr' ? cat.name_tr : cat.name_en,
      action: () => showCatTypes(ctx, cat),
    })),
    4
  );
}

function showCatTypes(ctx, cat) {
  const catName = S.lang === 'tr' ? cat.name_tr : cat.name_en;
  botMsg(catName);
  addOptions([{ label: T('backCats'), action: () => showCategories(ctx) }]);

  addGrid(
    cat.types.map(type => ({
      icon:   resolveIcon(type),
      label:  S.lang === 'tr' ? type.name_tr : type.name_en,
      sub:    (S.lang === 'tr' ? type.floors_tr : type.floors_en).join(', '),
      action: () => showPoiInstances(ctx, type),
    })),
    2
  );
}

function showPoiInstances(ctx, type) {
  const typeName = S.lang === 'tr' ? type.name_tr : type.name_en;
  botMsg(`<i data-lucide="${resolveIcon(type)}"></i> ${typeName}`);

  const items = [];

  if (ctx === 'dest') {
    items.push({
      label:   T('nearestOf', typeName),
      primary: true,
      action:  () => selectLoc(ctx, {
        char:    type.char,
        name_tr: type.name_tr,
        name_en: type.name_en,
      }),
    });
  }

  if (type.floors.length === 1) {
    /* Single floor – skip floor selection, list instances directly */
    _addInstancesForFloor(ctx, type, type.floors[0], 0, items);
    addOptions(items);
    return;
  }

  /* Multiple floors – show floor buttons first */
  type.floors.forEach((f, i) => {
    const fname = S.lang === 'tr' ? type.floors_tr[i] : type.floors_en[i];
    items.push({
      label:  fname,
      action: () => showFloorInstances(ctx, type, f, i),
    });
  });

  addOptions(items);
}

function showFloorInstances(ctx, type, floor, floorIdx) {
  const typeName  = S.lang === 'tr' ? type.name_tr  : type.name_en;
  const floorName = S.lang === 'tr' ? type.floors_tr[floorIdx] : type.floors_en[floorIdx];

  botMsg(`<i data-lucide="${resolveIcon(type)}"></i> ${typeName} — ${floorName}`);
  addOptions([{ label: T('backTypes'), action: () => showPoiInstances(ctx, type) }]);

  const items = [];
  _addInstancesForFloor(ctx, type, floor, floorIdx, items);
  addOptions(items);
}

function _addInstancesForFloor(ctx, type, floor, floorIdx, items) {
  const floorName    = S.lang === 'tr' ? type.floors_tr[floorIdx] : type.floors_en[floorIdx];
  const floorName_en = type.floors_en[floorIdx];

  const floorLabeled = type.labeled.filter(lp => lp.floor === floor);

  if (floorLabeled.length > 0) {
    floorLabeled.forEach(lp => {
      items.push({
        label:  S.lang === 'tr' ? (lp.name_tr || lp.name) : lp.name,
        action: () => selectLoc(ctx, {
          char:       type.char,
          state:      { floor: lp.floor, x: lp.x, y: lp.y },
          all_states: lp.all_states || null,
          name_tr:    lp.name_tr || lp.name,
          name_en:    lp.name,
        }),
      });
    });
    return;
  }

  /* No labeled instances – use BFS components if multiple, else single option */
  const comps = type.components_by_floor?.[String(floor)];
  if (comps && comps.length > 1) {
    comps.forEach((comp, idx) => {
      const num    = idx + 1;
      const label  = `<i data-lucide="${resolveIcon(type)}"></i> ${floorName} ${num}`;
      items.push({
        label,
        action: () => selectLoc(ctx, {
          char:    type.char,
          state:   { floor: floor, x: comp.x, y: comp.y },
          name_tr: `${type.name_tr} ${num} (${floorName})`,
          name_en: `${type.name_en} ${num} (${floorName_en})`,
        }),
      });
    });
  } else {
    const cell = type.first_cell_by_floor?.[floor] || type.first_cell;
    items.push({
      label:  `<i data-lucide="${resolveIcon(type)}"></i> ${floorName}`,
      action: () => selectLoc(ctx, {
        char:    type.char,
        state:   { floor: floor, x: cell.x, y: cell.y },
        name_tr: `${type.name_tr} (${floorName})`,
        name_en: `${type.name_en} (${floorName_en})`,
      }),
    });
  }
}

/* ── Navigation ───────────────────────────────────────────── */

async function doNavigate() {
  showSpinner(T('computing'));

  const body = {
    start: S.start
      ? { floor: S.start.state?.floor ?? S.start.floor,
          x:     S.start.state?.x     ?? S.start.x,
          y:     S.start.state?.y     ?? S.start.y,
          char:    S.start.char   || null,
          name_tr: S.start.name_tr,
          name_en: S.start.name_en }
      : null,
    destination: {
      char:       S.dest.char,
      state:      S.dest.state,
      all_states: S.dest.all_states || null,
      name_tr:    S.dest.name_tr,
      name_en:    S.dest.name_en,
    },
  };

  try {
    const resp = await fetch('/api/navigate', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    });
    const data = await resp.json();
    hideSpinner();

    if (!data.ok) {
      botMsg(S.lang === 'tr'
        ? (data.error_tr || 'Hata oluştu.')
        : (data.error_en || 'An error occurred.'));
      return;
    }

    S.routes        = data.routes;
    S.activeRouteId = data.routes.find(r => r.available)?.id || 'fastest';
    S.activeFloor   = null;
    S.mapCache      = {};

    botMsg(T('routesReady'));
    showRouteCards(data.routes);
    await initMapView(data.routes);

    addOptions([{ label: T('newSearch'), action: () => resetNav() }]);

  } catch (e) {
    hideSpinner();
    botMsg(`<i data-lucide="triangle-alert"></i> Error: ${e.message}`);
  }
}

/* ── Single route card in chat ───────────────────────────── */

function fmtDur(totalS) {
  const m   = Math.floor(totalS / 60);
  const sec = Math.round(totalS % 60);
  if (m === 0) return `${sec} s`;
  if (sec === 0) return `${m} ${T('minutes')}`;
  return `${m} ${T('minutes')} ${sec} s`;
}

function showRouteCards(routes) {
  const wrap = document.createElement('div');
  wrap.className = 'route-single-card-wrap';

  const route = routes.find(r => r.available);

  if (!route) {
    wrap.innerHTML = `<div class="route-single-card"><div class="rsc-unavail">${T('noRoute')}</div></div>`;
    el('messages').appendChild(wrap);
    scrollDown();
    return;
  }

  const durStr    = fmtDur(route.duration_s || 0);
  const distStr   = `${route.distance_m} ${T('meters')}`;
  const floorStr  = T('floorCount', route.floors_visited.length);

  const card = document.createElement('div');
  card.className = 'route-single-card';
  card.innerHTML =
    `<div class="rsc-title"><i data-lucide="map"></i> ${T('routeReady')}</div>` +
    `<div class="rsc-stats">` +
      `<div class="rsc-row"><i data-lucide="timer"></i> ${durStr}</div>` +
      `<div class="rsc-row"><i data-lucide="map-pin"></i> ${distStr}</div>` +
      `<div class="rsc-row"><i data-lucide="layers"></i> ${floorStr}</div>` +
    `</div>` +
    `<button class="rsc-btn">${T('showOnMap')}</button>`;


  wrap.appendChild(card);
  el('messages').appendChild(wrap);
  scrollDown();
}

/* ── Map panel ────────────────────────────────────────────── */

async function initMapView(routes) {
  el('map-welcome').classList.add('hidden');
  el('map-view').classList.remove('hidden');

  // Restore legend in case floor browser hid it
  const legend = el('map-view').querySelector('.map-legend');
  if (legend) legend.classList.remove('hidden');

  const first = routes.find(r => r.available);
  if (first) await selectRoute(first.id);
}

function buildFloorTabs(route) {
  const tabs = el('map-floor-tabs');
  tabs.innerHTML = '';
  const names = S.lang === 'tr'
    ? (S.poiData.floor_tr || TR.tr.floorNames)
    : (S.poiData.floor_en || TR.en.floorNames);

  const startFloor = route.start_state[0];
  const endFloor   = route.end_state[0];
  const ascending  = startFloor <= endFloor;
  const floors     = [...route.floors_visited].sort((a, b) => ascending ? a - b : b - a);

  floors.forEach(f => {
    const btn = document.createElement('button');
    btn.className = 'ftab';
    btn.id        = `ftab-${f}`;
    btn.textContent = names[f] || `F${f}`;
    btn.addEventListener('click', () => loadFloor(route, f));
    tabs.appendChild(btn);
  });
}

async function selectRoute(routeId) {
  S.activeRouteId = routeId;

  const route = S.routes.find(r => r.id === routeId);
  if (!route || !route.available) return;

  buildFloorTabs(route);
  buildMapStats(route);

  const startFloor = route.start_state[0];
  await loadFloor(route, startFloor);
}

async function loadFloor(route, floor) {
  S.activeFloor = floor;

  /* Highlight floor tab */
  document.querySelectorAll('.ftab').forEach(t => t.classList.remove('active'));
  const fTab = el(`ftab-${floor}`);
  if (fTab) fTab.classList.add('active');

  const cacheKey = `${route.id}_${floor}`;
  if (S.mapCache[cacheKey]) {
    el('map-img').src = `data:image/png;base64,${S.mapCache[cacheKey]}`;
    return;
  }

  /* Show loading overlay */
  el('map-loading').classList.remove('hidden');
  el('map-img').src = '';

  const pathPts  = route.path_by_floor[String(floor)] || [];
  const transPts = route.trans_points[String(floor)]  || [];

  const startF = route.start_state[0];
  const endF   = route.end_state[0];
  const startPt = (floor === startF && pathPts.length)
    ? pathPts[0] : null;
  const endPt   = (floor === endF && pathPts.length)
    ? pathPts[pathPts.length - 1] : null;

  try {
    const resp = await fetch('/api/map-image', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        floor:             floor,
        path_points:       pathPts,
        color:             route.color,
        start_point:       startPt,
        end_point:         endPt,
        transition_points: transPts,
      }),
    });
    const data = await resp.json();
    if (data.ok) {
      S.mapCache[cacheKey] = data.image;
      el('map-img').src = `data:image/png;base64,${data.image}`;
    }
  } catch (e) {
    console.error('Map image error:', e);
  } finally {
    el('map-loading').classList.add('hidden');
  }
}

/* ── Floor map browser (used during start-location disambiguation) ─── */

async function showFloorBrowser(initialFloor) {
  el('map-welcome').classList.add('hidden');
  el('map-view').classList.remove('hidden');

  // Hide route legend and stats — this is browse mode, not route mode
  const legend = el('map-view').querySelector('.map-legend');
  if (legend) legend.classList.add('hidden');
  const stats = el('map-stats');
  if (stats) stats.innerHTML = '';

  // Build tabs for all 6 floors
  const tabs  = el('map-floor-tabs');
  tabs.innerHTML = '';
  const names = S.lang === 'tr'
    ? (S.poiData?.floor_tr || ['Alt Zemin','Zemin','Birinci','İkinci','Üçüncü','Dördüncü'])
    : (S.poiData?.floor_en || ['Lower Ground','Ground','First','Second','Third','Fourth']);

  for (let f = 0; f < names.length; f++) {
    const btn = document.createElement('button');
    btn.className   = 'ftab';
    btn.id          = `ftab-${f}`;
    btn.textContent = names[f];
    btn.addEventListener('click', () => loadFloorBrowse(f));
    tabs.appendChild(btn);
  }

  await loadFloorBrowse(initialFloor ?? 1);
}

async function loadFloorBrowse(floor) {
  S.activeFloor = floor;

  document.querySelectorAll('.ftab').forEach(t => t.classList.remove('active'));
  const fTab = el(`ftab-${floor}`);
  if (fTab) fTab.classList.add('active');

  el('map-loading').classList.remove('hidden');
  el('map-img').src = '';

  try {
    const resp = await fetch(`/api/floor-map/${floor}`);
    const data = await resp.json();
    if (data.ok) {
      el('map-img').src = `data:image/png;base64,${data.image}`;
    }
  } catch (e) {
    console.error('Floor browse error:', e);
  } finally {
    el('map-loading').classList.add('hidden');
  }
}

/* ── Kat Planları tab ─────────────────────────────────────── */

async function initPlansView() {
  S.plansLoaded = true;

  const tabs  = el('plans-floor-tabs');
  tabs.innerHTML = '';
  const names = S.lang === 'tr'
    ? (S.poiData?.floor_tr || ['Alt Zemin','Zemin','Birinci','İkinci','Üçüncü','Dördüncü'])
    : (S.poiData?.floor_en || ['Lower Ground','Ground','First','Second','Third','Fourth']);

  // Reverse order: highest floor at top (elevator logic)
  for (let f = names.length - 1; f >= 0; f--) {
    const btn = document.createElement('button');
    btn.className   = 'ftab';
    btn.id          = `ptab-${f}`;
    btn.textContent = names[f];
    btn.addEventListener('click', () => loadPlanFloor(f));
    tabs.appendChild(btn);
  }

  await loadPlanFloor(S.plansFloor);
}

async function loadPlanFloor(floor) {
  S.plansFloor = floor;

  document.querySelectorAll('#plans-floor-tabs .ftab').forEach(t => t.classList.remove('active'));
  const fTab = el(`ptab-${floor}`);
  if (fTab) fTab.classList.add('active');

  el('plans-loading').classList.remove('hidden');
  el('plans-img').src = '';

  try {
    const resp = await fetch(`/api/floor-map/${floor}`);
    const data = await resp.json();
    if (data.ok) {
      el('plans-img').src = `data:image/png;base64,${data.image}`;
    }
  } catch (e) {
    console.error('Floor plan error:', e);
  } finally {
    el('plans-loading').classList.add('hidden');
  }
}

function buildMapStats(route) {
  const stats = el('map-stats');
  if (!stats) return;

  const names = S.lang === 'tr'
    ? (S.poiData.floor_tr || [])
    : (S.poiData.floor_en || []);

  const fname = f => names[f] || `F${f}`;

  let html =
    `<div class="mstat-title">${T('routeSteps')}</div>` +
    `<div class="mstat-steps">`;

  (route.segments || []).forEach(seg => {
    if (seg.kind === 'walk') {
      html +=
        `<div class="mstep walk">${T('walk', fname(seg.floor), seg.distance_m, seg.duration_s)}</div>`;
    } else if (seg.kind === 'elevator') {
      const a = S.lang === 'tr' ? seg.from_tr : seg.from_en;
      const b = S.lang === 'tr' ? seg.to_tr   : seg.to_en;
      html +=
        `<div class="mstep elev">${T('elev', a, b, seg.direction)}</div>`;
    } else if (seg.kind === 'stair') {
      const a = S.lang === 'tr' ? seg.from_tr : seg.from_en;
      const b = S.lang === 'tr' ? seg.to_tr   : seg.to_en;
      html +=
        `<div class="mstep stair">${T('stair', a, b, seg.direction)}</div>`;
    } else {
      const a = S.lang === 'tr' ? seg.from_tr : seg.from_en;
      const b = S.lang === 'tr' ? seg.to_tr   : seg.to_en;
      html +=
        `<div class="mstep lift">${T('lift', a, b, seg.direction)}</div>`;
    }
  });

  html += `</div>`;

  const dur  = route.duration_min < 1
    ? `<1 ${T('minutes')}`
    : `${route.duration_min.toFixed(1)} ${T('minutes')}`;
  html +=
    `<div class="mstat-total"><i data-lucide="timer"></i> ${dur} &nbsp;·&nbsp; <i data-lucide="ruler"></i> ${route.distance_m} ${T('meters')}</div>`;

  stats.innerHTML = html;
  lucide.createIcons();
}

/* ── Mode switching ───────────────────────────────────────── */

function switchMode(mode) {
  S.mode = mode;
  ['mode-nav', 'mode-explore', 'mode-plans'].forEach(id => {
    const div = el(id);
    if (div) div.classList.add('hidden');
  });
  ['tab-nav', 'tab-explore', 'tab-plans'].forEach(id => {
    const btn = el(id);
    if (btn) btn.classList.remove('active');
  });

  if (mode === 'nav') {
    el('mode-nav').classList.remove('hidden');
    el('tab-nav').classList.add('active');
  } else if (mode === 'explore') {
    el('mode-explore').classList.remove('hidden');
    el('tab-explore').classList.add('active');
    if (!S.exploreData) loadExplore();
    const expMsgs = el('exp-messages');
    if (expMsgs && expMsgs.children.length === 0) {
      S.expHistory = [];
      addExpBubble('bot', T('exploreGreet'));
    }
  } else if (mode === 'plans') {
    el('mode-plans').classList.remove('hidden');
    el('tab-plans').classList.add('active');
    if (!S.plansLoaded) initPlansView();
  }
}

/* ── Explore data loading ──────────────────────────────────── */

async function loadExplore() {
  try {
    const r = await fetch('/api/explore');
    const data = await r.json();
    S.exploreData = data;
    // Populate floor filter
    const sel = el('exp-floor-filter');
    if (sel) {
      // Clear existing options beyond the "All floors" one
      while (sel.options.length > 1) sel.remove(1);
      const floorNames = S.lang === 'tr' ? data.floor_tr : data.floor_en;
      floorNames.forEach((name, idx) => {
        const opt = document.createElement('option');
        opt.value = String(idx);
        opt.textContent = name;
        sel.appendChild(opt);
      });
    }
    renderExploreTree();
  } catch (e) {
    const tree = el('explore-tree');
    if (tree) tree.innerHTML = '<div class="explore-loading">Yüklenemedi.</div>';
  }
}

/* ── Explore tree rendering ────────────────────────────────── */

/* Lucide icon name for each category/POI — frontend source of truth */
const LUCIDE_ICONS = {
  // Categories
  entrance:  'door-open',
  food:      'coffee',
  amenity:   'droplets',
  teaching:  'graduation-cap',
  labs:      'flask-conical',
  offices:   'briefcase',
  library:   'book-marked',
  study:     'book-open',
  special:   'leaf',
  // POI chars
  N: 'door-open',  X: 'flame',         T: 'droplets',   V: 'trees',
  S: 'trending-up',E: 'arrow-up-down', O: 'briefcase',  B: 'armchair',
  Z: 'book-open',  A: 'users',         H: 'presentation',M: 'users-round',
  G: 'flask-conical',C:'monitor',      e: 'video',      J: 'dna',
  P: 'test-tube',  K: 'activity',      L: 'microscope', I: 'scan',
  W: 'wrench',     Y: 'leaf',          q: 'sun',        z: 'settings-2',
  F: 'coffee',     R: 'bell-ring',     Q: 'sun',        D: 'cloud-sun',
  U: 'book-marked',j: 'utensils',     '.': 'footprints',
};

function resolveIcon(cat) {
  return LUCIDE_ICONS[cat.id] || LUCIDE_ICONS[cat.char] || 'circle';
}

function renderExploreTree(floorFilter = '', searchText = '') {
  if (!S.exploreData) return;
  const tree = el('explore-tree');
  if (!tree) return;
  tree.innerHTML = '';

  const lang  = S.lang;
  const srch  = searchText.trim().toLowerCase();
  const floor = floorFilter === '' ? null : parseInt(floorFilter, 10);

  S.exploreData.categories.forEach(cat => {
    // Filter: collect instances passing filter
    const filteredTypes = [];
    cat.types.forEach(type => {
      const filteredGroups = [];
      type.groups.forEach(group => {
        const filteredInsts = group.instances.filter(inst => {
          if (floor !== null && inst.floor !== floor) return false;
          if (srch) {
            const n1 = (inst.name    || '').toLowerCase();
            const n2 = (inst.name_tr || '').toLowerCase();
            if (!n1.includes(srch) && !n2.includes(srch)) return false;
          }
          return true;
        });
        if (filteredInsts.length > 0) {
          filteredGroups.push({ ...group, instances: filteredInsts });
        }
      });
      if (filteredGroups.length > 0) {
        filteredTypes.push({ ...type, groups: filteredGroups });
      }
    });

    if (filteredTypes.length === 0) return;

    // Category section
    const catSection = document.createElement('div');
    catSection.className = 'exp-category';

    const catHeader = document.createElement('div');
    catHeader.className = 'exp-cat-header';
    catHeader.innerHTML =
      `<span class="exp-cat-icon exp-cat-icon--${cat.id}"><i data-lucide="${resolveIcon(cat)}"></i></span>` +
      `<span class="exp-cat-name">${lang === 'tr' ? cat.name_tr : cat.name_en}</span>` +
      `<span class="exp-chevron">▶</span>`;

    const catBody = document.createElement('div');
    catBody.className = 'exp-cat-body hidden';

    catHeader.addEventListener('click', () => {
      const open = !catBody.classList.contains('hidden');
      if (!open) {
        document.querySelectorAll('.exp-cat-body').forEach(b => b.classList.add('hidden'));
        document.querySelectorAll('.exp-chevron').forEach(c => c.textContent = '▶');
      }
      catBody.classList.toggle('hidden', open);
      catHeader.querySelector('.exp-chevron').textContent = open ? '▶' : '▼';
    });

    filteredTypes.forEach(type => {
      if (type.groups.length > 1) {
        const typeHeader = document.createElement('div');
        typeHeader.className = 'exp-type-header';
        typeHeader.innerHTML =
          `<i data-lucide="${resolveIcon(type)}"></i> ${lang === 'tr' ? type.name_tr : type.name_en}`;
        catBody.appendChild(typeHeader);
      }

      type.groups.forEach(group => {
        if (group.key !== '_all' && group.name_en) {
          const groupHeader = document.createElement('div');
          groupHeader.className = 'exp-group-header';
          groupHeader.textContent = lang === 'tr' ? group.name_tr : group.name_en;
          catBody.appendChild(groupHeader);
        }

        group.instances.forEach(inst => {
          const dispName = lang === 'tr' ? (inst.name_tr || inst.name) : inst.name;

          const instEl = document.createElement('div');
          instEl.className = 'exp-instance';
          instEl.dataset.floor = String(inst.floor);

          const instHeader = document.createElement('div');
          instHeader.className = 'exp-inst-header';

          const nameRow = document.createElement('div');
          nameRow.className = 'exp-inst-name-row';

          const nameEl = document.createElement('span');
          nameEl.className = 'exp-inst-name';
          nameEl.textContent = dispName;
          nameRow.appendChild(nameEl);

          const floorName = lang === 'tr'
            ? (inst.floor_tr || '')
            : (inst.floor_en || '');
          if (floorName) {
            const floorBadge = document.createElement('span');
            floorBadge.className = 'exp-floor-badge';
            floorBadge.textContent = floorName;
            nameRow.appendChild(floorBadge);
          }
          instHeader.appendChild(nameRow);

          const descText = lang === 'tr'
            ? (inst.description_tr || inst.description || '')
            : (inst.description || '');
          if (descText) {
            const descEl = document.createElement('div');
            descEl.className = 'exp-inst-desc-inline';
            descEl.textContent = descText;
            instHeader.appendChild(descEl);
          }

          if (inst.open_hours) {
            const hoursEl = document.createElement('div');
            hoursEl.className = 'exp-inst-hours';
            hoursEl.innerHTML = '<i data-lucide="clock"></i> ' + translateHours(inst.open_hours);
            instHeader.appendChild(hoursEl);
          }

          const instBody = document.createElement('div');
          instBody.className = 'exp-inst-body hidden';

          const navBtn = document.createElement('button');
          navBtn.className = 'exp-nav-btn';
          navBtn.textContent = lang === 'tr' ? 'Git →' : 'Go →';
          navBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            startNavFromExplore(
              inst.char, inst.floor, inst.x, inst.y,
              inst.name_tr || inst.name, inst.name,
              inst.all_states
            );
          });
          instBody.appendChild(navBtn);

          instHeader.addEventListener('click', () => {
            instBody.classList.toggle('hidden');
          });

          instEl.appendChild(instHeader);
          instEl.appendChild(instBody);
          catBody.appendChild(instEl);
        });
      });
    });

    catSection.appendChild(catHeader);
    catSection.appendChild(catBody);
    tree.appendChild(catSection);
  });

  if (tree.children.length === 0) {
    tree.innerHTML = '<div class="explore-loading">Sonuç bulunamadı.</div>';
  }
  lucide.createIcons();
}

/* ── Navigate from explore ─────────────────────────────────── */

function startNavFromExplore(char, floor, x, y, nameTr, nameEn, allStates) {
  S.pendingDest = {
    char,
    state:      { floor, x, y },
    all_states: allStates,
    name_tr:    nameTr,
    name_en:    nameEn,
  };
  switchMode('nav');
  // If already navigating, just switch modes
  if (S.dest !== null) return;
  // Reset and start fresh
  el('messages').innerHTML = '';
  S.start = null;
  botMsg(S.lang === 'tr'
    ? `<i data-lucide="navigation"></i> Hedef: <strong>${nameTr}</strong> — Şu an neredesiniz?`
    : `<i data-lucide="navigation"></i> Destination: <strong>${nameEn}</strong> — Where are you now?`);
  showLocOptions('start');
}

/* ── Explore chat bubble ───────────────────────────────────── */

function addExpBubble(role, html) {
  const expMsgs = el('exp-messages');
  if (!expMsgs) return null;
  const row = document.createElement('div');
  row.className = `msg ${role}`;
  const bub = document.createElement('div');
  bub.className = `bubble ${role}-bubble`;
  bub.innerHTML = html;
  row.appendChild(bub);
  expMsgs.appendChild(row);
  requestAnimationFrame(() => { expMsgs.scrollTop = expMsgs.scrollHeight; });
  lucide.createIcons();
  return bub;
}

/* ── Explore info submit ───────────────────────────────────── */

async function expSubmit() {
  const input = el('exp-input');
  if (!input) return;
  const q = input.value.trim();
  if (!q) return;
  input.value = '';

  addExpBubble('user', q);
  S.expHistory.push({ role: 'user', content: q });

  try {
    const resp = await fetch('/api/ask', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        query:   q,
        lang:    S.lang,
        history: S.expHistory.slice(-10),  // son 5 alışveriş (10 mesaj)
      }),
    });
    const data = await resp.json();

    if (!data.ok && !data.text) {
      addExpBubble('bot', T('expNotFound', q));
      S.expHistory.push({ role: 'assistant', content: T('expNotFound', q) });
      return;
    }

    const botText = data.text || T('expNotFound', q);
    const bub = addExpBubble('bot', botText);
    S.expHistory.push({ role: 'assistant', content: botText });

    // Navigate butonu — ilk lokasyon için
    if (bub && data.locations && data.locations.length > 0) {
      const loc = data.locations[0];
      const btn = document.createElement('button');
      btn.className = 'exp-nav-btn';
      btn.textContent = T('expNavigate');
      btn.addEventListener('click', () => {
        startNavFromExplore(
          loc.char, loc.floor, loc.x, loc.y,
          loc.name_tr || loc.name, loc.name,
          loc.all_states
        );
      });
      bub.appendChild(btn);
    }
  } catch (e) {
    addExpBubble('bot', `<i data-lucide="triangle-alert"></i> Error: ${e.message}`);
  }
}

/* ── Event wiring ─────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  el('send-btn').addEventListener('click', submitText);
  el('text-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') submitText();
    if (e.key === 'Escape') {
      el('input-bar').classList.add('hidden');
    }
  });

  // Explore event listeners
  el('exp-send-btn').addEventListener('click', expSubmit);
  el('exp-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') expSubmit();
  });
  el('exp-search').addEventListener('input', () => {
    renderExploreTree(el('exp-floor-filter').value, el('exp-search').value);
  });
  el('exp-floor-filter').addEventListener('change', () => {
    renderExploreTree(el('exp-floor-filter').value, el('exp-search').value);
  });

  // ── Landing page → App transition ─────────────────────
  const launchBtn = el('launch-btn');
  if (launchBtn) {
    launchBtn.addEventListener('click', () => {
      const lp   = document.getElementById('landing-page');
      const main = document.getElementById('main-app');

      // Slide landing page up and fade out
      lp.classList.add('lp-exit');

      // Fade in main app simultaneously
      main.classList.add('lp-visible');

      // Remove landing page from DOM after animation completes
      setTimeout(() => {
        lp.style.display = 'none';
        showOnboarding();
      }, 900);
    });
  }

  // ── Onboarding modal ──────────────────────────────────
  function showOnboarding() {
    const overlay = el('onboarding-overlay');
    if (!overlay) return;
    overlay.classList.remove('hidden');
    lucide.createIcons();                 // render icons inside modal
    setLang(S.lang);                      // apply current language to modal text
  }

  const obClose = el('ob-close');
  if (obClose) {
    obClose.addEventListener('click', () => {
      el('onboarding-overlay').classList.add('hidden');
    });
  }
  el('onboarding-overlay')?.addEventListener('click', e => {
    if (e.target === el('onboarding-overlay'))
      el('onboarding-overlay').classList.add('hidden');
  });

  init();
  lucide.createIcons();
});
