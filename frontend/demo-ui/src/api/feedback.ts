import apiClient from './client';
import type { FeedbackRequest, FeedbackResponse, FeedbackStats } from '../types/api';

export const feedbackApi = {
    /**
     * Submit user correction feedback for active learning
     */
    async submitFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
        const response = await apiClient.post('/feedback/submit', feedback);
        return response.data;
    },

    /**
     * Get active learning statistics
     */
    async getStats(): Promise<FeedbackStats> {
        const response = await apiClient.get('/feedback/stats');
        return response.data;
    },
};
