const COLORS = {Entity:"#2f7f86", Claim:"#e3a73a", Evidence:"#8fb996",
                U1:"#2f8f5b", U2:"#d98e1f", U3:"#c4452f"};
const EDGE_COLORS = {Supports:"#2f8f5b", Challenges:"#c4452f", Refines:"#6a5acd", Inconclusive:"#d98e1f"};
let network, nodesDS, edgesDS, current;

const $ = s => document.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

fetch("/api/keywords").then(r => r.json()).then(groups => {
  $("#chips").innerHTML = Object.entries(groups).map(([cat, kws]) =>
    `<div class="chip-group"><b>${esc(cat)}</b>${kws.map(k =>
      `<button type="button" class="chip" data-k="${esc(k)}">${esc(k)}</button>`).join("")}</div>`).join("");
  $("#chips").addEventListener("click", e => {
    const k = e.target.dataset.k; if (k) { $("#q").value = k; run(k); }
  });
});
$("#searchForm").addEventListener("submit", e => { e.preventDefault(); run($("#q").value); });
$("#legend").innerHTML = [["Entity",COLORS.Entity],["Claim",COLORS.Claim],["Evidence",COLORS.Evidence],
  ["U1 low",COLORS.U1],["U2 moderate",COLORS.U2],["U3 high",COLORS.U3]]
  .map(([l,c]) => `<li><i style="background:${c}"></i>${l}</li>`).join("");

async function run(q) {
  q = q.trim(); if (!q) return;
  $("#summary").textContent = "Building graph...";
  const res = await fetch("/api/search?q=" + encodeURIComponent(q));
  const g = await res.json();
  if (!res.ok) { $("#summary").textContent = g.error; return; }
  current = g; render(g);
}

function nodeStyle(n) {
  const base = {id:n.id, label:n.label, title:n.type, _n:n, font:{face:"IBM Plex Sans", size:13}};
  if (n.type === "Entity") return {...base, shape:"ellipse", color:{background:COLORS.Entity, border:"#1d5a60"},
      font:{color:"#fff", size:n.data.is_query ? 18 : 14, face:"IBM Plex Sans"}, borderWidth:n.data.is_query ? 4 : 1};
  if (n.type === "Claim") return {...base, shape:"box", color:{background:COLORS.Claim, border:"#a87a1c"},
      widthConstraint:{maximum:230}, font:{color:"#1a1a1a", size:12, face:"IBM Plex Sans"}, margin:8};
  if (n.type === "Evidence") return {...base, shape:"box", shapeProperties:{borderDashes:[4,3]},
      color:{background:COLORS.Evidence, border:"#5d8d66"}, widthConstraint:{maximum:200},
      font:{color:"#10261a", size:11, face:"IBM Plex Sans"}};
  return {...base, shape:"diamond", size:16, color:{background:COLORS[n.data.level], border:"#00000055"},
      font:{color:"#888", size:12, face:"IBM Plex Sans"}};
}

function render(g) {
  const s = g.stats;
  $("#summary").innerHTML = `<b>${esc(g.keyword)}</b>: ${s.claims} claims from ${s.abstracts} abstracts, ` +
    `${s.entities} entities. Uncertainty U1 ${s.uncertainty.U1} / U2 ${s.uncertainty.U2} / U3 ${s.uncertainty.U3}.`;
  if (!s.claims) { $("#summary").innerHTML += " No matching claims found."; }
  $("#filters").hidden = false;
  nodesDS = new vis.DataSet(g.nodes.map(nodeStyle));
  edgesDS = new vis.DataSet(g.edges.map((e,i) => ({id:i, from:e.from, to:e.to, label:e.label, _e:e,
    arrows:"to", font:{size:10, align:"middle", strokeWidth:3, strokeColor:getComputedStyle(document.body).backgroundColor},
    color:{color:EDGE_COLORS[e.label] || "#7a9296"}, width:EDGE_COLORS[e.label] ? 3 : 1,
    dashes: e.label === "From Finding"})));
  network = new vis.Network($("#graph"), {nodes:nodesDS, edges:edgesDS}, {
    physics:{solver:"forceAtlas2Based", forceAtlas2Based:{gravitationalConstant:-70, springLength:130}, stabilization:{iterations:200}},
    interaction:{hover:true}});
  network.on("click", p => {
    if (p.nodes.length) showNode(nodesDS.get(p.nodes[0])._n);
    else if (p.edges.length) showEdgeTriple(edgesDS.get(p.edges[0])._e);
  });
  applyFilters();
}

