import React from 'react';
import { Layers, AlertTriangle, CheckCircle, XCircle, HelpCircle } from 'lucide-react';
import { ScenarioKey, DocumentType } from '../types';
import { getAvailableScenarios } from '../services/api';

interface ScenarioSelectorProps {
  selectedScenario: ScenarioKey;
  onSelectScenario: (scenario: ScenarioKey, recommendedDocType?: DocumentType) => void;
}

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  selectedScenario,
  onSelectScenario,
}) => {
  const scenarios = getAvailableScenarios();

  return (
    <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-xl p-5 shadow-panel">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-zinc-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded bg-amber-950/40 border border-amber-700/50 flex items-center justify-center text-amber-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-wide text-zinc-100 font-mono">
              EVALUATION SCENARIOS (MOCK ENGINE)
            </h3>
            <p className="text-[11px] text-zinc-400 font-mono">
              SELECT FORENSIC TEST SUITE CASE
            </p>
          </div>
        </div>

        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
          {scenarios.length} SCENARIOS CONFIGURED
        </span>
      </div>

      {/* Scenario Selection Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
        {scenarios.map((sc) => {
          const isSelected = selectedScenario === sc.id;

          let badgeIcon = CheckCircle;
          let badgeColor = 'text-emerald-400 border-emerald-500/30 bg-emerald-950/40';

          if (sc.outcome === 'REJECTED') {
            badgeIcon = XCircle;
            badgeColor = 'text-rose-400 border-rose-500/30 bg-rose-950/40';
          } else if (sc.outcome === 'MANUAL_REVIEW') {
            badgeIcon = AlertTriangle;
            badgeColor = 'text-amber-400 border-amber-500/30 bg-amber-950/40';
          } else if (sc.id === 'UNAVAILABLE_INCONCLUSIVE') {
            badgeIcon = HelpCircle;
            badgeColor = 'text-zinc-400 border-zinc-700 bg-zinc-800';
          }

          const BadgeIcon = badgeIcon;

          return (
            <button
              key={sc.id}
              type="button"
              onClick={() => onSelectScenario(sc.id as ScenarioKey, sc.document_type as DocumentType)}
              className={`text-left p-3 rounded-lg border transition-all flex flex-col justify-between font-mono ${
                isSelected
                  ? 'bg-zinc-800/90 border-cyan-500/70 shadow-glow-cyan text-zinc-100 ring-1 ring-cyan-500/40'
                  : 'bg-zinc-950/50 border-zinc-800/80 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border flex items-center space-x-1 ${badgeColor}`}>
                    <BadgeIcon className="w-2.5 h-2.5" />
                    <span>{sc.outcome}</span>
                  </span>
                  <span className="text-[9px] text-zinc-400">
                    {sc.document_type.replace('_', ' ')}
                  </span>
                </div>

                <div className="text-xs font-semibold text-zinc-200 mt-1">
                  {sc.label.replace('Scenario ', 'S').split(':')[1]?.trim() || sc.label}
                </div>
              </div>

              <div className="text-[10px] text-zinc-400 mt-2 line-clamp-2 leading-relaxed">
                {sc.description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
