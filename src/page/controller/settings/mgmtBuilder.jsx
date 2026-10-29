import { toast } from "react-toastify";
import { database } from "../../../lib/globalState";
import { useEffect, useRef, useState } from "react";

export default function ContainerStructure ({crntData = {}}) {
    let {setDB} = database();
    const {name, searchWid} = crntData;
    const [builDerLocalData, setIntoLocalData] = useState(crntData);

    const inputRef = useRef(null);
    useEffect(()=>{
        // console.log(builDerLocalData);
        setDB({data:builDerLocalData,isGet:false})
    },[builDerLocalData]);

    const ToggleButton =  (key) => {
        if (!key || !key.trim()) return toast.error("Something went wrong");
        // console.log(builDerLocalData,key);
        setIntoLocalData(prev=>({
            ...prev,
            [key]:{
                ...prev[key],
                isVisible: !prev[key].isVisible
            }
        }));
    }

    const changeName =  (inp) => {
        let value = inp.value;
        if (!value || !value.trim()) return;
        
        setIntoLocalData(prev=>({
            ...prev,
            ["name"]:{
                ...prev["name"],
                username:value
            }
        }))
    }

    useEffect(()=>{
        if (!inputRef || inputRef=== null) return;
        let inp = inputRef.current;
        
        inp.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                changeName(e.target);
            }
        });
    },[])
    return(
        <>
            <p className="headingP">👋 Greeting & Search Box</p>

            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">🔍</div>
                    <div className="textHolder">
                        <p>Show search</p>
                        <span>Display Search Container</span>
                    </div>
                </div>
                <div className={`rightaSideC ${searchWid.isVisible ? "Active" : ""}`}>
                    <button onClick={()=>ToggleButton("searchWid")}>
                        <p/>
                    </button>
                </div>
            </div>
            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">👤</div>
                    <div className="textHolder">
                        <p>Display Name</p>
                        <span>Display Name</span>
                    </div>
                </div>
                <div className={`rightaSideC ${name.isVisible ? "Active" : ""}`}>
                    <button onClick={()=>ToggleButton("name")}>
                        <p/>
                    </button>
                </div>
            </div>

            <div className="inputDiv">
                <input ref={inputRef} type="text" placeholder={name.username} />
            </div>
        </>

    )
}