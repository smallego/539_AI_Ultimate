async function loadDecisionPage() {
  const data = await fetchJson("/api/decision");
  const badge = byId("decision-recommendation");

  setText("decision-stars", data.stars);
  setText("decision-score", data.decisionScore);
  setText("decision-confidence", data.confidence);
  setText("decision-risk", data.risk);
  if (badge) {
    badge.innerText = data.recommendation;
    badge.className = `badge text-bg-${recommendationTone(data.recommendation)}`;
  }

  const reasons = data.reasons || {};
  byId("decision-reasons").innerHTML = Object.entries(reasons).map(([title, values]) => `
    <div class="decision-reason">
      <span>${title}</span>
      <strong>${Array.isArray(values) && values.length ? values.join(" / ") : "-"}</strong>
    </div>
  `).join("");
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadDecisionPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
refreshPage();
