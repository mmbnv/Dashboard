import AnalogClock from "./anaLogClock";
import DigitalClock from "./digitalClock";

export default function ClockMgmt({Obj}) {

  return(
    <div className={`blurBg relative ${Obj.anaLog ? "h-55 w-80" : "w-100 h-70"} flex items-center justify-center text-white`}>
      {!Obj.anaLog && <DigitalClock/>}
      {Obj.anaLog && <AnalogClock/>}
    </div>
  )
}