function setSettingsHealth(health) {
  setHealth("settings-health-database", health.database);
  setHealth("settings-health-api", health.api);
  setHealth("settings-health-learning", health.learning);
  setHealth("settings-health-dashboard", health.dashboard);
  setHealth("settings-health-prediction", health.prediction);
  setHealth("settings-health-runAll", health.runAll);
  const allOk = Object.values(health).every((item) => item && item.ok);
  setText("settings-health-status", allOk ? t("status.healthy") : t("status.needsAttention"));
}

function loadPreferences() {
  const values = {
    "pref-language": getLanguage(),
    "pref-theme": getThemePreference(),
    "pref-default-page": localStorage.getItem("defaultPage") || "/dashboard",
    "pref-auto-refresh": localStorage.getItem("autoRefresh") || "0",
    "pref-chart-animation": localStorage.getItem("chartAnimation") || "on",
    "pref-compact-mode": localStorage.getItem("compactMode") || "off",
  };
  Object.entries(values).forEach(([id, value]) => {
    const element = byId(id);
    if (element) element.value = value;
  });
}

function bindPreferenceControls() {
  const bind = (id, handler) => {
    const element = byId(id);
    if (element) element.addEventListener("change", () => handler(element.value));
  };
  bind("pref-language", (value) => setLanguage(value));
  bind("pref-theme", (value) => setTheme(value));
  bind("pref-default-page", (value) => setPreference("defaultPage", value));
  bind("pref-auto-refresh", (value) => setPreference("autoRefresh", value));
  bind("pref-chart-animation", (value) => setPreference("chartAnimation", value));
  bind("pref-compact-mode", (value) => setPreference("compactMode", value));
}

async function loadSettingsPage() {
  const data = await fetchJson("/api/system");
  setText("settings-status", t("status.ready"));
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
  loadPreferences();
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadSettingsPage();
  setRunState("Ready", "secondary");
}

bindPreferenceControls();
bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);
