import React, { useState, useEffect } from 'react';
import { Shield, Cpu, Activity, Server, Link as LinkIcon, User, ChevronDown } from 'lucide-react';
import { isMockMode, setMockMode, getApiBaseUrl, checkHealth, getStoredUser } from '../services/api';
import { LoginModal } from './LoginModal';
import { LedgerModal } from './LedgerModal';

interface HeaderProps {
  currentCaseId?: string | null;
}

export const Header: React.FC<HeaderProps> = ({ currentCaseId }) => {
  const [mockActive, setMockActiveState] = useState<boolean>(isMockMode());
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [user, setUser] = useState<{ email: string; role: string }>(getStoredUser());
  const [isLoginOpen, setIsLoginOpen] = useState<boolean>(false);
  const [isLedgerOpen, setIsLedgerOpen] = useState<boolean>(false);
  const baseUrl = getApiBaseUrl();

  useEffect(() => {
    let mounted = true;
    const pollHealth = async () => {
      const status = await checkHealth();
      if (mounted) {
        setIsOnline(status.online);
      }
    };

    pollHealth();
    const interval = setInterval(pollHealth, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleToggleMock = () => {
    const nextMode = !mockActive;
    setMockMode(nextMode);
    setMockActiveState(nextMode);
  };

  return (
    <>
      <header className="border-b border-[#e0e2e6] bg-white/95 backdrop-blur-sm sticky top-0 z-50 font-sans">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Brand & Suite Identification */}
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8] shadow-sm">
              <Shield className="w-5 h-5 text-[#1a73e8]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-[#202124]">TRUST-ID</span>
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[#e8f0fe] text-[#1a73e8]">
                  Enterprise
                </span>
              </div>
              <p className="text-xs text-[#5f6368] font-normal">
                Identity Verification & Biometric Forensics
              </p>
            </div>
          </div>

          {/* Telemetry, Controls & Modals */}
          <div className="flex items-center space-x-2.5 text-xs">
            {currentCaseId && (
              <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#f1f3f4] text-[#3c4043] border border-[#dadce0]">
                <span className="text-[#5f6368]">Case:</span>
                <span className="text-[#1a73e8] font-semibold">{currentCaseId}</span>
              </div>
            )}

            {/* Cryptographic Ledger Modal Trigger */}
            <button
              type="button"
              onClick={() => setIsLedgerOpen(true)}
              title="Verify cryptographic hash-chain ledger integrity"
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full border border-[#dadce0] bg-white hover:bg-[#f8fafd] text-[#3c4043] font-medium text-xs transition-colors shadow-sm"
            >
              <LinkIcon className="w-3.5 h-3.5 text-[#1a73e8]" />
              <span className="hidden sm:inline">Audit Ledger</span>
            </button>

            {/* Officer Profile Chip */}
            <button
              type="button"
              onClick={() => setIsLoginOpen(true)}
              title="Officer session / Switch account"
              className="flex items-center space-x-2 px-3 py-1.5 rounded-full border border-[#dadce0] bg-white hover:bg-[#f8fafd] text-[#3c4043] text-xs font-medium transition-colors shadow-sm"
            >
              <div className="w-5 h-5 rounded-full bg-[#1a73e8] text-white flex items-center justify-center text-[10px] font-bold">
                {user.email ? user.email.charAt(0).toUpperCase() : 'O'}
              </div>
              <span className="truncate max-w-[90px]">{user.role || 'Officer'}</span>
              <ChevronDown className="w-3 h-3 text-[#5f6368]" />
            </button>

            {/* Engine Mode Toggle (Mock vs Live POST /api/v1/verify) */}
            <button
              type="button"
              onClick={handleToggleMock}
              title={`Switch engine mode: currently ${mockActive ? 'Mock Simulator' : 'Live FastAPI Backend (8000)'}`}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-all shadow-sm ${
                mockActive
                  ? 'bg-[#fef7e0] border-[#feefc3] text-[#b06000] hover:bg-[#feefc3]'
                  : 'bg-[#e6f4ea] border-[#ceead6] text-[#137333] hover:bg-[#ceead6]'
              }`}
            >
              {mockActive ? (
                <>
                  <Cpu className="w-3.5 h-3.5 text-[#e37400]" />
                  <span className="hidden md:inline">Mock Mode</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/70">Sim</span>
                </>
              ) : (
                <>
                  <Server className="w-3.5 h-3.5 text-[#1e8e3e]" />
                  <span className="hidden md:inline">Live API</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-white/70 font-semibold">8000</span>
                </>
              )}
            </button>

            {/* Real-time Health Telemetry */}
            <div className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-full border ${
              isOnline 
                ? 'bg-[#e6f4ea] border-[#ceead6] text-[#137333]' 
                : 'bg-[#fce8e6] border-[#fad2cf] text-[#c5221f]'
            }`}>
              <span className={`w-2 h-2 rounded-full ${isOnline ? 'bg-[#1e8e3e] animate-pulse' : 'bg-[#d93025]'}`} />
              <span className="text-[11px] font-medium hidden sm:inline">{isOnline ? 'Online' : 'Offline'}</span>
            </div>
          </div>

        </div>
      </header>

      {/* Modals */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLoginSuccess={(loggedUser) => setUser(loggedUser)}
      />
      <LedgerModal
        isOpen={isLedgerOpen}
        onClose={() => setIsLedgerOpen(false)}
      />
    </>
  );
};
