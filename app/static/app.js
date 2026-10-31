document.addEventListener("DOMContentLoaded", () => {
  // mobile menu
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.getElementById("nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      toggle.setAttribute("aria-expanded", nav.classList.toggle("open"));
    });
  }

  // flash messages: close button, auto-hide for success/info
  document.querySelectorAll(".flash").forEach((el) => {
    const close = el.querySelector(".flash-close");
    if (close) close.addEventListener("click", () => el.remove());
    if (el.classList.contains("success") || el.classList.contains("info")) {
      setTimeout(() => el.remove(), 6000);
    }
  });

  // show / hide password
  document.querySelectorAll("[data-toggle-password]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
    });
  });

  // leave form: end date cannot be before start date
  const start = document.querySelector("[data-start]");
  const end = document.querySelector("[data-end]");
  if (start && end) {
    start.addEventListener("change", () => {
      end.min = start.value;
      if (end.value && end.value < start.value) end.value = start.value;
    });
  }

  // character counter for textareas
  document.querySelectorAll("[data-counter]").forEach((area) => {
    const out = document.getElementById(area.dataset.counter);
    const update = () => { out.textContent = area.value.length + "/" + area.maxLength; };
    area.addEventListener("input", update);
    update();
  });

  // ask before destructive actions
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // filter chips + search for tables
  document.querySelectorAll("[data-filterable]").forEach((box) => {
    const rows = [...box.querySelectorAll("[data-row]")];
    const chips = [...box.querySelectorAll("[data-filter]")];
    const search = box.querySelector("[data-search]");
    const none = box.querySelector("[data-no-match]");
    let status = "all";
    const apply = () => {
      const q = search ? search.value.toLowerCase() : "";
      let shown = 0;
      rows.forEach((row) => {
        const ok = (status === "all" || row.dataset.status === status) &&
                   row.textContent.toLowerCase().includes(q);
        row.hidden = !ok;
        if (ok) shown++;
      });
      if (none) none.hidden = shown !== 0;
    };
    chips.forEach((chip) => chip.addEventListener("click", () => {
      status = chip.dataset.filter;
      chips.forEach((c) => c.classList.toggle("active", c === chip));
      apply();
    }));
    if (search) search.addEventListener("input", apply);
  });
});
