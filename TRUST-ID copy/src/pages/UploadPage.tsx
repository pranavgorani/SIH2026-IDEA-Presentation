import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowRight, 
  AlertCircle, 
  Sparkles,
  CreditCard,
  Car,
  Globe,
  Compass,
  ShieldCheck,
  CheckCircle2,
  Lock
} from 'lucide-react';
import { DocumentType, ScenarioKey } from '../types';
import { DocumentUpload } from '../components/DocumentUpload';
import { FaceUpload } from '../components/FaceUpload';
import { ScenarioSelector } from '../components/ScenarioSelector';
import { useVerification } from '../hooks/useVerification';

interface UploadPageProps {
  onCaseCreated?: (caseId: string) => void;
}

const DOCUMENT_TYPES: Array<{
  type: DocumentType;
  label: string;
  code: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}> = [
  {
    type: 'AUTO_DETECT',
    label: 'Auto-Detect (Recommended)',
    code: 'OCR + Gemini Vision',
    icon: Sparkles,
    description: 'Auto-identifies PAN, Aadhaar, Passport, Voter ID, DL, or unclassified documents',
  },
  {
    type: 'PAN',
    label: 'PAN Card',
    code: 'Income Tax Dept',
    icon: CreditCard,
    description: 'Permanent Account Number card with 10-character syntax validation',
  },
  {
    type: 'AADHAAR',
    label: 'Aadhaar Card',
    code: 'UIDAI Standard',
    icon: ShieldCheck,
    description: '12-digit national identity card or masked Aadhaar',
  },
  {
    type: 'PASSPORT',
    label: 'Biometric Passport',
    code: 'ICAO Doc 9303',
    icon: Globe,
    description: 'Machine Readable Travel Documents with 2-line MRZ checksums',
  },
  {
    type: 'VOTER_ID',
    label: 'Voter ID (EPIC)',
    code: 'ECI Standard',
    icon: Compass,
    description: 'Election Commission of India Electors Photo Identity Card',
  },
  {
    type: 'DRIVING_LICENSE',
    label: 'Driving Licence',
    code: 'MoRTH / Sarathi',
    icon: Car,
    description: 'Indian or international motor vehicle driving licences',
  },
];

