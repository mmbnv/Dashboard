/**
 * Platform layer.
 *
 * The dashboard runs in two environments: as a Chrome/Edge MV3 extension
 * (chrome.* APIs available) and as a plain web app / installed PWA.
 * Everything environment-specific goes through this module so the rest of
 * the code never has to branch on `chrome`.
 */

export const isExtension =
  typeof chrome !== "undefined" && !!chrome?.runtime?.id;

/* ------------------------------------------------------------------ *
 * Storage
 * ------------------------------------------------------------------ */

// Keys that were written under a different name before this layer existed.
const LEGACY_KEYS = {
  db: ["db", "Saved"],
};

const readLocal = (key) => {
  const raw = localStorage.getItem(key);
  if (raw == null) return undefined;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
};

export function storageGet(keys) {
  const list = Array.isArray(keys) ? keys : [keys];

  if (isExtension && chrome.storage?.local) {
    return new Promise((resolve) => {
      chrome.storage.local.get(list, (data) => resolve(data || {}));
    });
  }

  const out = {};
  for (const key of list) {
    const candidates = LEGACY_KEYS[key] || [key];
    for (const candidate of candidates) {
      const value = readLocal(candidate);
      if (value !== undefined) {
        out[key] = value;
        break;
      }
    }
  }
  return Promise.resolve(out);
}

export function storageSet(patch) {
  if (isExtension && chrome.storage?.local) {
    return new Promise((resolve) => {
      chrome.storage.local.set(patch, () => resolve());
    });
  }

  try {
    for (const [key, value] of Object.entries(patch)) {
      localStorage.setItem(key, JSON.stringify(value));
    }
  } catch (err) {
    console.error("Unable to persist", Object.keys(patch), err);
  }
  return Promise.resolve();
}

/* ------------------------------------------------------------------ *
 * Top sites
 * ------------------------------------------------------------------ */

const FREQUENT_KEY = "frequentSites";

const hostLabel = (url) => {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "").split(".")[0];
    return host.charAt(0).toUpperCase() + host.slice(1);
  } catch {
    return url;
  }
};

/**
 * Records a visit so "frequently visited" works without chrome.topSites.
 * Only used outside the extension.
 */
export function recordVisit(url) {
  if (isExtension) return;
  try {
    const counts = JSON.parse(localStorage.getItem(FREQUENT_KEY) || "{}");
    counts[url] = (counts[url] || 0) + 1;
    localStorage.setItem(FREQUENT_KEY, JSON.stringify(counts));
  } catch {
    /* ignore quota / parse errors */
  }
}

function localFrequent(limit) {
  try {
    const counts = JSON.parse(localStorage.getItem(FREQUENT_KEY) || "{}");
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([url]) => ({ url, name: hostLabel(url) }));
  } catch {
    return [];
  }
}

export async function getTopSites(limit = 3) {
  if (isExtension && chrome.topSites?.get) {
    const sites = await chrome.topSites.get();
    return sites
      .slice(0, limit)
      .map((site) => ({ url: site.url, name: hostLabel(site.url) }));
  }
  return localFrequent(limit);
}

/* ------------------------------------------------------------------ *
 * Bookmarks
 * ------------------------------------------------------------------ */

const LOCAL_BOOKMARKS_KEY = "bookmarks";

const readLocalBookmarks = () => {
  const raw = readLocal(LOCAL_BOOKMARKS_KEY);
  return Array.isArray(raw) ? raw : [];
};

const writeLocalBookmarks = (list) => {
  localStorage.setItem(LOCAL_BOOKMARKS_KEY, JSON.stringify(list));
};

const uid = () =>
  `local-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

/** Returns the same shape as chrome.bookmarks.getTree(): an array of roots. */
export async function getBookmarkTree() {
  if (isExtension && chrome.bookmarks?.getTree) {
    return chrome.bookmarks.getTree();
  }

  const children = readLocalBookmarks().map((bookmark) => ({
    id: bookmark.id,
    title: bookmark.title,
    url: bookmark.url,
    dateAdded: bookmark.dateAdded,
  }));

  return [{ id: "local-root", title: "Bookmarks", children }];
}

export async function addBookmark({ title, url }) {
  if (isExtension && chrome.bookmarks?.create) {
    return chrome.bookmarks.create({ title, url });
  }

  const list = readLocalBookmarks();
  const bookmark = {
    id: uid(),
    title: title || hostLabel(url),
    url,
    dateAdded: Date.now(),
  };
  writeLocalBookmarks([bookmark, ...list]);
  return bookmark;
}

export async function removeBookmark(id) {
  if (isExtension && chrome.bookmarks?.remove) {
    return chrome.bookmarks.remove(id);
  }
  writeLocalBookmarks(readLocalBookmarks().filter((b) => b.id !== id));
}

/**
 * Imports a browser bookmark export (Netscape bookmark HTML) into the local
 * store. Only meaningful outside the extension, where real bookmarks exist.
 */
export async function importBookmarksHtml(html) {
  if (isExtension) return 0;

  const doc = new DOMParser().parseFromString(html, "text/html");
  const list = readLocalBookmarks();
  const known = new Set(list.map((b) => b.url));
  let added = 0;

  for (const anchor of doc.querySelectorAll("a[href]")) {
    const url = anchor.getAttribute("href");
    if (!/^https?:/i.test(url) || known.has(url)) continue;
    known.add(url);
    list.push({
      id: uid(),
      title: anchor.textContent.trim() || hostLabel(url),
      url,
      dateAdded: Date.now(),
    });
    added += 1;
  }

  writeLocalBookmarks(list);
  return added;
}

/* ------------------------------------------------------------------ *
 * Service worker (PWA)
 * ------------------------------------------------------------------ */

export async function registerServiceWorker() {
  if (isExtension) return;
  if (!("serviceWorker" in navigator)) return;
  try {
    const { registerSW } = await import("virtual:pwa-register");
    registerSW({ immediate: true });
  } catch (err) {
    console.warn("Service worker registration skipped", err);
  }
}
