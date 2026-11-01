import { useState } from "react";
import { PRIORITIES } from "../../../../lib/tasksStore";

const emptyDraft = {
  title: "",
  notes: "",
  status: "todo",
  priority: "medium",
  due: "",
  tags: "",
};

const toDraft = (initial, defaultStatus) =>
  initial
    ? {
        title: initial.title || "",
        notes: initial.notes || "",
        status: initial.status || "todo",
        priority: initial.priority || "medium",
        due: initial.due || "",
        tags: (initial.tags || []).join(", "),
      }
    : { ...emptyDraft, status: defaultStatus };

export default function TaskComposer({
  columns,
  initial,
  defaultStatus = "todo",
  onSubmit,
  onCancel,
}) {
  const [draft, setDraft] = useState(() => toDraft(initial, defaultStatus));

  const set = (key, value) => setDraft((prev) => ({ ...prev, [key]: value }));

  const submit = (e) => {
    e.preventDefault();
    if (!draft.title.trim()) return;
    onSubmit({
      title: draft.title.trim(),
      notes: draft.notes.trim(),
      status: draft.status,
      priority: draft.priority,
      due: draft.due,
      tags: draft.tags
        .split(",")
        .map((t) => t.trim().replace(/^#/, ""))
        .filter(Boolean),
    });
  };

  const field =
    "w-full rounded-lg bg-black/30 border border-white/10 px-2.5 py-2 text-sm text-zinc-100 outline-none focus:border-violet-400/60 placeholder:text-zinc-600";

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <input
        autoFocus
        className={field}
        placeholder="What needs to be done?"
        value={draft.title}
        onChange={(e) => set("title", e.target.value)}
      />

      <textarea
        className={`${field} resize-none`}
        rows={2}
        placeholder="Notes (optional)"
        value={draft.notes}
        onChange={(e) => set("notes", e.target.value)}
      />

      <div className="grid grid-cols-3 gap-2">
        <select
          className={field}
          value={draft.status}
          onChange={(e) => set("status", e.target.value)}
        >
          {columns.map((c) => (
            <option key={c.id} value={c.id} className="bg-zinc-900">
              {c.title}
            </option>
          ))}
        </select>

        <select
          className={field}
          value={draft.priority}
          onChange={(e) => set("priority", e.target.value)}
        >
          {PRIORITIES.map((p) => (
            <option key={p.id} value={p.id} className="bg-zinc-900">
              {p.label}
            </option>
          ))}
        </select>

        <input
          type="date"
          className={field}
          value={draft.due}
          onChange={(e) => set("due", e.target.value)}
        />
      </div>

      <input
        className={field}
        placeholder="Tags, comma separated"
        value={draft.tags}
        onChange={(e) => set("tags", e.target.value)}
      />

      <div className="flex items-center gap-2 justify-end">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 rounded-lg text-sm text-zinc-400 hover:text-white hover:bg-white/10"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-violet-600 hover:bg-violet-500 text-white"
        >
          {initial ? "Save" : "Add task"}
        </button>
      </div>
    </form>
  );
}
