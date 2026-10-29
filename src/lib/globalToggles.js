import { create } from "zustand";

export const toggler = create((set)=> ({
    toggleVideo:false,
    toggleEdit:false,
    toggleBookmarks:false,

    toggleTab: (obj = {}) =>
        set((state) => {
            
            if (!obj || Object.keys(obj).length === 0) return state;
            let key = Object.keys(obj)[0];
            let  value = obj[key];

            return{
                ...state,
                [key]: value
            }
        })
}))