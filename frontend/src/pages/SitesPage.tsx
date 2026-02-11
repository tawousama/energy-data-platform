/**
 * SitesPage - Page listant tous les sites énergétiques
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter } from 'lucide-react';
import SitesList from '../components/Sites/SitesList';
import { sitesApi } from '../services/api';
import type { SiteType } from '../types';

const SitesPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<SiteType | 'all'>('all');

  // Récupérer tous les sites
  const { data: sites = [], isLoading, error } = useQuery({
    queryKey: ['sites', 'all'],
    queryFn: () => sitesApi.getAll(),
  });

  // Filtrer les sites
  const filteredSites = sites.filter((site) => {
    const matchesSearch = site.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         site.location.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'all' || site.site_type === filterType;
    return matchesSearch && matchesType;
  });

  const siteTypes = [
    { value: 'all', label: 'Tous' },
    { value: 'solar', label: 'Solaire' },
    { value: 'wind', label: 'Éolien' },
    { value: 'hydro', label: 'Hydraulique' },
    { value: 'nuclear', label: 'Nucléaire' },
    { value: 'thermal', label: 'Thermique' },
    { value: 'consumer', label: 'Consommateur' },
  ];

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-6 text-center">
        <p className="text-red-500">Erreur lors du chargement des sites</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Sites Énergétiques</h1>
        <p className="mt-2 text-gray-400">
          Gestion et monitoring de tous les sites
        </p>
      </div>

      {/* Filtres */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Recherche */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un site..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="
              w-full pl-10 pr-4 py-2 
              bg-gray-900 border border-gray-800 rounded-lg
              text-white placeholder-gray-500
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            "
          />
        </div>

        {/* Filtre par type */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as SiteType | 'all')}
            className="
              pl-10 pr-8 py-2 
              bg-gray-900 border border-gray-800 rounded-lg
              text-white
              focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
              appearance-none cursor-pointer
            "
          >
            {siteTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Statistiques */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            {filteredSites.length} site{filteredSites.length > 1 ? 's' : ''} trouvé{filteredSites.length > 1 ? 's' : ''}
          </span>
          <span className="text-gray-400">
            Capacité totale : {(filteredSites.reduce((sum, s) => sum + s.capacity_kw, 0) / 1000).toFixed(1)} MW
          </span>
        </div>
      </div>

      {/* Liste des sites */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <SitesList sites={filteredSites} />
      )}
    </div>
  );
};

export default SitesPage;