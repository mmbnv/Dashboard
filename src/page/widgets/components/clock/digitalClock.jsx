import { useEffect, useRef } from "react";


export default function DigitalClock() {
  let isCalled = false
  const secondsRef = useRef(null);
  const minutesRef = useRef(null);
  const minuteRef = useRef(null);
  const hourRef = useRef(null);
  const dateRef = useRef(null)

  useEffect(() => {
    const seconds = secondsRef.current;
    const minutes = minutesRef.current;
    const minute = minuteRef.current;
    const hour = hourRef.current;
    const refDate = dateRef.current;


      function SetDate() {
        if (isCalled) return;
        isCalled = true;
        const dateSpan = document.createElement("span");
        const monthSpan = document.createElement("span")
        let DateStr = new Date();
        dateSpan.style.fontSize="20px"
      
        let monthName = DateStr.toLocaleString('default', { month: 'long' });
        dateSpan.innerText = DateStr.getDate();
        monthSpan.innerText = monthName;

        refDate.appendChild(dateSpan)
        refDate.appendChild(monthSpan)
      }
      SetDate()

    // create spikes
    for (let s = 0; s < 60; s++) {

      const mSpike = document.createElement("i");
      const sSpike = document.createElement("i");


      mSpike.className = "spike";
      sSpike.className = "spike";

      mSpike.style.setProperty("--rotate", `${6 * s}deg`);
      sSpike.style.setProperty("--rotate", `${6 * s}deg`);

      mSpike.setAttribute("data-i", s);
      sSpike.setAttribute("data-i", s);

      minutes.appendChild(mSpike);
      seconds.appendChild(sSpike);
    }

    function getTime() {

      const date = new Date();
      const s = date.getSeconds();
      const m = date.getMinutes();

      hour.textContent = date.getHours();
      minute.textContent = m;

      minutes.style.setProperty("--dRotate", `${6 * m}deg`);
      seconds.style.setProperty("--dRotate", `${6 * s}deg`);

      seconds.classList.toggle("stop-anim", s === 0);
      minutes.classList.toggle("stop-anim", m === 0);
    }

    getTime();
    const interval = setInterval(getTime, 1000);

    return () => clearInterval(interval);

  }, []);

  return (
    <>
      <div className="absolute dateHere flex gap-2.5 bottom-2.5 left-2.5 text-white" ref={dateRef}>
          
      </div>
      <div className="clock">

        <div ref={secondsRef} className="seconds"></div>

        <div ref={minutesRef} className="minutes"></div>

        <div ref={minuteRef} className="minute">00</div>

        <div ref={hourRef} className="hour">00</div>

      </div>
    </>
  );
}