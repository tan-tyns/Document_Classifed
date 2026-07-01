// Archive.jsx
import React, { useState, useEffect } from 'react';
import { saveAs } from 'file-saver';
import JSZip from 'jszip';
import {
  Search, Filter, FileSpreadsheet, Archive as ArchiveIcon,
  Eye, X, FileText, Trash2, Edit3, Save, Tag, MapPin, Hash,
  User, Shield, Users, Clock, CheckCircle, XCircle, AlertTriangle,
  FolderOpen, Download, Calendar, ChevronDown, ChevronUp,
  ZoomIn, ZoomOut, AlertCircle, Send
} from 'lucide-react';

const DOCUMENT_TYPES = ['Báo cáo', 'Công văn', 'Giấy mời', 'Kế hoạch', 'Quyết định', 'Thông báo', 'Tờ trình', 'Khác'];

const truncateWords = (text, maxWords = 20) => {
  if (!text) return 'Chưa có trích yếu';
  const words = text.trim().split(/\s+/);
  if (words.length > maxWords) {
    return words.slice(0, maxWords).join(' ') + '...';
  }
  return text;
};

export default function Archive({ archivedDocs, setArchivedDocs, user, t, showToast }) {
  const [activeTab, setActiveTab] = useState('Tất cả');
  const [searchSoHieu, setSearchSoHieu] = useState('');
  const [searchNoiBanHanh, setSearchNoiBanHanh] = useState('');
  const [searchTrichYeu, setSearchTrichYeu] = useState('');
  const [searchUser, setSearchUser] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
  const [showAdvancedFilter, setShowAdvancedFilter] = useState(false);

  const [viewingDoc, setViewingDoc] = useState(null);
  const [editingDocId, setEditingDocId] = useState(null);
  const [editForm, setEditForm] = useState({
    docType: '', soHieu: '', date: '', trichYeu: '', content: '', noiBanHanh: ''
  });

  const [zoomLevel, setZoomLevel] = useState(1);

  const [deleteRequests, setDeleteRequests] = useState([]);
  const [showDeleteRequests, setShowDeleteRequests] = useState(false);
  const [loadingExport, setLoadingExport] = useState(false);

  // 🔥 State cho modal yêu cầu xóa (dành cho nhân viên)
  const [deleteRequestModal, setDeleteRequestModal] = useState({
    show: false,
    docId: null,
    reason: ''
  });

  const isEmployee = user?.role === 'employee';
  const isManager = user?.role === 'manager';
  const isAdmin = user?.role === 'admin';
  const canApproveDelete = isAdmin || isManager;

  useEffect(() => {
    const fetchArchiveData = async () => {
      if (!user?.id) return;
      try {
        const response = await fetch(`http://localhost:8000/documents?user_id=${user.id}&role=${user.role}`);
        const data = await response.json();
        if (response.ok) setArchivedDocs(data);
      } catch (error) {
        console.error("Lỗi kết nối API kho lưu trữ:", error);
      }
    };
    fetchArchiveData();
  }, [user, setArchivedDocs]);

  useEffect(() => {
    if (!canApproveDelete || !user?.id) return;
    const fetchDeleteRequests = async () => {
      try {
        const response = await fetch(`http://localhost:8000/documents/delete-requests`);
        if (response.ok) {
          const data = await response.json();
          setDeleteRequests(data);
        }
      } catch (error) {
        console.error("Lỗi tải yêu cầu xóa:", error);
      }
    };
    fetchDeleteRequests();
    const interval = setInterval(fetchDeleteRequests, 30000);
    return () => clearInterval(interval);
  }, [canApproveDelete, user]);

  const getCountByType = (type) => {
    if (type === 'Tất cả') return archivedDocs.length;
    return archivedDocs.filter(doc => (doc.docType || '').toLowerCase() === type.toLowerCase()).length;
  };

  const filteredArchive = archivedDocs.filter(doc => {
    const matchesTab = activeTab === 'Tất cả' || (doc.docType || '').toLowerCase() === activeTab.toLowerCase();
    const matchesSoHieu = (doc.soHieu || '').toLowerCase().includes(searchSoHieu.toLowerCase());
    const matchesNoiBanHanh = (doc.noiBanHanh || '').toLowerCase().includes(searchNoiBanHanh.toLowerCase());
    const matchesTrichYeu = (doc.trichYeu || '').toLowerCase().includes(searchTrichYeu.toLowerCase());
    const matchesUser = !searchUser || String(doc.user_id || '').includes(searchUser) ||
      (doc.uploaderName || '').toLowerCase().includes(searchUser.toLowerCase());
    // Lọc theo ngày (nếu có)
    let matchesDate = true;
    if (filterDateFrom && doc.date) {
      const docDate = new Date(doc.date.split('/').reverse().join('-'));
      const from = new Date(filterDateFrom);
      if (docDate < from) matchesDate = false;
    }
    if (filterDateTo && doc.date) {
      const docDate = new Date(doc.date.split('/').reverse().join('-'));
      const to = new Date(filterDateTo);
      if (docDate > to) matchesDate = false;
    }
    return matchesTab && matchesSoHieu && matchesNoiBanHanh && matchesTrichYeu && matchesUser && matchesDate;
  });

  const startEdit = (doc) => {
    setEditingDocId(doc.id);
    setEditForm({
      docType: doc.docType || '',
      soHieu: doc.soHieu || '',
      date: doc.date || '',
      trichYeu: doc.trichYeu || '',
      content: doc.content || '',
      noiBanHanh: doc.noiBanHanh || '',
    });
  };

  const handleSaveUpdate = async (docId) => {
    if (!editForm.content?.trim()) {
      showToast('Nội dung văn bản không được để trống!', 'error');
      return;
    }
    if (!editForm.trichYeu?.trim()) {
      showToast('Trích yếu không được để trống!', 'error');
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/documents/${docId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...editForm, edited_by: user?.id })
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Không thể cập nhật tài liệu.');
      }

      setArchivedDocs(prev => prev.map(d => d.id === docId ? { ...d, ...editForm } : d));
      if (viewingDoc?.id === docId) setViewingDoc(prev => ({ ...prev, ...editForm }));
      setEditingDocId(null);
      showToast('Cập nhật văn bản thành công!', 'success');
    } catch (error) {
      showToast('Lỗi: ' + error.message, 'error');
    }
  };

  const cancelEdit = () => {
    setEditingDocId(null);
    setEditForm({ docType: '', soHieu: '', date: '', trichYeu: '', content: '', noiBanHanh: '' });
  };

  // ============================================================
  // XÓA VĂN BẢN – PHÂN QUYỀN
  // ============================================================
  const handleDeleteDoc = async (docId) => {
    // 👉 NHÂN VIÊN: mở modal yêu cầu xóa
    if (isEmployee) {
      setDeleteRequestModal({ show: true, docId, reason: '' });
      return;
    }

    // 👉 ADMIN / MANAGER: xóa trực tiếp (có confirm)
    if (!window.confirm('Bạn có chắc chắn muốn xóa vĩnh viễn văn bản này?')) return;
    try {
      const response = await fetch(`http://localhost:8000/documents/${docId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Không thể xóa bản ghi trên hệ thống.');
      setArchivedDocs(prev => prev.filter(d => d.id !== docId));
      if (viewingDoc?.id === docId) setViewingDoc(null);
      showToast('Đã xóa văn bản thành công!', 'success');
    } catch (error) {
      showToast('Lỗi: ' + error.message, 'error');
    }
  };

  // Gửi yêu cầu xóa từ modal (dành cho nhân viên)
  const submitDeleteRequest = async () => {
    const { docId, reason } = deleteRequestModal;
    if (!reason.trim()) {
      showToast('Vui lòng nhập lý do xóa.', 'error');
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/documents/${docId}/request-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requested_by: user.id, reason: reason.trim() })
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Không thể gửi yêu cầu.');
      }
      showToast('Đã gửi yêu cầu xóa lên quản lí. Chờ phê duyệt.', 'info');
      setDeleteRequestModal({ show: false, docId: null, reason: '' });
    } catch (error) {
      showToast('Lỗi: ' + error.message, 'error');
    }
  };

  // ============================================================
  // DUYỆT YÊU CẦU XÓA (Manager / Admin)
  // ============================================================
  const handleApproveDelete = async (requestId, docId) => {
    if (!window.confirm('Phê duyệt yêu cầu xóa? Văn bản sẽ bị xóa vĩnh viễn.')) return;
    try {
      const response = await fetch(`http://localhost:8000/documents/delete-requests/${requestId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved_by: user.id })
      });
      if (!response.ok) throw new Error('Phê duyệt thất bại.');
      setArchivedDocs(prev => prev.filter(d => d.id !== docId));
      setDeleteRequests(prev => prev.filter(r => r.id !== requestId));
      showToast('Đã phê duyệt và xóa văn bản thành công!', 'success');
    } catch (error) {
      showToast('Lỗi: ' + error.message, 'error');
    }
  };

  const handleRejectDelete = async (requestId) => {
    try {
      const response = await fetch(`http://localhost:8000/documents/delete-requests/${requestId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rejected_by: user.id })
      });
      if (!response.ok) throw new Error('Từ chối thất bại.');
      setDeleteRequests(prev => prev.filter(r => r.id !== requestId));
      showToast('Đã từ chối yêu cầu xóa.', 'info');
    } catch (error) {
      showToast('Lỗi: ' + error.message, 'error');
    }
  };

  // ============================================================
  // XUẤT DỮ LIỆU
  // ============================================================
  const exportToCSV = () => {
    if (filteredArchive.length === 0) return;
    let csvContent = '\uFEFFTên File,Nơi Ban Hành,Loại Văn Bản,Số Hiệu,Ngày Ban Hành,Trích Yếu,Nội Dung\n';
    filteredArchive.forEach(r => {
      const safeContent = (r.content || '').replace(/"/g, '""');
      const safeTrichYeu = (r.trichYeu || '').replace(/"/g, '""');
      csvContent += `"${r.fileName}","${r.noiBanHanh}","${r.docType}","${r.soHieu}","${r.date}","${safeTrichYeu}","${safeContent}"\n`;
    });
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, 'KhoLuuTru_VanBan.csv');
  };

  const exportImageFolders = async () => {
    const docsWithFiles = filteredArchive.filter(doc => doc.filePath && doc.filePath !== '');
    if (docsWithFiles.length === 0) {
      showToast('Không có tài liệu nào có file đính kèm để xuất.', 'info');
      return;
    }

    setLoadingExport(true);
    showToast('Đang tạo thư mục ảnh, vui lòng chờ...', 'info');

    try {
      const zip = new JSZip();

      const grouped = {};
      docsWithFiles.forEach(doc => {
        const folderName = (doc.docType || 'Khác').replace(/[^a-zA-Z0-9À-ỹ\s]/g, '_').trim();
        if (!grouped[folderName]) grouped[folderName] = [];
        grouped[folderName].push(doc);
      });

      const fetchPromises = [];

      for (const [folderName, docs] of Object.entries(grouped)) {
        const folder = zip.folder(folderName);
        docs.forEach((doc, idx) => {
          const promise = fetch(doc.filePath)
            .then(res => {
              if (!res.ok) throw new Error(`Không tải được: ${doc.filePath}`);
              return res.blob();
            })
            .then(blob => {
              const ext = doc.filePath.split('.').pop().split('?')[0] || 'jpg';
              const safeName = (doc.trichYeu || doc.fileName || `file_${idx + 1}`)
                .replace(/[^a-zA-Z0-9À-ỹ\s]/g, '_')
                .substring(0, 50)
                .trim();
              folder.file(`${safeName}.${ext}`, blob);
            })
            .catch(err => console.warn('Bỏ qua file lỗi:', err.message));
          fetchPromises.push(promise);
        });
      }

      await Promise.all(fetchPromises);

      const content = await zip.generateAsync({ type: 'blob' });
      saveAs(content, 'KhoAnh_PhanLoai_VanBan.zip');
      showToast(`Xuất thành công ${docsWithFiles.length} file trong ${Object.keys(grouped).length} thư mục!`, 'success');
    } catch (error) {
      showToast('Lỗi xuất thư mục: ' + error.message, 'error');
    } finally {
      setLoadingExport(false);
    }
  };

  const pendingCount = deleteRequests.filter(r => r.status === 'pending').length;

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 flex flex-col flex-1 overflow-hidden min-h-0 animate-in fade-in duration-300">
      <div className={`${t.panel} rounded-3xl ${t.border} border p-6 flex-1 flex flex-col shadow-2xl overflow-hidden min-h-0`}>

        {/* BANNER PHÂN QUYỀN */}
        <div className="flex items-center justify-between mb-4 shrink-0 gap-3 flex-wrap">
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border ${t.border} bg-black/5`}>
            {isAdmin && <><Shield size={14} className="text-purple-500" /><span className="text-purple-500">Quản trị viên</span><span className={t.subtext}>— Xem toàn bộ kho, duyệt xóa</span></>}
            {isManager && <><Users size={14} className="text-blue-500" /><span className="text-blue-500">Quản lí</span><span className={t.subtext}>— Xem toàn bộ kho, duyệt xóa</span></>}
            {isEmployee && <><User size={14} className="text-green-500" /><span className="text-green-500">Nhân viên</span><span className={t.subtext}>— Chỉ xem văn bản của bạn, gửi yêu cầu xóa</span></>}
          </div>

          {canApproveDelete && (
            <button
              onClick={() => setShowDeleteRequests(!showDeleteRequests)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all ${
                pendingCount > 0
                  ? 'bg-red-500/10 border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white animate-pulse'
                  : `bg-black/5 ${t.border} ${t.subtext} hover:bg-black/10`
              }`}
            >
              <AlertTriangle size={14} />
              Yêu cầu xóa
              {pendingCount > 0 && (
                <span className="bg-red-500 text-white text-[9px] font-black px-1.5 py-0.5 rounded-full">
                  {pendingCount}
                </span>
              )}
            </button>
          )}
        </div>

        {/* PANEL YÊU CẦU XÓA ĐANG CHỜ DUYỆT */}
        {canApproveDelete && showDeleteRequests && (
          <div className={`mb-4 shrink-0 rounded-2xl border ${t.border} overflow-hidden`}>
            <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-3 flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest text-red-500 flex items-center gap-2">
                <Trash2 size={13} /> Yêu cầu chờ phê duyệt xóa
              </span>
              <button onClick={() => setShowDeleteRequests(false)} className="text-red-400 hover:text-red-600">
                <X size={16} />
              </button>
            </div>
            {deleteRequests.filter(r => r.status === 'pending').length === 0 ? (
              <div className="px-6 py-4 text-xs text-center opacity-50">Không có yêu cầu nào đang chờ xử lí.</div>
            ) : (
              <div className="divide-y divide-white/5 max-h-60 overflow-y-auto">
                {deleteRequests.filter(r => r.status === 'pending').map(req => {
                  const doc = archivedDocs.find(d => d.id === req.doc_id);
                  return (
                    <div key={req.id} className="px-5 py-3 flex items-center gap-4 hover:bg-black/5">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold truncate">{doc?.trichYeu || req.doc_id}</p>
                        <p className={`text-[10px] ${t.subtext} mt-0.5`}>
                          Nhân viên #{req.requested_by} • {new Date(req.created_at).toLocaleString('vi-VN')}
                        </p>
                        {req.reason && <p className={`text-[10px] ${t.subtext} italic mt-0.5`}>"{req.reason}"</p>}
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <button
                          onClick={() => handleRejectDelete(req.id)}
                          className="px-3 py-1.5 rounded-lg text-[10px] font-bold bg-gray-500/10 text-gray-500 border border-gray-500/20 hover:bg-gray-500 hover:text-white transition-colors flex items-center gap-1"
                        >
                          <XCircle size={12} /> Từ chối
                        </button>
                        <button
                          onClick={() => handleApproveDelete(req.id, req.doc_id)}
                          className="px-3 py-1.5 rounded-lg text-[10px] font-bold bg-green-500/10 text-green-500 border border-green-500/20 hover:bg-green-500 hover:text-white transition-colors flex items-center gap-1"
                        >
                          <CheckCircle size={12} /> Phê duyệt
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* BỘ LỌC TÌM KIẾM */}
        <div className="bg-black/5 p-4 rounded-2xl border border-white/5 mb-5 shrink-0">
          <button
            onClick={() => setShowAdvancedFilter(!showAdvancedFilter)}
            className={`text-[10px] font-black uppercase tracking-widest opacity-60 mb-3 flex items-center gap-1 hover:opacity-100 transition-opacity`}
          >
            <Search size={12} /> Bộ lọc tìm kiếm
            {showAdvancedFilter ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>

          <div className={`grid gap-3 ${(isAdmin || isManager) ? 'grid-cols-1 sm:grid-cols-4' : 'grid-cols-1 sm:grid-cols-3'}`}>
            <div className="relative">
              <Hash size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input
                type="text" value={searchSoHieu}
                onChange={e => setSearchSoHieu(e.target.value)}
                placeholder="Số hiệu..."
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-xs font-bold`}
              />
            </div>
            <div className="relative">
              <MapPin size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input
                type="text" value={searchNoiBanHanh}
                onChange={e => setSearchNoiBanHanh(e.target.value)}
                placeholder="Nơi ban hành..."
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-xs font-bold`}
              />
            </div>
            <div className="relative">
              <FileText size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input
                type="text" value={searchTrichYeu}
                onChange={e => setSearchTrichYeu(e.target.value)}
                placeholder="Trích yếu..."
                className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-xs font-bold`}
              />
            </div>
            {(isAdmin || isManager) && (
              <div className="relative">
                <User size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
                <input
                  type="text" value={searchUser}
                  onChange={e => setSearchUser(e.target.value)}
                  placeholder="Tên / ID nhân viên..."
                  className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-xs font-bold`}
                />
              </div>
            )}
          </div>

          {showAdvancedFilter && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3 pt-3 border-t border-white/5">
              <div className="relative">
                <Calendar size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
                <input
                  type="date" value={filterDateFrom}
                  onChange={e => setFilterDateFrom(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-xs font-bold`}
                />
                <span className={`absolute -top-2 left-3 text-[9px] px-1 ${t.panel} ${t.subtext} font-bold`}>Từ ngày</span>
              </div>
              <div className="relative">
                <Calendar size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
                <input
                  type="date" value={filterDateTo}
                  onChange={e => setFilterDateTo(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-xs font-bold`}
                />
                <span className={`absolute -top-2 left-3 text-[9px] px-1 ${t.panel} ${t.subtext} font-bold`}>Đến ngày</span>
              </div>
            </div>
          )}
        </div>

        {/* THANH TAB + NÚT XUẤT FILE */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b pb-3 mb-6 border-white/5 gap-3 shrink-0 overflow-x-auto custom-scrollbar w-full">
          <div className="flex gap-1.5 items-center flex-nowrap">
            {['Tất cả', ...DOCUMENT_TYPES].map(type => {
              const isActive = activeTab === type;
              return (
                <button
                  key={type}
                  onClick={() => setActiveTab(type)}
                  className={`px-3 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 whitespace-nowrap ${
                    isActive
                      ? `${t.button.split(' ')[0]} ${t.shadow} text-inherit scale-105`
                      : `bg-black/5 border ${t.border} ${t.subtext} hover:bg-black/10`
                  }`}
                >
                  {type}
                  <span className={`px-1.5 py-0.5 rounded-md text-[9px] ${isActive ? 'bg-white/20' : 'bg-black/10 opacity-60'}`}>
                    {getCountByType(type)}
                  </span>
                </button>
              );
            })}
          </div>

          <div className="flex gap-2 shrink-0 self-end sm:self-auto">
            {filteredArchive.length > 0 && (
              <>
                <button
                  onClick={exportToCSV}
                  className="px-3 py-2 flex items-center gap-2 rounded-xl text-xs font-bold bg-green-600/20 text-green-500 border border-green-500/30 hover:bg-green-600 hover:text-white transition-all whitespace-nowrap"
                >
                  <FileSpreadsheet size={14} /> CSV ({filteredArchive.length})
                </button>
                <button
                  onClick={exportImageFolders}
                  disabled={loadingExport}
                  className={`px-3 py-2 flex items-center gap-2 rounded-xl text-xs font-bold border transition-all whitespace-nowrap ${
                    loadingExport
                      ? 'opacity-50 cursor-not-allowed bg-black/5 border-white/10'
                      : 'bg-blue-600/20 text-blue-500 border-blue-500/30 hover:bg-blue-600 hover:text-white'
                  }`}
                >
                  <FolderOpen size={14} />
                  {loadingExport ? 'Đang tạo...' : 'Xuất thư mục ảnh'}
                </button>
              </>
            )}
          </div>
        </div>

        {/* LƯỚI DANH SÁCH VĂN BẢN */}
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
          {filteredArchive.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredArchive.map((doc, idx) => (
                <div
                  key={doc.id || idx}
                  className={`flex flex-col bg-black/5 rounded-2xl border ${t.border} p-5 hover:shadow-lg transition-shadow`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${t.button.split(' ')[0]} ${t.shadow}`}>
                      {doc.docType || 'Không xác định'}
                    </div>
                    <span className={`text-[10px] font-bold ${t.subtext}`}>{doc.date}</span>
                  </div>

                  <h3 className="font-bold text-base mb-1" title={doc.trichYeu}>
                    {truncateWords(doc.trichYeu, 20)}
                  </h3>
                  
                  <p className={`text-xs ${t.subtext} mb-1 font-mono truncate`}>
                    Số: {doc.soHieu || 'N/A'} • Nơi BH: {doc.noiBanHanh || 'N/A'}
                  </p>

                  {(isAdmin || isManager) && doc.user_id && (
                    <p className={`text-[10px] ${t.subtext} mb-3 flex items-center gap-1`}>
                      <User size={10} />
                      {doc.uploaderName || `Nhân viên #${doc.user_id}`}
                    </p>
                  )}

                  <div className="mt-auto flex gap-2">
                    <button
                      onClick={() => { setViewingDoc(doc); setEditingDocId(null); setZoomLevel(1); }}
                      className={`flex-1 py-2 rounded-xl text-xs font-bold bg-white/50 border ${t.border} hover:bg-white transition-colors flex justify-center items-center gap-2`}
                    >
                      <Eye size={14} /> Xem
                    </button>

                    <button
                      onClick={() => { setViewingDoc(doc); startEdit(doc); setZoomLevel(1); }}
                      className="py-2 px-3 rounded-xl text-xs font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500 hover:text-white transition-colors"
                      title="Chỉnh sửa"
                    >
                      <Edit3 size={14} />
                    </button>

                    <button
                      onClick={() => handleDeleteDoc(doc.id)}
                      className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors ${
                        isEmployee
                          ? 'bg-orange-500/10 text-orange-500 border-orange-500/20 hover:bg-orange-500 hover:text-white'
                          : 'bg-red-500/10 text-red-500 border-red-500/20 hover:bg-red-500 hover:text-white'
                      }`}
                      title={isEmployee ? 'Gửi yêu cầu xóa' : 'Xóa văn bản'}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center opacity-50 py-12">
              <ArchiveIcon size={64} className="mb-4 animate-pulse" />
              <h3 className="text-base font-black uppercase tracking-widest">Không tìm thấy tài liệu phù hợp</h3>
              <p className="text-xs mt-1">Thử điều chỉnh lại bộ lọc hoặc tab phân loại.</p>
            </div>
          )}
        </div>
      </div>

      {/* ============================================================ */}
      {/* MODAL XEM CHI TIẾT & CHỈNH SỬA (CÓ ZOOM ẢNH) */}
      {/* ============================================================ */}
      {viewingDoc && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 lg:p-6 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
          
          <div className={`${t.panel} w-full max-w-[95vw] lg:max-w-7xl h-[95vh] rounded-3xl shadow-2xl border ${t.border} flex flex-col overflow-hidden relative`}>

            <button
              onClick={() => { setViewingDoc(null); cancelEdit(); }}
              className="absolute top-4 right-4 z-50 bg-black/10 hover:bg-red-500 text-white p-2 rounded-full backdrop-blur-md transition-colors"
            >
              <X size={20} />
            </button>

            <div className={`p-6 border-b ${t.border} bg-black/5 shrink-0`}>
              {editingDocId === viewingDoc.id ? (
                <input
                  type="text"
                  value={editForm.trichYeu}
                  onChange={e => setEditForm({ ...editForm, trichYeu: e.target.value })}
                  className={`w-full max-w-4xl px-3 py-1.5 rounded-xl border ${t.border} ${t.inputBg} font-black uppercase text-lg outline-none`}
                  placeholder="Nhập trích yếu..."
                />
              ) : (
                <h2 className="text-2xl font-black uppercase tracking-tight pr-12 line-clamp-2">
                  {viewingDoc.trichYeu || 'Không có tiêu đề'}
                </h2>
              )}

              <div className="flex flex-wrap gap-3 mt-3 text-xs font-bold font-mono items-center">
                {editingDocId === viewingDoc.id ? (
                  <>
                    <select
                      value={editForm.docType}
                      onChange={e => setEditForm({ ...editForm, docType: e.target.value })}
                      className={`px-2 py-1 rounded border ${t.border} ${t.inputBg}`}
                    >
                      {DOCUMENT_TYPES.map(type => <option key={type} value={type}>{type}</option>)}
                    </select>
                    <span>Số:</span>
                    <input
                      type="text" value={editForm.soHieu}
                      onChange={e => setEditForm({ ...editForm, soHieu: e.target.value })}
                      className={`w-28 px-2 py-1 rounded border ${t.border} ${t.inputBg}`}
                      placeholder="Số hiệu..."
                    />
                    <span>Ngày:</span>
                    <input
                      type="text" value={editForm.date}
                      onChange={e => setEditForm({ ...editForm, date: e.target.value })}
                      className={`w-32 px-2 py-1 rounded border ${t.border} ${t.inputBg}`}
                      placeholder="dd/mm/yyyy"
                    />
                    <span>Nơi BH:</span>
                    <input
                      type="text" value={editForm.noiBanHanh}
                      onChange={e => setEditForm({ ...editForm, noiBanHanh: e.target.value })}
                      className={`w-40 px-2 py-1 rounded border ${t.border} ${t.inputBg}`}
                      placeholder="Nơi ban hành..."
                    />
                  </>
                ) : (
                  <>
                    <span className={t.accent}>Loại: {viewingDoc.docType}</span>
                    <span className="opacity-30">|</span>
                    <span>Số: {viewingDoc.soHieu || 'N/A'}</span>
                    <span className="opacity-30">|</span>
                    <span>Ngày: {viewingDoc.date || 'N/A'}</span>
                    <span className="opacity-30">|</span>
                    <span>Nơi BH: {viewingDoc.noiBanHanh || 'N/A'}</span>
                    {(isAdmin || isManager) && viewingDoc.user_id && (
                      <>
                        <span className="opacity-30">|</span>
                        <span className="flex items-center gap-1"><User size={11} /> {viewingDoc.uploaderName || `#${viewingDoc.user_id}`}</span>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>

            <div className="flex-1 flex flex-col lg:flex-row overflow-hidden bg-black/5 min-h-0">

              {viewingDoc.filePath && viewingDoc.filePath !== '' && (
                <div className={`w-full lg:w-1/2 p-4 border-b lg:border-b-0 lg:border-r ${t.border} flex flex-col bg-black/10 min-h-[50%] lg:min-h-full`}>
                  <h3 className={`text-xs font-black uppercase tracking-widest ${t.subtext} mb-3 shrink-0`}>Bản gốc tải lên</h3>
                  
                  <div className="flex-1 rounded-2xl overflow-auto border border-white/10 bg-black/20 relative custom-scrollbar">
                    
                    {!viewingDoc.filePath.toLowerCase().endsWith('.pdf') && (
                      <div className="sticky top-4 left-1/2 -translate-x-1/2 w-max z-10 flex items-center justify-center gap-2 bg-black/60 p-1.5 rounded-xl backdrop-blur-md text-white shadow-lg">
                        <button 
                          onClick={() => setZoomLevel(p => Math.max(0.25, p - 0.25))} 
                          className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                          title="Thu nhỏ"
                        >
                          <ZoomOut size={16} />
                        </button>
                        <button 
                          onClick={() => setZoomLevel(1)} 
                          className="px-2 hover:bg-white/20 rounded-lg text-xs font-bold font-mono transition-colors" 
                          title="Đặt lại mức mặc định (100%)"
                        >
                          {Math.round(zoomLevel * 100)}%
                        </button>
                        <button 
                          onClick={() => setZoomLevel(p => Math.min(5, p + 0.25))} 
                          className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
                          title="Phóng to"
                        >
                          <ZoomIn size={16} />
                        </button>
                      </div>
                    )}

                    <div className="min-w-full min-h-full flex items-start justify-center p-4">
                      {viewingDoc.filePath.toLowerCase().endsWith('.pdf') ? (
                        <iframe src={viewingDoc.filePath} className="w-full h-full absolute inset-0" title="Bản gốc PDF" />
                      ) : (
                        <img 
                          src={viewingDoc.filePath} 
                          alt="Bản gốc" 
                          className="transition-all duration-200 shadow-md object-contain"
                          style={{
                              width: `${zoomLevel * 100}%`,
                              height: 'auto',
                              maxWidth: 'none'
                          }}
                        />
                      )}
                    </div>
                  </div>
                  
                  <a
                    href={viewingDoc.filePath}
                    download
                    target="_blank"
                    rel="noreferrer"
                    className={`mt-3 py-2 px-4 shrink-0 rounded-xl text-xs font-bold border ${t.border} bg-black/5 hover:bg-black/20 transition-colors flex items-center justify-center gap-2`}
                  >
                    <Download size={13} /> Tải file gốc
                  </a>
                </div>
              )}

              <div className={`w-full ${viewingDoc.filePath ? 'lg:w-1/2' : ''} p-4 flex flex-col gap-4 min-h-[50%] lg:min-h-full overflow-hidden`}>
                <h3 className={`text-xs font-black uppercase tracking-widest ${t.subtext} shrink-0`}>Nội dung số hóa (OCR)</h3>

                {editingDocId === viewingDoc.id ? (
                  <textarea
                    value={editForm.content}
                    onChange={e => setEditForm({ ...editForm, content: e.target.value })}
                    className={`w-full flex-1 h-full min-h-0 ${t.inputBg} border ${t.border} rounded-2xl p-5 text-sm font-mono leading-relaxed outline-none resize-none shadow-inner`}
                    placeholder="Nội dung số hóa không được để trống..."
                  />
                ) : (
                  <textarea
                    readOnly
                    value={viewingDoc.content}
                    className={`w-full flex-1 h-full min-h-0 ${t.panel} border ${t.border} rounded-2xl p-5 text-sm font-mono leading-relaxed outline-none resize-none shadow-inner custom-scrollbar`}
                  />
                )}

                <div className="flex justify-end gap-2 shrink-0 pt-2 flex-wrap">
                  {editingDocId === viewingDoc.id ? (
                    <>
                      <button
                        onClick={cancelEdit}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-gray-500/20 text-gray-400 hover:bg-gray-500 hover:text-white transition-colors"
                      >
                        Hủy
                      </button>
                      <button
                        onClick={() => handleSaveUpdate(viewingDoc.id)}
                        className={`px-4 py-2 rounded-xl text-xs font-bold ${t.button} flex items-center gap-1.5`}
                      >
                        <Save size={14} /> Lưu thay đổi
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={() => startEdit(viewingDoc)}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-500/20 text-amber-500 hover:bg-amber-500 hover:text-white transition-colors flex items-center gap-1.5"
                      >
                        <Edit3 size={14} /> Chỉnh sửa
                      </button>
                      <button
                        onClick={() => {
                          const id = viewingDoc.id;
                          setViewingDoc(null);
                          handleDeleteDoc(id);
                        }}
                        className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-colors ${
                          isEmployee
                            ? 'bg-orange-500/20 text-orange-500 hover:bg-orange-500 hover:text-white'
                            : 'bg-red-500/20 text-red-500 hover:bg-red-500 hover:text-white'
                        }`}
                      >
                        <Trash2 size={14} />
                        {isEmployee ? 'Yêu cầu xóa' : 'Xóa văn bản'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* MODAL YÊU CẦU XÓA (dành cho nhân viên) */}
      {/* ============================================================ */}
      {deleteRequestModal.show && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className={`${t.panel} w-full max-w-md rounded-3xl shadow-2xl border ${t.border} p-6 relative`}>
            <button
              onClick={() => setDeleteRequestModal({ show: false, docId: null, reason: '' })}
              className="absolute top-4 right-4 text-gray-500 hover:text-red-500 transition-colors p-1"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-full bg-orange-500/10 text-orange-500">
                <AlertCircle size={24} />
              </div>
              <h3 className="text-lg font-black uppercase tracking-widest">Yêu cầu xóa văn bản</h3>
            </div>

            <p className={`text-xs ${t.subtext} mb-4`}>
              Vui lòng nhập lý do bạn muốn xóa văn bản này. Yêu cầu sẽ được gửi đến quản lí để phê duyệt.
            </p>

            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-bold uppercase tracking-widest opacity-60">Lý do <span className="text-red-500">*</span></label>
              <textarea
                value={deleteRequestModal.reason}
                onChange={(e) => setDeleteRequestModal(prev => ({ ...prev, reason: e.target.value }))}
                className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} text-sm font-bold outline-none resize-none h-28`}
                placeholder="Nhập lý do xóa (không được để trống)..."
              />
            </div>

            <div className="mt-6 pt-4 border-t border-white/10 flex justify-end gap-3">
              <button
                onClick={() => setDeleteRequestModal({ show: false, docId: null, reason: '' })}
                className={`px-6 py-2.5 rounded-xl text-sm font-bold border ${t.border} hover:bg-black/5 transition-colors`}
              >
                Hủy
              </button>
              <button
                onClick={submitDeleteRequest}
                className={`px-6 py-2.5 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}
              >
                <Send size={16} /> Gửi yêu cầu
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}