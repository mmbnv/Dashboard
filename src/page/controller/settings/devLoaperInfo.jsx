export default function DevInfo () {

    return(
        <>
            <div className="h-15 w-full border-b border-b-gray-500/40">
               <div className="flex items-center justify-center">👋 <p className="neonTxt text-xl font-bold">Hello! From Glassy Dhasboard</p></div>
                <span className="text-[12px] text-gray-500!">Version 1.0.0</span>
            </div>

            <div className="controlleBoxA h-40! flex items-center flex-col gap-1">
                <p className="headingP text-[15px]! border-none!">✨ Welcome to GNTD: Glass New Tab Dashboard!</p>
                <p className="text-[12px] p-2 text-gray-300/50!">Thank you for choosing our extension, We've crafted this beautiful, Glassy Dashboard  new tab experience with love and attention to detail, Enjou the smooth glass effects, powerful customization, and seamless productivity features.</p>
            </div>

            <p className="headingP border-b-gray-500/20!">👨‍💻 Developer</p>

            <div className="controlleBoxA h-15! flex items-center flex-row">
                <div className="imgHolderDiv flex-1 h-full flex items-center justify-center">
                    <img className="h-12! p-0.5 object-cover w-12! rounded-full" src="https://res.cloudinary.com/dcve50avm/image/upload/v1785595343/artneversleeps-20251103-0017_c0bypq.jpg" alt="" />
                </div>
                <div className="flex-3 h-full flex items-start flex-col">
                    <p className="text-md! mt-1">TheCoding Freak</p>
                    <span className="text-sm text-gray-400/20!">Software Developer</span>
                </div>
            </div>
            <div className="controlleBoxA h-10! flex items-center justify-center bg-blue-500/10! hover:bg-blue-500/20!">
                <p className="text-blue-700! font-bold"><i className="bx bxl-github text-lg text-blue-700!"></i> Github Profile</p>
            </div>

            <div className="controlleBoxA  h-10! bg-transparent! flex items-center flex-row gap-5">
                <div className="controlleBoxA h-8! w-1/2! flex items-center justify-center bg-blue-500/10! hover:bg-blue-500/20!">
                    <p className="text-[10px]" >☕ Buy me a coffee (optional)</p>
                </div>
                <div onClick={()=>{
                    window.open("https://github.com/Freak644/Glassy_DashBoard", "_blank")
                }} className="controlleBoxA h-8! w-1/4! flex items-center justify-center bg-blue-500/10! hover:bg-blue-500/20!">
                    <p className="text-[10px]" >✨ Star me</p>
                </div>
            </div>

            <div className="border border-gray-500/20 w-full m-2.5"/>

            <div className="finalDiv"><p>Made with 💖 by </p> <span>Freak</span> <p>in</p><span>India</span></div>
        </>
    )
}