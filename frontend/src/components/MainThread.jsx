// src/components/MainThread.jsx
import React, { useEffect, useState, useRef } from 'react';
import { FileText, Send, Sparkles, Upload, BookOpen } from 'lucide-react';
import clsx from 'clsx';
import * as API from '../api';
// import ReactMarkdown from "react-markdown";
import KnowledgeCard from './KnowledgeCard';

export default function MainThread({ spaceId, onOpenBranch }) {
    const [roadmap, setRoadmap] = useState([]);
    const [masteryData, setMasteryData] = useState({});
    const [messages, setMessages] = useState([]);
    const [threadId, setThreadId] = useState(null);
    const [loading, setLoading] = useState(false);
    const fileInputRef = useRef(null);
    const [uploading, setUploading] = useState(false);
    const [uploadLogs, setUploadLogs] = useState([]);
    const [chatMsg, setChatMsg] = useState('');
    const [agentThoughts, setAgentThoughts] = useState('');
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

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Read global AI config from localStorage
        const config = {
            exam_weights: {}, // Disable weights logic
            priority_chapters: [], // Extract all content
            llm_provider: localStorage.getItem('llm_provider') || 'local',
            llm_api_key: localStorage.getItem('llm_api_key') || '',
            llm_base_url: localStorage.getItem('llm_base_url') || 'https://api.deepseek.com/v1',
            llm_model: localStorage.getItem('llm_model') || 'deepseek-chat'
        };

        setUploading(true);
        setUploadLogs(['文件正在上传...']);
        try {
            // Update space with global config settings
            await API.updateSpaceConfig(spaceId, config);
            
            // Start upload and extraction pipeline
            const uploadRes = await API.uploadFile(spaceId, file);
            
            if (uploadRes.data && uploadRes.data.job_id) {
                const jobId = uploadRes.data.job_id;
                
                // Poll for completion
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await API.getFileStatus(jobId);
                        
                        if (statusRes.data.message) {
                            setUploadLogs(prev => {
                                if (prev.length === 0 || prev[prev.length - 1] !== statusRes.data.message) {
                                    return [...prev, statusRes.data.message];
                                }
                                return prev;
                            });
                        }

                        if (statusRes.data.status === 'completed') {
                            clearInterval(pollInterval);
                            await loadData();
                            setUploading(false);
                            setUploadLogs(prev => [...prev, '资料解析完成！']);
                        } else if (statusRes.data.status === 'failed') {
                            clearInterval(pollInterval);
                            alert("后台解析失败，请检查服务日志。");
                            setUploading(false);
                            setUploadLogs(prev => [...prev, '资料解析失败！']);
                        }
                    } catch (pollErr) {
                        console.error("Polling error", pollErr);
                    }
                }, 3000);
            } else {
                await loadData();
                setUploading(false);
            }
        } catch (error) {
            console.error("Upload failed", error);
            alert(error.response?.data?.detail || "上传失败，请确保后台服务已启动或网络正常。");
            setUploading(false);
        }

        // Reset file input
        e.target.value = '';
    };

    const handleSendMainChat = async () => {
        if (!chatMsg.trim() || !threadId) return;

        const userMsg = { role: 'user', content: chatMsg, created_at: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setChatMsg('');
        setAgentThoughts(''); // 开始新的推理轨迹

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
            let sseBuffer = '';

            // Add initial empty AI message
            setMessages(prev => [...prev, { role: 'assistant', content: '', created_at: new Date().toISOString() }]);

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    if (aiContent.includes('<ACTION>')) {
                        await loadData();
                    }
                    setTimeout(() => setAgentThoughts(''), 2000); // 延迟清理，让用户多看一会儿思考完成状态
                    break;
                }
                
                const chunk = decoder.decode(value, { stream: true });
                sseBuffer += chunk;
                
                // Split by double newline which divides SSE events
                const events = sseBuffer.split('\n\n');
                // The last element is the remaining incomplete buffer
                sseBuffer = events.pop() || '';
                
                for (const ev of events) {
                    if (ev.startsWith('data: ')) {
                        const jsonStr = ev.substring(6).trim();
                        if (!jsonStr) continue;
                        
                        try {
                            const data = JSON.parse(jsonStr);
                            
                            if (data.type === 'thought') {
                                setAgentThoughts(prev => prev + data.content);
                                setMessages(prev => {
                                    const next = [...prev];
                                    const last = next[next.length - 1];
                                    last.thoughts = (last.thoughts || '') + data.content;
                                    return next;
                                });
                            } else if (data.type === 'message') {
                                aiContent += data.content;
                                // V2.5/V3: Hide legacy <ACTION> XML tags from the user interface continuously
                                const displayContent = aiContent.replace(/<ACTION>[\s\S]*?(?:<\/ACTION>|$)/g, '').trim();

                                setMessages(prev => {
                                    const next = [...prev];
                                    next[next.length - 1].content = displayContent;
                                    return next;
                                });
                            }
                        } catch(e) {
                            console.error("Failed to parse SSE JSON:", jsonStr, e);
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Chat error", error);
            setMessages(prev => [...prev, { role: 'assistant', content: "抱歉，出错了。", created_at: new Date().toISOString() }]);
            setAgentThoughts('执行中断');
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
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
                                解析中...
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
                        ) : uploading ? (
                            <div className="flex flex-col bg-white border border-blue-100 rounded-3xl shadow-sm overflow-hidden min-h-[400px]">
                                <div className="px-6 py-4 border-b border-gray-100 bg-blue-50 flex items-center gap-4 shrink-0">
                                    <div className="bg-white p-2 text-blue-600 rounded-full shadow-sm relative">
                                        <Upload size={20} className="animate-pulse" />
                                        <div className="absolute inset-0 border-2 border-blue-400 rounded-full animate-ping opacity-20"></div>
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-800 text-lg">解析引擎运行中</h3>
                                        <p className="text-xs text-gray-500 mt-0.5">正在提取并重构知识图谱，这可能需要几十秒时间...</p>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto p-6 space-y-3 bg-slate-50/50 custom-scrollbar font-mono text-sm max-h-[500px]">
                                    {uploadLogs.map((log, index) => (
                                        <div 
                                            key={index} 
                                            className={clsx(
                                                "flex items-start gap-3 fade-in slide-in-top-2 duration-300",
                                                index === uploadLogs.length - 1 ? "text-blue-700 font-medium" : "text-gray-400"
                                            )}
                                        >
                                            <div className="shrink-0 mt-1">
                                                {index === uploadLogs.length - 1 ? (
                                                    <span className="flex w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)] animate-pulse" />
                                                ) : (
                                                    <span className="flex w-2 h-2 rounded-full bg-gray-300" />
                                                )}
                                            </div>
                                            <span className="leading-5">{log}</span>
                                        </div>
                                    ))}
                                    <div className="h-2" />
                                </div>
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
                            <div 
                                onClick={() => fileInputRef.current.click()}
                                className="cursor-pointer group flex flex-col items-center justify-center text-center py-20 bg-gray-50/50 hover:bg-blue-50/50 border-2 border-dashed border-gray-200 hover:border-blue-300 rounded-3xl transition-all duration-300"
                            >
                                <div className="bg-white p-4 rounded-full shadow-sm mb-6 group-hover:scale-110 transition-transform duration-300 group-hover:text-blue-600 text-gray-400">
                                    <Upload size={32} />
                                </div>
                                <h3 className="text-xl font-bold text-gray-700 mb-2">主线待开启</h3>
                                <p className="text-sm text-gray-500 max-w-sm">点击此区域上传您的复习资料 (支持 PDF, PPT)。系统将自动提取大纲、知识点并生成专属自测题库。</p>
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
                                            {m.role === 'assistant' && (m.thoughts || (idx === messages.length - 1 && agentThoughts)) && (
                                                <div className="mb-4 bg-gray-50 border border-gray-100 rounded-lg p-3 text-xs text-gray-500 max-h-40 overflow-y-auto">
                                                    <div className="flex items-center gap-2 mb-2 font-bold text-gray-400">
                                                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-ping"></div>
                                                        Agent Trace
                                                    </div>
                                                    <div className="font-mono opacity-80 whitespace-pre-wrap">
                                                        {m.thoughts || agentThoughts}
                                                    </div>
                                                </div>
                                            )}
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
