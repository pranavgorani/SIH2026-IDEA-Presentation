import React, { useState } from 'react';
import { AlertTriangle, Crosshair, ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff } from 'lucide-react';
import { BoundingBox, EvidenceFlagItem, VisualForensics } from '../types';

interface DocumentEvidenceViewerProps {
  documentUri?: string;
  documentType: string;
  visualForensics: VisualForensics;
  evidenceItems?: EvidenceFlagItem[];
  selectedBoxId?: string | null;
  onSelectBox?: (boxId: string | null) => void;
}

export const DocumentEvidenceViewer: React.FC<DocumentEvidenceViewerProps> = ({
  documentUri,
  documentType,
  visualForensics,
  evidenceItems = [],
  selectedBoxId,
  onSelectBox,
}) => {
  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const [showOverlays, setShowOverlays] = useState<boolean>(true);

  // Extract regions from visual_forensics or evidenceItems
  const regions: BoundingBox[] = visualForensics.regions && visualForensics.regions.length > 0
    ? visualForensics.regions
    : visualForensics.bounding_boxes && visualForensics.bounding_boxes.length > 0
    ? visualForensics.bounding_boxes
    : evidenceItems
        .filter((item) => item.bounding_box)
        .map((item) => ({
          ...item.bounding_box!,
          label: item.category,
          reason: item.reason,
          severity: item.severity,
          confidence: item.confidence,
        }));

  const handleZoomIn = () => setZoomLevel((z) => Math.min(2.5, z + 0.25));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(0.75, z - 0.25));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div className="bg-white border border-[#dadce0] rounded-2xl p-5 shadow-xs space-y-4 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#f1f3f4]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-[#e8f0fe] flex items-center justify-center text-[#1a73e8]">
            <Crosshair className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-[#202124]">
              High-Resolution Surface & Anomaly Reticles
            </h3>
            <p className="text-xs text-[#5f6368]">
              {documentType.replace(/_/g, ' ')} specimen
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          {regions.length > 0 ? (
            <span className="px-2.5 py-0.5 rounded-full bg-[#fce8e6] text-[#c5221f] border border-[#fad2cf] font-medium">
              {regions.length} anomalies localized
            </span>
          ) : (
            <span className="px-2.5 py-0.5 rounded-full bg-[#e6f4ea] text-[#137333] border border-[#ceead6] font-medium">
              Surface verified clean
            </span>
          )}
        </div>
      </div>

      {/* Main Document Inspection Canvas */}
      <div className="relative rounded-2xl overflow-hidden border border-[#dadce0] bg-[#f8fafd] aspect-[16/10] sm:aspect-[16/9] flex items-center justify-center select-none shadow-inner group">
        
        {/* Document Image with Zoom */}
        <div 
          className="w-full h-full flex items-center justify-center p-4 transition-transform duration-200"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          {documentUri && (documentUri.startsWith('blob:') || documentUri.startsWith('data:') || documentUri.startsWith('/')) ? (
            <img
              src={documentUri}
              alt={`${documentType} Specimen`}
              className="max-h-full max-w-full object-contain rounded-lg shadow-sm"
            />
          ) : (
            <div className="w-full h-full max-w-md bg-white border border-[#dadce0] rounded-xl p-6 shadow-sm flex flex-col justify-between">
              <div className="flex justify-between items-center pb-2 border-b border-[#f1f3f4]">
                <span className="font-bold text-xs text-[#1a73e8] uppercase tracking-wider">{documentType.replace(/_/g, ' ')}</span>
                <span className="text-[10px] text-[#5f6368] font-mono">SPECIMEN</span>
              </div>
              <div className="space-y-2 text-xs text-[#3c4043] my-auto">
                <div><span className="text-[#5f6368]">NAME:</span> JANE DOE</div>
                <div><span className="text-[#5f6368]">DOC NO:</span> 9021-338210</div>
                <div><span className="text-[#5f6368]">NATIONALITY:</span> IND</div>
              </div>
              <div className="text-[10px] text-[#5f6368] pt-2 border-t border-[#f1f3f4]">
                TRUST-ID DETERMINISTIC NEURAL INSPECTION
              </div>
            </div>
          )}

          {/* Anomaly Reticle Overlays */}
          {showOverlays && regions.map((box, idx) => {
            const isSelected = selectedBoxId === box.id || selectedBoxId === String(idx);

            // Compute normalized coords
            const left = `${box.x_min ?? (box.x ?? 15)}%`;
            const top = `${box.y_min ?? (box.y ?? 20)}%`;
            const width = `${(box.x_max && box.x_min) ? (box.x_max - box.x_min) : (box.width ?? 25)}%`;
            const height = `${(box.y_max && box.y_min) ? (box.y_max - box.y_min) : (box.height ?? 20)}%`;

            return (
              <div
                key={box.id || idx}
                onClick={() => onSelectBox && onSelectBox(box.id || String(idx))}
                style={{ left, top, width, height }}
                className={`absolute cursor-pointer transition-all rounded ${
                  isSelected
                    ? 'border-2 border-[#d93025] bg-[#d93025]/20 ring-4 ring-[#fad2cf] z-30'
                    : 'border-2 border-dashed border-[#e37400] bg-[#fef7e0]/30 hover:border-[#d93025] z-20'
                }`}
              >
                <span className="absolute -top-5 left-0 px-1.5 py-0.2 rounded bg-[#d93025] text-white text-[9px] font-semibold whitespace-nowrap shadow-xs">
                  {box.label || box.reason || 'Flagged Region'}
                </span>
              </div>
            );
          })}
        </div>

        {/* Floating Zoom & Layer Controls */}
        <div className="absolute bottom-3 right-3 flex items-center space-x-1.5 bg-white/95 backdrop-blur-xs border border-[#dadce0] rounded-full p-1 shadow-sm">
          <button
            type="button"
            onClick={() => setShowOverlays(!showOverlays)}
            title={showOverlays ? 'Hide Anomaly Overlays' : 'Show Anomaly Overlays'}
            className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] transition-colors"
          >
            {showOverlays ? <Eye className="w-4 h-4 text-[#1a73e8]" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <div className="w-px h-4 bg-[#dadce0]" />
          <button
            type="button"
            onClick={handleZoomOut}
            title="Zoom Out"
            className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] transition-colors"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-[11px] font-medium text-[#3c4043] px-1">
            {Math.round(zoomLevel * 100)}%
          </span>
          <button
            type="button"
            onClick={handleZoomIn}
            title="Zoom In"
            className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] transition-colors"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            title="Reset Zoom"
            className="p-1.5 rounded-full hover:bg-[#f1f3f4] text-[#5f6368] transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
