// src/pages/StudySpace.jsx
import React, { useState, useCallback, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MainThread from '../components/MainThread';
import ChatInterface from '../components/ChatInterface';
import { X, MessageSquare, ChevronRight, History, ArrowLeft, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import * as API from '../api';

export default function StudySpace() {
    const { spaceId } = useParams();
    const [activeBranchId, setActiveBranchId] = useState(null);
    const [showRightPanel, setShowRightPanel] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [branchHistory, setBranchHistory] = useState([]);

    // Loading states phase 6.5
    const [isCreatingBranch, setIsCreatingBranch] = useState(false);
    const [branchLoadingText, setBranchLoadingText] = useState("");

    // Resizable panel state
    const [rightPanelWidth, setRightPanelWidth] = useState(400);
    const [isDragging, setIsDragging] = useState(false);

    const loadHistory = async () => {
        try {
            const res = await API.getBranches(spaceId);
            setBranchHistory(res.data);
        } catch (error) {
            console.error("Failed to load branches", error);
        }
    };

    useEffect(() => {
        if (spaceId && showHistory) {
            loadHistory();
        }
    }, [spaceId, showHistory]);

    const handleOpenBranch = async (pointOrBlockId) => {
        let payload = {};

        if (typeof pointOrBlockId === 'string') {
            if (pointOrBlockId === 'demo-block-id') {
                setShowRightPanel(true);
                return;
            }
            payload = { space_id: spaceId, source_block_id: pointOrBlockId };
        } else if (typeof pointOrBlockId === 'object') {
            payload = {
                space_id: spaceId,
                context: pointOrBlockId.content,
                title: pointOrBlockId.name
            };
        } else {
            console.error("Invalid branch source", pointOrBlockId);
            return;
        }

        // Optimistic update Phase 6.5
        setShowRightPanel(true);
        setShowHistory(false);
        setIsCreatingBranch(true);
        setActiveBranchId(null);
        
        const loadingSteps = [
            "正在初始化专属私教空间...",
            "正在检索关联上下文...",
            "正在聚合原子知识节点...",
            "正在唤醒私教 Agent..."
        ];
        
        let step = 0;
        setBranchLoadingText(loadingSteps[0]);
        const intervalTimer = setInterval(() => {
            step++;
            if (step < loadingSteps.length) {
                setBranchLoadingText(loadingSteps[step]);
            }
        }, 1800);

        try {
            const res = await API.createBranch(payload);
            clearInterval(intervalTimer);
            setActiveBranchId(res.data.thread_id);
        } catch (error) {
            clearInterval(intervalTimer);
            console.error("Failed to create branch", error);
            alert(error.response?.data?.detail || "无法创建支线对话，请检查后端服务与本地 LLM 连接。");
            setShowRightPanel(false);
        } finally {
            clearInterval(intervalTimer);
            setIsCreatingBranch(false);
        }
    };

    // Dragging Logic
    const handleMouseDown = useCallback((e) => {
        setIsDragging(true);
        e.preventDefault();
    }, []);

    const handleMouseMove = useCallback((e) => {
        if (!isDragging) return;

        // window.innerWidth is the total width. 
        // We calculate width from the right edge.
        let newWidth = window.innerWidth - e.clientX;

        // Constrain width
        if (newWidth < 280) newWidth = 280;
        if (newWidth > 720) newWidth = 720;

        setRightPanelWidth(newWidth);
    }, [isDragging]);

    const handleMouseUp = useCallback(() => {
        setIsDragging(false);
    }, []);

    useEffect(() => {
        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        } else {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        }
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging, handleMouseMove, handleMouseUp]);

    return (
        <div
            className="flex h-full select-none"
            style={{ cursor: isDragging ? 'ew-resize' : 'default' }}
        >
            {/* Center: Main Thread (Flexible) */}
            <div className={`flex-1 h-full min-w-0 ${isDragging ? 'pointer-events-none' : ''}`}>
                <MainThread
                    spaceId={spaceId}
                    onOpenBranch={handleOpenBranch}
                />
            </div>

            {/* Splitter */}
            {showRightPanel && (
                <div
                    onMouseDown={handleMouseDown}
                    className="w-1 cursor-ew-resize bg-gray-200 hover:bg-blue-400 active:bg-blue-500 transition-colors z-50 h-full relative"
                >
                    <div className="absolute inset-y-0 -left-1 -right-1 z-50"></div>
                </div>
            )}

            {/* Right: Branch Thread */}
            <div
                style={{ width: showRightPanel ? rightPanelWidth : 0 }}
                className={clsx(
                    "bg-white flex flex-col transition-none border-l border-gray-200",
                    !showRightPanel && "overflow-hidden border-0",
                    isDragging && 'pointer-events-none'
                )}
            >
                <div className="h-14 shrink-0 border-b flex items-center justify-between px-4 bg-gray-50/50">
                    <div className="flex items-center gap-2 text-sm font-semibold text-gray-700">
                        {showHistory ? (
                            <button onClick={() => setShowHistory(false)} className="flex items-center gap-1 hover:text-blue-600 transition">
                                <ArrowLeft size={16} /> 返回对话
                            </button>
                        ) : (
                            <>
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                分支探索
                            </>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        {!showHistory && (
                            <button
                                onClick={() => setShowHistory(true)}
                                className="p-1.5 hover:bg-gray-200 rounded text-gray-500 transition"
                                title="历史对话记录"
                            >
                                <History size={16} />
                            </button>
                        )}
                        <button
                            onClick={() => setShowRightPanel(false)}
                            className="p-1.5 hover:bg-gray-200 rounded text-gray-400 transition"
                            title="关闭侧边栏"
                        >
                            <X size={16} />
                        </button>
                    </div>
                </div>

                <div className="flex-1 overflow-hidden relative">
                    {showHistory ? (
                        <div className="h-full overflow-y-auto p-4 bg-gray-50">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-4 px-1">交互历史记录 (History)</h3>
                            <div className="space-y-3">
                                {branchHistory.length === 0 ? (
                                    <div className="text-center text-sm text-gray-400 py-10">暂无历史记录</div>
                                ) : (
                                    branchHistory.map(b => (
                                        <button
                                            key={b.id}
                                            onClick={() => {
                                                setActiveBranchId(b.id);
                                                setShowHistory(false);
                                            }}
                                            className={clsx(
                                                "w-full text-left p-4 rounded-xl shadow-sm border transition group flex flex-col gap-1.5",
                                                activeBranchId === b.id
                                                    ? "bg-blue-50 border-blue-200"
                                                    : "bg-white border-gray-100 hover:border-blue-300 hover:shadow-md"
                                            )}
                                        >
                                            <div className={clsx(
                                                "font-semibold text-sm line-clamp-2 leading-relaxed text-gray-800"
                                            )}>
                                                {b.title || '无标题对话'}
                                            </div>
                                            <div className="text-xs text-gray-400 font-mono">
                                                {new Date(b.created_at).toLocaleString()}
                                            </div>
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>
                    ) : isCreatingBranch ? (
                        <div className="flex flex-col items-center justify-center h-full text-blue-500 p-8 text-center bg-gray-50/50 animate-pulse">
                            <Loader2 size={36} className="mb-4 animate-spin text-blue-400" />
                            <h3 className="text-base font-semibold text-gray-700 mb-2 tracking-wide">即将进入支线探索</h3>
                            <p className="text-sm font-medium text-blue-500/80 transition-all duration-500">
                                {branchLoadingText}
                            </p>
                        </div>
                    ) : activeBranchId ? (
                        <ChatInterface threadId={activeBranchId} spaceId={spaceId} />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-400 p-8 text-center bg-gray-50/30">
                            <MessageSquare size={32} className="mb-2 opacity-20" />
                            <p className="text-sm">点击左侧知识点开启对话</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
