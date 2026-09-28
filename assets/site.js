/* Sections rise into place once as they scroll in. Only when motion is welcome,
   and only after this runs, so with JavaScript off nothing is ever hidden. */
(function () {
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var els = document.querySelectorAll('[data-rise]');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
  els.forEach(function (el) {
    // Anything already on screen at load stays put rather than blinking in.
    var r = el.getBoundingClientRect();
    if (r.top < window.innerHeight * 0.92) return;
    el.classList.add('rise');
    io.observe(el);
  });
})();
