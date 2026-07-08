const I18N_DEFAULT_LANGUAGE = "zh-TW";
let translations = {};

function getLanguage() {
  return localStorage.getItem("language") || I18N_DEFAULT_LANGUAGE;
}

function setLanguage(lang) {
  localStorage.setItem("language", lang);
  return loadTranslations().then(() => {
    applyTranslations();
    window.dispatchEvent(new CustomEvent("languageChanged", { detail: { language: lang } }));
  });
}

async function loadTranslations() {
  const lang = getLanguage();
  const response = await fetch(`/static/i18n/${lang}.json`);
  translations = response.ok ? await response.json() : {};
  document.documentElement.lang = lang;
  return translations;
}

function t(key) {
  return translations[key] || key;
}

function translateValue(value) {
  if (value === null || value === undefined) return value;
  const text = String(value);
  const normalizedText = text.toLowerCase().replaceAll(" ", "_");
  return translations[`risk.${text}`] ||
    translations[`decision.${text}`] ||
    translations[`signal.${normalizedText}`] ||
    translations[`status.${text.toLowerCase()}`] ||
    translations[`reason.${text}`] ||
    translations[`reason.${normalizedText}`] ||
    text;
}

function translateReasonType(value) {
  return translateValue(value);
}

function translateReasonText(value) {
  if (value === null || value === undefined) return "-";
  const text = String(value);
  if (translations[`reason.${text}`]) return translations[`reason.${text}`];
  const normalizedText = text.toLowerCase().replaceAll(" ", "_");
  if (translations[`reason.${normalizedText}`]) return translations[`reason.${normalizedText}`];

  const recentRoi = text.match(/^Recent ROI\s+(.+)$/);
  if (recentRoi) return `${t("reason.Recent ROI")} ${recentRoi[1]}`;

  const hit2 = text.match(/^Hit2\s+(.+)$/);
  if (hit2) return `${t("reason.Hit2")} ${hit2[1]}`;

  return translateValue(text);
}

function translateSignalReason(value) {
  if (value === null || value === undefined) return { label: "-", value: "" };
  const text = String(value);
  const patterns = [
    [/^decision score\s+(.+)$/i, "signal.decision_score"],
    [/^confidence\s+(.+)$/i, "signal.confidence"],
    [/^Risk\s+(.+)$/, "signal.risk"],
    [/^Strategy\s+(.+)$/, "signal.reason_strategy"],
    [/^Recent ROI\s+(.+)$/, "signal.reason_recent_roi"],
    [/^Recent Hit Rate\s+(.+)$/, "signal.reason_recent_hit_rate"],
    [/^Explain Score\s+(.+)$/, "signal.reason_explain_score"],
    [/^final score\s+(.+)$/i, "signal.reason_final_score"],
  ];
  for (const [regex, key] of patterns) {
    const match = text.match(regex);
    if (match) {
      const raw = match[1];
      const translated = translateValue(raw);
      return { label: t(key), value: translateStrategyName(translated) };
    }
  }
  return { label: t("signal.reason"), value: translateReasonText(text) };
}

function normalizeSignalReasons(reason) {
  if (reason === null || reason === undefined) return [];
  const source = Array.isArray(reason) ? reason : [reason];
  return source.flatMap((item) => String(item)
    .split(/\s+\/\s+/)
    .map((part) => part.trim())
    .filter(Boolean));
}

function signalReasonValue(signal, label) {
  const reasons = normalizeSignalReasons(signal && signal.reason);
  const pattern = new RegExp(`^${label}\\s+(.+)$`, "i");
  const matched = reasons.map((item) => item.match(pattern)).find(Boolean);
  return matched ? matched[1] : undefined;
}

function translateSignalRisk(value) {
  if (value === null || value === undefined || value === "") return "-";
  const text = String(value);
  const key = `signal.${text.toLowerCase()}`;
  return translations[key] || translateValue(text);
}

function renderSignalReasonItems(signal) {
  const decisionScore = signal?.decisionScore ?? signal?.decision_score ?? signalReasonValue(signal, "decision score");
  const confidence = signal?.confidence ?? signalReasonValue(signal, "confidence");
  const risk = signal?.risk ?? signalReasonValue(signal, "risk");
  const items = [
    { label: t("signal.decision_score"), value: decisionScore === undefined || decisionScore === null ? "-" : decisionScore },
    { label: t("signal.confidence"), value: confidence === undefined || confidence === null ? "-" : confidence },
    { label: t("signal.risk"), value: translateSignalRisk(risk) },
  ];

  return `
    <div class="signal-reason-list">
      ${items.map((item) => `
        <div class="signal-reason-row">
          <span>${item.label}</span>
          <strong>${item.value}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function translateStrategyName(value) {
  if (value === null || value === undefined) return "-";
  return translations[`strategy.${value}`] || String(value);
}

function formatTemplate(key, values) {
  return t(key).replace(/\{([^}]+)\}/g, (_, name) => values[name] ?? "");
}

