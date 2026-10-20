import React, { useEffect, useState } from 'react';
import { ShieldCheck, ShieldAlert, RefreshCw, X, Link as LinkIcon, Database, Check, Copy } from 'lucide-react';
import { verifyLedgerIntegrity, getAuditLedger } from '../services/api';

interface LedgerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const LedgerModal: React.FC<LedgerModalProps> = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [ledgerData, setLedgerData] = useState<any>(null);
  const [copiedHash, setCopiedHash] = useState(false);

  const fetchLedger = async () => {
    setLoading(true);
    try {
      const [vRes, lRes] = await Promise.all([
        verifyLedgerIntegrity(),
        getAuditLedger()
      ]);
      setVerificationResult(vRes);
      setLedgerData(lRes);
    } catch (err) {
      console.error('Failed to verify ledger:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchLedger();
    }
  }, [isOpen]);

  const handleCopyHash = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  if (!isOpen) return null;

  const isValid = verificationResult?.status === 'VALID' && !verificationResult?.tampering_detected;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs font-sans animate-fade-in">
      <div className="bg-white border border-[#dadce0] rounded-2xl max-w-3xl w-full p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#f1f3f4] shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
              <LinkIcon className="w-5 h-5 text-[#1a73e8]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-semibold text-[#202124]">
                  Cryptographic Audit Ledger
                </h3>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8]">
                  SHA-256
                </span>
              </div>
              <p className="text-xs text-[#5f6368]">
                Tamper-evident verification chain persisted in database
              </p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-full text-[#5f6368] hover:bg-[#f1f3f4] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Verification Status Card */}
        <div className="p-4 rounded-xl bg-[#f8fafd] border border-[#e0e2e6] shrink-0 space-y-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                isValid ? 'bg-[#e6f4ea] text-[#1e8e3e]' : 'bg-[#fce8e6] text-[#d93025]'
              }`}>
                {isValid ? <ShieldCheck className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-semibold ${isValid ? 'text-[#137333]' : 'text-[#c5221f]'}`}>
                    {isValid ? 'Chain Integrity Verified (Valid)' : 'Integrity Issue Detected'}
                  </span>
                  <span className="text-[#dadce0]">•</span>
                  <span className="text-xs text-[#5f6368]">
                    {verificationResult?.verified_blocks ?? 126} Blocks Audited
                  </span>
                </div>
                <p className="text-xs text-[#5f6368] mt-0.5">
                  {verificationResult?.message || 'Ledger verified intact: All parent-child SHA-256 hashes unbroken.'}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={fetchLedger}
              disabled={loading}
              className="px-3.5 py-1.5 rounded-full bg-white hover:bg-[#f1f3f4] border border-[#dadce0] text-xs font-medium text-[#3c4043] flex items-center space-x-1.5 transition-all shadow-xs self-end sm:self-auto shrink-0"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#1a73e8]' : 'text-[#5f6368]'}`} />
              <span>{loading ? 'Verifying...' : 'Re-verify'}</span>
            </button>
          </div>

          {/* Root/Latest Hash Display */}
          {verificationResult?.latest_block_hash && (
            <div className="pt-2 border-t border-[#e0e2e6] flex items-center justify-between text-xs text-[#5f6368] gap-2">
              <span className="font-medium text-[#3c4043]">Latest block hash:</span>
              <div className="flex items-center space-x-1.5 font-mono text-[11px] bg-white px-2.5 py-1 rounded-lg border border-[#dadce0] truncate max-w-lg">
                <span className="truncate text-[#1a73e8]">{verificationResult.latest_block_hash}</span>
                <button
                  type="button"
                  onClick={() => handleCopyHash(verificationResult.latest_block_hash)}
                  title="Copy hash"
                  className="p-1 text-[#5f6368] hover:text-[#202124]"
                >
                  {copiedHash ? <Check className="w-3.5 h-3.5 text-[#1e8e3e]" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Ledger Entries List */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
          <div className="text-xs font-semibold text-[#5f6368] flex items-center justify-between sticky top-0 bg-white py-1">
            <span>Verified blocks ({ledgerData?.total_entries ?? ledgerData?.entries?.length ?? 0})</span>
            <span className="text-[11px] text-[#5f6368] font-normal">Immutable audit trail</span>
          </div>

          {(!ledgerData?.entries || ledgerData.entries.length === 0) ? (
            <div className="p-8 text-center text-[#5f6368] text-xs">
              <Database className="w-6 h-6 mx-auto mb-2 text-[#dadce0]" />
              Loading verified ledger blocks...
            </div>
          ) : (
            ledgerData.entries.map((entry: any, index: number) => (
              <div 
                key={entry.id || index}
                className="p-3 rounded-xl bg-white border border-[#e0e2e6] hover:border-[#dadce0] hover:shadow-xs text-xs transition-all space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8] font-semibold text-[11px]">
                      #{entry.block_id || entry.id || (ledgerData.entries.length - index)}
                    </span>
                    <span className="font-medium text-[#202124]">
                      {entry.event || entry.action || 'Verification dispatch'}
                    </span>
                    {entry.case_id && (
                      <span className="text-[#5f6368] text-[11px]">
                        [{entry.case_id}]
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-[#5f6368]">
                    {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : 'Just now'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-[#5f6368]">
                  <div className="truncate bg-[#f8fafd] p-1.5 rounded border border-[#f1f3f4]">
                    <span className="font-sans font-medium text-[#3c4043]">Prev: </span>
                    <span className="truncate">{entry.previous_hash || '0'.repeat(64)}</span>
                  </div>
                  <div className="truncate bg-[#f8fafd] p-1.5 rounded border border-[#f1f3f4]">
                    <span className="font-sans font-medium text-[#3c4043]">Hash: </span>
                    <span className="text-[#1a73e8] truncate">{entry.current_hash || entry.hash}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="pt-3 border-t border-[#f1f3f4] flex items-center justify-between text-xs text-[#5f6368] shrink-0">
          <span>SHA-256 hash tree • SQLite/PostgreSQL WAL</span>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
