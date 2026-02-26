// src/components/ExamConfigModal.jsx
import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, BookOpen, Calculator, Server, Settings } from 'lucide-react';
import clsx from 'clsx';

const EXAM_TYPES = [
    { key: 'choice', label: '选择题', icon: '📝', default: 20 },
    { key: 'blank', label: '填空题', icon: '✍️', default: 10 },
    { key: 'judge', label: '判断题', icon: '✓✗', default: 10 },
    { key: 'short', label: '简答题', icon: '📄', default: 20 },
    { key: 'calc', label: '计算题', icon: '🔢', default: 30 },
    { key: 'comprehensive', label: '综合应用题', icon: '🎯', default: 10 },
];

export default function ExamConfigModal({ isOpen, onClose, onSubmit }) {
    const [step, setStep] = useState(1);
    const [weights, setWeights] = useState({});
    const [priorityChapters, setPriorityChapters] = useState('');

    // LLM Config
    const [llmProvider, setLlmProvider] = useState('local'); // 'local' or 'cloud'
    const [llmApiKey, setLlmApiKey] = useState('');
    const [llmBaseUrl, setLlmBaseUrl] = useState('https://api.deepseek.com/v1');
    const [llmModel, setLlmModel] = useState('deepseek-chat');

    useEffect(() => {
        if (isOpen) {
            // Initialize default weights
            const defaultWeights = {};
            EXAM_TYPES.forEach(type => {
                defaultWeights[type.key] = type.default;
            });
            setWeights(defaultWeights);
            setStep(1);
            setPriorityChapters('');
            // Keep previous LLM settings if already set in state
        }
    }, [isOpen]);

    const totalWeight = Object.values(weights).reduce((sum, val) => sum + val, 0);

    const handleWeightChange = (key, value) => {
        const newValue = Math.max(0, Math.min(100, parseInt(value) || 0));
        setWeights(prev => ({ ...prev, [key]: newValue }));
    };

    const handleSubmit = () => {
        const chapters = priorityChapters
            .split(/[,、，\s]+/)
            .map(ch => ch.trim().replace(/[^\d]/g, ''))
            .filter(ch => ch.length > 0);

        onSubmit({
            exam_weights: weights,
            priority_chapters: chapters,
            llm_provider: llmProvider,
            llm_api_key: llmApiKey,
            llm_base_url: llmBaseUrl,
            llm_model: llmModel
        });
        onClose();
    };

    const handleSkip = () => {
        onSubmit({
            exam_weights: {},
            priority_chapters: [],
            llm_provider: 'local',
            llm_api_key: '',
            llm_base_url: 'https://api.deepseek.com/v1',
            llm_model: 'deepseek-r1:7b'
        });
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 overflow-hidden">
                {/* Header */}
                <div className="px-6 py-4 border-b bg-gradient-to-r from-blue-50 to-indigo-50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center">
                                <Settings size={20} />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-gray-800">学习向导配置</h2>
                                <p className="text-xs text-gray-500">定制化引擎与复习侧重点</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-1 hover:bg-gray-200 rounded text-gray-400"
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Progress Indicator */}
                <div className="px-6 py-3 bg-gray-50 border-b">
                    <div className="flex items-center justify-center gap-2">
                        <div className={clsx(
                            "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                            step >= 1 ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-400"
                        )}>1</div>
                        <div className={clsx("w-8 h-0.5", step >= 2 ? "bg-blue-500" : "bg-gray-200")}></div>
                        <div className={clsx(
                            "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                            step >= 2 ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-400"
                        )}>2</div>
                        <div className={clsx("w-8 h-0.5", step >= 3 ? "bg-blue-500" : "bg-gray-200")}></div>
                        <div className={clsx(
                            "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                            step >= 3 ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-400"
                        )}>3</div>
                    </div>
                    <div className="flex justify-between mt-1 text-[10px] text-gray-500 font-medium px-6">
                        <span className="text-center">题型重点</span>
                        <span className="text-center">章节配置</span>
                        <span className="text-center">AI 引擎</span>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
                    {step === 1 && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <p className="text-sm text-gray-600 mb-4">
                                请配置本次考试各题型的分数占比（总和应为 100%）
                            </p>
                            {EXAM_TYPES.map(type => (
                                <div key={type.key} className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg">{type.icon}</span>
                                            <span className="text-sm font-medium text-gray-700">{type.label}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="number"
                                                min="0"
                                                max="100"
                                                value={weights[type.key] || 0}
                                                onChange={(e) => handleWeightChange(type.key, e.target.value)}
                                                className="w-16 px-2 py-1 text-sm text-right border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                                            />
                                            <span className="text-sm text-gray-500 w-4">%</span>
                                        </div>
                                    </div>
                                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-blue-500 transition-all duration-300"
                                            style={{ width: `${weights[type.key] || 0}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                            <div className={clsx(
                                "mt-4 p-3 rounded-lg text-sm font-medium text-center",
                                totalWeight === 100 ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                            )}>
                                总计: {totalWeight}% {totalWeight === 100 ? '✓' : `(需调整为 100%)`}
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    <BookOpen size={16} className="inline mr-1" />
                                    请标注本次考试的重点章节（可选）
                                </label>
                                <input
                                    type="text"
                                    value={priorityChapters}
                                    onChange={(e) => setPriorityChapters(e.target.value)}
                                    placeholder="例如: 3, 5, 7 (多个章节用逗号分隔)"
                                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                />
                                <p className="text-xs text-gray-500 mt-2">
                                    提示：标注为重点的章节会获得更高的权重，AI 会为其生成更多练习题
                                </p>
                            </div>

                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h4 className="text-sm font-bold text-blue-900 mb-2">📊 您的配置预览</h4>
                                <div className="space-y-1 text-xs text-blue-800">
                                    <p>• 题型重点: {Object.entries(weights).filter(([k, v]) => v > 0).sort((a, b) => b[1] - a[1]).slice(0, 2).map(([k, v]) => EXAM_TYPES.find(t => t.key === k)?.label).join('、')}</p>
                                    {priorityChapters && <p>• 重点章节: {priorityChapters || '未设置'}</p>}
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-5 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div>
                                <h3 className="text-sm font-bold text-gray-700 flex items-center gap-2 mb-3">
                                    <Server size={16} className="text-blue-500" /> AI 引擎设置 (Model Provider)
                                </h3>
                                <div className="flex gap-4">
                                    <label className="flex items-center gap-2 cursor-pointer p-3 border rounded-xl flex-1 hover:bg-gray-50 transition-colors">
                                        <input type="radio" value="local" checked={llmProvider === 'local'} onChange={(e) => setLlmProvider(e.target.value)} className="text-blue-500 focus:ring-blue-500" />
                                        <div className="text-sm font-medium">
                                            本地模型
                                            <div className="text-[10px] text-gray-400 font-normal">使用 Ollama 内置大模型</div>
                                        </div>
                                    </label>
                                    <label className="flex items-center gap-2 cursor-pointer p-3 border rounded-xl flex-1 hover:bg-gray-50 transition-colors">
                                        <input type="radio" value="cloud" checked={llmProvider === 'cloud'} onChange={(e) => setLlmProvider(e.target.value)} className="text-blue-500 focus:ring-blue-500" />
                                        <div className="text-sm font-medium">
                                            云端 API
                                            <div className="text-[10px] text-gray-400 font-normal">连接第三方大模型服务</div>
                                        </div>
                                    </label>
                                </div>
                            </div>

                            {llmProvider === 'cloud' && (
                                <div className="space-y-3 bg-gray-50 p-4 rounded-xl border border-gray-200">
                                    <div>
                                        <label className="block text-xs font-semibold text-gray-600 mb-1">API Key</label>
                                        <input type="password" value={llmApiKey} onChange={e => setLlmApiKey(e.target.value)} placeholder="sk-..." className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-1 focus:ring-blue-500 outline-none" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-semibold text-gray-600 mb-1">Base URL</label>
                                        <input type="text" value={llmBaseUrl} onChange={e => setLlmBaseUrl(e.target.value)} placeholder="https://api.deepseek.com/v1" className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-1 focus:ring-blue-500 outline-none" />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-semibold text-gray-600 mb-1">Model Name</label>
                                        <input type="text" value={llmModel} onChange={e => setLlmModel(e.target.value)} placeholder="deepseek-chat" className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-1 focus:ring-blue-500 outline-none" />
                                    </div>
                                </div>
                            )}

                            {llmProvider === 'local' && (
                                <div className="p-4 bg-blue-50 text-blue-800 rounded-xl text-sm border border-blue-100 leading-relaxed">
                                    将使用本地部署的 <strong className="font-bold underline">deepseek-r1:7b</strong> 模型。
                                    <br /><span className="text-xs text-blue-600 mt-1 block">请确保您已在后台运行 Ollama 并且成功拉取了该模型文件。</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
                    <button
                        onClick={handleSkip}
                        className="text-sm text-gray-500 hover:text-gray-700 font-medium"
                    >
                        跳过配置
                    </button>
                    <div className="flex gap-2">
                        {step > 1 && (
                            <button
                                onClick={() => setStep(step - 1)}
                                className="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg font-medium flex items-center gap-1 transition-colors"
                            >
                                <ChevronLeft size={16} />
                                上一步
                            </button>
                        )}
                        {step < 3 ? (
                            <button
                                onClick={() => setStep(step + 1)}
                                disabled={step === 1 && totalWeight !== 100}
                                className={clsx(
                                    "px-4 py-2 text-sm rounded-lg font-medium flex items-center gap-1 transition-colors",
                                    step === 1 && totalWeight !== 100
                                        ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                                        : "bg-blue-500 hover:bg-blue-600 text-white shadow-sm"
                                )}
                            >
                                下一步
                                <ChevronRight size={16} />
                            </button>
                        ) : (
                            <button
                                onClick={handleSubmit}
                                className="px-5 py-2 text-sm bg-black hover:bg-gray-800 text-white rounded-lg font-medium shadow-sm transition-colors"
                            >
                                开始生成路径
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
