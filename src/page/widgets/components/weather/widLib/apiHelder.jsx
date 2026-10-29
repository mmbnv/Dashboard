import { useState } from "react"
import { database } from "../../../../../lib/globalState";
import { toast } from "react-toastify";

export default  function WeatherAPI({setData}) {
    const [result, setResult] = useState({
        isResult:false,
        isTrue:false
    })
    

    const handleKey = async (evnt) => {
        evnt.preventDefault();
        let formData = new FormData(evnt.target);
        let {key} = Object.fromEntries(formData);
        let timeOut;
        try {
            let rkv = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=DELHI&appid=${key}&units=metric`)
            let data = await rkv.json();
            console.log(data)
            if (data.cod === 200) {
                setResult({isResult:true, isTrue: true})
                timeOut = setTimeout(() => {
                    setData(prev=>({
                        ...prev,
                        "weatherWid":{
                            ...prev["weatherWid"],
                            apiKey:key
                        }
                    }));
                    clearTimeout(timeOut);
                }, 1000);
            } else {
                throw new Error(data.message);
                
            }
        } catch (error) {
            toast.warning(error.message)
        }
    }
    return(
        <div className="underTaker bg-gray-700 gap-1.5 rounded-lg flex-col!">
            <p className="font-bold text-2xl">Please Create an API key</p>
            <p className="flex items-center justify-center p-1">
                <i className="bx bxl-youtube text-3xl text-red-600!"></i>
                <a href="https://www.youtube.com/watch?v=FWuRLS_wmWY">Click Here</a>
            </p>
            <form action="" className="p-1 flex items-center flex-col" onSubmit={handleKey}>
                <div className="flex items-center flex-row p-1 w-full gap-2.5 relative">
                    {result?.isResult && result?.isTrue && <i className="bx bx-check absolute left-3/5 text-green-500! font-bold text-2xl"></i>}
                    <input name="key" type="text" placeholder="API Key" className={`p-1 w-50 pl-2.5 border rounded-lg 
                        ${(result?.isResult && result?.isTrue) ? "border-green-600" : (!result?.isResult && result?.isTrue) ? "border-red-600" : ""}`} /> 

                    <button type="submit" className="bg-green-500 text-white font-bold p-1.5 rounded-lg cursor-pointer hover:bg-green-600">Check</button>
                </div>
            </form>
        </div>
    )
}