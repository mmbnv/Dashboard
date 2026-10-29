import { useEffect, useMemo, useState } from "react"
import { database } from "../../../../../lib/globalState";
import AskCity from "./readCity";
import CursorImg from '../../../../../assets/cursor.png';
import windGif from '../../../../../assets/WindGif.gif';

export default function WeatherCard() {
    const myData = database(stat=> stat.db?.weatherWid);
    
    let [weatherData,setData] = useState({});

    const featchWeather = async (city, api_key) => {
        if (Object.keys(weatherData).length !== 0) return;
        let rqst = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${api_key}&units=metric`)
        let data = await rqst.json();
        // console.log(data)
        setData(data);
    }


    useEffect(() => {
        if (!myData.city || Object.keys(weatherData).length !== 0) return;

        const { city, apiKey } = myData;

            featchWeather(city, apiKey);

        return () => clearInterval(interval);
    }, [myData, weatherData]);

    const getDirection = () => {
        const deg = weatherData?.wind?.deg;
        if (deg == null) return "";

        const directions = ["N","NE","E","SE","S","SW","W","NW"];
        const index = Math.round(((deg % 360) + 360) % 360 / 45) % 8;

        return directions[index];
    };

    const getWeatherGradient = (weatherMain) => {
        switch (weatherMain) {
            case "Clear":
            return "from-sky-300/10 via-blue-500/10 to-blue-700/10";

            case "Clouds":
            return "from-slate-300/10 via-slate-500/10 to-slate-750/10";

            case "Rain":
            case "Drizzle":
            return "from-slate-500/10 via-slate-700/10 to-black/10";

            case "Thunderstorm":
            return "from-purple-500/10 via-slate-700/10 to-black/10";

            case "Snow":
            return "from-sky-200/10 via-slate-300/10 to-slate-500/10";

            case "Mist":
            case "Fog":
            case "Haze":
            return "from-gray-300/10 via-slate-500/10 to-slate-700/10";

            default:
            return "from-slate-300 via-slate-500 to-slate-950";
        }
        };

        const gradientClass = useMemo(() => {
            return getWeatherGradient(weatherData?.weather?.[0]?.main);
        }, [weatherData]);

    return(
        <div className="p-1">
            {myData?.city.length === 0 ? <AskCity crntData={myData} /> :
            <>
                {Object.keys(weatherData).length === 0 ? <div className="loader"></div> :
                <>
                <div
                    className={`
                        relative
                        overflow-hidden
                        rounded-3xl
                        p-4
                        h-full
                       
                        bg-linear-to-br
                        ${gradientClass}
                       
                        backdrop-blur-lg
                        shadow-2xl
                    `}
                    >
                    {/* Background Glow */}
                    <div
                        className="
                        absolute
                        h-40
                        w-40
                        rounded-full
                        bg-blue-400/20
                        blur-lg
                        -bottom-10
                        right-0
                        pointer-events-none
                        "
                    />

                    {/* Top Section */}
                    <div className="relative flex items-start flex-row gap-7">
                        <div className="flex items-center gap-3">
                        <img
                            src={`https://openweathermap.org/img/wn/${weatherData.weather[0].icon}@2x.png`}
                            className="w-20 h-20 drop-shadow-lg"
                            alt=""
                        />

                        <div>
                            <h1 className="text-5xl font-black leading-none">
                            {Math.round(weatherData.main.temp)}
                            <span className="text-xl align-top">°C</span>
                            </h1>

                            <p className="text-xs text-white/60 mt-1">
                            Feels like {Math.round(weatherData.main.feels_like)}°C
                            </p>
                        </div>
                        </div>

                        <div className="text-right">
                        <p className="font-bold text-xl">
                            📍 <span className="neonTxt">{weatherData.name}</span>
                        </p>

                        <p className="text-sm tracking-wider uppercase text-white/70">
                            {weatherData.weather[0].description}
                        </p>
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="h-px bg-white/10 my-5" />

                    {/* Bottom Stats */}
                    <div className="grid grid-cols-3 gap-3">
                        {/* Wind */}
                        <div
                        className="
                            bg-white/10
                            backdrop-blur-md
                            rounded-2xl
                            p-3
                            flex
                            flex-col
                            items-center
                        "
                        >
                        <p className="text-xs text-white/60 uppercase">
                            Wind
                        </p>

                        <img
                            src={CursorImg}
                            className="w-10! h-10! my-2"
                            style={{
                            transform: `rotate(${weatherData.wind.deg}deg)`
                            }}
                            alt=""
                        />

                        <span className="font-bold">
                            {getDirection()}
                        </span>

                        <span className="text-xs text-white/70">
                            {weatherData.wind.speed} m/s
                        </span>
                        </div>

                        {/* Humidity */}
                        <div
                        className="
                            bg-white/10
                            backdrop-blur-md
                            rounded-2xl
                            p-3
                            flex
                            flex-col
                            justify-center
                            items-center
                        "
                        >
                        <p className="text-xs text-white/60 uppercase">
                            Humidity
                        </p>

                        <span className="text-3xl mt-2">
                            💧
                        </span>

                        <span className="font-bold text-lg">
                            {weatherData.main.humidity}%
                        </span>
                        </div>

                        {/* Pressure */}
                        <div
                        className="
                            bg-white/10
                            backdrop-blur-md
                            rounded-2xl
                            p-3
                            flex
                            flex-col
                            justify-center
                            items-center
                        "
                        >
                        <p className="text-xs text-white/60 uppercase">
                            Pressure
                        </p>

                        <span className="text-3xl mt-2">
                            🌡️
                        </span>

                        <span className="font-bold text-lg">
                            {weatherData.main.pressure}
                        </span>

                        <span className="text-xs text-white/70">
                            hPa
                        </span>
                        </div>
                    </div>
                    </div>
                </>}
            </>
            }
        </div>
    )
}