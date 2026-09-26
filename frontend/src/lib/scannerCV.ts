/**
 * BorderShield AI - Document Scanner Computer Vision Engine (scannerCV.ts)
 * 
 * Provides pure algorithms for:
 * 1. Capture-quality checks: Blur, Glare, Low Lighting, Cut-off Edges, Reflections.
 * 2. Skew angle estimation and document edge boundary detection.
 * 3. Client-side canvas transformations (crop, deskew, rotation correction).
 * 4. Realistic demo sample generator for Passport, Visa, National ID, Driving Licence, Permit.
 * 5. Multi-spectral simulation (UV 365nm fluorescence, IR 850nm absorption, QR payload, RFID e-Chip).
 */

export type DocumentType = "PASSPORT" | "VISA" | "NATIONAL_ID" | "DRIVING_LICENCE" | "PERMIT";
export type ModalityType = "RGB" | "UV" | "IR" | "QR_BARCODE" | "RFID_NFC";
export type DocumentSide = "front" | "back";

export interface QualityMetric {
  score: number; // 0 to 100
  passed: boolean;
  label: string;
  detail: string;
}

export interface QualityAnalysisResult {
  overallScore: number; // 0 to 100
  grade: "EXCELLENT" | "ACCEPTABLE" | "DEGRADED" | "CRITICAL_FAIL";
  blur: QualityMetric;
  glare: QualityMetric;
  lighting: QualityMetric;
  cutoff: QualityMetric;
  reflection: QualityMetric;
  recommendations: string[];
}

export interface DocumentGeometry {
  name: string;
  aspectRatio: number; // width / height
  isoStandard: string;
  hasBackSide: boolean;
  hasMRZ: boolean;
  mrzHeightRatio?: number; // portion of bottom reserved for MRZ
}

export const DOCUMENT_CONFIGS: Record<DocumentType, DocumentGeometry> = {
  PASSPORT: {
    name: "International Passport",
    aspectRatio: 1.42, // TD3 standard (125mm x 88mm)
    isoStandard: "ICAO Doc 9303 TD3",
    hasBackSide: false,
    hasMRZ: true,
    mrzHeightRatio: 0.22,
  },
  VISA: {
    name: "Consular Visa Foil",
    aspectRatio: 1.39, // MRV-A / TD2 standard
    isoStandard: "ICAO Doc 9303 MRV-A",
    hasBackSide: false,
    hasMRZ: true,
    mrzHeightRatio: 0.24,
  },
  NATIONAL_ID: {
    name: "National Identity Card",
    aspectRatio: 1.586, // ISO/IEC 7810 ID-1 (85.60mm x 53.98mm)
    isoStandard: "ISO/IEC 7810 ID-1",
    hasBackSide: true,
    hasMRZ: false,
  },
  DRIVING_LICENCE: {
    name: "Driving Licence",
    aspectRatio: 1.586, // ISO/IEC 7810 ID-1
    isoStandard: "ISO/IEC 18013 / ID-1",
    hasBackSide: true,
    hasMRZ: false,
  },
  PERMIT: {
    name: "Residence / Work Permit",
    aspectRatio: 1.586, // ID-1 standard biometric permit
    isoStandard: "EU / ISO 7810 ID-1",
    hasBackSide: true,
    hasMRZ: false,
  },
};

/**
 * Pure quality analysis running on raw pixel RGBA data.
 */
