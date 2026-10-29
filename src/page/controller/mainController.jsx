import { useState } from "react";
import { toggler } from "../../lib/globalToggles"
import { icons } from "lucide-react";

export default function Controller({settings}) {
    const [toggleTool, setTT] = useState(false);
    let {toggleTab} = toggler();
    const handleBg = ()=>{
        toggleTab({toggleVideo:true})
    }
    const items = [
        { icon: "bx-edit", onClick: () => toggleTab({ toggleEdit: true }) },
        { icon: "bxl-github", onClick: () => window.open("https://github.com/Freak644", "_blank") },
        { icon: "bx-image", onClick: handleBg },
        { icon: "bxs-bookmark-heart", onClick: () => toggleTab({toggleBookmarks:true})},
        
    ];
    return(
        <div id="controlPanel" className={`z-20 ${toggleTool && "active"}`}>
            <div className="control-panel">
                
                <p onClick={()=>setTT(prev=>!prev)} className="blurBg"><i>🛠️</i> <span>Tool</span></p>
                
                {items.map((item, i) => (
                    <button
                        key={i}
                        value={"2"}
                        className={`orbit-item ${toggleTool && "blurBg"}`}
                        style={{ "--i": i }}
                        onClick={item.onClick}
                    >
                        <i className={`bx ${item.icon} text-lg pointer-events-none`} />
                    </button>
                ))}
            </div>
        </div>
    )
}

