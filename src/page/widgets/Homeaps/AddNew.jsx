import { useState } from "react";
import { toast } from "react-toastify";
import { Apps } from "../../../lib/globalState";

export default function InstallApp ({active}) {
    const [appURl,setURL] = useState("");
    let {setApp} = Apps();
    const AllApps = Apps(stat=> stat.array) || [];

function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

const getWebsiteName = (url) => {
    const hostname = new URL(url).hostname.replace(/^www\./, "")
      .split(".")[0];

      return hostname.charAt(0).toUpperCase() + hostname.slice(1)
      
};


const InstallNewApp = () => {
  if (appURl.trim().length < 4) {
    return toast.warning("Invalid URL");
  }

  let tempURL = appURl.trim();

  if (!/^https?:\/\//i.test(tempURL)) {
    tempURL = `https://${tempURL}`;
  }

  if (!isValidUrl(tempURL)) {
    return toast.error("Check Your URL");
  }

  const normalizedURL = new URL(tempURL).origin.toLowerCase();

  const exists = AllApps.some(
    app => new URL(app.url).origin.toLowerCase() === normalizedURL
  );

  if (exists) {
    return toast.info("Already Installed");
  }

  const obj = {
    url: normalizedURL,
    name: getWebsiteName(normalizedURL),
  };

  setApp({newApp:obj,isGet:false});

  toast.success("Done");
  active(false)
};

    return(
        <div className="thornPrincess left-0 bg-gray-600/40 backdrop-blur-2xl">
            <div className="underTaker">
                <div className="h-1/4 relative bg-gray-500/40 border border-cyan-500 translate-y-4 rounded-lg w-100">
                    <p onClick={()=>active(false)} className="absolute hover:scale-95 cursor-pointer -top-2 -right-2 text-red-500! font-bold text-2xl">x</p>
    <div
      className="
        w-full
        h-full
        rounded-3xl
        border border-white/10
        bg-black/30
        backdrop-blur-xl
        p-5
        flex
        flex-col
        justify-between
      "
    >
      {/* Loader */}
      <div className="flex justify-center gap-2 pt-2">
        <span className="w-2 h-2 rounded-full bg-yellow-500! animate-bounce" />
        <span
          className="w-2 h-2 rounded-full bg-yellow-500! animate-bounce"
          style={{ animationDelay: "150ms" }}
        />
        <span
          className="w-2 h-2 rounded-full bg-yellow-500! animate-bounce"
          style={{ animationDelay: "300ms" }}
        />
      </div>

      {/* Input */}
        <p>
            Please Enter the URL....
        </p>
      <div className="flex justify-center">
        <input
          type="url"
          value={appURl}
          onChange={(evnt)=>setURL(evnt.target.value)}
          placeholder="Enter website URL..."
          className="
            w-full
            h-12
            rounded-2xl
            px-4
            bg-white/5
            border
            border-white/30
            text-white
            placeholder:text-white/40
            outline-none
            focus:border-cyan-400/50
            focus:bg-white/10
            transition-all
          "
        />
      </div>

      {/* Button */}
      <button onClick={InstallNewApp}
        className="
          h-12
          cursor-pointer
          rounded-2xl
          font-semibold
          text-white
          bg-cyan-500/20
          border
          border-cyan-400/30
          hover:bg-cyan-500/30
          active:scale-[0.98]
          transition-all
        "
      >
        Install
      </button>
    </div>
  );

                </div>
            </div>
        </div>
    )
}