function renderBacktestRows(rows) {
  const body = byId("bt-recent-rows");
  body.innerHTML = "";

  if (!rows || rows.length === 0) {
    body.innerHTML = `<tr><td colspan="6" class="text-muted">${t("msg.noBacktest")}</td></tr>`;
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

async function loadBacktestPage() {
  const data = await fetchJson("/api/backtest-center");
  const summary = data.summary || {};
  const hitTrend = data.hitTrend || {};
  const distribution = data.bestMatchDistribution || [];

  setText("bt-total-periods", summary.total_periods);
  setText("bt-cumulative-roi", formatPercent(summary.cumulative_roi));
  setText("bt-hit2", formatPercent(summary.hit2_rate));
  setText("bt-hit3", formatPercent(summary.hit3_rate));
  setText("bt-avg-match", formatScore(summary.avg_best_match));
  setText("bt-losing-streak", summary.max_losing_streak);
  setText("backtest-center-status", `${summary.total_periods || 0} ${t("msg.periods")}`);

  renderLineChart("bt-roi-chart", t("chart.cumulativeRoi"), data.roiTrend || [], "rgba(13, 110, 253, 1)");

  const labels = (hitTrend.hit2 || []).map((row) => row.label);
  renderMultiLineChart("bt-hit-chart", labels, [
    { label: t("label.hit2"), data: (hitTrend.hit2 || []).map((row) => row.value), borderColor: "rgba(25, 135, 84, 1)", backgroundColor: "rgba(25, 135, 84, 0.08)", tension: 0.25 },
    { label: t("label.hit3"), data: (hitTrend.hit3 || []).map((row) => row.value), borderColor: "rgba(255, 193, 7, 1)", backgroundColor: "rgba(255, 193, 7, 0.08)", tension: 0.25 },
    { label: t("label.hit4"), data: (hitTrend.hit4 || []).map((row) => row.value), borderColor: "rgba(220, 53, 69, 1)", backgroundColor: "rgba(220, 53, 69, 0.08)", tension: 0.25 },
  ]);

  renderSimpleBarChart(
    "bt-match-chart",
    t("chart.bestMatch"),
    distribution.map((row) => String(row.match)),
    distribution.map((row) => row.count),
    "rgba(111, 66, 193, 1)"
  );

  renderBacktestRows(data.recentRows || []);
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadBacktestPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);

