import { data, input, pre } from "framer-motion/client";
import { useEffect, useState } from "react"
import { toast } from "react-toastify";

export default function FranApp ({crntList, setData}) {
    let {quickAcSetting, quickAcces} = crntList;
    const [builDerLocalData, setIntoLocalData] = useState(quickAcces);

    const getWebsiteName = (url) => {
        const hostname = new URL(url).hostname.replace(/^www\./, "")
        .split(".")[0];

        return hostname.charAt(0).toUpperCase() + hostname.slice(1)
        
    };

    const getIcon = (url) =>
    `https://www.google.com/s2/favicons?sz=512&domain_url=${encodeURIComponent(url)}`;

    const saveUrl =  (inp) => {
       
        let {name, value} = inp;
        if (value.trim().length < 4) {
            return toast.warning("Invalid URL")
        }

        let tempURL = value.trim();

        if (!/^https?:\/\//i.test(tempURL)) {
            tempURL = `https://${tempURL}`;
        }

        let isValidUrl;

        try {
            new URL(tempURL);
            isValidUrl = true;
        } catch {
            isValidUrl = false;
        }

        if (!isValidUrl) {
            return toast.error("Please check your URL");
        }

        let normalizedURL = new URL(tempURL).origin.toLocaleLowerCase();
        
        let exists = builDerLocalData.some(
            app => new URL(app.url).origin.toLocaleLowerCase() === normalizedURL
        )
        if (exists) {
            return toast.info("Url Already Marked");
        }
        let tempObj = {
            url: normalizedURL,
            name: getWebsiteName(normalizedURL)
        }

        setIntoLocalData(prev => {
            const copy = [...prev];
            copy[name] = tempObj;
            return copy;
        });

        
    }   

    useEffect(()=> {

        let tempObj = {
            quickAcces:builDerLocalData
        }

        setData({data: tempObj, isGet:false})
    },[builDerLocalData]);

    const changeTheme = () => {
        const theme = quickAcSetting.crntTheme === "light" ? "dark" : "light";

        let tempObj = {
           quickAcSetting:{
               ...quickAcSetting,
               crntTheme:theme
           }
       }
       setData({data: tempObj , isGet: false});
    };

    return(
        <>
            <p className="headingP">🤖 Home & Theme</p>

            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">🌙</div>
                    <div className="textHolder">
                        <p>Toggle Theme</p>
                    <span>Click the button to toggle</span>
                    </div>
                </div>

                <div className="rightaSideC">
                    <div className="h-9 w-9 bg-blue-500/10 rounded-lg overflow-hidden">
                        <div onClick={changeTheme} className={`h-9 w-15 rounded-md flex gap-3 items-center justify-center duration-400 transition-all ease-in-out cursor-pointer 
                            ${quickAcSetting.crntTheme === "light" ? "-translate-x-7.5" : "translate-x-2"}`}>
                            <i className="text-2xl pointer-events-none bx bxs-moon text-blue-400!"></i>
                            <i className="text-2xl pointer-events-none bx bxs-sun text-amber-400!"></i>
                        </div>
                    </div>
                </div>
                
            </div>
            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">🤖</div>
                    <div className="textHolder">
                        <p>Featch From History</p>
                        <span>Show frequently acceded site</span>
                    </div>
                </div>

                <div className={`rightaSideC ${quickAcSetting.isFrequently ? "Active" : ""}`}>
                    <button onClick={()=>{
                        let tempObj = {
                            quickAcSetting:{
                                ...quickAcSetting,
                                isFrequently:!quickAcSetting.isFrequently
                            }
                        }
                        setData({data: tempObj , isGet: false})
                    }}>
                        <p></p>
                    </button>
                </div>

            </div>
            <div className="controlleBox">
                <div className="leftaSideC">
                    <div className="iconCon">🤖</div>
                    <div className="textHolder">
                        <p>Display Quick Access</p>
                        <span>Show Popular Wesite on home</span>
                    </div>
                </div>

                <div className={`rightaSideC ${quickAcSetting.showQuickApps ? "Active" : ""}`}>
                    <button onClick={()=>{
                        let tempObj = {
                            quickAcSetting:{
                                ...quickAcSetting,
                            showQuickApps:!quickAcSetting.showQuickApps
                            }
                        }
                        setData({data: tempObj , isGet: false})
                    }}>
                        <p></p>
                    </button>
                </div>

            </div>

            {
               !quickAcSetting.isFrequently && builDerLocalData.map((obj,index)=>(
                    <div key={index} className="controlleBoxA flex items-center flex-row gap-2">
                        <div className="imgHolder h-full flex-1 flex items-center justify-center">
                            <img src={getIcon(obj.url)} className="h-10! w-10!" alt="" />
                        </div>
                        <div className="inputHolder flex-5 flex items-center flex-row gap-2">
                            <input type="text" name={index.toString()} placeholder={obj.url} className="border-2 border-gray-400/10 h-10 rounded-lg p-2.5 w-4/5 placeholder:text-gray-500" />
                            <button onClick={(evnt)=>{
                                let input = evnt.target.previousElementSibling;
                              
                                saveUrl(input);
                            }} className="p-2.5 rounded-md border border-amber-50/40 bg-blue-700 hover:bg-blue-800 cursor-pointer"><i className="bx bx-save pointer-events-none"></i></button>
                        </div>
                    </div>
                ))
            }
            
        </>
    )
}