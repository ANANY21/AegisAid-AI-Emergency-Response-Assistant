import React from 'react';
import { PriorityLevel } from '../types';
import { AlertCircle, AlertTriangle, ShieldCheck, Flame } from 'lucide-react';

interface PriorityBadgeProps {
  priority: PriorityLevel;
  confidence?: number;
  showIcon?: boolean;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({ priority, confidence, showIcon = true }) => {
  const config = {
    CRITICAL: {
      bg: 'bg-emergency-900/40',
      border: 'border-emergency-500/60',
      text: 'text-emergency-500',
      glow: 'shadow-lg shadow-emergency-600/30 ring-1 ring-emergency-500',
      icon: Flame,
      label: 'CRITICAL EMERGENCY'
    },
    HIGH: {
      bg: 'bg-amber-950/40',
      border: 'border-amber-500/50',
      text: 'text-amber-400',
      glow: 'shadow-md shadow-amber-500/20',
      icon: AlertTriangle,
      label: 'HIGH PRIORITY'
    },
    MODERATE: {
      bg: 'bg-blue-950/40',
      border: 'border-blue-500/40',
      text: 'text-blue-400',
      glow: '',
      icon: AlertCircle,
      label: 'MODERATE URGENCY'
    },
    LOW: {
      bg: 'bg-emerald-950/40',
      border: 'border-emerald-500/40',
      text: 'text-emerald-400',
      glow: '',
      icon: ShieldCheck,
      label: 'LOW / ROUTINE'
    }
  }[priority] || {
    bg: 'bg-slate-900',
    border: 'border-slate-700',
    text: 'text-slate-300',
    glow: '',
    icon: AlertCircle,
    label: priority
  };

  const IconComponent = config.icon;

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border ${config.bg} ${config.border} ${config.text} ${config.glow}`}>
      {showIcon && <IconComponent className="w-4 h-4 animate-pulse" />}
      <span className="text-xs font-black tracking-wider uppercase">{config.label}</span>
      {confidence !== undefined && (
        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-slate-300 border border-white/10">
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
};
