import { useEffect, useRef, useState } from "react";

export default function AnalogClock() {
    let isCalled = false;
    const [dateObj,setDate] = useState({}); 
    const secondRef = useRef(null);
    const minuteRef = useRef(null);
    const hourRef = useRef(null);

useEffect(() => {

    const handleTime = () => {
        if(!secondRef.current || !minuteRef.current || !hourRef.current) return;
        const now = new Date();

        const seconds = (now.getSeconds() + now.getMilliseconds() / 1000) * 6;
        const minute = now.getMinutes() * 6 + now.getSeconds() * 0.1;
        const hours = (now.getHours() % 12) * 30 + now.getMinutes() * 0.5;

        secondRef.current.style.transform = `rotate(${seconds}deg)`;
        minuteRef.current.style.transform = `rotate(${minute}deg)`;
        hourRef.current.style.transform = `rotate(${hours}deg)`;
        if (!isCalled) {
            let dateStr = new Date();
            let today = dateStr.toLocaleString('default', {day: "2-digit"})
            let monthName = dateStr.toLocaleString('default', {month: 'short'})
            let year = dateStr.getFullYear();
            setDate({today,monthName,year})
            isCalled = true
        }
    };

    let timeInterval = setInterval(handleTime, 50);

    return () => clearInterval(timeInterval);

}, []);

    return(
        <>
            <div id="dateCol">
                <span className="date">{dateObj?.today}</span>
                <span className="month">{dateObj?.monthName}</span>
                <span className="year">{dateObj?.year}</span>
            </div>
            <div  id="clock-body" className="blurBg" >
                <span id="thre" className="cont">3</span>
                <span id="six" className="cont">6</span>
                <span id="nin" className="cont">9</span>
                <span id="twe" className="cont">12</span>
                
                <div id="midleC"></div>
                <div ref={secondRef} id="sec" className="ned"><h3></h3></div>
                <div ref={minuteRef} id="min" className="ned"><h3></h3></div>
                <div ref={hourRef} id="ho" className="ned"> <h3></h3></div>
            </div>
        </>
    )
}