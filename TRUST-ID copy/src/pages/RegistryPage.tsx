import React, { useState, useEffect } from 'react';
import { 
  Database, Plus, Search, RefreshCw, CheckCircle2, AlertTriangle, 
  Archive, Edit3, Eye, Trash2, X, ShieldAlert, AlertOctagon
} from 'lucide-react';
import { 
  getRegistryRecords, 
  createRegistryRecord, 
  updateRegistryRecord, 
  updateRegistryStatus, 
  deleteRegistryRecord,
  checkDuplicateDocument, 
  getRegistryStats 
} from '../services/api';

interface RegistryRecord {
  id: number | string;
  document_type: string;
  document_number: string;
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  nationality?: string;
  address?: string;
  issue_date?: string;
  expiry_date?: string;
  issuing_authority?: string;
  status: string;
  is_watchlist?: boolean;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

const DOC_TYPES = [
  { value: 'ALL', label: 'All Document Types' },
  { value: 'NATIONAL_ID', label: 'National ID / Aadhaar' },
  { value: 'DRIVING_LICENSE', label: 'Driving Licence' },
  { value: 'PASSPORT', label: 'Biometric Passport' },
  { value: 'TRAVEL_PERMIT', label: 'Transit / Travel Permit' },
];

const STATUS_TYPES = [
  { value: 'ALL', label: 'All Statuses' },
  { value: 'ACTIVE', label: 'Active / Valid' },
  { value: 'SUSPENDED', label: 'Suspended' },
  { value: 'REVOKED', label: 'Revoked' },
  { value: 'ARCHIVED', label: 'Archived' },
];

export const RegistryPage: React.FC = () => {
  const [records, setRecords] = useState<RegistryRecord[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Create / Edit Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedRecordId, setSelectedRecordId] = useState<number | string | null>(null);

  // Delete Confirmation Modal State
  const [recordToDelete, setRecordToDelete] = useState<RegistryRecord | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    document_type: 'DRIVING_LICENSE',
    document_number: '',
    full_name: '',
    date_of_birth: '',
    gender: 'MALE',
    nationality: 'Indian',
    issue_date: '',
    expiry_date: '',
    issuing_authority: 'Government of Tamil Nadu',
    address: '',
    status: 'ACTIVE',
    is_watchlist: false,
    notes: 'Authoritative sovereign record',
  });

  // Duplicate Check Feedback
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null);
  const [isCheckingDup, setIsCheckingDup] = useState(false);

  // Detail Dossier
  const [viewRecord, setViewRecord] = useState<RegistryRecord | null>(null);

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const fetchRecords = async () => {
    setLoading(true);
    setError(null);
    try {
      const typeParam = typeFilter !== 'ALL' ? typeFilter : undefined;
      const res = await getRegistryRecords({
        query: searchQuery || undefined,
        document_type: typeParam,
      });

      const list: RegistryRecord[] = Array.isArray(res) ? res : (res?.records || []);
      
      // Apply status filter on client side if needed
      const filtered = statusFilter !== 'ALL'
        ? list.filter((r) => r.status === statusFilter)
        : list;

      setRecords(filtered);

      const statsData = await getRegistryStats();
      setStats(statsData);
    } catch (err: any) {
      console.error('Failed to fetch registry data:', err);
      setError(err.message || 'Failed to load master registry records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [typeFilter, statusFilter]);

  // Real-time duplicate check
  useEffect(() => {
    if (isEditing || !formData.document_number.trim() || formData.document_number.trim().length < 4) {
      setDuplicateWarning(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsCheckingDup(true);
      try {
        const res = await checkDuplicateDocument(
          formData.document_number.trim(),
          formData.document_type
        );
        if (res.is_duplicate && res.existing_record) {
          setDuplicateWarning(
            `Duplicate Warning: A record for document number "${formData.document_number}" already exists in Master Registry (Holder: ${res.existing_record.full_name}, Type: ${res.existing_record.document_type}). Accidental duplicate registration is blocked.`
          );
        } else {
          setDuplicateWarning(null);
        }
      } catch (err) {
        console.warn('Duplicate check failed:', err);
      } finally {
        setIsCheckingDup(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [formData.document_number, formData.document_type, isEditing]);

  const handleOpenCreateModal = () => {
    setIsEditing(false);
    setSelectedRecordId(null);
    setDuplicateWarning(null);
    setFormData({
      document_type: 'DRIVING_LICENSE',
      document_number: '',
      full_name: '',
      date_of_birth: '',
      gender: '',
      nationality: '',
      issue_date: '',
      expiry_date: '',
      issuing_authority: 'Government of Tamil Nadu',
      address: '',
      status: 'ACTIVE',
      is_watchlist: false,
      notes: 'Authoritative sovereign record',
    });
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (rec: RegistryRecord) => {
    setIsEditing(true);
    setSelectedRecordId(rec.id);
    setDuplicateWarning(null);
    setFormData({
      document_type: rec.document_type,
      document_number: rec.document_number,
      full_name: rec.full_name,
      date_of_birth: rec.date_of_birth || '',
      gender: rec.gender || '',
      nationality: rec.nationality || '',
      issue_date: rec.issue_date || '',
      expiry_date: rec.expiry_date || '',
      issuing_authority: rec.issuing_authority || '',
      address: rec.address || '',
      status: rec.status,
      is_watchlist: !!rec.is_watchlist,
      notes: rec.notes || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.document_number.trim() || !formData.full_name.trim()) {
      showNotification('error', 'Document Number and Holder Full Name are required.');
      return;
    }

    if (!isEditing && duplicateWarning) {
      showNotification('error', 'Cannot register duplicate document. Please edit existing record.');
      return;
    }

    try {
      const payload: any = {
        document_type: formData.document_type,
        document_number: formData.document_number.trim(),
        full_name: formData.full_name.trim(),
        date_of_birth: formData.date_of_birth.trim() || null,
        gender: formData.gender.trim() || null,
        nationality: formData.nationality.trim() || null,
        issue_date: formData.issue_date.trim() || null,
        expiry_date: formData.expiry_date.trim() || null,
        issuing_authority: formData.issuing_authority.trim() || null,
        address: formData.address.trim() || null,
        status: formData.status,
        is_watchlist: formData.is_watchlist,
        notes: formData.notes.trim() || null,
      };

      if (isEditing && selectedRecordId) {
        await updateRegistryRecord(selectedRecordId, payload);
        showNotification('success', `Record ${formData.document_number} updated in Master Registry.`);
      } else {
        await createRegistryRecord(payload);
        showNotification('success', `Document ${formData.document_number} successfully registered in Master Registry.`);
      }
      setIsModalOpen(false);
      fetchRecords();
    } catch (err: any) {
      showNotification('error', err.message || 'Operation failed on Master Registry.');
    }
  };

  const handleStatusToggle = async (rec: RegistryRecord, newStatus: string) => {
    try {
      await updateRegistryStatus(rec.id, newStatus, `Manual admin status change to ${newStatus}`);
      showNotification('success', `Record status updated to ${newStatus}.`);
      fetchRecords();
    } catch (err: any) {
      showNotification('error', err.message || 'Failed to update record status.');
    }
  };

  const handleConfirmDelete = async () => {
    if (!recordToDelete) return;
    setIsDeleting(true);
    try {
      await deleteRegistryRecord(recordToDelete.id);
      showNotification('success', `Record ${recordToDelete.document_number} (${recordToDelete.full_name}) was permanently deleted.`);
      setRecordToDelete(null);
      if (viewRecord && viewRecord.id === recordToDelete.id) {
        setViewRecord(null);
      }
      await fetchRecords();
    } catch (err: any) {
      console.error('Delete error:', err);
      showNotification('error', err.message || 'Failed to delete record from Master Registry.');
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDocType = (type: string) => {
    switch (type) {
      case 'NATIONAL_ID':
        return 'National ID';
      case 'DRIVING_LICENSE':
      case 'DRIVING_LICENCE':
        return 'Driving Licence';
      case 'PASSPORT':
        return 'Passport';
      case 'TRAVEL_PERMIT':
        return 'Travel Permit';
      default:
        return type.replace(/_/g, ' ');
    }
  };

  const getDocTypeBadge = (type: string) => {
    switch (type) {
      case 'NATIONAL_ID':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'DRIVING_LICENSE':
      case 'DRIVING_LICENCE':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'PASSPORT':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'TRAVEL_PERMIT':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'SUSPENDED':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'REVOKED':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'ARCHIVED':
        return 'bg-gray-100 text-gray-600 border-gray-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Notification Toast */}
      {notification && (
        <div
          className={`fixed top-4 right-4 z-50 flex items-center space-x-2 px-4 py-3 rounded-lg shadow-lg border text-sm font-medium transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {notification.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
          )}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Header */}
      <div className="bg-white rounded-xl border border-[#e0e2e6] p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-[#e8f0fe] rounded-lg text-[#1a73e8]">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[#202124]">Master Identity Registry</h1>
            <p className="text-xs text-[#5f6368] mt-0.5">
              Authoritative sovereign registry in PostgreSQL. Reference records for document cross-checking.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => fetchRecords()}
            className="flex items-center space-x-1.5 px-3 py-2 text-xs font-medium text-[#5f6368] bg-[#f8fafd] hover:bg-[#f1f3f4] border border-[#dadce0] rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleOpenCreateModal}
            className="flex items-center space-x-2 px-4 py-2 text-xs font-medium text-white bg-[#1a73e8] hover:bg-[#1557b0] rounded-lg shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Register Document</span>
          </button>
        </div>
      </div>

      {/* Stats Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-[#e0e2e6] shadow-xs">
          <div className="text-xs font-medium text-[#5f6368]">Total Reference Records</div>
          <div className="text-2xl font-bold text-[#202124] mt-1">{stats?.total_records ?? records.length}</div>
          <div className="text-[11px] text-[#1a73e8] font-medium mt-1">Authoritative identities</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-[#e0e2e6] shadow-xs">
          <div className="text-xs font-medium text-[#5f6368]">Active / Verified</div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">{stats?.active_records ?? records.filter(r => r.status === 'ACTIVE').length}</div>
          <div className="text-[11px] text-emerald-700 font-medium mt-1">Eligible for 1:1 match</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-[#e0e2e6] shadow-xs">
          <div className="text-xs font-medium text-[#5f6368]">Archived / Suspended</div>
          <div className="text-2xl font-bold text-amber-600 mt-1">
            {(stats?.archived_records ?? 0) + (stats?.lost_or_stolen ?? 0)}
          </div>
          <div className="text-[11px] text-amber-700 font-medium mt-1">Flagged during lookup</div>
        </div>
        <div className="bg-white p-4 rounded-xl border border-[#e0e2e6] shadow-xs">
          <div className="text-xs font-medium text-[#5f6368]">Supported Document Types</div>
          <div className="text-2xl font-bold text-[#202124] mt-1">4</div>
          <div className="text-[11px] text-[#5f6368] font-medium mt-1">DL, Aadhaar, Passport, Permit</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-[#e0e2e6] p-4 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#5f6368] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Document Number or Holder Name (e.g. TN01 20240001308, NAISON PRAKASH)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchRecords()}
            className="w-full pl-9 pr-4 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8] focus:bg-white transition-all"
          />
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] font-medium focus:outline-none focus:border-[#1a73e8]"
          >
            {DOC_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] font-medium focus:outline-none focus:border-[#1a73e8]"
          >
            {STATUS_TYPES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          <button
            onClick={() => fetchRecords()}
            className="px-4 py-2 text-xs font-semibold text-[#1a73e8] bg-[#e8f0fe] hover:bg-[#d2e3fc] rounded-lg transition-colors whitespace-nowrap"
          >
            Apply Filter
          </button>
        </div>
      </div>

      {/* Registry Table */}
      <div className="bg-white rounded-xl border border-[#e0e2e6] shadow-xs overflow-hidden">
        {loading ? (
          <div className="py-16 text-center">
            <RefreshCw className="w-8 h-8 text-[#1a73e8] animate-spin mx-auto mb-3" />
            <p className="text-xs text-[#5f6368] font-medium">Querying Master Identity Registry in PostgreSQL...</p>
          </div>
        ) : error ? (
          <div className="py-12 px-6 text-center">
            <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm font-semibold text-red-600 mb-1">Failed to load registry</p>
            <p className="text-xs text-[#5f6368] mb-4">{error}</p>
            <button
              onClick={() => fetchRecords()}
              className="px-3 py-1.5 bg-[#f1f3f4] text-xs font-medium text-[#202124] rounded-lg hover:bg-[#dadce0]"
            >
              Retry
            </button>
          </div>
        ) : records.length === 0 ? (
          <div className="py-16 text-center">
            <Database className="w-10 h-10 text-[#bdc1c6] mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-[#202124]">No Registry Records Found</h3>
            <p className="text-xs text-[#5f6368] max-w-sm mx-auto mt-1 mb-4">
              No authoritative identity records match your search or filter criteria.
            </p>
            <button
              onClick={handleOpenCreateModal}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#1a73e8] rounded-lg hover:bg-[#1557b0]"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Register New Document</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#e0e2e6] bg-[#f8fafd] text-[11px] font-semibold text-[#5f6368] uppercase tracking-wider">
                  <th className="py-3 px-4">Document Details</th>
                  <th className="py-3 px-4">Holder Name & Demographics</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Issuing Authority / Dates</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#f1f3f4] text-xs">
                {records.map((rec) => (
                  <tr key={String(rec.id)} className="hover:bg-[#f8fafd] transition-colors">
                    {/* Document Number & ID */}
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono font-bold text-[#202124] text-xs">
                          {rec.document_number}
                        </span>
                        {rec.is_watchlist && (
                          <span className="px-1.5 py-0.5 text-[10px] font-bold bg-red-100 text-red-700 rounded border border-red-200">
                            WATCHLIST
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-[#5f6368] mt-0.5">
                        ID: {String(rec.id).substring(0, 8)}
                      </div>
                    </td>

                    {/* Holder Info */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#202124]">{rec.full_name}</div>
                      <div className="text-[11px] text-[#5f6368] flex items-center space-x-2 mt-0.5">
                        <span>DOB: {rec.date_of_birth || 'N/A'}</span>
                        {rec.gender && <span>• {rec.gender}</span>}
                        {rec.nationality && <span>• {rec.nationality}</span>}
                      </div>
                    </td>

                    {/* Type Badge */}
                    <td className="py-3 px-4">
                      <span className={`inline-block px-2.5 py-1 rounded-full text-[11px] font-semibold border ${getDocTypeBadge(rec.document_type)}`}>
                        {formatDocType(rec.document_type)}
                      </span>
                    </td>

                    {/* Issuing Authority & Validity */}
                    <td className="py-3 px-4">
                      <div className="text-[#202124] font-medium text-[11px]">
                        {rec.issuing_authority || 'Standard Authority'}
                      </div>
                      <div className="text-[11px] text-[#5f6368] mt-0.5">
                        {rec.issue_date && <span>Issued: {rec.issue_date}</span>}
                        {rec.issue_date && rec.expiry_date && <span> • </span>}
                        {rec.expiry_date ? (
                          <span>Valid Till: {rec.expiry_date}</span>
                        ) : (
                          <span className="text-gray-400">Validity: Lifetime / NT</span>
                        )}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4 text-center">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${getStatusBadge(rec.status)}`}>
                        {rec.status}
                      </span>
                    </td>

                    {/* Actions: View Record, Edit Record, Archive Record, Delete Record */}
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end space-x-1">
                        {/* 1. View Record */}
                        <button
                          onClick={() => setViewRecord(rec)}
                          title="View Record"
                          className="p-1.5 text-[#5f6368] hover:text-[#1a73e8] hover:bg-[#e8f0fe] rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {/* 2. Edit Record */}
                        <button
                          onClick={() => handleOpenEditModal(rec)}
                          title="Edit Record"
                          className="p-1.5 text-[#5f6368] hover:text-[#1a73e8] hover:bg-[#e8f0fe] rounded-lg transition-colors"
                        >
                          <Edit3 className="w-4 h-4" />
                        </button>

                        {/* 3. Archive Record */}
                        {rec.status === 'ACTIVE' ? (
                          <button
                            onClick={() => handleStatusToggle(rec, 'ARCHIVED')}
                            title="Archive Record"
                            className="p-1.5 text-[#5f6368] hover:text-amber-700 hover:bg-amber-50 rounded-lg transition-colors"
                          >
                            <Archive className="w-4 h-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleStatusToggle(rec, 'ACTIVE')}
                            title="Activate Record"
                            className="p-1.5 text-[#5f6368] hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </button>
                        )}

                        {/* 4. Delete Record */}
                        <button
                          onClick={() => setRecordToDelete(rec)}
                          title="Delete Record"
                          className="p-1.5 text-[#5f6368] hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {recordToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-[#dadce0] shadow-2xl max-w-md w-full overflow-hidden">
            <div className="p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2.5 bg-red-50 text-red-600 rounded-xl">
                  <AlertOctagon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#202124]">
                    Delete Registry Record
                  </h3>
                  <p className="text-xs text-[#5f6368]">
                    Authoritative Sovereign Master Identity Registry
                  </p>
                </div>
              </div>

              <div className="p-3.5 bg-red-50/50 border border-red-100 rounded-xl space-y-2 mb-4 text-xs">
                <div className="text-sm font-semibold text-red-900">
                  Delete this registry record permanently?
                </div>
                <div className="text-[#3c4043] space-y-1 pt-1 text-[11px]">
                  <div>
                    <span className="font-semibold text-[#202124]">Document Number:</span>{' '}
                    <span className="font-mono font-bold text-[#202124]">{recordToDelete.document_number}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-[#202124]">Holder Name:</span>{' '}
                    <span>{recordToDelete.full_name}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-[#202124]">Document Type:</span>{' '}
                    <span>{formatDocType(recordToDelete.document_type)}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-[#202124]">Status:</span>{' '}
                    <span className={`inline-block px-1.5 py-0.2 rounded font-semibold text-[10px] ${getStatusBadge(recordToDelete.status)}`}>
                      {recordToDelete.status}
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-xs text-[#5f6368] leading-relaxed mb-6">
                This will permanently delete this identity record from the Master Identity Registry in PostgreSQL. 
                Future verifications of this document will return <strong className="text-[#202124]">UNREGISTERED / NOT FOUND</strong> unless it is registered again.
              </p>

              <div className="flex items-center justify-end space-x-3">
                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={() => setRecordToDelete(null)}
                  className="px-4 py-2 text-xs font-medium text-[#5f6368] hover:bg-[#f1f3f4] rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={isDeleting}
                  onClick={handleConfirmDelete}
                  className="flex items-center space-x-1.5 px-4 py-2 text-xs font-semibold text-white bg-[#d93025] hover:bg-[#b3261e] rounded-lg shadow-xs transition-colors"
                >
                  {isDeleting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>Delete Record</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Registration & Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl border border-[#dadce0] shadow-2xl max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden my-8">
            <div className="px-6 py-4 border-b border-[#e0e2e6] flex items-center justify-between bg-[#f8fafd]">
              <div>
                <h3 className="text-base font-bold text-[#202124]">
                  {isEditing ? 'Edit Sovereign Registry Record' : 'Register Document in Master Identity Registry'}
                </h3>
                <p className="text-xs text-[#5f6368] mt-0.5">
                  {isEditing
                    ? 'Update authoritative attributes. Screenings match against these verified fields.'
                    : 'Add reference identity for sovereign 1:1 cross-referencing.'}
                </p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 text-[#5f6368] hover:text-[#202124] hover:bg-[#e0e2e6] rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitForm} className="p-6 space-y-4 overflow-y-auto flex-1">
              {/* Duplicate Warning */}
              {duplicateWarning && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 flex items-start space-x-2">
                  <ShieldAlert className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Duplicate Document Detected!</span>
                    <p className="mt-0.5">{duplicateWarning}</p>
                  </div>
                </div>
              )}

              {/* Document Type Selection */}
              <div>
                <label className="block text-xs font-semibold text-[#202124] mb-1">
                  Document Type *
                </label>
                <select
                  disabled={isEditing}
                  value={formData.document_type}
                  onChange={(e) => {
                    const newType = e.target.value;
                    let defAuth = 'Standard Authority';
                    if (newType === 'NATIONAL_ID') defAuth = 'Government of India / भारत सरकार';
                    if (newType === 'DRIVING_LICENSE') defAuth = 'Government of Tamil Nadu';
                    if (newType === 'PASSPORT') defAuth = 'Passport Seva / Sovereign Issuance';
                    if (newType === 'TRAVEL_PERMIT') defAuth = 'Federal Immigration Authority';

                    setFormData({
                      ...formData,
                      document_type: newType,
                      issuing_authority: defAuth,
                    });
                  }}
                  className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs font-medium text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                >
                  <option value="NATIONAL_ID">National ID / Aadhaar</option>
                  <option value="DRIVING_LICENSE">Indian Union Driving Licence</option>
                  <option value="PASSPORT">Biometric Passport</option>
                  <option value="TRAVEL_PERMIT">Transit / Travel Permit</option>
                </select>
                <p className="text-[11px] text-[#5f6368] mt-1">
                  {formData.document_type === 'DRIVING_LICENSE' && 'Note: Driving Licences do not require Nationality or strict Expiry Date.'}
                  {formData.document_type === 'NATIONAL_ID' && 'Note: National ID does not require an Expiry Date (Lifetime).'}
                </p>
              </div>

              {/* Document Number & Holder Name */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Document Number *
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      placeholder={formData.document_type === 'DRIVING_LICENSE' ? 'TN01 20240001308' : '5826 5071 6351'}
                      value={formData.document_number}
                      onChange={(e) => setFormData({ ...formData, document_number: e.target.value })}
                      className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs font-mono font-medium text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                    />
                    {isCheckingDup && (
                      <RefreshCw className="w-3.5 h-3.5 text-[#1a73e8] animate-spin absolute right-3 top-1/2 -translate-y-1/2" />
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Holder Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="NAISON PRAKASH"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs font-medium text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  />
                </div>
              </div>

              {/* Date of Birth & Gender */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Date of Birth * (YYYY-MM-DD or DD-MM-YYYY)
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="2001-08-25"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Gender {formData.document_type === 'DRIVING_LICENSE' ? '(Optional)' : ''}
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  >
                    <option value="">Not Specified / Optional</option>
                    <option value="MALE">Male</option>
                    <option value="FEMALE">Female</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
              </div>

              {/* Nationality & Issuing Authority */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Nationality {formData.document_type === 'DRIVING_LICENSE' ? '(N/A for DL)' : '*'}
                  </label>
                  <input
                    type="text"
                    disabled={formData.document_type === 'DRIVING_LICENSE'}
                    placeholder={formData.document_type === 'DRIVING_LICENSE' ? 'Not Applicable' : 'Indian'}
                    value={formData.nationality}
                    onChange={(e) => setFormData({ ...formData, nationality: e.target.value })}
                    className={`w-full px-3 py-2 border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8] ${
                      formData.document_type === 'DRIVING_LICENSE' ? 'bg-[#f1f3f4] cursor-not-allowed text-gray-400' : 'bg-[#f8fafd]'
                    }`}
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Issuing Authority
                  </label>
                  <input
                    type="text"
                    placeholder="Government of Tamil Nadu"
                    value={formData.issuing_authority}
                    onChange={(e) => setFormData({ ...formData, issuing_authority: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  />
                </div>
              </div>

              {/* Issue Date & Expiry Date */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Issue Date (Optional/Required per type)
                  </label>
                  <input
                    type="text"
                    placeholder="2024-03-01"
                    value={formData.issue_date}
                    onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Expiry Date {formData.document_type === 'NATIONAL_ID' ? '(N/A / Lifetime)' : ''}
                  </label>
                  <input
                    type="text"
                    placeholder={formData.document_type === 'NATIONAL_ID' ? 'Lifetime (Not Applicable)' : '2041-08-24'}
                    value={formData.expiry_date}
                    onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  />
                </div>
              </div>

              {/* Address (Optional) */}
              <div>
                <label className="block text-xs font-semibold text-[#202124] mb-1">
                  Registered Address (Optional)
                </label>
                <textarea
                  rows={2}
                  placeholder="Street, City, State, PIN"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                />
              </div>

              {/* Status and Watchlist Flags */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-[#202124] mb-1">
                    Registry Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs font-medium text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                  >
                    <option value="ACTIVE">ACTIVE (Valid Sovereign Identity)</option>
                    <option value="SUSPENDED">SUSPENDED (Pending Investigation)</option>
                    <option value="REVOKED">REVOKED (Invalidated)</option>
                    <option value="ARCHIVED">ARCHIVED (Historical / Inactive)</option>
                  </select>
                </div>

                <div className="flex items-center space-x-3 pt-4">
                  <label className="flex items-center space-x-2 text-xs font-semibold text-[#202124] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_watchlist}
                      onChange={(e) => setFormData({ ...formData, is_watchlist: e.target.checked })}
                      className="w-4 h-4 text-red-600 rounded border-[#dadce0] focus:ring-red-500"
                    />
                    <span className="text-red-700">Flag on Watchlist / Alert</span>
                  </label>
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-semibold text-[#202124] mb-1">
                  Administrative Reference Notes
                </label>
                <input
                  type="text"
                  placeholder="Authority issuance verification notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 bg-[#f8fafd] border border-[#dadce0] rounded-lg text-xs text-[#202124] focus:outline-none focus:border-[#1a73e8]"
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#e0e2e6]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-[#5f6368] hover:bg-[#f1f3f4] rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!isEditing && !!duplicateWarning}
                  className={`px-5 py-2 text-xs font-semibold text-white rounded-lg shadow-xs transition-colors ${
                    !isEditing && !!duplicateWarning
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-[#1a73e8] hover:bg-[#1557b0]'
                  }`}
                >
                  {isEditing ? 'Save Changes' : 'Register Identity'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Details Dossier Modal */}
      {viewRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-[#dadce0] shadow-2xl max-w-lg w-full overflow-hidden">
            <div className="px-6 py-4 border-b border-[#e0e2e6] flex items-center justify-between bg-[#f8fafd]">
              <div className="flex items-center space-x-2">
                <Database className="w-5 h-5 text-[#1a73e8]" />
                <h3 className="text-sm font-bold text-[#202124]">
                  Master Identity Dossier
                </h3>
              </div>
              <button
                onClick={() => setViewRecord(null)}
                className="p-1 text-[#5f6368] hover:text-[#202124] rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="flex items-center justify-between p-3 bg-[#f8fafd] rounded-xl border border-[#e0e2e6]">
                <div>
                  <div className="text-[10px] text-[#5f6368] uppercase font-semibold">Document Number</div>
                  <div className="text-base font-mono font-bold text-[#202124] mt-0.5">
                    {viewRecord.document_number}
                  </div>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getStatusBadge(viewRecord.status)}`}>
                  {viewRecord.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Document Type</span>
                  <span className="font-semibold text-[#202124]">{formatDocType(viewRecord.document_type)}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Holder Full Name</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.full_name}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Date of Birth</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.date_of_birth || 'N/A'}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Gender</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.gender || 'N/A'}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Nationality</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.nationality || 'N/A'}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Issuing Authority</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.issuing_authority || 'N/A'}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Issue Date</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.issue_date || 'N/A'}</span>
                </div>
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Expiry Date</span>
                  <span className="font-semibold text-[#202124]">{viewRecord.expiry_date || 'Lifetime / N/A'}</span>
                </div>
              </div>

              {viewRecord.address && (
                <div className="p-2.5 rounded-lg border border-[#e0e2e6]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Registered Address</span>
                  <span className="text-[#202124]">{viewRecord.address}</span>
                </div>
              )}

              {viewRecord.notes && (
                <div className="p-2.5 rounded-lg border border-[#e0e2e6] bg-[#f8fafd]">
                  <span className="text-[10px] text-[#5f6368] uppercase block font-medium">Administrative Notes</span>
                  <span className="text-[#5f6368]">{viewRecord.notes}</span>
                </div>
              )}

              <div className="pt-3 border-t border-[#e0e2e6] flex items-center justify-between">
                <button
                  onClick={() => {
                    setRecordToDelete(viewRecord);
                  }}
                  className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Record</span>
                </button>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      const rec = viewRecord;
                      setViewRecord(null);
                      handleOpenEditModal(rec);
                    }}
                    className="px-3 py-1.5 bg-[#f1f3f4] text-[#202124] rounded-lg text-xs font-medium hover:bg-[#dadce0]"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => setViewRecord(null)}
                    className="px-4 py-1.5 bg-[#1a73e8] text-white rounded-lg text-xs font-semibold hover:bg-[#1557b0]"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
