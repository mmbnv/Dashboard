import { useTaskStore } from "../../../lib/tasksStore";
import { useNotesStore } from "../../../lib/notesStore";
import { toast } from "react-toastify";

export default function ProductivityControl({ crntData, setData }) {
  const { taskWid, notesWid } = crntData;
  const tasks = useTaskStore((s) => s.tasks);
  const clearCompleted = useTaskStore((s) => s.clearCompleted);
  const notes = useNotesStore((s) => s.notes);

  const toggle = (key) => {
    setData({
      data: {
        [key]: {
          ...crntData[key],
          isVisible: !crntData[key].isVisible,
        },
      },
      isGet: false,
    });
  };

  return (
    <>
      <p className="headingP">✅ Tasks & Notes</p>

      <div className="controlleBox">
        <div className="leftaSideC">
          <div className="iconCon">📋</div>
          <div className="textHolder">
            <p>Show task widget</p>
            <span>Quick tasks on the home screen</span>
          </div>
        </div>
        <div className={`rightaSideC ${taskWid.isVisible ? "Active" : ""}`}>
          <button onClick={() => toggle("taskWid")}>
            <p />
          </button>
        </div>
      </div>

      <div className="controlleBox">
        <div className="leftaSideC">
          <div className="iconCon">📝</div>
          <div className="textHolder">
            <p>Show notes widget</p>
            <span>Sticky notes on the home screen</span>
          </div>
        </div>
        <div className={`rightaSideC ${notesWid.isVisible ? "Active" : ""}`}>
          <button onClick={() => toggle("notesWid")}>
            <p />
          </button>
        </div>
      </div>

      <div className="controlleBox">
        <div className="leftaSideC">
          <div className="iconCon">🧹</div>
          <div className="textHolder">
            <p>Clear completed tasks</p>
            <span>
              {tasks.filter((t) => t.status === "done").length} completed ·{" "}
              {notes.length} notes saved
            </span>
          </div>
        </div>
        <div className="rightaSideC">
          <button
            className="w-auto! px-3! text-[11px]"
            onClick={() => {
              clearCompleted();
              toast.success("Completed tasks cleared");
            }}
          >
            Clear
          </button>
        </div>
      </div>
    </>
  );
}
