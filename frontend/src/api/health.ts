import axios from 'axios';
import type { HealthStatus } from '../types/api';
import { apiOrigin } from './config';

export const healthApi = {
    /**
     * Get system health status (no auth required)
     */
    async getHealth(): Promise<HealthStatus> {
        const response = await axios.get(`${apiOrigin}/health`);
        return response.data;
    },
};
