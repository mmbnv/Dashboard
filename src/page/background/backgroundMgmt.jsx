import { useEffect, useState } from "react";
import { database } from "../../lib/globalState";
import ImageBg from "./BG/imageBg";
import VideoBg from "./BG/videoBg";

export default function BackGround() {
    const data = database(stat=>stat.db?.background)
    const [blogUrl,setVideo] = useState(null);
    useEffect(() => {
        if (data.load != "custom") return;
        const request = indexedDB.open("chromeDB", 3222);
        let url;

        request.onsuccess = evnt => {
            const db = evnt.target.result;
            const tx = db.transaction("myDB", "readonly");
            const store = tx.objectStore("myDB");

            const getRequest = store.get("backgroundStuff");

            getRequest.onsuccess = () => {
            const blogVideo = getRequest.result;
            if (!blogVideo) return;

            url = URL.createObjectURL(blogVideo);
            setVideo(url);
            // console.log(url)
            };
        };

        return () => {
            if (blogUrl) URL.revokeObjectURL(blogUrl);
        };
    }, [data]);
    return(
        <div className="thornPrincess">
            {data?.type == "video" ? <VideoBg isBlur={data.isBlur} blogUrl={blogUrl}/> :
            <ImageBg isBlur={data?.isBlur} blogURL={blogUrl} />}
        </div>
    )
}