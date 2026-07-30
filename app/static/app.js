const byId = (id) => document.getElementById(id);

function setScrollProgress() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  byId("scroll-progress").style.width = `${(window.scrollY / scrollable) * 100}%`;
  
  // Hero Zoom Logic
  const heroContainer = document.querySelector(".hero-container");
  if (heroContainer) {
    const rect = heroContainer.getBoundingClientRect();
    const progress = Math.max(0, Math.min(1, -rect.top / (rect.height - window.innerHeight)));
    const orbits = document.querySelector(".hero-orbits");
    const grid = document.querySelector(".hero-grid-lines");
    const slides = document.querySelectorAll(".hero-slide");
    
    if (orbits) orbits.style.transform = `scale(${1 + progress * 8}) rotate(${progress * 20}deg)`;
    if (grid) grid.style.transform = `perspective(1000px) rotateX(60deg) translateY(${progress * 200}px) scale(${1 + progress * 2})`;
    
    const slideIndex = Math.min(slides.length - 1, Math.floor(progress * slides.length * 1.2));
    slides.forEach((slide, i) => {
      if (i === slideIndex) slide.classList.add("active");
      else slide.classList.remove("active");
    });
  }
}

function animateStarfield() {
  const canvas = byId("starfield");
  const context = canvas.getContext("2d");
  const pointer = { x: 0, y: 0 };
  let stars = [];
  function resize() {
    canvas.width = window.innerWidth * devicePixelRatio;
    canvas.height = window.innerHeight * devicePixelRatio;
    context.scale(devicePixelRatio, devicePixelRatio);
    stars = Array.from({ length: Math.min(180, Math.floor(window.innerWidth / 7)) }, () => ({
      x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight,
      z: Math.random() * .8 + .2, size: Math.random() * 1.4 + .2,
    }));
  }
  function frame() {
    context.clearRect(0, 0, window.innerWidth, window.innerHeight);
    stars.forEach((star) => {
      const parallaxX = pointer.x * star.z * 10;
      const parallaxY = pointer.y * star.z * 10;
      context.fillStyle = `rgba(190,224,255,${star.z * .7})`;
      context.beginPath();
      context.arc(star.x + parallaxX, star.y + parallaxY, star.size, 0, Math.PI * 2);
      context.fill();
    });
    requestAnimationFrame(frame);
  }
  window.addEventListener("resize", resize);
  window.addEventListener("pointermove", (event) => {
    pointer.x = (event.clientX / window.innerWidth - .5) * -1;
    pointer.y = (event.clientY / window.innerHeight - .5) * -1;
  });
  resize(); frame();
}

function setRevealObservers() {
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add("visible");
  }), { threshold: .14 });
  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
  const flightSteps = document.querySelectorAll(".flight-step");
  const caption = byId("flight-caption");
  const flightVisual = document.querySelector(".flight-visual");
  const flightObserver = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    flightSteps.forEach((step) => step.classList.remove("active"));
    entry.target.classList.add("active");
    caption.style.opacity = "0";
    caption.style.transform = "translateY(12px)";
    setTimeout(() => {
      caption.innerHTML = `<span>${entry.target.dataset.step}</span><strong>${entry.target.dataset.title}</strong><p>${entry.target.dataset.copy}</p>`;
      caption.style.opacity = "1"; caption.style.transform = "none";
    }, 180);
    flightVisual.style.transform = `scale(${1 + Number(entry.target.dataset.step) * .045}) rotate(${Number(entry.target.dataset.step) * -4}deg)`;
  }), { threshold: .55 });
  flightSteps.forEach((step) => flightObserver.observe(step));

  // Method Scrollytelling Observer
  const methodSteps = document.querySelectorAll(".method-step");
  const diagramLayers = document.querySelectorAll(".diagram-layer");
  const methodObserver = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    diagramLayers.forEach((layer) => {
      if (layer.dataset.layer === entry.target.dataset.layer) layer.classList.add("active");
      else layer.classList.remove("active");
    });
  }), { threshold: .5 });
  methodSteps.forEach((step) => methodObserver.observe(step));
}

