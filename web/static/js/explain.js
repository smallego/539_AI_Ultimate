function explainScoreTone(score) {
  if (score >= 75) return "success";
  if (score >= 55) return "primary";
  return "danger";
}

function explainReasonScore(value) {
  const numeric = Number(value || 0);
  const sign = numeric > 0 ? "+" : "";
  return `${sign}${numeric}`;
}

function renderGlobalExplainReport(report) {
  setText("explain-subtitle", `${t("label.set")} ${report.setNo || "-"} | ${formatNumbers(report.numbers)} | ${report.createdAt || "-"}`);
  setText("explain-stars", formatStars(report.stars));
  setText("explain-score", report.decisionScore);
  setText("explain-confidence", formatScore(report.confidence));
  setText("explain-risk", translateValue(report.risk));

  const score = byId("explain-score");
  const scoreBox = score ? score.closest(".decision-score") : null;
  if (scoreBox) {
    scoreBox.classList.remove("score-success", "score-primary", "score-danger");
    scoreBox.classList.add(`score-${explainScoreTone(report.decisionScore)}`);
  }

  const reasons = byId("explain-reasons");
  if (reasons) {
    reasons.innerHTML = (report.reasons || []).map((reason) => `
      <div class="explain-reason">
        <div>
          <span>${translateReasonType(reason.type)}</span>
          <strong>${translateExplainTitle(reason.title)}</strong>
        </div>
        <b class="${Number(reason.score) >= 0 ? "positive" : "negative"}">${explainReasonScore(reason.score)}</b>
      </div>
    `).join("");
  }

  const timeline = byId("explain-timeline");
  if (timeline) {
    timeline.innerHTML = (report.timeline || []).map((item, index) => `
      <div class="timeline-item">
        <span>${index + 1}</span>
        <div><strong>${translateTimelineStep(item.step)}</strong><small>${translateTimelineTitle(item.title)}</small></div>
      </div>
    `).join("");
  }
  applyTranslations(byId("explain-drawer"));
}

async function openExplain(predictionId) {
  if (!predictionId) return;
  setRunState("Running", "primary");
  try {
    const report = await fetchJson(`/api/explain/${predictionId}`);
    renderGlobalExplainReport(report);
    bootstrap.Offcanvas.getOrCreateInstance(byId("explain-drawer")).show();
    setRunState("Ready", "secondary");
  } catch (error) {
    setRunState("Failed", "danger");
    setActionDetail(String(error));
  }
}

function bindExplainButtons(root = document) {
  root.querySelectorAll("[data-explain-id]").forEach((button) => {
    button.addEventListener("click", () => openExplain(button.dataset.explainId));
  });
}
