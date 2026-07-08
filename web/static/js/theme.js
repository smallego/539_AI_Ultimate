const THEME_STORAGE_KEY = "theme";
const prefersDarkQuery = window.matchMedia("(prefers-color-scheme: dark)");

function getThemePreference() {
  return localStorage.getItem(THEME_STORAGE_KEY) || "auto";
}

function getResolvedTheme(theme = getThemePreference()) {
  if (theme === "auto") return prefersDarkQuery.matches ? "dark" : "light";
  return theme;
}

function applyTheme(theme = getThemePreference()) {
  const resolved = getResolvedTheme(theme);
  document.documentElement.dataset.theme = resolved;
  document.documentElement.dataset.themePreference = theme;
  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    button.classList.toggle("active", button.dataset.themeOption === theme);
  });
  window.dispatchEvent(new CustomEvent("themeChanged", { detail: { theme, resolved } }));
}

function setTheme(theme) {
  localStorage.setItem(THEME_STORAGE_KEY, theme);
  applyTheme(theme);
}

function bindThemeSwitcher() {
  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    button.addEventListener("click", () => setTheme(button.dataset.themeOption));
  });
}

prefersDarkQuery.addEventListener("change", () => {
  if (getThemePreference() === "auto") applyTheme("auto");
});

applyTheme();
