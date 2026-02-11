/**
 * Layout - Structure principale de l'application
 */
import React from "react";
import { Outlet } from 'react-router-dom';
import Navbar from './NavBar';

const Layout = () => {
  return (
    <div className="min-h-screen bg-gray-950">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer optionnel */}
      <footer className="bg-gray-900 border-t border-gray-800 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-400">
            Energy Data Platform © 2024 - Developed for StarClay
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;