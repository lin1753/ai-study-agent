import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { BookOpen, Plus, Settings, Trash2, Edit2 } from 'lucide-react';
import * as API from '../api';
import clsx from 'clsx';
import SettingsModal from './SettingsModal';

export default function Sidebar() {
    const [spaces, setSpaces] = useState([]);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const navigate = useNavigate();
    const { spaceId } = useParams();

    useEffect(() => {
        loadSpaces();
    }, [spaceId]); // Reload when ID changes to ensure sync (optional)

    const loadSpaces = async () => {
        try {
            const res = await API.getSpaces();
            setSpaces(res.data);
        } catch (error) {
            console.error("Failed to load spaces", error);
        }
    };

    const handleCreate = async () => {
        const name = prompt("请输入新科目名称：");
        if (name) {
            try {
                const res = await API.createSpace(name);
                setSpaces(prev => [...prev, res.data]);
                navigate(`/space/${res.data.id}`);
            } catch (error) {
                alert("创建失败");
            }
        }
    };

    const handleDelete = async (e, id) => {
        e.stopPropagation();
        if (confirm("确定要删除这个科目吗？所有相关资料和对话都将丢失。")) {
            try {
                await API.deleteSpace(id);
                setSpaces(prev => prev.filter(s => s.id !== id));
                if (spaceId === id) navigate('/');
            } catch (error) {
                console.error("Delete failed", error);
                alert("删除失败");
            }
        }
    };

    const handleRename = async (e, space) => {
        e.stopPropagation();
        const newName = prompt("重命名科目：", space.name);
        if (newName && newName !== space.name) {
            try {
                const res = await API.updateSpace(space.id, newName);
                setSpaces(prev => prev.map(s => s.id === space.id ? res.data : s));
            } catch (error) {
                console.error("Rename failed", error);
                alert("重命名失败");
            }
        }
    };

    return (
        <div className="w-full bg-[#0a0a0b] text-gray-300 flex flex-col h-full border-r border-gray-800/60 shadow-[4px_0_24px_rgba(0,0,0,0.2)] z-10 relative">
            {/* Header */}
            <div className="p-5">
                <button
                    onClick={handleCreate}
                    className="w-full flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 transition-all duration-300 text-sm font-medium text-white bg-blue-600/90 hover:bg-blue-500 shadow-lg shadow-blue-900/20 border border-blue-500/20 hover:scale-[1.02]"
                >
                    <Plus size={16} strokeWidth={2.5} />
                    新建科目空间
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto px-3 space-y-1.5 mt-2">
                <div className="px-2 py-2 text-xs font-bold text-gray-500/80 uppercase tracking-widest">
                    My Subjects
                </div>
                {spaces.map(space => (
                    <div
                        key={space.id}
                        onClick={() => navigate(`/space/${space.id}`)}
                        className={clsx(
                            "w-full text-left px-3 py-2.5 rounded-xl text-sm flex items-center gap-3 transition-all duration-200 overflow-hidden group cursor-pointer border",
                            spaceId === space.id 
                                ? "bg-gray-800/80 text-white border-gray-700 shadow-sm" 
                                : "border-transparent hover:bg-gray-900/50 hover:border-gray-800"
                        )}
                    >
                        <BookOpen size={16} className={clsx("shrink-0 transition-colors", spaceId === space.id ? "text-blue-400" : "text-gray-500 group-hover:text-gray-300")} />
                        <span className="truncate flex-1 font-medium">{space.name}</span>

                        {/* Action Buttons (Visible on Hover) */}
                        <div className="hidden group-hover:flex items-center gap-1">
                            <button onClick={(e) => handleRename(e, space)} className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-white">
                                <Edit2 size={12} />
                            </button>
                            <button onClick={(e) => handleDelete(e, space.id)} className="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-red-400">
                                <Trash2 size={12} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-800">
                <button 
                    onClick={() => setIsSettingsOpen(true)}
                    className="flex items-center gap-2 text-sm hover:text-white transition w-full"
                >
                    <Settings size={16} />
                    <span>Settings</span>
                </button>
            </div>

            {/* Global Settings Modal */}
            <SettingsModal 
                isOpen={isSettingsOpen} 
                onClose={() => setIsSettingsOpen(false)} 
            />
        </div>
    );
}
