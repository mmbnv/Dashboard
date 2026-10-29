import { useEffect, useState } from "react";
import { Apps } from "../../../lib/globalState";
import { useScroll } from "framer-motion";
import InstallApp from "./AddNew";

export default function AppList () {
    const AllApps = Apps(stat=> stat.array) || [];
    const [myApps,setApps] = useState([]);
    const [inputVal,setVal] = useState("");
    const [isNew,setNew] = useState(false);

    const handleClick = url => {
        window.location.href=url;
    }

    useEffect(()=>{
        if (myApps.length !== 0) return;
        setApps(AllApps)
    },[AllApps]);

    const SearchFun =  (value) => {
      let filterList = AllApps.filter(app=> 
        app.name.toLowerCase().startsWith(value.toLowerCase())
      );
      setApps(filterList)
    }

    const SetDefault =  () => {
      setApps(AllApps);
    }

    useEffect(()=> {
      if (inputVal.length <= 2) return setApps(AllApps);
        SearchFun(inputVal);
    },[inputVal,AllApps]);


    const getIcon = (url) =>
    `https://www.google.com/s2/favicons?sz=512&domain_url=${encodeURIComponent(url)}`;

    

// console.log(getWebsiteName("https://github.com")); // github
// console.log(getWebsiteName("https://www.youtube.com")); // youtube

    return(
        <>
        {isNew && <InstallApp active={setNew} />}
        <div className="h-13 w-full  flex items-center justify-center">
            <div className="relative h-12 w-190">
  {/* Glow */}
  <div className="absolute inset-0 rounded-md bg-cyan-500/20 blur-md" />

  {/* Border */}
  <div className="absolute inset-0 rounded-md border border-cyan-400/40 bg-slate-950/80 backdrop-blur-sm" />

  {/* Top Accent */}
  <div className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-16 bg-cyan-400 shadow-[0_0_10px_#22d3ee]" />

  <div className="relative flex h-full items-center px-3">
    <svg
      className="w-4 h-4 text-cyan-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth="2"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M21 21l-4.35-4.35m1.85-5.15a7 7 0 11-14 0 7 7 0 0114 0z"
      />
    </svg>

    <input
      type="text"
      placeholder="Search..."
      value={inputVal}
      onChange={(evnt)=>setVal(evnt.target.value)}
      className="ml-2 w-full bg-transparent text-cyan-100 placeholder:text-cyan-500/60 outline-none text-sm"
    />

    <div className="flex gap-1 relative dropContainer h-2.5 cursor-progress">
      <span className="h-1 w-1 rounded-full bg-cyan-400" />
      <span className="h-1 w-1 rounded-full bg-cyan-400" />
      <span className="h-1 w-1 rounded-full bg-cyan-400" />
      
       <div className="innerDivSr absolute top-0 dropMenu -left-11 bg-black/40 rounded-lg backdrop-blur-lg w-25
      flex items-center flex-col gap-2.5 p-2.5">
        <ul className="flex items-strat flex-col gap-2.5 mt-1.5">
          <li onClick={()=>setNew(true)} className="border-b flex items-center justify-start text-gray-600 cursor-pointer"> <i className="bx bxl-android"></i> NewApps</li>
          <li className="border-b flex items-center justify-start text-gray-600 cursor-pointer"> <i className="bx bxs-trash"></i> Remove</li>
        </ul>
      </div>
    </div>
  </div>
</div>
        </div>
        <div className="h-9/10 w-full my-scroll grid gap-2 grid-cols-8 p-2.5 auto-rows-min auto-cols-min items-center justify-center">
            {
                myApps.map((app,index)=>(
                <div key={index} className="flex items-center flex-col gap-1.5 h-17 w-14 m-2">
                    <div onClick={()=>handleClick(app.url)} title={app?.name} className="allApps cursor-pointer flex hover:scale-105 items-center justify-center h-13 w-13 rounded-lg border border-cyan-400/30 bg-yellow-500/15">
                        <img src={getIcon(app.url)} className="h-4/5! w-4/5!" alt="" />
                    </div>
                    <span className="text-[8px]">{app.name}</span>
                </div>
                ))
            }
        </div>
        </>
    )
}