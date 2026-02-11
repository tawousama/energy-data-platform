/**
 * HomePage - Dashboard principal avec KPIs et graphiques
 */

import { useQuery } from '@tanstack/react-query';
import { MapPin, Zap, Activity, AlertTriangle } from 'lucide-react';
import KPICard from '../components/Dashboard/KPICard';
import ConsumptionChart from '../components/Charts/ConsumptionChart';
import SitesList from '../components/Sites/SitesList';
import { sitesApi, consumptionApi, analyticsApi } from '../services/api';

const HomePage = () => {
  // Récupérer les sites
  const { data: sites = [], isLoading: sitesLoading } = useQuery({
    queryKey: ['sites'],
    queryFn: () => sitesApi.getAll({ limit: 10 }),
  });

  // Récupérer les données de consommation (pour le premier compteur en exemple)
  const { data: dailyData = [] } = useQuery({
    queryKey: ['consumption', 'daily', 1],
    queryFn: () => consumptionApi.getDailyAggregation(1, 7),
    enabled: sites.length > 0,
  });

  // Récupérer les anomalies récentes
  const { data: anomaliesData } = useQuery({
    queryKey: ['anomalies', 'recent'],
    queryFn: () => analyticsApi.getRecentAnomalies(24, 10),
  });

  // Calculer les KPIs
  const totalSites = sites.length;
  const activeSites = sites.filter(s => s.site_type !== 'consumer').length;
  const totalCapacity = sites.reduce((sum, site) => sum + site.capacity_kw, 0);
  const totalAnomalies = anomaliesData?.total_anomalies || 0;

  if (sitesLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="mt-2 text-gray-400">
          Vue d'ensemble de la plateforme énergétique
        </p>
      </div>

      {/* KPIs */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Sites"
          value={totalSites}
          subtitle={`${activeSites} sites de production`}
          icon={MapPin}
          color="blue"
        />
        
        <KPICard
          title="Capacité Totale"
          value={`${(totalCapacity / 1000).toFixed(1)} MW`}
          subtitle="Puissance installée"
          icon={Zap}
          color="orange"
        />
        
        <KPICard
          title="Compteurs Actifs"
          value={sites.length * 2}
          subtitle="Monitoring en temps réel"
          icon={Activity}
          color="green"
        />
        
        <KPICard
          title="Anomalies (24h)"
          value={totalAnomalies}
          subtitle="Détectées automatiquement"
          icon={AlertTriangle}
          color={totalAnomalies > 5 ? 'red' : 'green'}
        />
      </div>

      {/* Graphique */}
      <ConsumptionChart 
        data={dailyData} 
        title="Consommation des 7 derniers jours"
        height={400}
      />

      {/* Sites récents */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Sites Énergétiques</h2>
        <SitesList sites={sites.slice(0, 6)} />
      </div>
    </div>
  );
};

export default HomePage;

