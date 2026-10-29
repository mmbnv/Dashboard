import { PRIORITIES } from "../../../../lib/tasksStore";

const priorityStyles = {
  low: "bg-emerald-400/20 text-emerald-300 border-emerald-400/30",
  medium: "bg-amber-400/20 text-amber-300 border-amber-400/30",
  high: "bg-rose-500/20 text-rose-300 border-rose-400/30",
};

function formatDue(due) {
  if (!due) return null;
  const date = new Date(due);
  if (Number.isNaN(date.getTime())) return null;

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  const diffDays = Math.round((target - today) / 86400000);

  const label = date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

  if (diffDays < 0) return { label, tone: "text-rose-300", text: `Overdue · ${label}` };
  if (diffDays === 0) return { label, tone: "text-amber-300", text: "Today" };
  if (diffDays === 1) return { label, tone: "text-cyan-300", text: "Tomorrow" };
  return { label, tone: "text-zinc-400", text: label };
}

export default function TaskCard({ task, onToggle, onEdit, onDelete, compact }) {
  const priority = PRIORITIES.find((p) => p.id === task.priority);
  const due = formatDue(task.due);
  const isDone = task.status === "done";

  return (
    <article
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData("text/plain", task.id);
        e.dataTransfer.effectAllowed = "move";
      }}
      className={`group relative rounded-xl border border-white/10 bg-white/5 backdrop-blur-md p-3 transition-all hover:border-violet-400/40 hover:bg-white/10 ${
        compact ? "text-xs" : "text-sm"
      }`}
    >
      <div className="flex items-start gap-2">
        <button
          onClick={() => onToggle?.(task.id)}
          title={isDone ? "Mark as not done" : "Mark as done"}
          className={`mt-0.5 h-5 w-5 shrink-0 rounded-md border flex items-center justify-center transition ${
            isDone
              ? "bg-emerald-500/80 border-emerald-400 text-white"
              : "border-white/30 hover:border-violet-400"
          }`}
        >
          {isDone && <i className="bx bx-check text-base leading-none" />}
        </button>

        <div className="flex-1 min-w-0">
          <p
            className={`font-medium leading-snug break-words ${
              isDone ? "line-through text-zinc-500" : "text-zinc-100"
            }`}
          >
            {task.title}
          </p>

          {!compact && task.notes && (
            <p className="mt-1 text-[11px] text-zinc-500 line-clamp-2">
              {task.notes}
            </p>
          )}

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            <span
              className={`px-1.5 py-0.5 rounded-full border text-[10px] uppercase tracking-wide ${
                priorityStyles[task.priority] || priorityStyles.medium
              }`}
            >
              {priority?.label}
            </span>

            {due && (
              <span className={`text-[10px] ${due.tone}`}>
                <i className="bx bx-calendar-event mr-0.5" />
                {due.text}
              </span>
            )}

            {task.tags?.map((tag) => (
              <span
                key={tag}
                className="px-1.5 py-0.5 rounded-full bg-violet-500/15 text-violet-300 text-[10px]"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-1 opacity-0 group-hover:opacity-100 transition">
          <button
            onClick={() => onEdit?.(task)}
            title="Edit"
            className="h-6 w-6 rounded-md text-zinc-400 hover:bg-white/10 hover:text-white"
          >
            <i className="bx bx-pencil" />
          </button>
          <button
            onClick={() => onDelete?.(task.id)}
            title="Delete"
            className="h-6 w-6 rounded-md text-zinc-400 hover:bg-rose-500/70 hover:text-white"
          >
            <i className="bx bx-trash" />
          </button>
        </div>
      </div>
    </article>
  );
}
