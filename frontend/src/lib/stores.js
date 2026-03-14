import { writable } from "svelte/store";

export const hardwareStore = writable([]);
export const vmStore = writable([]);
export const appStore = writable([]);
export const storageStore = writable([]);
export const networkStore = writable([]);
export const miscStore = writable([]);

export const activeDocId = writable(null);
export const toasts = writable([]);

// Auth stores — persisted to localStorage
export const authToken = writable(localStorage.getItem("authToken") || null);
export const isAdmin = writable(!!localStorage.getItem("authToken"));

authToken.subscribe((val) => {
  if (val) {
    localStorage.setItem("authToken", val);
    isAdmin.set(true);
  } else {
    localStorage.removeItem("authToken");
    isAdmin.set(false);
  }
});

let toastId = 0;
export function addToast(message, type = "info") {
  const id = ++toastId;
  toasts.update((t) => [...t, { id, message, type }]);
  setTimeout(() => {
    toasts.update((t) => t.filter((toast) => toast.id !== id));
  }, 3000);
}
