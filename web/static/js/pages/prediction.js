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
        Final ${formatScore(prediction.final_score)} |
        AI ${formatScore(prediction.ai_score)} |
        ${prediction.created_at || prediction.model_version}
      </small>
      <button class="btn btn-outline-primary btn-sm mt-2" data-explain-id="${prediction.id}">Explain</button>
    `;
    list.appendChild(item);
  });
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
      <td class="text-end">
        ${formatScore(row.ai_score)}
        <button class="btn btn-outline-primary btn-sm ms-2" data-explain-id="${row.id}">Explain</button>
      </td>
    `;
    body.appendChild(tr);
  });
}

function scoreTone(score) {
  if (score >= 75) return "success";
  if (score >= 55) return "primary";
  return "danger";
}

function reasonScore(value) {
  const numeric = Number(value || 0);
  const sign = numeric > 0 ? "+" : "";
  return `${sign}${numeric}`;
}

function renderExplainReport(report) {
  setText("explain-subtitle", `Set ${report.setNo || "-"} | ${formatNumbers(report.numbers)} | ${report.createdAt || "-"}`);
  setText("explain-stars", report.stars);
  setText("explain-score", report.decisionScore);
  setText("explain-confidence", formatScore(report.confidence));
  setText("explain-risk", report.risk);

  const scoreBox = byId("explain-score").closest(".decision-score");
  scoreBox.classList.remove("score-success", "score-primary", "score-danger");
  scoreBox.classList.add(`score-${scoreTone(report.decisionScore)}`);

  byId("explain-reasons").innerHTML = (report.reasons || []).map((reason) => `
    <div class="explain-reason">
      <div>
        <span>${reason.type}</span>
        <strong>${reason.title}</strong>
      </div>
      <b class="${Number(reason.score) >= 0 ? "positive" : "negative"}">${reasonScore(reason.score)}</b>
    </div>
  `).join("");

  byId("explain-timeline").innerHTML = (report.timeline || []).map((item, index) => `
    <div class="timeline-item">
      <span>${index + 1}</span>
      <div><strong>${item.step}</strong><small>${item.title}</small></div>
    </div>
  `).join("");
}

async function openExplainReport(predictionId) {
  setRunState("Explaining", "primary");
  const report = await fetchJson(`/api/explain/${predictionId}`);
  renderExplainReport(report);
  const drawer = bootstrap.Offcanvas.getOrCreateInstance(byId("explain-drawer"));
  drawer.show();
  setRunState("Ready", "secondary");
}

function bindExplainButtons() {
  document.querySelectorAll("[data-explain-id]").forEach((button) => {
    button.addEventListener("click", () => openExplainReport(button.dataset.explainId));
  });
}

async function loadPredictionPage() {
  const [status, dashboard, latest, history] = await Promise.all([
    fetchJson("/api/status"),
    fetchJson("/api/dashboard-data"),
    fetchJson("/api/predictions/latest"),
    fetchJson("/api/predictions/history"),
  ]);

  const latestDraw = dashboard.latestDraw || {};
  setText("db-status", status.database_exists ? "Database Ready" : "No Database");
  setText("latest-draw-no", latestDraw.drawNo);
  setText("latest-draw-date", latestDraw.drawDate);
  setText("latest-draw-numbers", formatNumbers(latestDraw.numbers));
  renderPredictions(latest);
  renderPredictionHistory(history);
  bindExplainButtons();
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadPredictionPage();
  setRunState("Ready", "secondary");
}

wireActions(refreshPage);
bindRefresh(refreshPage);
refreshPage();
