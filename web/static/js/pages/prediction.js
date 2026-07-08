function formatPrize(value) {
  if (value === null || value === undefined) return t("prediction.waiting");
  const number = Number(value || 0);
  return `$${number.toLocaleString()}`;
}

function analysisStatusText(status) {
  return t(`prediction.${status || "waiting"}`);
}

function drawStatusText(status) {
  return t(`prediction.${status || "waiting_draw"}`);
}

function prizeLevelText(level) {
  return t(`prediction.${level || "none"}`);
}

function formatAnalysisValue(value) {
  return value === null || value === undefined ? t("prediction.waiting") : value;
}

function formatHitRate(value) {
  return value === null || value === undefined ? t("prediction.waiting") : `${Number(value).toFixed(0)}%`;
}

function analysisBadge(row) {
  const tone = row.badge_tone || "secondary";
  return `<span class="badge text-bg-${tone}">${analysisStatusText(row.status)}</span>`;
}

function cardToneClass(row) {
  return `result-card-${row.card_tone || "neutral"}`;
}

function yesNo(value) {
  if (value === null || value === undefined) return t("prediction.waiting_draw");
  return value ? t("prediction.yes") : t("prediction.no");
}

function renderPredictions(predictions) {
  const list = byId("prediction-list");
  list.innerHTML = "";

  if (!predictions || predictions.length === 0) {
    list.innerHTML = `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
    return;
  }

  predictions.forEach((prediction) => {
    const item = document.createElement("div");
    item.className = "recommendation";
    item.innerHTML = `
      <div>
        <span>${t("label.set")} ${prediction.set_no}</span>
        <strong>${formatNumbers(prediction.numbers)}</strong>
      </div>
      <small>
        ${t("prediction.final")} ${formatScore(prediction.final_score)} |
        ${t("label.ai")} ${formatScore(prediction.ai_score)} |
        ${prediction.created_at || prediction.model_version}
      </small>
      <button class="btn btn-outline-primary btn-sm mt-2" data-explain-id="${prediction.id}" data-i18n="label.explain">${t("label.explain")}</button>
    `;
    list.appendChild(item);
  });
}

function renderPredictionAnalysis(analysis) {
  const rows = analysis.rows || [];
  const list = byId("prediction-analysis-list");
  const status = byId("prediction-analysis-status");

  setText("analysis-period", analysis.analysisPeriod || "-");
  setText("analysis-draw-period", analysis.drawPeriod || "-");
  setText("analysis-draw-numbers", analysis.drawNumbers && analysis.drawNumbers.length ? formatNumbers(analysis.drawNumbers) : t("prediction.waiting_draw"));
  setText("analysis-best-match", formatAnalysisValue(analysis.bestMatch));
  setText("analysis-average-hits", formatAnalysisValue(analysis.averageHits));
  setText("analysis-highest-hit-rate", formatHitRate(analysis.highestHitRate));
  setText("analysis-total-prize", analysis.status === "waiting_draw" ? t("prediction.waiting_draw") : formatPrize(analysis.totalPrize));
  setText("analysis-best-set", analysis.bestSet ? `${t("label.set")} ${analysis.bestSet}` : t("prediction.waiting_draw"));
  setText("analysis-has-winner", yesNo(analysis.hasWinner));
  setText("analysis-time", analysis.analysisTime || "-");
  if (status) {
    status.innerText = drawStatusText(analysis.status);
    status.className = `badge text-bg-${analysis.status === "finished" ? "success" : "secondary"}`;
  }

  if (!rows.length) {
    list.innerHTML = `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
    return;
  }

  list.innerHTML = rows.map((row) => `
    <div class="recommendation result-card ${cardToneClass(row)}">
      <div class="result-card-head">
        <span>${t("label.set")} ${row.set_no}</span>
        ${analysisBadge(row)}
      </div>
      <div class="result-number-block">
        <span>${t("prediction.predicted_numbers")}</span>
        <strong>${formatNumbers(row.numbers)}</strong>
      </div>
      <div class="result-number-block">
        <span>${t("prediction.draw_numbers")}</span>
        <strong>${row.draw_numbers && row.draw_numbers.length ? formatNumbers(row.draw_numbers) : t("prediction.waiting_draw")}</strong>
      </div>
      <div class="result-detail-grid">
        <small><span>${t("prediction.hits")}</span><b>⭐ ${formatAnalysisValue(row.hits)} / 5</b></small>
        <small><span>${t("prediction.matched_numbers")}</span><b>${row.matched_numbers && row.matched_numbers.length ? formatNumbers(row.matched_numbers) : formatAnalysisValue(row.hits === null ? null : "-")}</b></small>
        <small><span>${t("prediction.hit_rate")}</span><b>${formatHitRate(row.hit_rate)}</b></small>
        <small><span>${t("prediction.prize_level")}</span><b>${prizeLevelText(row.prize_level)}</b></small>
        <small><span>${t("prediction.prize")}</span><b>${formatPrize(row.prize)}</b></small>
        <small><span>${t("prediction.status")}</span><b>${drawStatusText(row.draw_status)}</b></small>
      </div>
      <button class="btn btn-outline-primary btn-sm mt-2" type="button" data-explain-id="${row.id}" data-i18n="label.explain">${t("label.explain")}</button>
    </div>
  `).join("");
}

