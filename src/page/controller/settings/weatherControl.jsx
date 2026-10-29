import { useEffect, useRef, useState } from "react"
import { database } from "../../../lib/globalState";

export default function WeatherColtroller ({crntData, setData}) {
    let {weatherWid} = crntData;
    
    const [builDerLocalData, setIntoLocalData] = useState(crntData);
    const cityInputRef = useRef(null);
    const keyInputRef = useRef(null);

    const upDatebase =  (inp) => {
            let value = inp.value;
            let key = inp.name;
            // console.log(inp);
            if (!value || !value.trim()) return;
            console.log({[key]:value});
            setIntoLocalData(prev=>({
                ...prev,
                ["weatherWid"]:{
                    ...prev["weatherWid"],
                    [key]:value
                }
            }))
        }
    
        useEffect(()=>{
            if (!cityInputRef || cityInputRef=== null || !keyInputRef || !keyInputRef === null) return;
            let cityInp = cityInputRef.current;
            let keyInp = keyInputRef.current
            
            cityInp.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    upDatebase(e.target);
                }
            });

            keyInp.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    upDatebase(e.target);
                }
            });
        },[]);

        useEffect(()=>{
            setData({data:builDerLocalData, isGet:false});
        },[builDerLocalData]);
    return(
        <>
            <p className="headingP">🌤️ Weather</p>

            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">🌨️</div>
                    <div className="textHolder">
                        <p>Show Weather</p>
                        <span>Display weather card</span>
                    </div>
                </div>

                <div className={`rightaSideC ${weatherWid.isVisible ? "Active" : ""}`}>
                    <button onClick={()=>{
                        setIntoLocalData(prev=>({
                            ...prev,
                            ["weatherWid"]:{
                                ...prev["weatherWid"],
                                isVisible: !prev["weatherWid"].isVisible
                            }
                        }))
                    }}>
                        <p></p>
                    </button>
                </div>
            </div>
            <div className="controlleBox justify-start! border-none!">
                <div className="leftaSideC">
                    <div className="iconCon">🗝️</div>
                    <div className="textHolder">
                        <p>Enter your OpenWeather key</p>
                        <span>Display weather card</span>
                    </div>
                </div>
                <div className="rightSideC">
                    <a className="text-sm text-blue-600! hover:text-blue-300!" href="https://www.youtube.com/watch?v=FWuRLS_wmWY">🗝️Get key</a>
                </div>
            </div>
            <div className="inputDivBtn">
                <input ref={keyInputRef} name="apiKey" type="text" placeholder={weatherWid.apiKey.length>0 ? "**********" : ""} />
                <button onClick={(evnt)=>{
                    let input = evnt.target.previousElementSibling;
                    upDatebase(input);
                }}>Save</button>
            </div>

            <div className="controlleBox justify-start! border-none!">
                <div className="leftaSideC">
                    <div className="iconCon">📍</div>
                    <div className="textHolder">
                        <p>Enter your city name</p>
                        <span>Fetch Weather for your city</span>
                    </div>
                </div>

            </div>
            <div className="inputDivBtn">
                <input ref={cityInputRef} name="city" placeholder={weatherWid.city} type="text" />
                <button onClick={(evnt)=>{
                    let input = evnt.target.previousElementSibling;
                    upDatebase(input);
                }}>Save</button>
            </div>
        </>
    )
}