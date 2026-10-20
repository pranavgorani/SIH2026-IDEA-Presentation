import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FolderKanban, 
  Search, 
  RefreshCw, 
  Filter,
  ArrowRight,
  Plus
} from 'lucide-react';
import { getCases } from '../services/api';
import { getOutcomeBadgeStyles, getRiskBadgeInfo, formatDocumentType } from '../utils/formatters';

export const CasesPage: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('ALL');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await getCases();
      setCases(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch cases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const filteredCases = cases.filter(c => {
    const matchesSearch = 
      (c.case_id && c.case_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (c.full_name && c.full_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (c.document_type && c.document_type.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (c.document_number && c.document_number.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const riskLevel = c.risk_level || (c.overall_score < 30 ? 'LOW' : c.overall_score < 60 ? 'MEDIUM' : 'HIGH');
    const matchesRisk = filterRisk === 'ALL' || riskLevel === filterRisk;

    return matchesSearch && matchesRisk;
  });

  return (
    <div className="space-y-6 pb-16 font-sans">
      {/* Top Banner */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 sm:p-7 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
              <FolderKanban className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-[#202124] tracking-tight">
                  Verification Dossier Registry
                </h1>
                <span className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8]">
                  Database
                </span>
              </div>
              <p className="text-xs text-[#5f6368] mt-0.5">
                Sovereign verification records with hash-chained integrity logs ({cases.length} cases indexed)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={fetchCases}
              disabled={loading}
              className="px-4 py-2 rounded-full border border-[#dadce0] hover:bg-[#f8fafd] text-xs font-medium text-[#3c4043] flex items-center space-x-2 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#1a73e8]' : 'text-[#5f6368]'}`} />
              <span>{loading ? 'Syncing...' : 'Sync Registry'}</span>
            </button>
            <button
              type="button"
              onClick={() => navigate('/upload')}
              className="px-5 py-2 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white font-medium text-xs flex items-center space-x-1.5 transition-all shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Verification</span>
            </button>
          </div>
        </div>

        {/* Filter / Search Bar */}
        <div className="mt-6 pt-5 border-t border-[#f1f3f4] flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-[#5f6368] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Case ID, name, document..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[#f8fafd] border border-[#dadce0] rounded-full pl-9 pr-4 py-2 text-xs text-[#202124] placeholder-[#80868b] focus:outline-none focus:border-[#1a73e8] focus:bg-white transition-all"
            />
          </div>

          <div className="flex items-center space-x-1.5 text-xs w-full sm:w-auto overflow-x-auto">
            <span className="text-[#5f6368] font-medium text-xs flex items-center space-x-1 shrink-0 mr-1">
              <Filter className="w-3.5 h-3.5" />
              <span>Risk:</span>
            </span>
            {['ALL', 'LOW', 'MEDIUM', 'HIGH'].map(lvl => (
              <button
                key={lvl}
                onClick={() => setFilterRisk(lvl)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors shrink-0 ${
                  filterRisk === lvl
                    ? 'bg-[#1a73e8] text-white shadow-xs'
                    : 'bg-[#f1f3f4] hover:bg-[#e8eaed] text-[#3c4043]'
                }`}
              >
                {lvl === 'ALL' ? 'All' : lvl.charAt(0) + lvl.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Cases Table */}
      <div className="bg-white border border-[#dadce0] rounded-3xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#f1f3f4] bg-[#fafbfc] text-[#5f6368] font-medium text-[11px]">
                <th className="py-3.5 px-4">Case ID</th>
                <th className="py-3.5 px-4">Subject / Holder</th>
                <th className="py-3.5 px-4">Document</th>
                <th className="py-3.5 px-4">Processed</th>
                <th className="py-3.5 px-4">Risk Score</th>
                <th className="py-3.5 px-4">Decision</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f1f3f4]">
              {filteredCases.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[#5f6368]">
                    {loading ? (
                      <div className="flex items-center justify-center space-x-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-[#1a73e8]" />
                        <span>Querying case registry...</span>
                      </div>
                    ) : (
                      <span>No matching verification dossiers found. Run a new verification to create one.</span>
                    )}
                  </td>
                </tr>
              ) : (
                filteredCases.map((c) => {
                  const score = typeof c.overall_score === 'number' ? c.overall_score : 0;
                  const level = c.risk_level ?? 'LOW';
                  const riskBadge = getRiskBadgeInfo(score, level);
                  const outcome = c.decision || c.status || 'PROCESSED';
                  const outcomeBadge = getOutcomeBadgeStyles(outcome);
                  const holderName = c.full_name && c.full_name !== 'UNKNOWN' ? c.full_name : '—';
                  const formattedTime = c.processed_at 
                    ? new Date(c.processed_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                    : 'Recent';

                  return (
                    <tr key={c.case_id} className="hover:bg-[#f8fafd] transition-colors">
                      <td className="py-3.5 px-4">
                        <button
                          type="button"
                          onClick={() => navigate(`/result?caseId=${encodeURIComponent(c.case_id)}`)}
                          className="font-semibold text-[#1a73e8] hover:underline text-left"
                        >
                          {c.case_id}
                        </button>
                      </td>
                      <td className="py-3.5 px-4 text-[#202124] font-medium">
                        {holderName}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex flex-col">
                          <span className="font-medium text-[#3c4043]">{formatDocumentType(c.document_type)}</span>
                          <span className="text-[11px] font-mono text-[#5f6368]">{c.document_number || '—'}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-[#5f6368]">
                        {formattedTime}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium ${riskBadge.badge}`}>
                          {score} • {riskBadge.label}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full border text-[11px] font-medium ${outcomeBadge.bg}`}>
                          {outcomeBadge.label}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            type="button"
                            onClick={() => navigate(`/result?caseId=${encodeURIComponent(c.case_id)}`)}
                            className="px-3 py-1 rounded-full border border-[#dadce0] hover:bg-white text-[#3c4043] text-xs font-medium transition-colors"
                          >
                            Dossier
                          </button>
                          <button
                            type="button"
                            onClick={() => navigate(`/human-review?caseId=${encodeURIComponent(c.case_id)}`)}
                            className="px-3 py-1 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white text-xs font-medium transition-colors"
                          >
                            Adjudicate
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
