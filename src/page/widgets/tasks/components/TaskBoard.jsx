import { useMemo, useRef, useState } from "react";
import { toast } from "react-toastify";
import { COLUMNS, PRIORITIES, useTaskStore } from "../../../../lib/tasksStore";
import { useTaskStats } from "../useTaskStats";
import TaskCard from "./TaskCard";
import TaskComposer from "./TaskComposer";

const columnAccent = {
  violet: "text-violet-300 border-violet-400/40",
  cyan: "text-cyan-300 border-cyan-400/40",
  emerald: "text-emerald-300 border-emerald-400/40",
};

function StatCard({ icon, label, value, tone }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-md p-3 flex items-center gap-3">
      <div className={`h-9 w-9 rounded-lg flex items-center justify-center bg-white/5 ${tone}`}>
        <i className={`bx ${icon} text-xl`} />
      </div>
      <div>
        <p className="text-[11px] uppercase tracking-wide text-zinc-500">{label}</p>
        <p className="text-lg font-bold text-zinc-100 leading-tight">{value}</p>
      </div>
    </div>
  );
}

function ProgressRing({ value }) {
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className="relative h-16 w-16">
      <svg viewBox="0 0 64 64" className="h-16 w-16 -rotate-90">
        <circle cx="32" cy="32" r={radius} fill="none" stroke="rgba(255,255,255,.1)" strokeWidth="6" />
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke="url(#ringGrad)"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
        <defs>
          <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-sm font-bold text-zinc-100">
        {value}%
      </span>
    </div>
  );
}

