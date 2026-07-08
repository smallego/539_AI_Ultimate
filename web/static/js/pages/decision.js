function renderCurrentPredictions(predictions) {
  const box = byId("decision-current-predictions");
  if (!box) return;

  if (!predictions || predictions.length === 0) {
    box.innerHTML = `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
    return;
  }

  box.innerHTML = predictions.slice(0, 5).map((prediction) => `
    <div class="recommendation">
      <div class="d-flex justify-content-between gap-3 align-items-start flex-wrap">
        <div>
          <span>${t("decision.set")} ${prediction.set_no}</span>
          <strong>${formatNumbers(prediction.numbers)}</strong>
        </div>
        <button class="btn btn-outline-primary btn-sm" type="button" data-explain-id="${prediction.id}" data-i18n="decision.explain">${t("decision.explain")}</button>
      </div>
      <small>
        ${t("decision.final_score")} ${formatScore(prediction.final_score)} |
        ${t("decision.ai_score")} ${formatScore(prediction.ai_score)}
      </small>
    </div>
  `).join("");
}

function renderDecision(data) {
  const badge = byId("decision-recommendation");

  setText("decision-stars", formatStars(data.stars));
  setText("decision-score", data.decisionScore);
  setText("decision-confidence", data.confidence);
  setText("decision-risk", translateValue(data.risk));
  if (badge) {
    badge.innerText = translateValue(data.recommendation);
    badge.className = `badge text-bg-${recommendationTone(data.recommendation)}`;
  }
  setText("decision-recommendation-text", translateValue(data.recommendation));

  const reasons = data.reasons || {};
  byId("decision-reasons").innerHTML = Object.entries(reasons).map(([title, values]) => `
    <div class="decision-reason">
      <span>${translateReasonType(title)}</span>
      <strong>${Array.isArray(values) && values.length ? values.map(translateReasonText).join(" / ") : "-"}</strong>
    </div>
  `).join("");
}

function renderAiSignal(signal) {
  const badge = byId("signal-badge");
  if (badge) {
    badge.className = `badge text-bg-${signal.color || "secondary"}`;
    badge.innerText = translateValue(signal.signal || "-");
  }
  setText("signal-stars", formatStars(signal.stars));
  setText("signal-score", formatScore(signal.score));
  setText("signal-confidence", formatScore(signal.confidence));
  setText("signal-risk", translateValue(signal.risk));
  const reasonBox = byId("signal-reason");
  if (reasonBox) {
    reasonBox.innerHTML = renderSignalReasonItems(signal);
  }
}

async function loadDecisionPage() {
  const [decision, predictions, signal] = await Promise.all([
    fetchJson("/api/decision"),
    fetchJson("/api/predictions/latest"),
    fetchJson("/api/ai-signal"),
  ]);

  renderDecision(decision);
  renderCurrentPredictions(predictions);
  renderAiSignal(signal);
  bindExplainButtons();
  applyTranslations();
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadDecisionPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);
