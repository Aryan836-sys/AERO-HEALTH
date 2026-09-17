# Aero Health | Frontend edition

A map-first air-quality experience for Kathmandu Valley. Version 2 replaces the small v1 homepage prototype with a multi-page, mock-backed frontend.

**Start here:** open [`frontend/README.md`](frontend/README.md).

```text
aero-health-v2/
  frontend/               React + TypeScript application
  docs/                   Design, integration, requirements, and validation notes
  .github/workflows/      Frontend CI workflow
```

The backend is intentionally not included or modified. When integrating into your existing `aero-health/` repository, back up the old frontend and replace only its `frontend/` directory with this one. Do not replace your backend or root repository configuration blindly.

The delivered source includes the map, area detail, comparison, auth, optional profile, explainable advisory, dashboard, favorites, alerts, community reporting, moderation, awareness, and a design-system page. Measurements and community incidents are fictional demo fixtures, not current air-quality information.

## Validation disclosure

54 automated tests of the project's own utilities and mock services passed during authoring. Source-integrity and constrained desktop/mobile source-rendering checks were also completed. Package downloads were unavailable in the authoring environment, so **a dependency-installed `npm run build` and the included full Playwright suite have not been executed**. Run the commands in the frontend README before your presentation or deployment. See [`docs/TESTING.md`](docs/TESTING.md) for the exact boundary of those checks.
