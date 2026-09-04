const state = {
  car: null,
  track: null,
  style: "polyvalent",
  meta: null,
  last: null,
  garage: null,
  circuits: null,
  regionId: null,
  makerId: null,
  trackRegionId: null,
  circuitId: null,
};

const $ = (id) => document.getElementById(id);
const STYLE_INFO = {
  stable: { title: "Course stable", hint: "Priorité à la prévisibilité et au grip." },
  polyvalent: { title: "Polyvalent", hint: "Équilibré sur l'ensemble du tour." },
  chrono: { title: "Qualifs / chrono", hint: "Agressif : appui et réponse pour le temps au tour." },
  drift: { title: "Drift", hint: "L'auto doit pivoter et rester jouable en glisse." },
};
const collator = new Intl.Collator("fr", { sensitivity: "base", numeric: true });

function byName(a, b, key = "name") {
  return collator.compare(a[key] || "", b[key] || "");
}

function debounce(fn, ms = 180) {
  let t;
  return (...a) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...a), ms);
  };
}

function money(n) {
  if (!n) return "—";
  return new Intl.NumberFormat("fr-FR").format(n) + " Cr.";
}

function rangePrice(a, b) {
  if (!a && !b) return "Roulette / variable";
  if (a === b) return money(a);
  return `${money(a)} – ${money(b)}`;
}

async function loadMeta() {
  const meta = await (await fetch("/api/meta")).json();
  state.meta = meta;
  fillSymptoms(meta.symptoms || []);
  fillPiloting(meta.piloting || []);
  if (window.matchMedia("(max-width: 760px)").matches) {
    document.querySelectorAll(".form-panel details.regs").forEach((d) => {
      const t = (d.querySelector("summary")?.textContent || "");
      d.open = t.includes("Style de pilotage");
    });
  }
  fillSelect($("weather"), meta.weather, "id", "label", "dry");
  const tires = $("tires");
  meta.tires.forEach((t) => {
    const o = document.createElement("option");
    o.value = t.id;
    o.textContent = `${t.id} — ${t.name_fr}`;
    tires.appendChild(o);
  });
  fillChips($("catChips"), meta.categories);
  fillChips($("typeChips"), meta.car_types);
  fillChips($("dtChips"), meta.drivetrains);
  const dt = $("dtOverride");
  meta.drivetrains.forEach((d) => {
    const o = document.createElement("option");
    o.value = d.id;
    o.textContent = d.label;
    dt.appendChild(o);
  });
}

function fillSelect(el, items, id, label, selected) {
  el.innerHTML = "";
  items.forEach((it) => {
    const o = document.createElement("option");
    o.value = it[id];
    o.textContent = it[label];
    if (it[id] === selected) o.selected = true;
    el.appendChild(o);
  });
}

function fillChips(el, items) {
  el.innerHTML = "";
  items.forEach((it) => {
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.id = it.id;
    b.textContent = it.id;
    b.title = it.label;
    b.addEventListener("click", () => b.classList.toggle("on"));
    el.appendChild(b);
  });
}

function selectedChips(el) {
  return [...el.querySelectorAll("button.on")].map((b) => b.dataset.id);
}

function setSlotMedia(id, src, alt) {
  const el = $(id);
  if (!el) return;
  const ph = (alt || "GT").replace(/[^A-Za-z0-9]/g, "").slice(0, 2).toUpperCase() || "GT";
  if (src) {
    el.innerHTML = `<img src="${src}" alt="" loading="lazy">`;
    el.querySelector("img").addEventListener("error", () => {
      el.innerHTML = `<span class="slot-ph">${ph}</span>`;
    }, { once: true });
  } else {
    el.innerHTML = `<span class="slot-ph">${ph}</span>`;
  }
}

