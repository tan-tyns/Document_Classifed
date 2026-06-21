import React, { useState } from 'react';
import { saveAs } from 'file-saver';
import { Search, Filter, FileSpreadsheet, Archive as ArchiveIcon, Eye, X, FileText } from 'lucide-react';

const DOCUMENT_TYPES = ['Báo cáo', 'Công văn', 'Giấy mời', 'Kế hoạch', 'Quyết định', 'Thông báo', 'Tờ trình', 'Khác'];

export default function Archive({ archivedDocs, t }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [viewingDoc, setViewingDoc] = useState(null);

  const filteredArchive = archivedDocs.filter(doc => {
    const matchesFilter = filterType === 'ALL' || doc.docType.toLowerCase().includes(filterType.toLowerCase());
    const searchLower = searchQuery.toLowerCase();
    const matchesSearch = 
      doc.fileName.toLowerCase().includes(searchLower) ||
      doc.soHieu.toLowerCase().includes(searchLower) ||
      doc.trichYeu.toLowerCase().includes(searchLower) ||
      doc.noiBanHanh.toLowerCase().includes(searchLower);
    return matchesFilter && matchesSearch;
  });

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
        
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 mb-6 shrink-0">
          <div className="flex flex-1 w-full gap-4">
            <div className="relative flex-1 max-w-md">
              <Search size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Tìm theo tên file, số hiệu, trích yếu..." className={`w-full pl-11 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm`} />
            </div>
            <div className="relative w-48">
              <Filter size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 ${t.subtext}`} />
              <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className={`w-full pl-11 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm appearance-none cursor-pointer font-bold`}>
                <option value="ALL">Tất cả loại văn bản</option>
                {DOCUMENT_TYPES.map(type => <option key={type} value={type}>{type}</option>)}
              </select>
            </div>
          </div>
          {archivedDocs.length > 0 && (
            <button onClick={exportToCSV} className={`px-4 py-2.5 flex items-center gap-2 rounded-xl text-xs font-bold bg-green-600/20 text-green-500 border border-green-500/30 hover:bg-green-600 hover:text-white transition-all whitespace-nowrap`}>
              <FileSpreadsheet size={16} /> Xuất Excel Tổng
            </button>
          )}
        </div>

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
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center opacity-50">
              <ArchiveIcon size={64} className="mb-4" />
              <h3 className="text-lg font-bold uppercase tracking-widest">Kho lưu trữ trống</h3>
              <p className="text-sm">Hãy trích xuất và "Lưu chính thức" để dữ liệu hiện ở đây.</p>
            </div>
          )}
        </div>
      </div>

      {viewingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 lg:p-8 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className={`${t.panel} w-full max-w-4xl max-h-[90vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border ${t.border} relative`}>
            <button onClick={() => setViewingDoc(null)} className="absolute top-4 right-4 z-50 bg-black/10 hover:bg-red-500 text-white p-2 rounded-full backdrop-blur-md transition-colors"><X size={20} /></button>
            <div className={`p-6 border-b ${t.border} bg-black/5`}>
              <h2 className="text-2xl font-black uppercase tracking-tight pr-12">{viewingDoc.trichYeu || "Không có tiêu đề"}</h2>
              <div className="flex gap-4 mt-3 text-xs font-bold font-mono">
                <span className={t.accent}>Loại: {viewingDoc.docType}</span><span className="opacity-50">|</span>
                <span>Số: {viewingDoc.soHieu}</span><span className="opacity-50">|</span><span>Ngày: {viewingDoc.date}</span>
              </div>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar flex-1 bg-black/5">
              <textarea readOnly value={viewingDoc.content} className={`w-full h-full min-h-[400px] ${t.panel} border ${t.border} rounded-2xl p-6 text-sm font-mono leading-relaxed text-inherit outline-none resize-none shadow-inner`} />
            </div>
          </div>
        </div>
      )}
    </main>
  );
}