import { storageGet, storageSet } from "./platform";

export function loadValue(key) {
  return storageGet([key]).then((data) => data?.[key] ?? null);
}

export function saveValue(key, value) {
  return storageSet({ [key]: value });
}
