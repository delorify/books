// Theme (light / dark) -------------------------------------------------------

const BH_THEME_KEY = "bookhub:theme";

function bhGetPreferredTheme() {
  const stored = window.localStorage.getItem(BH_THEME_KEY);
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  return window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function bhApplyTheme(theme) {
  document.documentElement.dataset.theme = theme;
}

function bhToggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  window.localStorage.setItem(BH_THEME_KEY, next);
  bhApplyTheme(next);
}

// Toasts ---------------------------------------------------------------------

function bhInitToasts() {
  const container = document.querySelector(".bh-toast-container");
  if (!container) return;

  const toasts = Array.from(container.querySelectorAll(".bh-toast"));
  toasts.forEach((toast, index) => {
    // Staggered entrance
    setTimeout(() => {
      toast.classList.add("bh-toast-visible");
    }, 80 * index);

    // Auto-dismiss
    const timeout = Number(toast.dataset.timeout || 3500);
    setTimeout(() => {
      toast.classList.remove("bh-toast-visible");
    }, timeout + 80 * index);
  });
}

// Modals ---------------------------------------------------------------------

function bhInitModals() {
  document.addEventListener("click", (event) => {
    const openTrigger = event.target.closest("[data-bh-modal-open]");
    if (openTrigger) {
      const targetId = openTrigger.getAttribute("data-bh-modal-open");
      const backdrop = document.getElementById(targetId);
      if (backdrop) {
        backdrop.classList.add("bh-modal-open");
      }
      return;
    }

    const closeTrigger = event.target.closest("[data-bh-modal-close]");
    if (closeTrigger) {
      const backdrop = closeTrigger.closest(".bh-modal-backdrop");
      if (backdrop) {
        backdrop.classList.remove("bh-modal-open");
      }
      return;
    }

    // Click outside modal content
    const backdrop = event.target.closest(".bh-modal-backdrop");
    if (backdrop && !event.target.closest(".bh-modal")) {
      backdrop.classList.remove("bh-modal-open");
    }
  });
}

// Dropdowns ------------------------------------------------------------------

function bhInitDropdowns() {
  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-bh-dropdown-toggle]");

    const openClass = "bh-dropdown-open";
    const menus = document.querySelectorAll(".bh-dropdown-menu");

    if (!toggle) {
      menus.forEach((menu) => menu.classList.remove(openClass));
      return;
    }

    const dropdown = toggle.closest(".bh-dropdown");
    if (!dropdown) return;
    const menu = dropdown.querySelector(".bh-dropdown-menu");
    if (!menu) return;

    const isOpen = menu.classList.contains(openClass);
    menus.forEach((m) => m.classList.remove(openClass));
    if (!isOpen) {
      menu.classList.add(openClass);
    }
  });
}

// Simple loading indicators on forms -----------------------------------------

function bhInitFormLoading() {
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;

    const loadingTargetSelector = form.getAttribute("data-bh-loading-target");
    if (!loadingTargetSelector) return;

    const target = document.querySelector(loadingTargetSelector);
    if (!target) return;

    target.classList.add("bh-skeleton");
  });
}

// Search interactions (subtle only) -----------------------------------------

function bhInitSearchHints() {
  const inputs = document.querySelectorAll("input[data-bh-search]");
  inputs.forEach((input) => {
    input.addEventListener("focus", () => {
      input.parentElement?.classList.add("bh-search-focused");
    });
    input.addEventListener("blur", () => {
      input.parentElement?.classList.remove("bh-search-focused");
    });
  });
}

// Reader controls -----------------------------------------------------------

function bhInitReader() {
  const container = document.querySelector(".bh-reader");
  if (!container) return;

  const page = container.querySelector(".bh-reader-page");
  if (!page) return;

  const baseUrl = container.getAttribute("data-bh-reader-base-url");
  const total = Number(container.getAttribute("data-bh-reader-total") || "0");
  let current = Number(container.getAttribute("data-bh-reader-page") || "1");

  function goTo(pageNumber) {
    if (!baseUrl || !total) return;
    const next = Math.max(1, Math.min(total, pageNumber));
    if (next === current) return;

    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set("page", String(next));
    container.classList.add("bh-skeleton");
    window.location.href = url.toString();
  }

  container.addEventListener("click", (event) => {
    const fontBtn = event.target.closest("[data-bh-reader-font]");
    if (fontBtn) {
      const size = fontBtn.getAttribute("data-bh-reader-font");
      if (size === "small") page.style.fontSize = "16px";
      if (size === "medium") page.style.fontSize = "17px";
      if (size === "large") page.style.fontSize = "18px";
    }

    const widthBtn = event.target.closest("[data-bh-reader-width]");
    if (widthBtn) {
      const width = widthBtn.getAttribute("data-bh-reader-width");
      page.classList.remove("narrow", "wide");
      if (width === "narrow") page.classList.add("narrow");
      if (width === "wide") page.classList.add("wide");
    }

    const fontFamilyBtn = event.target.closest("[data-bh-reader-family]");
    if (fontFamilyBtn) {
      const family = fontFamilyBtn.getAttribute("data-bh-reader-family");
      if (family === "serif") {
        page.classList.remove("sans");
      } else if (family === "sans") {
        page.classList.add("sans");
      }
    }

    const navBtn = event.target.closest("[data-bh-reader-nav]");
    if (navBtn) {
      const dir = navBtn.getAttribute("data-bh-reader-nav");
      if (dir === "prev") {
        goTo(current - 1);
      } else if (dir === "next") {
        goTo(current + 1);
      }
    }
  });

  const slider = container.querySelector("[data-bh-reader-slider]");
  if (slider) {
    slider.addEventListener("change", (event) => {
      const value = Number(event.target.value || "1");
      goTo(value);
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      goTo(current - 1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      goTo(current + 1);
    }
  });

  let touchStartX = null;
  container.addEventListener("touchstart", (event) => {
    if (event.touches && event.touches.length === 1) {
      touchStartX = event.touches[0].clientX;
    }
  });
  container.addEventListener("touchend", (event) => {
    if (touchStartX == null || !event.changedTouches || event.changedTouches.length === 0) {
      return;
    }
    const dx = event.changedTouches[0].clientX - touchStartX;
    touchStartX = null;
    if (Math.abs(dx) < 40) return;
    if (dx < 0) {
      goTo(current + 1);
    } else {
      goTo(current - 1);
    }
  });

  document.body.style.overflowY = "hidden";
}

// Bootstrapping --------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  bhApplyTheme(bhGetPreferredTheme());

  const themeToggle = document.querySelector("[data-bh-theme-toggle]");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      bhToggleTheme();
    });
  }

  bhInitToasts();
  bhInitModals();
  bhInitDropdowns();
  bhInitFormLoading();
  bhInitSearchHints();
  bhInitReader();
});