function analysisByPredictionId(analysis) {
  const map = {};
  (analysis.rows || []).forEach((row) => {
    if (row.id !== undefined && row.id !== null) map[row.id] = row;
  });
  return map;
}

async function loadPredictionAnalysis() {
  return fetchJson("/api/prediction-analysis");
}

function renderPredictionHistory(rows, analysis) {
  const body = byId("prediction-history");
  const analysisMap = analysisByPredictionId(analysis || {});
  body.innerHTML = "";

  if (!rows || rows.length === 0) {
    body.innerHTML = `<tr><td colspan="11" class="text-muted">${t("msg.noPredictionHistory")}</td></tr>`;
    return;
  }

  rows.forEach((row) => {
    const result = analysisMap[row.id] || {};
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.created_at || "-"}</td>
      <td>${row.set_no}</td>
      <td class="history-numbers">${formatNumbers(row.numbers)}</td>
      <td class="text-end">${result.hits !== undefined ? formatAnalysisValue(result.hits) : "-"}</td>
      <td>${result.matched_numbers && result.matched_numbers.length ? formatNumbers(result.matched_numbers) : "-"}</td>
      <td>${result.prize_level ? prizeLevelText(result.prize_level) : "-"}</td>
      <td class="text-end">${result.prize !== undefined ? formatPrize(result.prize) : "-"}</td>
      <td>${result.status ? analysisStatusText(result.status) : "-"}</td>
      <td class="text-end">${formatScore(row.final_score)}</td>
      <td class="text-end">${formatScore(row.ai_score)}</td>
      <td><button class="btn btn-outline-primary btn-sm" data-explain-id="${row.id}" data-i18n="label.explain">${t("label.explain")}</button></td>
    `;
    body.appendChild(tr);
  });
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

function predictionGridOptions() {
  return {
    color: "rgba(100,116,139,0.12)",
    drawBorder: false,
  };
}

function bucketIndex(value, buckets) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 0;
  const index = buckets.findIndex((bucket) => number >= bucket.min && number < bucket.max);
  return index === -1 ? buckets.length - 1 : index;
}

function scoreValue(row, key = "ai_score") {
  const raw = Number(row[key] ?? row.aiScore ?? 0);
  if (!Number.isFinite(raw)) return 0;
  return key === "final_score" && raw <= 1 ? raw * 100 : raw;
}

function countRows(labels) {
  return labels.map((label) => ({ label, count: 0 }));
}

function buildPredictionPerformanceSummary(performance) {
  const rows = performance.recentRows || [];
  const hitDistribution = countRows(["0", "1", "2", "3", "4", "5"]);
  const prizeBuckets = [
    { label: "$0", min: 0, max: 1 },
    { label: "$50", min: 1, max: 51 },
    { label: "$300", min: 51, max: 301 },
    { label: "$1,000", min: 301, max: 1001 },
    { label: "$20,000", min: 1001, max: 20001 },
    { label: "Jackpot", min: 20001, max: Number.POSITIVE_INFINITY },
  ];
  const prizeDistribution = countRows(prizeBuckets.map((bucket) => bucket.label));
  const scoreBuckets = [
    { label: "0-60", min: 0, max: 60 },
    { label: "60-70", min: 60, max: 70 },
    { label: "70-80", min: 70, max: 80 },
    { label: "80-90", min: 80, max: 90 },
    { label: "90-95", min: 90, max: 95 },
    { label: "95-100", min: 95, max: Number.POSITIVE_INFINITY },
  ];
  const aiScoreDistribution = countRows(scoreBuckets.map((bucket) => bucket.label));
  const scoreBucketAverageHits = scoreBuckets.map((bucket) => ({
    label: bucket.label,
    totalHits: 0,
    count: 0,
    avgHits: 0,
  }));

  rows.forEach((row) => {
    const hits = Math.max(0, Math.min(5, Number(row.hits || 0)));
    hitDistribution[hits].count += 1;
    prizeDistribution[bucketIndex(row.prize || 0, prizeBuckets)].count += 1;
    aiScoreDistribution[bucketIndex(scoreValue(row), scoreBuckets)].count += 1;

    const scoreBucket = scoreBucketAverageHits[bucketIndex(scoreValue(row), scoreBuckets)];
    scoreBucket.totalHits += hits;
    scoreBucket.count += 1;
  });

  scoreBucketAverageHits.forEach((bucket) => {
    bucket.avgHits = bucket.count ? Number((bucket.totalHits / bucket.count).toFixed(2)) : 0;
    delete bucket.totalHits;
  });

  return {
    hitDistribution,
    prizeDistribution,
    aiScoreDistribution,
    scoreBucketAverageHits,
  };
}

function renderDistributionBarChart(id, label, rows, valueKey, color, xLabelKey, yLabelKey) {
  const canvas = byId(id);
  if (!canvas) return;
  const sourceRows = rows || [];
  destroyChart(id);
  charts[id] = new Chart(canvas, {
    type: "bar",
    data: {
      labels: sourceRows.map((row) => row.label),
      datasets: [{
        label,
        data: sourceRows.map((row) => row[valueKey] || 0),
        borderColor: color,
        backgroundColor: color.replace("1)", "0.65)"),
        borderWidth: 1,
        borderRadius: 6,
        maxBarThickness: 34,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: chartAnimationOptions(),
      plugins: {
        legend: { display: false },
        tooltip: {
          ...chartTooltipOptions(),
          callbacks: {
            title(items) {
              const index = items.length ? items[0].dataIndex : -1;
              return sourceRows[index]?.label || "";
            },
            label(context) {
              const row = sourceRows[context.dataIndex] || {};
              if (valueKey === "avgHits") {
                return `${t("prediction.average_hits")}: ${formatScore(row.avgHits)}`;
              }
              return `${t("prediction.record_count")}: ${row.count || 0}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: predictionGridOptions(),
          title: { display: true, text: t(xLabelKey), color: chartTheme().text },
          ticks: { color: chartTheme().muted, autoSkip: false, maxRotation: 0 },
        },
        y: {
          beginAtZero: true,
          grid: predictionGridOptions(),
          title: { display: true, text: t(yLabelKey), color: chartTheme().text },
          ticks: { color: chartTheme().muted, precision: valueKey === "avgHits" ? undefined : 0 },
        },
      },
    },
  });
}

