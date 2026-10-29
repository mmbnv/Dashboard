import { useMemo } from "react";
import { COLUMNS, useTaskStore } from "../../../lib/tasksStore";

const startOfDay = (d) => {
  const copy = new Date(d);
  copy.setHours(0, 0, 0, 0);
  return copy;
};

export function useTaskStats() {
  const tasks = useTaskStore((s) => s.tasks);

  return useMemo(() => {
    const total = tasks.length;
    const done = tasks.filter((t) => t.status === "done").length;
    const overdue = tasks.filter((t) => {
      if (!t.due || t.status === "done") return false;
      return startOfDay(t.due) < startOfDay(new Date());
    }).length;
    const today = tasks.filter((t) => {
      if (!t.due || t.status === "done") return false;
      return startOfDay(t.due).getTime() === startOfDay(new Date()).getTime();
    }).length;

    const byColumn = COLUMNS.reduce((acc, col) => {
      acc[col.id] = tasks.filter((t) => t.status === col.id).length;
      return acc;
    }, {});

    const byPriority = tasks.reduce((acc, t) => {
      if (t.status !== "done") acc[t.priority] = (acc[t.priority] || 0) + 1;
      return acc;
    }, {});

    return {
      total,
      done,
      open: total - done,
      overdue,
      today,
      byColumn,
      byPriority,
      progress: total === 0 ? 0 : Math.round((done / total) * 100),
    };
  }, [tasks]);
}