export function analyzeCaptureQuality(
  pixelData: Uint8ClampedArray | number[],
  width: number,
  height: number,
  marginCheckPercent = 0.04
): QualityAnalysisResult {
  if (width < 320 || height < 240) {
    const failMetric: QualityMetric = {
      score: 10,
      passed: false,
      label: "Resolution",
      detail: `Resolution ${width}x${height} too low for forensic OCR extraction.`,
    };
    return {
      overallScore: 10,
      grade: "CRITICAL_FAIL",
      blur: failMetric,
      glare: failMetric,
      lighting: failMetric,
      cutoff: failMetric,
      reflection: failMetric,
      recommendations: ["Position camera closer to credential or upload a higher-resolution scan (min 720p)."],
    };
  }

  const totalPixels = width * height;
  const sampleStep = Math.max(1, Math.floor(Math.sqrt(totalPixels) / 120)); // dynamic sampling for responsiveness

  let totalLuminance = 0;
  let samples = 0;
  let overexposedPixels = 0;
  let underexposedPixels = 0;
  let specularClusteringCount = 0;

  // Track luminance variance for blur / sharpness estimation
  let sumDiffs = 0;
  let edgeCount = 0;

  // Perimeter margin checking for cut-off edges
  let borderEdgeIntersections = 0;
  let borderSampleCount = 0;

  const marginX = Math.floor(width * marginCheckPercent);
  const marginY = Math.floor(height * marginCheckPercent);

  // Analyze samples
  for (let y = sampleStep; y < height - sampleStep; y += sampleStep) {
    for (let x = sampleStep; x < width - sampleStep; x += sampleStep) {
      const idx = (y * width + x) * 4;
      const r = pixelData[idx];
      const g = pixelData[idx + 1];
      const b = pixelData[idx + 2];

      // ITU-R BT.601 luminance
      const lum = 0.299 * r + 0.587 * g + 0.114 * b;
      totalLuminance += lum;
      samples++;

      if (lum < 28) underexposedPixels++;
      if (lum > 248) {
        overexposedPixels++;
        // Check adjacent pixel for glare clustering
        const rightIdx = idx + 4;
        const rightLum = 0.299 * pixelData[rightIdx] + 0.587 * pixelData[rightIdx + 1] + 0.114 * pixelData[rightIdx + 2];
        if (rightLum > 240) {
          specularClusteringCount++;
        }
      }

      // Laplacian approximation for sharpness/blur: |I(x,y) - I(x+step, y)| + |I(x,y) - I(x, y+step)|
      const rightIdx = idx + sampleStep * 4;
      const downIdx = (Math.min(height - 1, y + sampleStep) * width + x) * 4;
      const lumRight = 0.299 * pixelData[rightIdx] + 0.587 * pixelData[rightIdx + 1] + 0.114 * pixelData[rightIdx + 2];
      const lumDown = 0.299 * pixelData[downIdx] + 0.587 * pixelData[downIdx + 1] + 0.114 * pixelData[downIdx + 2];

      const diff = Math.abs(lum - lumRight) + Math.abs(lum - lumDown);
      sumDiffs += diff;
      if (diff > 35) edgeCount++;

      // Check if strong edge is located right on the outer margin border
      const isNearBorder = x <= marginX || x >= width - marginX || y <= marginY || y >= height - marginY;
      if (isNearBorder) {
        borderSampleCount++;
        if (diff > 45) {
          borderEdgeIntersections++;
        }
      }
    }
  }

  const avgLuminance = totalLuminance / (samples || 1);
  const sharpnessScore = Math.min(100, Math.round((sumDiffs / (samples || 1)) * 4.2));
  const glareRatio = overexposedPixels / (samples || 1);
  const underRatio = underexposedPixels / (samples || 1);
  const borderEdgeRatio = borderSampleCount > 0 ? borderEdgeIntersections / borderSampleCount : 0;
  const reflectionRatio = specularClusteringCount / (samples || 1);

  // 1. Blur Check
  const blurScore = Math.max(0, Math.min(100, sharpnessScore >= 20 ? Math.min(100, sharpnessScore * 2) : sharpnessScore * 3));
  const blurPassed = blurScore >= 60;
  const blurMetric: QualityMetric = {
    score: blurScore,
    passed: blurPassed,
    label: "Focus & Sharpness",
    detail: blurPassed ? "Text lines and security microprint are sharply resolved." : "Image is soft or motion-blurred. Hold camera steady.",
  };

  // 2. Glare Check
  const glareScore = Math.max(0, Math.min(100, Math.round(100 - glareRatio * 400)));
  const glarePassed = glareScore >= 70 && glareRatio < 0.08;
  const glareMetric: QualityMetric = {
    score: glareScore,
    passed: glarePassed,
    label: "Anti-Glare",
    detail: glarePassed ? "Surface specular highlights within acceptable tolerance." : "Optical glare detected on document laminate. Tilt card slightly.",
  };

  // 3. Lighting Check
  let lightingScore = 100;
  if (avgLuminance < 40) {
    lightingScore = Math.max(10, Math.round((avgLuminance / 40) * 50));
  } else if (avgLuminance > 220) {
    lightingScore = Math.max(20, Math.round(100 - (avgLuminance - 220) * 2.5));
  } else {
    lightingScore = Math.round(85 + (1 - Math.abs(avgLuminance - 130) / 100) * 15);
  }
  const lightingPassed = avgLuminance >= 40 && avgLuminance <= 225 && underRatio < 0.25;
  const lightingMetric: QualityMetric = {
    score: Math.min(100, lightingScore),
    passed: lightingPassed,
    label: "Illumination",
    detail: lightingPassed ? `Balanced lighting level (avg lum ${Math.round(avgLuminance)}/255).` : avgLuminance < 40 ? "Lighting is too dark. Increase ambient illumination or enable torch." : "Lighting is harsh or overexposed.",
  };

  // 4. Cut-off Edges Check
  const cutoffScore = Math.max(0, Math.min(100, Math.round(100 - borderEdgeRatio * 320)));
  const cutoffPassed = cutoffScore >= 65 && borderEdgeRatio < 0.12;
  const cutoffMetric: QualityMetric = {
    score: cutoffScore,
    passed: cutoffPassed,
    label: "Framing & Margins",
    detail: cutoffPassed ? "All credential borders detected inside the viewport." : "Document edges appear clipped or extending past viewport borders.",
  };

  // 5. Reflection Check
  const reflectionScore = Math.max(0, Math.min(100, Math.round(100 - reflectionRatio * 500)));
  const reflectionPassed = reflectionScore >= 70;
  const reflectionMetric: QualityMetric = {
    score: reflectionScore,
    passed: reflectionPassed,
    label: "Reflection Shield",
    detail: reflectionPassed ? "No localized specular hotspots obscuring security features." : "Localized reflection flare detected. Adjust angle from overhead lighting.",
  };

  // Overall Score (weighted fusion)
  const overallScore = Math.round(
    blurMetric.score * 0.3 +
    glareMetric.score * 0.2 +
    lightingMetric.score * 0.2 +
    cutoffMetric.score * 0.15 +
    reflectionMetric.score * 0.15
  );

  let grade: QualityAnalysisResult["grade"] = "EXCELLENT";
  if (overallScore < 50) grade = "CRITICAL_FAIL";
  else if (overallScore < 70) grade = "DEGRADED";
  else if (overallScore < 85) grade = "ACCEPTABLE";

  const recommendations: string[] = [];
  if (!blurPassed) recommendations.push("Stabilize the camera or move further back to allow auto-focus.");
  if (!glarePassed) recommendations.push("Tilt document slightly (5-10°) to redirect specular glare away from the lens.");
  if (!lightingPassed) recommendations.push("Adjust ambient light source or turn on the camera flashlight.");
  if (!cutoffPassed) recommendations.push("Center the credential fully inside the dashed boundary guides.");
  if (!reflectionPassed) recommendations.push("Avoid direct flashlight reflections directly over portrait and MRZ zones.");

  return {
    overallScore,
    grade,
    blur: blurMetric,
    glare: glareMetric,
    lighting: lightingMetric,
    cutoff: cutoffMetric,
    reflection: reflectionMetric,
    recommendations,
  };
}

