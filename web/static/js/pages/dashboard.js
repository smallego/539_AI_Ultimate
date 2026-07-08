function money(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `$${Number(value).toLocaleString()}`;
}

function score2(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : value;
}

function pct(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  return Number.isFinite(number) ? `${number.toFixed(2)}%` : value;
}

function drawStatus(value) {
  if (!value) return "-";
  return t(`prediction.${value}`) || translateValue(value);
}

function statusTone(value) {
  if (value === "finished") return "success";
  if (value === "waiting_draw") return "warning";
  return "secondary";
}

function riskTone(risk) {
  if (risk === "Low") return "success";
  if (risk === "Medium") return "warning";
  return "danger";
}

function numberPills(numbers) {
  if (!numbers || !numbers.length) return `<span class="text-muted">-</span>`;
  return numbers.map((number) => `<span class="number-pill">${String(number).padStart(2, "0")}</span>`).join("");
}

function predictionQuality(row) {
  return Number(row?.ai_score || 0) + Number(row?.final_score || 0) * 100;
}

function bestPickRows(todayPrediction) {
  const rows = [...(todayPrediction.rows || [])];
  return rows.sort((a, b) => {
    if (a.set_no === todayPrediction.bestSet) return -1;
    if (b.set_no === todayPrediction.bestSet) return 1;
    return predictionQuality(b) - predictionQuality(a);
  });
}

function renderHero(summary, signal) {
  const badge = byId("signal-badge");
  const status = summary.drawStatus;
  if (badge) {
    badge.className = `badge text-bg-${signal.color || "secondary"}`;
    badge.innerText = translateValue(signal.signal || "-");
  }
  setText("signal-stars", formatStars(signal.stars));
  setText("signal-score", score2(signal.score));
  setText("signal-name", translateValue(signal.signal || "-"));
  setText("signal-confidence", score2(signal.confidence));
  setText("signal-risk", translateValue(signal.risk || "-"));
  setText("hero-latest-draw", summary.latestDraw || "-");
  setText("hero-draw-status", drawStatus(status));
  const reason = byId("signal-reason");
  if (reason) reason.innerHTML = renderSignalReasonItems(signal);
}

