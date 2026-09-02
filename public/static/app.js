const state = {
  car: null,
  track: null,
  style: "polyvalent",
  meta: null,
  last: null,
  garage: null,
  regionId: null,
  makerId: null,
};

const $ = (id) => document.getElementById(id);

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
  $("stats").innerHTML = `${meta.counts.cars} voitures · ${meta.counts.swaps || "—"} swaps · ${meta.counts.tracks} tracés`;
  if (meta.coverage) {
    $("footNote").innerHTML = `${meta.coverage.cars_note} ${meta.coverage.swaps_note} Miniatures : gtplus.app. Non affilié à PD / SIE.`;
  }
  fillSymptoms(meta.symptoms || []);
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

function bindCombo(input, list, kind) {
  const search = debounce(async () => {
    const q = input.value.trim();
    const url = kind === "car" ? `/api/cars?q=${encodeURIComponent(q)}&limit=40` : `/api/tracks?q=${encodeURIComponent(q)}&limit=40`;
    const rows = await (await fetch(url)).json();
    list.hidden = false;
    list.innerHTML = "";
    if (!rows.length) {
      list.innerHTML = `<button type="button" disabled>Aucun résultat</button>`;
      return;
    }
    rows.forEach((row, i) => {
      const b = document.createElement("button");
      b.type = "button";
      if (kind === "car") {
        b.innerHTML = `<strong>${row.full_name}</strong><small>${row.category} · ${row.drivetrain}${row.has_swap ? " · swap" : ""}</small>`;
      } else {
        const p = row.profile?.labels?.join(" · ") || row.category;
        b.innerHTML = `<strong>${row.name}</strong><small>${p}</small>`;
      }
      if (i === 0) b.classList.add("active");
      b.addEventListener("click", () => pick(kind, row));
      list.appendChild(b);
    });
  });
  input.addEventListener("input", search);
  input.addEventListener("focus", () => {
    if (input.value || !list.innerHTML) search();
    else list.hidden = false;
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      const first = list.querySelector("button:not([disabled])");
      if (first) first.click();
    }
    if (e.key === "Escape") list.hidden = true;
  });
  document.addEventListener("click", (ev) => {
    if (!ev.target.closest(".combo")) list.hidden = true;
  });
}

function pick(kind, row) {
  if (kind === "car") {
    state.car = row;
    $("carPicked").textContent = `${row.full_name}  ·  ${row.category}  ·  ${row.drivetrain}${row.has_swap ? "  ·  swap dispo" : ""}`;
    $("carQuery").value = row.full_name;
    $("carList").hidden = true;
  } else {
    state.track = row;
    $("trackPicked").textContent = `${row.name}  ·  ${(row.profile?.labels || []).join(" · ")}`;
    $("trackQuery").value = row.name;
    $("trackList").hidden = true;
  }
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
    allow_swap: $("allowSwap").checked,
    has_ultimate: $("ultimate").checked,
    drivetrain_override: $("dtOverride").value || null,
    symptoms: selectedChips($("symptomGroups")),
  };
}

