
import { pre } from "framer-motion/client";
import { create } from "zustand";

export const database = create((set, get) => ({
  db: {
    "background":{
      load:"default",
      type:"image",
      isBlur:false,
      grdColor:"default"
    },
    "name":{
      username:"John Deo",
      isVisible:true
    },
    "searchWid":{
      isVisible:true,
      position:{
        x:10, y:10
      }
    },
    "clockWid":{
      isVisible:true,
      anaLog:true,
      position:{
        x:10, y:200
      }
    },
    "weatherWid":{
      isVisible:true,
      apiKey:"",
      city:"",
      position:{
        x:150, y:250,
      }
    },
    "quickAcSetting":{
      showQuickApps:true,
      isFrequently: false,
      crntTheme:"light"
    },
      "quickAcces":[
        {
          url: "https://mail.google.com/",
          icon: "	https://www.gstatic.com/images/branding/product/2x/gmail_2020q4_48dp.png",
          name: "Gmail"
        },
        {
          url: "https://www.youtube.com/",
          icon: "https://www.google.com/s2/favicons?domain=youtube.com",
          name: "YouTube"
        },
        {
          url: "https://monkeytype.com/",
          icon: "https://www.google.com/s2/favicons?domain=monkeytype.com",
          name: "Monkeytype"
        }
      ],
      "topBookSlide":{
        isTrue:false,
        data:[]
      },
  },
  

  setDB: (obj = {}) => {
    const current = get().db;
    let {data,isGet} = obj;

   

    if (!data || Object.keys(data).length === 0) return;
    const newDb = {...current };

    Object.keys(data).forEach(key=>{
        const value = data[key];
       // console.log(value)
    
        if (typeof value === "object" && !Array.isArray(value)) {
          newDb[key] = {
            ...(newDb[key] || {}),
            ...value
          };
        } else {
          newDb[key] = value;
        } 
    })
    // Save the FULL DB
    if (!isGet) {
      if (typeof chrome !== "undefined" && chrome.storage) {
        chrome.storage.local.set({ db: newDb }, () => {
          console.log("Saved");
        });
      } else {
        localStorage.setItem("Saved", JSON.stringify(newDb));
      }
    }
    //console.log(newDb)

    set({ db: newDb });
  }
}));

