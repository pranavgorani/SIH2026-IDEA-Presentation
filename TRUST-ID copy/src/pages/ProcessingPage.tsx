import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  UploadCloud, 
  Activity, 
  FileText, 
  ShieldCheck, 
  Fingerprint, 
  Search, 
  Database, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  RefreshCw,
  Sparkles
} from 'lucide-react';
import { getCaseResult } from '../services/api';
import { VerificationResponse } from '../types';
import { GlobalScenarioBar } from '../components/GlobalScenarioBar';

export const ProcessingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const caseId = searchParams.get('caseId') || 'TR-2026-8821-GEN';

  const [caseData, setCaseData] = useState<VerificationResponse | null>(null);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  // 8 Pipeline Stages
  const PIPELINE_STAGES = [
    {
      id: 'UPLOAD',
      title: 'Upload & Ingestion',
      subtitle: 'SHA-256 payload integrity check and metadata sanitization',
      icon: UploadCloud,
    },
    {
      id: 'QUALITY',
      title: 'Image Quality Assessment',
      subtitle: 'Specular glare detection, blur scoring, and DPI assurance',
      icon: Activity,
    },
    {
      id: 'OCR',
      title: 'Neural OCR Text Extraction',
      subtitle: 'EasyOCR text extraction and MRZ B93 check-digit parsing',
      icon: FileText,
    },
    {
      id: 'VALIDATION',
      title: 'Rule & Expiry Validation',
      subtitle: 'Expiration date checks, ISO-7064 checksums, format validation',
      icon: ShieldCheck,
    },
    {
      id: 'IDENTITY',
      title: 'Biometric Face Comparison',
      subtitle: 'ArcFace/FaceNet 512D deep feature vector extraction & 1:1 match',
      icon: Fingerprint,
    },
    {
      id: 'FORENSICS',
      title: 'Visual Tampering Forensics',
      subtitle: 'Error Level Analysis (ELA) and copy-move spatial cloning detection',
      icon: Search,
    },
    {
      id: 'RECORD_CHECK',
      title: 'Civil Registry Cross-Check',
      subtitle: 'Civil record match for document number, name, and DOB',
      icon: Database,
    },
    {
      id: 'RISK_ANALYSIS',
      title: 'Deterministic Risk Synthesis',
      subtitle: 'Multi-factor Bayesian threat weighting and policy outcome generation',
      icon: AlertTriangle,
    },
  ];

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch case data
  useEffect(() => {
    let mounted = true;
    getCaseResult(caseId)
      .then((data) => {
        if (mounted && data) {
          setCaseData(data);
        }
      })
      .catch((err) => {
        if (mounted) {
          setErrorMsg(err.message || 'Failed to load case results.');
        }
      });
    return () => {
      mounted = false;
    };
  }, [caseId]);

  // Smooth stage simulation
  useEffect(() => {
    const totalStages = PIPELINE_STAGES.length;
    const intervalTime = 300; // 300ms per stage

    const interval = setInterval(() => {
      setActiveStepIndex((prev) => {
        if (prev < totalStages - 1) {
          return prev + 1;
        } else {
          clearInterval(interval);
          setIsCompleted(true);
          return prev;
        }
      });
    }, intervalTime);

    return () => clearInterval(interval);
  }, []);

  const progressPercent = Math.round(((activeStepIndex + (isCompleted ? 1 : 0)) / PIPELINE_STAGES.length) * 100);

  return (
    <div className="space-y-8 pb-16 font-sans">
      
      {/* 3-Step Flow Stepper */}
      <div className="bg-white border border-[#dadce0] rounded-2xl p-4 shadow-xs">
        <div className="flex items-center justify-between max-w-2xl mx-auto text-xs">
          {/* Step 1 */}
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-full bg-[#e6f4ea] text-[#1e8e3e] font-bold flex items-center justify-center text-xs">
              ✓
            </span>
            <span className="font-medium text-[#137333]">Upload Document</span>
          </div>

          <div className="w-12 h-0.5 bg-[#1a73e8]" />

          {/* Step 2 */}
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-full bg-[#1a73e8] text-white font-bold flex items-center justify-center text-xs shadow-xs">
              02
            </span>
            <span className="font-semibold text-[#1a73e8]">Analyze Pipeline</span>
          </div>

          <div className="w-12 h-0.5 bg-[#dadce0]" />

          {/* Step 3 */}
          <div className="flex items-center space-x-2.5 opacity-60">
            <span className="w-7 h-7 rounded-full bg-[#f1f3f4] text-[#5f6368] font-bold flex items-center justify-center text-xs">
              03
            </span>
            <span className="text-[#5f6368] font-medium">Result & Review</span>
          </div>
        </div>
      </div>

      {/* Hero Progress Header */}
      <div className="bg-white border border-[#dadce0] rounded-3xl p-6 sm:p-8 shadow-xs text-center space-y-4">
        <div className="w-14 h-14 rounded-full bg-[#e8f0fe] text-[#1a73e8] flex items-center justify-center mx-auto">
          {isCompleted ? (
            <CheckCircle2 className="w-8 h-8 text-[#1e8e3e]" />
          ) : (
            <RefreshCw className="w-7 h-7 text-[#1a73e8] animate-spin" />
          )}
        </div>

        {errorMsg ? (
          <div className="p-4 rounded-2xl bg-[#fce8e6] border border-[#fad2cf] text-[#c5221f] text-left max-w-lg mx-auto space-y-2">
            <div className="flex items-center space-x-2 font-semibold text-xs">
              <AlertTriangle className="w-4 h-4 text-[#c5221f]" />
              <span>Pipeline Error</span>
            </div>
            <p className="text-xs text-[#374151]">{errorMsg}</p>
            <button
              type="button"
              onClick={() => navigate('/upload')}
              className="mt-2 px-4 py-1.5 rounded-full bg-[#c5221f] hover:bg-[#b31412] text-white text-xs font-medium"
            >
              Return to Upload
            </button>
          </div>
        ) : (
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-[#202124]">
              {isCompleted ? 'Forensic Analysis Complete' : 'Analyzing Document & Biometrics'}
            </h1>
            <p className="text-xs text-[#374151] mt-1 max-w-lg mx-auto">
              {isCompleted 
                ? 'Multi-factor verification pipeline finished processing all forensic signals.' 
                : 'Executing real-time neural OCR, Error Level Analysis, and cryptographic audit checks...'}
            </p>
          </div>
        )}

        {/* Progress Bar */}
        <div className="max-w-md mx-auto space-y-1.5 pt-2">
          <div className="flex justify-between text-xs font-semibold text-[#3c4043]">
            <span>Pipeline Progress</span>
            <span className="text-[#1a73e8]">{progressPercent}%</span>
          </div>
          <div className="w-full h-2.5 bg-[#f1f3f4] rounded-full overflow-hidden">
            <div 
              className="h-full bg-[#1a73e8] rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {isCompleted && (
          <div className="pt-2 animate-fade-in">
            <button
              type="button"
              onClick={() => navigate(`/result?caseId=${caseId}`)}
              className="px-6 py-3 rounded-full bg-[#1a73e8] hover:bg-[#1557d0] text-white font-medium text-xs inline-flex items-center space-x-2 transition-all shadow-sm"
            >
              <span>View Verification Result</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* 8 Pipeline Stages Cards */}
      <div className="space-y-3">
        <h2 className="text-xs font-semibold text-[#202124]">
          Verification Modules (8 Stages)
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {PIPELINE_STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            const isDone = idx < activeStepIndex || isCompleted;
            const isCurrent = idx === activeStepIndex && !isCompleted;

            return (
              <div
                key={stage.id}
                className={`p-4 rounded-2xl border transition-all ${
                  isDone
                    ? 'bg-white border-[#ceead6] shadow-xs'
                    : isCurrent
                    ? 'bg-[#e8f0fe]/40 border-[#1a73e8] ring-2 ring-[#e8f0fe] shadow-xs'
                    : 'bg-white border-[#dadce0] opacity-60'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    isDone
                      ? 'bg-[#e6f4ea] text-[#1e8e3e]'
                      : isCurrent
                      ? 'bg-[#e8f0fe] text-[#1a73e8]'
                      : 'bg-[#f1f3f4] text-[#5f6368]'
                  }`}>
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-[#1e8e3e]" />
                    ) : isCurrent ? (
                      <RefreshCw className="w-4 h-4 text-[#1a73e8] animate-spin" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>

                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    isDone
                      ? 'bg-[#e6f4ea] text-[#137333]'
                      : isCurrent
                      ? 'bg-[#e8f0fe] text-[#1a73e8]'
                      : 'bg-[#f1f3f4] text-[#5f6368]'
                  }`}>
                    {isDone ? 'COMPLETED' : isCurrent ? 'Running' : 'Pending'}
                  </span>
                </div>

                <div className="mt-3">
                  <h3 className="text-xs font-semibold text-[#202124]">
                    {stage.title}
                  </h3>
                  <p className="text-[11px] text-[#5f6368] mt-0.5 leading-snug">
                    {stage.subtitle}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};