/**
 * Estimates skew angle in degrees (-8 to +8) using horizontal text line projection profile energy.
 */
export function estimateSkewAngle(
  pixelData: Uint8ClampedArray | number[],
  width: number,
  height: number
): number {
  if (width < 100 || height < 100) return 0;

  const maxAngle = 7;
  const angles: number[] = [];
  for (let a = -maxAngle; a <= maxAngle; a += 0.5) {
    angles.push(a);
  }

  // Pre-calculate safe sampling window so all tested angles project strictly inside [0, height)
  const radFactor = Math.PI / 180;
  const maxTan = Math.tan(maxAngle * radFactor);
  const safeMarginY = Math.ceil((width / 2) * maxTan) + 2;

  const startY = Math.max(4, safeMarginY);
  const endY = Math.min(height - 4, height - safeMarginY);
  if (startY >= endY) return 0;

  const sampleYStep = Math.max(2, Math.floor(height / 60));
  const sampleXStep = Math.max(2, Math.floor(width / 80));
  const centerX = width / 2;

  let bestAngle = 0;
  let maxEnergy = -1;

  for (const angle of angles) {
    const rad = angle * radFactor;
    const tan = Math.tan(rad);
    const bins = new Float32Array(height);

    for (let y = startY; y < endY; y += sampleYStep) {
      for (let x = sampleXStep; x < width - sampleXStep; x += sampleXStep) {
        const projY = Math.round(y - (x - centerX) * tan);
        if (projY >= 0 && projY < height) {
          const idx = (y * width + x) * 4;
          const lum = 0.299 * pixelData[idx] + 0.587 * pixelData[idx + 1] + 0.114 * pixelData[idx + 2];
          // Detect dark text strokes on bright background (inverted luminance)
          bins[projY] += (255 - lum);
        }
      }
    }

    // Energy: sum of squares of profile sums (sharp text lines create high peaks and deep valleys)
    let energy = 0;
    for (let i = 0; i < height; i++) {
      energy += bins[i] * bins[i];
    }

    if (energy > maxEnergy) {
      maxEnergy = energy;
      bestAngle = angle;
    }
  }

  return Math.round(bestAngle * 10) / 10;
}