function setLabTabs() {
  document.querySelectorAll(".lab-tab").forEach((tab) => tab.addEventListener("click", () => {
    document.querySelectorAll(".lab-tab,.lab-panel").forEach((element) => element.classList.remove("active"));
    tab.classList.add("active"); byId(tab.dataset.panel).classList.add("active");
  }));
}

function setUploadStates() {
  document.querySelectorAll(".dropzone").forEach((zone) => {
    const input = zone.querySelector("input"); const label = zone.querySelector("strong");
    input.addEventListener("change", () => { if (input.files[0]) label.textContent = input.files[0].name; });
    ["dragenter", "dragover"].forEach((eventName) => zone.addEventListener(eventName, (event) => { event.preventDefault(); zone.classList.add("dragging"); }));
    ["dragleave", "drop"].forEach((eventName) => zone.addEventListener(eventName, (event) => { event.preventDefault(); zone.classList.remove("dragging"); }));
    zone.addEventListener("drop", (event) => { input.files = event.dataTransfer.files; input.dispatchEvent(new Event("change")); });
  });
  document.querySelectorAll("input[type=range]").forEach((input) => input.addEventListener("input", () => {
    const output = document.querySelector(`[data-output="${input.name}"]`);
    output.textContent = input.name === "capacity_weight" ? `${Math.round(input.value * 100)}%` : `${input.value} km`;
  }));
}

