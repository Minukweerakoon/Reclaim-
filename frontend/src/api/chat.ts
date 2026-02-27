import apiClient from './client';
import type { ChatRequest, ChatResponse } from '../types/api';

export const chatApi = {
    /**
     * Send a chat message
     */
    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        const response = await apiClient.post('/chat/message', request);
        return response.data;
    },
};
