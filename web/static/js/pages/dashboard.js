async function loadDashboardStatus() {
  const [system, status, data, performance] = await Promise.all([
    fetchJson("/api/system"),
    fetchJson("/api/status"),
    fetchJson("/api/dashboard-data"),
    fetchJson("/api/performance"),
  ]);

  const health = system.health || {};
  setHealth("health-database", health.database);
  setHealth("health-api", health.api);
  setHealth("health-learning", health.learning);
  setHealth("health-dashboard", health.dashboard);
  setHealth("health-prediction", health.prediction);
  setHealth("health-runAll", health.runAll);

  const allOk = Object.values(health).every((item) => item && item.ok);
  setText("system-health-status", allOk ? "Healthy" : "Needs Attention");
  setText("draw-count", data.databaseCount);
  setText("prediction-count", status.prediction_count);
  setText("data-window-count", data.recentDraws ? data.recentDraws.length : 0);
  setText("dashboard-status", status.dashboard_exists ? "Ready" : "Missing");
  setText("data-window-status", `${(data.sumTrend || []).length} draws`);

  renderLineChart("sum-trend-chart", "Sum", data.sumTrend, "rgba(25, 135, 84, 1)");
  renderBarChart("hot-chart", "Hot Count", data.hot, "rgba(13, 110, 253, 1)");
  renderBarChart("cold-chart", "Cold Count", data.cold, "rgba(108, 117, 125, 1)");
  renderPieChart("odd-even-chart", ["Odd", "Even"], [data.oddEven.odd, data.oddEven.even], ["#0d6efd", "#20c997"]);
  renderPieChart("low-high-chart", ["Low 1-19", "High 20-39"], [data.lowHigh.low, data.lowHigh.high], ["#6f42c1", "#fd7e14"]);
  renderPerformance(performance);
}

function renderPerformance(performance) {
  setText("performance-status", `${performance.recentApiCount || 0} requests`);
  setText("perf-average-api", `${performance.averageApiTime || 0} ms`);
  setText("perf-cache-hit", performance.cacheHit || 0);
  setText("perf-cache-miss", performance.cacheMiss || 0);
  setText("perf-cache-rate", `${performance.cacheHitRate || 0}%`);
  setText("perf-memory", performance.memory && performance.memory.available ? `${performance.memory.rssMb} MB` : "Unavailable");
  setText("perf-cpu", performance.cpu && performance.cpu.available ? `${performance.cpu.percent}%` : "Unavailable");

  const body = byId("performance-recent");
  const rows = (performance.recentApi || []).slice().reverse();
  if (!rows.length) {
    body.innerHTML = '<tr><td colspan="5" class="text-muted">No API samples yet.</td></tr>';
    return;
  }

  body.innerHTML = rows.map((row) => `
    <tr>
      <td>${row.timestamp || "-"}</td>
      <td>${row.method || "-"}</td>
      <td>${row.path || "-"}</td>
      <td class="text-end">${row.durationMs} ms</td>
      <td>${row.success ? "Success" : "Fail"}</td>
    </tr>
  `).join("");
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadDashboardStatus();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
refreshPage();
