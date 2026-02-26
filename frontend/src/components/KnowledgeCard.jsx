// src/components/KnowledgeCard.jsx
// 每章节：章节标题 → 知识点列表 → 例题区
// 章节掌握度 = 所有子知识点 + 所有例题掌握度的聚合
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Star, PlayCircle, Info, BookOpen, Brain } from 'lucide-react';
import clsx from 'clsx';

// ---- 掌握度配置 ----
const MASTERY_OPTS = [
    { value: 'unknown', color: 'bg-red-400', border: 'border-red-400', shadow: 'shadow-red-500/30', label: '未掌握' },
    { value: 'learning', color: 'bg-yellow-400', border: 'border-yellow-400', shadow: 'shadow-yellow-500/30', label: '学习中' },
    { value: 'mastered', color: 'bg-green-500', border: 'border-green-500', shadow: 'shadow-green-500/30', label: '已掌握' },
];

// 根据所有子条目计算章节整体掌握度
function calcChapterMastery(chapter, masteryData) {
    const ids = [
        ...(chapter.points || []).map(p => p.id),
        ...(chapter.examples || []).map((_, i) => `${chapter.id}_ex_${i}`),
    ];
    if (ids.length === 0) return 'unknown';
    const statuses = ids.map(id => masteryData[id] || 'unknown');
    if (statuses.every(s => s === 'mastered')) return 'mastered';
    if (statuses.some(s => s === 'learning' || s === 'mastered')) return 'learning';
    return 'unknown';
}

// ---- 主章节卡片 ----
export default function KnowledgeCard({ chapter, masteryData, onUpdateMastery, onOpenBranch }) {
    if (!chapter || !chapter.id) return null;

    const chapterMastery = calcChapterMastery(chapter, masteryData);
    const chapterOpt = MASTERY_OPTS.find(o => o.value === chapterMastery) || MASTERY_OPTS[0];

    return (
        <div className="mb-14 relative">
            {/* 时间线竖线 */}
            <div className="absolute left-4 top-12 bottom-[-40px] w-px bg-gray-100 z-0" />

            {/* 章节标题区 */}
            <div className="flex items-start gap-4 mb-5 relative z-10">
                {/* 章节掌握度指示灯（整体聚合，不可直接点击，仅可视） */}
                <div
                    title={`章节整体掌握度：${chapterOpt.label}`}
                    className={clsx(
                        "w-8 h-8 rounded-xl flex items-center justify-center shrink-0 border-2 shadow-sm transition-all",
                        chapterOpt.color,
                        chapterOpt.border
                    )}
                >
                    <Brain size={14} className="text-white" />
                </div>

                <div className="flex-1 pt-1">
                    <h2 className="font-bold text-xl text-gray-900 leading-snug">
                        {chapter.title}
                    </h2>
                    {chapter.summary && (
                        <p className="text-sm text-gray-500 mt-1 leading-relaxed max-w-2xl">
                            {chapter.summary}
                        </p>
                    )}
                    {/* 进度 mini bar */}
                    <ChapterProgressBar chapter={chapter} masteryData={masteryData} />
                </div>
            </div>

            {/* 知识点列表 */}
            <div className="pl-14 space-y-3 relative z-10">
                {(chapter.points || []).map((point) => (
                    <PointCard
                        key={point.id}
                        point={point}
                        mastery={masteryData[point.id] || 'unknown'}
                        onUpdateMastery={(level) => onUpdateMastery(point.id, level)}
                        onOpenBranch={() => onOpenBranch(point)}
                    />
                ))}

                {/* 例题区 */}
                {(chapter.examples || []).length > 0 && (
                    <ExamplesCard
                        examples={chapter.examples}
                        chapterId={chapter.id}
                        masteryData={masteryData}
                        onUpdateMastery={onUpdateMastery}
                        onOpenBranch={onOpenBranch}
                    />
                )}
            </div>
        </div>
    );
}

// ---- 章节进度条 ----
function ChapterProgressBar({ chapter, masteryData }) {
    const allIds = [
        ...(chapter.points || []).map(p => p.id),
        ...(chapter.examples || []).map((_, i) => `${chapter.id}_ex_${i}`),
    ];
    if (allIds.length === 0) return null;
    const mastered = allIds.filter(id => (masteryData[id] || 'unknown') === 'mastered').length;
    const learning = allIds.filter(id => (masteryData[id] || 'unknown') === 'learning').length;
    const total = allIds.length;
    const masteredPct = Math.round((mastered / total) * 100);
    const learningPct = Math.round((learning / total) * 100);

    return (
        <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden flex">
                <div className="h-full bg-green-400 transition-all duration-500" style={{ width: `${masteredPct}%` }} />
                <div className="h-full bg-yellow-300 transition-all duration-500" style={{ width: `${learningPct}%` }} />
            </div>
            <span className="text-[10px] text-gray-400 font-medium shrink-0">
                {mastered}/{total} 已掌握
            </span>
        </div>
    );
}