function renderPredictionPerformance(performance) {
  const summary = buildPredictionPerformanceSummary(performance || {});
  renderDistributionBarChart("prediction-hit-distribution", t("prediction.hit_distribution"), summary.hitDistribution, "count", "rgba(25, 135, 84, 1)", "prediction.hit_count", "prediction.record_count");
  renderDistributionBarChart("prediction-prize-distribution", t("prediction.prize_distribution"), summary.prizeDistribution, "count", "rgba(13, 110, 253, 1)", "prediction.prize_bucket", "prediction.record_count");
  renderDistributionBarChart("prediction-ai-score-distribution", t("prediction.ai_score_distribution"), summary.aiScoreDistribution, "count", "rgba(111, 66, 193, 1)", "prediction.score_bucket", "prediction.record_count");
  renderDistributionBarChart("prediction-score-bucket-average-hits", t("prediction.score_bucket_avg_hits"), summary.scoreBucketAverageHits, "avgHits", "rgba(255, 193, 7, 1)", "prediction.score_bucket", "prediction.average_hits");
}

function renderSetPerformance(data) {
  const box = byId("set-performance");
  const rows = data.sets || [];
  box.innerHTML = rows.map((row) => `
    <div class="risk-card">
      <div>
        <span>${t("label.set")} ${row.setNo}</span>
        <strong>${formatPrize(row.totalPrize)}</strong>
        <small>${t("prediction.average_hit")} ${formatScore(row.averageHits)} | ROI ${formatPercent(row.roi)}</small>
      </div>
      <b>${row.bestHit}</b>
    </div>
  `).join("") || `<div class="empty-state">${t("msg.noPredictionHistory")}</div>`;
}

