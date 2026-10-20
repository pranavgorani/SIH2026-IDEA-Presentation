import { ScenarioPreset } from '../types';

export const mockScenarios: Record<string, ScenarioPreset> = {
  GENUINE: {
    id: 'GENUINE',
    label: 'Scenario 1: Fully Genuine (Passport)',
    document_type: 'PASSPORT',
    outcome: 'APPROVED',
    description: 'Cryptographic checks pass, biometric match is 96.2%, OCR verified with 0 visual anomalies. Risk score: 4 (LOW).',
    data: {
      case_id: 'TR-2026-8821-GEN',
      status: 'COMPLETED',
      document_type: 'PASSPORT',
      quality: {
        score: 0.97,
        glare: 0.04,
        blur: 0.02,
        resolution: '3840x2160',
        illumination: 'OPTIMAL',
        status: 'pass',
        issues: []
      },
      preprocessing: {
        normalized: true,
        deskew_angle: 0.35,
        color_space: 'sRGB',
        resolution_dpi: 300,
        pipeline_steps: ['Auto-crop', 'Perspective correction', 'Specular glare suppression', 'Contrast optimization']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.985,
        language: 'en',
        raw_text: 'P<USASPECI<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<\n4401234567USA8502158M3110141<<<<<<<<<<<<<<04',
        status: 'pass',
        mrz: {
          raw: 'P<USASPECI<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<4401234567USA8502158M3110141<<<<<<<<<<<<<<04',
          parsed: {
            type: 'Passport',
            country: 'USA',
            surname: 'SPECI',
            given_name: 'JOHN',
            doc_number: '440123456',
            dob: '1985-02-15',
            sex: 'M',
            expiry: '2031-10-14'
          },
          valid: true
        }
      },
      fields: {
        document_number: '440123456',
        first_name: 'JOHN',
        last_name: 'SPECI',
        full_name: 'JOHN SPECI',
        date_of_birth: '1985-02-15',
        expiry_date: '2031-10-14',
        issue_date: '2021-10-15',
        gender: 'M',
        nationality: 'USA',
        issuing_country: 'United States of America',
        address: 'N/A',
        _metadata: {
          document_number: { value: '440123456', confidence: 0.99, validation_status: 'VALID' },
          full_name: { value: 'JOHN SPECI', confidence: 0.98, validation_status: 'VALID' },
          date_of_birth: { value: '1985-02-15', confidence: 0.99, validation_status: 'VALID' },
          expiry_date: { value: '2031-10-14', confidence: 0.98, validation_status: 'VALID' },
          nationality: { value: 'USA', confidence: 0.99, validation_status: 'VALID' }
        }
      },
      document_validation: {
        valid_format: true,
        checksum_passed: true,
        expiry_check: 'VALID',
        security_features_verified: true,
        status: 'pass',
        issues: []
      },
      record_check: {
        database_match: true,
        registry_name: 'Federal Civil Identity Registry (FCIR)',
        query_status: 'VERIFIED',
        status: 'match',
        discrepancy_fields: [],
        remarks: 'Direct match against issuer cryptographic key and sovereign registry.'
      },
      identity: {
        face_match_confidence: 0.962,
        match_status: 'MATCH',
        liveness_score: 0.981,
        liveness_status: 'PASSED',
        status: 'match',
        notes: 'High spatial similarity with document portrait. Passive 3D liveness verified.'
      },
      visual_forensics: {
        copy_move_detected: false,
        font_anomaly: false,
        metadata_tampered: false,
        ela_score: 0.04,
        edge_inconsistency: false,
        status: 'pass',
        anomalies: [],
        regions: []
      },
      risk: {
        overall_score: 4,
        level: 'LOW',
        factors: [
          'High-confidence cryptographic validation -20',
          'Optimal biometric similarity (96.2%) -15',
          'Zero visual anomalies identified -10'
        ],
        factors_breakdown: [
          { factor: 'Cryptographic Checksum Pass', impact: '-20', score_delta: -20, source: 'Validation Engine' },
          { factor: 'Biometric Face Match (0.962)', impact: '-15', score_delta: -15, source: 'ArcFace Recognizer' },
          { factor: 'Zero Spatial/Frequency Anomalies', impact: '-10', score_delta: -10, source: 'Forensic Engine' }
        ]
      },
      evidence: {
        artifacts: [
          {
            id: 'art-01',
            type: 'DOCUMENT_ORIGINAL',
            title: 'Passport Primary Credential',
            uri: '/samples/passport_specimen.png',
            hash_sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            description: 'Uncompressed raw scan at 300 DPI'
          },
          {
            id: 'art-02',
            type: 'FACE_SELFIE',
            title: 'Biometric Reference Probe',
            uri: '/samples/selfie_specimen.png',
            hash_sha256: 'ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb',
            description: 'Live frontal probe with structured illumination'
          }
        ],
        audit_trail: [
          { timestamp: '2026-09-08T15:30:01Z', step: 'INGESTION', status: 'SUCCESS', detail: 'Payload integrity confirmed via SHA-256.' },
          { timestamp: '2026-09-08T15:30:02Z', step: 'OCR_EXTRACTION', status: 'SUCCESS', detail: 'ICAO Doc 9303 MRZ parsed with 98.5% confidence.' },
          { timestamp: '2026-09-08T15:30:03Z', step: 'VALIDATION', status: 'SUCCESS', detail: 'All checksums and expiry constraints valid.' },
          { timestamp: '2026-09-08T15:30:04Z', step: 'BIOMETRIC_MATCH', status: 'SUCCESS', detail: 'Cosine similarity 0.962 exceeds threshold 0.75.' },
          { timestamp: '2026-09-08T15:30:05Z', step: 'REGISTRY_QUERY', status: 'SUCCESS', detail: 'Verified in sovereign registry.' }
        ],
        items: []
      },
      decision: {
        outcome: 'APPROVED',
        confidence: 0.98,
        rationale: 'All forensic tests, biometric matches, and civil registry lookups passed with zero anomalies.',
        recommended_actions: ['Automated approval recorded in verification ledger', 'Certificate of Authenticity issued'],
        evaluated_at: '2026-09-08T15:30:07Z'
      }
    }
  },

  EXPIRED: {
    id: 'EXPIRED',
    label: 'Scenario 2: Expired Credential (Driving License)',
    document_type: 'DRIVING_LICENSE',
    outcome: 'REJECTED',
    description: 'Document format is valid, but expiry check failed (expired 2024-03-15). Risk score: 78 (HIGH).',
    data: {
      case_id: 'TR-2026-4419-EXP',
      status: 'COMPLETED',
      document_type: 'DRIVING_LICENSE',
      quality: {
        score: 0.91,
        glare: 0.08,
        blur: 0.05,
        resolution: '2400x1600',
        illumination: 'OPTIMAL',
        status: 'pass',
        issues: []
      },
      preprocessing: {
        normalized: true,
        deskew_angle: -1.2,
        color_space: 'sRGB',
        resolution_dpi: 300,
        pipeline_steps: ['Card boundary segmentation', 'Homography alignment', 'Binarization check']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.962,
        language: 'en',
        raw_text: 'STATE MOTOR VEHICLE PERMIT\nLIC NO: DL-8893120-X\nEXP: 2024-03-15\nDOB: 1988-07-22\nNAME: ROBERT E. VANCE\nCLASS: C',
        status: 'pass'
      },
      fields: {
        document_number: 'DL-8893120-X',
        first_name: 'ROBERT',
        last_name: 'VANCE',
        full_name: 'ROBERT E. VANCE',
        date_of_birth: '1988-07-22',
        expiry_date: '2024-03-15',
        issue_date: '2019-03-16',
        gender: 'M',
        nationality: 'USA',
        issuing_country: 'United States',
        address: '742 Evergreen Terrace, Springfield',
        _metadata: {
          document_number: { value: 'DL-8893120-X', confidence: 0.97, validation_status: 'VALID' },
          full_name: { value: 'ROBERT E. VANCE', confidence: 0.96, validation_status: 'VALID' },
          date_of_birth: { value: '1988-07-22', confidence: 0.98, validation_status: 'VALID' },
          expiry_date: { value: '2024-03-15', confidence: 0.99, validation_status: 'DISCREPANCY' }
        }
      },
      document_validation: {
        valid_format: true,
        checksum_passed: true,
        expiry_check: 'EXPIRED',
        security_features_verified: true,
        status: 'fail',
        issues: ['Document expired on 2024-03-15 (lapsed by 898 days)']
      },
      record_check: {
        database_match: true,
        registry_name: 'DMV Unified Vehicle & Operator Database',
        query_status: 'VERIFIED',
        status: 'match',
        discrepancy_fields: [],
        remarks: 'Record exists in state DMV archive; operator license status is LAPSED/EXPIRED.'
      },
      identity: {
        face_match_confidence: 0.924,
        match_status: 'MATCH',
        liveness_score: 0.941,
        liveness_status: 'PASSED',
        status: 'match',
        notes: 'Face matches operator record photograph.'
      },
      visual_forensics: {
        copy_move_detected: false,
        font_anomaly: false,
        metadata_tampered: false,
        ela_score: 0.08,
        edge_inconsistency: false,
        status: 'pass',
        anomalies: [],
        regions: []
      },
      risk: {
        overall_score: 78,
        level: 'HIGH',
        factors: [
          'Document validity period lapsed +45',
          'Civil registry status lapsed +33'
        ],
        factors_breakdown: [
          { factor: 'Document Expired (2024-03-15)', impact: '+45', score_delta: 45, source: 'Validation Engine' },
          { factor: 'Registry Operator Status Lapsed', impact: '+33', score_delta: 33, source: 'DMV Registry' }
        ]
      },
      evidence: {
        artifacts: [
          {
            id: 'art-exp-01',
            type: 'DOCUMENT_ORIGINAL',
            title: 'Driving License Specimen Scan',
            uri: '/samples/dl_specimen.png',
            hash_sha256: '9f83c605d4a66a1a1f335b376d49938b815e9a4f4cf986df95eb635ef838b7e2',
            description: 'State operator license scan showing expired validity block'
          }
        ],
        audit_trail: [
          { timestamp: '2026-09-08T15:32:10Z', step: 'INGESTION', status: 'SUCCESS', detail: 'Driving license image received.' },
          { timestamp: '2026-09-08T15:32:11Z', step: 'VALIDATION', status: 'FAILED', detail: 'Expiry rule failed: Expiration date is in the past.' },
          { timestamp: '2026-09-08T15:32:12Z', step: 'RECORD_CHECK', status: 'WARNING', detail: 'DMV registry confirms operator record expired.' }
        ],
        items: [
          {
            id: 'ev-exp-01',
            severity: 'CRITICAL',
            category: 'Temporal Validity',
            source: 'Validation Engine',
            reason: 'Credential expired on March 15, 2024. Does not satisfy requirement for active unexpired documentation.',
            confidence: 0.99
          }
        ]
      },
      decision: {
        outcome: 'REJECTED',
        confidence: 0.99,
        rationale: 'Credential expired on March 15, 2024. Active unexpired identity documents are strictly required.',
        recommended_actions: ['Reject verification request', 'Prompt applicant to submit an unexpired credential or renewal receipt'],
        evaluated_at: '2026-09-08T15:32:14Z'
      }
    }
  },

  VISUAL_ANOMALY: {
    id: 'VISUAL_ANOMALY',
    label: 'Scenario 3: Visual Forgery Anomaly (National ID)',
    document_type: 'NATIONAL_ID',
    outcome: 'MANUAL_REVIEW',
    description: 'Copy-move cloning, ELA spike in DOB region, font baseline anomaly. Bounding boxes ready. Risk score: 94 (HIGH).',
    data: {
      case_id: 'TR-2026-7092-FOR',
      status: 'COMPLETED',
      document_type: 'NATIONAL_ID',
      quality: {
        score: 0.88,
        glare: 0.12,
        blur: 0.09,
        resolution: '1920x1080',
        illumination: 'ADEQUATE',
        status: 'pass',
        issues: ['Localized compression artifacts around alphanumeric regions']
      },
      preprocessing: {
        normalized: true,
        deskew_angle: 0.8,
        color_space: 'sRGB',
        resolution_dpi: 300,
        pipeline_steps: ['Noise analysis', 'Frequency domain DCT filter', 'Error Level Analysis (ELA)']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.764,
        language: 'en',
        raw_text: 'REPUBLIC OF CIPHER - NATIONAL IDENTITY CARD\nID NO: 9021-338210-9\nNAME: MARCUS A. AURELIUS\nDOB: 1996-11-04\nEXP: 2030-05-12',
        status: 'pass'
      },
      fields: {
        document_number: '9021-338210-9',
        first_name: 'MARCUS',
        last_name: 'AURELIUS',
        full_name: 'MARCUS A. AURELIUS',
        date_of_birth: '1996-11-04',
        expiry_date: '2030-05-12',
        issue_date: '2020-05-12',
        gender: 'M',
        nationality: 'CIPHER',
        issuing_country: 'Republic of Cipher',
        address: '42 Cryptography Lane, Sector 9',
        _metadata: {
          document_number: { value: '9021-338210-9', confidence: 0.78, validation_status: 'DISCREPANCY' },
          full_name: { value: 'MARCUS A. AURELIUS', confidence: 0.82, validation_status: 'VALID' },
          date_of_birth: { value: '1996-11-04', confidence: 0.65, validation_status: 'DISCREPANCY' },
          expiry_date: { value: '2030-05-12', confidence: 0.91, validation_status: 'VALID' }
        }
      },
      document_validation: {
        valid_format: true,
        checksum_passed: false,
        expiry_check: 'VALID',
        security_features_verified: false,
        status: 'fail',
        issues: ['Microprint integrity compromised', 'Checksum mismatch in ISO-7064 check digit']
      },
      record_check: {
        database_match: false,
        registry_name: 'National Civil ID Ledger',
        query_status: 'DISCREPANCY',
        status: 'mismatch',
        discrepancy_fields: ['date_of_birth', 'full_name'],
        remarks: 'Record checksum does not reconcile with sovereign registry hash.'
      },
      identity: {
        face_match_confidence: 0.74,
        match_status: 'INCONCLUSIVE',
        liveness_score: 0.91,
        liveness_status: 'PASSED',
        status: 'inconclusive',
        notes: 'Document portrait exhibits edge smoothing and artificial color gradient around collar line.'
      },
      visual_forensics: {
        copy_move_detected: true,
        font_anomaly: true,
        metadata_tampered: true,
        ela_score: 0.892,
        edge_inconsistency: true,
        status: 'fail',
        anomalies: [
          'Error Level Analysis (ELA): High-frequency residue spike in DOB bounding box',
          'Font Typography Anomaly: Non-standard kerning detected in ID number',
          'Copy-Move Forgery: Matched 14 duplicated keypoint clusters in identity card background',
          'EXIF/Metadata Tampering: Adobe Photoshop editing tag identified in JFIF stream'
        ],
        regions: [
          {
            x: 28,
            y: 52,
            width: 32,
            height: 14,
            label: 'DOB REGION SPLICING',
            reason: 'Error Level Analysis (ELA) discrepancy 0.892 indicating localized pixel alteration in date of birth',
            severity: 'CRITICAL',
            confidence: 0.942
          },
          {
            x: 52,
            y: 18,
            width: 42,
            height: 12,
            label: 'FONT KERNING ANOMALY',
            reason: 'Non-standard kerning & baseline deviation detected in document number characters',
            severity: 'HIGH',
            confidence: 0.891
          },
          {
            x: 4,
            y: 56,
            width: 22,
            height: 38,
            label: 'COPY-MOVE CLONED PIXELS',
            reason: '14 duplicated keypoint clusters detected in security guilloche pattern',
            severity: 'HIGH',
            confidence: 0.865
          }
        ]
      },
      risk: {
        overall_score: 94,
        level: 'HIGH',
        factors: [
          'Visual anomaly (ELA DOB spike) +35',
          'Visual anomaly (Font baseline deviation) +30',
          'Record mismatch in civil ledger +25',
          'Photoshop metadata tag +4'
        ],
        factors_breakdown: [
          { factor: 'Visual Anomaly: ELA DOB Spike (0.892)', impact: '+35', score_delta: 35, source: 'Forensic ELA Engine' },
          { factor: 'Visual Anomaly: Font Baseline Deviation', impact: '+30', score_delta: 30, source: 'Typography Model' },
          { factor: 'Civil Registry Record Discrepancy', impact: '+25', score_delta: 25, source: 'Civil ID Ledger' },
          { factor: 'Editing Software Signature Detected', impact: '+4', score_delta: 4, source: 'EXIF Parser' }
        ]
      },
      evidence: {
        artifacts: [
          {
            id: 'art-for-01',
            type: 'DOCUMENT_ORIGINAL',
            title: 'Submitted ID Card Image',
            uri: '/samples/id_tampered.png',
            hash_sha256: '5d41402abc4b2a76b9719d911017c592ff37803a6c9d0902c1fd33b8a3465134',
            description: 'Original input image with detected digital anomalies'
          },
          {
            id: 'art-for-02',
            type: 'ELA_HEATMAP',
            title: 'Error Level Analysis (ELA) Heatmap',
            uri: '/samples/ela_heatmap.png',
            description: 'White heat signatures indicate edited regions around DOB text'
          },
          {
            id: 'art-for-03',
            type: 'TAMPER_MASK',
            title: 'Copy-Move Spatial Keypoint Vectors',
            uri: '/samples/keypoint_cloning.png',
            description: 'Cloned pixel vector paths between background elements'
          }
        ],
        audit_trail: [
          { timestamp: '2026-09-08T15:35:00Z', step: 'INGESTION', status: 'SUCCESS', detail: 'ID Card image loaded for forensic screening.' },
          { timestamp: '2026-09-08T15:35:01Z', step: 'FORENSIC_SCAN', status: 'FAILED', detail: 'Copy-move pattern detector triggered in guilloche pattern.' },
          { timestamp: '2026-09-08T15:35:02Z', step: 'ELA_ANALYSIS', status: 'FAILED', detail: 'Severe compression variance (0.892) detected in DOB region.' },
          { timestamp: '2026-09-08T15:35:03Z', step: 'METADATA_ANALYSIS', status: 'WARNING', detail: 'Adobe editing tool signatures present in image metadata stream.' }
        ],
        items: [
          {
            id: 'flag-01',
            severity: 'CRITICAL',
            category: 'Pixel Tampering',
            source: 'ELA-Detector-v2',
            reason: 'Localized high-frequency compression variance (0.892) indicates edited digits in the Date of Birth field.',
            confidence: 0.942,
            bounding_box: { x: 28, y: 52, width: 32, height: 14, label: 'DOB ALTERATION' }
          },
          {
            id: 'flag-02',
            severity: 'HIGH',
            category: 'Typography & Kerning',
            source: 'TypographyModel-v1',
            reason: 'Document number text features non-standard character spacing and baseline variance of 4.8%.',
            confidence: 0.891,
            bounding_box: { x: 52, y: 18, width: 42, height: 12, label: 'FONT ANOMALY' }
          },
          {
            id: 'flag-03',
            severity: 'HIGH',
            category: 'Copy-Move Cloning',
            source: 'SpatialCloneMatcher',
            reason: '14 duplicated keypoint clusters detected between left and right guilloche security patterns.',
            confidence: 0.865,
            bounding_box: { x: 4, y: 56, width: 22, height: 38, label: 'COPY-MOVE' }
          },
          {
            id: 'flag-04',
            severity: 'MEDIUM',
            category: 'Metadata Stream',
            source: 'EXIF Integrity Parser',
            reason: 'Adobe Photoshop CC 2024 software tag identified in JFIF application segment marker.',
            confidence: 0.999
          }
        ]
      },
      decision: {
        outcome: 'MANUAL_REVIEW',
        confidence: 0.94,
        rationale: 'Multiple visual forensics models detected digital tampering, font inconsistency, and localized compression anomalies.',
        recommended_actions: [
          'Hold case for Level-2 forensic examiner review',
          'Request physical verification under ultraviolet (UV) and infrared (IR) scanning',
          'Notify anti-fraud investigation unit'
        ],
        evaluated_at: '2026-09-08T15:35:05Z'
      }
    }
  },

  FACE_MISMATCH: {
    id: 'FACE_MISMATCH',
    label: 'Scenario 4: Face Biometric Mismatch (Passport)',
    document_type: 'PASSPORT',
    outcome: 'REJECTED',
    description: 'Credential is valid, but live face probe confidence is 14.2% (mismatch). Risk score: 89 (HIGH).',
    data: {
      case_id: 'TR-2026-1184-MIS',
      status: 'COMPLETED',
      document_type: 'PASSPORT',
      quality: {
        score: 0.95,
        glare: 0.03,
        blur: 0.02,
        resolution: '3840x2160',
        illumination: 'OPTIMAL',
        status: 'pass',
        issues: []
      },
      preprocessing: {
        normalized: true,
        deskew_angle: 0.1,
        color_space: 'sRGB',
        resolution_dpi: 300,
        pipeline_steps: ['Face detection and landmark extraction', 'Pose normalization', 'ArcFace biometric embedding']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.99,
        language: 'en',
        raw_text: 'P<GBRTHOMPSON<<SARAH<<<<<<<<<<<<<<<<<<<<<<<<\n9812041238GBR9108144F2911206<<<<<<<<<<<<<<02',
        status: 'pass',
        mrz: {
          raw: 'P<GBRTHOMPSON<<SARAH<<<<<<<<<<<<<<<<<<<<<<<<9812041238GBR9108144F2911206<<<<<<<<<<<<<<02',
          parsed: {
            type: 'Passport',
            country: 'GBR',
            surname: 'THOMPSON',
            given_name: 'SARAH',
            doc_number: '981204123',
            dob: '1991-08-14',
            sex: 'F',
            expiry: '2029-11-20'
          },
          valid: true
        }
      },
      fields: {
        document_number: '981204123',
        first_name: 'SARAH',
        last_name: 'THOMPSON',
        full_name: 'SARAH THOMPSON',
        date_of_birth: '1991-08-14',
        expiry_date: '2029-11-20',
        issue_date: '2019-11-21',
        gender: 'F',
        nationality: 'GBR',
        issuing_country: 'United Kingdom',
        address: 'N/A',
        _metadata: {
          document_number: { value: '981204123', confidence: 0.99, validation_status: 'VALID' },
          full_name: { value: 'SARAH THOMPSON', confidence: 0.99, validation_status: 'VALID' },
          date_of_birth: { value: '1991-08-14', confidence: 0.99, validation_status: 'VALID' }
        }
      },
      document_validation: {
        valid_format: true,
        checksum_passed: true,
        expiry_check: 'VALID',
        security_features_verified: true,
        status: 'pass',
        issues: []
      },
      record_check: {
        database_match: true,
        registry_name: 'HMPO Passport Verification Service',
        query_status: 'VERIFIED',
        status: 'match',
        discrepancy_fields: [],
        remarks: 'Passport record active and authentic in issuing passport ledger.'
      },
      identity: {
        face_match_confidence: 0.142,
        match_status: 'MISMATCH',
        liveness_score: 0.978,
        liveness_status: 'PASSED',
        status: 'mismatch',
        notes: 'Biometric distance is 1.48 (Threshold: 0.60). High probability of identity impersonation.'
      },
      visual_forensics: {
        copy_move_detected: false,
        font_anomaly: false,
        metadata_tampered: false,
        ela_score: 0.05,
        edge_inconsistency: false,
        status: 'pass',
        anomalies: [],
        regions: []
      },
      risk: {
        overall_score: 89,
        level: 'HIGH',
        factors: [
          'Face mismatch (confidence 14.2%) +55',
          'Impersonation probability high +34'
        ],
        factors_breakdown: [
          { factor: 'Face Mismatch: Live Probe vs Document Portrait', impact: '+55', score_delta: 55, source: 'ArcFace Recognizer' },
          { factor: 'High Risk Impersonation Attempt', impact: '+34', score_delta: 34, source: 'Identity Module' }
        ]
      },
      evidence: {
        artifacts: [
          {
            id: 'art-mis-01',
            type: 'DOCUMENT_ORIGINAL',
            title: 'Passport Holder Portrait Scan',
            uri: '/samples/passport_portrait.png',
            description: 'Extracted biometric portrait from authentic document'
          },
          {
            id: 'art-mis-02',
            type: 'FACE_SELFIE',
            title: 'Live Selfie Probe',
            uri: '/samples/probe_mismatch.png',
            description: 'Live applicant probe showing distinct facial geometry'
          }
        ],
        audit_trail: [
          { timestamp: '2026-09-08T15:37:10Z', step: 'INGESTION', status: 'SUCCESS', detail: 'Document and biometric assets received.' },
          { timestamp: '2026-09-08T15:37:11Z', step: 'LIVENESS', status: 'SUCCESS', detail: 'Live subject passed passive micro-expression and depth liveness.' },
          { timestamp: '2026-09-08T15:37:12Z', step: 'BIOMETRIC_MATCH', status: 'FAILED', detail: 'Face similarity is 14.2%, far below 75.0% threshold.' }
        ],
        items: [
          {
            id: 'flag-mis-01',
            severity: 'CRITICAL',
            category: 'Biometric Authentication',
            source: 'ArcFace-512D Embedding Matcher',
            reason: 'Cosine similarity between document portrait and live selfie is 0.142 (threshold 0.750).',
            confidence: 0.985
          }
        ]
      },
      decision: {
        outcome: 'REJECTED',
        confidence: 0.98,
        rationale: 'The live selfie photograph does not biometrically match the portrait presented on the genuine document.',
        recommended_actions: [
          'Immediate rejection of identity claim',
          'Flag session for impersonation risk',
          'Log biometric embedding for fraud syndicate detection'
        ],
        evaluated_at: '2026-09-08T15:37:14Z'
      }
    }
  },

  RECORD_MISMATCH: {
    id: 'RECORD_MISMATCH',
    label: 'Scenario 5: Civil Registry Record Mismatch (Travel Permit)',
    document_type: 'TRAVEL_PERMIT',
    outcome: 'MANUAL_REVIEW',
    description: 'Document looks valid, but sovereign database registers differing DOB and nationality. Risk score: 74 (HIGH).',
    data: {
      case_id: 'TR-2026-9932-REC',
      status: 'COMPLETED',
      document_type: 'TRAVEL_PERMIT',
      quality: {
        score: 0.93,
        glare: 0.06,
        blur: 0.04,
        resolution: '2560x1440',
        illumination: 'OPTIMAL',
        status: 'pass',
        issues: []
      },
      preprocessing: {
        normalized: true,
        deskew_angle: 0.4,
        color_space: 'sRGB',
        resolution_dpi: 300,
        pipeline_steps: ['Color balance', 'Barcode decodification', 'Security guilloche extraction']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.971,
        language: 'en',
        raw_text: 'INTERNATIONAL TRANSIT & TRAVEL PERMIT\nPERMIT NO: TP-2026-8819\nHOLDER: CARLOS M. MENDEZ\nDOB: 1994-04-12\nNATIONALITY: ESP',
        status: 'pass'
      },
      fields: {
        document_number: 'TP-2026-8819',
        first_name: 'CARLOS',
        last_name: 'MENDEZ',
        full_name: 'CARLOS M. MENDEZ',
        date_of_birth: '1994-04-12',
        expiry_date: '2027-12-31',
        issue_date: '2025-01-01',
        gender: 'M',
        nationality: 'ESP',
        issuing_country: 'Spain',
        address: 'Calle Mayor 14, Madrid',
        _metadata: {
          document_number: { value: 'TP-2026-8819', confidence: 0.98, validation_status: 'VALID' },
          full_name: { value: 'CARLOS M. MENDEZ', confidence: 0.97, validation_status: 'VALID' },
          date_of_birth: { value: '1994-04-12', confidence: 0.98, validation_status: 'DISCREPANCY' },
          nationality: { value: 'ESP', confidence: 0.98, validation_status: 'DISCREPANCY' }
        }
      },
      document_validation: {
        valid_format: true,
        checksum_passed: true,
        expiry_check: 'VALID',
        security_features_verified: true,
        status: 'pass',
        issues: []
      },
      record_check: {
        database_match: false,
        registry_name: 'Immigration & Border Security Registry (IBSR)',
        query_status: 'DISCREPANCY',
        status: 'mismatch',
        discrepancy_fields: ['date_of_birth', 'nationality'],
        remarks: 'Registry entry for TP-2026-8819 matches CARLOS MENDEZ, but lists DOB as 1991-04-12 and Nationality as MEX.'
      },
      identity: {
        face_match_confidence: 0.938,
        match_status: 'MATCH',
        liveness_score: 0.965,
        liveness_status: 'PASSED',
        status: 'match',
        notes: 'Live face matches physical permit photograph.'
      },
      visual_forensics: {
        copy_move_detected: false,
        font_anomaly: false,
        metadata_tampered: false,
        ela_score: 0.07,
        edge_inconsistency: false,
        status: 'pass',
        anomalies: [],
        regions: []
      },
      risk: {
        overall_score: 74,
        level: 'HIGH',
        factors: [
          'Record mismatch in date of birth +35',
          'Record mismatch in nationality +30',
          'Civil registry discrepancy +9'
        ],
        factors_breakdown: [
          { factor: 'Registry Discrepancy: Date of Birth', impact: '+35', score_delta: 35, source: 'IBSR Registry' },
          { factor: 'Registry Discrepancy: Nationality (ESP vs MEX)', impact: '+30', score_delta: 30, source: 'IBSR Registry' },
          { factor: 'Discrepancy Severity Weight', impact: '+9', score_delta: 9, source: 'Record Comparator' }
        ]
      },
      evidence: {
        artifacts: [
          {
            id: 'art-rec-01',
            type: 'DOCUMENT_ORIGINAL',
            title: 'Submitted Travel Permit',
            uri: '/samples/permit_specimen.png',
            description: 'High-resolution scan of travel authorization card'
          }
        ],
        audit_trail: [
          { timestamp: '2026-09-08T15:40:01Z', step: 'INGESTION', status: 'SUCCESS', detail: 'Travel permit asset processed.' },
          { timestamp: '2026-09-08T15:40:02Z', step: 'OCR_EXTRACTION', status: 'SUCCESS', detail: 'Permit ID TP-2026-8819 parsed.' },
          { timestamp: '2026-09-08T15:40:03Z', step: 'REGISTRY_QUERY', status: 'WARNING', detail: 'Central IBSR returned field value discrepancy on DOB & Nationality.' }
        ],
        items: [
          {
            id: 'flag-rec-01',
            severity: 'HIGH',
            category: 'Civil Registry Verification',
            source: 'Immigration & Border Security Registry (IBSR)',
            reason: 'Physical card lists Date of Birth as 1994-04-12, but official sovereign registry ledger has 1991-04-12.',
            confidence: 0.98
          },
          {
            id: 'flag-rec-02',
            severity: 'HIGH',
            category: 'Civil Registry Verification',
            source: 'Immigration & Border Security Registry (IBSR)',
            reason: 'Physical card indicates Nationality ESP (Spain), but official record lists MEX (Mexico).',
            confidence: 0.98
          }
        ]
      },
      decision: {
        outcome: 'MANUAL_REVIEW',
        confidence: 0.82,
        rationale: 'Physical document passes visual and biometric checks, but central civil registry data contradicts date of birth and nationality.',
        recommended_actions: [
          'Escalate to border immigration supervisor',
          'Cross-reference with embassy bilateral records'
        ],
        evaluated_at: '2026-09-08T15:40:05Z'
      }
    }
  },

  UNAVAILABLE_INCONCLUSIVE: {
    id: 'UNAVAILABLE_INCONCLUSIVE',
    label: 'Scenario 6: Edge Case (Unavailable & Inconclusive Data)',
    document_type: 'NATIONAL_ID',
    outcome: 'MANUAL_REVIEW',
    description: 'Face probe unavailable, registry unreachable, visual forensics inconclusive. Risk: INSUFFICIENT_EVIDENCE (N/A).',
    data: {
      case_id: 'TR-2026-3301-UNA',
      status: 'COMPLETED',
      document_type: 'NATIONAL_ID',
      quality: {
        score: 0.62,
        glare: 0.28,
        blur: 0.35,
        resolution: '1280x720',
        illumination: 'LOW',
        status: 'inconclusive',
        issues: ['Sub-optimal lighting conditions', 'Minor motion blur across character edges']
      },
      preprocessing: {
        normalized: true,
        deskew_angle: 2.4,
        color_space: 'sRGB',
        resolution_dpi: 150,
        pipeline_steps: ['Auto-crop attempted', 'Contrast stretching', 'Histogram equalization']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.54,
        language: 'en',
        raw_text: 'REPUBLIC ID CARD\nDOC: [ILLEGIBLE-BLUR]\nNAME: ALEX K. CHEN\nEXP: 2028-??-??',
        status: 'inconclusive'
      },
      fields: {
        document_number: 'N/A (UNRESOLVED)',
        first_name: 'ALEX',
        last_name: 'CHEN',
        full_name: 'ALEX K. CHEN',
        date_of_birth: 'UNREADABLE',
        expiry_date: '2028-??-??',
        _metadata: {
          document_number: { value: 'UNRESOLVED', confidence: 0.35, validation_status: 'UNAVAILABLE' },
          full_name: { value: 'ALEX K. CHEN', confidence: 0.72, validation_status: 'UNVERIFIED' },
          date_of_birth: { value: 'UNREADABLE', confidence: 0.21, validation_status: 'UNAVAILABLE' }
        }
      },
      document_validation: {
        valid_format: true,
        checksum_passed: false,
        expiry_check: 'UNAVAILABLE',
        security_features_verified: false,
        status: 'inconclusive',
        issues: ['Checksum could not be verified due to incomplete alphanumeric parsing']
      },
      record_check: {
        database_match: false,
        registry_name: 'Central Identity Authority Gateway',
        query_status: 'SERVICE_UNAVAILABLE',
        status: 'unavailable',
        discrepancy_fields: [],
        remarks: 'Registry lookup timed out (HTTP 503 Service Unavailable). Not considered a match or mismatch.'
      },
      identity: {
        face_match_confidence: 0.0,
        match_status: 'UNAVAILABLE',
        liveness_score: 0.0,
        liveness_status: 'UNAVAILABLE',
        status: 'unavailable',
        notes: 'No reference biometric face selfie was uploaded for this case.'
      },
      visual_forensics: {
        copy_move_detected: false,
        font_anomaly: false,
        metadata_tampered: false,
        ela_score: 0.42,
        edge_inconsistency: false,
        status: 'inconclusive',
        anomalies: [
          'Inconclusive ELA: Input resolution (150 DPI) below optimal forensic threshold (300 DPI)',
          'Guilloche pattern partially obscured by specular glare'
        ],
        regions: []
      },
      risk: {
        overall_score: 0,
        level: 'INSUFFICIENT_EVIDENCE',
        factors: [
          'Insufficient primary data to compute deterministic risk score',
          'Biometric reference probe missing (not provided by applicant)',
          'Civil registry connectivity temporarily unavailable (HTTP 503)',
          'Visual forensics inconclusive due to sub-optimal image capture'
        ],
        factors_breakdown: [
          { factor: 'Missing Biometric Probe', impact: 'N/A', score_delta: 0, source: 'Biometric Engine' },
          { factor: 'Registry Timeout (HTTP 503)', impact: 'N/A', score_delta: 0, source: 'Registry Gateway' },
          { factor: 'Inconclusive Optical Resolution', impact: 'N/A', score_delta: 0, source: 'Quality Engine' }
        ]
      },
      evidence: {
        artifacts: [
          {
            id: 'art-una-01',
            type: 'DOCUMENT_ORIGINAL',
            title: 'Sub-Optimal Input Scan',
            uri: '/samples/blurry_specimen.png',
            description: 'Low-resolution input showing glare in header region'
          }
        ],
        audit_trail: [
          { timestamp: '2026-09-08T15:42:01Z', step: 'INGESTION', status: 'WARNING', detail: 'Document ingested at 150 DPI. No biometric probe attached.' },
          { timestamp: '2026-09-08T15:42:02Z', step: 'OCR_EXTRACTION', status: 'WARNING', detail: 'Partial character recognition confidence (54%).' },
          { timestamp: '2026-09-08T15:42:03Z', step: 'REGISTRY_QUERY', status: 'UNAVAILABLE', detail: 'Central Identity Gateway returned HTTP 503.' }
        ],
        items: [
          {
            id: 'flag-una-01',
            severity: 'INFO',
            category: 'System Availability',
            source: 'Central Identity Gateway',
            reason: 'Sovereign civil registry was unreachable during inspection. Card marked UNAVAILABLE (not treated as fraud).',
            confidence: 1.0
          },
          {
            id: 'flag-una-02',
            severity: 'INFO',
            category: 'Input Completeness',
            source: 'Biometric Pipeline',
            reason: 'Applicant did not upload live reference selfie. Face verification marked UNAVAILABLE.',
            confidence: 1.0
          }
        ]
      },
      decision: {
        outcome: 'MANUAL_REVIEW',
        confidence: 0.45,
        rationale: 'Verification inconclusive due to incomplete input assets and external registry downtime. Never automatically treated as fraudulent.',
        recommended_actions: [
          'Request re-submission with higher resolution scan (≥ 300 DPI)',
          'Request live biometric face capture',
          'Retry civil registry lookup once sovereign gateway recovers'
        ],
        evaluated_at: '2026-09-08T15:42:05Z'
      }
    }
  },

  PIPELINE_ERROR: {
    id: 'PIPELINE_ERROR',
    label: 'Scenario 7: Verification System Error',
    document_type: 'PASSPORT',
    outcome: 'MANUAL_REVIEW',
    description: 'Simulates an upstream processing fault or file decode corruption. Status: FAILED.',
    data: {
      case_id: 'TR-2026-0099-ERR',
      status: 'FAILED',
      document_type: 'PASSPORT',
      quality: {
        score: 0.0,
        glare: 0.0,
        blur: 0.0,
        resolution: 'UNKNOWN',
        illumination: 'IRREGULAR',
        status: 'fail',
        issues: ['Corrupted JPEG header / stream decode error']
      },
      preprocessing: {
        normalized: false,
        deskew_angle: 0.0,
        color_space: 'UNKNOWN',
        resolution_dpi: 0,
        pipeline_steps: ['Ingestion failed']
      },
      ocr: {
        engine: 'ForensicOCR-v3.4',
        confidence: 0.0,
        language: 'unknown',
        raw_text: '',
        status: 'unavailable'
      },
      fields: {
        document_number: 'N/A',
        first_name: 'N/A',
        last_name: 'N/A',
        full_name: 'N/A',
        date_of_birth: 'N/A',
        expiry_date: 'N/A'
      },
      document_validation: {
        valid_format: false,
        checksum_passed: false,
        expiry_check: 'UNAVAILABLE',
        security_features_verified: false,
        status: 'unavailable',
        issues: ['Processing aborted: payload stream decode failure']
      },
      record_check: {
        database_match: false,
        registry_name: 'N/A',
        query_status: 'SERVICE_UNAVAILABLE',
        status: 'unavailable',
        discrepancy_fields: [],
        remarks: 'Pipeline aborted before registry dispatch.'
      },
      identity: {
        face_match_confidence: 0.0,
        match_status: 'UNAVAILABLE',
        liveness_score: 0.0,
        liveness_status: 'UNAVAILABLE',
        status: 'unavailable',
        notes: 'Biometric pipeline not reached.'
      },
      visual_forensics: {
        copy_move_detected: false,
        font_anomaly: false,
        metadata_tampered: false,
        ela_score: 0.0,
        edge_inconsistency: false,
        status: 'unavailable',
        anomalies: ['Pipeline aborted before visual forensic pass'],
        regions: []
      },
      risk: {
        overall_score: 0,
        level: 'INSUFFICIENT_EVIDENCE',
        factors: [
          'Verification pipeline terminated unexpectedly',
          'File stream corrupted or unsupported encoding'
        ],
        factors_breakdown: []
      },
      evidence: {
        artifacts: [],
        audit_trail: [
          { timestamp: '2026-09-08T15:45:00Z', step: 'INGESTION', status: 'FAILED', detail: 'Fatal decode error: premature EOF in input image byte stream.' }
        ],
        items: [
          {
            id: 'flag-err-01',
            severity: 'CRITICAL',
            category: 'System Error',
            source: 'ImageDecoder-Pipeline',
            reason: 'Corrupted payload byte stream. Processing halted.',
            confidence: 1.0
          }
        ]
      },
      decision: {
        outcome: 'MANUAL_REVIEW',
        confidence: 0.0,
        rationale: 'System was unable to decode input image stream. No determination could be made.',
        recommended_actions: [
          'Prompt user to re-upload image in uncorrupted standard JPEG or PNG format',
          'Check ingestion gateway logs'
        ],
        evaluated_at: '2026-09-08T15:45:02Z'
      }
    }
  }
};
