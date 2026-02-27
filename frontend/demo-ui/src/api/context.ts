import apiClient from './client';
import type { SpatialTemporalRequest, SpatialTemporalResponse, SpatialTemporalStats } from '../types/api';

export const contextApi = {
    /**
     * Validate spatial-temporal plausibility of an item-location-time combination
     */
    async validateContext(request: SpatialTemporalRequest): Promise<SpatialTemporalResponse> {
        const response = await apiClient.post('/validate/context', request);
        return response.data;
    },

    /**
     * Get spatial-temporal statistics
     */
    async getStats(): Promise<SpatialTemporalStats> {
        const response = await apiClient.get('/spatial-temporal/stats');
        return response.data;
    },
};
