import apiClient from './client';
import type { EntityDetectionRequest, EntityDetectionResponse, EntityType } from '../types/api';

export const entitiesApi = {
    /**
     * Detect entities from text (uses text-based entity extraction)
     */
    async detectEntities(request: EntityDetectionRequest): Promise<EntityDetectionResponse> {
        const response = await apiClient.post('/entities/detect/text', request);
        return response.data;
    },

    /**
     * Get available entity types
     */
    async getEntityTypes(): Promise<EntityType[]> {
        const response = await apiClient.get('/entities/types');
        return response.data;
    },
};
