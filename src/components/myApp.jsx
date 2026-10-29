import { useEffect, useState } from "react";
import NewTab from "../page/newTab";
import { Apps, database } from "../lib/globalState";
import { useTaskStore } from "../lib/tasksStore";
import { useNotesStore } from "../lib/notesStore";
import '../assets/style/pasesTwo.css'


export default function MyApp() {
    let {setDB} = database();
    const crntTheme = database(stat=>stat.db.quickAcSetting.crntTheme);
    let {setApp} = Apps();
    let [isReady, setReady] = useState(false);
    const hydrateTasks = useTaskStore(stat => stat.hydrate);
    const hydrateNotes = useNotesStore(stat => stat.hydrate);

    useEffect(() => {
            Promise.all([hydrateTasks(), hydrateNotes()]);

            if (typeof chrome !== "undefined" && chrome.storage?.local) {
                chrome.storage.local.get(["db", "appList"], (data) => {

                    if (data?.db && Object.keys(data.db).length > 0) {
                        setDB({
                            data: data.db,
                            isGet: true
                        });
                    }

                    if (Array.isArray(data?.appList) && data.appList.length > 0) {
                        setApp({
                            newApp: data.appList,
                            isGet: true
                        });
                    }
                });
            } else {
                const savedDB = JSON.parse(
                    localStorage.getItem("Saved") || "{}"
                );

                const appList = JSON.parse(
                    localStorage.getItem("appList") || "[]"
                );

                if (Object.keys(savedDB).length > 0) {
                 
                    setDB({
                        data: savedDB,
                        isGet: true
                    });
                }

                if (appList.length > 0) {
                    setApp({
                        newApp: appList,
                        isGet: true
                    });
                }
            }

            setReady(true)
        }, []);

        useEffect(()=>{
            document.documentElement.setAttribute("data-theme", crntTheme);
        },[crntTheme]);
    return(
        <>
        {
            isReady ? <NewTab/> : <div className="miniLoader"/>
        }
        </>
    )
}