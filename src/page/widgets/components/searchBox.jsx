import { useState } from "react";
import { database } from "../../../lib/globalState"
import { toggler } from "../../../lib/globalToggles"

export default function SearchBar() {
    const {username} = database(stat=> stat.db.name);
    let {setDB} = database();
    const [isEdit,setEdit] = useState(false);
    
    const handle = (evnt)=> {
        evnt.preventDefault()
        let formData = new FormData(evnt.target);
        let {newName} = Object.fromEntries(formData)
        let data = {
            name:{
                username:newName
            }
        }
        setDB({data,isGet:false})
        setEdit(false)
    }

    function handleSearch(evnt) {
        evnt.preventDefault();

        let formData = new FormData(evnt.target);
        let {query} = Object.fromEntries(formData);


        if (!query) return;

        // Already has http:// or https://
        if (/^https?:\/\//i.test(query)) {
            window.location.href = query;
            return;
        }

        // Looks like a domain
        if (/^[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+([/?#].*)?$/.test(query)) {
            window.location.href = `https://${query}`;
            return;
        }

        // Otherwise, Google search
        const encode = encodeURIComponent(query);
        window.location.href = `https://www.google.com/search?q=${encode}`;
    }

    return(  
         <div className="blurBg search">
             { isEdit ? <form action="" className="absolute! top-0!" onSubmit={handle}>
                <input autoComplete="off" type="text" name="newName" placeholder="Enter your nickname" />
             </form> :
             <p id="greet">Wellcome! <span className="neonTxt">{username}</span> { username === "John Deo" && <i onClick={()=> setEdit(true)} className="bx bx-pencil cursor-pointer"></i>}</p>
             }
             <form action="" onSubmit={handleSearch}>
                 <input autoComplete="off" type="text" name="query" placeholder="Find or Enter URL" />
                 <i onClick={handleSearch} className="bx bx-search-alt"></i>
             </form>
         </div>
    )
}