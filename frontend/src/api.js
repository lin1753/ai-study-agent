// src/api.js
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000',
});

export const getSpaces = () => api.get('/spaces');
export const createSpace = (name) => api.post('/spaces', { name });
export const deleteSpace = (spaceId) => api.delete(`/spaces/${spaceId}`);
export const updateSpace = (spaceId, name) => api.put(`/spaces/${spaceId}`, { name });
export const uploadFile = (spaceId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/spaces/${spaceId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const uploadSupplementaryFile = (spaceId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/spaces/${spaceId}/upload_supplementary`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
};
export const getFileStatus = (jobId) => api.get(`/spaces/files/status/${jobId}`);
export const getBlocks = (spaceId) => api.get(`/spaces/${spaceId}/blocks`);
export const updateSpaceConfig = (spaceId, config) => api.put(`/spaces/${spaceId}/config`, config);
export const createBranch = (data) => api.post('/threads/branch', data);
export const getChatHistory = (threadId) => api.get(`/threads/${threadId}/history`);
export const getMainThread = (spaceId) => api.get(`/spaces/${spaceId}/main_thread`);
export const updateMastery = (spaceId, pointId, level) => api.put(`/spaces/${spaceId}/mastery`, { point_id: pointId, level });
export const getBranches = (spaceId) => api.get(`/spaces/${spaceId}/branches`);

// Streaming chat helper
export const getChatStreamUrl = () => 'http://127.0.0.1:8000/chat/stream';
export const getMainChatStreamUrl = () => 'http://127.0.0.1:8000/chat/main';

export default api;
