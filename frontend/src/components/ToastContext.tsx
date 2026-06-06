const TOAST_EVENT = "scriptforge-toast";

type ToastType = "success" | "error" | "info";

export function toast(type: ToastType, message: string) {
  window.dispatchEvent(
    new CustomEvent(TOAST_EVENT, { detail: { type, message } })
  );
}

export function getToastEventName() {
  return TOAST_EVENT;
}