export default function TaskBoard({ onClose }) {
  const tasks = useTaskStore((s) => s.tasks);
  const addTask = useTaskStore((s) => s.addTask);
  const updateTask = useTaskStore((s) => s.updateTask);
  const removeTask = useTaskStore((s) => s.removeTask);
  const moveTask = useTaskStore((s) => s.moveTask);
  const toggleTask = useTaskStore((s) => s.toggleTask);
  const clearCompleted = useTaskStore((s) => s.clearCompleted);
  const importTasks = useTaskStore((s) => s.importTasks);
  const stats = useTaskStats();

  const [query, setQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [showComposer, setShowComposer] = useState(false);
  const [editing, setEditing] = useState(null);
  const [dragOver, setDragOver] = useState(null);
  const fileRef = useRef(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return tasks.filter((t) => {
      if (priorityFilter !== "all" && t.priority !== priorityFilter) return false;
      if (!q) return true;
      return (
        t.title.toLowerCase().includes(q) ||
        t.notes.toLowerCase().includes(q) ||
        t.tags.some((tag) => tag.toLowerCase().includes(q))
      );
    });
  }, [tasks, query, priorityFilter]);

  const grouped = useMemo(
    () =>
      COLUMNS.reduce((acc, col) => {
        acc[col.id] = filtered.filter((t) => t.status === col.id);
        return acc;
      }, {}),
    [filtered],
  );

  const handleDrop = (e, status) => {
    e.preventDefault();
    setDragOver(null);
    const id = e.dataTransfer.getData("text/plain");
    if (id) moveTask(id, status);
  };

  const handleSubmit = (data) => {
    if (editing) {
      updateTask(editing.id, data);
      toast.success("Task updated");
      setEditing(null);
    } else {
      addTask(data);
      setShowComposer(false);
    }
  };

  const exportTasks = () => {
    const blob = new Blob([JSON.stringify(tasks, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "dashboard-tasks.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const importFromFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result);
        const count = importTasks(parsed);
        count ? toast.success(`Imported ${count} task(s)`) : toast.info("Nothing new to import");
      } catch {
        toast.error("Invalid task file");
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="w-full h-full flex flex-col overflow-hidden text-zinc-100">
      {/* Header */}
      <header className="shrink-0 border-b border-white/10 bg-black/30 backdrop-blur-xl">
        <div className="flex items-center gap-3 px-5 py-4">
          <div className="h-11 w-11 rounded-xl bg-violet-500/20 border border-violet-400/30 flex items-center justify-center">
            <i className="bx bx-task text-2xl text-violet-300" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold leading-tight">Task Board</h1>
            <p className="text-xs text-zinc-500">
              {stats.open} open · {stats.done} completed
              {stats.overdue > 0 && (
                <span className="text-rose-400"> · {stats.overdue} overdue</span>
              )}
            </p>
          </div>

          <div className="relative">
            <i className="bx bx-search absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search tasks..."
              className="h-10 w-56 rounded-xl bg-white/5 border border-white/10 pl-9 pr-3 text-sm outline-none focus:border-violet-400/60 placeholder:text-zinc-600"
            />
          </div>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="h-10 rounded-xl bg-white/5 border border-white/10 px-3 text-sm outline-none focus:border-violet-400/60"
          >
            <option value="all" className="bg-zinc-900">All priorities</option>
            {PRIORITIES.map((p) => (
              <option key={p.id} value={p.id} className="bg-zinc-900">
                {p.label}
              </option>
            ))}
          </select>

          <button
            onClick={() => {
              setEditing(null);
              setShowComposer((v) => !v);
            }}
            className="h-10 px-4 rounded-xl bg-violet-600 hover:bg-violet-500 font-semibold text-sm flex items-center gap-1.5"
          >
            <i className="bx bx-plus text-lg" /> New task
          </button>

          <button
            onClick={onClose}
            title="Close"
            className="h-10 w-10 rounded-xl bg-white/5 hover:bg-rose-500/60 border border-white/10"
          >
            <i className="bx bx-x text-xl" />
          </button>
        </div>

        {/* Dashboard strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-5 pb-4">
          <div className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-md p-3 flex items-center gap-4">
            <ProgressRing value={stats.progress} />
            <div>
              <p className="text-[11px] uppercase tracking-wide text-zinc-500">Progress</p>
              <p className="text-sm text-zinc-300">
                {stats.done}/{stats.total} done
              </p>
            </div>
          </div>
          <StatCard icon="bx-list-check" label="Open" value={stats.open} tone="text-cyan-300" />
          <StatCard icon="bx-time-five" label="Due today" value={stats.today} tone="text-amber-300" />
          <StatCard
            icon="bx-error-circle"
            label="Overdue"
            value={stats.overdue}
            tone="text-rose-300"
          />
        </div>

        {(showComposer || editing) && (
          <div className="px-5 pb-4">
            <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-md p-4">
              <TaskComposer
                key={editing?.id || "new"}
                columns={COLUMNS}
                initial={editing}
                defaultStatus={editing?.status || "todo"}
                onSubmit={handleSubmit}
                onCancel={() => {
                  setShowComposer(false);
                  setEditing(null);
                }}
              />
            </div>
          </div>
        )}
      </header>

      {/* Board */}
      <div className="flex-1 min-h-0 my-scroll px-5 py-5">
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-3 h-full">
          {COLUMNS.map((col) => (
            <section
              key={col.id}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(col.id);
              }}
              onDragLeave={() => setDragOver((c) => (c === col.id ? null : c))}
              onDrop={(e) => handleDrop(e, col.id)}
              className={`flex flex-col min-h-[200px] rounded-2xl border bg-black/20 backdrop-blur-md p-3 transition ${
                dragOver === col.id
                  ? "border-violet-400/70 bg-violet-500/10"
                  : "border-white/10"
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`flex items-center gap-2 border-b ${columnAccent[col.accent]} pb-1`}>
                  <h2 className="font-semibold">{col.title}</h2>
                  <span className="text-xs px-1.5 rounded-full bg-white/10">
                    {grouped[col.id].length}
                  </span>
                </div>
                <button
                  onClick={() => {
                    setEditing(null);
                    setShowComposer(true);
                  }}
                  className="h-7 w-7 rounded-lg text-zinc-400 hover:bg-white/10 hover:text-white"
                  title={`Add to ${col.title}`}
                >
                  <i className="bx bx-plus" />
                </button>
              </div>

              <div className="flex-1 min-h-0 overflow-y-auto my-scroll flex flex-col gap-2 pr-1">
                {grouped[col.id].map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onToggle={toggleTask}
                    onEdit={setEditing}
                    onDelete={(id) => {
                      removeTask(id);
                      toast.success("Task deleted");
                    }}
                  />
                ))}

                {grouped[col.id].length === 0 && (
                  <div className="flex-1 flex items-center justify-center text-xs text-zinc-600 border border-dashed border-white/10 rounded-xl py-6">
                    Drop tasks here
                  </div>
                )}
              </div>
            </section>
          ))}
        </div>

        <div className="flex items-center justify-between mt-4 text-xs text-zinc-500">
          <span>{filtered.length} of {tasks.length} tasks shown</span>
          <div className="flex items-center gap-2">
            <button onClick={exportTasks} className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10">
              <i className="bx bx-download mr-1" /> Export
            </button>
            <button
              onClick={() => fileRef.current?.click()}
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10"
            >
              <i className="bx bx-upload mr-1" /> Import
            </button>
            <input
              ref={fileRef}
              type="file"
              accept="application/json"
              className="hidden"
              onChange={(e) => {
                importFromFile(e.target.files?.[0]);
                e.target.value = "";
              }}
            />
            <button
              onClick={() => {
                clearCompleted();
                toast.success("Completed tasks cleared");
              }}
              className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-rose-500/40"
            >
              <i className="bx bx-trash mr-1" /> Clear done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
