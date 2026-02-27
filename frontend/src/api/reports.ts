import apiClient from './client';
import type { Report, ReportsListResponse } from '../types/api';

export interface SaveReportRequest {
    item_type: string;
    description: string;
    color?: string;
    brand?: string;
    location?: string;
    intention: 'lost' | 'found';
    confidence_score?: number;
    routing?: string;
    action?: string;
    image_url?: string;
    validation_results?: Record<string, unknown>;
}

export const reportsApi = {
    /**
     * Save a validated report (persists to both Firestore and Supabase)
     */
    async saveReport(data: SaveReportRequest): Promise<{ report_id: string; message: string }> {
        const response = await apiClient.post('/reports', data);
        return response.data;
    },

    /**
     * Get all reports (uses /reports/all which has no Firebase auth requirement)
     */
    async getReports(limit: number = 20): Promise<ReportsListResponse> {
        try {
            const response = await apiClient.get('/reports/all', {
                params: { limit },
            });
            // Backend returns { reports: [], count: N }
            const data = response.data;
            if (Array.isArray(data)) {
                return { reports: data, count: data.length };
            }
            return data || { reports: [], count: 0 };
        } catch {
            // If reports endpoint fails, return empty list silently
            return { reports: [], count: 0 };
        }
    },

    /**
     * Get current user's reports (requires Supabase auth)
     */
    async getMyReports(): Promise<ReportsListResponse> {
        try {
            const response = await apiClient.get('/reports');
            const data = response.data;
            if (Array.isArray(data)) {
                return { reports: data, count: data.length };
            }
            return data || { reports: [], count: 0 };
        } catch {
            return { reports: [], count: 0 };
        }
    },

    /**
     * Get a specific report by ID
     */
    async getReport(id: string): Promise<Report> {
        const response = await apiClient.get(`/reports/${id}`);
        return response.data;
    },
};
