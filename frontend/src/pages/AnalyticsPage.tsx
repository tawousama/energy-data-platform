/**
 * AnalyticsPage V2 - Page d'analyse avec filtres dynamiques
 */

import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MdWarning, MdCheckCircle, MdCancel } from 'react-icons/md';
import { analyticsApi, sitesApi } from '../services/api';
import KPICard from '../components/Dashboard/KPICard';

type PeriodFilter = '24h' | '48h' | '7d' | '30d';
type StatusFilter = 'all' | 'pending' | 'verified' | 'ignored';

const AnalyticsPage = () => {
  // États des filtres
  const [selectedPeriod, setSelectedPeriod] = useState<PeriodFilter>('7d');
  const [selectedStatus, setSelectedStatus] = useState<StatusFilter>('all');
  const [selectedMeterId, setSelectedMeterId] = useState<number | 'all'>('all');
  const [selectedMethod, setSelectedMethod] = useState<'zscore' | 'iqr' | 'moving_average'>('zscore');

  const queryClient = useQueryClient();

  // Calculer les heures selon la période
  const periodHours = useMemo(() => {
    const periods = { '24h': 24, '48h': 48, '7d': 168, '30d': 720 };
    return periods[selectedPeriod];
  }, [selectedPeriod]);

  // Labels pour l'affichage
  const periodLabels = {
    '24h': '24 heures',
    '48h': '48 heures',
    '7d': '7 jours',
    '30d': '30 jours',
  };

  const statusLabels = {
    all: 'Toutes',
    pending: 'À vérifier',
    verified: 'Vérifiées',
    ignored: 'Ignorées',
  };

  // Récupérer les sites/compteurs disponibles
  const { data: sites = [] } = useQuery({
    queryKey: ['sites'],
    queryFn: () => sitesApi.getAll(),
  });

  // Récupérer les anomalies
  const { data: recentAnomalies, refetch: refetchAnomalies } = useQuery({
    queryKey: ['anomalies', 'recent', periodHours],
    queryFn: () => analyticsApi.getRecentAnomalies(periodHours, 100),
  });

  // Récupérer le résumé (si un compteur spécifique est sélectionné)
  const { data: summary } = useQuery({
    queryKey: ['anomalies', 'summary', selectedMeterId, selectedPeriod],
    queryFn: () => analyticsApi.getAnomalySummary(
      selectedMeterId as number,
      Math.floor(periodHours / 24)
    ),
    enabled: selectedMeterId !== 'all',
  });

  // Mutation pour détecter les anomalies
  const detectMutation = useMutation({
    mutationFn: () => {
      if (selectedMeterId === 'all') {
        return analyticsApi.detectAnomalies(1, selectedMethod);
      }
      return analyticsApi.detectAnomalies(selectedMeterId as number, selectedMethod);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      refetchAnomalies();
    },
  });

  // Mutation pour changer le statut
  const updateStatusMutation = useMutation({
    mutationFn: ({ readingId, status }: { readingId: number; status: 'pending' | 'verified' | 'ignored' }) =>
      analyticsApi.updateAnomalyStatus(readingId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['anomalies'] });
      refetchAnomalies();
    },
  });

  // Filtrer les anomalies selon les critères
  const filteredAnomalies = useMemo(() => {
    if (!recentAnomalies?.anomalies) return [];

    return recentAnomalies.anomalies.filter((anomaly) => {
      if (selectedMeterId !== 'all' && anomaly.meter_id !== selectedMeterId) {
        return false;
      }

      if (selectedStatus !== 'all' && anomaly.anomaly_status !== selectedStatus) {
        return false;
      }

      return true;
    });
  }, [recentAnomalies, selectedMeterId, selectedStatus]);

  // Statistiques filtrées
  const stats = useMemo(() => {
    const pending = filteredAnomalies.filter(a => a.anomaly_status === 'pending').length;
    const verified = filteredAnomalies.filter(a => a.anomaly_status === 'verified').length;
    const ignored = filteredAnomalies.filter(a => a.anomaly_status === 'ignored').length;

    return { total: filteredAnomalies.length, pending, verified, ignored };
  }, [filteredAnomalies]);

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critique: 'text-red-500 bg-red-500/10 border-red-500/20',
      élevée: 'text-orange-500 bg-orange-500/10 border-orange-500/20',
      modérée: 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20',
    };
    return colors[severity] || colors.modérée;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-500/10 text-yellow-500',
      verified: 'bg-green-500/10 text-green-500',
      ignored: 'bg-gray-500/10 text-gray-500',
    };
    return colors[status] || colors.pending;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics & Anomalies</h1>
        <p className="mt-2 text-gray-400">
          Détection intelligente et gestion des anomalies énergétiques
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title={`Total (${periodLabels[selectedPeriod]})`}
          value={stats.total}
          subtitle="Anomalies détectées"
          icon={MdWarning}
          color="blue"
        />
        
        <KPICard
          title="À Vérifier"
          value={stats.pending}
          subtitle="En attente d'action"
          icon={MdWarning}
          color="orange"
        />
        
        <KPICard
          title="Vérifiées"
          value={stats.verified}
          subtitle="Anomalies confirmées"
          icon={MdCheckCircle}
          color="green"
        />
        
        <KPICard
          title="Ignorées"
          value={stats.ignored}
          subtitle="Fausses alertes"
          icon={MdCancel}
          color="purple"
        />
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Filtres</h2>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Période</label>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value as PeriodFilter)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="24h">Dernières 24h</option>
              <option value="48h">Dernières 48h</option>
              <option value="7d">7 derniers jours</option>
              <option value="30d">30 derniers jours</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Compteur</label>
            <select
              value={selectedMeterId}
              onChange={(e) => setSelectedMeterId(e.target.value === 'all' ? 'all' : Number(e.target.value))}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Tous les compteurs</option>
              {Array.from({ length: 10 }, (_, i) => i + 1).map(id => (
                <option key={id} value={id}>Compteur #{id}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Statut</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as StatusFilter)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Toutes</option>
              <option value="pending">À vérifier</option>
              <option value="verified">Vérifiées</option>
              <option value="ignored">Ignorées</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Méthode</label>
            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value as typeof selectedMethod)}
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="zscore">Z-Score (Rapide)</option>
              <option value="iqr">IQR (Robuste)</option>
              <option value="moving_average">Moving Average</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <button
            onClick={() => detectMutation.mutate()}
            disabled={detectMutation.isPending}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50 transition-colors"
          >
            {detectMutation.isPending ? 'Analyse...' : 'Lancer la Détection'}
          </button>

          {detectMutation.isSuccess && (
            <div className="flex items-center px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg">
              <p className="text-green-500 text-sm">✓ {detectMutation.data.message}</p>
            </div>
          )}
        </div>
      </div>

      <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">
            Anomalies {statusLabels[selectedStatus]} ({periodLabels[selectedPeriod]})
          </h2>
          <span className="text-sm text-gray-400">
            {filteredAnomalies.length} résultat{filteredAnomalies.length > 1 ? 's' : ''}
          </span>
        </div>

        {filteredAnomalies.length > 0 ? (
          <div className="space-y-3">
            {filteredAnomalies.map((anomaly) => (
              <div
                key={anomaly.reading_id}
                className="flex items-center justify-between p-4 bg-gray-800 rounded-lg border border-gray-700"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(anomaly.severity)}`}>
                      {anomaly.severity.toUpperCase()}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(anomaly.anomaly_status)}`}>
                      {statusLabels[anomaly.anomaly_status]}
                    </span>
                    <span className="text-sm text-gray-400">Compteur #{anomaly.meter_id}</span>
                  </div>
                  <p className="text-white font-medium">Valeur : {anomaly.value_kwh.toFixed(2)} kWh</p>
                  <p className="text-sm text-gray-400">{new Date(anomaly.timestamp).toLocaleString('fr-FR')}</p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-400">Score</p>
                    <p className="text-lg font-bold text-white">{anomaly.anomaly_score.toFixed(2)}σ</p>
                  </div>

                  <div className="flex gap-2">
                    {anomaly.anomaly_status !== 'verified' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ readingId: anomaly.reading_id, status: 'verified' })}
                        className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded"
                      >
                        Vérifier
                      </button>
                    )}
                    {anomaly.anomaly_status !== 'ignored' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ readingId: anomaly.reading_id, status: 'ignored' })}
                        className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded"
                      >
                        Ignorer
                      </button>
                    )}
                    {anomaly.anomaly_status !== 'pending' && (
                      <button
                        onClick={() => updateStatusMutation.mutate({ readingId: anomaly.reading_id, status: 'pending' })}
                        className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded"
                      >
                        Réouvrir
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <MdWarning className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>Aucune anomalie trouvée avec ces filtres</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;
