/**
 * ConsumptionChart - Graphique de consommation énergétique
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { AggregatedConsumption } from '../../types';

interface ConsumptionChartProps {
  data: AggregatedConsumption[];
  title?: string;
  height?: number;
}

const ConsumptionChart = ({ data, title = 'Energy Consumption', height = 300 }: ConsumptionChartProps) => {
  // Formater les données pour Recharts
  const chartData = data.map((item) => ({
    period: new Date(item.period).toLocaleDateString('fr-FR', {
      month: 'short',
      day: 'numeric',
    }),
    total: Math.round(item.total_kwh),
    average: Math.round(item.average_kwh),
    min: item.min_kwh ? Math.round(item.min_kwh) : 0,
    max: item.max_kwh ? Math.round(item.max_kwh) : 0,
  }));

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 p-6">
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="period" 
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
            label={{ value: 'kWh', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F9FAFB',
            }}
          />
          <Legend 
            wrapperStyle={{ color: '#9CA3AF' }}
          />
          <Line 
            type="monotone" 
            dataKey="total" 
            stroke="#3B82F6" 
            strokeWidth={2}
            name="Total (kWh)"
            dot={{ fill: '#3B82F6' }}
          />
          <Line 
            type="monotone" 
            dataKey="average" 
            stroke="#10B981" 
            strokeWidth={2}
            name="Average (kWh)"
            dot={{ fill: '#10B981' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ConsumptionChart;