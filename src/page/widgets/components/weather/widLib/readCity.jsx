
import { database } from "../../../../../lib/globalState"
import { toast } from "react-toastify";

export default function AskCity({crntData}) {
    let {setDB} = database();
    

    const handleName = async (evnt) => {
        evnt.preventDefault();
        const formData = new FormData(evnt.target);
        const {key} = Object.fromEntries(formData);
        let rkv = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${key}&appid=${crntData.apiKey}&units=metric`);
        let tempData = await rkv.json();
        console.log(tempData);
        if (tempData.cod !== 200) {
            return toast.error("City Not Found");
        }

        let conctructure = {...crntData, city:key}
        let data = {weatherWid:conctructure}
        setDB({data, isGet:false});
    }

    return(
        <div className="underTaker flex-col gap-6 blurBg bg-blue-500/20">
            <p className="font-bold text-2xl">Enter Your City</p>
            <form action="" onSubmit={handleName} className="p-1 flex items-center flex-col" >
                <div className="flex items-center flex-row p-1 w-full gap-5 relative">
                   
                    <input name="key" type="text" placeholder="City" className={`p-1 w-50 pl-2.5 border rounded-lg 
                      `} /> 

                    <button type="submit" className="bg-green-500 text-white font-bold p-1.5 rounded-lg cursor-pointer hover:bg-green-600">Save</button>
                </div>
            </form>
        </div>
    )
}