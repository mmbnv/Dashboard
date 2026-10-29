import { useEffect, useRef, useState } from "react"
import ContainerHolder from "../../controller/settings/ContainerHolder";

export default function AbsIcons () {
    const [isTrue, setTrue] = useState(false);

    const containerRef = useRef(null);
    const iconRef = useRef(null);


    useEffect(() => {
        const handleClick = (event) => {
            const slider = containerRef.current;
            const icon = iconRef.current;

            if (!slider || !icon) return;

            if (
                !slider.contains(event.target) &&
                !icon.contains(event.target)
            ) {
                setTrue(false);
            }
        };

        window.addEventListener("click", handleClick);

        return () => {
            window.removeEventListener("click", handleClick);
        };
    }, []);

    return(
        <>
        
            <div ref={iconRef} onClick={()=>setTrue(prev=>!prev)} className="setingIcon h-13 w-13 border bg-purple-600/10 cursor-pointer backdrop-blur-2xl border-white/10 rounded-lg top-2.5 right-1/100 z-20 absolute
            flex items-center justify-center" >
                <i className="bx bx-cog text-2xl font-normal duration-300 "></i>
            </div>

            { isTrue && 
                    <div className="thornPrincess z-20 bg-black/60">
                        <div ref={containerRef} className={`setingSlider cameIn absolute backdrop-blur-lg bg-black/30 overflow-hidden rounded-lg h-screen w-1/4
                            shadow-2xl shadow-white/80 opacity-20 -right-25`}>
                                <div className="underTaker">
                                    <div className="sticky top-0 h-1/10 border-b w-full border-gray-600/40 
                                    flex items-center justify-between p-4">
                                        <p className="font-bold text-2xl">⚙️ Settings</p>
                                        <div onClick={()=> setTrue(false)} className="h-10 rounded-full bg-gray-500/40 hover:rotate-90 hover:bg-red-500/40 hover:scale-90 border border-white/50 duration-200 cursor-pointer w-10 flex items-center justify-center">
                                            <i className="bx bx-x"></i>
                                        </div>
                                    </div>
                                    <div className="h-9/10 border border-blue-500 relative  w-full p-3 my-scroll flex gap-2.5 flex-col">
                                        <ContainerHolder />
                                    </div>
                                </div>
                        </div>
                        
                    </div>
            }
        </>
    )
}