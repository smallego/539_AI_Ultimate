const charts = {};

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const element = byId(id);
  if (element) element.innerText = value ?? "-";
}

function setRunState(text, tone = "secondary") {
  const state = byId("run-state");
  if (!state) return;
  state.className = `badge text-bg-${tone}`;
  state.innerText = text;
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

function formatNumbers(numbers) {
  if (!numbers || numbers.length === 0) return "-";
  return numbers.map((number) => String(number).padStart(2, "0")).join(" ");
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toFixed(4).replace(/\.?0+$/, "");
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${Number(value).toFixed(2)}%`;
}

function setHealth(id, item) {
  const box = byId(id);
  if (!box) return;
  box.classList.toggle("ok", Boolean(item && item.ok));
  box.classList.toggle("warn", !Boolean(item && item.ok));
  const label = box.querySelector("strong");
  if (label) label.innerText = item ? item.label : "-";
}

function destroyChart(id) {
  if (charts[id]) charts[id].destroy();
}

function chartLabels(rows, key = "number") {
  return rows.map((row) => String(row[key]).padStart(2, "0"));
}

function chartValues(rows, key = "count") {
  return rows.map((row) => row[key]);
}

function renderBarChart(id, label, rows, color) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: chartLabels(rows || []),
      datasets: [{
        label,
        data: chartValues(rows || []),
        borderColor: color,
        backgroundColor: color.replace("1)", "0.72)"),
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function renderSimpleBarChart(id, label, labels, values, color) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label,
        data: values,
        borderColor: color,
        backgroundColor: color.replace("1)", "0.72)"),
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function renderLineChart(id, label, rows, color) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "line",
    data: {
      labels: (rows || []).map((row) => row.label),
      datasets: [{
        label,
        data: (rows || []).map((row) => row.value),
        borderColor: color,
        backgroundColor: color.replace("1)", "0.12)"),
        fill: true,
        pointRadius: 1.5,
        tension: 0.25,
      }],
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 10 } },
        y: { beginAtZero: false },
      },
    },
  });
}

function renderPieChart(id, labels, values, colors) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderColor: "#ffffff", borderWidth: 2 }],
    },
    options: {
      responsive: true,
      cutout: "58%",
      plugins: { legend: { position: "bottom" } },
    },
  });
}

function renderMultiLineChart(id, labels, datasets) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "line",
    data: { labels, datasets },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { ticks: { maxTicksLimit: 8 } },
        y: { beginAtZero: false },
      },
    },
  });
}

function recommendationTone(recommendation) {
  if (recommendation === "Strong Buy") return "success";
  if (recommendation === "Buy") return "primary";
  if (recommendation === "Neutral") return "secondary";
  return "danger";
}

async function executeAction(url, afterRun) {
  const output = byId("output");
  setRunState("Running", "primary");
  if (output) output.innerText = "Running existing program...\n";

  try {
    const response = await fetch(url, { method: "POST" });
    const data = await response.json();
    const lines = [
      `OK: ${data.ok}`,
      `Return Code: ${data.returncode}`,
      "",
      data.stdout ? `===== STDOUT =====\n${data.stdout}` : "",
      data.stderr ? `===== STDERR =====\n${data.stderr}` : "",
    ].filter(Boolean);

    if (output) output.innerText = lines.join("\n");
    setRunState(data.ok ? "Completed" : "Failed", data.ok ? "success" : "danger");
    if (typeof afterRun === "function") await afterRun();
  } catch (error) {
    if (output) output.innerText = String(error);
    setRunState("Error", "danger");
  }
}

function wireActions(afterRun) {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => executeAction(button.dataset.action, afterRun));
  });
}

async function loadFooterVersion() {
  try {
    const data = await fetchJson("/api/system");
    setText("footer-version", `Version ${data.version} | ${data.gitBranch} ${data.gitCommit}`);
  } catch (error) {
    setText("footer-version", "Version unavailable");
  }
}

function bindRefresh(refreshFn) {
  const button = byId("refresh-btn");
  if (button && typeof refreshFn === "function") button.addEventListener("click", refreshFn);
}

loadFooterVersion();
