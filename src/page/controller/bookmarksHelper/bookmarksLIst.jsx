import { useEffect, useState } from "react";
import { toggler } from "../../../lib/globalToggles";

export default function BookmarkList() {
    const [bookList, setList] = useState({});
    const [search, setSearch] = useState("");
    const { toggleTab } = toggler();

    function groupBookmarks(nodes, folder = "Bookmarks", result = {}) {
        for (const node of nodes) {
            if (node.url) {
                if (!result[folder]) result[folder] = [];

                result[folder].push({
                    id: node.id,
                    title: node.title,
                    url: node.url,
                    dateAdded: node.dateAdded,
                    dateLastUsed: node.dateLastUsed
                });
            }

            if (node.children) {
                groupBookmarks(
                    node.children,
                    node.title || folder,
                    result
                );
            }
        }

        return result;
    }

    const filteredBookmarks = Object.entries(bookList).reduce(
            (result, [folder, bookmarks]) => {

                const filtered = bookmarks.filter(bookmark => {

                    const q = search.toLowerCase();

                    return (
                        bookmark.title.toLowerCase().includes(q) ||
                        bookmark.url.toLowerCase().includes(q) ||
                        folder.toLowerCase().includes(q)
                    );
                });

                if (filtered.length > 0) {
                    result[folder] = filtered;
                }

                return result;

            },
            {}
        );

    const loadBookmarks = async () => {
        try {
            const tree = await chrome.bookmarks.getTree();
            setList(groupBookmarks(tree));
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        loadBookmarks();
    }, []);

    async function deleteBookmark(id) {
        try {
            await chrome.bookmarks.remove(id);

            setList(prev => {
                const updated = { ...prev };

                for (const folder in updated) {
                    updated[folder] = updated[folder].filter(
                        b => b.id !== id
                    );

                    if (updated[folder].length === 0) {
                        delete updated[folder];
                    }
                }

                return updated;
            });
        } catch (err) {
            console.error(err);
        }
    }

    const getIcon = (url) =>
    `https://www.google.com/s2/favicons?sz=512&domain_url=${encodeURIComponent(url)}`;

    return (
        <div className="w-full h-full flex flex-col overflow-hidden">

            {/* Header */}

            <div className="sticky top-0 z-20 bg-[#111319] border-b border-white/10">

                <div className="flex items-center gap-3 p-4">

                    <button
                        onClick={() => toggleTab({ toggleBookmarks: false })}
                        className="w-11 h-11 rounded-xl bg-white/5 hover:bg-white/10 transition"
                    >
                        <i className="bx bxs-left-arrow-circle text-3xl text-white"></i>
                    </button>

                    <div className="flex-1 relative">

                        <i className="bx bx-search absolute left-4 top-1/2 -translate-y-1/2 text-xl text-zinc-500"></i>

                        <input
                            value={search}
                            onChange={(e)=>setSearch(e.target.value)}
                            placeholder="Search bookmarks..."
                            className="
                                w-full
                                h-11
                                rounded-xl
                                pl-12
                                pr-4
                                bg-white/5
                                border
                                border-white/10
                                outline-none
                                text-white
                                placeholder:text-zinc-500
                                focus:border-violet-500
                            "
                        />

                    </div>

                </div>

            </div>

            {/* Body */}

            <div className="flex-1 my-scroll px-6 py-6">

                {Object.entries(filteredBookmarks).map(([folder, bookmarks]) => (

                    <div key={folder} className="mb-10">

                        {/* Folder */}

                        <div className="flex items-center gap-3 mb-5">

                            <i className="bx bxs-folder-open text-3xl text-violet-400"></i>

                            <h2 className="text-xl font-semibold text-white">
                                {folder}
                            </h2>

                            <span className="px-2 py-1 rounded-full bg-violet-500/20 text-violet-300 text-xs">
                                {bookmarks.length}
                            </span>

                        </div>

                        {/* Bookmark Grid */}

                        <div className="grid gap-3 grid-cols-[repeat(auto-fill,minmax(90px,1fr))]">

                            {bookmarks.map(bookmark => (

                                <div
                                    key={bookmark.id}
                                    className="
                                        group
                                        relative
                                        rounded-xl
                                        border
                                        border-white/10
                                        bg-white/5
                                        backdrop-blur-md
                                        hover:border-violet-500/40
                                        hover:-translate-y-1
                                        transition-all
                                        duration-200
                                    "
                                >

                                    <button
                                        onClick={() => deleteBookmark(bookmark.id)}
                                        className="
                                            absolute
                                            top-1
                                            right-1
                                            w-6
                                            h-6
                                            rounded-md
                                            flex
                                            items-center
                                            justify-center
                                            text-zinc-500
                                            hover:bg-red-500
                                            hover:text-white
                                            transition
                                            opacity-0
                                            group-hover:opacity-100
                                        "
                                    >
                                        <i className="bx bx-trash text-sm cursor-pointer"></i>
                                    </button>

                                    <a
                                        href={bookmark.url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="flex flex-col items-center px-2 py-3"
                                    >

                                        <img
                                            src={getIcon(bookmark.url)}
                                            alt={bookmark.title}
                                            className="w-8 h-8 object-contain"
                                        />

                                        <span
                                            className="
                                                mt-2
                                                text-[11px]
                                                text-center
                                                text-white
                                                line-clamp-1
                                                w-full
                                            "
                                        >
                                            {bookmark.title}
                                        </span>

                                        <span
                                            className="
                                                mt-0.5
                                                text-[10px]
                                                text-zinc-500
                                                text-center
                                                line-clamp-1
                                                w-full
                                            "
                                        >
                                            {new URL(bookmark.url).hostname.replace("www.", "")}
                                        </span>

                                    </a>

                                </div>

                            ))}

                        </div>

                    </div>

                ))}

                {Object.keys(filteredBookmarks).length === 0 && (
                    <div className="flex items-center justify-center py-20 text-zinc-500">
                        <div className="text-center">
                            <i className="bx bx-search-alt text-6xl mb-4"></i>
                            <p>No bookmarks found.</p>
                        </div>
                    </div>
                )}

            </div>

        </div>
    );
}