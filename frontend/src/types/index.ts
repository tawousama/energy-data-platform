/**
 * Types TypeScript correspondant aux modèles du backend Python
 * 
 * Ces types reflètent exactement les schémas Pydantic de l'API
 */

// Enum pour les types de sites
export type SiteType = 'solar' | 'wind' | 'hydro' | 'nuclear' | 'thermal' | 'consumer';

// Interface Site (correspond au modèle Site Python)
export interface Site {
  id: number;
  name: string;
  site_type: SiteType;
  location: string;
  latitude: number | null;
  longitude: number | null;
  capacity_kw: number;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

// Interface pour créer un site
export interface SiteCreate {
  name: string;
  site_type: SiteType;
  location: string;
  latitude?: number;
  longitude?: number;
  capacity_kw: number;
  description?: string;
}

// Interface Meter
export interface Meter {
  id: number;
  site_id: number;
  meter_id: string;
  meter_type: 'production' | 'consumption';
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

// Interface ConsumptionReading
export interface ConsumptionReading {
  id: number;
  meter_id: number;
  timestamp: string;
  value_kwh: number;
  is_anomaly: boolean;
  anomaly_score: number | null;
  anomaly_status: 'pending' | 'verified' | 'ignored';
  created_at: string;
}

// Interface pour les données agrégées
export interface AggregatedConsumption {
  period: string;
  total_kwh: number;
  average_kwh: number;
  min_kwh: number | null;
  max_kwh: number | null;
  reading_count: number;
}

// Interface pour les statistiques
export interface ConsumptionStats {
  meter_id: number;
  period_days: number;
  total_kwh: number;
  daily_average_kwh: number;
  peak_kwh: number;
  anomaly_count: number;
}

// Interface pour le résumé des anomalies
export interface AnomalySummary {
  meter_id: number;
  period_days: number;
  total_readings: number;
  anomaly_count: number;
  anomaly_rate: number;
}

// Interface pour la détection d'anomalies
export interface AnomalyDetectionResponse {
  meter_id: number;
  method: 'zscore' | 'iqr' | 'moving_average';
  anomalies_detected: number;
  message: string;
}

// Interface pour les anomalies récentes
export interface RecentAnomaly {
  reading_id: number;
  meter_id: number;
  timestamp: string;
  value_kwh: number;
  anomaly_score: number;
  anomaly_status: 'pending' | 'verified' | 'ignored';
  severity: 'critique' | 'élevée' | 'modérée';
}

// Interface pour les statistiques d'un site
export interface SiteStatistics {
  site_id: number;
  site_name: string;
  total_meters: number;
  active_meters: number;
  capacity_kw: number;
}

// Types utilitaires
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

export interface ApiError {
  detail: string;
}