import React from 'react';
import { Layers } from 'lucide-react';
import { getAvailableScenarios } from '../services/api';

interface GlobalScenarioBarProps {
  activeScenarioId?: string;
  onSelectScenario: (scenarioId: string) => void;
}

export const GlobalScenarioBar: React.FC<GlobalScenarioBarProps> = ({
  activeScenarioId,
  onSelectScenario,
}) => {
  const scenarios = getAvailableScenarios();

  return (
    <div className="bg-white border border-[#dadce0] rounded-2xl p-3 shadow-xs font-sans text-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 mb-2 border-b border-[#f1f3f4]">
        <div className="flex items-center space-x-2">
          <div className="w-5 h-5 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
            <Layers className="w-3 h-3 text-[#1a73e8]" />
          </div>
          <span className="font-semibold text-[#202124]">Test Scenarios (Demonstration Presets)</span>
        </div>
        <span className="text-[11px] text-[#5f6368] hidden md:inline">
          Switch test specimen payloads instantly
        </span>
      </div>

      <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
        {scenarios.map((sc) => {
          const isActive = activeScenarioId === sc.id;

          let badgeColor = 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]';
          if (sc.outcome === 'REJECTED') {
            badgeColor = 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]';
          } else if (sc.outcome === 'MANUAL_REVIEW') {
            badgeColor = 'bg-[#fef7e0] text-[#b06000] border-[#feefc3]';
          }

          return (
            <button
              key={sc.id}
              type="button"
              onClick={() => onSelectScenario(sc.id)}
              className={`px-3 py-1.5 rounded-full border whitespace-nowrap text-left transition-all flex items-center space-x-2 text-xs font-medium ${
                isActive
                  ? 'bg-[#e8f0fe] border-[#1a73e8] text-[#1a73e8] shadow-xs'
                  : 'bg-white border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043]'
              }`}
            >
              <span className={`text-[10px] px-2 py-0.2 rounded-full border ${badgeColor}`}>
                {sc.outcome === 'APPROVED' ? 'Pass' : sc.outcome === 'REJECTED' ? 'Fail' : 'Review'}
              </span>
              <span>{sc.label.replace('Scenario ', 'S').split(':')[1]?.trim() || sc.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
