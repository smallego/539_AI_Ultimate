const charts = {};
let CHART_GRID_COLOR = "rgba(100, 116, 139, 0.15)";
const LINE_DATASET_DEFAULTS = {
  borderWidth: 2,
  pointRadius: 2,
  pointHoverRadius: 5,
  tension: 0.35,
  spanGaps: true,
};
const STATUS_KEYS = {
  Ready: "status.ready",
  Running: "status.running",
  Completed: "status.completed",
  Failed: "status.failed",
  Error: "status.failed",
  Refreshing: "status.running",
  Explaining: "status.running",
};

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const element = byId(id);
  if (element) element.innerText = value ?? "-";
}

function setRunState(text, tone = "secondary") {
  const translated = t(STATUS_KEYS[text] || text);
  const state = byId("run-state");
  if (state) {
    state.className = `badge text-bg-${tone}`;
    state.innerText = translated;
  }

  const sidebarState = byId("action-state");
  if (sidebarState) {
    sidebarState.className = `badge text-bg-${tone}`;
    sidebarState.innerText = translated;
  }
}

function preference(key, fallback = "") {
  return localStorage.getItem(key) || fallback;
}

function setPreference(key, value) {
  localStorage.setItem(key, value);
  window.dispatchEvent(new CustomEvent("preferenceChanged", { detail: { key, value } }));
}

function chartTheme() {
  const dark = document.documentElement.dataset.theme === "dark";
  CHART_GRID_COLOR = dark ? "rgba(148, 163, 184, 0.18)" : "#ececec";
  return {
    text: dark ? "#dce7f5" : "#172033",
    muted: dark ? "#94a3b8" : "#6b778c",
    tooltipBg: dark ? "#0f172a" : "#ffffff",
    tooltipText: dark ? "#f8fafc" : "#172033",
  };
}

function chartAnimationOptions() {
  return preference("chartAnimation", "on") === "off" ? false : { duration: 300 };
}

function setActionDetail(text) {
  setText("action-detail", text);
}

function setActionButtonsDisabled(disabled) {
  document.querySelectorAll(".sidebar-action").forEach((button) => {
    button.disabled = disabled;
  });
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

function formatNumbers(numbers) {
  if (!numbers || numbers.length === 0) return "-";
  return numbers.map((number) => String(number).padStart(2, "0")).join(" ");
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toFixed(4).replace(/\.?0+$/, "");
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  return `${Number(value).toFixed(2)}%`;
}

function translateSystemHealthLabel(value) {
  if (value === null || value === undefined || value === "") return "-";
  const text = String(value);
  const countMatch = text.match(/^(\d+)\s+(draws|runs|rows)$/i);
  if (countMatch) {
    const unitKey = {
      draws: "msg.draws",
      runs: "msg.runs",
      rows: "msg.rows",
    }[countMatch[2].toLowerCase()];
    return `${countMatch[1]} ${t(unitKey)}`;
  }
  return translateValue(text);
}

function setHealth(id, item) {
  const box = byId(id);
  if (!box) return;
  box.classList.toggle("ok", Boolean(item && item.ok));
  box.classList.toggle("warn", !Boolean(item && item.ok));
  const label = box.querySelector("strong");
  if (label) label.innerText = item ? translateSystemHealthLabel(item.label) : "-";
}

function destroyChart(id) {
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }
}

function chartLabels(rows, key = "number") {
  return rows.map((row) => String(row[key]).padStart(2, "0"));
}

function chartValues(rows, key = "count") {
  return rows.map((row) => row[key]);
}

function chartGridOptions() {
  return {
    color: CHART_GRID_COLOR,
    drawBorder: false,
  };
}

function chartXAxisOptions() {
  return {
    grid: chartGridOptions(),
    ticks: {
      autoSkip: true,
      maxTicksLimit: 6,
    },
  };
}

function lineDataset(dataset) {
  return {
    ...LINE_DATASET_DEFAULTS,
    fill: dataset.fill ?? false,
    ...dataset,
    ...LINE_DATASET_DEFAULTS,
  };
}

function trendTooltipLabel(context) {
  const label = context.dataset.label || "";
  const value = context.parsed.y ?? context.raw ?? "-";
  return `${label}: ${value}`;
}