export const UploadPage: React.FC<UploadPageProps> = ({ onCaseCreated }) => {
  const navigate = useNavigate();
  const {
    documentFile,
    setDocumentFile,
    faceFile,
    setFaceFile,
    documentType,
    setDocumentType,
    scenario,
    setScenario,
    isSubmitting,
    error,
    executeVerification,
  } = useVerification();

  const [preloadingSample, setPreloadingSample] = useState(false);

  // Helper to load sample files for immediate testing
  const handleLoadSample = async () => {
    setPreloadingSample(true);
    try {
      const sampleDocCanvas = document.createElement('canvas');
      sampleDocCanvas.width = 1200;
      sampleDocCanvas.height = 760;
      const ctx = sampleDocCanvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, 1200, 760);
        // Header
        ctx.fillStyle = '#1a73e8';
        ctx.fillRect(0, 0, 1200, 110);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 32px sans-serif';
        ctx.fillText(`OFFICIAL SPECIMEN • ${documentType.replace(/_/g, ' ')}`, 60, 70);
        // Text
        ctx.fillStyle = '#202124';
        ctx.font = 'bold 24px sans-serif';
        ctx.fillText('NAME / HOLDER: JANE DOE', 60, 200);
        ctx.font = '22px sans-serif';
        ctx.fillStyle = '#3c4043';
        ctx.fillText('DOCUMENT NO: TR-9021-338210', 60, 260);
        ctx.fillText('DATE OF BIRTH: 1992-04-18', 60, 320);
        ctx.fillText('EXPIRATION DATE: 2032-11-05', 60, 380);
        ctx.fillText('NATIONALITY: IND', 60, 440);
        ctx.fillText('ISSUING AUTHORITY: CIVIL REGISTRATION', 60, 500);
        // Border
        ctx.strokeStyle = '#dadce0';
        ctx.lineWidth = 4;
        ctx.strokeRect(30, 30, 1140, 700);
      }

      const docBlob = await new Promise<Blob>((resolve) => {
        sampleDocCanvas.toBlob((b) => resolve(b || new Blob()), 'image/jpeg');
      });
      const mockDoc = new File([docBlob], `specimen_${documentType.toLowerCase()}.jpg`, { type: 'image/jpeg' });
      setDocumentFile(mockDoc);

      const sampleFaceCanvas = document.createElement('canvas');
      sampleFaceCanvas.width = 600;
      sampleFaceCanvas.height = 600;
      const fCtx = sampleFaceCanvas.getContext('2d');
      if (fCtx) {
        fCtx.fillStyle = '#ffffff';
        fCtx.fillRect(0, 0, 600, 600);
        fCtx.fillStyle = '#1a73e8';
        fCtx.beginPath();
        fCtx.arc(300, 260, 110, 0, Math.PI * 2);
        fCtx.fill();
        fCtx.beginPath();
        fCtx.arc(300, 540, 200, 0, Math.PI * 2);
        fCtx.fill();
      }

      const faceBlob = await new Promise<Blob>((resolve) => {
        sampleFaceCanvas.toBlob((b) => resolve(b || new Blob()), 'image/jpeg');
      });
      const mockFace = new File([faceBlob], 'specimen_reference_selfie.jpg', { type: 'image/jpeg' });
      setFaceFile(mockFace);

    } catch (e) {
      console.error('Failed to create sample specimen', e);
    } finally {
      setPreloadingSample(false);
    }
  };

  const handleStartVerification = async () => {
    const result = await executeVerification();
    if (result && result.case_id) {
      if (onCaseCreated) {
        onCaseCreated(result.case_id);
      }
      navigate(`/processing?caseId=${result.case_id}`);
    }
  };

  return (
    <div className="space-y-8 pb-16 font-sans">
      
      {/* 3-Step Flow Stepper */}
      <div className="bg-white border border-[#dadce0] rounded-2xl p-4 shadow-xs">
        <div className="flex items-center justify-between max-w-2xl mx-auto text-xs">
          {/* Step 1 */}
          <div className="flex items-center space-x-2.5">
            <span className="w-7 h-7 rounded-full bg-[#1a73e8] text-white font-bold flex items-center justify-center text-xs shadow-xs">
              01
            </span>
            <span className="font-semibold text-[#1a73e8]">Upload Document</span>
          </div>

          <div className="w-12 h-0.5 bg-[#dadce0]" />

          {/* Step 2 */}
          <div className="flex items-center space-x-2.5 opacity-60">
            <span className="w-7 h-7 rounded-full bg-[#f1f3f4] text-[#5f6368] font-bold flex items-center justify-center text-xs">
              02
            </span>
            <span className="text-[#5f6368] font-medium">Analyze Pipeline</span>
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

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#202124] tracking-tight">
            New Verification
          </h1>
          <p className="text-xs text-[#5f6368] mt-1">
            Submit an identity document and optional selfie probe for automated forensic screening.
          </p>
        </div>

        <button
          type="button"
          onClick={handleLoadSample}
          disabled={preloadingSample}
          className="px-4 py-2 rounded-full bg-white hover:bg-[#f8fafd] border border-[#dadce0] text-[#3c4043] text-xs font-medium flex items-center space-x-2 transition-all shadow-xs self-start md:self-auto"
        >
          <Sparkles className="w-3.5 h-3.5 text-[#1a73e8]" />
          <span>{preloadingSample ? 'Preparing...' : 'Load Sample Specimen'}</span>
        </button>
      </div>

      {/* Document Type Selection */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-[#202124]">
            1. Select Document Type
          </label>
          <span className="text-xs text-[#5f6368]">
            Selected: {documentType.replace(/_/g, ' ')}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {DOCUMENT_TYPES.map((item) => {
            const Icon = item.icon;
            const isSelected = documentType === item.type;

            return (
              <button
                key={item.type}
                type="button"
                onClick={() => setDocumentType(item.type)}
                className={`p-4 rounded-2xl text-left transition-all border ${
                  isSelected
                    ? 'bg-[#e8f0fe]/50 border-[#1a73e8] ring-2 ring-[#e8f0fe] shadow-xs'
                    : 'bg-white border-[#dadce0] hover:border-[#bdc1c6] hover:bg-[#fafbfc]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center ${
                    isSelected ? 'bg-[#1a73e8] text-white' : 'bg-[#f1f3f4] text-[#5f6368]'
                  }`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                    isSelected ? 'bg-[#1a73e8] text-white' : 'bg-[#f1f3f4] text-[#5f6368]'
                  }`}>
                    {item.code}
                  </span>
                </div>

                <div className="mt-3">
                  <h3 className={`text-xs font-semibold ${isSelected ? 'text-[#1a73e8]' : 'text-[#202124]'}`}>
                    {item.label}
                  </h3>
                  <p className="text-[11px] text-[#5f6368] mt-1 leading-snug">
                    {item.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Ingestion Dropzones */}
      <div className="space-y-3">
        <label className="text-xs font-semibold text-[#202124]">
          2. Upload Credentials
        </label>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <DocumentUpload
            selectedFile={documentFile}
            onFileSelect={setDocumentFile}
            documentType={documentType}
          />
          <FaceUpload
            selectedFile={faceFile}
            onFileSelect={setFaceFile}
          />
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 rounded-2xl bg-[#fce8e6] border border-[#fad2cf] text-[#c5221f] text-xs flex items-center space-x-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Verification Integrity Note & Action Button */}
      <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start space-x-3 text-xs text-[#5f6368]">
          <ShieldCheck className="w-5 h-5 text-[#1e8e3e] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-[#202124] block">Deterministic Verification Integrity</span>
            <span>
              Real neural OCR, ELA tampering scan, FaceNet comparison, and database check are executed. Unreadable or non-document files are automatically flagged.
            </span>
          </div>
        </div>

        <button
          type="button"
          onClick={handleStartVerification}
          disabled={!documentFile || isSubmitting}
          className={`px-8 py-3.5 rounded-full font-medium text-xs flex items-center justify-center space-x-2 transition-all shadow-sm shrink-0 ${
            !documentFile || isSubmitting
              ? 'bg-[#dadce0] text-[#80868b] cursor-not-allowed'
              : 'bg-[#1a73e8] hover:bg-[#1557d0] text-white'
          }`}
        >
          <span>{isSubmitting ? 'Submitting...' : 'Analyze Document'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

    </div>
  );
};
