import React, { useState, useEffect } from 'react';
import { X, Server } from 'lucide-react';

export default function SettingsModal({ isOpen, onClose }) {
    const [llmProvider, setLlmProvider] = useState('local'); // 'local' or 'cloud'
    const [llmApiKey, setLlmApiKey] = useState('');
    const [llmBaseUrl, setLlmBaseUrl] = useState('https://api.deepseek.com/v1');
    const [llmModel, setLlmModel] = useState('deepseek-chat');

    // Load from localStorage on mount
    useEffect(() => {
        if (isOpen) {
            setLlmProvider(localStorage.getItem('llm_provider') || 'local');
            setLlmApiKey(localStorage.getItem('llm_api_key') || '');
            setLlmBaseUrl(localStorage.getItem('llm_base_url') || 'https://api.deepseek.com/v1');
            setLlmModel(localStorage.getItem('llm_model') || 'deepseek-chat');
        }
    }, [isOpen]);

    const handleSave = () => {
        localStorage.setItem('llm_provider', llmProvider);
        localStorage.setItem('llm_api_key', llmApiKey);
        localStorage.setItem('llm_base_url', llmBaseUrl);
        localStorage.setItem('llm_model', llmModel);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl mx-4 overflow-hidden relative">
                {/* Header */}
                <div className="px-6 py-4 border-b bg-gray-50 flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                        <Server size={20} className="text-blue-500" /> 全局系统设置
                    </h2>
                    <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded-lg text-gray-500 transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 bg-white space-y-5">
                    <div>
                        <h3 className="text-sm font-bold text-gray-700 mb-3">AI 引擎设置 (Model Provider)</h3>
                        <p className="text-xs text-gray-500 mb-4">
                            配置提取文档原题及生成知识点所使用的大模型引擎。当前配置将在所有学科空间通用，一键生效。
                        </p>
                        <div className="flex gap-4">
                            <label className="flex items-center gap-2 cursor-pointer p-4 border rounded-xl flex-1 hover:bg-gray-50 transition-colors group">
                                <input 
                                    type="radio" 
                                    value="local" 
                                    checked={llmProvider === 'local'} 
                                    onChange={(e) => setLlmProvider(e.target.value)} 
                                    className="text-blue-500 focus:ring-blue-500 w-4 h-4 cursor-pointer" 
                                />
                                <div>
                                    <div className="text-sm font-semibold text-gray-800">本地模型 Local</div>
                                    <div className="text-xs text-gray-400 mt-0.5">使用 Ollama 内置运行的大模型</div>
                                </div>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer p-4 border rounded-xl flex-1 hover:bg-gray-50 transition-colors group">
                                <input 
                                    type="radio" 
                                    value="cloud" 
                                    checked={llmProvider === 'cloud'} 
                                    onChange={(e) => setLlmProvider(e.target.value)} 
                                    className="text-blue-500 focus:ring-blue-500 w-4 h-4 cursor-pointer" 
                                />
                                <div>
                                    <div className="text-sm font-semibold text-gray-800">云端 API Cloud</div>
                                    <div className="text-xs text-gray-400 mt-0.5">连接第三方云端大模型服务</div>
                                </div>
                            </label>
                        </div>
                    </div>

                    {llmProvider === 'cloud' && (
                        <div className="space-y-4 bg-gray-50/50 p-5 rounded-xl border border-gray-100">
                            <div>
                                <label className="block text-xs font-semibold text-gray-600 mb-1.5">API Key <span className="text-red-500">*</span></label>
                                <input 
                                    type="password" 
                                    value={llmApiKey} 
                                    onChange={e => setLlmApiKey(e.target.value)} 
                                    placeholder="sk-..." 
                                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" 
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Base URL <span className="text-red-500">*</span></label>
                                <input 
                                    type="text" 
                                    value={llmBaseUrl} 
                                    onChange={e => setLlmBaseUrl(e.target.value)} 
                                    placeholder="https://api.deepseek.com/v1" 
                                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" 
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-gray-600 mb-1.5">Model Name <span className="text-red-500">*</span></label>
                                <input 
                                    type="text" 
                                    value={llmModel} 
                                    onChange={e => setLlmModel(e.target.value)} 
                                    placeholder="deepseek-chat" 
                                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all" 
                                />
                            </div>
                        </div>
                    )}

                    {llmProvider === 'local' && (
                        <div className="p-4 bg-blue-50/80 text-blue-900 rounded-xl text-sm border border-blue-100/50 leading-relaxed flex gap-3">
                            <span className="text-xl">💡</span>
                            <div>
                                将使用本地默认的 <strong className="font-bold px-1 text-blue-700">deepseek-r1:7b</strong> 模型体系。
                                <br />
                                <span className="text-xs text-blue-600/80 mt-1.5 block font-medium">请确保后台已启动 Ollama 并已拉取相应模型。如果希望提取速度更快，推荐切换为 Cloud API 云端模型。</span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-end gap-3">
                    <button 
                        onClick={onClose} 
                        className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        取消
                    </button>
                    <button 
                        onClick={handleSave} 
                        className="px-6 py-2 text-sm font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm shadow-blue-500/30 transition-all hover:scale-[1.02] active:scale-[0.98]"
                    >
                        保存全局设置
                    </button>
                </div>
            </div>
        </div>
    );
}