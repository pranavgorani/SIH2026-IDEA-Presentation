/**
 * TRUST-ID Forensic Analysis Excel & CSV Exporter
 * Generates formatted Excel spreadsheets (.xls / .csv) containing
 * case metadata, traveler particulars, and the complete 100-check inspection matrix.
 */

export interface CheckItem {
  check_id: string;
  category: string;
  name: string;
  status: "PASS" | "FAIL" | "WARNING" | "UNAVAILABLE" | "NOT_CHECKED" | "NOT_APPLICABLE" | string;
  severity: string;
  message?: string;
  evidence?: string;
}

export interface ExportData {
  caseNumber: string;
  screeningTime: string;
  checkpoint: string;
  officerId: string;
  decision: string;
  riskScore: number;
  documentType: string;
  documentNumber: string;
  fullName: string;
  nationality: string;
  dob: string;
  gender: string;
  expiryDate: string;
  issuingCountry: string;
  documentSha256: string;
  tamperingAssessment: string;
  biometricMatch: string;
  watchlistStatus: string;
  blockchainHash: string;
  checks: CheckItem[];
}

export function exportAnalysisToExcel(data: ExportData) {
  // Generate multi-worksheet Excel XML format
  const xmlContent = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Styles>
  <Style ss:ID="Default" ss:Name="Normal">
   <Alignment ss:Vertical="Center"/>
   <Borders/>
   <Font ss:FontName="Segoe UI" ss:Size="10" ss:Color="#000000"/>
  </Style>
  <Style ss:ID="Title">
   <Font ss:FontName="Segoe UI" ss:Size="14" ss:Bold="1" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#0F172A" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
  </Style>
  <Style ss:ID="Header">
   <Font ss:FontName="Segoe UI" ss:Size="11" ss:Bold="1" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#1E293B" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
  </Style>
  <Style ss:ID="SubHeader">
   <Font ss:FontName="Segoe UI" ss:Size="10" ss:Bold="1" ss:Color="#1E293B"/>
   <Interior ss:Color="#E2E8F0" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="Pass">
   <Font ss:FontName="Segoe UI" ss:Size="10" ss:Bold="1" ss:Color="#16A34A"/>
   <Interior ss:Color="#DCFCE7" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center"/>
  </Style>
  <Style ss:ID="Fail">
   <Font ss:FontName="Segoe UI" ss:Size="10" ss:Bold="1" ss:Color="#DC2626"/>
   <Interior ss:Color="#FEE2E2" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center"/>
  </Style>
  <Style ss:ID="Warning">
   <Font ss:FontName="Segoe UI" ss:Size="10" ss:Bold="1" ss:Color="#D97706"/>
   <Interior ss:Color="#FEF3C7" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center"/>
  </Style>
  <Style ss:ID="HighRisk">
   <Font ss:FontName="Segoe UI" ss:Size="12" ss:Bold="1" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#DC2626" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center"/>
  </Style>
  <Style ss:ID="LowRisk">
   <Font ss:FontName="Segoe UI" ss:Size="12" ss:Bold="1" ss:Color="#FFFFFF"/>
   <Interior ss:Color="#16A34A" ss:Pattern="Solid"/>
   <Alignment ss:Horizontal="Center"/>
  </Style>
 </Styles>

 <!-- WORKSHEET 1: DOSSIER EXECUTIVE SUMMARY -->
 <Worksheet ss:Name="Dossier Executive Summary">
  <Table ss:DefaultColumnWidth="140">
   <Column ss:Width="200"/>
   <Column ss:Width="300"/>
   
   <Row ss:Height="30">
    <Cell ss:MergeAcross="1" ss:StyleID="Title">
     <Data ss:Type="String">MINISTRY OF HOME AFFAIRS (MHA) - BORDER SECURITY DOSSIER</Data>
    </Cell>
   </Row>
   <Row ss:Height="20">
    <Cell ss:MergeAcross="1" ss:StyleID="SubHeader">
     <Data ss:Type="String">LEGAL EVIDENTIARY FORENSIC SCREENING REPORT</Data>
    </Cell>
   </Row>
   <Row><Cell><Data ss:Type="String"/></Cell></Row>

   <!-- SECTION: METADATA -->
   <Row ss:Height="22">
    <Cell ss:MergeAcross="1" ss:StyleID="Header"><Data ss:Type="String">1. INSPECTION METADATA</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Case Number</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.caseNumber)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Checkpoint / Terminal</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.checkpoint)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Screening Timestamp (UTC)</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.screeningTime)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Inspection Officer</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.officerId)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Border Clearance Verdict</Data></Cell>
    <Cell ss:StyleID="${data.riskScore >= 70 ? "HighRisk" : "LowRisk"}">
     <Data ss:Type="String">${escapeXml(data.decision)} (RISK: ${data.riskScore}/100)</Data>
    </Cell>
   </Row>
   <Row><Cell><Data ss:Type="String"/></Cell></Row>

   <!-- SECTION: TRAVELER -->
   <Row ss:Height="22">
    <Cell ss:MergeAcross="1" ss:StyleID="Header"><Data ss:Type="String">2. TRAVELER PARTICULARS</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Holder Full Name</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.fullName)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Document Type</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.documentType)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Document Number</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.documentNumber)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Nationality</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.nationality)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Date of Birth</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.dob)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Gender / Sex</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.gender)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Expiry Date</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.expiryDate)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Issuing Country</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.issuingCountry)}</Data></Cell>
   </Row>
   <Row><Cell><Data ss:Type="String"/></Cell></Row>

   <!-- SECTION: FORENSICS & BLOCKCHAIN -->
   <Row ss:Height="22">
    <Cell ss:MergeAcross="1" ss:StyleID="Header"><Data ss:Type="String">3. FORENSICS &amp; CRYPTOGRAPHIC AUDIT</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Substrate Tampering Assessment</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.tamperingAssessment)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">1:1 Biometric Face Match</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.biometricMatch)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Watchlist Clearance</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.watchlistStatus)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Document SHA-256</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.documentSha256)}</Data></Cell>
   </Row>
   <Row>
    <Cell ss:StyleID="SubHeader"><Data ss:Type="String">Blockchain Audit Block Hash</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(data.blockchainHash)}</Data></Cell>
   </Row>
  </Table>
 </Worksheet>

 <!-- WORKSHEET 2: 100 CHECKS FULL INSPECTION MATRIX -->
 <Worksheet ss:Name="100 Checks Full Matrix">
  <Table ss:DefaultColumnWidth="120">
   <Column ss:Width="80"/>
   <Column ss:Width="160"/>
   <Column ss:Width="260"/>
   <Column ss:Width="90"/>
   <Column ss:Width="90"/>
   <Column ss:Width="380"/>

   <Row ss:Height="25">
    <Cell ss:StyleID="Header"><Data ss:Type="String">Check ID</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Category</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Inspection Test Name</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Verdict Status</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Severity</Data></Cell>
    <Cell ss:StyleID="Header"><Data ss:Type="String">Evidence &amp; Analysis Notes</Data></Cell>
   </Row>
   ${data.checks.map(c => {
     const statusStyle = c.status === "PASS" ? "Pass" : c.status === "FAIL" ? "Fail" : "Warning";
     return `
   <Row>
    <Cell><Data ss:Type="String">${escapeXml(c.check_id)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(c.category)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(c.name)}</Data></Cell>
    <Cell ss:StyleID="${statusStyle}"><Data ss:Type="String">${escapeXml(c.status)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(c.severity)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(c.message || c.evidence || "")}</Data></Cell>
   </Row>`;
   }).join("")}
  </Table>
 </Worksheet>