function chartTooltipOptions() {
  const theme = chartTheme();
  return {
    backgroundColor: theme.tooltipBg,
    titleColor: theme.tooltipText,
    bodyColor: theme.tooltipText,
    borderColor: CHART_GRID_COLOR,
    borderWidth: 1,
    padding: 10,
    callbacks: {
      title(items) {
        return items.length ? items[0].label : "";
      },
      label: trendTooltipLabel,
    },
  };
}

function renderBarChart(id, label, rows, color) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: chartLabels(rows || []),
      datasets: [{
        label,
        data: chartValues(rows || []),
        borderColor: color,
        backgroundColor: color.replace("1)", "0.72)"),
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: chartAnimationOptions(),
      plugins: { legend: { display: false, labels: { color: chartTheme().text } }, tooltip: chartTooltipOptions() },
      scales: {
        x: chartXAxisOptions(),
        y: { beginAtZero: true, grid: chartGridOptions(), ticks: { precision: 0 } },
      },
    },
  });
}

function renderSimpleBarChart(id, label, labels, values, color) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label,
        data: values,
        borderColor: color,
        backgroundColor: color.replace("1)", "0.72)"),
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: chartAnimationOptions(),
      plugins: { legend: { display: false, labels: { color: chartTheme().text } }, tooltip: chartTooltipOptions() },
      scales: {
        x: chartXAxisOptions(),
        y: { beginAtZero: true, grid: chartGridOptions(), ticks: { precision: 0 } },
      },
    },
  });
}

function renderLineChart(id, label, rows, color) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "line",
    data: {
      labels: (rows || []).map((row) => row.label),
      datasets: [lineDataset({
        label,
        data: (rows || []).map((row) => row.value),
        borderColor: color,
        backgroundColor: color.replace("1)", "0.12)"),
        fill: true,
      })],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false, position: "top", labels: { usePointStyle: true, boxWidth: 8, color: chartTheme().text } },
        tooltip: chartTooltipOptions(),
      },
      animation: chartAnimationOptions(),
      scales: {
        x: chartXAxisOptions(),
        y: { beginAtZero: false, grid: chartGridOptions() },
      },
    },
  });
}

function renderDualAxisTrendChart(id, sumRows, spanRows) {
  const canvas = byId(id);
  if (!canvas) return;
  const labels = (sumRows || []).map((row) => row.label);
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        lineDataset({
          label: t("chart.sum"),
          data: (sumRows || []).map((row) => row.value),
          borderColor: "rgba(25, 135, 84, 1)",
          backgroundColor: "rgba(25, 135, 84, 0.08)",
          yAxisID: "y",
        }),
        lineDataset({
          label: t("chart.span"),
          data: (spanRows || []).map((row) => row.value),
          borderColor: "rgba(255, 193, 7, 1)",
          backgroundColor: "rgba(255, 193, 7, 0.08)",
          yAxisID: "y1",
        }),
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8, color: chartTheme().text } },
        tooltip: chartTooltipOptions(),
      },
      animation: chartAnimationOptions(),
      scales: {
        x: chartXAxisOptions(),
        y: {
          type: "linear",
          position: "left",
          title: { display: true, text: t("chart.sum"), color: chartTheme().text },
          grid: chartGridOptions(),
        },
        y1: {
          type: "linear",
          position: "right",
          title: { display: true, text: t("chart.span"), color: chartTheme().text },
          grid: { drawOnChartArea: false, color: CHART_GRID_COLOR, drawBorder: false },
        },
      },
    },
  });
}

function renderPieChart(id, labels, values, colors) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderColor: "#ffffff", borderWidth: 2 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "58%",
      animation: chartAnimationOptions(),
      plugins: { legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8, color: chartTheme().text } }, tooltip: chartTooltipOptions() },
    },
  });
}

function renderMultiLineChart(id, labels, datasets) {
  const canvas = byId(id);
  if (!canvas) return;
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "line",
    data: { labels, datasets: datasets.map(lineDataset) },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top", labels: { usePointStyle: true, boxWidth: 8, color: chartTheme().text } },
        tooltip: chartTooltipOptions(),
      },
      animation: chartAnimationOptions(),
      scales: {
        x: chartXAxisOptions(),
        y: { beginAtZero: false, grid: chartGridOptions() },
      },
    },
  });
}

