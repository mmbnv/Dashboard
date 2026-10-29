# ✨ Glassy Dashboard

A modern glassmorphism-powered **Chrome New Tab Extension** that transforms your browser into a beautiful, customizable dashboard.

<p align="center">
  <img src="https://res.cloudinary.com/dcve50avm/image/upload/v1785610310/output_5s_512_24fps_p80swr.gif" alt="Glassy Dashboard Demo" width="700">
</p>

---

## ✨ Features

### 🧑‍💻 Dashboard
- 🕒 Live Clock
- 🎨 Glassmorphism UI
- 🌓 Light & Dark Theme
- 🖱️ Drag-and-drop widget layout
- 💾 Local Storage

### ✅ Tasks
- 📋 Kanban board: To Do / In Progress / Done
- 🎯 Priority, due date and tags
- 🔍 Search and priority filter
- ⚡ Quick-add widget on the home screen
- 📥 Import / export tasks as JSON

### 📝 Notes
- 🗒️ Sticky notes widget
- ✏️ Edit and delete inline

### 🔖 Bookmarks
- 📂 Folder-based bookmark manager
- 🔍 Instant bookmark search
- 🗑️ Delete bookmarks
- ➕ Add and import bookmarks (standalone app mode)

### 🚀 More
- 🖼️ Custom Background
- 📌 Frequently Visited Sites
- 🌦️ Weather widget (OpenWeather API key)
- 📲 Installable as a standalone app (PWA)
- 🔒 Runs locally — extension APIs in the extension, localStorage otherwise

---

## 📦 Installation

The dashboard runs in two ways. Pick one.

### Option A — Standalone app (no browser extension)

```bash
npm install
npm run app
```

`npm run app` builds the project and serves it at <http://localhost:4173>.
Open that URL and use the dashboard as a normal web page.

To install it as a real desktop app: open the URL in Chrome or Edge and click the
**install** icon in the address bar (or *Menu → Cast, save and share → Install page as app*).
It then opens in its own window with its own taskbar/dock icon and works offline.

### Option B — Chrome / Edge extension (New Tab override)

```bash
npm install
npm run build
```

Then open `chrome://extensions`, enable **Developer Mode**, click **Load unpacked**,
and select the **`dist`** folder — not the project root.

> ⚠️ **"Файл манифеста отсутствует или недоступен для чтения" / "Manifest file is missing or unreadable"**
>
> This error means the folder you selected has no `manifest.json` at its top level.
> Two common causes:
>
> 1. You selected the project root (`Glassy_DashBoard-main`) instead of `dist`.
>    `manifest.json` lives in `public/` and is copied into `dist/` only during a build,
>    so **run `npm run build` first** and then load `dist/`.
> 2. `npm run build` failed — usually `vite` was not found because dependencies were
>    never installed. Run `npm install` first (see *Troubleshooting* below).

---

## 🛠️ Built With

- React
- Vite
- Tailwind CSS
- Chrome Extension Manifest V3 / PWA

---

## 📂 Project Structure

```text
public/
├── manifest.json          MV3 manifest (copied into dist/ at build time)
└── pwa-*.png              app icons for the standalone/PWA mode

src/
├── assets/
├── components/
├── lib/
│   ├── platform.js        the only place that talks to chrome.* / localStorage
│   ├── persistence.js     key/value helper built on platform.js
│   ├── globalState.js     dashboard config + quick-access apps
│   ├── globalToggles.js   UI visibility flags
│   ├── tasksStore.js      task state
│   └── notesStore.js      notes state
├── page/
│   ├── controller/        radial toolbar, bookmarks, settings panels
│   └── widgets/           clock, search, weather, tasks, notes
└── utils/
```

### Two environments, one codebase

`src/lib/platform.js` detects where the code is running:

| Capability   | Extension (MV3)              | Standalone app / PWA            |
|--------------|------------------------------|---------------------------------|
| Detection    | `chrome.runtime.id` present  | otherwise                       |
| Storage      | `chrome.storage.local`       | `localStorage`                  |
| Bookmarks    | `chrome.bookmarks`           | local store + HTML import       |
| Top sites    | `chrome.topSites`            | visit counter in `localStorage` |
| Install      | Load unpacked                | PWA install prompt              |

No component branches on `chrome` directly — add new browser integrations to
`platform.js` and give them a web fallback.

---

## 🧰 Troubleshooting

**`"vite" не является внутренней или внешней командой` / `'vite' is not recognized`**

Dependencies are not installed. Run:

```bash
npm install
```

Then re-run `npm run build`. `npm run build` runs `vite` from
`node_modules/.bin`, which only exists after `npm install`.

**Extension: "Manifest file is missing or unreadable"**

You pointed *Load unpacked* at a folder without `manifest.json`. Run
`npm run build` and load the `dist` folder.

---

## 🗺️ Roadmap

- [x] Dashboard
- [x] Bookmark Manager
- [x] Search
- [x] Theme Switcher
- [x] Weather Widget
- [x] Notes
- [x] Todo List / Task Board
- [x] Draggable Widgets
- [x] Standalone installable app (PWA)
- [ ] Chrome Web Store Release

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

---

## 📜 License

MIT License

---

<p align="center">
Made with ❤️ using React, Tailwind CSS & Chrome Extension APIs
</p>