function fillSymptoms(groups) {
  const root = $("symptomGroups");
  if (!root) return;
  root.innerHTML = groups.map((g) => `
    <div class="sym-group">
      <h4>${g.label}</h4>
      <div class="chips sym">${g.items.map((s) =>
        `<button type="button" data-id="${s.id}" title="${s.hint || ""}">${s.label}</button>`
      ).join("")}</div>
    </div>`).join("");
  root.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => b.classList.toggle("on")));
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
    render(data);
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
  body.prefer_swap = $("allowSwap").checked;
  const res = await fetch("/api/suggest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) return alert(data.error || "Erreur");
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
    b.addEventListener("click", () => {
      pick("car", c);
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
        <span class="meta">Budget pièces conseillées</span>
        <b>${money(d.cost_min)} – ${money(d.cost_max)}</b>
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
      <button class="on" data-tab="shop">Liste d'achats</button>
      <button data-tab="auto">GT Auto</button>
      <button data-tab="setup">Réglages</button>
      <button data-tab="plan">Plan de session</button>
      <button data-tab="cat">Catalogue atelier</button>
    </div>
    <div class="tabpane" id="tab-shop">
      ${shopGroups.map((g) => `<div class="group"><h3>${tierLabel(g.tier)}</h3>${partTable(g.items)}</div>`).join("") || "<p>Rien à acheter ? Étrange.</p>"}
    </div>
    <div class="tabpane" id="tab-auto" hidden>
      ${d.gt_auto.length ? autoGroups.map((g) => `<div class="group"><h3>GT Auto</h3>${partTable(g.items)}</div>`).join("") : "<p>GT Auto ignoré ou rien de pertinent.</p>"}
      ${renderSwaps(d)}
    </div>
    <div class="tabpane" id="tab-setup" hidden>
      <div class="setup-grid">
        ${card("Pneus", s.tires)}
        ${card("Aéro", `<p>Avant : ${s.aero.front}<br>Arrière : ${s.aero.rear}</p><p>${s.aero.note}</p>`)}
        ${card("Hauteur", `<p>AV ${s.ride.front}<br>AR ${s.ride.rear}</p><p>${s.ride.note}</p>`)}
        ${card("Ressorts", `<p>AV ${s.springs.front}<br>AR ${s.springs.rear}</p>`)}
        ${card("Fréquence naturelle", `<p>AV ${s.nfr.front}<br>AR ${s.nfr.rear}</p><p>${s.nfr.note}</p>`)}
        ${card("Barres anti-roulis", `<p>AV ${s.arbs.front}<br>AR ${s.arbs.rear}</p>`)}
        ${card("Amortisseurs", `<p>Comp. rapide ${s.dampers.comp_fast}<br>Comp. lente ${s.dampers.comp_slow}<br>Dét. rapide ${s.dampers.ext_fast}<br>Dét. lente ${s.dampers.ext_slow}</p>`)}
        ${card("Carrossage", `<p>AV ${s.camber.front}<br>AR ${s.camber.rear}</p><p>${s.camber.note}</p>`)}
        ${card("Pincement", `<p>AV ${s.toe.front}<br>AR ${s.toe.rear}</p>`)}
        ${card("LSD", `<p>Init ${s.lsd.initial}<br>Accel ${s.lsd.accel}<br>Décel ${s.lsd.decel}</p><p>${s.lsd.note}</p>`)}
        ${card("Freins", `<p>Force ${s.brakes_force}<br>Répartition ${s.brake_balance}<br>ABS ${s.abs}</p>`)}
        ${card("Aides", `<p>TCS ${s.tcs}<br>ASM ${s.asm}<br>Contre-braquage auto ${s.countersteer}</p>`)}
        ${card("Boîte / pont", `<p>${s.transmission}</p><p>${s.final_drive}</p>`, true)}
        ${gearingCard(s.gearing)}
        ${diagCard(s.diagnostics)}
        ${card("PP / ECU / lest", `<p>ECU : ${s.ecu}</p><p>Lest : ${s.ballast}</p><p>Position : ${s.ballast_pos}</p>`, true)}
        ${card("Pilotage", s.controller, true)}
      </div>
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
  const pick = (d.gt_auto || []).find((x) => x.swap_all);
  if (!pick) {
    if (d.car.has_swap) {
      return `<div class="group"><h3>Swaps connus</h3><ul>${d.car.swaps.map((s) => `<li><strong>${s.engine}</strong> — ${s.donor}</li>`).join("")}</ul></div>`;
    }
    return "";
  }
  return `<div class="group"><h3>Swaps disponibles (${pick.swap_all.length})</h3>
    <table><thead><tr><th>Moteur</th><th>Voiture donneuse</th></tr></thead>
    <tbody>${pick.swap_all.map((s, i) => `<tr><td>${i === 0 ? '<span class="badge power">conseillé</span>' : ""}${s.engine}</td><td>${s.donor}</td></tr>`).join("")}</tbody></table>
  </div>`;
}

function card(title, body, wide = false) {
  const inner = body.startsWith("<") ? body : `<p>${body}</p>`;
  return `<div class="card${wide ? " wide" : ""}"><h4>${title}</h4>${inner}</div>`;
}

function gearingCard(g) {
  if (!g) return "";
  const rows = (g.ratios || []).map((r) => `<tr><td>${r.gear}${r.gear === 1 ? "re" : "e"}</td><td>${Number(r.ratio).toFixed(3)}</td></tr>`).join("");
  return `<div class="card wide"><h4>Étalonnage de boîte</h4>
    <p>${g.note || ""}</p>
    <table class="gear-table">
      <tr><td>Vmax auto</td><td><strong>${g.max_speed} km/h</strong></td></tr>
      <tr><td>Rapports</td><td>${g.gears} · ${g.spread}</td></tr>
      <tr><td>Pont</td><td><strong>${Number(g.final_drive).toFixed(3)}</strong></td></tr>
      ${rows}
    </table>
    <ul>${(g.howto || []).map((h) => `<li>${h}</li>`).join("")}</ul>
  </div>`;
}

function diagCard(d) {
  if (!d || !(d.corrections || []).length) return "";
  return `<div class="card wide"><h4>Diagnostic — ${d.labels.join(" · ")}</h4>
    <div class="fix-list">${d.corrections.map((c) =>
      `<div class="fix-item"><b>${c.area}</b><p>${c.text}</p><p class="meta">${c.symptom}</p></div>`
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
  if (s.gearing) {
    lines.push("");
    lines.push("ETALONNAGE BOITE");
    lines.push(`Vmax auto ${s.gearing.max_speed} km/h · pont ${s.gearing.final_drive}`);
    (s.gearing.ratios || []).forEach((r) => lines.push(`  ${r.gear} : ${Number(r.ratio).toFixed(3)}`));
  }
  if (s.diagnostics?.corrections?.length) {
    lines.push("");
    lines.push("DIAGNOSTIC");
    s.diagnostics.corrections.forEach((c) => lines.push(`- ${c.area}: ${c.text}`));
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
  row.innerHTML = `<button type="button" data-id="" class="${state.regionId == null ? "on" : ""}">Toutes</button>` +
    g.regions.map((r) => `<button type="button" data-id="${r.id}" class="${state.regionId === r.id ? "on" : ""}">${r.name} (${r.count})</button>`).join("");
  row.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    state.regionId = b.dataset.id === "" ? null : Number(b.dataset.id);
    state.makerId = null;
    renderRegions(g); renderMakers(g); renderCarGrid(g);
  }));
}

function renderMakers(g) {
  const row = $("makerRow");
  const makers = g.makers.filter((m) => state.regionId == null || m.region_id === state.regionId);
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
  }).slice(0, 120);
  $("carGrid").innerHTML = cars.map((c) => `
    <button type="button" class="car-card" data-id="${c.id}">
      ${imgTag(c.thumb, c.maker, c.thumb_alt)}
      <div class="info">
        <strong>${c.name}</strong>
        <small>${c.maker} · ${c.drivetrain} · ${c.category}${c.has_swap ? " · swap" : ""}</small>
      </div>
    </button>`).join("") || `<p class="meta">Aucun modèle.</p>`;
  bindThumbs($("carGrid"));
  $("carGrid").querySelectorAll(".car-card").forEach((b) => b.addEventListener("click", () => {
    const car = g.cars.find((c) => c.id === Number(b.dataset.id));
    if (car) {
      pick("car", car);
      $("garageModal").hidden = true;
    }
  }));
}

$("collector").addEventListener("input", () => ($("clVal").textContent = $("collector").value));
document.querySelectorAll("#styleSeg button").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll("#styleSeg button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    state.style = b.dataset.v;
  });
});
$("go").addEventListener("click", generate);
$("suggest").addEventListener("click", suggest);
$("openGarage").addEventListener("click", openGarage);
$("closeGarage").addEventListener("click", () => ($("garageModal").hidden = true));
$("garageModal").addEventListener("click", (e) => {
  if (e.target.id === "garageModal") $("garageModal").hidden = true;
});
$("garageSearch").addEventListener("input", debounce(() => {
  if (state.garage) renderCarGrid(state.garage);
}, 120));
bindCombo($("carQuery"), $("carList"), "car");
bindCombo($("trackQuery"), $("trackList"), "track");
loadMeta();
