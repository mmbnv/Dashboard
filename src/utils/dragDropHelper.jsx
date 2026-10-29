import { motion, useDragControls } from "framer-motion";

export default function DraggableWidget({
  id,
  position,
  setdata,
  toggleEdit,
  children,
  className = "",
}) {
  const controls = useDragControls();

  const handleDragEnd = (e, info) => {
    setdata((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        position:{
          x: prev[id].position.x + info.offset.x,
          y: prev[id].position.y + info.offset.y,
        }
      },
    }));
  };

  const hideWid = (crntID) => {
    setdata((prev)=> ({
      ...prev,
      [crntID]: {
        ...prev[crntID],
        isVisible:false
      }
    }))
  }

  return (
    <motion.div
      drag={toggleEdit}
      dragControls={controls}
      dragListener={false}
      dragElastic={0}
      dragMomentum={false}
      onDragEnd={handleDragEnd}
      className={`${className} absolute p-1`}
      dragTransition={{ bounceStiffness: 1000, bounceDamping: 50 }}
      style={{
        x: position.x,
        y: position.y,
      }}
    >
      {toggleEdit && (
        <div className="moverDiv">
          <i
            className="bx bxs-grid cursor-grab active:cursor-grabbing"
            onPointerDown={(e) => controls.start(e)}
          ></i>
          <i className="bx bx-x" onClick={()=>hideWid(id)}></i>
        </div>
      )}

      {children}
    </motion.div>
  );
}