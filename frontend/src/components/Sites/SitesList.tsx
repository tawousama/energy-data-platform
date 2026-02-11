/**
 * SitesList - Liste des sites énergétiques
 */

import { MapPin, Zap } from 'lucide-react';
import type { Site } from '../../types';

interface SitesListProps {
  sites: Site[];
  onSiteClick?: (site: Site) => void;
}

const SitesList = ({ sites, onSiteClick }: SitesListProps) => {
  const getSiteTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      solar: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
      wind: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      hydro: 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
      nuclear: 'bg-purple-500/10 text-purple-500 border-purple-500/20',
      thermal: 'bg-red-500/10 text-red-500 border-red-500/20',
      consumer: 'bg-gray-500/10 text-gray-500 border-gray-500/20',
    };
    return colors[type] || colors.consumer;
  };

  const getSiteTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      solar: 'Solaire',
      wind: 'Éolien',
      hydro: 'Hydraulique',
      nuclear: 'Nucléaire',
      thermal: 'Thermique',
      consumer: 'Consommateur',
    };
    return labels[type] || type;
  };

  if (sites.length === 0) {
    return (
      <div className="bg-gray-900 rounded-lg border border-gray-800 p-8 text-center">
        <MapPin className="h-12 w-12 text-gray-600 mx-auto mb-3" />
        <p className="text-gray-400">Aucun site disponible</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {sites.map((site) => (
        <div
          key={site.id}
          onClick={() => onSiteClick?.(site)}
          className={`
            bg-gray-900 rounded-lg border border-gray-800 p-6
            hover:border-gray-700 transition-all duration-200
            ${onSiteClick ? 'cursor-pointer hover:shadow-lg' : ''}
          `}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-white mb-1 line-clamp-1">
                {site.name}
              </h3>
              <div className="flex items-center text-sm text-gray-400">
                <MapPin className="h-4 w-4 mr-1" />
                {site.location}
              </div>
            </div>
            
            <div className={`px-2 py-1 rounded-md text-xs font-medium border ${getSiteTypeColor(site.site_type)}`}>
              {getSiteTypeLabel(site.site_type)}
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-800">
            <div className="flex items-center text-sm">
              <Zap className="h-4 w-4 text-yellow-500 mr-2" />
              <span className="text-gray-300">
                {site.capacity_kw.toLocaleString()} kW
              </span>
            </div>
            
            {site.latitude && site.longitude && (
              <div className="text-xs text-gray-500">
                {site.latitude.toFixed(2)}°, {site.longitude.toFixed(2)}°
              </div>
            )}
          </div>

          {/* Description */}
          {site.description && (
            <p className="mt-3 text-sm text-gray-400 line-clamp-2">
              {site.description}
            </p>
          )}
        </div>
      ))}
    </div>
  );
};

export default SitesList;