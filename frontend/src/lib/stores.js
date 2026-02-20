import { writable } from "svelte/store";

export const hardwareStore = writable([]);
export const vmStore = writable([]);
export const appStore = writable([]);
export const storageStore = writable([]);
export const networkStore = writable([]);
export const miscStore = writable([]);
export const isMobile = writable(false);

export const activeDocId = writable(null);
export const toasts = writable([]);

let toastId = 0;
export function addToast(message, type = "info") {
  const id = ++toastId;
  toasts.update((t) => [...t, { id, message, type }]);
  setTimeout(() => {
    toasts.update((t) => t.filter((toast) => toast.id !== id));
  }, 3000);
}
