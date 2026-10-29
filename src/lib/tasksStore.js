import { create } from "zustand";
import { loadValue, saveValue } from "./persistence";

export const STORAGE_KEY = "taskBoard";

export const COLUMNS = [
  { id: "todo", title: "To Do", accent: "violet" },
  { id: "doing", title: "In Progress", accent: "cyan" },
  { id: "done", title: "Done", accent: "emerald" },
];

export const PRIORITIES = [
  { id: "low", label: "Low" },
  { id: "medium", label: "Medium" },
  { id: "high", label: "High" },
];

export const STATUS_IDS = COLUMNS.map((c) => c.id);

const uid = () =>
  `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;

const normalizeTask = (raw) => {
  if (!raw || typeof raw !== "object") return null;
  const title = String(raw.title ?? "").trim();
  if (!title) return null;

  return {
    id: raw.id || uid(),
    title,
    notes: typeof raw.notes === "string" ? raw.notes : "",
    status: STATUS_IDS.includes(raw.status) ? raw.status : "todo",
    priority: PRIORITIES.some((p) => p.id === raw.priority)
      ? raw.priority
      : "medium",
    due: typeof raw.due === "string" ? raw.due : "",
    tags: Array.isArray(raw.tags) ? raw.tags.filter(Boolean).map(String) : [],
    createdAt: raw.createdAt || new Date().toISOString(),
    completedAt: raw.completedAt || null,
  };
};

const seedTasks = () => [
  normalizeTask({
    title: "Customize the dashboard layout",
    notes: "Drag widgets into edit mode to reposition them.",
    status: "todo",
    priority: "medium",
  }),
  normalizeTask({
    title: "Try the task board",
    notes: "Move this card to Done to see the progress ring update.",
    status: "doing",
    priority: "high",
  }),
].filter(Boolean);

export const useTaskStore = create((set, get) => ({
  tasks: [],
  hydrated: false,

  hydrate: async () => {
    if (get().hydrated) return;
    const stored = await loadValue(STORAGE_KEY);
    const list = Array.isArray(stored)
      ? stored.map(normalizeTask).filter(Boolean)
      : seedTasks();
    set({ tasks: list, hydrated: true });
  },

  addTask: (partial = {}) => {
    const task = normalizeTask(partial);
    if (!task) return null;
    set((state) => ({ tasks: [task, ...state.tasks] }));
    return task;
  },

  updateTask: (id, patch = {}) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === id ? { ...task, ...patch, id: task.id } : task,
      ),
    })),

  removeTask: (id) =>
    set((state) => ({ tasks: state.tasks.filter((t) => t.id !== id) })),

  moveTask: (id, status) => {
    if (!STATUS_IDS.includes(status)) return;
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === id
          ? {
              ...task,
              status,
              completedAt:
                status === "done"
                  ? task.completedAt || new Date().toISOString()
                  : null,
            }
          : task,
      ),
    }));
  },

  toggleTask: (id) => {
    const task = get().tasks.find((t) => t.id === id);
    if (!task) return;
    get().moveTask(id, task.status === "done" ? "todo" : "done");
  },

  clearCompleted: () =>
    set((state) => ({ tasks: state.tasks.filter((t) => t.status !== "done") })),

  importTasks: (incoming) => {
    const list = (Array.isArray(incoming) ? incoming : [])
      .map(normalizeTask)
      .filter(Boolean);
    if (!list.length) return 0;
    set((state) => {
      const known = new Set(state.tasks.map((t) => t.id));
      const fresh = list.filter((t) => !known.has(t.id));
      return { tasks: [...fresh, ...state.tasks] };
    });
    return list.length;
  },
}));

let persistTimer;
useTaskStore.subscribe((state, prev) => {
  if (!state.hydrated || state.tasks === prev.tasks) return;
  clearTimeout(persistTimer);
  persistTimer = setTimeout(() => saveValue(STORAGE_KEY, state.tasks), 250);
});
