import { DecisionOutcome, RiskLevel, CardStatus } from '../types';

/**
 * Format bytes into human readable string
 */
export function formatFileSize(bytes: number): string {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Format ISO date string into readable format
 */
export function formatAuditTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return isoString;
  }
}

/**
 * Return CSS badge styles based on Decision Outcome
 */
export function getOutcomeBadgeStyles(outcome: DecisionOutcome | string) {
  const norm = (outcome || '').toUpperCase();
  switch (norm) {
    case 'APPROVE':
    case 'APPROVED':
      return {
        bg: 'bg-[#e6f4ea] border-[#ceead6] text-[#137333]',
        dot: 'bg-[#1e8e3e]',
        label: 'Approved • Authentic',
      };
    case 'REJECT':
    case 'REJECTED':
      return {
        bg: 'bg-[#fce8e6] border-[#fad2cf] text-[#c5221f]',
        dot: 'bg-[#d93025]',
        label: 'Rejected • Discrepancy Found',
      };
    case 'REQUEST_REUPLOAD':
      return {
        bg: 'bg-[#fef7e0] border-[#feefc3] text-[#b06000]',
        dot: 'bg-[#e37400]',
        label: 'Re-upload Requested',
      };
    case 'REFER_FOR_REVIEW':
    case 'MANUAL_REVIEW':
    case 'REQUIRES_MANUAL_REVIEW':
      return {
        bg: 'bg-[#fef7e0] border-[#feefc3] text-[#b06000]',
        dot: 'bg-[#e37400]',
        label: 'Manual Review Required',
      };
    case 'PROCESSED':
      return {
        bg: 'bg-[#e8f0fe] border-[#d2e3fc] text-[#1a73e8]',
        dot: 'bg-[#1a73e8]',
        label: 'Processed • Ready',
      };
    default:
      return {
        bg: 'bg-[#f1f3f4] border-[#dadce0] text-[#3c4043]',
        dot: 'bg-[#5f6368]',
        label: outcome,
      };
  }
}

/**
 * Format document type into institutional title
 */
export function formatDocumentType(docType?: string): string {
  if (!docType) return 'Unknown Document';
  const norm = docType.toUpperCase();
  switch (norm) {
    case 'PAN':
    case 'PAN_CARD':
      return 'PAN Card (Permanent Account Number)';
    case 'AADHAAR':
      return 'Aadhaar Card (UIDAI)';
    case 'PASSPORT':
    case 'INDIAN_PASSPORT':
      return 'Passport (ICAO 9303)';
    case 'VOTER_ID':
      return 'Voter ID (EPIC)';
    case 'DRIVING_LICENSE':
    case 'DRIVER_LICENSE':
      return 'Driving Licence';
    case 'NATIONAL_ID':
      return 'National ID Card';
    case 'TRAVEL_PERMIT':
      return 'Travel & Transit Permit';
    case 'VEHICLE_RC':
      return 'Vehicle Registration Certificate (RC)';
    case 'GENERIC_ID':
      return 'Official Identity Credential (Generic ID)';
    case 'UNKNOWN':
      return 'Unclassified Document (Unknown Type)';
    default:
      return docType.replace(/_/g, ' ');
  }
}

/**
 * Standardized card evaluation styling in Google style with high contrast
 */
export function getCardStatusBadge(status?: CardStatus | string) {
  const norm = (status || '').toLowerCase();

  switch (norm) {
    case 'pass':
      return {
        label: 'Pass',
        badge: 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]',
        cardBorder: 'border-[#e0e2e6] hover:border-[#ceead6]',
        indicator: 'bg-[#1e8e3e]',
        iconType: 'check',
      };
    case 'match':
      return {
        label: 'Match',
        badge: 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]',
        cardBorder: 'border-[#e0e2e6] hover:border-[#ceead6]',
        indicator: 'bg-[#1e8e3e]',
        iconType: 'check',
      };
    case 'fail':
      return {
        label: 'Fail',
        badge: 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]',
        cardBorder: 'border-[#fad2cf] hover:border-[#f28b82]',
        indicator: 'bg-[#d93025]',
        iconType: 'cross',
      };
    case 'mismatch':
      return {
        label: 'Mismatch',
        badge: 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]',
        cardBorder: 'border-[#fad2cf] hover:border-[#f28b82]',
        indicator: 'bg-[#d93025]',
        iconType: 'cross',
      };
    case 'unavailable':
      return {
        label: 'Not Available',
        badge: 'bg-[#f1f3f4] text-[#374151] border-[#dadce0]',
        cardBorder: 'border-[#e0e2e6]',
        indicator: 'bg-[#9aa0a6]',
        iconType: 'slash',
        note: 'Not provided or optional registry check'
      };
    case 'inconclusive':
      return {
        label: 'Inconclusive',
        badge: 'bg-[#fef7e0] text-[#b06000] border-[#feefc3]',
        cardBorder: 'border-[#feefc3]',
        indicator: 'bg-[#f9ab00]',
        iconType: 'question',
        note: 'Ambiguous indicators requiring human check'
      };
    default:
      return {
        label: status || 'Unknown',
        badge: 'bg-[#f1f3f4] text-[#374151] border-[#dadce0]',
        cardBorder: 'border-[#e0e2e6]',
        indicator: 'bg-[#9aa0a6]',
        iconType: 'info',
      };
  }
}

/**
 * Return CSS badge & score representation based on Risk Level
 */
export function getRiskBadgeInfo(score: number | null | undefined, level?: RiskLevel | string) {
  if (score === null || score === undefined || level === 'INSUFFICIENT_EVIDENCE' || level === 'NOT_APPLICABLE') {
    return {
      level: level || 'NOT_APPLICABLE',
      label: 'Manual Review Required',
      badge: 'bg-[#f1f3f4] text-[#374151] border-[#dadce0]',
      text: 'text-[#374151]',
      displayScore: 'N/A',
      subtext: 'Document unclassified or insufficient signals to compute score; manual officer verification required',
      color: '#6b7280'
    };
  }

  if (score <= 29) {
    return {
      level: 'LOW',
      label: 'Low Risk',
      badge: 'bg-[#e6f4ea] text-[#137333] border-[#ceead6]',
      text: 'text-[#137333]',
      displayScore: String(score),
      subtext: 'Document satisfies core authenticity and integrity checks',
      color: '#1e8e3e'
    };
  } else if (score <= 59) {
    return {
      level: 'MEDIUM',
      label: 'Medium Risk',
      badge: 'bg-[#fef7e0] text-[#b06000] border-[#feefc3]',
      text: 'text-[#b06000]',
      displayScore: String(score),
      subtext: 'Moderate variance or low image quality detected',
      color: '#e37400'
    };
  } else {
    return {
      level: 'HIGH',
      label: 'High Risk',
      badge: 'bg-[#fce8e6] text-[#c5221f] border-[#fad2cf]',
      text: 'text-[#c5221f]',
      displayScore: String(score),
      subtext: 'Significant tampering, expiry, or biometric mismatch detected',
      color: '#d93025'
    };
  }
}
