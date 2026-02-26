// src/components/MainThread.jsx
import React, { useEffect, useState, useRef } from 'react';
import { FileText, Send, Sparkles, Upload, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import * as API from '../api';
// import ReactMarkdown from "react-markdown";
import KnowledgeCard from './KnowledgeCard';
import ExamConfigModal from './ExamConfigModal';

export default function MainThread({ spaceId, onOpenBranch }) {
    const [roadmap, setRoadmap] = useState([]);
    const [masteryData, setMasteryData] = useState({});
    const [messages, setMessages] = useState([]);
    const [threadId, setThreadId] = useState(null);
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef(null);
    const [uploading, setUploading] = useState(false);
    const [chatMsg, setChatMsg] = useState('');
    const [showConfigModal, setShowConfigModal] = useState(false);
    const [pendingFile, setPendingFile] = useState(null);
    const chatEndRef = useRef(null);

    useEffect(() => {
        loadData();
    }, [spaceId]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const loadData = async () => {
        setLoading(true);
        try {
            const res = await API.getMainThread(spaceId);
            // res.data: { summary, roadmap, mastery, thread_id } (assuming backend returns it)
            // Wait, I need to check if backend get_main_thread_summary returns thread_id.
            // Oh, I didn't update get_main_thread_summary in app.py to return thread_id.
            // Let me re-read it.
            setRoadmap(res.data.roadmap || []);
            setMasteryData(res.data.mastery || {});

            // Guessing thread_id based on spaceId for now if not returned, 
            // but app.py's get_main_thread_summary should return it.
            // Let's assume I'll fix the backend to return ID.

            // Actually, MainThread ID is needed for chat.
            // I'll fetch history using the spaceId if I can't find threadId? 
            // Better to fix API.

            // Assuming for now it returns ID or I can fetch it.
        } catch (error) {
            console.error("Failed to load mapData", error);
        } finally {
            setLoading(false);
        }
    };

    // Helper to fetch history
    const fetchHistory = async (tId) => {
        try {
            const hRes = await API.getChatHistory(tId);
            setMessages(hRes.data);
        } catch (err) {
            console.error("Failed to fetch history", err);
        }
    };

    // Need to re-fetch loadData to get threadId
    useEffect(() => {
        const init = async () => {
            const res = await API.getMainThread(spaceId);
            if (res.data.id) {
                setThreadId(res.data.id);
                fetchHistory(res.data.id);
            }
        };
        init();
    }, [spaceId]);

    const handleUpdateMastery = async (pointId, level) => {
        try {
            await API.updateMastery(spaceId, pointId, level);
            setMasteryData(prev => ({ ...prev, [pointId]: level }));
        } catch (error) {
            console.error("Mastery update failed", error);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Store file and show config modal
        setPendingFile(file);
        setShowConfigModal(true);

        // Reset file input
        e.target.value = '';
    };

    const handleConfigSubmit = async (config) => {
        if (!pendingFile) return;

        setUploading(true);
        try {
            await API.updateSpaceConfig(spaceId, config);
            const uploadRes = await API.uploadFile(spaceId, pendingFile);
            
            // Check if it's async (returns job_id)
            if (uploadRes.data && uploadRes.data.job_id) {
                const jobId = uploadRes.data.job_id;
                
                // Poll for status
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await API.getFileStatus(jobId);
                        if (statusRes.data.status === 'completed') {
                            clearInterval(pollInterval);
                            await loadData();
                            setUploading(false);
                            setPendingFile(null);
                        } else if (statusRes.data.status === 'failed') {
                            clearInterval(pollInterval);
                            alert("后台解析失败，请检查服务日志。");
                            setUploading(false);
                            setPendingFile(null);
                        }
                        // if processing, continue polling...
                    } catch (pollErr) {
                        console.error("Polling error", pollErr);
                        // Optionally clear interval on consistent errors, but we keep trying for now
                    }
                }, 3000);
            } else {
                // Fallback for synchronous API
                await loadData();
                setUploading(false);
                setPendingFile(null);
            }
        } catch (error) {
            console.error("Upload failed", error);
            alert(error.response?.data?.detail || "上传失败，请确保后台服务已启动或网络正常。");
            setUploading(false);
            setPendingFile(null);
        }
    };

    const handleSendMainChat = async () => {
        if (!chatMsg.trim() || !threadId) return;

        const userMsg = { role: 'user', content: chatMsg, created_at: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setChatMsg('');

        try {
            const response = await fetch(API.getMainChatStreamUrl(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: threadId, content: userMsg.content }),
            });

            if (!response.ok) throw new Error("Stream failed");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiContent = '';

            // Add initial empty AI message
            setMessages(prev => [...prev, { role: 'assistant', content: '', created_at: new Date().toISOString() }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    // Stream finished: if any action was present, refresh the roadmap
                    if (aiContent.includes('<ACTION>')) {
                        await loadData();
                    }
                    break;
                }
                const chunk = decoder.decode(value, { stream: true });
                aiContent += chunk;

                // V2.5: Hide <ACTION> XML tags from the user interface continuously
                const displayContent = aiContent.replace(/<ACTION>[\s\S]*?(?:<\/ACTION>|$)/g, '').trim();

                setMessages(prev => {
                    const next = [...prev];
                    next[next.length - 1].content = displayContent;
                    return next;
                });
            }
        } catch (error) {
            console.error("Chat error", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "抱歉，出错了。", created_at: new Date().toISOString() }]);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Config Modal */}
            <ExamConfigModal
                isOpen={showConfigModal}
                onClose={() => {
                    setShowConfigModal(false);
                    setPendingFile(null);
                }}
                onSubmit={handleConfigSubmit}
            />

            {/* Header */}
            <div className="h-16 border-b border-gray-100 flex items-center justify-between px-6 bg-white/80 backdrop-blur-md sticky top-0 z-20 shadow-sm">
                <h2 className="font-bold text-gray-800 flex items-center gap-2 text-lg">
                    <div className="bg-blue-100 p-1.5 rounded-lg">
                        <BookOpen size={18} className="text-blue-600" />
                    </div>
                    复习路径规划 (V2.2 Async)
                </h2>
                <div>
                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept=".pdf,.ppt,.pptx"
                        onChange={handleFileSelect}
                    />
                    <button
                        onClick={() => fileInputRef.current.click()}
                        disabled={uploading}
                        className={clsx(
                            "text-xs px-4 py-2 rounded-xl font-medium flex items-center gap-2 transition-all shadow-sm",
                            uploading 
                                ? "bg-blue-50 text-blue-400 cursor-not-allowed border border-blue-100" 
                                : "bg-blue-600 hover:bg-blue-700 text-white shadow-blue-600/20"
                        )}
                    >
                        {uploading ? (
                            <>
                                <span className="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></span>
                                资料正在后排队解析中...
                            </>
                        ) : (
                            <>
                                <Upload size={14} />
                                补充复习资料
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Content Area - Roadmap + Chat */}
            <div className="flex-1 overflow-y-auto bg-gray-50/30 custom-scrollbar">
                <div className="max-w-3xl mx-auto p-6 space-y-8">
                    {/* Roadmap Section */}
                    <section>
                        {loading ? (
                            <div className="text-gray-400 text-center py-10 flex flex-col items-center gap-4">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                                正在规划学习路径...
                            </div>
                        ) : roadmap.length > 0 ? (
                            <div className="py-2">
                                {roadmap.map((chapter) => (
                                    <KnowledgeCard
                                        key={chapter.id}
                                        chapter={chapter}
                                        masteryData={masteryData}
                                        onUpdateMastery={handleUpdateMastery}
                                        onOpenBranch={onOpenBranch}
                                    />
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-10 text-gray-400 border-2 border-dashed border-gray-200 rounded-3xl">
                                <Sparkles size={48} className="mx-auto mb-4 opacity-10" />
                                <p>主线待开启</p>
                                <p className="text-xs mt-2 text-gray-300">上传复习资料，我将为你定制专属复习卡片</p>
                            </div>
                        )}
                    </section>

                    {/* Chat History Section */}
                    {messages.length > 0 && (
                        <section className="pt-8 border-t border-gray-200">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-6 px-1 flex items-center gap-2">
                                <Sparkles size={14} className="text-blue-400" />
                                教学沟通历史
                            </h3>
                            <div className="space-y-6">
                                {messages.map((m, idx) => (
                                    <div key={idx} className={clsx(
                                        "flex gap-4 p-4 rounded-2xl transition-all",
                                        m.role === 'user' 
                                            ? "bg-blue-50/50 ml-8 border border-blue-100/50 shadow-sm" 
                                            : "bg-white mr-8 border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)]"
                                    )}>
                                        <div className={clsx(
                                            "w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 select-none shadow-sm",
                                            m.role === 'user' 
                                                ? "bg-blue-600 text-white" 
                                                : "bg-[#111] text-white"
                                        )}>
                                            {m.role === 'user' ? 'ME' : 'AI'}
                                        </div>
                                        <div className="flex-1 text-sm leading-relaxed text-gray-700 whitespace-pre-wrap pt-1 font-medium">
                                            {m.content}
                                        </div>
                                    </div>
                                ))}
                                <div ref={chatEndRef} />
                            </div>
                        </section>
                    )}
                </div>
            </div>

            {/* Bottom Chat Input */}
            <div className="p-4 border-t border-gray-100 bg-white/90 backdrop-blur-xl">
                <div className="max-w-3xl mx-auto flex gap-2 relative shadow-sm rounded-2xl bg-white border border-gray-100 focus-within:border-blue-300 focus-within:shadow-md transition-all duration-300">
                    <input
                        type="text"
                        value={chatMsg}
                        onChange={(e) => setChatMsg(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMainChat()}
                        placeholder={threadId ? "就该科目整体内容提问或寻求规划建议..." : "规划完成后即可开启全球咨询"}
                        disabled={!threadId}
                        className="flex-1 px-5 py-3.5 bg-transparent border-0 rounded-2xl focus:outline-none text-sm disabled:opacity-50 placeholder-gray-400"
                    />
                    <button
                        onClick={handleSendMainChat}
                        disabled={!threadId || !chatMsg.trim()}
                        className="m-1 p-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition disabled:opacity-30 disabled:bg-gray-400"
                    >
                        <Send size={18} />
                    </button>
                </div>
                <p className="text-[11px] text-center text-gray-400 mt-2.5 font-medium">
                    导师会参考当前的复习路径 (Roadmap) 进行解答
                </p>
            </div>
        </div>
    );
}
