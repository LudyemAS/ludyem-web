/* Runway launch-state toggle.
   Flips the whole site from pre-launch (beta + waitlist) to live (App Store)
   with no redeploy and no launch-day edit. Loaded synchronously in <head>,
   before first paint, so the correct state is on <html> before anything renders.

     class="js-prelaunch"  shows only BEFORE launch (beta / waitlist CTAs)
     class="js-live"       shows only AFTER launch (App Store CTAs)

   Markup ships with <html class="is-prelaunch">, so with JavaScript off the
   beta CTAs still show and nothing looks broken.

   Preview the live state right now, without waiting for the date:
     localStorage.setItem('runwayLive', '1')   // force live
     localStorage.setItem('runwayLive', '0')   // force pre-launch
     localStorage.removeItem('runwayLive')      // back to automatic (by date)
*/
(function () {
  // Default flip date: Runway available on the App Store worldwide (2026-09-15).
  // A page can override it by setting window.RUNWAY_LAUNCH to an ISO date BEFORE
  // this script loads. The Norway-first landing page uses 2026-08-25 (Norway can
  // download from launch day); the global blog waits for the worldwide date so
  // the download link works for every reader. Move a date in one place only.
  var iso = (typeof window !== 'undefined' && window.RUNWAY_LAUNCH) || '2026-09-15T00:00:00Z';
  var LAUNCH = Date.parse(iso);

  var override = null;
  try { override = localStorage.getItem('runwayLive'); } catch (e) {}

  var live = override === '1' || (override !== '0' && Date.now() >= LAUNCH);

  var root = document.documentElement;
  root.classList.remove('is-prelaunch', 'is-live');
  root.classList.add(live ? 'is-live' : 'is-prelaunch');
})();
