import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { MetricTimeSeriesPoint } from '../../types';

interface ChartProps {
  data: MetricTimeSeriesPoint[];
  metricType?: 'cpu' | 'memory';
  height?: number;
}

export const ResourceUtilizationChart: React.FC<ChartProps> = ({
  data,
  metricType = 'cpu',
  height = 240
}) => {
  const isCpu = metricType === 'cpu';

  return (
    <div className="w-full" style={{ height: `${height}px` }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="cpuColor" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="memoryColor" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#56e5a9" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#56e5a9" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1c2b3c" vertical={false} />
          <XAxis
            dataKey="timestamp"
            stroke="#87929a"
            tick={{ fill: '#bdc8d1', fontSize: 11 }}
            axisLine={{ stroke: '#273647' }}
          />
          <YAxis
            stroke="#87929a"
            tick={{ fill: '#bdc8d1', fontSize: 11 }}
            axisLine={{ stroke: '#273647' }}
            domain={[0, 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0d1c2d',
              borderColor: '#273647',
              borderRadius: '8px',
              color: '#d4e4fa',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              fontSize: '12px'
            }}
          />
          {isCpu ? (
            <>
              <Area
                type="monotone"
                dataKey="cpuLimit"
                name="CPU Limit"
                stroke="#ffb4ab"
                strokeWidth={1}
                strokeDasharray="4 4"
                fill="none"
              />
              <Area
                type="monotone"
                dataKey="cpuRequest"
                name="CPU Request"
                stroke="#a4c9ff"
                strokeWidth={1.5}
                strokeDasharray="2 2"
                fill="none"
              />
              <Area
                type="monotone"
                dataKey="cpuUsage"
                name="CPU Usage (Cores)"
                stroke="#38bdf8"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#cpuColor)"
              />
            </>
          ) : (
            <>
              <Area
                type="monotone"
                dataKey="memoryLimitMb"
                name="Memory Limit (MB)"
                stroke="#ffb4ab"
                strokeWidth={1}
                strokeDasharray="4 4"
                fill="none"
              />
              <Area
                type="monotone"
                dataKey="memoryUsageMb"
                name="Memory Usage (MB)"
                stroke="#56e5a9"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#memoryColor)"
              />
            </>
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
