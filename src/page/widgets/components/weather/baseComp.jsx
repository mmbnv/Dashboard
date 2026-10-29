import WeatherAPI from "./widLib/apiHelder";
import WeatherCard from "./widLib/weatherCard";

export default function BaseWeather({API, setData}) {
    
    return(
        <div className="relative h-80 w-110">
            {API.length === 0 ? <WeatherAPI setData={setData}/> : <WeatherCard/>}
        </div>
    )
}