import { useEffect } from "react";
import { database, useTabToggle } from "../lib/globalState"
import BackGround from "./background/backgroundMgmt";
import Controller from "./controller/mainController";
import Widgets from "./widgets/mainHandler";
import MainBookmark from "./controller/mainBookmark";
import AllAps from "./widgets/Homeaps/homeAll";
import AppList from "./widgets/Homeaps/apsList";
import AbsIcons from "./widgets/Homeaps/abIcons";
import { toggler } from "../lib/globalToggles";
export default function NewTab() {
    const {showQuickApps} = database(stat=>stat.db.quickAcSetting);
    const tabsObj = useTabToggle(stat => stat.tabObj);
    const isBookTab = toggler(stat=>stat.toggleBookmarks);
    let {toggleTabs} = useTabToggle();
    
    return(
        <div className="underTaker">
            <BackGround/>
            <Controller />
            <Widgets />
            <MainBookmark/>
            {(!isBookTab && showQuickApps) && <AllAps/>}
            <AbsIcons/>

            {tabsObj.allApps && <div className="thornPrincess inCommingAnim flex items-center justify-center bg-blue-600/15 backdrop-blur-lg z-20">
                <div className="underTaker">
                    <button onClick={()=>toggleTabs("")} className="flex absolute top-2.5 right-2.5 items-center justify-center p-2.5 hover:bg-gray-500/25 hover:rotate-180 duration-300 transition-all cursor-pointer text-red-500! font-bold text-2xl rounded-full">
                        X
                    </button>

                    <div className="innerContainer-forApp h-5/7 w-210 bg-black/30 rounded-lg shadow">
                        <AppList/>
                    </div>
                </div>
            </div>}

        </div>
    )
}