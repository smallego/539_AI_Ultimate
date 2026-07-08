const NOTIFICATION_STORAGE_KEY = "notifications";
const NOTIFICATION_LIMIT = 20;

function notificationTitle(type) {
  return t(type === "error" ? "notification.error" : "notification.success");
}

function normalizeNotification(item) {
  const type = item.type || "success";
  return {
    id: item.id || `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    title: item.title || notificationTitle(type),
    message: item.message || "",
    type,
    createdAt: item.createdAt || item.time || new Date().toLocaleString(),
    read: Boolean(item.read),
  };
}

function readNotifications() {
  try {
    const items = JSON.parse(localStorage.getItem(NOTIFICATION_STORAGE_KEY) || "[]");
    return Array.isArray(items) ? items.map(normalizeNotification) : [];
  } catch (error) {
    return [];
  }
}

function writeNotifications(items) {
  localStorage.setItem(
    NOTIFICATION_STORAGE_KEY,
    JSON.stringify(items.map(normalizeNotification).slice(0, NOTIFICATION_LIMIT))
  );
}

function addNotification(type, message, title) {
  const item = normalizeNotification({
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    title: title || notificationTitle(type),
    message,
    type,
    createdAt: new Date().toLocaleString(),
    read: false,
  });
  writeNotifications([item, ...readNotifications()]);
  renderNotifications();
}

function unreadNotificationCount(items) {
  return items.filter((item) => !item.read).length;
}

function markNotificationRead(id) {
  writeNotifications(readNotifications().map((item) => (
    String(item.id) === String(id) ? { ...item, read: true } : item
  )));
  renderNotifications();
}

function deleteNotification(id) {
  writeNotifications(readNotifications().filter((item) => String(item.id) !== String(id)));
  renderNotifications();
}

function markAllNotificationsRead() {
  writeNotifications(readNotifications().map((item) => ({ ...item, read: true })));
  renderNotifications();
}

function clearAllNotifications() {
  localStorage.removeItem(NOTIFICATION_STORAGE_KEY);
  renderNotifications();
}

function notificationTone(type) {
  if (type === "error") return "error";
  if (type === "success") return "success";
  return "info";
}

function renderNotifications() {
  const list = byId("notification-list");
  const count = byId("notification-count");
  const unreadLabel = byId("notification-unread-label");
  if (!list || !count) return;

  const items = readNotifications();
  const unread = unreadNotificationCount(items);
  count.textContent = unread;
  count.classList.toggle("d-none", unread === 0);
  if (unreadLabel) {
    unreadLabel.textContent = unread > 0 ? `${unread} ${t("notification.unread")}` : "";
  }

  list.innerHTML = items.length ? items.map((item) => `
    <div class="notification-item ${notificationTone(item.type)} ${item.read ? "is-read" : "is-unread"}">
      <div class="notification-item-main">
        <strong>${item.title || notificationTitle(item.type)}</strong>
        <span>${item.message}</span>
        <small>${item.createdAt}</small>
      </div>
      <div class="notification-item-actions">
        <button class="btn btn-link btn-sm" type="button" data-notification-read="${item.id}" ${item.read ? "disabled" : ""}>${t("notification.mark_read")}</button>
        <button class="btn btn-link btn-sm text-danger" type="button" data-notification-delete="${item.id}">${t("notification.delete")}</button>
      </div>
    </div>
  `).join("") : `<div class="notification-empty">${t("notification.empty")}</div>`;

  list.querySelectorAll("[data-notification-read]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      markNotificationRead(button.dataset.notificationRead);
    });
  });
  list.querySelectorAll("[data-notification-delete]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteNotification(button.dataset.notificationDelete);
    });
  });
}

function bindNotificationActions() {
  const markAll = byId("notification-mark-all-read");
  const clearAll = byId("notification-clear-all");
  if (markAll) markAll.addEventListener("click", (event) => {
    event.stopPropagation();
    markAllNotificationsRead();
  });
  if (clearAll) clearAll.addEventListener("click", (event) => {
    event.stopPropagation();
    clearAllNotifications();
  });
}

window.addAppNotification = addNotification;
window.renderNotifications = renderNotifications;
window.bindNotificationActions = bindNotificationActions;
