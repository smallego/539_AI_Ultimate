const EXPORTABLE_PAGES = new Set(["dashboard", "prediction", "decision", "strategy"]);

function currentExportReportType() {
  const page = document.body.dataset.activePage || "dashboard";
  return EXPORTABLE_PAGES.has(page) ? page : "dashboard";
}

function timestampForFilename() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return [
    now.getFullYear(),
    pad(now.getMonth() + 1),
    pad(now.getDate()),
    "_",
    pad(now.getHours()),
    pad(now.getMinutes()),
    pad(now.getSeconds()),
  ].join("");
}

function exportFilename(extension) {
  return `539_AI_Ultimate_Report_${timestampForFilename()}.${extension}`;
}

async function downloadExport(apiUrl, extension, successKey) {
  try {
    const response = await fetch(apiUrl);
    if (!response.ok) throw new Error(`${apiUrl} returned ${response.status}`);
    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = exportFilename(extension);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
    if (window.addAppNotification) {
      addAppNotification("success", t(successKey));
    }
  } catch (error) {
    if (window.addAppNotification) {
      addAppNotification("error", `${t(successKey)} ${t("status.failed")}`);
    }
  }
}

function exportPdf() {
  downloadExport("/api/export/pdf", "pdf", "export.pdf");
}

function exportExcel() {
  downloadExport("/api/export/excel", "xlsx", "export.excel");
}

function bindExportActions() {
  document.querySelectorAll("[data-export-pdf]").forEach((button) => {
    button.addEventListener("click", exportPdf);
  });
  document.querySelectorAll("[data-export-excel]").forEach((button) => {
    button.addEventListener("click", exportExcel);
  });
}
