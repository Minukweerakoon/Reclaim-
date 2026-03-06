import axios from 'axios';
import type { HealthStatus } from '../types/api';

export const healthApi = {
    /**
     * Get system health status (no auth required)
     */
    async getHealth(): Promise<HealthStatus> {
        const response = await axios.get('/health');
        return response.data;
    },
};