function heatTone(count, max) {
  if (!max || count <= 0) return "heat-0";
  const ratio = count / max;
  if (ratio >= 0.75) return "heat-4";
  if (ratio >= 0.5) return "heat-3";
  if (ratio >= 0.25) return "heat-2";
  return "heat-1";
}

function renderHeatmap(data) {
  const setBox = byId("set-hit-heatmap");
  const numberBox = byId("number-hit-heatmap");
  const setRows = data.setHitCount || [];
  const numberRows = data.numberHitFrequency || [];
  const maxSet = Math.max(...setRows.map((row) => row.count), 0);
  const maxNumber = Math.max(...numberRows.map((row) => row.count), 0);

  setBox.innerHTML = `
    <div class="heat-cell heat-head">Set</div>
    ${[0, 1, 2, 3, 4, 5].map((hit) => `<div class="heat-cell heat-head">${hit}</div>`).join("")}
    ${[1, 2, 3, 4, 5].map((setNo) => `
      <div class="heat-cell heat-head">${t("label.set")} ${setNo}</div>
      ${[0, 1, 2, 3, 4, 5].map((hit) => {
        const row = setRows.find((item) => item.setNo === setNo && item.hits === hit) || { count: 0 };
        return `<div class="heat-cell ${heatTone(row.count, maxSet)}">${row.count}</div>`;
      }).join("")}
    `).join("")}
  `;

  numberBox.innerHTML = numberRows.map((row) => `
    <div class="number-heat-cell ${heatTone(row.count, maxNumber)}">
      <strong>${String(row.number).padStart(2, "0")}</strong>
      <span>${row.count}</span>
    </div>
  `).join("");
}

async function loadPredictionPage() {
  const [status, dashboard, latest, history, analysis, performance, setPerformance, heatmap, signal] = await Promise.all([
    fetchJson("/api/status"),
    fetchJson("/api/dashboard-data"),
    fetchJson("/api/predictions/latest"),
    fetchJson("/api/predictions/history"),
    loadPredictionAnalysis(),
    fetchJson("/api/prediction-performance"),
    fetchJson("/api/set-performance"),
    fetchJson("/api/hit-heatmap"),
    fetchJson("/api/ai-signal"),
  ]);

  const latestDraw = dashboard.latestDraw || {};
  setText("db-status", status.database_exists ? t("status.ready") : t("status.noDatabase"));
  setText("latest-draw-no", latestDraw.drawNo);
  setText("latest-draw-date", latestDraw.drawDate);
  setText("latest-draw-numbers", formatNumbers(latestDraw.numbers));
  renderPredictionAnalysis(analysis);
  renderPredictions(latest);
  renderPredictionHistory(history, analysis);
  renderPredictionPerformance(performance);
  renderSetPerformance(setPerformance);
  renderHeatmap(heatmap);
  renderAiSignal(signal);
  bindExplainButtons();
  applyTranslations();
}

async function refreshPage() {
  setRunState("Refreshing", "secondary");
  await loadPredictionPage();
  setRunState("Ready", "secondary");
}

bindRefresh(refreshPage);
window.i18nReady.then(refreshPage);
