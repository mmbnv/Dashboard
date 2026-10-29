import { useEffect, useState } from "react";
import NewTab from "../page/newTab";
import { Apps, database } from "../lib/globalState";
import { useTaskStore } from "../lib/tasksStore";
import { useNotesStore } from "../lib/notesStore";
import { registerServiceWorker, storageGet } from "../lib/platform";
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

            storageGet(["db", "appList"]).then((data) => {
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

                setReady(true);
            });

            registerServiceWorker();
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