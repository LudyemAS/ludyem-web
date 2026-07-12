/* Runway shared UI behaviour: the footer light/dark toggle and the mobile nav
   hamburger. The initial theme (saved choice, else the OS setting) is resolved
   by a tiny inline script in each page's <head> to avoid a flash; this file only
   wires the interactive controls. */
(function () {
  var root = document.documentElement;
  function current() { return root.getAttribute("data-theme") === "light" ? "light" : "dark"; }

  // Footer light/dark toggle
  var toggle = document.getElementById("theme-toggle");
  function renderToggle() {
    if (!toggle) return;
    var t = current();
    var label = toggle.querySelector(".theme-toggle-label");
    if (label) label.textContent = t === "light" ? "Dark" : "Light";
    toggle.setAttribute("aria-label", "Switch to " + (t === "light" ? "dark" : "light") + " theme");
  }
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = current() === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("runway-theme", next); } catch (e) {}
      renderToggle();
    });
    renderToggle();
  }

  // Mobile nav hamburger
  var nav = document.querySelector("nav");
  var navToggle = document.querySelector(".nav-toggle");
  if (nav && navToggle) {
    navToggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    Array.prototype.forEach.call(nav.querySelectorAll(".nav-links a"), function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }
})();
