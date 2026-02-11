/**
 * Navbar - Barre de navigation principale
 */

import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, MapPin, Activity, Settings } from 'lucide-react';

const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/sites', label: 'Sites', icon: MapPin },
    { path: '/analytics', label: 'Analytics', icon: Activity },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <Activity className="h-8 w-8 text-blue-500" />
              <span className="text-xl font-bold text-white">
                Energy Platform
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <div className="flex space-x-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`
                    flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium
                    transition-colors duration-200
                    ${
                      active
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* User menu (optionnel) */}
          <div className="flex items-center">
            <div className="text-sm text-gray-400">
              Demo Mode
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;