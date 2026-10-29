import { useEffect, useState } from "react";
import { database } from "../../../lib/globalState"
import { toast } from "react-toastify";
import { pre } from "framer-motion/client";

export default function ClockCotroll ({crntData}) {
    let {setDB} = database();
    let {clockWid} = crntData;
    const [builDerLocalData, setIntoLocalData] = useState(crntData);

    useEffect(()=>{
        setDB({data:builDerLocalData, isGet:false});
    },[builDerLocalData]);

    return(
        <>
            <p className="headingP">
                🕝 Clock & Time
            </p>

            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">⏱️</div>
                    <div className="textHolder">
                        <p>Hide Clock</p>
                        <span>Hide the clock & date</span>
                    </div>
                </div>
                <div className={`rightaSideC ${clockWid.isVisible ? "Active" : ""}`}>
                     <button onClick={()=>{
                        setIntoLocalData(prev=>({
                            ...prev,
                            ["clockWid"]:{
                                ...prev["clockWid"],
                                isVisible: !prev["clockWid"].isVisible
                            }
                        }))
                     }}>
                        <p></p>
                     </button>
                </div>
            </div>

            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">🕧</div>
                    <div className="textHolder">
                        <p>Digital Clock</p>
                        <span>Switch to digital clock display</span>
                    </div>
                </div>
                <div className={`rightaSideC ${clockWid.anaLog ? "" : "Active"}`}>
                     <button onClick={()=>{
                        setIntoLocalData(prev=>({
                            ...prev,
                            ["clockWid"]:{
                                ...prev["clockWid"],
                                anaLog: !prev["clockWid"].anaLog
                            }
                        }));
                     }}>
                        <p></p>
                     </button>
                </div>
            </div>
        </>
    )
}