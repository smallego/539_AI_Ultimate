function setSettingsHealth(health) {
  setHealth("settings-health-database", health.database);
  setHealth("settings-health-api", health.api);
  setHealth("settings-health-learning", health.learning);
  setHealth("settings-health-dashboard", health.dashboard);
  setHealth("settings-health-prediction", health.prediction);
  setHealth("settings-health-runAll", health.runAll);
  const allOk = Object.values(health).every((item) => item && item.ok);
  setText("settings-health-status", allOk ? "Healthy" : "Needs Attention");
}

async function loadSettingsPage() {
  const data = await fetchJson("/api/system");
  setText("settings-status", "Ready");
  setText("settings-version", data.version);
  setText("settings-model", data.modelVersion);
  setText("settings-build-time", data.buildTime);
  setText("settings-git-branch", data.gitBranch);
  setText("settings-git-commit", data.gitCommit);
  setText("settings-dashboard-time", data.dashboardTime || "-");
  setText("settings-database-count", data.databaseCount);
  setText("settings-prediction-count", data.predictionCount);
  setText("settings-learning-count", data.learningCount);
  setSettingsHealth(data.health || {});
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadSettingsPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
refreshPage();