function translateExplainTitle(value) {
  if (value === null || value === undefined) return "-";
  const text = String(value);

  let match = text.match(/^(\d{2}) is hot in the last 30 draws \((\d+) hits\)$/);
  if (match) return formatTemplate("explain.hotPattern", { number: match[1], count: match[2] });

  match = text.match(/^(\d{2}) is cold in the last 30 draws \((\d+) hits\)$/);
  if (match) return formatTemplate("explain.coldPattern", { number: match[1], count: match[2] });

  match = text.match(/^(.+) is the strongest current learning weight \((.+)\)$/);
  if (match) return formatTemplate("explain.learningStrongest", { key: match[1], value: match[2] });

  match = text.match(/^AI score contributes (.+)$/);
  if (match) return formatTemplate("explain.aiContributes", { value: match[1] });

  match = text.match(/^final score normalizes to (.+)$/i);
  if (match) return formatTemplate("explain.finalNormalizes", { value: match[1] });

  const map = {
    "No learning weights available yet": "explain.noLearningWeights",
    "Sum matches the recent average": "explain.sumMatches",
    "Sum is outside the recent average band": "explain.sumOutside",
    "Span matches the recent average": "explain.spanMatches",
    "Span is outside the recent average band": "explain.spanOutside",
    "Recent ROI is improving": "explain.roiImproving",
    "Recent ROI is not improving": "explain.roiNotImproving",
  };
  return map[text] ? t(map[text]) : translateReasonText(text);
}

function translateTimelineStep(value) {
  return translations[`timeline.${value}`] || translateValue(value);
}

function translateTimelineTitle(value) {
  const map = {
    "Prediction set loaded from prediction_history": "timeline.predictionLoaded",
    "AI score and final score normalized": "timeline.decisionNormalized",
    "Latest learning result and weights evaluated": "timeline.learningEvaluated",
    "Recent backtest ROI and hit rate evaluated": "timeline.backtestEvaluated",
    "Reason scores combined into explainable report": "timeline.explainCombined",
  };
  return t(map[value] || value);
}

function translateOptimizerReason(value) {
  if (value === null || value === undefined) return "-";
  const text = String(value);

  let match = text.match(/^ROI normalized to (.+)$/);
  if (match) return formatTemplate("optimizer.roiNormalized", { value: match[1] });

  match = text.match(/^Hit rate contributes (.+)$/);
  if (match) return formatTemplate("optimizer.hitRateContributes", { value: match[1] });

  match = text.match(/^Decision score contributes (.+)$/);
  if (match) return formatTemplate("optimizer.decisionContributes", { value: match[1] });

  match = text.match(/^Explain score contributes (.+)$/);
  if (match) return formatTemplate("optimizer.explainContributes", { value: match[1] });

  match = text.match(/^Risk is (.+)$/);
  if (match) return formatTemplate("optimizer.riskIs", { value: translateValue(match[1]) });

  match = text.match(/^confidence is (.+)$/i);
  if (match) return formatTemplate("optimizer.confidenceIs", { value: match[1] });

  return translateValue(text);
}

function formatStars(value) {
  if (!value) return "\u2606\u2606\u2606\u2606\u2606";
  const text = String(value);
  if (text.includes("*") || text.includes("-")) {
    return text.replaceAll("*", "\u2605").replaceAll("-", "\u2606");
  }
  return text;
}

function applyTranslations(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  root.querySelectorAll("[data-i18n-title]").forEach((element) => {
    element.title = t(element.dataset.i18nTitle);
  });
  root.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
  root.querySelectorAll("[data-language-option]").forEach((element) => {
    element.classList.toggle("active", element.dataset.languageOption === getLanguage());
  });
  if (typeof getThemePreference === "function") {
    root.querySelectorAll("[data-theme-option]").forEach((element) => {
      element.classList.toggle("active", element.dataset.themeOption === getThemePreference());
    });
  }
}

window.i18nReady = loadTranslations().then(() => {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => applyTranslations());
  } else {
    applyTranslations();
  }
});
