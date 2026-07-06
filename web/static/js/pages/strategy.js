function riskTone(risk) {
  if (risk === "Low") return "success";
  if (risk === "Medium") return "warning";
  return "danger";
}

function renderRanking(rows) {
  const body = byId("strategy-ranking");
  if (!rows || rows.length === 0) {
    body.innerHTML = '<tr><td colspan="8" class="text-muted">No strategy data available.</td></tr>';
    return;
  }

  body.innerHTML = rows.map((row, index) => `
    <tr>
      <td>${index + 1}</td>
      <td><strong>${row.name}</strong></td>
      <td class="text-muted">${row.source}</td>
      <td class="text-end">${formatPercent(row.roi)}</td>
      <td class="text-end">${formatPercent(row.hit2Rate)}</td>
      <td class="text-end">${formatPercent(row.hit3Rate)}</td>
      <td><span class="badge text-bg-${riskTone(row.risk)}">${row.risk}</span></td>
      <td class="text-end"><strong>${formatScore(row.score)}</strong></td>
    </tr>
  `).join("");
}

function renderRiskCompare(rows) {
  const box = byId("risk-compare");
  if (!rows || rows.length === 0) {
    box.innerHTML = '<div class="empty-state">No risk data available.</div>';
    return;
  }

  box.innerHTML = rows.map((row) => `
    <div class="risk-card">
      <div>
        <span>${row.name}</span>
        <strong>${row.risk}</strong>
        <small>${row.sampleSize} samples</small>
      </div>
      <b>${row.riskScore}</b>
    </div>
  `).join("");
}

function renderStrategyCharts(data) {
  renderSimpleBarChart(
    "strategy-roi-chart",
    "ROI",
    data.roiCompare.labels,
    data.roiCompare.values,
    "rgba(13, 110, 253, 1)"
  );

  renderMultiLineChart("strategy-hit-chart", data.hitCompare.labels, [
    {
      label: "Hit 2+",
      data: data.hitCompare.hit2,
      borderColor: "rgba(25, 135, 84, 1)",
      backgroundColor: "rgba(25, 135, 84, 0.08)",
      tension: 0.25,
    },
    {
      label: "Hit 3+",
      data: data.hitCompare.hit3,
      borderColor: "rgba(255, 193, 7, 1)",
      backgroundColor: "rgba(255, 193, 7, 0.08)",
      tension: 0.25,
    },
  ]);
}

function renderOptimizer(optimizer) {
  const recommendation = optimizer.recommendation || {};
  setText("optimizer-status", `${(optimizer.strategies || []).length} optimized`);
  setText("optimizer-score", recommendation.overallScore || 0);
  setText("optimizer-best", recommendation.strategy || "-");
  setText("optimizer-risk", recommendation.risk || "-");
  setText("optimizer-confidence", formatScore(recommendation.confidence));

  const reasons = recommendation.reasons || [];
  byId("optimizer-reasons").innerHTML = reasons.map((reason) => `
    <div class="optimizer-reason">${reason}</div>
  `).join("");

  renderRadarChart(optimizer);
}

function renderRadarChart(optimizer) {
  const comparison = optimizer.comparison || {};
  const labels = comparison.labels || [];
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
        label: strategy.name,
        data: labels.map((label) => (strategy.radar || {})[label] || 0),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length].replace("1)", "0.12)"),
        pointRadius: 2,
      })),
    },
    options: {
      responsive: true,
      plugins: { legend: { position: "bottom" } },
      scales: {
        r: {
          suggestedMin: 0,
          suggestedMax: 100,
          ticks: { stepSize: 20 },
        },
      },
    },
  });
}

async function loadStrategyLab() {
  const [data, optimizer] = await Promise.all([
    fetchJson("/api/strategy-lab"),
    fetchJson("/api/strategy-optimizer"),
  ]);
  const recommendation = data.recommendation || {};

  setText("strategy-status", `${(data.strategies || []).length} strategies`);
  setText("recommended-score", recommendation.score || 0);
  setText("recommended-strategy", recommendation.strategy || "-");
  setText("recommended-risk", recommendation.risk || "-");
  setText("recommended-reason", recommendation.reason || "-");

  renderRanking(data.ranking || []);
  renderRiskCompare(data.riskCompare || []);
  renderStrategyCharts(data);
  renderOptimizer(optimizer);
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadStrategyLab();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
refreshPage();