function describeNode(n) {
  if (!n) return "Unknown node";
  const d = n.data || {};
  if (n.type === "Entity") return "Entity (" + d.entity_type + "): " + n.label;
  if (n.type === "Claim") return "Claim [" + d.abstract_id + "]: " + d.full_text;
  if (n.type === "Evidence") return "Evidence [" + d.abstract_id + "]: " + d.passage;
  if (n.type === "Uncertainty") return "Uncertainty: " + d.level;
  return n.type + ": " + n.label;
}

function renderTriples(g, hidden = new Set()) {
  const byId = new Map(g.nodes.map(n => [n.id, n]));
  const visible = g.edges.filter(e => !hidden.has(e.from) && !hidden.has(e.to));
  $("#tripleCount").textContent = visible.length + " triples";
  $("#triples tbody").innerHTML = visible.length
    ? visible.map(e => "<tr><td>" + esc(describeNode(byId.get(e.from))) +
        "</td><td class=\"triple-relation\">" + esc(e.label) +
        "</td><td>" + esc(describeNode(byId.get(e.to))) + "</td></tr>").join("")
    : "<tr><td colspan=\"3\" class=\"muted\">No triples match the current filters.</td></tr>";
}

function showEdgeTriple(e) {
  const byId = new Map(current.nodes.map(n => [n.id, n]));
  $("#detail").innerHTML = "<h2>Graph triple</h2><dl class=\"triple-detail\">" +
    "<dt>Head</dt><dd>" + esc(describeNode(byId.get(e.from))) + "</dd>" +
    "<dt>Relation</dt><dd><b>" + esc(e.label) + "</b></dd>" +
    "<dt>Tail</dt><dd>" + esc(describeNode(byId.get(e.to))) + "</dd></dl>";
}

function applyFilters() {
  if (!current) return;
  const on = new Set([...document.querySelectorAll("[data-u]")].filter(c => c.checked).map(c => c.dataset.u));
  const ev = $("#showEv").checked, hide = new Set();
  current.nodes.forEach(n => {
    if (n.type === "Uncertainty" && !on.has(n.data.level)) { hide.add(n.id); hide.add(n.id.replace("U_","")); hide.add(n.id.replace("U_","EV_")); }
    if (n.type === "Evidence" && !ev) hide.add(n.id);
  });
  // a claim is hidden only if its own uncertainty level is filtered out
  const claimHidden = id => hide.has(id) && current.nodes.find(n => n.id === "U_" + id && !on.has(n.data.level));
  nodesDS.update(current.nodes.map(n => ({id:n.id,
    hidden: n.type === "Claim" ? !!claimHidden(n.id)
          : n.type === "Evidence" ? (!ev || !!claimHidden(n.id.replace("EV_","")))
          : n.type === "Uncertainty" ? !on.has(n.data.level) : false})));
  renderTriples(current, hide);
}
document.querySelector("#filters").addEventListener("change", applyFilters);

function showNode(n) {
  const d = n.data; let h = `<h2>${esc(n.type)}</h2><p><b>${esc(n.label)}</b></p>`;
  if (n.type === "Entity") h += `<dl class="kv"><dt>Type</dt><dd>${esc(d.entity_type)}</dd></dl>`;
  if (n.type === "Claim") {
    h += `<p class="ctx">${esc(d.full_text)}</p><h3>Scope</h3><dl class="kv">` +
      (Object.entries(d.scope).filter(([k]) => k !== "inherited_from_abstract").map(([k,v]) =>
        `<dt>${esc(k.replace("_"," "))}</dt><dd>${esc(v)}${(d.scope.inherited_from_abstract||[]).includes(k) ? " <span class='muted'>(from elsewhere in abstract)</span>" : ""}</dd>`).join("") || "<dd class='muted'>None stated</dd>") +
      `</dl><dl class="kv"><dt>Polarity</dt><dd>${esc(d.polarity)}</dd><dt>Source</dt><dd>${esc(d.abstract_id)}</dd></dl>`;
  }
  if (n.type === "Evidence") {
    const c = d.context; h += `<p class="muted">${esc(d.abstract_id)}: ${esc(d.abstract_title)}</p><p class="ctx">` +
      esc(c.slice(0,d.start)) + `<mark>${esc(c.slice(d.start,d.end))}</mark>` + esc(c.slice(d.end)) + `</p>`;
  }
  if (n.type === "Uncertainty") h += `<p><span class="badge" style="background:${COLORS[d.level]}">${esc(d.level)}</span></p><p>${esc(d.description)}</p>` +
      (d.cue ? `<p class="muted">Triggered by: "${esc(d.cue)}"</p>` : "");
  $("#detail").innerHTML = h;
}
function showEdge(e) {
  $("#detail").innerHTML = `<h2>Relationship</h2><p><b>${esc(e.label)}</b></p><p class="muted">${esc(e.from)} to ${esc(e.to)}</p>`;
}