function renderBestPick(todayPrediction) {
  const rows = bestPickRows(todayPrediction);
  const best = rows[0];
  const card = byId("best-pick-card");
  const list = byId("top-picks");
  const badge = byId("best-pick-badge");
  if (!best) {
    if (card) card.innerHTML = `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
    if (list) list.innerHTML = "";
    if (badge) badge.innerText = "-";
    return;
  }
  if (badge) badge.innerText = `${t("label.set")} ${best.set_no}`;
  card.innerHTML = `
    <div class="best-pick-head">
      <span>${t("dashboard.best_pick")}</span>
      <strong>${t("label.set")} ${best.set_no}</strong>
    </div>
    <div class="number-pill-row">${numberPills(best.numbers)}</div>
    <div class="best-pick-meta">
      <span>${t("decision.ai_score")}: <b>${score2(best.ai_score)}</b></span>
      <span>${t("decision.final_score")}: <b>${score2(best.final_score)}</b></span>
    </div>
    <button class="btn btn-sm btn-outline-primary" type="button" data-explain-id="${best.id}">${t("label.explain")}</button>
  `;
  list.innerHTML = rows.slice(1, 5).map((row, index) => `
    <div class="top-pick-item">
      <span>${t("dashboard.top")} ${index + 2}</span>
      <strong>${t("label.set")} ${row.set_no}</strong>
      <div class="number-pill-row">${numberPills(row.numbers)}</div>
      <small>${t("decision.ai_score")} ${score2(row.ai_score)} / ${t("decision.final_score")} ${score2(row.final_score)}</small>
    </div>
  `).join("");
  bindExplainButtons(card);
}

function renderCurrentResult(summary, result, analysis) {
  const status = result.status || summary.drawStatus || "waiting_draw";
  const statusBadge = byId("today-result-status");
  if (statusBadge) {
    statusBadge.className = `badge text-bg-${statusTone(status)}`;
    statusBadge.innerText = drawStatus(status);
  }
  setText("result-latest-draw", summary.latestDraw || "-");
  setText("result-best-hit", analysis.bestMatch ?? result.bestHit ?? "-");
  setText("result-best-set", analysis.bestSet ? `${t("label.set")} ${analysis.bestSet}` : result.bestSet ? `${t("label.set")} ${result.bestSet}` : "-");
  setText("result-total-prize", status === "waiting_draw" ? t("dashboard.waiting_draw") : money(analysis.totalPrize ?? result.prize));
  setText("result-roi", status === "waiting_draw" ? "-" : pct(result.roi));
  const matched = byId("result-matched");
  if (matched) {
    matched.innerHTML = status === "waiting_draw"
      ? `<span class="badge text-bg-warning">${t("dashboard.waiting_draw")}</span>`
      : `<span class="badge text-bg-success">${t("prediction.matched_numbers")}</span><div class="number-pill-row">${numberPills(result.matchedNumbers || [])}</div>`;
  }
}

function renderRecentPerformance(pro, analysis) {
  const result = pro.todayResult || {};
  const trend = pro.trend30 || {};
  const hitRows = trend.hitRate || [];
  const latestHit = hitRows.length ? hitRows[hitRows.length - 1].value : null;
  setText("performance-status", `${(hitRows.length || 0)} ${t("msg.draws")}`);
  setText("perf-roi", pct(result.roi));
  setText("perf-hit-rate", latestHit === null || latestHit === undefined ? "-" : pct(latestHit));
  setText("perf-average-hits", analysis.averageHits ?? result.bestHit ?? "-");
  setText("perf-prize", money(analysis.totalPrize ?? result.prize));
  setText("perf-average-api", `${(pro.performance || {}).averageApiTime || 0} ms`);
  renderPerformanceTrend(trend);
}

function executiveLineOptions() {
  const theme = chartTheme();
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: chartAnimationOptions(),
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8, color: theme.text } },
      tooltip: {
        ...chartTooltipOptions(),
        cornerRadius: 8,
      },
    },
    scales: {
      x: {
        grid: { color: getComputedStyle(document.documentElement).getPropertyValue("--chart-grid").trim() || "#ececec" },
        ticks: { color: theme.muted, autoSkip: true, maxTicksLimit: 8 },
      },
      y: {
        beginAtZero: false,
        grid: { color: getComputedStyle(document.documentElement).getPropertyValue("--chart-grid").trim() || "#ececec" },
        ticks: { color: theme.muted },
      },
      y1: {
        type: "linear",
        position: "right",
        grid: { drawOnChartArea: false },
        ticks: { color: theme.muted },
      },
    },
  };
}

function lineData(rows) {
  return (rows || []).map((row) => row.value);
}

function lineLabels(rows) {
  return (rows || []).map((row) => row.label);
}

function renderPerformanceTrend(trend) {
  const roi = trend.roi || [];
  const hit = trend.hitRate || [];
  const decision = trend.decisionScore || [];
  const labels = lineLabels(roi.length ? roi : hit.length ? hit : decision);
  destroyChart("performance-trend-chart");
  charts["performance-trend-chart"] = new Chart(byId("performance-trend-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: t("chart.roi"),
          data: lineData(roi),
          borderColor: "rgba(13, 110, 253, 1)",
          backgroundColor: "rgba(13, 110, 253, 0.12)",
          borderWidth: 2,
          pointRadius: 2,
          pointHoverRadius: 5,
          tension: 0.35,
          yAxisID: "y",
        },
        {
          label: t("prediction.hit_rate"),
          data: lineData(hit),
          borderColor: "rgba(25, 135, 84, 1)",
          backgroundColor: "rgba(25, 135, 84, 0.12)",
          borderWidth: 2,
          pointRadius: 2,
          pointHoverRadius: 5,
          tension: 0.35,
          yAxisID: "y1",
        },
        {
          label: t("label.decisionScore"),
          data: lineData(decision),
          borderColor: "rgba(111, 66, 193, 1)",
          backgroundColor: "rgba(111, 66, 193, 0.12)",
          borderWidth: 2,
          pointRadius: 2,
          pointHoverRadius: 5,
          tension: 0.35,
          yAxisID: "y1",
        },
      ],
    },
    options: executiveLineOptions(),
  });
}

function renderStrategySummary(strategy) {
  const ranking = strategy.ranking || [];
  const best = ranking[0] || {};
  setText("strategy-overview-status", `${ranking.length} ${t("msg.strategies")}`);
  setText("strategy-best", translateStrategyName(strategy.bestStrategy || best.name || "-"));
  setText("strategy-overall-score", score2(strategy.overallScore || best.score));
  setText("strategy-roi", pct(best.roi));
  setText("strategy-win-rate", pct(best.hit2Rate));
  const explain = byId("strategy-explain");
  if (explain) {
    explain.innerHTML = `
      <div class="decision-reason">
        <span>${t("label.strategy")}</span>
        <strong>${translateStrategyName(strategy.bestStrategy || best.name || "-")}</strong>
      </div>
      <div class="decision-reason">
        <span>${t("label.risk")}</span>
        <strong><span class="badge text-bg-${riskTone(strategy.risk || best.risk)}">${translateValue(strategy.risk || best.risk || "-")}</span></strong>
      </div>
      <div class="decision-reason">
        <span>${t("label.explain")}</span>
        <strong>${formatTemplate("dashboard.strategy_explain", { strategy: translateStrategyName(strategy.bestStrategy || best.name || "-") })}</strong>
      </div>
    `;
  }
  renderStrategyChart(ranking);
}

function renderStrategyChart(ranking) {
  const rows = (ranking || []).slice(0, 5);
  destroyChart("strategy-summary-chart");
  charts["strategy-summary-chart"] = new Chart(byId("strategy-summary-chart"), {
    type: "bar",
    data: {
      labels: rows.map((row) => translateStrategyName(row.name)),
      datasets: [
        {
          label: t("label.score"),
          data: rows.map((row) => row.score || 0),
          backgroundColor: "rgba(13, 110, 253, 0.72)",
          borderColor: "rgba(13, 110, 253, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: chartAnimationOptions(),
      plugins: {
        legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8, color: chartTheme().text } },
        tooltip: chartTooltipOptions(),
      },
      scales: {
        x: { grid: { color: CHART_GRID_COLOR }, ticks: { color: chartTheme().muted, autoSkip: true, maxTicksLimit: 8 } },
        y: { beginAtZero: true, grid: { color: CHART_GRID_COLOR }, ticks: { color: chartTheme().muted } },
      },
    },
  });
}

function dashboardMode() {
  return preference("dashboardMode", "simple");
}

function translateModelName(name) {
  const key = {
    "Prediction Strategy": "dashboard.prediction_model",
    "Backtest Strategy": "dashboard.backtest_model",
    "Learning Strategy": "dashboard.learning_model",
    "Hybrid Strategy": "dashboard.hybrid_model",
  }[name];
  return key ? t(key) : translateStrategyName(name || "-");
}

function renderSimplePrediction(data) {
  const prediction = data || {};
  const signal = prediction.aiSignal || {};
  const best = prediction.bestPick || {};
  const recommendations = prediction.recommendations || [];
  const badge = byId("simple-buy-badge");
  if (badge) {
    badge.className = `badge text-bg-${prediction.shouldBuy ? "success" : "warning"}`;
    badge.innerText = prediction.shouldBuy ? t("dashboard.should_buy") : t("dashboard.watch_first");
  }
  setText("simple-buy-recommendation", translateValue(prediction.buyRecommendation || "-"));
  setText("simple-ai-signal", `${translateValue(signal.signal || "-")} ${score2(signal.score)}`);
  setText("simple-best-set", best.set_no ? `${t("label.set")} ${best.set_no}` : "-");
  const bestNumbers = byId("simple-best-numbers");
  if (bestNumbers) bestNumbers.innerHTML = numberPills(best.numbers || []);

  const explainButton = byId("simple-explain-button");
  if (explainButton) {
    explainButton.dataset.explainId = best.id || "";
    explainButton.disabled = !best.id;
    bindExplainButtons(explainButton.parentElement);
  }

  const list = byId("simple-prediction-list");
  if (!list) return;
  list.innerHTML = recommendations.slice(0, 5).map((row) => `
    <div class="simple-list-item">
      <strong>${t("label.set")} ${row.set_no || "-"}</strong>
      <div class="number-pill-row">${numberPills(row.numbers || [])}</div>
      <small>${t("decision.ai_score")} ${score2(row.ai_score)} / ${t("prediction.final_score")} ${score2(row.final_score)}</small>
    </div>
  `).join("") || `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
}

function renderSimpleLastResult(data) {
  const result = data || {};
  const status = result.status || "waiting_draw";
  const badge = byId("simple-result-status");
  if (badge) {
    badge.className = `badge text-bg-${statusTone(status)}`;
    badge.innerText = drawStatus(status);
  }
  setText("simple-draw-no", result.drawNo || "-");
  const drawNumbers = byId("simple-draw-numbers");
  if (drawNumbers) drawNumbers.innerHTML = numberPills(result.drawNumbers || []);
  setText("simple-total-prize", status === "waiting_draw" ? t("dashboard.waiting_draw") : money(result.totalPrize));
  setText("simple-roi", status === "waiting_draw" ? "-" : pct(result.roi));

  const list = byId("simple-result-list");
  if (!list) return;
  const rows = result.predictions || [];
  list.innerHTML = rows.map((row) => `
    <div class="simple-list-item simple-result-item">
      <div>
        <strong>${t("label.set")} ${row.set_no || "-"}</strong>
        <div class="number-pill-row">${numberPills(row.numbers || [])}</div>
      </div>
      <div class="simple-result-metrics">
        <span>${t("prediction.hits")}: <b>${row.hits ?? "-"}</b></span>
        <span>${t("prediction.matched_numbers")}: ${numberPills(row.matched_numbers || [])}</span>
        <span>${t("prediction.prize")}: <b>${row.prize === null || row.prize === undefined ? "-" : money(row.prize)}</b></span>
      </div>
    </div>
  `).join("") || `<div class="empty-state">${t("dashboard.waiting_draw")}</div>`;
}

function renderSimpleModelComparison(models, bestModel) {
  const table = byId("simple-model-comparison");
  setText("simple-best-model", bestModel ? translateModelName(bestModel.name) : "-");
  if (!table) return;
  table.innerHTML = (models || []).map((model) => `
    <tr>
      <td><strong>${translateModelName(model.name)}</strong></td>
      <td>${pct(model.recentRoi)}</td>
      <td>${pct(model.hitRate)}</td>
      <td>${score2(model.averageHits)}</td>
      <td><span class="badge text-bg-${riskTone(model.risk)}">${translateValue(model.risk || "-")}</span></td>
      <td>${translateValue(model.recommendation || "-")}</td>
    </tr>
  `).join("") || `<tr><td colspan="6" class="text-muted">${t("msg.noData")}</td></tr>`;
}

function renderSimpleAutoModel(data) {
  const auto = data || {};
  const last = auto.lastRun || {};
  setText("auto-model-version", auto.modelVersion || "-");
  setText("auto-last-run", last.createdAt || t("dashboard.no_history"));
  setText("auto-old-roi", last.oldRoi === null || last.oldRoi === undefined ? pct(auto.currentRoi) : pct(last.oldRoi));
  setText("auto-new-roi", last.newRoi === null || last.newRoi === undefined ? "-" : pct(last.newRoi));
  setText("auto-backtest-result", last.reason || "-");
  setText("auto-adopted", last.createdAt ? (last.adopted ? t("dashboard.adopted") : t("dashboard.not_adopted")) : "-");
  setText("auto-model-reason", last.reason || t("dashboard.no_history"));
}

function setDashboardMode(mode) {
  const nextMode = mode === "advanced" ? "advanced" : "simple";
  setPreference("dashboardMode", nextMode);
  document.querySelectorAll("[data-dashboard-mode]").forEach((button) => {
    const active = button.dataset.dashboardMode === nextMode;
    button.classList.toggle("btn-primary", active);
    button.classList.toggle("btn-outline-primary", !active);
  });
  byId("simple-dashboard")?.classList.toggle("d-none", nextMode !== "simple");
  byId("advanced-dashboard")?.classList.toggle("d-none", nextMode !== "advanced");
}

function bindDashboardModeToggle() {
  document.querySelectorAll("[data-dashboard-mode]").forEach((button) => {
    button.addEventListener("click", async () => {
      setDashboardMode(button.dataset.dashboardMode);
      await refreshPage();
    });
  });
}

async function loadSimpleDashboard() {
  const data = await fetchJson("/api/simple-dashboard");
  renderSimplePrediction(data.currentPrediction || {});
  renderSimpleLastResult(data.lastResult || {});
  renderSimpleModelComparison(data.modelComparison || [], data.bestModel || null);
  renderSimpleAutoModel(data.autoModel || {});
  applyTranslations();
}

async function loadAdvancedDashboard() {
  const [pro, signal, analysis] = await Promise.all([
    fetchJson("/api/dashboard-pro"),
    fetchJson("/api/ai-signal"),
    fetchJson("/api/prediction-analysis"),
  ]);
  renderHero(pro.todaySummary || {}, signal || {});
  renderBestPick(pro.todayPrediction || {});
  renderCurrentResult(pro.todaySummary || {}, pro.todayResult || {}, analysis || {});
  renderRecentPerformance(pro || {}, analysis || {});
  renderStrategySummary(pro.strategyOverview || {});
  applyTranslations();
}

async function runAutoModel() {
  setRunState("Running", "primary");
  setActionDetail(`${t("dashboard.auto_model_loop")} ${t("status.running")}...`);
  try {
    const response = await fetch("/api/auto-model/run", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.reason || response.statusText);
    if (window.addAppNotification) {
      addAppNotification(data.adopted ? "success" : "info", data.reason || t("status.completed"));
    }
    await loadSimpleDashboard();
    setRunState("Completed", "success");
  } catch (error) {
    setRunState("Failed", "danger");
    setActionDetail(String(error));
    if (window.addAppNotification) addAppNotification("error", t("status.failed"));
  }
}

function bindAutoModelRun() {
  document.querySelectorAll("[data-auto-model-run]").forEach((button) => {
    button.addEventListener("click", runAutoModel);
  });
}

function bindDashboardActions() {
  document.querySelectorAll("[data-dashboard-action]").forEach((button) => {
    button.addEventListener("click", () => runAction(button.innerText.trim(), button.dataset.apiUrl));
  });
}

async function loadDashboardStatus() {
  if (dashboardMode() === "advanced") {
    await loadAdvancedDashboard();
  } else {
    await loadSimpleDashboard();
  }
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadDashboardStatus();
  setRunState("Ready", "secondary");
}

setDashboardMode(dashboardMode());
bindDashboardModeToggle();
bindDashboardActions();
bindAutoModelRun();
bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);
