(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};

  const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.reducedMotion = reducedMotion;

  /**
   * Momentum projection: where a flick comes to rest, given its release
   * velocity. Exponential decay, not the v²/2a textbook form.
   */
  const project = (velocity, decelerationRate = 0.998) =>
    (velocity / 1000) * decelerationRate / (1 - decelerationRate);

  /**
   * Drag-to-pan for a scrolling surface.
   *
   * The pointer is tracked 1:1 from the exact point it grabbed, momentum
   * continues at the release velocity, and a new press cancels the glide on
   * the very next frame instead of waiting for it to finish. Panning writes to
   * the container's own scroll offsets, so the wheel, the trackpad, the
   * scrollbars and keyboard scrolling keep working unchanged.
   */
  root.attachPan = function attachPan(container) {
    if (!container || container.__kgPan) return container.__kgPan;

    let glide = 0;
    let pointerId = null;
    let origin = null;
    let history = [];

    const stopGlide = () => {
      if (glide) window.cancelAnimationFrame(glide);
      glide = 0;
    };

    const isInteractive = (target) => Boolean(
      target.closest("button, a, input, select, textarea, [data-kg-node], [data-kg-relation]")
    );

    container.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 || isInteractive(event.target)) return;
      stopGlide();
      pointerId = event.pointerId;
      container.setPointerCapture(pointerId);
      container.dataset.panning = "true";
      origin = {
        x: event.clientX, y: event.clientY,
        left: container.scrollLeft, top: container.scrollTop,
      };
      history = [{ x: event.clientX, y: event.clientY, time: event.timeStamp }];
    });

    container.addEventListener("pointermove", (event) => {
      if (pointerId !== event.pointerId || !origin) return;
      container.scrollLeft = origin.left - (event.clientX - origin.x);
      container.scrollTop = origin.top - (event.clientY - origin.y);
      history.push({ x: event.clientX, y: event.clientY, time: event.timeStamp });
      if (history.length > 6) history.shift();
    });

    const release = (event) => {
      if (pointerId !== event.pointerId) return;
      container.releasePointerCapture?.(pointerId);
      pointerId = null;
      origin = null;
      delete container.dataset.panning;

      const first = history[0];
      const last = history[history.length - 1];
      history = [];
      if (!first || !last || reducedMotion()) return;
      const elapsed = last.time - first.time;
      if (elapsed <= 0) return;
      // px/s at release, handed straight to the glide.
      let vx = ((last.x - first.x) / elapsed) * -1000;
      let vy = ((last.y - first.y) / elapsed) * -1000;
      if (Math.hypot(vx, vy) < 120) return;

      const targetLeft = container.scrollLeft + project(vx);
      const targetTop = container.scrollTop + project(vy);
      let currentLeft = container.scrollLeft;
      let currentTop = container.scrollTop;

      const step = () => {
        currentLeft += (targetLeft - currentLeft) * 0.14;
        currentTop += (targetTop - currentTop) * 0.14;
        container.scrollLeft = currentLeft;
        container.scrollTop = currentTop;
        if (Math.abs(targetLeft - currentLeft) < 0.5 && Math.abs(targetTop - currentTop) < 0.5) {
          glide = 0;
          return;
        }
        glide = window.requestAnimationFrame(step);
      };
      glide = window.requestAnimationFrame(step);
    };

    container.addEventListener("pointerup", release);
    container.addEventListener("pointercancel", release);

    container.__kgPan = { stop: stopGlide };
    return container.__kgPan;
  };
})();