function recommendationTone(recommendation) {
  if (recommendation === "Strong Buy") return "success";
  if (recommendation === "Buy") return "primary";
  if (recommendation === "Neutral") return "secondary";
  return "danger";
}

async function executeAction(url, afterRun) {
  const output = byId("output");
  setRunState("Running", "primary");
    if (output) output.innerText = `${t("status.running")}...\n`;

  try {
    const response = await fetch(url, { method: "POST" });
    const data = await response.json();
    const lines = [
      `OK: ${data.ok}`,
      `Return Code: ${data.returncode}`,
      "",
      data.stdout ? `===== STDOUT =====\n${data.stdout}` : "",
      data.stderr ? `===== STDERR =====\n${data.stderr}` : "",
    ].filter(Boolean);

    if (output) output.innerText = lines.join("\n");
    setRunState(data.ok ? "Completed" : "Failed", data.ok ? "success" : "danger");
    if (window.addAppNotification) {
      addAppNotification(data.ok ? "success" : "error", `${url} ${data.ok ? t("status.completed") : t("status.failed")}`);
    }
    if (typeof afterRun === "function") await afterRun();
  } catch (error) {
    if (output) output.innerText = String(error);
    setRunState("Error", "danger");
  }
}

function wireActions(afterRun) {
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => runAction(button.innerText || t("action.center"), button.dataset.action, afterRun));
  });
}

async function refreshCurrentPage() {
  setRunState("Running", "primary");
  setActionDetail(t("msg.refreshing"));
  setActionButtonsDisabled(true);

  try {
    if (typeof window.refreshPage === "function") {
      await window.refreshPage();
    } else if (typeof refreshPage === "function") {
      await refreshPage();
    } else {
      window.location.reload();
      return;
    }
    setRunState("Completed", "success");
    setActionDetail(t("msg.refreshed"));
  } catch (error) {
    setRunState("Failed", "danger");
    setActionDetail(String(error));
  } finally {
    setActionButtonsDisabled(false);
  }
}

async function runAction(actionName, apiUrl, afterRun) {
  setRunState("Running", "primary");
  setActionDetail(`${actionName} ${t("status.running")}...`);
  setActionButtonsDisabled(true);

  try {
    const response = await fetch(apiUrl, { method: "POST" });
    const data = await response.json();
    const ok = response.ok && data.ok !== false;

    setRunState(ok ? "Completed" : "Failed", ok ? "success" : "danger");
    setActionDetail(`${actionName} ${ok ? t("status.completed") : t("status.failed")}${data.returncode !== undefined ? ` (${t("label.returnCode")} ${data.returncode})` : ""}.`);
    if (window.addAppNotification) {
      addAppNotification(ok ? "success" : "error", `${actionName} ${ok ? t("status.completed") : t("status.failed")}`);
    }

    if (typeof afterRun === "function") {
      await afterRun();
    } else {
      await refreshCurrentPage();
    }
    return data;
  } catch (error) {
    setRunState("Failed", "danger");
    setActionDetail(String(error));
    if (window.addAppNotification) addAppNotification("error", `${actionName} ${t("status.failed")}`);
    return null;
  } finally {
    setActionButtonsDisabled(false);
  }
}

function bindSidebarActions() {
  document.querySelectorAll("[data-global-action]").forEach((button) => {
    button.addEventListener("click", () => runAction(button.innerText.trim(), button.dataset.apiUrl));
  });

  document.querySelectorAll("[data-refresh-current]").forEach((button) => {
    button.addEventListener("click", refreshCurrentPage);
  });
}

function bindLanguageSwitcher() {
  document.querySelectorAll("[data-language-option]").forEach((button) => {
    button.addEventListener("click", () => setLanguage(button.dataset.languageOption));
  });
}

function bindSidebarToggle() {
  const sidebar = byId("sidebar");
  const toggle = byId("sidebar-toggle");
  const backdrop = byId("mobile-backdrop");
  if (!sidebar || !toggle || !backdrop) return;
  const close = () => document.body.classList.remove("sidebar-open");
  toggle.addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
  backdrop.addEventListener("click", close);
  sidebar.querySelectorAll(".nav-link").forEach((link) => link.addEventListener("click", close));
}