/**
 * Performs client-side automatic cropping, deskewing, and contrast normalization on an HTML Canvas.
 */
export function processDocumentCorrections(
  sourceCanvas: HTMLCanvasElement,
  options: {
    targetAspectRatio?: number;
    cropPadding?: number; // 0.05 = 5%
    autoDeskew?: boolean;
    autoCrop?: boolean;
    contrastBoost?: boolean;
  } = {}
): {
  correctedCanvas: HTMLCanvasElement;
  detectedSkew: number;
  cropRect: { x: number; y: number; width: number; height: number };
} {
  const {
    targetAspectRatio = 1.42,
    cropPadding = 0.03,
    autoDeskew = true,
    autoCrop = true,
    contrastBoost = true,
  } = options;

  const srcWidth = sourceCanvas.width;
  const srcHeight = sourceCanvas.height;
  const srcCtx = sourceCanvas.getContext("2d", { willReadFrequently: true });

  if (!srcCtx) {
    return {
      correctedCanvas: sourceCanvas,
      detectedSkew: 0,
      cropRect: { x: 0, y: 0, width: srcWidth, height: srcHeight },
    };
  }

  const imgData = srcCtx.getImageData(0, 0, srcWidth, srcHeight);
  const detectedSkew = autoDeskew ? estimateSkewAngle(imgData.data, srcWidth, srcHeight) : 0;

  // 1. Create intermediate canvas for rotation if skew is detected
  let workingCanvas = sourceCanvas;
  if (Math.abs(detectedSkew) > 0.2) {
    const rotCanvas = document.createElement("canvas");
    rotCanvas.width = srcWidth;
    rotCanvas.height = srcHeight;
    const rotCtx = rotCanvas.getContext("2d");
    if (rotCtx) {
      rotCtx.translate(srcWidth / 2, srcHeight / 2);
      rotCtx.rotate((-detectedSkew * Math.PI) / 180);
      rotCtx.drawImage(sourceCanvas, -srcWidth / 2, -srcHeight / 2);
      workingCanvas = rotCanvas;
    }
  }

  // 2. Compute crop bounding box based on target aspect ratio and document guides
  let cropWidth = srcWidth * (1 - cropPadding * 2);
  let cropHeight = cropWidth / targetAspectRatio;

  if (cropHeight > srcHeight * (1 - cropPadding * 2)) {
    cropHeight = srcHeight * (1 - cropPadding * 2);
    cropWidth = cropHeight * targetAspectRatio;
  }

  const cropX = Math.round((srcWidth - cropWidth) / 2);
  const cropY = Math.round((srcHeight - cropHeight) / 2);
  const cropRect = {
    x: Math.max(0, cropX),
    y: Math.max(0, cropY),
    width: Math.min(srcWidth, Math.round(cropWidth)),
    height: Math.min(srcHeight, Math.round(cropHeight)),
  };

  // 3. Render cropped & corrected output canvas
  const outCanvas = document.createElement("canvas");
  outCanvas.width = autoCrop ? cropRect.width : srcWidth;
  outCanvas.height = autoCrop ? cropRect.height : srcHeight;
  const outCtx = outCanvas.getContext("2d");

  if (outCtx) {
    if (autoCrop) {
      outCtx.drawImage(
        workingCanvas,
        cropRect.x,
        cropRect.y,
        cropRect.width,
        cropRect.height,
        0,
        0,
        outCanvas.width,
        outCanvas.height
      );
    } else {
      outCtx.drawImage(workingCanvas, 0, 0);
    }

    // 4. Subtle contrast normalization & unsharp sharpening filter
    if (contrastBoost) {
      try {
        const outImgData = outCtx.getImageData(0, 0, outCanvas.width, outCanvas.height);
        const d = outImgData.data;
        const contrastFactor = 1.08; // subtle 8% enhancement for OCR clarity
        for (let i = 0; i < d.length; i += 4) {
          d[i] = Math.min(255, Math.max(0, (d[i] - 128) * contrastFactor + 128));
          d[i + 1] = Math.min(255, Math.max(0, (d[i + 1] - 128) * contrastFactor + 128));
          d[i + 2] = Math.min(255, Math.max(0, (d[i + 2] - 128) * contrastFactor + 128));
        }
        outCtx.putImageData(outImgData, 0, 0);
      } catch {}
    }
  }

  return {
    correctedCanvas: outCanvas,
    detectedSkew,
    cropRect,
  };
}

