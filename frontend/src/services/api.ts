/**
 * Service API pour communiquer avec le backend FastAPI
 * 
 * Utilise Axios pour les requêtes HTTP
 */

import axios from 'axios';
import type {
  Site,
  SiteCreate,
  Meter,
  ConsumptionReading,
  AggregatedConsumption,
  ConsumptionStats,
  AnomalySummary,
  AnomalyDetectionResponse,
  RecentAnomaly,
  SiteStatistics,
  PaginationParams,
} from '../types';

// Configuration de l'URL de base de l'API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
console.log('API URL:', API_BASE_URL);
const API_V1 = `${API_BASE_URL}api/v1`;

// Instance Axios configurée
const apiClient = axios.create({
  baseURL: API_V1,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour logger les erreurs (utile en dev)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ==================== SITES ====================

export const sitesApi = {
  /**
   * Récupère tous les sites avec filtres optionnels
   */
  getAll: async (params?: PaginationParams & { 
    site_type?: string; 
    search?: string;
  }): Promise<Site[]> => {
    const response = await apiClient.get<Site[]>('/sites', { params });
    return response.data;
  },

  /**
   * Récupère un site par son ID
   */
  getById: async (id: number): Promise<Site> => {
    const response = await apiClient.get<Site>(`/sites/${id}`);
    return response.data;
  },

  /**
   * Crée un nouveau site
   */
  create: async (site: SiteCreate): Promise<Site> => {
    const response = await apiClient.post<Site>('/sites', site);
    return response.data;
  },

  /**
   * Met à jour un site
   */
  update: async (id: number, site: Partial<SiteCreate>): Promise<Site> => {
    const response = await apiClient.put<Site>(`/sites/${id}`, site);
    return response.data;
  },

  /**
   * Supprime un site
   */
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/sites/${id}`);
  },

  /**
   * Récupère les statistiques d'un site
   */
  getStatistics: async (id: number): Promise<SiteStatistics> => {
    const response = await apiClient.get<SiteStatistics>(`/sites/${id}/statistics`);
    return response.data;
  },
};

// ==================== CONSUMPTION ====================

export const consumptionApi = {
  /**
   * Récupère les lectures de consommation
   */
  getReadings: async (params?: {
    meter_id?: number;
    start_date?: string;
    end_date?: string;
    only_anomalies?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<ConsumptionReading[]> => {
    const response = await apiClient.get<ConsumptionReading[]>('/consumption/readings', { params });
    return response.data;
  },

  /**
   * Crée une nouvelle lecture
   */
  createReading: async (reading: {
    meter_id: number;
    timestamp: string;
    value_kwh: number;
  }): Promise<ConsumptionReading> => {
    const response = await apiClient.post<ConsumptionReading>('/consumption/readings', reading);
    return response.data;
  },

  /**
   * Récupère les données agrégées par heure
   */
  getHourlyAggregation: async (meter_id: number, days: number = 7): Promise<AggregatedConsumption[]> => {
    const response = await apiClient.get<AggregatedConsumption[]>('/consumption/aggregated/hourly', {
      params: { meter_id, days },
    });
    return response.data;
  },

  /**
   * Récupère les données agrégées par jour
   */
  getDailyAggregation: async (meter_id: number, days: number = 30): Promise<AggregatedConsumption[]> => {
    const response = await apiClient.get<AggregatedConsumption[]>('/consumption/aggregated/daily', {
      params: { meter_id, days },
    });
    return response.data;
  },

  /**
   * Récupère les statistiques de consommation
   */
  getStats: async (meter_id: number, days: number = 7): Promise<ConsumptionStats> => {
    const response = await apiClient.get<ConsumptionStats>(`/consumption/stats/${meter_id}`, {
      params: { days },
    });
    return response.data;
  },
};

// ==================== ANALYTICS ====================

export const analyticsApi = {
  /**
   * Déclenche la détection d'anomalies
   */
  detectAnomalies: async (
    meter_id: number,
    method: 'zscore' | 'iqr' | 'moving_average' = 'zscore'
  ): Promise<AnomalyDetectionResponse> => {
    const response = await apiClient.post<AnomalyDetectionResponse>(
      `/analytics/anomalies/detect/${meter_id}`,
      null,
      { params: { method } }
    );
    return response.data;
  },

  /**
   * Récupère le résumé des anomalies
   */
  getAnomalySummary: async (meter_id: number, days: number = 7): Promise<AnomalySummary> => {
    const response = await apiClient.get<AnomalySummary>(`/analytics/anomalies/summary/${meter_id}`, {
      params: { days },
    });
    return response.data;
  },

  /**
   * Récupère les anomalies récentes
   */
  getRecentAnomalies: async (hours: number = 24, limit: number = 50): Promise<{
    period_hours: number;
    total_anomalies: number;
    anomalies: RecentAnomaly[];
  }> => {
    const response = await apiClient.get('/analytics/anomalies/recent', {
      params: { hours, limit },
    });
    return response.data;
  },

  /**
   * Réinitialise les flags d'anomalies
   */
  resetAnomalies: async (meter_id: number): Promise<void> => {
    await apiClient.delete(`/analytics/anomalies/reset/${meter_id}`);
  },

  /**
   * Met à jour le statut d'une anomalie
   */
  updateAnomalyStatus: async (
    reading_id: number,
    status: 'pending' | 'verified' | 'ignored'
  ): Promise<{ message: string }> => {
    const response = await apiClient.patch(`/analytics/anomalies/${reading_id}/status`, {
      status,
    });
    return response.data;
  },
};

// Export tout
export default {
  sites: sitesApi,
  consumption: consumptionApi,
  analytics: analyticsApi,
};