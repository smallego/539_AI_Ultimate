function renderLearningWeights(weights) {
  const box = byId("learning-weights");
  const entries = Object.entries(weights || {});
  if (entries.length === 0) {
    box.innerHTML = '<div class="empty-state">No model weights yet.</div>';
    return;
  }

  box.innerHTML = entries.map(([key, value]) => `
    <div class="weight-chip">
      <span>${key}</span>
      <strong>${Number(value).toFixed(4)}</strong>
    </div>
  `).join("");
}

async function loadLearningPage() {
  const [latest, history, weights] = await Promise.all([
    fetchJson("/api/learning/latest"),
    fetchJson("/api/learning/history"),
    fetchJson("/api/learning/weights"),
  ]);
  const chronological = [...history].reverse();

  setText("learning-model", latest.model_version || "-");
  setText("learning-roi", formatPercent(latest.roi));
  setText("learning-hit2", formatPercent(latest.hit2));
  setText("learning-hit3", formatPercent(latest.hit3));
  setText("learning-hit4", formatPercent(latest.hit4));
  setText("learning-avg", formatScore(latest.avg_match));
  setText("learning-time", latest.created_at || "No learning yet");

  renderLearningWeights(weights.current || latest.weights || {});

  renderLineChart(
    "learning-roi-chart",
    "ROI",
    chronological.map((row) => ({ label: row.created_at, value: row.roi })),
    "rgba(13, 110, 253, 1)"
  );

  const labels = chronological.map((row) => row.created_at);
  renderMultiLineChart("learning-hit-chart", labels, [
    { label: "Hit 2+", data: chronological.map((row) => row.hit2), borderColor: "rgba(25, 135, 84, 1)", backgroundColor: "rgba(25, 135, 84, 0.08)", tension: 0.25 },
    { label: "Hit 3+", data: chronological.map((row) => row.hit3), borderColor: "rgba(255, 193, 7, 1)", backgroundColor: "rgba(255, 193, 7, 0.08)", tension: 0.25 },
    { label: "Hit 4+", data: chronological.map((row) => row.hit4), borderColor: "rgba(220, 53, 69, 1)", backgroundColor: "rgba(220, 53, 69, 0.08)", tension: 0.25 },
  ]);

  const weightHistory = weights.history || [];
  const weightLabels = weightHistory.map((row) => row.created_at);
  const weightKeys = Array.from(new Set(weightHistory.flatMap((row) => Object.keys(row.weights || {}))));
  const colors = [
    "rgba(13, 110, 253, 1)",
    "rgba(32, 201, 151, 1)",
    "rgba(255, 193, 7, 1)",
    "rgba(111, 66, 193, 1)",
    "rgba(253, 126, 20, 1)",
  ];

  renderMultiLineChart(
    "learning-weight-chart",
    weightLabels,
    weightKeys.map((key, index) => ({
      label: key,
      data: weightHistory.map((row) => (row.weights || {})[key]),
      borderColor: colors[index % colors.length],
      backgroundColor: colors[index % colors.length].replace("1)", "0.08)"),
      tension: 0.25,
    }))
  );
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadLearningPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
refreshPage();
