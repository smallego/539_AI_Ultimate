async function loadDataPage() {
  const data = await fetchJson("/api/dashboard-data");
  const latest = data.latestDraw || {};

  setText("data-status", `${(data.recentDraws || []).length} draws`);
  setText("data-latest-draw-no", latest.drawNo);
  setText("data-latest-draw-date", latest.drawDate);
  setText("data-latest-draw-numbers", formatNumbers(latest.numbers));
  setText("data-database-count", data.databaseCount);
  setText("data-window-count", (data.recentDraws || []).length);

  const labels = (data.sumTrend || []).map((row) => row.label);
  renderMultiLineChart("data-trend-chart", labels, [
    { label: "Sum", data: (data.sumTrend || []).map((row) => row.value), borderColor: "rgba(25, 135, 84, 1)", backgroundColor: "rgba(25, 135, 84, 0.08)", tension: 0.25 },
    { label: "Span", data: (data.spanTrend || []).map((row) => row.value), borderColor: "rgba(255, 193, 7, 1)", backgroundColor: "rgba(255, 193, 7, 0.08)", tension: 0.25 },
  ]);
  renderBarChart("data-hot-chart", "Hot Count", data.hot, "rgba(13, 110, 253, 1)");
  renderBarChart("data-cold-chart", "Cold Count", data.cold, "rgba(108, 117, 125, 1)");
  renderPieChart("data-odd-even-chart", ["Odd", "Even"], [data.oddEven.odd, data.oddEven.even], ["#0d6efd", "#20c997"]);
  renderPieChart("data-low-high-chart", ["Low 1-19", "High 20-39"], [data.lowHigh.low, data.lowHigh.high], ["#6f42c1", "#fd7e14"]);
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadDataPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
refreshPage();
