function riskTone(risk) {
  if (risk === "Low") return "success";
  if (risk === "Medium") return "warning";
  return "danger";
}

function strategySourceLabel(value) {
  return translateStrategyName(value);
}

function renderRanking(rows) {
  const body = byId("strategy-ranking");
  if (!rows || rows.length === 0) {
    body.innerHTML = `<tr><td colspan="8" class="text-muted">${t("msg.noStrategyData")}</td></tr>`;
    return;
  }

  body.innerHTML = rows.map((row, index) => `
    <tr>
      <td>${index + 1}</td>
      <td><strong>${translateStrategyName(row.name)}</strong></td>
      <td class="text-muted">${strategySourceLabel(row.source)}</td>
      <td class="text-end">${formatPercent(row.roi)}</td>
      <td class="text-end">${formatPercent(row.hit2Rate)}</td>
      <td class="text-end">${formatPercent(row.hit3Rate)}</td>
      <td><span class="badge text-bg-${riskTone(row.risk)}">${translateValue(row.risk)}</span></td>
      <td class="text-end"><strong>${formatScore(row.score)}</strong></td>
    </tr>
  `).join("");
}

function renderRiskCompare(rows) {
  const box = byId("risk-compare");
  if (!rows || rows.length === 0) {
    box.innerHTML = `<div class="empty-state">${t("msg.noRiskData")}</div>`;
    return;
  }

  box.innerHTML = rows.map((row) => `
    <div class="risk-card">
      <div>
        <span>${translateStrategyName(row.name)}</span>
        <strong>${translateValue(row.risk)}</strong>
        <small>${row.sampleSize} ${t("label.samples")}</small>
      </div>
      <b>${row.riskScore}</b>
    </div>
  `).join("");
}

function renderStrategyCharts(data) {
  renderSimpleBarChart(
    "strategy-roi-chart",
    t("chart.roi"),
    (data.roiCompare.labels || []).map(translateStrategyName),
    data.roiCompare.values,
    "rgba(13, 110, 253, 1)"
  );

  renderMultiLineChart("strategy-hit-chart", (data.hitCompare.labels || []).map(translateStrategyName), [
    {
      label: t("label.hit2"),
      data: data.hitCompare.hit2,
      borderColor: "rgba(25, 135, 84, 1)",
      backgroundColor: "rgba(25, 135, 84, 0.08)",
      tension: 0.25,
    },
    {
      label: t("label.hit3"),
      data: data.hitCompare.hit3,
      borderColor: "rgba(255, 193, 7, 1)",
      backgroundColor: "rgba(255, 193, 7, 0.08)",
      tension: 0.25,
    },
  ]);
}

function renderOptimizer(optimizer) {
  const recommendation = optimizer.recommendation || {};
  setText("optimizer-status", `${(optimizer.strategies || []).length} ${t("msg.optimized")}`);
  setText("optimizer-score", recommendation.overallScore || 0);
  setText("optimizer-best", translateStrategyName(recommendation.strategy || "-"));
  setText("optimizer-risk", translateValue(recommendation.risk || "-"));
  setText("optimizer-confidence", formatScore(recommendation.confidence));

  const reasons = recommendation.reasons || [];
  byId("optimizer-reasons").innerHTML = reasons.map((reason) => `
    <div class="optimizer-reason">${translateOptimizerReason(reason)}</div>
  `).join("");

  renderRadarChart(optimizer);
}

function renderRadarChart(optimizer) {
  const comparison = optimizer.comparison || {};
  const rawLabels = comparison.labels || [];
  const labelKeys = {
    roi: "chart.roi",
    "hit rate": "label.hit2",
    risk: "label.risk",
    decision: "label.decisionScore",
    confidence: "label.confidence",
    explain: "label.explain",
  };
  const labels = rawLabels.map((label) => t(labelKeys[String(label).toLowerCase()] || label));
  const strategies = (optimizer.strategies || []).slice(0, 4);
  const colors = [
    "rgba(13, 110, 253, 1)",
    "rgba(25, 135, 84, 1)",
    "rgba(255, 193, 7, 1)",
    "rgba(111, 66, 193, 1)",
  ];

  destroyChart("strategy-radar-chart");
  charts["strategy-radar-chart"] = new Chart(byId("strategy-radar-chart"), {
    type: "radar",
    data: {
      labels,
      datasets: strategies.map((strategy, index) => ({
        label: translateStrategyName(strategy.name),
        data: rawLabels.map((label) => (strategy.radar || {})[label] || 0),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length].replace("1)", "0.12)"),
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8, color: chartTheme().text } },
        tooltip: chartTooltipOptions(),
      },
      scales: {
        r: {
          suggestedMin: 0,
          suggestedMax: 100,
          ticks: { stepSize: 20, color: chartTheme().muted },
          grid: { color: CHART_GRID_COLOR },
          angleLines: { color: CHART_GRID_COLOR },
          pointLabels: { color: chartTheme().text },
        },
      },
    },
  });
}

function renderStrategyExplainPredictions(predictions) {
  const box = byId("strategy-explain-predictions");
  if (!box) return;
  if (!predictions || !predictions.length) {
    box.innerHTML = `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
    return;
  }
  box.innerHTML = predictions.slice(0, 5).map((prediction) => `
    <div class="prediction-command-card">
      <div class="prediction-command-head"><strong>${t("label.set")} ${prediction.set_no}</strong></div>
      <div class="history-numbers">${formatNumbers(prediction.numbers)}</div>
      <div class="prediction-command-meta">
        <span>${t("label.final")}: <b>${formatScore(prediction.final_score)}</b></span>
        <span>${t("label.ai")}: <b>${formatScore(prediction.ai_score)}</b></span>
      </div>
      <button class="btn btn-sm btn-outline-primary" type="button" data-explain-id="${prediction.id}" data-i18n="label.explain">${t("label.explain")}</button>
    </div>
  `).join("");
  bindExplainButtons(box);
}

async function loadStrategyLab() {
  const [data, optimizer, predictions] = await Promise.all([
    fetchJson("/api/strategy-lab"),
    fetchJson("/api/strategy-optimizer"),
    fetchJson("/api/predictions/latest"),
  ]);
  const recommendation = data.recommendation || {};

  setText("strategy-status", `${(data.strategies || []).length} ${t("msg.strategies")}`);
  setText("recommended-score", recommendation.score || 0);
  setText("recommended-strategy", translateStrategyName(recommendation.strategy || "-"));
  setText("recommended-risk", translateValue(recommendation.risk || "-"));
  setText(
    "recommended-reason",
    recommendation.strategy
      ? formatTemplate("msg.bestStrategyReason", { strategy: translateStrategyName(recommendation.strategy) })
      : "-"
  );

  renderRanking(data.ranking || []);
  renderRiskCompare(data.riskCompare || []);
  renderStrategyCharts(data);
  renderOptimizer(optimizer);
  renderStrategyExplainPredictions(predictions);
  applyTranslations();
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadStrategyLab();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);
