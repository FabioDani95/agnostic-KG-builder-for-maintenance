# Frontend design references

The workspace application follows the compact, restrained interaction
direction recorded in:

- [DESIGN.md](DESIGN.md): supplied visual reference, density, typography,
  surface and component guidance;
- [SKILL.md](SKILL.md): direct-manipulation, motion and accessibility guidance.

These files are design inputs. The shipped token implementation is
[frontend/design.css](../../frontend/design.css), and layout/component rules
are in [frontend/app.css](../../frontend/app.css). The CSS is the executable
source of truth for current token names and values; this repository does not
claim that every value in the DESIGN.md front matter is copied byte-for-byte.

## Styling boundary

design.css owns the workspace application's semantic palette, type colours,
surface materials, theme behavior, shared controls and motion primitives.
app.css owns phase-specific layout and component geometry. Raw layout
measurements in app.css are intentional when they express a local size rather
than a reusable semantic token.

The retained PDF console keeps its established palette in console.css. Its
rules are scoped away from #app.app so they cannot override the workspace
application when console.html loads both style sheets.

## Theme and accessibility

The workspace UI provides explicit light/dark and Italian/English controls,
persisted locally. CSS honors reduced motion and reduced transparency. Status
is always paired with text or shape, never encoded by colour alone.

## Graph interaction

The graph map in frontend/app/explorer.js is the main direct-manipulation
surface:

- node and canvas drag use pointer capture and preserve the grab point;
- wheel zoom is centered on the pointer;
- keyboard arrows traverse neighbouring graph nodes;
- a dropped node stays pinned until explicitly released;
- filter changes preserve positions and selection where valid;
- frontend/app/force.js keeps the surrounding graph responsive during drag.

The current deliberate trade-off is that canvas boundary resistance uses
native browser overscroll rather than a custom rubber-band curve.

## Change rule

Visual changes must preserve the separation between shared tokens and
phase-specific geometry, keep both themes readable, and pass the Playwright
workspace scenarios. If the supplied design references and the shipped CSS
are intentionally realigned, update this note in the same change.
