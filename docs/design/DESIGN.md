---
version: "1.0"
name: "Compact Apple-Inspired Interface"

colors:
  background: "#F5F5F7"
  background-subtle: "#FAFAFC"
  surface: "#FFFFFF"
  surface-muted: "#F0F0F3"

  text-primary: "#1D1D1F"
  text-secondary: "#6E6E73"
  text-tertiary: "#98989D"

  accent: "#4776C5"
  accent-hover: "#3E69B0"
  accent-soft: "#E8EFFA"

  success: "#4D9460"
  success-soft: "#E8F3EB"

  warning: "#B5823D"
  warning-soft: "#F8F0E3"

  danger: "#C65A5A"
  danger-soft: "#FAEAEA"

  border: "#D9D9DE"
  separator: "#E5E5EA"
  focus: "#4776C5"

dark_colors:
  background: "#101012"
  background-subtle: "#161618"
  surface: "#1C1C1E"
  surface-muted: "#242426"

  text-primary: "#F5F5F7"
  text-secondary: "#A1A1A6"
  text-tertiary: "#7D7D83"

  accent: "#6E9FE8"
  accent-hover: "#83ADF0"
  accent-soft: "#1D2B42"

  border: "#38383D"
  separator: "#2C2C2E"

rounded:
  small: "8px"
  medium: "10px"
  large: "14px"
  panel: "18px"
  pill: "999px"

spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  5: "20px"
  6: "24px"
  8: "32px"

sizing:
  control-small: "28px"
  control-default: "34px"
  control-large: "40px"
  sidebar: "240px"
  content-max: "1440px"
---

# Design System

Create a compact, precise and understated web interface inspired by Apple
design principles, without copying any specific Apple product or application.

The interface must feel dense enough for professional work while remaining
clear, calm and easy to scan.

## Core direction

- Prefer clarity, precision and restraint over decoration.
- Keep layouts compact, but never cramped.
- Show more useful information without reducing readability.
- Use neutral surfaces for most of the interface.
- Use color primarily for actions, selection, status and feedback.
- Avoid oversized headings, excessive empty space and large marketing-style cards.
- Avoid decorative gradients, glowing effects and excessive glassmorphism.
- Every visual element must have a functional reason.

## Density

- Use `12px–16px` padding inside ordinary cards and panels.
- Use `8px–12px` gaps between related controls.
- Use `16px–24px` gaps between major sections.
- Keep desktop controls between `32px` and `40px` high.
- Tables and data lists should use rows between `36px` and `44px`.
- Avoid large empty hero areas inside application screens.
- Prefer inline actions, compact toolbars and grouped controls.
- Use whitespace to separate concepts, not to make the interface feel luxurious.
- Do not place every section inside a separate card.
- Preserve a clear hierarchy even when information density is high.

## Color usage

- Use neutral colors for the majority of the interface.
- Use the accent color only for primary actions, links and selected states.
- Prefer soft, slightly desaturated colors over highly saturated colors.
- Never communicate status using color alone.
- Pair status colors with text, icons or shape.
- Keep large surfaces neutral.
- Use soft tinted backgrounds for status messages rather than fully saturated fills.
- Maintain accessible contrast in light and dark mode.

## Surfaces and materials

- Use white or near-white backgrounds in light mode.
- Use dark neutral surfaces in dark mode.
- Use translucent materials only for floating navigation, toolbars, popovers and overlays.
- Never stack multiple light translucent surfaces.
- Prefer subtle shadows and separators over heavy borders.
- Use blur only when content visibly moves underneath a floating surface.
- Large surfaces may use a slightly stronger blur and shadow than small controls.
- Avoid unnecessary borders around every container.

Recommended translucent surface:

```css
.floating-surface {
  background: color-mix(in srgb, var(--surface) 78%, transparent);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  border: 1px solid color-mix(in srgb, var(--border) 70%, transparent);
}
```

## Typography

Use the platform system font:

```css
font-family:
  system-ui,
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  sans-serif;
```

Recommended type scale:

| Role | Size | Line height | Weight | Tracking |
| --- | ---: | ---: | ---: | ---: |
| Display | 36px | 1.08 | 600 | -0.025em |
| Page title | 28px | 1.15 | 600 | -0.02em |
| Section title | 20px | 1.25 | 600 | -0.01em |
| Body | 15px | 1.5 | 400 | 0 |
| UI label | 14px | 1.35 | 500 | 0 |
| Secondary | 13px | 1.4 | 400 | 0.005em |
| Caption | 12px | 1.35 | 500 | 0.01em |

Rules:

- Use weight and spacing to create hierarchy, not size alone.
- Keep application page titles compact.
- Avoid giant headings inside operational screens.
- Use slightly negative tracking on large headings.
- Do not use font weights heavier than `700` without a strong reason.
- Allow text resizing without breaking layouts.
- Do not place low-contrast gray text over translucent backgrounds.

