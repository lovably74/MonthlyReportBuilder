import { create } from 'zustand';

export interface ToastItem {
  id: string;
  message: string;
  type: 'success' | 'error';
}

export interface ToastStore {
  toasts: ToastItem[];
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  dismiss: (id: string) => void;
}

let nextId = 0;

function generateId(): string {
  nextId += 1;
  return `toast-${nextId}-${Date.now()}`;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],

  showSuccess: (message: string) => {
    const id = generateId();
    set((state) => ({
      toasts: [...state.toasts, { id, message, type: 'success' }],
    }));
  },

  showError: (message: string) => {
    const id = generateId();
    set((state) => ({
      toasts: [...state.toasts, { id, message, type: 'error' }],
    }));
  },

  dismiss: (id: string) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
}));