function csvDownload(rows, filename) {
  if (!rows.length) return "";
  const columns = Object.keys(rows[0]);
  const csv = [columns.join(","), ...rows.map((row) => columns.map((column) => JSON.stringify(row[column] ?? "")).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  return URL.createObjectURL(blob);
}

function table(rows, limit = 12) {
  if (!rows.length) return "<p class='result-caveat'>No data meets the current criteria.</p>";
  const columns = Object.keys(rows[0]).slice(0, 9);
  const format = (value) => typeof value === "number" ? Number(value.toFixed(3)) : value ?? "-";
  return `<div class="result-table-wrap"><table class="result-table"><thead><tr>${columns.map((column) => `<th>${column}</th>`).join("")}</tr></thead><tbody>${rows.slice(0, limit).map((row) => `<tr>${columns.map((column) => `<td>${format(row[column])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function topThree(rows) {
  if (!rows || rows.length === 0) return "";
  const top = rows.slice(0, 3);
  return `
    <div class="top-three-grid">
      ${top.map((row, i) => `
        <div class="top-basin-card ${i === 0 ? 'winner' : ''}">
          <span class="rank">#${i + 1}</span>
          <div class="card-body">
            <strong>${row.basin || "Unknown Basin"}</strong>
            <div class="score-line"><small>Screening Score</small> <span>${Number(row.screening_score || 0).toFixed(1)}</span></div>
            <div class="stats-row">
              <div><small>Emitter Dist.</small><span>${Math.round(row.nearest_emitter_km || 0)} km</span></div>
              <div><small>SRL</small><span>${row.srl || "2"}</span></div>
            </div>
            <button class="select-basin-button" onclick="selectBasinForTier2('${row.basin.replace(/'/g, "\\'")}')">Select for Reservoir Analysis<i>→</i></button>
          </div>
        </div>
      `).join("")}
    </div>
  `;
}

function selectBasinForTier2(name) {
  const tier2Tab = document.querySelector('[data-panel="tier2"]');
  if (tier2Tab) {
    tier2Tab.click();
    const tier2Form = byId("tier2-form");
    tier2Form.scrollIntoView({ behavior: "smooth", block: "center" });
    
    // Add a temporary highlight or message
    const copy = tier2Form.previousElementSibling.querySelector("p");
    const originalText = copy.innerHTML;
    copy.innerHTML = `<strong>Target Basin: ${name}</strong>. Please upload the specific reservoir grid for this candidate.`;
    copy.style.color = "var(--acid)";
    setTimeout(() => {
      copy.innerHTML = originalText;
      copy.style.color = "";
    }, 5000);
  }
}

function metrics(summary) {
  return `<div class="metric-grid">${Object.entries(summary).map(([key, value]) => `<div class="metric-card"><span>${key.replaceAll("_", " ")}</span><strong>${typeof value === "number" ? value.toLocaleString() : value}</strong></div>`).join("")}</div>`;
}

function tier2Justification(summary, payload) {
  return `
    <div class="justification-box">
      <p class="eyebrow">Scientific Justification</p>
      <p>The screening identified <strong>${summary.connected_clusters} clusters</strong> covering <strong>${summary.connected_area_km2} km²</strong> that satisfy the multi-criteria optimal gate.</p>
      <div class="logic-grid">
        <div class="logic-item"><span>1. Physics</span><small>CO2 density > 300 kg/m³ ensures efficient storage phase.</small></div>
        <div class="logic-item"><span>2. Geology</span><small>Porosity > 10% ensures sufficient injectivity and volume.</small></div>
        <div class="logic-item"><span>3. Risk</span><small>Setbacks from fault traces mitigate structural integrity risks.</small></div>
        <div class="logic-item"><span>4. Scale</span><small>Only clusters > 100 km² were retained for project viability.</small></div>
      </div>
    </div>
  `;
}

async function submitWorkflow(event, endpoint, type) {
  event.preventDefault();
  const form = event.currentTarget; const button = form.querySelector("button"); const results = byId("results");
  button.disabled = true; button.querySelector("span").textContent = "Processing evidence...";
  results.innerHTML = `<div class="result-empty"><span>ORBIT COMPUTING</span><p>Tracing the field...</p></div>`;
  try {
    const response = await fetch(endpoint, { method: "POST", body: new FormData(form) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The analysis could not be completed.");
    const rows = type === "tier1" ? payload.results : payload.capacities;
    const filename = type === "tier1" ? "orbit_tier1_results.csv" : "orbit_tier2_capacity.csv";
    const link = csvDownload(rows, filename);
    const gridLink = type === "tier2" ? csvDownload(payload.grid, "orbit_tier2_classified_grid.csv") : "";
    const downloads = `${link ? `<a class="download-result" href="${link}" download="${filename}">Download result CSV ↓</a>` : ""}${gridLink ? `<a class="download-result secondary" href="${gridLink}" download="orbit_tier2_classified_grid.csv">Download classified grid ↓</a>` : ""}`;
    const heading = type === "tier1" ? "National Screening: Top 3 Recommended Basins" : "Reservoir Screening: Identified Optimal Clusters";
    const topResults = type === "tier1" ? topThree(rows) : tier2Justification(payload.summary, payload);
    results.innerHTML = `
      <div class="result-heading"><div><p class="eyebrow">RESULT / SCIENTIFIC OUTPUT</p><h3>${heading}</h3></div></div>
      ${topResults}
      ${type === "tier1" ? "" : metrics(payload.summary)}
      ${table(rows)}
      <p class="result-caveat">${payload.caveat}</p>
      ${downloads}
    `;
    results.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (error) {
    results.innerHTML = `<div class="result-empty"><span>ANALYSIS INTERRUPTED</span><p>${error.message}</p></div>`;
  } finally {
    button.disabled = false; button.querySelector("span").textContent = type === "tier1" ? "Run national screening" : "Run reservoir screening";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  animateStarfield(); setRevealObservers(); setLabTabs(); setUploadStates(); setScrollProgress();
  window.addEventListener("scroll", setScrollProgress, { passive: true });
  byId("tier1-form").addEventListener("submit", (event) => submitWorkflow(event, "/api/tier1", "tier1"));
  byId("tier2-form").addEventListener("submit", (event) => submitWorkflow(event, "/api/tier2", "tier2"));
});
