/**
 * AnalyticsPage - Page d'analyse et détection d'anomalies
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, TrendingUp, CheckCircle, XCircle } from 'lucide-react';
import { analyticsApi } from '../services/api';
import KPICard from '../components/Dashboard/KPICard';

const AnalyticsPage = () => {
  const [selectedMeterId, setSelectedMeterId] = useState(1);
  const [selectedMethod, setSelectedMethod] = useState<'zscore' | 'iqr' | 'moving_average'>('zscore');
  const queryClient = useQueryClient();

  // Récupérer les anomalies récentes
  const { data: recentAnomalies } = useQuery({
    queryKey: ['anomalies', 'recent'],
    queryFn: () => analyticsApi.getRecentAnomalies(72, 20),
  });

  // Récupérer le résumé des anomalies
  const { data: summary } = useQuery({
    queryKey: ['anomalies', 'summary', selectedMeterId],
    queryFn: () => analyticsApi.getAnomalySummary(selectedMeterId, 7),
  });

  // Mutation pour détecter les anomalies
  const detectMutation = useMutation({
    mutationFn: () => analyticsApi.detectAnomalies(selectedMeterId, selectedMethod),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
    },
  });

  const handleDetect = () => {
    detectMutation.mutate();
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critique: 'text-red-500 bg-red-500/10',
      élevée: 'text-orange-500 bg-orange-500/10',
      modérée: 'text-yellow-500 bg-yellow-500/10',
    };
    return colors[severity] || colors.modérée;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics & Anomalies</h1>
        <p className="mt-2 text-gray-400">
          Détection intelligente des anomalies énergétiques
        </p>
      </div>

      {/* KPIs */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Anomalies (24h)"
          value={recentAnomalies?.total_anomalies || 0}
          subtitle="Détectées automatiquement"
          icon={AlertTriangle}
          color="red"
        />
        
        <KPICard
          title="Taux d'Anomalies"
          value={summary ? `${(summary.anomaly_rate * 100).toFixed(2)}%` : '0%'}
          subtitle="Sur les 7 derniers jours"
          icon={TrendingUp}
          color="orange"
        />
        
        <KPICard
          title="Lectures Analysées"
          value={summary?.total_readings || 0}
          subtitle={`Compteur #${selectedMeterId}`}
          icon={CheckCircle}
          color="blue"
        />
        
        <KPICard
          title="Anomalies Totales"
          value={summary?.anomaly_count || 0}
          subtitle="Période de 7 jours"
          icon={XCircle}
          color={summary && summary.anomaly_count > 10 ? 'red' : 'green'}
        />
      </div>

      {/* Contrôles de détection */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">
          Détection d'Anomalies
        </h2>

        <div className="grid gap-4 md:grid-cols-3">
          {/* Sélection compteur */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Compteur
            </label>
            <input
              type="number"
              value={selectedMeterId}
              onChange={(e) => setSelectedMeterId(Number(e.target.value))}
              className="
                w-full px-4 py-2 
                bg-gray-800 border border-gray-700 rounded-lg
                text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500
              "
              min="1"
            />
          </div>

          {/* Sélection méthode */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Méthode de Détection
            </label>
            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value as typeof selectedMethod)}
              className="
                w-full px-4 py-2 
                bg-gray-800 border border-gray-700 rounded-lg
                text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500
              "
            >
              <option value="zscore">Z-Score (Rapide)</option>
              <option value="iqr">IQR (Robuste)</option>
              <option value="moving_average">Moving Average (Patterns)</option>
            </select>
          </div>

          {/* Bouton */}
          <div className="flex items-end">
            <button
              onClick={handleDetect}
              disabled={detectMutation.isPending}
              className="
                w-full px-4 py-2 
                bg-blue-600 hover:bg-blue-700 
                text-white font-medium rounded-lg
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors
              "
            >
              {detectMutation.isPending ? 'Analyse...' : 'Lancer la Détection'}
            </button>
          </div>
        </div>

        {/* Résultat de la détection */}
        {detectMutation.isSuccess && (
          <div className="mt-4 p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
            <p className="text-green-500">
              ✓ {detectMutation.data.message}
            </p>
          </div>
        )}

        {detectMutation.isError && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-red-500">
              ✗ Erreur lors de la détection
            </p>
          </div>
        )}
      </div>

      {/* Liste des anomalies récentes */}
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">
          Anomalies Récentes (24h)
        </h2>

        {recentAnomalies && recentAnomalies.anomalies.length > 0 ? (
          <div className="space-y-3">
            {recentAnomalies.anomalies.map((anomaly) => (
              <div
                key={anomaly.reading_id}
                className="flex items-center justify-between p-4 bg-gray-800 rounded-lg border border-gray-700"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(anomaly.severity)}`}>
                      {anomaly.severity.toUpperCase()}
                    </span>
                    <span className="text-sm text-gray-400">
                      Compteur #{anomaly.meter_id}
                    </span>
                  </div>
                  <p className="mt-2 text-white">
                    Valeur : {anomaly.value_kwh.toFixed(2)} kWh
                  </p>
                  <p className="text-sm text-gray-400">
                    {new Date(anomaly.timestamp).toLocaleString('fr-FR')}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm font-medium text-gray-400">Score</p>
                  <p className="text-lg font-bold text-white">
                    {anomaly.anomaly_score.toFixed(2)}σ
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <AlertTriangle className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>Aucune anomalie détectée dans les dernières 24h</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;