function autoRefreshAllowed() {
  return ["dashboard", "prediction", "decision"].includes(document.body.dataset.activePage);
}

function setupAutoRefresh() {
  let timer = null;
  const start = () => {
    if (timer) clearInterval(timer);
    const seconds = Number(preference("autoRefresh", "0"));
    if (!seconds || !autoRefreshAllowed()) return;
    timer = setInterval(() => {
      if (typeof window.refreshPage === "function") window.refreshPage();
    }, seconds * 1000);
  };
  start();
  window.addEventListener("preferenceChanged", (event) => {
    if (event.detail.key === "autoRefresh") start();
  });
}

function bindKeyboardShortcuts() {
  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
    if (event.key === "?") {
      bootstrap.Modal.getOrCreateInstance(byId("shortcut-help-modal")).show();
      return;
    }
    if (!event.ctrlKey) return;
    const key = event.key.toLowerCase();
    const actions = {
      r: [t("action.runAll"), "/api/run-all"],
      p: [t("action.predict"), "/api/predict"],
      u: [t("action.update"), "/api/update"],
      b: [t("action.backtest"), "/api/backtest"],
    };
    if (actions[key]) {
      event.preventDefault();
      runAction(actions[key][0], actions[key][1]);
    }
  });
}

function signalReasonParts(reason) {
  if (reason === null || reason === undefined) return [];
  const source = Array.isArray(reason) ? reason : [reason];
  return source.flatMap((item) => String(item)
    .split(/\s+\/\s+/)
    .map((part) => part.trim())
    .filter(Boolean));
}

function signalReasonPartValue(signal, label) {
  const parts = signalReasonParts(signal && signal.reason);
  const pattern = new RegExp(`^${label}\\s+(.+)$`, "i");
  const matched = parts.map((part) => part.match(pattern)).find(Boolean);
  return matched ? matched[1] : undefined;
}

function formatSignalReasonNumber(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : value;
}

function renderSignalReasonItems(signal) {
  const decisionScore = signal?.decisionScore ?? signal?.decision_score ?? signalReasonPartValue(signal, "decision score");
  const confidence = signal?.confidence ?? signalReasonPartValue(signal, "confidence");
  const risk = signal?.risk ?? signalReasonPartValue(signal, "risk");
  const rows = [
    { label: t("signal.decision_score"), value: formatSignalReasonNumber(decisionScore) },
    { label: t("signal.confidence"), value: formatSignalReasonNumber(confidence) },
    { label: t("signal.risk"), value: translateValue(risk || "-") },
  ];

  return `
    <div class="signal-reason-list">
      ${rows.map((row) => `
        <div class="signal-reason-row">
          <span>${row.label}</span>
          <strong>${row.value}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function applyCompactMode() {
  document.body.classList.toggle("compact-mode", preference("compactMode", "off") === "on");
}

async function loadFooterVersion() {
  try {
    const data = await fetchJson("/api/system");
    setText("footer-version", `${t("label.version")} ${data.version} | ${data.gitBranch} ${data.gitCommit}`);
  } catch (error) {
    setText("footer-version", t("msg.versionUnavailable"));
  }
}

function bindRefresh(refreshFn) {
  window.refreshPage = refreshFn;
  const button = byId("refresh-btn");
  if (button && typeof refreshFn === "function") button.addEventListener("click", refreshFn);
  window.addEventListener("languageChanged", () => {
    applyTranslations();
    if (typeof refreshFn === "function") refreshFn();
  });
}

window.i18nReady.then(() => {
  loadFooterVersion();
  bindSidebarActions();
  bindLanguageSwitcher();
  bindThemeSwitcher();
  bindSidebarToggle();
  bindExportActions();
  bindKeyboardShortcuts();
  bindNotificationActions();
  setupAutoRefresh();
  applyCompactMode();
  renderNotifications();
  setRunState("Ready", "secondary");
});

window.addEventListener("themeChanged", () => {
  Object.keys(charts).forEach((id) => destroyChart(id));
  if (typeof window.refreshPage === "function") window.refreshPage();
});

window.addEventListener("preferenceChanged", (event) => {
  if (event.detail.key === "compactMode") applyCompactMode();
  if (event.detail.key === "chartAnimation" && typeof window.refreshPage === "function") window.refreshPage();
});
