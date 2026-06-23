// Archive.jsx
import React, { useState, useEffect } from 'react';
import { saveAs } from 'file-saver';
import { Search, Filter, FileSpreadsheet, Archive as ArchiveIcon, Eye, X, FileText, Trash2, Edit3, Save, Tag, MapPin, Hash } from 'lucide-react';

const DOCUMENT_TYPES = ['Báo cáo', 'Công văn', 'Giấy mời', 'Kế hoạch', 'Quyết định', 'Thông báo', 'Tờ trình', 'Khác'];

export default function Archive({ archivedDocs, setArchivedDocs, user, t }) {
  // --- CÁC TRẠNG THÁI BỘ LỌC TÌM KIẾM ---
  const [activeTab, setActiveTab] = useState('Tất cả'); // Tab loại văn bản hiện tại
  const [searchSoHieu, setSearchSoHieu] = useState(''); // Tìm theo Số hiệu
  const [searchNoiBanHanh, setSearchNoiBanHanh] = useState(''); // Tìm theo Nơi ban hành
  const [searchTrichYeu, setSearchTrichYeu] = useState(''); // Tìm theo Trích yếu
  
  // Trạng thái modal xem chi tiết & chỉnh sửa
  const [viewingDoc, setViewingDoc] = useState(null);
  const [editingDocId, setEditingDocId] = useState(null);
  const [editForm, setEditForm] = useState({ docType: '', soHieu: '', date: '', trichYeu: '', content: '', noiBanHanh: '' });

  const isEmployee = user?.role === 'employee';

  // --- TỰ ĐỘNG GỌI API LẤY DỮ LIỆU TỪ DATABASE KHI ĐĂNG NHẬP ---
  useEffect(() => {
    const fetchArchiveData = async () => {
      if (!user?.id) return;
      try {
        const response = await fetch(`http://localhost:8000/documents?user_id=${user.id}&role=${user.role}`);
        const data = await response.json();
        if (response.ok) {
          setArchivedDocs(data);
        } else {
          console.error("Lỗi fetch DB:", data.detail);
        }
      } catch (error) {
        console.error("Lỗi kết nối API kho lưu trữ:", error);
      }
    };
    fetchArchiveData();
  }, [user, setArchivedDocs]);

  // --- HÀM TÍNH SỐ LƯỢNG FILE THEO TỪNG LOẠI ĐỂ ĐÍNH LÊN TAB ---
  const getCountByType = (type) => {
    if (type === 'Tất cả') return archivedDocs.length;
    return archivedDocs.filter(doc => (doc.docType || '').toLowerCase() === type.toLowerCase()).length;
  };

  // --- BIÊN DỊCH BỘ LỌC TÌM KIẾM CHI TIẾT ---
  const filteredArchive = archivedDocs.filter(doc => {
    // 1. Lọc theo Tab loại văn bản đang chọn
    const matchesTab = activeTab === 'Tất cả' || (doc.docType || '').toLowerCase() === activeTab.toLowerCase();
    
    // 2. Lọc theo các ô tìm kiếm nâng cao độc lập
    const matchesSoHieu = (doc.soHieu || '').toLowerCase().includes(searchSoHieu.toLowerCase());
    const matchesNoiBanHanh = (doc.noiBanHanh || '').toLowerCase().includes(searchNoiBanHanh.toLowerCase());
    const matchesTrichYeu = (doc.trichYeu || '').toLowerCase().includes(searchTrichYeu.toLowerCase());

    return matchesTab && matchesSoHieu && matchesNoiBanHanh && matchesTrichYeu;
  });

  const startEdit = (doc) => {
    setEditingDocId(doc.id);
    setEditForm({ ...doc });
  };

  const handleSaveUpdate = async (docId) => {
    if (!editForm.content || editForm.content.trim() === '') {
      alert("❌ Lỗi: Nội dung văn bản (OCR) không được phép để trống!");
      return;
    }
    if (!editForm.trichYeu || editForm.trichYeu.trim() === '') {
      alert("❌ Lỗi: Trích yếu không được phép để trống!");
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
        throw new Error(errData.detail || "Không thể cập nhật tài liệu.");
      }

      setArchivedDocs(prev => prev.map(d => d.id === docId ? { ...d, ...editForm } : d));
      setEditingDocId(null);
      if (viewingDoc && viewingDoc.id === docId) {
        setViewingDoc({ ...viewingDoc, ...editForm });
      }
      alert("✅ Cập nhật văn bản thành công!");
    } catch (error) {
      alert("Lỗi: " + error.message);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (isEmployee) {
      alert("❌ Bạn không có quyền xóa tài liệu này!");
      return;
    }
    if (!window.confirm("Bạn có chắc chắn muốn xóa vĩnh viễn văn bản này khỏi hệ thống?")) return;

    try {
      const response = await fetch(`http://localhost:8000/documents/${docId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error("Không thể xóa bản ghi trên hệ thống.");

      setArchivedDocs(prev => prev.filter(d => d.id !== docId));
      alert("🗑️ Đã xóa văn bản thành công!");
    } catch (error) {
      alert("Lỗi: " + error.message);
    }
  };

  const exportToCSV = () => {
    if (archivedDocs.length === 0) return;
    let csvContent = "\uFEFFTên File,Nơi Ban Hành,Loại Văn Bản,Số Hiệu,Ngày Ban Hành,Trích Yếu,Nội Dung\n";
    archivedDocs.forEach(r => {
      const safeContent = r.content ? r.content.replace(/"/g, '""') : "";
      const safeTrichYeu = r.trichYeu ? r.trichYeu.replace(/"/g, '""') : "";
      csvContent += `"${r.fileName}","${r.noiBanHanh}","${r.docType}","${r.soHieu}","${r.date}","${safeTrichYeu}","${safeContent}"\n`;
    });
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    saveAs(blob, "KhoLuuTru_VanBan.csv");
  };

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 flex flex-col flex-1 overflow-hidden min-h-0 animate-in fade-in duration-300">
      <div className={`${t.panel} rounded-3xl ${t.border} border p-6 flex-1 flex flex-col shadow-2xl overflow-hidden min-h-0`}>
        
        {/* ================================================================= */}
        {/* 1. KHU VỰC BỘ LỌC TÌM KIẾM NÂNG CAO (MỚI) */}
        {/* ================================================================= */}
        <div className="bg-black/5 p-4 rounded-2xl border border-white/5 mb-5 shrink-0">
          <div className="text-[10px] font-black uppercase tracking-widest opacity-60 mb-3 flex items-center gap-1"><Search size={12} /> Bộ lọc tìm kiếm chi tiết</div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
            
            <div className="relative">
              <Hash size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input type="text" value={searchSoHieu} onChange={(e) => setSearchSoHieu(e.target.value)} placeholder="Tìm theo Số hiệu văn bản..." className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-xs font-bold`} />
            </div>

            <div className="relative">
              <MapPin size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input type="text" value={searchNoiBanHanh} onChange={(e) => setSearchNoiBanHanh(e.target.value)} placeholder="Tìm theo Nơi ban hành..." className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-xs font-bold`} />
            </div>

            <div className="relative">
              <FileText size={14} className={`absolute left-3.5 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input type="text" value={searchTrichYeu} onChange={(e) => setSearchTrichYeu(e.target.value)} placeholder="Tìm theo cụm từ Trích yếu..." className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-xs font-bold`} />
            </div>

          </div>
        </div>

        {/* ================================================================= */}
        {/* 2. THANH CHUYỂN TAB CÁC LOẠI VĂN BẢN (MỚI) */}
        {/* ================================================================= */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b pb-3 mb-6 border-white/5 gap-4 shrink-0 overflow-x-auto custom-scrollbar w-full">
          <div className="flex gap-1.5 items-center">
            {['Tất cả', ...DOCUMENT_TYPES].map((type) => {
              const isActive = activeTab === type;
              const fileCount = getCountByType(type);
              return (
                <button
                  key={type}
                  type="button"
                  onClick={() => setActiveTab(type)}
                  className={`px-4 py-2 rounded-xl text-xs font-black transition-all flex items-center gap-2 whitespace-nowrap ${isActive ? `${t.button.split(' ')[0]} ${t.shadow} text-inherit scale-105` : `bg-black/5 border ${t.border} ${t.subtext} hover:bg-black/10`}`}
                >
                  {type}
                  <span className={`px-1.5 py-0.5 rounded-md text-[9px] ${isActive ? 'bg-white/20 text-inherit' : 'bg-black/10 opacity-60'}`}>{fileCount}</span>
                </button>
              );
            })}
          </div>

          {filteredArchive.length > 0 && (
            <button onClick={exportToCSV} className="px-4 py-2 flex items-center gap-2 rounded-xl text-xs font-bold bg-green-600/20 text-green-500 border border-green-500/30 hover:bg-green-600 hover:text-white transition-all whitespace-nowrap self-end sm:self-auto">
              <FileSpreadsheet size={16} /> Xuất file CSV ({filteredArchive.length})
            </button>
          )}
        </div>

        {/* ================================================================= */}
        {/* 3. LƯỚI DANH SÁCH VĂN BẢN */}
        {/* ================================================================= */}
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
          {filteredArchive.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {filteredArchive.map((doc, idx) => (
                <div key={doc.id || idx} className={`flex flex-col bg-black/5 rounded-2xl border ${t.border} p-5 hover:shadow-lg transition-shadow`}>
                  <div className="flex justify-between items-start mb-3">
                    <div className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${t.button.split(' ')[0]} ${t.shadow}`}>{doc.docType || "Không xác định"}</div>
                    <span className={`text-[10px] font-bold ${t.subtext}`}>{doc.date}</span>
                  </div>
                  <h3 className="font-bold text-base mb-1 truncate" title={doc.trichYeu}>{doc.trichYeu || "Chưa có trích yếu"}</h3>
                  <p className={`text-xs ${t.subtext} mb-4 font-mono truncate`}>Số hiệu: {doc.soHieu || "N/A"} • Nơi BH: {doc.noiBanHanh || "N/A"}</p>
                  
                  <div className="mt-auto flex gap-2">
                    <button onClick={() => setViewingDoc(doc)} className={`flex-1 py-2 rounded-xl text-xs font-bold bg-white/50 border ${t.border} hover:bg-white transition-colors flex justify-center items-center gap-2`}><Eye size={14} /> Xem văn bản</button>
                    <button onClick={() => startEdit(doc)} className={`py-2 px-3 rounded-xl text-xs font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500 hover:text-white transition-colors`} title="Sửa nhanh"><Edit3 size={14} /></button>
                    
                    {!isEmployee && (
                      <button onClick={() => handleDeleteDoc(doc.id)} className={`py-2 px-3 rounded-xl text-xs font-bold bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white transition-colors`} title="Xóa văn bản"><Trash2 size={14} /></button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center opacity-50 py-12">
              <ArchiveIcon size={64} className="mb-4 text-dashed animate-pulse" />
              <h3 className="text-base font-black uppercase tracking-widest">Không tìm thấy tài liệu phù hợp</h3>
              <p className="text-xs mt-1">Vui lòng điều chỉnh lại tab phân loại hoặc các ô tìm kiếm nâng cao phía trên.</p>
            </div>
          )}
        </div>
      </div>

      {/* ================================================================= */}
      {/* 4. MODAL XEM CHI TIẾT & SỬA ĐỔI */}
      {/* ================================================================= */}
      {viewingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 lg:p-8 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className={`${t.panel} w-full max-w-4xl max-h-[90vh] rounded-3xl shadow-2xl border ${t.border} flex flex-col overflow-hidden relative`}>
            <button onClick={() => { setViewingDoc(null); setEditingDocId(null); }} className="absolute top-4 right-4 z-50 bg-black/10 hover:bg-red-500 text-white p-2 rounded-full backdrop-blur-md transition-colors"><X size={20} /></button>
            
            <div className={`p-6 border-b ${t.border} bg-black/5`}>
              {editingDocId === viewingDoc.id ? (
                <input type="text" value={editForm.trichYeu} onChange={e => setEditForm({...editForm, trichYeu: e.target.value})} className={`w-full max-w-2xl px-3 py-1.5 rounded-xl border ${t.border} ${t.inputBg} font-black uppercase text-lg outline-none`} placeholder="Nhập trích yếu..." />
              ) : (
                <h2 className="text-2xl font-black uppercase tracking-tight pr-12">{viewingDoc.trichYeu || "Không có tiêu đề"}</h2>
              )}
              
              <div className="flex flex-wrap gap-4 mt-3 text-xs font-bold font-mono items-center">
                {editingDocId === viewingDoc.id ? (
                  <>
                    <select value={editForm.docType} onChange={e => setEditForm({...editForm, docType: e.target.value})} className={`px-2 py-1 rounded border ${t.border} ${t.inputBg}`}>
                      {DOCUMENT_TYPES.map(type => <option key={type} value={type}>{type}</option>)}
                    </select>
                    <span>Số:</span>
                    <input type="text" value={editForm.soHieu} onChange={e => setEditForm({...editForm, soHieu: e.target.value})} className={`w-24 px-2 py-1 rounded border ${t.border} ${t.inputBg}`} />
                    <span>Ngày:</span>
                    <input type="text" value={editForm.date} onChange={e => setEditForm({...editForm, date: e.target.value})} className={`w-32 px-2 py-1 rounded border ${t.border} ${t.inputBg}`} />
                    <span>Nơi ban hành:</span>
                    <input type="text" value={editForm.noiBanHanh} onChange={e => setEditForm({...editForm, noiBanHanh: e.target.value})} className={`w-40 px-2 py-1 rounded border ${t.border} ${t.inputBg}`} />
                  </>
                ) : (
                  <>
                    <span className={t.accent}>Loại: {viewingDoc.docType}</span><span className="opacity-50">|</span>
                    <span>Số: {viewingDoc.soHieu || "N/A"}</span><span className="opacity-50">|</span>
                    <span>Ngày: {viewingDoc.date || "N/A"}</span><span className="opacity-50">|</span>
                    <span>Nơi BH: {viewingDoc.noiBanHanh || "N/A"}</span>
                  </>
                )}
              </div>
            </div>

            <div className="p-6 overflow-y-auto custom-scrollbar flex-1 bg-black/5 flex flex-col gap-4">
              {editingDocId === viewingDoc.id ? (
                <textarea value={editForm.content} onChange={e => setEditForm({...editForm, content: e.target.value})} className={`w-full flex-1 min-h-[350px] ${t.inputBg} border ${t.border} rounded-2xl p-6 text-sm font-mono leading-relaxed outline-none resize-none shadow-inner`} placeholder="Nội dung số hóa không được phép để trống..." />
              ) : (
                <textarea readOnly value={viewingDoc.content} className={`w-full flex-1 min-h-[350px] ${t.panel} border ${t.border} rounded-2xl p-6 text-sm font-mono leading-relaxed text-inherit outline-none resize-none shadow-inner`} />
              )}
              
              <div className="flex justify-end gap-2 shrink-0">
                {editingDocId === viewingDoc.id ? (
                  <>
                    <button onClick={() => setEditingDocId(null)} className="px-4 py-2 rounded-xl text-xs font-bold bg-gray-500/20 text-gray-400 hover:bg-gray-500 hover:text-white transition-colors">Hủy</button>
                    <button onClick={() => handleSaveUpdate(viewingDoc.id)} className={`px-4 py-2 rounded-xl text-xs font-bold ${t.button} flex items-center gap-1.5`}><Save size={14} /> Lưu thay đổi</button>
                  </>
                ) : (
                  <button onClick={() => startEdit(viewingDoc)} className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-500/20 text-amber-500 hover:bg-amber-500 hover:text-white transition-colors flex items-center gap-1.5"><Edit3 size={14} /> Chỉnh sửa</button>
                )}
                {!isEmployee && !editingDocId && (
                  <button onClick={() => { const id = viewingDoc.id; setViewingDoc(null); handleDeleteDoc(id); }} className="px-4 py-2 rounded-xl text-xs font-bold bg-red-500/20 text-red-500 hover:bg-red-500 hover:text-white transition-colors flex items-center gap-1.5"><Trash2 size={14} /> Xóa văn bản</button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}