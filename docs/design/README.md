# Design system

The operator interface follows one visual direction, defined by two documents
supplied by the Product Owner. They are normative for the frontend.

- [DESIGN.md](DESIGN.md) — "Compact Apple-Inspired Interface": the token values
  (colours light and dark, radii, spacing, sizing), the type scale, density
  rules, and the component rules for buttons, inputs, panels, tables and
  navigation.
- [SKILL.md](SKILL.md) — interaction and motion: response on pointer-down, 1:1
  direct manipulation, interruptible spring motion, velocity hand-off, momentum
  projection, translucent materials, typography, and the reduced-motion,
  reduced-transparency and increased-contrast requirements.

## Where the tokens live

Every value from the `DESIGN.md` front matter is declared once, in
[`frontend/design.css`](../../frontend/design.css), as a CSS custom property on
`:root`, with a dark-mode block and a `prefers-contrast: more` block. The
application layer, [`frontend/app.css`](../../frontend/app.css), never contains
a raw colour, radius or spacing value: it only references tokens.

Four token families are **not** in `DESIGN.md` and are declared with their
rationale inline in `frontend/design.css`:

| Token family | Why it exists |
|---|---|
| `--shadow-1/2/3` | `DESIGN.md` asks for subtle shadows over heavy borders but fixes no values. Three steps only: resting, raised, floating. |
| `--node-*` | One low-chroma hue per ontological node type, deliberately outside the status hues so a type is never read as a status. The type name is always spelled out in text as well, so the hue is redundant reinforcement and never the sole channel. |
| `--motion-*`, `--ease-*` | The interaction timings `SKILL.md` prescribes, named once instead of repeated. |
| dark `--success/--warning/--danger` and their `-soft` fills | `dark_colors` in `DESIGN.md` omits the status colours. These are the light hues lifted to readable luminance on a near-black surface, with the soft fills rebuilt as low-alpha tints rather than pale pastels. |

The retained PDF-baseline console keeps its own palette in
`frontend/console.css`; its global rules are scoped away from `.kg-app` so the
two cannot bleed into each other.

## Where the motion rules are applied

`SKILL.md` is written for gesture-driven interfaces. The place it genuinely
applies here is the graph canvas, in
[`frontend/app/motion.js`](../../frontend/app/motion.js): drag-to-pan tracks the
pointer 1:1 from the exact grab point using pointer capture, keeps a short
velocity history, and hands the release velocity to a glide whose resting point
comes from the exponential momentum projection. A new press cancels the glide on
the next frame, so the motion is always interruptible. Everything is skipped
under `prefers-reduced-motion`.

Panning writes to the container's own scroll offsets rather than to a transform,
so the wheel, the trackpad, the scrollbars and keyboard scrolling keep working
unchanged. The trade-off is that boundary resistance is the browser's native
overscroll rather than the rubber-band curve in `SKILL.md` §9.
