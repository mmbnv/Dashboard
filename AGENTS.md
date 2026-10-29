# AGENTS.md — Glassy Dashboard

Glassy Dashboard (React 19 + Vite 7 + Zustand + Tailwind 4 + framer-motion).
Ships as a Manifest V3 extension that overrides the New Tab page **and** as a
standalone installable web app (PWA) — see *Two runtime targets* below.

## Commands

- `npm install` — required before anything else; `npm run build` calls `vite` from
  `node_modules/.bin`, so a missing install shows up as "vite is not recognized".
- `npm run dev` — Vite dev server (config sets port 3221, `host: true`, `allowedHosts: true`).
  For remote/preview hosts run `npx vite --port <port> --host 0.0.0.0` and use the mapped URL.
- `npm run build` — production build into `dist/` (also emits `sw.js` + `manifest.webmanifest`).
- `npm run preview` / `npm run app` — serve the built output on port 4173.
- `npx eslint .` — lint. There is no test runner in this repo.

## Two runtime targets

The same bundle runs as an MV3 extension and as a standalone installable web app.
`src/lib/platform.js` is the only module allowed to touch `chrome.*`; it detects the
extension via `chrome.runtime.id` and falls back to `localStorage` (plus a local
bookmark store and a visit counter) in the web build. Add new browser integrations
there with a web fallback rather than branching on `chrome` inside components.

- Extension: load **`dist/`** via *Load unpacked* — `manifest.json` is only in `dist/`
  after a build, never in the project root.
- Standalone: `npm run app`, then use the browser's install prompt for its own window.

## Architecture

- `src/lib/platform.js` — environment boundary: storage, bookmarks, top sites, SW registration.
- `src/lib/globalState.js` — Zustand stores. `database` holds `db`, the per-widget config
  (each widget has `{isVisible, ...}`); `Apps` holds the quick-access app array.
  `setDB({data, isGet})` merges a partial patch into `db` and persists it; pass `isGet: true`
  to merge without writing storage. Persistence uses `chrome.storage.local` in the extension
  and falls back to `localStorage` on the web. There is also `removeApp(url)`.
- `src/lib/globalToggles.js` — `toggler` store with UI visibility flags (`toggleEdit`,
  `toggleTasks`, `toggleBookmarks`, `toggleVideo`, ...) driven by `toggleTab({flag: true})`.
- `src/page/widgets/mainHandler.jsx` — renders every widget inside `DraggableWidget`,
  gated by the matching `db` config flag and toggle.
- `src/page/controller/` — radial toolbar (`mainController.jsx`) and the settings panels
  (`settings/ContainerHolder.jsx` composes each `*Control.jsx`).
- `src/lib/persistence.js` — small storage helper shared by the task/notes stores.

## Adding a widget

1. Create `src/page/widgets/<name>/<Name>Widget.jsx`.
2. Add a `<name>Wid` entry to the `db` default in `globalState.js`.
3. Import and render it in `mainHandler.jsx` wrapped in `DraggableWidget`.
4. Add a settings row in `src/page/controller/settings/` and register it in `ContainerHolder.jsx`.
5. Optionally add a toolbar button in `mainController.jsx` plus a flag in `globalToggles.js`.

## Conventions

- Task/notes state lives in `src/lib/tasksStore.js` and `src/lib/notesStore.js`
  (Zustand + `persistence.js`), consumed by the widgets and `productivityControl.jsx`.
- ESLint globals include `chrome: 'readonly'`. `motion` imports in `Handlebg.jsx` and
  `dragDropHelper.jsx` are used only as `<motion.div>`; they carry an inline
  `eslint-disable-next-line no-unused-vars` because `eslint-plugin-react` is not installed.
- Async data loads in effects (`homeAll`, `bookmarksLIst`, `weatherCard`) carry inline
  `react-hooks/set-state-in-effect` disables — the rule fires on the synchronous
  `fetchX()` call even though the state update happens after `await`.
- Use `window.location.assign(url)` rather than assigning `window.location.href`
  (the `react-hooks/immutability` rule rejects the latter).

## Theming

- `src/assets/style/baseStyle.css` defines `--bg-color` / `--text-color`; the dark theme is
  `[data-theme='dark']`. Keep the dark text light — an earlier revision set it to `black`
  on a dark backdrop, making text unreadable.
- The radial toolbar places buttons with `--i` and `--step` (`72deg` for 5 buttons);
  change `--step` when the number of toolbar items changes.
