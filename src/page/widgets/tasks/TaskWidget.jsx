import { useMemo, useState } from "react";
import { useTaskStore } from "../../../lib/tasksStore";
import { useTaskStats } from "./useTaskStats";
import TaskCard from "./components/TaskCard";

export default function TaskWidget({ onOpenBoard }) {
  const tasks = useTaskStore((s) => s.tasks);
  const addTask = useTaskStore((s) => s.addTask);
  const toggleTask = useTaskStore((s) => s.toggleTask);
  const removeTask = useTaskStore((s) => s.removeTask);
  const stats = useTaskStats();
  const [draft, setDraft] = useState("");

  const visible = useMemo(() => {
    const order = { high: 0, medium: 1, low: 2 };
    return tasks
      .filter((t) => t.status !== "done")
      .sort((a, b) => {
        if (a.due && b.due) return new Date(a.due) - new Date(b.due);
        if (a.due) return -1;
        if (b.due) return 1;
        return order[a.priority] - order[b.priority];
      })
      .slice(0, 4);
  }, [tasks]);

  const submit = (e) => {
    e.preventDefault();
    if (!draft.trim()) return;
    addTask({ title: draft.trim() });
    setDraft("");
  };

  return (
    <div className="blurBg w-90 p-3.5 flex flex-col gap-3 text-zinc-100">
      <div className="flex items-center gap-2.5">
        <div className="h-9 w-9 rounded-lg bg-violet-500/20 border border-violet-400/30 flex items-center justify-center">
          <i className="bx bx-task text-lg text-violet-300" />
        </div>
        <div className="flex-1">
          <p className="font-semibold leading-tight">Tasks</p>
          <p className="text-[11px] text-zinc-400">
            {stats.open} open · {stats.done} done
            {stats.overdue > 0 && (
              <span className="text-rose-400"> · {stats.overdue} overdue</span>
            )}
          </p>
        </div>
        <button
          onClick={onOpenBoard}
          className="text-[11px] px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10"
        >
          Open board
        </button>
      </div>

      <div className="h-1.5 w-full rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-linear-to-r from-violet-500 to-cyan-400 transition-all duration-500"
          style={{ width: `${stats.progress}%` }}
        />
      </div>

      <form onSubmit={submit} className="flex items-center gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add a quick task..."
          className="flex-1 h-9 rounded-lg bg-black/30 border border-white/10 px-2.5 text-sm outline-none focus:border-violet-400/60 placeholder:text-zinc-600"
        />
        <button
          type="submit"
          className="h-9 w-9 rounded-lg bg-violet-600 hover:bg-violet-500 flex items-center justify-center"
          title="Add task"
        >
          <i className="bx bx-plus text-lg" />
        </button>
      </form>

      <div className="flex flex-col gap-2 max-h-56 overflow-y-auto my-scroll">
        {visible.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            compact
            onToggle={toggleTask}
            onDelete={removeTask}
          />
        ))}
        {visible.length === 0 && (
          <p className="text-xs text-zinc-500 text-center py-3">
            Nothing open. Enjoy your day ✨
          </p>
        )}
      </div>
    </div>
  );
}
