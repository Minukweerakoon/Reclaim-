import apiClient from './client';
import type { AttentionMapRequest, AttentionMapResponse, XAIExplainRequest, XAIExplainResponse } from '../types/api';

export const xaiApi = {
    /**
     * Generate attention heatmap for an image
     */
    async getAttentionMap(request: AttentionMapRequest): Promise<AttentionMapResponse> {
        const response = await apiClient.post('/xai/attention', request);
        return response.data;
    },

    /**
     * Get enhanced explainability analysis for discrepancies
     */
    async explainEnhanced(request: XAIExplainRequest): Promise<XAIExplainResponse> {
        const response = await apiClient.post('/xai/explain-enhanced', request);
        return response.data;
    },
};
