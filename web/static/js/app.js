const charts = {};

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  byId(id).innerText = value ?? "-";
}

function setRunState(text, tone) {
  const state = byId("run-state");
  state.className = `badge text-bg-${tone}`;
  state.innerText = text;
}

function setHealth(id, item) {
  const box = byId(id);
  box.classList.toggle("ok", Boolean(item && item.ok));
  box.classList.toggle("warn", !Boolean(item && item.ok));
  box.querySelector("strong").innerText = item ? item.label : "-";
}

function formatNumbers(numbers) {
  if (!numbers || numbers.length === 0) return "-";
  return numbers.map((number) => String(number).padStart(2, "0")).join(" ");
}

function chartLabels(rows, key = "number") {
  return rows.map((row) => String(row[key]).padStart(2, "0"));
}

function chartValues(rows, key = "count") {
  return rows.map((row) => row[key]);
}

function destroyChart(id) {
  if (charts[id]) {
    charts[id].destroy();
  }
}

function renderBarChart(id, label, rows, color) {
  destroyChart(id);
  charts[id] = new Chart(byId(id), {
    type: "bar",
    data: {
      labels: chartLabels(rows),
      datasets: [
        {
          label,
          data: chartValues(rows),
          borderColor: color,
          backgroundColor: color.replace("1)", "0.72)"),
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });
}

function renderSimpleBarChart(id, label, labels, values, color) {
  destroyChart(id);
  charts[id] = new Chart(byId(id), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label,
          data: values,
          borderColor: color,
          backgroundColor: color.replace("1)", "0.72)"),
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });
}

function renderLineChart(id, label, rows, color) {
  destroyChart(id);
  charts[id] = new Chart(byId(id), {
    type: "line",
    data: {
      labels: rows.map((row) => row.label),
      datasets: [
        {
          label,
          data: rows.map((row) => row.value),
          borderColor: color,
          backgroundColor: color.replace("1)", "0.12)"),
          fill: true,
          pointRadius: 1.5,
          tension: 0.25,
        },
      ],
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
  destroyChart(id);
  charts[id] = new Chart(byId(id), {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderColor: "#ffffff",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      cutout: "58%",
      plugins: {
        legend: { position: "bottom" },
      },
    },
  });
}

function renderMultiLineChart(id, labels, datasets) {
  destroyChart(id);
  charts[id] = new Chart(byId(id), {
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

async function executeAction(url) {
  const output = byId("output");
  setRunState("Running", "primary");
  setText("return-code", "return code: -");
  output.innerText = "Running existing program...\n";

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

    output.innerText = lines.join("\n");
    setText("return-code", `return code: ${data.returncode}`);
    setRunState(data.ok ? "Completed" : "Failed", data.ok ? "success" : "danger");
    await refreshDashboard();
  } catch (error) {
    output.innerText = String(error);
    setRunState("Error", "danger");
  }
}

function renderPredictions(predictions) {
  const list = byId("prediction-list");
  list.innerHTML = "";

  if (!predictions || predictions.length === 0) {
    list.innerHTML = '<div class="empty-state">No prediction history yet.</div>';
    return;
  }

  predictions.forEach((prediction) => {
    const item = document.createElement("div");
    item.className = "recommendation";
    item.innerHTML = `
      <div>
        <span>Set ${prediction.set_no}</span>
        <strong>${formatNumbers(prediction.numbers)}</strong>
      </div>
      <small>
        Final ${formatScore(prediction.final_score)} ·
        AI ${formatScore(prediction.ai_score)} ·
        ${prediction.created_at || prediction.model_version}
      </small>
    `;
    list.appendChild(item);
  });
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toFixed(4).replace(/\.?0+$/, "");
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${Number(value).toFixed(2)}%`;
}

function renderPredictionHistory(rows) {
  const body = byId("prediction-history");
  body.innerHTML = "";

  if (!rows || rows.length === 0) {
    body.innerHTML = '<tr><td colspan="5" class="text-muted">No prediction history yet.</td></tr>';
    return;
  }

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.created_at || "-"}</td>
      <td>${row.set_no}</td>
      <td class="history-numbers">${formatNumbers(row.numbers)}</td>
      <td class="text-end">${formatScore(row.final_score)}</td>
      <td class="text-end">${formatScore(row.ai_score)}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadStatus() {
  const response = await fetch("/api/status");
  const data = await response.json();

  setText("prediction-count", data.prediction_count);
  setText("dashboard-status", data.dashboard_exists ? "Ready" : "Missing");
  setText("db-status", data.database_exists ? "Database Ready" : "No Database");
}

async function loadSystemInfo() {
  const response = await fetch("/api/system");
  const data = await response.json();
  const health = data.health || {};

  setHealth("health-database", health.database);
  setHealth("health-api", health.api);
  setHealth("health-learning", health.learning);
  setHealth("health-dashboard", health.dashboard);
  setHealth("health-prediction", health.prediction);
  setHealth("health-runAll", health.runAll);

  const allOk = Object.values(health).every((item) => item && item.ok);
  setText("system-health-status", allOk ? "Healthy" : "Needs Attention");

  setText("version-value", data.version);
  setText("git-branch", data.gitBranch);
  setText("git-commit", data.gitCommit);
  setText("build-time", data.buildTime);
}

function recommendationTone(recommendation) {
  if (recommendation === "Strong Buy") return "success";
  if (recommendation === "Buy") return "primary";
  if (recommendation === "Neutral") return "secondary";
  return "danger";
}

async function loadDecisionCenter() {
  const response = await fetch("/api/decision");
  const data = await response.json();
  const badge = byId("decision-recommendation");

  setText("decision-stars", data.stars);
  setText("decision-score", data.decisionScore);
  setText("decision-confidence", data.confidence);
  setText("decision-risk", data.risk);
  badge.innerText = data.recommendation;
  badge.className = `badge text-bg-${recommendationTone(data.recommendation)}`;

  const reasons = data.reasons || {};
  byId("decision-reasons").innerHTML = Object.entries(reasons).map(([title, values]) => `
    <div class="decision-reason">
      <span>${title}</span>
      <strong>${Array.isArray(values) && values.length ? values.join(" / ") : "-"}</strong>
    </div>
  `).join("");
}

async function loadPredictions() {
  const [latestResponse, historyResponse] = await Promise.all([
    fetch("/api/predictions/latest"),
    fetch("/api/predictions/history"),
  ]);
  const latest = await latestResponse.json();
  const history = await historyResponse.json();

  renderPredictions(latest);
  renderPredictionHistory(history);
}

async function loadDashboardData() {
  const response = await fetch("/api/dashboard-data");
  const data = await response.json();
  const latest = data.latestDraw || {};

  setText("draw-count", data.databaseCount);
  setText("data-window-count", data.recentDraws ? data.recentDraws.length : 0);
  setText("data-window-status", `${data.sumTrend.length} draws`);
  setText("latest-draw-no", latest.drawNo);
  setText("latest-draw-date", latest.drawDate);
  setText("latest-draw-numbers", formatNumbers(latest.numbers));

  renderBarChart("hot-chart", "Hot Count", data.hot, "rgba(13, 110, 253, 1)");
  renderBarChart("cold-chart", "Cold Count", data.cold, "rgba(108, 117, 125, 1)");
  renderLineChart("sum-trend-chart", "Sum", data.sumTrend, "rgba(25, 135, 84, 1)");
  renderLineChart("span-trend-chart", "Span", data.spanTrend, "rgba(255, 193, 7, 1)");
  renderPieChart(
    "odd-even-chart",
    ["Odd", "Even"],
    [data.oddEven.odd, data.oddEven.even],
    ["#0d6efd", "#20c997"]
  );
  renderPieChart(
    "low-high-chart",
    ["Low 1-19", "High 20-39"],
    [data.lowHigh.low, data.lowHigh.high],
    ["#6f42c1", "#fd7e14"]
  );
}

function renderLearningWeights(weights) {
  const box = byId("learning-weights");
  const entries = Object.entries(weights || {});
  if (entries.length === 0) {
    box.innerHTML = '<div class="empty-state">No model weights yet.</div>';
    return;
  }

  box.innerHTML = entries.map(([key, value]) => `
    <div class="weight-chip">
      <span>${key}</span>
      <strong>${Number(value).toFixed(4)}</strong>
    </div>
  `).join("");
}

async function loadLearningCenter() {
  const [latestResponse, historyResponse, weightsResponse] = await Promise.all([
    fetch("/api/learning/latest"),
    fetch("/api/learning/history"),
    fetch("/api/learning/weights"),
  ]);
  const latest = await latestResponse.json();
  const history = await historyResponse.json();
  const weights = await weightsResponse.json();
  const chronological = [...history].reverse();

  setText("learning-model", latest.model_version || "-");
  setText("learning-roi", formatPercent(latest.roi));
  setText("learning-hit2", formatPercent(latest.hit2));
  setText("learning-hit3", formatPercent(latest.hit3));
  setText("learning-hit4", formatPercent(latest.hit4));
  setText("learning-avg", formatScore(latest.avg_match));
  setText("learning-time", latest.created_at || "No learning yet");

  renderLearningWeights(weights.current || latest.weights || {});

  renderLineChart(
    "learning-roi-chart",
    "ROI",
    chronological.map((row) => ({ label: row.created_at, value: row.roi })),
    "rgba(13, 110, 253, 1)"
  );

  const labels = chronological.map((row) => row.created_at);
  renderMultiLineChart("learning-hit-chart", labels, [
    {
      label: "Hit 2+",
      data: chronological.map((row) => row.hit2),
      borderColor: "rgba(25, 135, 84, 1)",
      backgroundColor: "rgba(25, 135, 84, 0.08)",
      tension: 0.25,
    },
    {
      label: "Hit 3+",
      data: chronological.map((row) => row.hit3),
      borderColor: "rgba(255, 193, 7, 1)",
      backgroundColor: "rgba(255, 193, 7, 0.08)",
      tension: 0.25,
    },
    {
      label: "Hit 4+",
      data: chronological.map((row) => row.hit4),
      borderColor: "rgba(220, 53, 69, 1)",
      backgroundColor: "rgba(220, 53, 69, 0.08)",
      tension: 0.25,
    },
  ]);

  const weightHistory = weights.history || [];
  const weightLabels = weightHistory.map((row) => row.created_at);
  const weightKeys = Array.from(new Set(weightHistory.flatMap((row) => Object.keys(row.weights || {}))));
  const colors = [
    "rgba(13, 110, 253, 1)",
    "rgba(32, 201, 151, 1)",
    "rgba(255, 193, 7, 1)",
    "rgba(111, 66, 193, 1)",
    "rgba(253, 126, 20, 1)",
  ];

  renderMultiLineChart(
    "learning-weight-chart",
    weightLabels,
    weightKeys.map((key, index) => ({
      label: key,
      data: weightHistory.map((row) => (row.weights || {})[key]),
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length].replace("1)", "0.08)"),
      tension: 0.25,
    }))
  );
}

function renderBacktestRows(rows) {
  const body = byId("bt-recent-rows");
  body.innerHTML = "";

  if (!rows || rows.length === 0) {
    body.innerHTML = '<tr><td colspan="6" class="text-muted">No backtest report yet.</td></tr>';
    return;
  }

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.draw_date || "-"}</td>
      <td>${row.draw_no || "-"}</td>
      <td class="text-end">${row.best_match}</td>
      <td class="text-end">${formatPercent(row.period_roi)}</td>
      <td class="text-end">${formatPercent(row.cumulative_roi)}</td>
      <td class="history-numbers">${row.winning_numbers || "-"}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadBacktestCenter() {
  const response = await fetch("/api/backtest-center");
  const data = await response.json();
  const summary = data.summary || {};
  const hitTrend = data.hitTrend || {};
  const distribution = data.bestMatchDistribution || [];

  setText("bt-total-periods", summary.total_periods);
  setText("bt-cumulative-roi", formatPercent(summary.cumulative_roi));
  setText("bt-hit2", formatPercent(summary.hit2_rate));
  setText("bt-hit3", formatPercent(summary.hit3_rate));
  setText("bt-avg-match", formatScore(summary.avg_best_match));
  setText("bt-losing-streak", summary.max_losing_streak);
  setText("backtest-center-status", `${summary.total_periods || 0} periods`);

  renderLineChart(
    "bt-roi-chart",
    "Cumulative ROI",
    (data.roiTrend || []).map((row) => ({ label: row.label, value: row.value })),
    "rgba(13, 110, 253, 1)"
  );

  const labels = (hitTrend.hit2 || []).map((row) => row.label);
  renderMultiLineChart("bt-hit-chart", labels, [
    {
      label: "Hit 2+",
      data: (hitTrend.hit2 || []).map((row) => row.value),
      borderColor: "rgba(25, 135, 84, 1)",
      backgroundColor: "rgba(25, 135, 84, 0.08)",
      tension: 0.25,
    },
    {
      label: "Hit 3+",
      data: (hitTrend.hit3 || []).map((row) => row.value),
      borderColor: "rgba(255, 193, 7, 1)",
      backgroundColor: "rgba(255, 193, 7, 0.08)",
      tension: 0.25,
    },
    {
      label: "Hit 4+",
      data: (hitTrend.hit4 || []).map((row) => row.value),
      borderColor: "rgba(220, 53, 69, 1)",
      backgroundColor: "rgba(220, 53, 69, 0.08)",
      tension: 0.25,
    },
  ]);

  renderSimpleBarChart(
    "bt-match-chart",
    "Best Match",
    distribution.map((row) => String(row.match)),
    distribution.map((row) => row.count),
    "rgba(111, 66, 193, 1)"
  );

  renderBacktestRows(data.recentRows || []);
}

async function refreshDashboard() {
  await loadSystemInfo();
  await loadDecisionCenter();
  await loadStatus();
  await loadPredictions();
  await loadDashboardData();
  await loadLearningCenter();
  await loadBacktestCenter();
}

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => executeAction(button.dataset.action));
});

byId("refresh-btn").addEventListener("click", refreshDashboard);

refreshDashboard();
