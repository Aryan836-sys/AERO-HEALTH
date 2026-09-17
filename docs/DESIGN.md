# Design system and reference interpretation

## Direction

The user's screenshots are a quality/style reference, not copied assets: a map-first light interface, floating rounded station bubbles, quiet mint surfaces, a lower AQI-and-trend band, and purple interaction accents. The new logo and wordmark are Aero Health-specific. No original reference branding, avatar, New York location data, or screenshot pixels are embedded in the application.

All pages share one layout shell and one CSS/token vocabulary. Auth, moderation, reporting, profile, and awareness are designed as parts of the same product, not differently styled templates.

## Core tokens

| Token | Value | Use |
| --- | --- | --- |
| Ink | `#18312e` | Primary text |
| Muted | `#647970` | Supporting text |
| Canvas | `#f6f8f6` | Page background |
| Surface | `#ffffff` | Cards and navigation |
| Mint | `#13b992` | Air/environment accents |
| Violet | `#6651d8` | Primary controls |
| Border | `#e6ece7` | Quiet boundaries |
| Radius | `20px` | Main cards |

Typography requests Manrope, with system and Devanagari fallbacks. No font binary is included. Motion is deliberately restrained: short transitions, card/pin emphasis, and soft orbit details; reduced-motion preferences disable nonessential animation.

## AQI and honesty

The requested green/yellow/red/purple progression is retained. The build guide additionally requires all six US EPA categories, so the complete mapping includes orange and deep maroon: Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous.

Every category has a readable label and distinct symbol, not color alone. The six badge foreground/background pairs pass the included numerical 4.5:1 contrast assertions. This is not a certification that every text element in the full application meets WCAG.

The shared gauge clamps its arc to 0-500, displays the actual numeric value, and still treats higher values as hazardous. No direct data is visually distinct from a low reading. Stationless areas expose nearest-station distance, and charts show gaps instead of interpolating absent measurements.

The map is point-based. Broad pollution contours were intentionally not invented: they would conflict with the guide's no-direct-data requirement. Pollutant numbers are demo concentrations, not calculations from the sample AQI.

## Accessibility and responsive behavior

- Native buttons, selects, radio groups, checkboxes, and dialog elements.
- Keyboard map markers plus a text-based location list as an alternative to the map.
- Visible focus styling, skip link, navigation labels, and page-heading hierarchy.
- Dialog Escape handling and focus restoration; reduced-motion and forced-color support.
- Chart summaries, labeled time ranges, a data-table alternative, and CSV export.
- State components for loading, errors/retry, empty lists, and unavailable readings.
- A high-contrast preview toggle on the design-system page.

Layouts were source-render checked at 375px and 1440px. Real-library browser checks, screen-reader review, wider device coverage, and complete Nepali copy review remain acceptance tasks.
