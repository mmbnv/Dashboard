import { useEffect, useRef, useState } from "react"
import {motion, scale} from 'framer-motion';
import {toast} from 'react-toastify';
import {useDropzone} from 'react-dropzone';
import {Upload} from 'lucide-react';
import { toggler } from "../lib/globalToggles";
import { database } from "../lib/globalState";
export default function HandleBGUpload() {
    const [background,setBackground] = useState({
        objUrl:"",
        file:null,
        isBlur:false,
        bgType:""
    });

    const containerRef = useRef(null);
    let {toggleTab} = toggler();
    const tVData = toggler(stat=>stat.toggleVideo);

    let {setDB} = database();

    const checkVideoDuration = (file) => {
        return new Promise((resolve, reject) => {

            const video = document.createElement("video");
            video.preload = "metadata";

            video.onloadedmetadata = () => {
                URL.revokeObjectURL(video.src);

                if (video.duration > 60) {
                    reject("video is too long, 30second is the limit");
                } else {
                    resolve(true);
                }
            };

            video.src = URL.createObjectURL(file);
        });
    };


    const onDrop = async (acceptedFiles) => {
        let file = acceptedFiles[0]
        if (!file) return toast.info("File! Not Found");
        let crntFileType = file.type.split("/")[0];
        console.log(crntFileType)

        if (crntFileType === "video") {
             try {
                   await checkVideoDuration(file);
               } catch(err) {
                   return toast.error(err);
               }
        }

  
   
        setBackground(prev=>({
            ...prev,
            objUrl:URL.createObjectURL(file),
            file,
            bgType:crntFileType
        }));
     
    }

    const {getRootProps,getInputProps,isDragActive} = useDropzone({
        onDrop,
        multiple:false,
        maxSize: 150 * 1024 * 1024,
        accept:{
            "video/*":[],
            "image/*":[]
        }
    })

    
    useEffect(() => {
        if (!containerRef) return;
        const tab = containerRef.current;

        const handleClick = (event) => {
            let traget = event.target.value;
            // console.log(traget);
            if (tab && !tab.contains(event.target) && traget != "null" && traget != 2) {
                    toggleTab({ toggleVideo: false });
                    URL.revokeObjectURL(background.objUrl);
                    setBackground({
                        objUrl:"",
                        file:null,
                        isBlur:false
                    })
            }
        };
        
        document.addEventListener("click", handleClick);
        
        return () => {
            document.removeEventListener("click", handleClick);
        };
    }, [tVData]);

    const saveTheVideo = () => {

        if (!background.file) {
            return toast.info("Not Found! please try again");
        }

        const request = indexedDB.open("chromeDB", 3222);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            if (!db.objectStoreNames.contains("myDB")) {
                db.createObjectStore("myDB");
            }
        };

        request.onerror = () => {
            console.error("IndexedDB error");
        };

        request.onsuccess = (event) => {
            const db = event.target.result;

            const tx = db.transaction("myDB", "readwrite");
            const store = tx.objectStore("myDB");

            store.put(background.file, "backgroundStuff");

            tx.oncomplete = () => {
                toast.success("✅ Video Saved!");
                db.close();
            };

            tx.onerror = () => {
                toast.warning("Transaction failed");
            };
        };
        let data = {
            "background":{
                "load":"custom",
                "type":background.bgType,
                "isBlur":background.isBlur
            }
        }

        setDB({data,isGet:false})

        URL.revokeObjectURL(background.objUrl);
        setBackground({
            objUrl:"",
            file:null,
            isBlur:false
        })
        toggleTab({ toggleVideo: false });
    };

    return(
        <div ref={containerRef} className="h-6/10 w-5/10 flex items-center justify-center absolute left-1/4
        bg-black/20 backdrop-blur-2xl rounded-lg top-1/5
        ">
            {background.file === null ? <div className="notvideo h-8/10 w-8/10 blurBg flex relative items-start justify-center p-2">
                <motion.div
                    {...getRootProps()}
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    whileHover={{ scale: 1.02 }}
                    className={`border-2 flex flex-col items-center border-dashed rounded-2xl p-10 w-full max-w-xl cursor-pointer text-center transition-all duration-300
                        ${
                        isDragActive
                            ? "border-cyan-400/80 bg-black/40 shadow-[0_0_25px_-8px_rgba(6,182,212,0.6)]"
                            : "border-gray-700 bg-[#000000a5] hover:border-cyan-400/40 hover:bg-black/80"
                        }`}
                    >
                    <input {...getInputProps()} accept="video/*,image/*" />

                    <motion.div
                        animate={{ y: isDragActive ? -6 : 0 }}
                        transition={{ type: "spring", stiffness: 200 }}
                        className="flex flex-col items-center gap-3"
                    >
                        <Upload className="text-cyan-400 w-full h-40 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]" />
                        <p className="text-gray-300 text-lg font-medium">
                        {isDragActive
                            ? "Drop files here"
                            : "Drag & drop or click to browse"}
                        </p>
                        <p className="text-sm text-gray-500">Max size Limit for Video 150MB</p>
                    </motion.div>
                </motion.div>
                
            </div> : 
            
            <div  className="afterSelected h-8/10 w-9/10 p-2 relative">
                {background.bgType === "video" ? <video className="h-full w-full rounded-lg object-cover z-1! relative" autoPlay muted loop>
                    <source type="video/mp4" src={background?.objUrl} />
                </video> : <div className="h-full w-full rounded-lg object-cover z-1! relative"><img src={background?.objUrl} alt="" /></div>}
                {background.isBlur && <div className="blurBg z-2! h-full w-full absolute top-0 left-0"></div>}
                <button id="btn" onClick={()=>setBackground(prev=>({
                    ...prev,
                    isBlur: !prev.isBlur
                }))} className="miniController z-2! h-10 w-25 rounded-lg bg-size-[200%_200%] hover:bg-position-[100%_150%]  transition-all duration-700 ease-in-out
                absolute bottom-0 right-30 overflow-hidden bg-linear-to-l cursor-pointer from-blue-600/50 via-pink-600/50 to-sky-600/50 btn backdrop-blur-2xl">
                    <div className="text-lg h-full w-full font-semibold">
                        <span>Blur</span> <i>BG</i>
                    </div>
                </button>

                <button id="btn" onClick={saveTheVideo} className="miniController z-2! h-10 w-25 rounded-lg bg-size-[200%_200%] hover:bg-position-[100%_150%]  transition-all duration-700 ease-in-out
                absolute bottom-0 right-0 overflow-hidden bg-linear-to-r cursor-pointer from-blue-500 via-pink-500 to-green-600 btn">
                    <div className="text-lg h-full w-full font-bold"><span>Upload</span> <i className="bx bx-upload"></i> </div>
                </button>

                <button id="btn" onClick={()=>{
                    URL.revokeObjectURL(background.objUrl);
                    setBackground({
                        objUrl:"",
                        file:null,
                        isBlur:false
                    })
                }} className="miniController z-2! h-10 w-20 rounded-lg 
                absolute bottom-0 left-0 overflow-hidden bg-red-400 font-semibold hover:bg-red-500 cursor-pointer ">
                    Clear
                </button>
            </div>}
            <i onClick={()=>toggleTab({ toggleVideo: false })} className="bx bx-x font-bold text-2xl absolute top-2.5 right-2.5 text-rose-500! cursor-pointer"></i>
        </div>
    )
}