export const Apps = create((set, get) => ({
  array: [
  // AI
        {
          url: "https://chatgpt.com/",
          icon: "https://www.google.com/s2/favicons?domain=chatgpt.com",
          name: "ChatGPT"
        },
        {
          url: "https://gemini.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=gemini.google.com",
          name: "Gemini"
        },
        {
          url: "https://claude.ai/",
          icon: "https://www.google.com/s2/favicons?domain=claude.ai",
          name: "Claude"
        },

        // Google
        {
          url: "https://mail.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=gmail.com",
          name: "Gmail"
        },
        {
          url: "https://drive.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=drive.google.com",
          name: "Drive"
        },
        {
          url: "https://docs.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=docs.google.com",
          name: "Docs"
        },
        {
          url: "https://sheets.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=sheets.google.com",
          name: "Sheets"
        },
        {
          url: "https://slides.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=slides.google.com",
          name: "Slides"
        },
        {
          url: "https://calendar.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=calendar.google.com",
          name: "Calendar"
        },
        {
          url: "https://photos.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=photos.google.com",
          name: "Photos"
        },
        {
          url: "https://meet.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=meet.google.com",
          name: "Meet"
        },
        {
          url: "https://news.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=news.google.com",
          name: "News"
        },
        {
          url: "https://maps.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=maps.google.com",
          name: "Maps"
        },
        {
          url: "https://keep.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=keep.google.com",
          name: "Keep"
        },
        {
          url: "https://contacts.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=contacts.google.com",
          name: "Contacts"
        },
        {
          url: "https://translate.google.com/",
          icon: "https://www.google.com/s2/favicons?domain=translate.google.com",
          name: "Translate"
        },
        {
          url: "https://www.youtube.com/",
          icon: "https://www.google.com/s2/favicons?domain=youtube.com",
          name: "YouTube"
        },

        // Developer
        {
          url: "https://github.com/",
          icon: "https://www.google.com/s2/favicons?domain=github.com",
          name: "GitHub"
        },
        {
          url: "https://gitlab.com/",
          icon: "https://www.google.com/s2/favicons?domain=gitlab.com",
          name: "GitLab"
        },
        {
          url: "https://stackoverflow.com/",
          icon: "https://www.google.com/s2/favicons?domain=stackoverflow.com",
          name: "Stack Overflow"
        },
        {
          url: "https://codepen.io/",
          icon: "https://www.google.com/s2/favicons?domain=codepen.io",
          name: "CodePen"
        },
        {
          url: "https://replit.com/",
          icon: "https://www.google.com/s2/favicons?domain=replit.com",
          name: "Replit"
        },
        {
          url: "https://vercel.com/",
          icon: "https://www.google.com/s2/favicons?domain=vercel.com",
          name: "Vercel"
        },

        // Productivity
        {
          url: "https://www.notion.so/",
          icon: "https://www.google.com/s2/favicons?domain=notion.so",
          name: "Notion"
        },
        {
          url: "https://trello.com/",
          icon: "https://www.google.com/s2/favicons?domain=trello.com",
          name: "Trello"
        },
        {
          url: "https://slack.com/",
          icon: "https://www.google.com/s2/favicons?domain=slack.com",
          name: "Slack"
        },
        {
          url: "https://discord.com/",
          icon: "https://www.google.com/s2/favicons?domain=discord.com",
          name: "Discord"
        },

        // Learning
        {
          url: "https://www.w3schools.com/",
          icon: "https://www.google.com/s2/favicons?domain=w3schools.com",
          name: "W3Schools"
        },
        {
          url: "https://developer.mozilla.org/",
          icon: "https://www.google.com/s2/favicons?domain=developer.mozilla.org",
          name: "MDN"
        },
        {
          url: "https://www.freecodecamp.org/",
          icon: "https://www.google.com/s2/favicons?domain=freecodecamp.org",
          
          name: "freeCodeCamp"
        },

        // Typing
        {
          url: "https://monkeytype.com/",
          icon: "https://www.google.com/s2/favicons?domain=monkeytype.com",
          name: "Monkeytype"
        },
        {
          url: "https://play.typeracer.com/",
          icon: "https://www.google.com/s2/favicons?domain=typeracer.com",
          name: "TypeRacer"
        },

        // Social
        {
          url: "https://reddit.com/",
          icon: "https://www.google.com/s2/favicons?domain=reddit.com",
          name: "Reddit"
        },
        {
          url: "https://x.com/",
          icon: "https://www.google.com/s2/favicons?domain=x.com",
          name: "X"
        },
        {
          url: "https://linkedin.com/",
          icon: "https://www.google.com/s2/favicons?domain=linkedin.com",
          name: "LinkedIn"
        },

        // Entertainment
        {
          url: "https://netflix.com/",
          icon: "https://www.google.com/s2/favicons?domain=netflix.com",
          name: "Netflix"
        },
        {
          url: "https://spotify.com/",
          icon: "https://www.google.com/s2/favicons?domain=spotify.com",
          name: "Spotify"
        },
        {
  url: "https://outlook.live.com/",
  name: "Outlook"
},
{
  url: "https://onedrive.live.com/",
  name: "OneDrive"
},
{
  url: "https://office.com/",
  name: "Microsoft 365"
},
{
  url: "https://teams.microsoft.com/",
  name: "Teams"
},
{
  url: "https://copilot.microsoft.com/",
  name: "Copilot"
},
{
  url: "https://cloudflare.com/",
  name: "Cloudflare"
},
{
  url: "https://railway.app/",
  name: "Railway"
},
{
  url: "https://render.com/",
  name: "Render"
},
{
  url: "https://netlify.com/",
  name: "Netlify"
},
{
  url: "https://supabase.com/",
  name: "Supabase"
},
{
  url: "https://firebase.google.com/",
  name: "Firebase"
},
{
  url: "https://planetscale.com/",
  name: "PlanetScale"
},
{
  url: "https://figma.com/",
  name: "Figma"
},
{
  url: "https://www.canva.com/",
  name: "Canva"
},
{
  url: "https://dribbble.com/",
  name: "Dribbble"
},
{
  url: "https://behance.net/",
  name: "Behance"
},
{
  url: "https://coolors.co/",
  name: "Coolors"
},
{
  url: "https://twitch.tv/",
  name: "Twitch"
},
{
  url: "https://medium.com/",
  name: "Medium"
},
{
  url: "https://substack.com/",
  name: "Substack"
},
{
  url: "https://pinterest.com/",
  name: "Pinterest"
},
{
  url: "https://temp-mail.org/",
  name: "Temp Mail"
},
{
  url: "https://speedtest.net/",
  name: "Speedtest"
},
{
  url: "https://archive.org/",
  name: "Internet Archive"
},
{
  url: "https://web.whatsapp.com/",
  name: "WhatsApp"
},
{
  url: "https://telegram.org/",
  name: "Telegram"
},
{
  url: "https://leetcode.com/",
  name: "LeetCode"
},
{
  url: "https://hackerrank.com/",
  name: "HackerRank"
},
{
  url: "https://excalidraw.com/",
  name: "Excalidraw"
},
{
  url: "https://regex101.com/",
  name: "Regex101"
},
{
  url: "https://jsonformatter.org/",
  name: "JSON Formatter"
},
{
  url: "https://caniuse.com/",
  name: "Can I Use"
},
{
  url: "https://roadmap.sh/",
  name: "Roadmap"
},
{
  url: "https://npmjs.com/",
  name: "NPM"
},
{
  url: "https://bun.sh/",
  name: "Bun"
},
{
  url: "https://react.dev/",
  name: "React"
},
{
  url: "https://tailwindcss.com/",
  name: "Tailwind"
},
{
  url: "https://nextjs.org/",
  name: "Next.js"
},
{
  url: "https://nodejs.org/",
  name: "Node.js"
},
{
  url: "https://typescriptlang.org/",
  name: "TypeScript"
}
      ],

      setApp: (dataObj = {}) => {
    const { newApp, isGet } = dataObj;
      
    if (!newApp) return;

    set((state) => {
        // Convert object -> array
        const incomingApps = Array.isArray(newApp)
            ? newApp
            : [newApp];

        // Remove invalid entries
        const validApps = incomingApps.filter(
            app => app && Object.keys(app).length >= 2
        );

        if (!validApps.length) return state;

        // Prevent duplicates
        const uniqueApps = validApps.filter(
            app => !state.array.some(
                existing => existing.url === app.url
            )
        );

        if (!uniqueApps.length) return state;

        const newList = [...state.array, ...uniqueApps];

        if (!isGet) {
            if (typeof chrome !== "undefined" && chrome.storage) {
                chrome.storage.local.set(
                    { appList: newList },
                    () => console.log("Saved")
                );
            } else {
                localStorage.setItem(
                    "appList",
                    JSON.stringify(newList)
                );
            }
        }

        return {
            array: newList
        };
    });
}

}));


export const useTabToggle = create((set) => ({
  tabObj: {
    allApps: false,
    settings: false,
    profile: false,
  },

  toggleTabs: (tabName) => 
    set(() => ({
      tabObj: {
        allApps: tabName === "allApps",
        settings: tabName === "settings",
        profile: tabName === "profile",
      },
    })),
}));