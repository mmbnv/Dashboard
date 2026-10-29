import defaultImg from '../../../assets/default.jpg'
export default function ImageBg({blogURL,isBlur}) {
    
    return(
        <div className="underTaker">
            <img src={blogURL || defaultImg} alt="" />
            {isBlur && <div className="blurBg z-2! h-full w-full absolute top-0 left-0"></div>}
        </div>
    )
}