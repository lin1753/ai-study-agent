// src/pages/SubjectList.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, BookOpen } from 'lucide-react';
import { getSpaces, createSpace } from '../api';

export default function SubjectList() {
    const [spaces, setSpaces] = useState([]);
    const [newSpaceName, setNewSpaceName] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        loadSpaces();
    }, []);

    const loadSpaces = async () => {
        try {
            const res = await getSpaces();
            setSpaces(res.data);
        } catch (error) {
            console.error("Failed to load spaces", error);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!newSpaceName.trim()) return;
        try {
            await createSpace(newSpaceName);
            setNewSpaceName('');
            loadSpaces();
        } catch (error) {
            console.error("Failed to create space", error);
        }
    };

    return (
        <div className="max-w-4xl mx-auto p-8">
            <h1 className="text-3xl font-bold mb-8 text-gray-800">我的复习科目</h1>

            {/* Create New */}
            <form onSubmit={handleCreate} className="mb-10 flex gap-4">
                <input
                    type="text"
                    placeholder="输入新科目名称，例如：高等数学"
                    className="flex-1 p-4 rounded-xl border border-gray-200 shadow-sm focus:ring-2 focus:ring-blue-500 outline-none transition"
                    value={newSpaceName}
                    onChange={(e) => setNewSpaceName(e.target.value)}
                />
                <button
                    type="submit"
                    className="bg-black text-white px-8 py-4 rounded-xl font-medium hover:bg-gray-800 transition flex items-center gap-2"
                >
                    <Plus size={20} />
                    创建科目
                </button>
            </form>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {spaces.map((space) => (
                    <div
                        key={space.id}
                        onClick={() => navigate(`/space/${space.id}`)}
                        className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md cursor-pointer transition group"
                    >
                        <div className="flex items-center justify-between mb-4">
                            <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-full flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition">
                                <BookOpen size={24} />
                            </div>
                        </div>
                        <h3 className="text-xl font-semibold text-gray-800 group-hover:text-blue-600 transition">
                            {space.name}
                        </h3>
                        <p className="text-sm text-gray-400 mt-2">点击进入复习空间</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
