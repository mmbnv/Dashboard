import { toggler } from "../../lib/globalToggles";
import HandleBGUpload from "../../utils/Handlebg";
import ClockMgmt from "./components/clock/clockmgmt";
import SearchBar from "./components/searchBox";
import { useEffect, useState } from "react";
import DraggableWidget from "../../utils/dragDropHelper";
import { database } from "../../lib/globalState";
import BaseWeather from "./components/weather/baseComp";

export default function Widgets() {
  const toggleVideo = toggler((stat) => stat.toggleVideo);
  const toggleEdit = toggler(stat=> stat.toggleEdit)
  const { toggleTab } = toggler();
  const globData = database(stat=> stat.db)
  const {setDB} = database();
  let {clockWid, searchWid, weatherWid} = globData;

  const [data, setdata] = useState({clockWid, searchWid, weatherWid});

  useEffect(()=>{
    
    setDB({data,isGet:false})
  },[data])

  return (
    <div className="z-10 bg-transparent relative! h-screen w-screen">

      {toggleEdit && (
        <div
          onClick={() => toggleTab({ toggleEdit: false })}
          className="bg-white/20 flex items-center justify-center absolute top-0.5 left-[48%] cursor-pointer hover:bg:black/10 p-4 backdrop-blur-2xl rounded-full h-15 w-15"
        >
          <i className="bx bx-x text-2xl text-white"></i>
        </div>
      )}

     {searchWid.isVisible && <DraggableWidget 
        id="searchWid"
        position={data.searchWid.position}
        setdata={setdata}
        toggleEdit={toggleEdit}
     >
        <SearchBar />
     </DraggableWidget>}

     {clockWid.isVisible && <DraggableWidget
        id="clockWid"
        position={data.clockWid.position}
        setdata={setdata}
        toggleEdit={toggleEdit}
    >
        <ClockMgmt Obj={clockWid} />
    </DraggableWidget>}

    {weatherWid?.isVisible && <DraggableWidget
        id="weatherWid"
        position={data.weatherWid.position}
        setdata={setdata}
        toggleEdit={toggleEdit}
    >
      <BaseWeather API={weatherWid.apiKey} setData={setdata} />
    </DraggableWidget>}

      {toggleVideo && <HandleBGUpload />}
    </div>
  );
}

// function getFavicon(url) {
//   return `https://www.google.com/s2/favicons?domain=${url}`;
// }