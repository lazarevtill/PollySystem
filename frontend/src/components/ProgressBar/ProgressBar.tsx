import React from 'react';

interface ProgressBarProps {
  value: number;
  max: number;
  color: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ value, max, color }) => {
  const percentage = Math.min(100, (value / max) * 100);
  return (
    <div className="w-full h-2 bg-gray-200 rounded-full">
      <div 
        className={`h-full rounded-full ${color}`} 
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};