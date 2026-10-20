import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Header } from './components/Header';
import { Navigation } from './components/Navigation';
import { OverviewPage } from './pages/OverviewPage';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ResultPage } from './pages/ResultPage';
import { EvidencePage } from './pages/EvidencePage';
import { HumanReviewPage } from './pages/HumanReviewPage';
import { CasesPage } from './pages/CasesPage';
import { ReportsPage } from './pages/ReportsPage';
import { RegistryPage } from './pages/RegistryPage';

const AppLayout: React.FC = () => {
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const location = useLocation();

  // Extract caseId from query params whenever location changes
  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const id = params.get('caseId');
    if (id) {
      setActiveCaseId(id);
    }
  }, [location]);

  return (
    <div className="min-h-screen bg-[#f8fafd] text-[#202124] flex flex-col font-sans selection:bg-[#e8f0fe] selection:text-[#1a73e8]">
      {/* Enterprise Header */}
      <Header currentCaseId={activeCaseId} />

      {/* Navigation Bar */}
      <Navigation currentCaseId={activeCaseId} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8">
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/overview" element={<OverviewPage />} />
          <Route 
            path="/upload" 
            element={<UploadPage onCaseCreated={(id) => setActiveCaseId(id)} />} 
          />
          <Route path="/processing" element={<ProcessingPage />} />
          <Route path="/result" element={<ResultPage />} />
          <Route path="/evidence" element={<EvidencePage />} />
          <Route path="/human-review" element={<HumanReviewPage />} />
          <Route path="/cases" element={<CasesPage />} />
          <Route path="/registry" element={<RegistryPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </main>

      {/* Enterprise Footer */}
      <footer className="border-t border-[#e0e2e6] bg-white py-5 text-center text-[#5f6368] text-xs font-normal mt-12">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2.5">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-[#202124]">TRUST-ID Enterprise</span>
            <span>•</span>
            <span>Intelligent Identity Forensics</span>
          </div>
          <div className="flex items-center space-x-3 text-[11px] text-[#5f6368]">
            <span>ISO/IEC 19794 & ICAO Doc 9303 Compliant</span>
            <span>•</span>
            <span>SHA-256 Chained Integrity</span>
            <span>•</span>
            <span>Restricted Sovereign Access</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;
