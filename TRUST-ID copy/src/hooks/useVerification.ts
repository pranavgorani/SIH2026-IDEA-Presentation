import { useState, useCallback } from 'react';
import { DocumentType, ScenarioKey, VerificationResponse } from '../types';
import { verifyDocument } from '../services/api';

export function useVerification() {
  const [documentFile, setDocumentFile] = useState<File | null>(null);
  const [faceFile, setFaceFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType>('AUTO_DETECT');
  const [scenario, setScenario] = useState<ScenarioKey>('GENUINE');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setDocumentFile(null);
    setFaceFile(null);
    setDocumentType('AUTO_DETECT');
    setVerificationResult(null);
    setError(null);
  }, []);

  const executeVerification = useCallback(async (): Promise<VerificationResponse | null> => {
    if (!documentFile) {
      setError('A primary document image must be provided before initiating verification.');
      return null;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result = await verifyDocument({
        documentFile,
        faceFile: faceFile || undefined,
        documentType,
        scenario,
      });

      setVerificationResult(result);
      return result;
    } catch (err: any) {
      const message = err?.message || 'An unexpected error occurred during document verification.';
      setError(message);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, [documentFile, faceFile, documentType, scenario]);

  return {
    documentFile,
    setDocumentFile,
    faceFile,
    setFaceFile,
    documentType,
    setDocumentType,
    scenario,
    setScenario,
    isSubmitting,
    verificationResult,
    error,
    executeVerification,
    reset,
  };
}