async function pick(kind, row) {
  if (kind === "car") {
    if (row.has_swap && !(row.swaps && row.swaps.length)) {
      try {
        row = await (await fetch(`/api/cars/${row.id}`)).json();
      } catch (_) { /* keep the thin row */ }
    }
    state.car = row;
    $("carPicked").textContent = row.full_name;
    if ($("carMeta")) {
      $("carMeta").textContent = `${row.category} · ${row.drivetrain}${row.has_swap ? " · swap" : ""}`;
    }
    setSlotMedia("carMedia", row.thumb || row.image, row.maker || row.name);
    $("openGarage")?.classList.add("filled");
    fillSwapSelect(row);
  } else {
    state.track = row;
    $("trackPicked").textContent = row.name;
    if ($("trackMeta")) {
      $("trackMeta").textContent = (row.profile?.labels || []).join(" · ") || "Circuit";
    }
    setSlotMedia("trackMedia", row.thumb, row.name);
    $("openTracks")?.classList.add("filled");
  }
}

function fillSwapSelect(car) {
  const box = $("swapBox");
  const sel = $("swapSelect");
  if (!box || !sel) return;
  const prev = sel.value;
  sel.innerHTML = "";
  const none = document.createElement("option");
  none.value = "";
  none.textContent = "Moteur d'origine (pas de swap)";
  sel.appendChild(none);
  const swaps = car?.swaps || [];
  if (!swaps.length) {
    box.hidden = true;
    return;
  }
  box.hidden = false;
  swaps.forEach((s) => {
    const o = document.createElement("option");
    o.value = s.engine;
    const cr = s.price ? money(s.price) : "prix variable";
    o.textContent = `${s.engine} — ${s.donor} · ${cr}`;
    sel.appendChild(o);
  });
  if (prev && [...sel.options].some((o) => o.value === prev)) sel.value = prev;
}

function payload() {
  return {
    car_id: state.car?.id,
    track_id: state.track?.id,
    collector_level: Number($("collector").value),
    style: state.style,
    weather: $("weather").value,
    tires: $("tires").value || null,
    pp_limit: $("pp").value ? Number($("pp").value) : null,
    categories: selectedChips($("catChips")),
    car_types: selectedChips($("typeChips")),
    drivetrains: selectedChips($("dtChips")),
    has_gt_auto: $("gtAuto").checked,
    allow_wide: $("allowWide").checked,
    allow_swap: Boolean($("swapSelect") && $("swapSelect").value),
    swap_engine: ($("swapSelect") && $("swapSelect").value) || "",
    has_ultimate: $("ultimate").checked,
    drivetrain_override: $("dtOverride").value || null,
    symptoms: selectedChips($("symptomGroups")),
    pilot: readPilot(),
  };
}

function fillPiloting(groups) {
  const root = $("pilotFields");
  if (!root) return;
  root.className = "pilot-grid";
  root.innerHTML = groups.map((g) => `
    <label>${g.label}
      <select data-pilot="${g.id}">
        ${g.options.map((o) => `<option value="${o.id}" ${o.id === g.default ? "selected" : ""}>${o.label}</option>`).join("")}
      </select>
    </label>`).join("");
}

function readPilot() {
  const out = {};
  document.querySelectorAll("[data-pilot]").forEach((el) => {
    out[el.dataset.pilot] = el.value;
  });
  return out;
}

