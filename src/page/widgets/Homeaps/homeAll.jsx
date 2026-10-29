import { useEffect, useState } from "react";
import { database, useTabToggle } from "../../../lib/globalState"

export default function AllAps() {
    const quickAc = database(stat=> stat.db.quickAcces || []);
    const isFrequently = database(stat => stat.db.quickAcSetting?.isFrequently || false);
    let {toggleTabs} = useTabToggle();
    const [frequentlyArr, setArr] = useState([]);

    const handleClick = url => {
        window.location.href=url;
    }

    const getWebsiteName = (url) => {
        const hostname = new URL(url).hostname.replace(/^www\./, "")
        .split(".")[0];

        return hostname.charAt(0).toUpperCase() + hostname.slice(1)
        
    };

    const fetchTopSites = async () => {
        let topSite = await chrome.topSites.get();
        let tempArr = []
        topSite.slice(0, 3).forEach(obj => {
            let tempObj = {
                name:getWebsiteName(obj.url),
                url:obj.url
            }
            tempArr.push(tempObj);
        });
        setArr(tempArr);
        console.log(tempArr);
    }

    useEffect(()=>{
        if (isFrequently) {
            fetchTopSites();
        }
    },[isFrequently]);
    

     return (
        <div className="h-18 w-70 rounded-lg allApps overflow-hidden blurBg absolute bottom-7 z-20 myShadow">
            <div className="underTaker justify-start!">
                <div onClick={()=>toggleTabs("allApps")} title="All Apps" className="miniIconDiv p-2 cursor-pointer border border-white/25 bg-gray-500/50 ml-3.5 rounded-md">
                    <i className="bx bxs-dashboard text-3xl transition-all duration-300"></i>
                </div>
                <span className="m-2 text-gray-500/50! text-2xl">|</span>
                <div className="quickAccessH h-full w-48 flex items-center justify-center gap-2.5">
                    {
                       isFrequently ? frequentlyArr.map((app, i)=>(
                        <div key={i} onClick={()=> handleClick(app.url)} title={app?.name} className="allApps cursor-pointer flex hover:scale-105 items-center justify-center h-13 w-13 rounded-lg border border-white/25 bg-blue-500/30" >
                            <img src={`https://www.google.com/s2/favicons?domain=${app.url}`} className="h-4/5! w-4/5!" alt="" />
                        </div>
                       )) : quickAc.map((app,index)=>(
                            <div key={index} onClick={()=>handleClick(app.url)} title={app?.name} className="allApps cursor-pointer flex hover:scale-105 items-center justify-center h-13 w-13 rounded-lg border border-white/25 bg-blue-500/30">
                                <img src={`https://www.google.com/s2/favicons?domain=${app.url}`} className="h-4/5! w-4/5!" alt="" />
                            </div>
                        ))
                    }
                </div>
            </div>
        </div>
     )
}