## Layout

- Use a consistent alignment grid.
- Keep primary actions close to the content they affect.
- Place filters and secondary actions in compact toolbars.
- Prefer split views, sidebars and inspectors for professional workflows.
- Keep main content widths appropriate to the task.
- Use full available width for tables, dashboards and editors.
- Limit long-form reading content to approximately `720px`.
- On mobile, reduce columns before reducing text size.
- Preserve clear navigation and visible escape routes.

## Components

### Buttons

- Default height: `34px`.
- Compact height: `28px`.
- Large height: `40px`.
- Horizontal padding: `12px–16px`.
- Primary buttons use the accent color.
- Secondary buttons use neutral surfaces.
- Tertiary actions may appear as text or icon buttons.
- Avoid excessive pill-shaped buttons.
- Provide immediate feedback on pointer-down.
- Use visible focus states.
- Disable actions only when necessary and explain unavailable actions where useful.

### Inputs

- Default height: `34px–38px`.
- Use clear labels instead of relying only on placeholders.
- Keep borders subtle but focus states unmistakable.
- Validate inline near the affected input.
- Use compact help text only when it prevents an error.
- Group related fields with proximity.

### Cards and panels

- Use cards only when they communicate grouping, selection or elevation.
- Default padding: `14px–16px`.
- Default radius: `14px`.
- Avoid placing cards inside cards.
- Avoid giving every dashboard metric its own large container.
- Use separators and alignment when elevation is unnecessary.

### Tables and lists

- Row height: `36px–44px`.
- Align numeric values consistently.
- Keep column headers concise.
- Use subtle row hover states.
- Keep row actions visible on selection or hover without hiding essential actions.
- Support keyboard navigation where appropriate.
- Avoid excessive vertical padding.

### Navigation

- Keep navigation persistent where it improves orientation.
- Clearly distinguish selected, hovered and focused states.
- Use specific labels such as `Projects`, `Reports` or `Activity`.
- Avoid generic labels such as `Home` when a more precise label exists.
- Keep sidebar items compact and easy to scan.

### Dialogs and sheets

- Use dialogs only for focused tasks.
- Use confirmation dialogs only for destructive or irreversible actions.
- Anchor popovers and menus to their trigger.
- Enter and exit along the same spatial path.
- Allow users to interrupt or dismiss transitions immediately.

## Icons

- Use one consistent icon family.
- Prefer simple outline icons with consistent optical weight.
- Use icons without text only when their meaning is universally clear.
- Keep icon sizes between `16px` and `20px` in compact controls.
- Align icons optically, not only geometrically.
- Avoid mixing filled and outline styles without semantic reason.

## Motion

Follow all interaction and motion rules contained in `SKILL.md`.

Additional constraints:

- Keep motion subtle, purposeful and interruptible.
- Prefer spring-based motion for interactive elements.
- Use immediate pointer-down feedback.
- Animate mainly `transform` and `opacity`.
- Avoid animating layout when a direct transition is clearer.
- Never delay an action only to display an animation.
- Reserve bounce for interactions carrying real momentum.
- Avoid decorative looping animation.
- Respect `prefers-reduced-motion`.
- Replace large movement with short cross-fades when reduced motion is enabled.

## Accessibility

- Meet WCAG AA contrast for essential text and controls.
- Preserve visible keyboard focus.
- Support keyboard operation for all primary workflows.
- Do not rely on hover alone.
- Do not rely on color alone.
- Respect:
  - `prefers-reduced-motion`
  - `prefers-contrast`
  - `prefers-reduced-transparency`, where supported
- Keep touch targets large enough on touch devices, even when desktop controls are compact.
- Provide labels for icon-only controls.

## Implementation rules for the agent

Before changing a page:

1. Inspect the existing components and design tokens.
2. Preserve all current functionality.
3. Identify the most important user task on the page.
4. Simplify hierarchy before adding decoration.
5. Reuse existing components whenever appropriate.
6. Explain any new design token before introducing it.
7. Avoid one-off spacing, color and radius values.
8. Verify light mode, dark mode, mobile and reduced motion.
9. Keep the result compact, coherent and production-ready.
10. Do not imitate a specific Apple application screen.

## Final review checklist

- Is the page compact without feeling cramped?
- Is the primary action immediately identifiable?
- Are related controls visually grouped?
- Is color used sparingly and consistently?
- Are headings appropriately sized for an application?
- Are cards used only where they add meaning?
- Are rows and controls compact enough for professional use?
- Are animations interruptible and accessible?
- Does the page work in light and dark mode?
- Does the interface feel calm, precise and intentional?