// ---- 知识点原子卡片 ----
function PointCard({ point, mastery, onUpdateMastery, onOpenBranch }) {
    const cycleMastery = (e) => {
        e.stopPropagation();
        const currentIndex = MASTERY_OPTS.findIndex(o => o.value === mastery);
        const nextIndex = (currentIndex + 1) % MASTERY_OPTS.length;
        onUpdateMastery(MASTERY_OPTS[nextIndex].value);
    };

    const currentOpt = MASTERY_OPTS.find(o => o.value === mastery) || MASTERY_OPTS[0];

    return (
        <div
            className="group bg-white border border-gray-100 rounded-xl px-4 py-3.5 shadow-sm hover:shadow-md hover:border-blue-200 transition-all cursor-pointer flex gap-3 items-start"
            onClick={onOpenBranch}
        >
            {/* 三色掌握度指示灯 */}
            <button
                onClick={cycleMastery}
                title={`当前：${currentOpt.label}（点击循环切换）`}
                className="mt-0.5 shrink-0 focus:outline-none"
            >
                <div className={clsx(
                    "w-3.5 h-3.5 rounded-full border-2 transition-all duration-300 hover:scale-125",
                    currentOpt.color,
                    currentOpt.border,
                    mastery !== 'unknown' && "shadow-[0_0_6px_0]",
                    mastery === 'learning' && "shadow-yellow-400/60",
                    mastery === 'mastered' && "shadow-green-400/60",
                )} />
            </button>

            <div className="flex-1 min-w-0">
                {/* 知识点名称 + 重要度星级 */}
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <h4 className="font-bold text-sm text-gray-800 leading-snug">{point.name}</h4>
                    <div className="flex gap-0.5 bg-gray-50 px-1.5 py-0.5 rounded-md border border-gray-100">
                        {[...Array(5)].map((_, i) => (
                            <Star
                                key={i}
                                size={11}
                                fill={i < (point.importance || 0) ? "#F59E0B" : "none"}
                                className={i < (point.importance || 0) ? "text-yellow-500" : "text-gray-200"}
                            />
                        ))}
                    </div>
                </div>
                {/* 内容解析 */}
                <p className="text-sm text-gray-600 leading-relaxed font-medium bg-gray-50/50 p-2.5 rounded-lg border border-gray-50">
                    {point.content}
                </p>
            </div>

            {/* 进入支线 hover 按钮 */}
            <div className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5">
                <span className="text-xs font-semibold text-blue-500 bg-blue-50 px-2 py-1 rounded-full flex items-center gap-1 whitespace-nowrap">
                    <PlayCircle size={12} />
                    深入探讨
                </span>
            </div>
        </div>
    );
}

// ---- 例题区块（可折叠，每道题目独立掌握度 + 支线入口）----
function ExamplesCard({ examples, chapterId, masteryData, onUpdateMastery, onOpenBranch }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="border border-dashed border-gray-200 rounded-xl overflow-hidden bg-gray-50/50">
            {/* 折叠 Header */}
            <div
                className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-gray-100/50 transition-colors"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-600">
                    <BookOpen size={15} className="text-blue-400" />
                    典型例题 ({examples.length} 题)
                </div>
                {expanded
                    ? <ChevronDown size={16} className="text-gray-400" />
                    : <ChevronRight size={16} className="text-gray-400" />
                }
            </div>

            {/* 展开内容 */}
            <div className={clsx(
                "overflow-hidden transition-all duration-300",
                expanded ? "max-h-[3000px] opacity-100" : "max-h-0 opacity-0"
            )}>
                <div className="px-4 pb-4 space-y-3 border-t border-gray-100 pt-3">
                    {examples.map((ex, i) => {
                        const exId = `${chapterId}_ex_${i}`;
                        const exMastery = masteryData[exId] || 'unknown';
                        const exOpt = MASTERY_OPTS.find(o => o.value === exMastery) || MASTERY_OPTS[0];

                        return (
                            <div
                                key={i}
                                className="group bg-white border border-gray-100 rounded-xl overflow-hidden hover:border-blue-200 transition-all cursor-pointer"
                                onClick={() => onOpenBranch({
                                    id: exId,
                                    name: `例题 ${i + 1}`,
                                    content: `${ex.question}\n\n[参考解答/解析]:\n${ex.solution}`
                                })}
                            >
                                <div className="px-4 py-3 flex items-start gap-3">
                                    {/* 例题掌握度指示灯 */}
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            const idx = MASTERY_OPTS.findIndex(o => o.value === exMastery);
                                            onUpdateMastery(exId, MASTERY_OPTS[(idx + 1) % MASTERY_OPTS.length].value);
                                        }}
                                        title={`当前：${exOpt.label}（点击切换）`}
                                        className="mt-1 shrink-0"
                                    >
                                        <div className={clsx(
                                            "w-3 h-3 rounded-full border-2 transition-all hover:scale-125",
                                            exOpt.color,
                                            exOpt.border
                                        )} />
                                    </button>

                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <Info size={13} className="text-blue-500 shrink-0" />
                                            <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                                                例题 {i + 1}
                                            </span>
                                        </div>
                                        <p className="text-sm font-medium text-gray-800 leading-relaxed">{ex.question}</p>
                                        {/* 答案/解析 - 悬停展开 */}
                                        <div className="mt-2 pl-2 border-l-2 border-blue-100">
                                            <p className="text-xs text-gray-300 font-semibold mb-0.5 uppercase tracking-wider">解析：</p>
                                            <p className="text-sm text-gray-500 leading-relaxed whitespace-pre-wrap">{ex.solution}</p>
                                        </div>
                                    </div>

                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5">
                                        <span className="text-xs font-semibold text-blue-500 bg-blue-50 px-2 py-1 rounded-full flex items-center gap-1 whitespace-nowrap">
                                            <PlayCircle size={12} />
                                            练习
                                        </span>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
