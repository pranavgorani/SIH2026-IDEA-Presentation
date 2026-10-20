import React, { useState } from 'react';
import { Shield, Lock, X, Check } from 'lucide-react';
import { loginUser } from '../services/api';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { email: string; role: string }) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [email, setEmail] = useState('admin@trustid.demo');
  const [password, setPassword] = useState('admin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await loginUser(email, password);
      if (res.success && res.user) {
        onLoginSuccess(res.user);
        onClose();
      } else {
        setError('Invalid credentials.');
      }
    } catch {
      setError('Connection to authentication service failed.');
    } finally {
      setLoading(false);
    }
  };

  const setPresetUser = (presetEmail: string) => {
    setEmail(presetEmail);
    setPassword(presetEmail.split('@')[0]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs font-sans animate-fade-in">
      <div className="bg-white border border-[#dadce0] rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#f1f3f4]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-[#202124]">
                Officer Sign In
              </h3>
              <p className="text-xs text-[#5f6368]">TRUST-ID Enterprise Portal</p>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-1.5 rounded-full text-[#5f6368] hover:bg-[#f1f3f4] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="text-xs font-medium text-[#3c4043] block mb-1.5">Email address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white border border-[#dadce0] rounded-lg px-3.5 py-2.5 text-sm text-[#202124] focus:outline-none focus:border-[#1a73e8] focus:ring-2 focus:ring-[#e8f0fe] transition-all"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-[#3c4043] block mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white border border-[#dadce0] rounded-lg px-3.5 py-2.5 text-sm text-[#202124] focus:outline-none focus:border-[#1a73e8] focus:ring-2 focus:ring-[#e8f0fe] transition-all"
            />
          </div>

          {error && (
            <div className="p-2.5 rounded-lg bg-[#fce8e6] border border-[#fad2cf] text-[#c5221f] text-xs">
              {error}
            </div>
          )}

          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-sm"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>{loading ? 'Authenticating...' : 'Sign In as Officer'}</span>
            </button>
          </div>
        </form>

        {/* Preset Roles */}
        <div className="pt-3 border-t border-[#f1f3f4] space-y-2">
          <span className="text-[#5f6368] font-medium text-[11px] block">Quick test accounts:</span>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setPresetUser('admin@trustid.demo')}
              className={`p-2 rounded-xl border text-center transition-all ${
                email.includes('admin')
                  ? 'bg-[#e8f0fe] border-[#1a73e8] text-[#1a73e8]'
                  : 'bg-white border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043]'
              }`}
            >
              <div className="font-semibold text-xs">Admin</div>
              <div className="text-[10px] text-[#5f6368]">Supervisor</div>
            </button>
            <button
              type="button"
              onClick={() => setPresetUser('reviewer@trustid.demo')}
              className={`p-2 rounded-xl border text-center transition-all ${
                email.includes('reviewer')
                  ? 'bg-[#e8f0fe] border-[#1a73e8] text-[#1a73e8]'
                  : 'bg-white border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043]'
              }`}
            >
              <div className="font-semibold text-xs">Reviewer</div>
              <div className="text-[10px] text-[#5f6368]">Adjudicator</div>
            </button>
            <button
              type="button"
              onClick={() => setPresetUser('analyst@trustid.demo')}
              className={`p-2 rounded-xl border text-center transition-all ${
                email.includes('analyst')
                  ? 'bg-[#e8f0fe] border-[#1a73e8] text-[#1a73e8]'
                  : 'bg-white border-[#dadce0] hover:bg-[#f8fafd] text-[#3c4043]'
              }`}
            >
              <div className="font-semibold text-xs">Analyst</div>
              <div className="text-[10px] text-[#5f6368]">Forensics</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
