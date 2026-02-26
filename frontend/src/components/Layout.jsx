// src/components/Layout.jsx
import React, { useState, useCallback, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
    const [sidebarWidth, setSidebarWidth] = useState(260);
    const [isDragging, setIsDragging] = useState(false);

    const handleMouseDown = useCallback((e) => {
        setIsDragging(true);
        e.preventDefault(); // Prevent text selection
    }, []);

    const handleMouseMove = useCallback((e) => {
        if (!isDragging) return;

        let newWidth = e.clientX;
        if (newWidth < 180) newWidth = 180;
        if (newWidth > 400) newWidth = 400;

        setSidebarWidth(newWidth);
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
            className="flex h-screen bg-gray-50 font-sans select-none"
            style={{ cursor: isDragging ? 'ew-resize' : 'default' }}
        >
            <div style={{ width: sidebarWidth, flexShrink: 0 }} className="h-full">
                <Sidebar />
            </div>

            {/* Splitter */}
            <div
                onMouseDown={handleMouseDown}
                className="w-1 cursor-ew-resize bg-gray-200 hover:bg-blue-400 active:bg-blue-500 transition-colors z-50 h-full relative"
            >
                {/* Invisible wider hit area for easier grabbing */}
                <div className="absolute inset-y-0 -left-1 -right-1 z-50"></div>
            </div>

            <div className={`flex-1 overflow-hidden relative ${isDragging ? 'pointer-events-none' : ''}`}>
                <Outlet />
            </div>
        </div>
    );
}
