async function loadDataPage() {
  const data = await fetchJson("/api/dashboard-data");
  const latest = data.latestDraw || {};

  setText("data-status", `${(data.recentDraws || []).length} ${t("msg.draws")}`);
  setText("data-latest-draw-no", latest.drawNo);
  setText("data-latest-draw-date", latest.drawDate);
  setText("data-latest-draw-numbers", formatNumbers(latest.numbers));
  setText("data-database-count", data.databaseCount);
  setText("data-window-count", (data.recentDraws || []).length);

  renderDualAxisTrendChart("data-trend-chart", data.sumTrend || [], data.spanTrend || []);
  renderBarChart("data-hot-chart", t("chart.hotCount"), data.hot, "rgba(13, 110, 253, 1)");
  renderBarChart("data-cold-chart", t("chart.coldCount"), data.cold, "rgba(108, 117, 125, 1)");
  renderPieChart("data-odd-even-chart", [t("chart.odd"), t("chart.even")], [data.oddEven.odd, data.oddEven.even], ["#0d6efd", "#20c997"]);
  renderPieChart("data-low-high-chart", [t("chart.low"), t("chart.high")], [data.lowHigh.low, data.lowHigh.high], ["#6f42c1", "#fd7e14"]);
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadDataPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);