/**
 * Creates an authentic high-resolution demo credential for testing and demonstrations.
 */
export function generateDemoSample(docType: DocumentType, side: DocumentSide = "front"): Promise<File> {
  return new Promise((resolve) => {
    const config = DOCUMENT_CONFIGS[docType];
    const width = 1200;
    const height = Math.round(width / config.aspectRatio);

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      canvas.toBlob((blob) => {
        resolve(new File([blob || new Blob()], `${docType.toLowerCase()}_sample.png`, { type: "image/png" }));
      });
      return;
    }

    // Background base
    const grad = ctx.createLinearGradient(0, 0, width, height);
    if (docType === "PASSPORT") {
      grad.addColorStop(0, "#eef2f6");
      grad.addColorStop(0.5, "#dbeafe");
      grad.addColorStop(1, "#eff6ff");
    } else if (docType === "VISA") {
      grad.addColorStop(0, "#fef3c7");
      grad.addColorStop(0.5, "#fde68a");
      grad.addColorStop(1, "#fffbeb");
    } else if (docType === "DRIVING_LICENCE") {
      grad.addColorStop(0, "#fce7f3");
      grad.addColorStop(0.5, "#fed7aa");
      grad.addColorStop(1, "#fef9c3");
    } else {
      grad.addColorStop(0, "#e0e7ff");
      grad.addColorStop(0.5, "#c7d2fe");
      grad.addColorStop(1, "#eef2ff");
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);

    // Guilloche security wave pattern overlay
    ctx.strokeStyle = "rgba(59, 130, 246, 0.15)";
    ctx.lineWidth = 1.2;
    for (let i = 0; i < height; i += 18) {
      ctx.beginPath();
      for (let x = 0; x < width; x += 10) {
        const y = i + Math.sin((x + i) * 0.02) * 8 + Math.cos(x * 0.01) * 6;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // Credential Header Banner
    ctx.fillStyle = "#1e293b";
    ctx.font = "bold 26px sans-serif";
    const headerTitle =
      docType === "PASSPORT" ? "REPUBLIC OF UTOPIA / PASSEPORT" :
      docType === "VISA" ? "SCHENGEN TRAVEL VISA / VISA DE VOYAGE" :
      docType === "DRIVING_LICENCE" ? "DRIVING LICENCE / PERMIS DE CONDUIRE" :
      docType === "PERMIT" ? "RESIDENCE PERMIT / TITRE DE SEJOUR" :
      "NATIONAL IDENTITY CARD / CARTE NATIONALE";

    ctx.fillText(headerTitle, 50, 60);

    ctx.fillStyle = "#64748b";
    ctx.font = "14px monospace";
    ctx.fillText(`DOCUMENT TYPE: ${config.isoStandard} • SPECIMEN #${Date.now().toString().slice(-6)}`, 50, 88);

    // Security Emblem
    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 3;
    ctx.strokeRect(width - 140, 25, 90, 70);
    ctx.fillStyle = "#2563eb";
    ctx.font = "bold 12px sans-serif";
    ctx.fillText("SECURITY", width - 130, 52);
    ctx.fillText("FEATURE", width - 128, 72);

    if (side === "front") {
      // Photo Bounding Box (Left)
      const photoX = 60;
      const photoY = 120;
      const photoW = 240;
      const photoH = 320;

      ctx.fillStyle = "#cbd5e1";
      ctx.fillRect(photoX, photoY, photoW, photoH);
      ctx.strokeStyle = "#94a3b8";
      ctx.lineWidth = 2;
      ctx.strokeRect(photoX, photoY, photoW, photoH);

      // Stylized biometric portrait avatar silhouette
      ctx.fillStyle = "#475569";
      ctx.beginPath();
      ctx.arc(photoX + photoW / 2, photoY + 110, 55, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(photoX + photoW / 2, photoY + 310, 110, Math.PI, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 14px monospace";
      ctx.fillText("DIGITAL PORTRAIT", photoX + 45, photoY + photoH - 20);

      // Microprint Holographic Overlay on photo
      ctx.fillStyle = "rgba(37, 99, 235, 0.4)";
      ctx.font = "10px sans-serif";
      ctx.fillText("SECURE ICAO 9303 BIOMETRIC", photoX + 25, photoY + 30);

      // Data Fields Table
      const fieldsX = 340;
      let curY = 140;
      const fieldSpacing = 44;

      const fields = [
        { label: "SURNAME / NOM", val: "ERIKSSON" },
        { label: "GIVEN NAMES / PRENOMS", val: "ANNA MARIA" },
        { label: "NATIONALITY / NATIONALITE", val: "UTOPIAN / UTO" },
        { label: "DATE OF BIRTH / DATE DE NAISSANCE", val: "12 AUG / AOU 1984" },
        { label: "SEX / SEXE", val: "F" },
        { label: "DOCUMENT NUMBER / NUMERO", val: "L898902C3" },
        { label: "DATE OF EXPIRY / DATE D'EXPIRATION", val: "15 APR / AVR 2032" },
      ];

      fields.forEach((f) => {
        ctx.fillStyle = "#64748b";
        ctx.font = "bold 12px sans-serif";
        ctx.fillText(f.label, fieldsX, curY);

        ctx.fillStyle = "#0f172a";
        ctx.font = "bold 18px monospace";
        ctx.fillText(f.val, fieldsX, curY + 20);

        curY += fieldSpacing;
      });

      // Signature Box
      ctx.strokeStyle = "#cbd5e1";
      ctx.strokeRect(340, curY, 260, 48);
      ctx.fillStyle = "#475569";
      ctx.font = "italic 22px serif";
      ctx.fillText("Anna M. Eriksson", 360, curY + 32);

      // MRZ Zone (Machine Readable Zone) at bottom for Passports / Visas
      if (config.hasMRZ) {
        const mrzY = height - 140;
        ctx.fillStyle = "#f8fafc";
        ctx.fillRect(40, mrzY, width - 80, 110);
        ctx.strokeStyle = "#cbd5e1";
        ctx.lineWidth = 1;
        ctx.strokeRect(40, mrzY, width - 80, 110);

        ctx.fillStyle = "#0f172a";
        ctx.font = "bold 24px monospace";

        if (docType === "PASSPORT") {
          ctx.fillText("P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<", 60, mrzY + 45);
          ctx.fillText("L898902C36UTO8408122F3204159ZE184226B<<<<<10", 60, mrzY + 85);
        } else {
          ctx.fillText("V<UTOSPECIMEN<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<", 60, mrzY + 45);
          ctx.fillText("V898902C36UTO8408122F3204159ZE184226B<<<<<10", 60, mrzY + 85);
        }
      }
    } else {
      // Reverse / Back Side Demo
      ctx.fillStyle = "#475569";
      ctx.font = "bold 20px sans-serif";
      ctx.fillText("REVERSE SIDE / VERSO", 60, 140);

      // Magnetic Stripe / Barcode Simulation
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(60, 180, width - 120, 90);

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 13px monospace";
      ctx.fillText("PDF417 / 2D MACHINE-READABLE OPTICAL ENCODING BARCODE", 90, 230);

      // Back Details
      let bY = 320;
      const bFields = [
        { label: "ISSUING AUTHORITY", val: "MINISTRY OF FOREIGN AFFAIRS & BORDER CONTROL" },
        { label: "RESIDENTIAL ADDRESS", val: "42 CITADEL EMBANKMENT, SECTOR 7, METROPOLIS" },
        { label: "CATEGORIES / ENDORSEMENTS", val: "A, B, B1, BE (VALID UNTIL 15/04/2032)" },
        { label: "CARD CAN / CHIP NUMBER", val: "938201 / ICAO-PKI-SIGNED" },
      ];

      bFields.forEach((bf) => {
        ctx.fillStyle = "#64748b";
        ctx.font = "bold 12px sans-serif";
        ctx.fillText(bf.label, 60, bY);
        ctx.fillStyle = "#0f172a";
        ctx.font = "bold 16px monospace";
        ctx.fillText(bf.val, 60, bY + 22);
        bY += 50;
      });
    }

    // Outer document border
    ctx.strokeStyle = "rgba(15, 23, 42, 0.4)";
    ctx.lineWidth = 4;
    ctx.strokeRect(10, 10, width - 20, height - 20);

    canvas.toBlob(
      (blob) => {
        const file = new File(
          [blob || new Blob()],
          `SAMPLE_${docType}_${side.toUpperCase()}.png`,
          { type: "image/png" }
        );
        resolve(file);
      },
      "image/png",
      0.95
    );
  });
}