</Workbook>`;

  // Trigger download with application/vnd.ms-excel
  const blob = new Blob([xmlContent], { type: "application/vnd.ms-excel;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const safeDocNo = (data.documentNumber || "DOC").replace(/[^a-zA-Z0-9]/g, "");
  link.download = `TRUST-ID_Forensic_Analysis_${safeDocNo}_${data.caseNumber || "CASE"}.xls`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportAnalysisToCsv(data: ExportData) {
  const headers = ["Check ID", "Category", "Inspection Test Name", "Status", "Severity", "Evidence / Forensic Notes"];
  const rows = data.checks.map(c => [
    `"${c.check_id}"`,
    `"${c.category}"`,
    `"${(c.name || "").replace(/"/g, '""')}"`,
    `"${c.status}"`,
    `"${c.severity}"`,
    `"${(c.message || c.evidence || "").replace(/"/g, '""')}"`
  ]);

  const summary = [
    `"MINISTRY OF HOME AFFAIRS (MHA) - BORDER SECURITY IMMIGRATION DOSSIER"`,
    `"CASE NUMBER","${data.caseNumber}"`,
    `"CHECKPOINT","${data.checkpoint}"`,
    `"SCREENING TIME","${data.screeningTime}"`,
    `"OFFICER ID","${data.officerId}"`,
    `"VERDICT","${data.decision}"`,
    `"RISK SCORE","${data.riskScore} / 100"`,
    `"DOCUMENT NUMBER","${data.documentNumber}"`,
    `"HOLDER FULL NAME","${data.fullName}"`,
    `"NATIONALITY","${data.nationality}"`,
    `"DATE OF BIRTH","${data.dob}"`,
    `"EXPIRY DATE","${data.expiryDate}"`,
    `"DOCUMENT SHA-256","${data.documentSha256}"`,
    `""`,
    headers.join(",")
  ];

  const fullCsv = "\uFEFF" + summary.concat(rows.map(r => r.join(","))).join("\r\n");
  const blob = new Blob([fullCsv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const safeDocNo = (data.documentNumber || "DOC").replace(/[^a-zA-Z0-9]/g, "");
  link.download = `TRUST-ID_Forensic_Analysis_${safeDocNo}_${data.caseNumber || "CASE"}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function escapeXml(unsafe: string | number | undefined | null): string {
  if (unsafe === undefined || unsafe === null) return "";
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}
