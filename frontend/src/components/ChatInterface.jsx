// src/components/ChatInterface.jsx
import React, { useEffect, useState, useRef } from 'react';
import { Send, User, Bot, Paperclip, Loader } from 'lucide-react';
import * as API from '../api';
import clsx from 'clsx';
// import { fetchEventSource } from '@microsoft/fetch-event-source'; // Removed unused import 
// Native EventSource is GET only usually, but for POST stream we might need fetch.
// For simplicity V1, we use a basic fetch reader loop or library.
// Let's implement a custom fetch reader for streaming.

export default function ChatInterface({ threadId, spaceId }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        loadHistory();
    }, [threadId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const loadHistory = async () => {
        try {
            const res = await API.getChatHistory(threadId);
            setMessages(res.data);
        } catch (error) {
            console.error("Failed to load chat history", error);
        }
    };

    const calculateClass = (role) => {
        return role === 'user'
            ? "bg-black text-white ml-auto"
            : "bg-gray-100 text-gray-800 mr-auto";
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isTyping) return;

        const userMsg = { role: 'user', content: input, created_at: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsTyping(true);

        // Initial placeholder for AI
        const aiMsgId = Date.now();
        setMessages(prev => [...prev, { role: 'assistant', content: '', created_at: new Date().toISOString(), id: aiMsgId }]);

        try {
            const response = await fetch('http://localhost:8000/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ thread_id: threadId, content: userMsg.content }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let aiContent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                aiContent += chunk;

                // Update the last message
                setMessages(prev => prev.map(msg =>
                    msg.id === aiMsgId ? { ...msg, content: aiContent } : msg
                ));
            }
        } catch (error) {
            console.error("Chat error", error);
            setMessages(prev => [...prev, { role: 'system', content: 'Error: Failed to get response' }]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file || !spaceId) return;

        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            await API.uploadSupplementaryFile(spaceId, file);
            
            // Alert user success
            setMessages(prev => [...prev, { 
                role: 'system', 
                content: `补充材料 [${file.name}] 已成功入库，您可以开始就该材料提问了！`, 
                created_at: new Date().toISOString() 
            }]);
        } catch (err) {
            console.error('Failed to upload supplementary material:', err);
            setMessages(prev => [...prev, { 
                role: 'system', 
                content: `上传失败: ${err.message}`, 
                created_at: new Date().toISOString() 
            }]);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={clsx("flex gap-3 max-w-[90%]", msg.role === 'user' ? "ml-auto flex-row-reverse" : "")}>
                        <div className={clsx("w-8 h-8 rounded-full flex items-center justify-center shrink-0", msg.role === 'user' ? "bg-gray-200" : "bg-green-100 text-green-600")}>
                            {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                        </div>
                        <div className={clsx("px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap", calculateClass(msg.role))}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isTyping && (
                    <div className="flex gap-3 max-w-[90%]">
                        <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center shrink-0 animate-pulse">
                            <Bot size={16} />
                        </div>
                        <div className="px-4 py-3 rounded-2xl bg-gray-50 text-gray-400 text-sm">
                            正在思考...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t bg-white">
                {isUploading && (
                    <div className="mb-2 flex items-center gap-2 text-sm text-blue-600 bg-blue-50/50 p-2 rounded-lg">
                        <Loader size={14} className="animate-spin" />
                        <span>正在上传并解析补充材料...</span>
                    </div>
                )}
                <form onSubmit={handleSend} className="relative flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        title="上传图片/习题进行辅导 (RAG侧载)"
                        className="p-2.5 text-gray-500 hover:text-blue-500 hover:bg-blue-50 rounded-xl transition-colors disabled:opacity-50"
                    >
                        <Paperclip size={20} />
                    </button>
                    <input 
                        type="file" 
                        ref={fileInputRef} 
                        className="hidden" 
                        accept=".pdf,.ppt,.pptx,.jpg,.jpeg,.png,.webp"
                        onChange={handleFileUpload}
                    />
                    
                    <div className="relative flex-1">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="输入你的问题..."
                            className="w-full pl-4 pr-12 py-3 bg-gray-50 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-black/5 transition"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isTyping || isUploading}
                            className="absolute right-2 top-2 p-1.5 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition"
                        >
                            <Send size={18} />
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
