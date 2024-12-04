import React from 'react';
import { Bar } from 'react-chartjs-2';

interface ResourceUsageProps {
  data: {
    labels: string[];
    cpu: number[];
    memory: number[];
    disk: number[];
  };
}

export const ResourceUsage: React.FC<ResourceUsageProps> = ({ data }) => {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'CPU Usage',
        data: data.cpu,
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
      {
        label: 'Memory Usage',
        data: data.memory,
        backgroundColor: 'rgba(16, 185, 129, 0.5)',
        borderColor: 'rgb(16, 185, 129)',
        borderWidth: 1,
      },
      {
        label: 'Disk Usage',
        data: data.disk,
        backgroundColor: 'rgba(249, 115, 22, 0.5)',
        borderColor: 'rgb(249, 115, 22)',
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  };

  return <Bar data={chartData} options={options} />;
};
