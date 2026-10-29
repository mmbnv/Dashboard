import { database } from "../../../lib/globalState";
import ClockCotroll from "./clockControl";
import FranApp from "./customApp";
import DevInfo from "./devLoaperInfo";
import ContainerStructure from "./mgmtBuilder";
import WeatherColtroller from "./weatherControl";
import ProductivityControl from "./productivityControl";

export default function ContainerHolder () {
    const {name, searchWid, clockWid, weatherWid, quickAcSetting, quickAcces, taskWid, notesWid} = database(stat=> stat.db);
    let {setDB} = database();

    return(
        <>
            <div className="controllerContainer">
                <ContainerStructure crntData={{name,searchWid}}/>
            </div>
            <div className="controllerContainer">
                <ClockCotroll crntData={{clockWid}}/>
            </div>
            <div className="controllerContainer">
                <WeatherColtroller crntData={{weatherWid}} setData={setDB} />
            </div>
            <div className="controllerContainer">
                <ProductivityControl crntData={{taskWid, notesWid}} setData={setDB} />
            </div>
            <div className="controllerContainer">
                <FranApp crntList={{quickAcces, quickAcSetting}} setData={setDB} />
            </div>
            <div className="controllerContainer">
                <DevInfo />
            </div>
        </>
    )
}
