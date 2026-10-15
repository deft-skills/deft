// DEFT site behaviour: theme, mobile menu, Markdown rendering, tabs, filters, table of contents.
(function () {
  const root = document.documentElement;
  try {
    const saved = localStorage.getItem("deft-theme");
    if (saved) root.setAttribute("data-theme", saved);
  } catch (e) { /* storage unavailable */ }

  function currentTheme() {
    const t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const themeBtn = document.getElementById("theme");
    if (themeBtn) themeBtn.addEventListener("click", function () {
      const next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("deft-theme", next); } catch (e) { /* ignore */ }
      renderMermaid(true);
    });
    const menuBtn = document.getElementById("menu");
    if (menuBtn) menuBtn.addEventListener("click", function () { document.body.classList.toggle("menu-open"); });

    // Markdown blocks: <div data-md="script-id"> filled from a JSON string
    if (window.marked) {
      document.querySelectorAll("[data-md]").forEach(function (el) {
        const src = document.getElementById(el.dataset.md);
        if (src) el.innerHTML = window.marked.parse(JSON.parse(src.textContent));
      });
      // ```mermaid blocks become diagrams
      document.querySelectorAll("code.language-mermaid").forEach(function (code) {
        const pre = document.createElement("pre");
        pre.className = "mermaid";
        pre.textContent = code.textContent;
        code.parentElement.replaceWith(pre);
      });
      // anchors for headings of rendered Markdown
      document.querySelectorAll(".md h2:not([id]), .md h3:not([id])").forEach(function (h) {
        h.id = h.textContent.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
      });
      if (location.hash) {
        const target = document.getElementById(location.hash.slice(1));
        if (target) target.scrollIntoView();
      }
    }

    // Tabs
    document.querySelectorAll("[data-tabs]").forEach(function (group) {
      const tabs = group.querySelectorAll(".tab");
      tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
          tabs.forEach(function (t) { t.classList.remove("active"); });
          group.parentElement.querySelectorAll(".tabpanel").forEach(function (p) { p.classList.remove("active"); });
          tab.classList.add("active");
          const panel = document.getElementById(tab.dataset.panel);
          if (panel) panel.classList.add("active");
        });
      });
    });

    // Catalogue search and filters
    const search = document.getElementById("search");
    const chips = document.querySelectorAll(".chip");
    let kind = "all";
    function applyFilter() {
      const q = (search && search.value || "").toLowerCase();
      document.querySelectorAll("[data-skill]").forEach(function (card) {
        const okText = !q || card.dataset.skill.indexOf(q) !== -1;
        const okKind = kind === "all" || card.dataset.kind === kind;
        card.style.display = okText && okKind ? "" : "none";
      });
    }
    if (search) search.addEventListener("input", applyFilter);
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        kind = chip.dataset.kind;
        applyFilter();
      });
    });

    // Copy buttons
    document.querySelectorAll("[data-copy]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const src = document.getElementById(btn.dataset.copy);
        if (!src || !navigator.clipboard) return;
        navigator.clipboard.writeText(src.textContent).then(function () {
          const old = btn.textContent; btn.textContent = "Copied"; setTimeout(function () { btn.textContent = old; }, 1200);
        });
      });
    });

    // On-this-page table of contents
    const toc = document.getElementById("toc-links");
    if (toc) {
      const heads = document.querySelectorAll(".content h2[id]");
      if (!heads.length) toc.parentElement.style.display = "none";
      heads.forEach(function (h) {
        const a = document.createElement("a");
        a.href = "#" + h.id; a.textContent = h.textContent;
        toc.appendChild(a);
      });
    }
    renderMermaid(false);
  });

  function renderMermaid(rerender) {
    if (!window.mermaid) return;
    const dark = currentTheme() === "dark";
    window.mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "neutral", securityLevel: "strict",
      flowchart: { curve: "basis", htmlLabels: true } });
    document.querySelectorAll(".mermaid").forEach(function (el) {
      if (!el.dataset.src) el.dataset.src = el.textContent;
      if (rerender) { el.removeAttribute("data-processed"); el.innerHTML = el.dataset.src; }
    });
    window.mermaid.run({ querySelector: ".mermaid" });
  }
})();
