# Compiler Explorer frontend

React + Vite + TypeScript source for the web application served by the
FastAPI backend (`compiler/web/app.py`).

## Development

```bash
npm install
npm run dev      # dev server on :5173, proxies /api to the backend on :8080
```

Run the backend in another terminal: `python -m compiler.web.app`.

## Building

```bash
npm run build    # emits into ../compiler/web/static/ (committed to the repo)
```

The built output is committed so the app runs from a fresh clone without
Node. Rebuild and commit `compiler/web/static/` whenever you change the
frontend.

## Layout

- `src/App.tsx` — sidebar shell and section routing
- `src/api.ts` — typed client for the compiler API
- `src/pages/` — Playground, OptLab, AssemblyView, Explorer, Reference
- `src/components/` — Editor (CodeMirror), PipelineRail, AstTree, etc.
- Fonts are bundled via @fontsource; no CDN dependencies.