function fillSymptoms(groups) {
  const root = $("symptomGroups");
  const pop = $("symPop");
  if (!root) return;
  const touch = window.matchMedia("(hover: none)").matches;
  root.innerHTML = groups.map((g) => `
    <div class="sym-group">
      <h4>${g.label}</h4>
      <div class="chips sym">${g.items.map((s) =>
        `<button type="button" data-id="${s.id}" data-detail="${(s.detail || s.hint || "").replace(/"/g, "&quot;")}">${s.label}</button>`
      ).join("")}</div>
    </div>`).join("");
  const show = (btn) => {
    pop.hidden = false;
    pop.innerHTML = `<b>${btn.textContent}</b><p>${btn.dataset.detail || ""}</p>`;
    const r = btn.getBoundingClientRect();
    const left = Math.min(Math.max(8, r.left), window.innerWidth - 28);
    pop.style.left = left + "px";
    pop.style.top = Math.min(r.bottom + 8, window.innerHeight - 120) + "px";
  };
  const hide = () => { pop.hidden = true; };
  root.querySelectorAll("button").forEach((b) => {
    b.addEventListener("click", (e) => {
      b.classList.toggle("on");
      if (touch) {
        e.stopPropagation();
        show(b);
      }
    });
    if (!touch) {
      b.addEventListener("mouseenter", () => show(b));
      b.addEventListener("mouseleave", hide);
      b.addEventListener("focus", () => show(b));
      b.addEventListener("blur", hide);
    }
  });
  if (touch) {
    document.addEventListener("click", (e) => {
      if (!e.target.closest("#symptomGroups") && !e.target.closest("#symPop")) hide();
    });
  }
}

async function generate() {
  if (!state.car || !state.track) {
    alert("Choisis une voiture et un circuit.");
    return;
  }
  $("go").disabled = true;
  try {
    const res = await fetch("/api/tune", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload()),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Erreur");
    state.last = data;
    document.body.classList.add("has-plan");
    render(data);
    if (window.matchMedia("(max-width: 980px)").matches) {
      $("results").scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (err) {
    alert(err.message);
  } finally {
    $("go").disabled = false;
  }
}

async function suggest() {
  if (!state.track) {
    alert("Choisis d'abord un circuit (les restrictions filtrent ensuite).");
    return;
  }
  const body = payload();
  body.prefer_swap = Boolean($("swapSelect") && $("swapSelect").options.length > 1);
  const res = await fetch("/api/suggest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) return alert(data.error || "Erreur");
  document.body.classList.add("has-plan");
  const box = $("results");
  box.innerHTML = `
    <div class="hero"><div>
      <p class="eyebrow">Suggestions</p>
      <h2>Voitures pour ${data.track.name}</h2>
      <p class="meta">Filtrées selon tes catégories / tractions. Clique pour la charger, puis génère le plan.</p>
    </div></div>
    <div class="suggest-list" id="sug"></div>`;
  const root = $("sug");
  data.cars.forEach((c) => {
    const b = document.createElement("button");
    b.innerHTML = `<strong>${c.full_name}</strong><div class="meta">${c.category} · ${c.drivetrain} · ${c.car_type}${c.has_swap ? " · swap" : ""}</div>`;
    b.addEventListener("click", async () => {
      await pick("car", c);
      generate();
    });
    root.appendChild(b);
  });
}

function badge(p) {
  const k = p.optional ? "optional" : p.priority;
  const label = { must: "obligatoire", core: "chassis", power: "moteur", pp: "PP", optional: "optionnel" }[k] || k;
  return `<span class="badge ${k}">${label}</span>`;
}

function groupParts(list) {
  const order = ["sports", "club", "semi", "racing", "extreme", "ultimate", "gtauto"];
  const map = {};
  list.forEach((p) => {
    const t = p.tier || "sports";
    (map[t] ||= []).push(p);
  });
  return order.filter((k) => map[k]).map((k) => ({ tier: k, items: map[k] }));
}

function partTable(items) {
  return `<table>
    <thead><tr><th>Pièce</th><th>Prix</th><th>Pourquoi</th></tr></thead>
    <tbody>
      ${items.map((p) => `<tr>
        <td>${badge(p)}${p.name_fr}${p.permanent ? " <small>· permanent</small>" : ""}${p.rev ? ` <small>· ${p.rev}</small>` : ""}</td>
        <td class="price">${rangePrice(p.price_min, p.price_max)}</td>
        <td class="why">${p.why || p.note || ""}</td>
      </tr>`).join("")}
    </tbody>
  </table>`;
}

function render(d) {
  const shopGroups = groupParts(d.shopping);
  const autoGroups = groupParts(d.gt_auto);
  const s = d.setup;
  $("results").innerHTML = `
    <div class="hero">
      <div>
        <p class="eyebrow">${d.car.maker} · ${d.drivetrain} · rang ${d.collector_level}</p>
        <h2>${d.car.name}</h2>
        <p class="meta">${d.strategy}</p>
        <div class="pills">${(d.profile.labels || []).map((x) => `<span class="pill">${x}</span>`).join("")}
          <span class="pill">${d.tire.name_fr}</span>
          ${d.pp_limit ? `<span class="pill">${d.pp_limit} PP</span>` : `<span class="pill">PP libre</span>`}
        </div>
      </div>
      <div class="cost">
        <span class="meta">${d.price_note || "Budget pièces conseillées"}</span>
        <b>${d.cost_typical ? money(d.cost_typical) : `${money(d.cost_min)} – ${money(d.cost_max)}`}</b>
        <div class="toolbar" style="margin-top:8px">
          <button class="btn ghost" id="copyBtn">Copier</button>
          <button class="btn ghost" id="printBtn">Imprimer</button>
        </div>
      </div>
    </div>
    <div class="warns">
      ${(d.warnings || []).map((w) => `<div class="warn">${w}</div>`).join("")}
      ${(d.notes || []).slice(0, 4).map((n) => `<div class="note">${n}</div>`).join("")}
    </div>
    <div class="tabs">
      <button class="on" data-tab="setup">Réglages</button>
      <button data-tab="shop">Liste d'achats</button>
      <button data-tab="auto">GT Auto</button>
      <button data-tab="plan">Plan de session</button>
      <button data-tab="cat">Catalogue atelier</button>
    </div>
    <div class="tabpane" id="tab-shop" hidden>
      ${shopGroups.map((g) => `<div class="group"><h3>${tierLabel(g.tier)}</h3>${partTable(g.items)}</div>`).join("") || "<p>Rien à acheter ? Étrange.</p>"}
    </div>
    <div class="tabpane" id="tab-auto" hidden>
      ${d.gt_auto.length ? autoGroups.map((g) => `<div class="group"><h3>GT Auto</h3>${partTable(g.items)}</div>`).join("") : "<p>GT Auto ignoré ou rien de pertinent.</p>"}
      ${renderSwaps(d)}
    </div>
    <div class="tabpane" id="tab-setup">
      ${renderSheet(s)}
      ${diagCard(s.diagnostics)}
      ${card("Pilotage", s.controller, true)}
    </div>
    <div class="tabpane" id="tab-plan" hidden>
      <div class="card wide"><ol>${s.session_plan.map((x) => `<li>${x.replace(/^\d+\.\s*/, "")}</li>`).join("")}</ol></div>
      ${(d.skipped || []).length ? `<div class="group"><h3>Volontairement écarté</h3><ul>${d.skipped.map((x) => `<li>${x}</li>`).join("")}</ul></div>` : ""}
      ${(d.notes || []).slice(4).map((n) => `<div class="note">${n}</div>`).join("")}
    </div>
    <div class="tabpane" id="tab-cat" hidden>
      <p class="meta">Catalogue de référence (tous étages). Les pièces verrouillées par ton rang n'apparaissent pas dans la liste d'achats.</p>
      <div id="fullCat"></div>
    </div>
  `;
  document.querySelectorAll(".tabs button").forEach((b) => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".tabs button").forEach((x) => x.classList.remove("on"));
      b.classList.add("on");
      document.querySelectorAll(".tabpane").forEach((p) => (p.hidden = true));
      $(`tab-${b.dataset.tab}`).hidden = false;
      if (b.dataset.tab === "cat") renderCatalog();
    });
  });
  $("copyBtn").addEventListener("click", () => copyPlan(d));
  $("printBtn").addEventListener("click", () => window.print());
}

function renderSwaps(d) {
  const item = (d.gt_auto || []).find((x) => x.swap_all);
  const chosen = item?.swap_pick?.engine;
  const list = item?.swap_all || d.car.swaps || [];
  if (!list.length) return "";
  return `<div class="group"><h3>Swaps disponibles (${list.length})</h3>
    <table><thead><tr><th>Moteur</th><th>Donneuse</th><th>Prix GT Auto</th></tr></thead>
    <tbody>${list.map((s) => `<tr>
      <td>${s.engine === chosen ? '<span class="badge power">choisi</span>' : ""}${s.engine}</td>
      <td>${s.donor}</td>
      <td class="price">${s.price ? money(s.price) : "variable"}</td>
    </tr>`).join("")}</tbody></table>
    ${chosen ? "" : `<p class="meta">Choisis un moteur dans Options atelier pour l'ajouter au plan et au budget.</p>`}
  </div>`;
}

function card(title, body, wide = false) {
  const inner = body.startsWith("<") ? body : `<p>${body}</p>`;
  return `<div class="card${wide ? " wide" : ""}"><h4>${title}</h4>${inner}</div>`;
}

function renderSheet(s) {
  const sheet = s.sheet;
  if (!sheet || !sheet.blocks) return `<p>Feuille indisponible.</p>`;
  const blocks = sheet.blocks.map((b) => {
    if (b.kind === "fr") {
      const rows = b.rows.map((r) =>
        `<div class="gt7-row"><span class="lab">${r.label}</span><span class="val">${r.front}</span><span class="val">${r.rear}</span></div>`
      ).join("");
      return `<div class="gt7-block"><h4>${b.title}</h4>
        <div class="gt7-cols"><span></span><span>Avant</span><span>Arrière</span></div>${rows}</div>`;
    }
    const rows = b.rows.map((r) =>
      `<div class="gt7-row single"><span class="lab">${r.label}</span><span class="val">${r.value}</span></div>`
    ).join("");
    return `<div class="gt7-block"><h4>${b.title}</h4>${rows}</div>`;
  }).join("");
  const howto = (sheet.gearing?.howto || []).map((h) => `<li>${h}</li>`).join("");
  return `<div class="gt7-sheet">
    <div class="sheet-head"><h3>Réglages</h3><span class="meta">${s.tires}</span></div>
    ${blocks}
    <div class="sheet-note">${sheet.disclaimer || ""}</div>
    ${howto ? `<div class="sheet-note"><ol>${howto}</ol></div>` : ""}
  </div>`;
}

function diagCard(d) {
  const items = d?.items || d?.corrections || [];
  if (!d || !items.length) return "";
  const labels = (d.labels || []).join(" · ");
  return `<div class="card wide" style="margin-top:12px"><h4>Diagnostic — ${labels}</h4>
    <div class="fix-list">${items.map((c) =>
      `<div class="fix-item"><b>${c.symptom || c.area}</b><p>${c.detail || c.text || ""}</p></div>`
    ).join("")}</div>
  </div>`;
}

function tierLabel(t) {
  return {
    sports: "Sports — atelier de base",
    club: "Club Sports — rang 4",
    semi: "Semi-Racing — rang 5",
    racing: "Racing — rang 6",
    extreme: "Extreme — rang 50",
    ultimate: "Ultimate — tickets roulette",
    gtauto: "GT Auto",
  }[t] || t;
}

async function renderCatalog() {
  const box = $("fullCat");
  if (box.dataset.done) return;
  const data = await (await fetch("/api/catalog")).json();
  const by = {};
  data.parts.forEach((p) => (by[p.tier] ||= []).push(p));
  box.innerHTML = Object.keys(data.tiers)
    .map((t) => {
      const items = by[t] || [];
      if (!items.length) return "";
      const info = data.tiers[t];
      return `<div class="group"><h3>${info.label_fr} ${info.level ? `(rang ${info.level}+)` : ""}</h3>
        <table><thead><tr><th>Pièce</th><th>Groupe</th><th>Prix</th><th>Note</th></tr></thead>
        <tbody>${items.map((p) => `<tr>
          <td>${p.name_fr}${p.permanent ? " · perm." : ""}</td>
          <td>${p.group}</td>
          <td class="price">${rangePrice(p.price_min, p.price_max)}</td>
          <td class="why">${p.note || ""}</td>
        </tr>`).join("")}</tbody></table></div>`;
    })
    .join("");
  box.dataset.done = "1";
}

function copyPlan(d) {
  const lines = [];
  lines.push(`GT7 TuneLab — ${d.car.full_name} @ ${d.track.name}`);
  lines.push(d.strategy);
  lines.push("");
  lines.push("ACHATS ATELIER");
  d.shopping.forEach((p) => lines.push(`- [${p.optional ? "opt" : p.priority}] ${p.name_fr} (${rangePrice(p.price_min, p.price_max)}) — ${p.why}`));
  lines.push("");
  lines.push("GT AUTO");
  d.gt_auto.forEach((p) => lines.push(`- ${p.name_fr} — ${p.why}`));
  lines.push("");
  lines.push("REGLAGES");
  const s = d.setup;
  lines.push(`Pneus: ${s.tires}`);
  lines.push(`Aéro AV ${s.aero.front} / AR ${s.aero.rear}`);
  lines.push(`LSD init ${s.lsd.initial} / accel ${s.lsd.accel} / decel ${s.lsd.decel}`);
  lines.push(`TCS ${s.tcs} · ABS ${s.abs}`);
  if (s.sheet?.blocks) {
    lines.push("");
    lines.push("FEUILLE GT7");
    s.sheet.blocks.forEach((b) => {
      lines.push(`[${b.title}]`);
      b.rows.forEach((r) => {
        if (r.value != null) lines.push(`  ${r.label}: ${r.value}`);
        else lines.push(`  ${r.label}: AV ${r.front} / AR ${r.rear}`);
      });
    });
  }
  navigator.clipboard.writeText(lines.join("\n")).then(() => alert("Plan copié dans le presse-papiers."));
}

function imgTag(src, alt, fallback) {
  const initials = (alt || "?").slice(0, 2).toUpperCase();
  return `<img src="${src || ""}" alt="" loading="lazy" data-fb="${fallback || ""}" data-ph="${initials}">`;
}
function bindThumbs(root) {
  root.querySelectorAll("img").forEach((img) => {
    img.addEventListener("error", function fail() {
      if (img.dataset.fb) {
        const next = img.dataset.fb;
        img.dataset.fb = "";
        img.src = next;
        return;
      }
      const d = document.createElement("div");
      d.className = "ph";
      d.textContent = img.dataset.ph || "?";
      img.replaceWith(d);
    }, { once: false });
  });
}

async function ensureGarage() {
  if (state.garage) return state.garage;
  state.garage = await (await fetch("/api/garage")).json();
  return state.garage;
}

async function openGarage() {
  const g = await ensureGarage();
  $("garageModal").hidden = false;
  renderRegions(g);
  renderMakers(g);
  renderCarGrid(g);
}

function renderRegions(g) {
  const row = $("regionRow");
  const regions = [...g.regions].sort((a, b) => byName(a, b));
  row.innerHTML = `<button type="button" data-id="" class="${state.regionId == null ? "on" : ""}">Toutes</button>` +
    regions.map((r) => `<button type="button" data-id="${r.id}" class="${state.regionId === r.id ? "on" : ""}">${r.name} (${r.count})</button>`).join("");
  row.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    state.regionId = b.dataset.id === "" ? null : Number(b.dataset.id);
    state.makerId = null;
    renderRegions(g); renderMakers(g); renderCarGrid(g);
  }));
}

function renderMakers(g) {
  const row = $("makerRow");
  const makers = g.makers
    .filter((m) => state.regionId == null || m.region_id === state.regionId)
    .sort((a, b) => byName(a, b));
  row.innerHTML = `<button type="button" data-id="" class="${state.makerId == null ? "on" : ""}">Tous</button>` +
    makers.map((m) => `<button type="button" data-id="${m.id}" class="${state.makerId === m.id ? "on" : ""}">${m.name} (${m.count})</button>`).join("");
  row.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    state.makerId = b.dataset.id === "" ? null : Number(b.dataset.id);
    renderMakers(g); renderCarGrid(g);
  }));
}

function renderCarGrid(g) {
  const q = ($("garageSearch").value || "").trim().toLowerCase();
  const cars = g.cars.filter((c) => {
    if (state.regionId != null && c.region_id !== state.regionId) return false;
    if (state.makerId != null && c.maker_id !== state.makerId) return false;
    if (q && !`${c.full_name} ${c.category} ${c.drivetrain}`.toLowerCase().includes(q)) return false;
    return true;
  }).sort((a, b) => collator.compare(a.full_name, b.full_name)).slice(0, 120);
  $("carGrid").innerHTML = cars.map((c) => `
    <button type="button" class="car-card" data-id="${c.id}">
      ${imgTag(c.thumb, c.maker, c.thumb_alt)}
      <div class="info">
        <strong>${c.name}</strong>
        <small>${c.maker} · ${c.drivetrain} · ${c.category}${c.has_swap ? " · swap" : ""}</small>
      </div>
    </button>`).join("") || `<p class="meta">Aucun modèle.</p>`;
  bindThumbs($("carGrid"));
  $("carGrid").querySelectorAll(".car-card").forEach((b) => b.addEventListener("click", async () => {
    const car = g.cars.find((c) => c.id === Number(b.dataset.id));
    if (car) {
      await pick("car", car);
      $("garageModal").hidden = true;
    }
  }));
}

function setStyleCard(id) {
  const info = STYLE_INFO[id] || STYLE_INFO.polyvalent;
  if ($("styleTitle")) $("styleTitle").textContent = info.title;
  if ($("styleHint")) $("styleHint").textContent = info.hint;
}
$("collector").addEventListener("input", () => ($("clVal").textContent = $("collector").value));
document.querySelectorAll("#styleSeg button").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll("#styleSeg button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    state.style = b.dataset.v;
    setStyleCard(state.style);
  });
});

$("go").addEventListener("click", generate);
$("suggest").addEventListener("click", suggest);
async function ensureCircuits() {
  if (state.circuits) return state.circuits;
  state.circuits = await (await fetch("/api/circuits")).json();
  return state.circuits;
}

async function openTracks() {
  const g = await ensureCircuits();
  $("trackModal").hidden = false;
  renderTrackRegions(g);
  renderCircuitRow(g);
  renderVariants(g);
}

function renderTrackRegions(g) {
  const row = $("trackRegionRow");
  const regions = [...g.regions].sort((a, b) => byName(a, b));
  row.innerHTML = `<button type="button" data-id="" class="${state.trackRegionId == null ? "on" : ""}">Toutes</button>` +
    regions.map((r) => `<button type="button" data-id="${r.id}" class="${state.trackRegionId === r.id ? "on" : ""}">${r.name} (${r.count})</button>`).join("");
  row.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    state.trackRegionId = b.dataset.id === "" ? null : Number(b.dataset.id);
    state.circuitId = null;
    renderTrackRegions(g); renderCircuitRow(g); renderVariants(g);
  }));
}

function renderCircuitRow(g) {
  const row = $("circuitRow");
  const list = g.circuits
    .filter((c) => state.trackRegionId == null || c.region_id === state.trackRegionId)
    .sort((a, b) => byName(a, b));
  row.innerHTML = list.map((c) =>
    `<button type="button" data-id="${c.id}" class="${state.circuitId === c.id ? "on" : ""}">${c.name}</button>`
  ).join("");
  row.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    state.circuitId = Number(b.dataset.id);
    renderCircuitRow(g); renderVariants(g);
  }));
}

function renderVariants(g) {
  const q = ($("trackSearch").value || "").trim().toLowerCase();
  let circuits = g.circuits.filter((c) => state.trackRegionId == null || c.region_id === state.trackRegionId);
  if (state.circuitId != null) circuits = circuits.filter((c) => c.id === state.circuitId);
  const cards = [];
  circuits.forEach((c) => {
    c.variants.forEach((v) => {
      if (q && !`${c.name} ${v.name}`.toLowerCase().includes(q)) return;
      cards.push({ c, v });
    });
  });
  cards.sort((a, b) => collator.compare(a.v.name, b.v.name) || collator.compare(a.c.name, b.c.name));
  $("variantGrid").innerHTML = cards.slice(0, 80).map(({ c, v }) => `
    <button type="button" class="car-card" data-id="${v.id}">
      ${imgTag(v.thumb || c.thumb, c.name, c.thumb)}
      <div class="info">
        <strong>${v.name.replace(c.name, "").replace(/^[\s\-:]+/, "") || v.name}</strong>
        <small>${c.name} · ${Math.round(v.length)} m · ${v.corners} virages${v.reverse ? " · inv." : ""}</small>
      </div>
    </button>`).join("") || `<p class="meta">Aucune variante.</p>`;
  bindThumbs($("variantGrid"));
  $("variantGrid").querySelectorAll(".car-card").forEach((b) => b.addEventListener("click", () => {
    const id = Number(b.dataset.id);
    let found = null;
    g.circuits.forEach((c) => c.variants.forEach((v) => { if (v.id === id) found = { ...v, family: c.name, thumb: v.thumb || c.thumb }; }));
    if (found) {
      pick("track", { id: found.id, name: found.name, profile: { labels: found.labels || [] }, thumb: found.thumb });
      $("trackModal").hidden = true;
    }
  }));
}

$("openGarage").addEventListener("click", openGarage);
$("closeGarage").addEventListener("click", () => ($("garageModal").hidden = true));
$("openTracks").addEventListener("click", openTracks);
$("closeTracks").addEventListener("click", () => ($("trackModal").hidden = true));
$("trackModal").addEventListener("click", (e) => {
  if (e.target.id === "trackModal") $("trackModal").hidden = true;
});
$("trackSearch").addEventListener("input", debounce(() => {
  if (state.circuits) renderVariants(state.circuits);
}, 120));
$("garageModal").addEventListener("click", (e) => {
  if (e.target.id === "garageModal") $("garageModal").hidden = true;
});
$("garageSearch").addEventListener("input", debounce(() => {
  if (state.garage) renderCarGrid(state.garage);
}, 120));
function startHeroFx() {
  const c = $("heroFx");
  if (!c || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const ctx = c.getContext("2d");
  const drops = [];
  const fit = () => {
    const r = c.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    c.width = Math.max(1, Math.floor(r.width * dpr));
    c.height = Math.max(1, Math.floor(r.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const w = r.width;
    const h = r.height;
    const n = Math.max(50, Math.min(180, Math.floor((w * h) / 5000)));
    drops.length = 0;
    for (let i = 0; i < n; i++) {
      drops.push({
        x: Math.random() * w,
        y: Math.random() * h,
        len: 14 + Math.random() * 22,
        spd: 14 + Math.random() * 18,
      });
    }
  };
  const tick = () => {
    const w = c.clientWidth;
    const h = c.clientHeight;
    ctx.clearRect(0, 0, w, h);
    ctx.lineCap = "round";
    for (const d of drops) {
      ctx.strokeStyle = "rgba(235,245,255,0.72)";
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(d.x, d.y);
      ctx.lineTo(d.x + 4, d.y + d.len);
      ctx.stroke();
      d.y += d.spd;
      d.x += 1.6;
      if (d.y > h + 20) {
        d.y = -d.len;
        d.x = Math.random() * w;
      }
    }
    requestAnimationFrame(tick);
  };
  fit();
  window.addEventListener("resize", fit);
  tick();
}

loadMeta();
startHeroFx();
