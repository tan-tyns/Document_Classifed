import React, { useState } from 'react';
import axios from 'axios';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { 
  Upload, Loader2, CheckCircle2, FileText, Search, X, 
  Image as ImageIconUI, FileSpreadsheet, Archive, CalendarDays, Bookmark, Trash2, Edit3, MapPin, FileSearch
} from 'lucide-react';
import EditModal from '../components/EditModal';

export default function OCRStation({ onArchiveSave, t }) {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [results, setResults] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [editingIndex, setEditingIndex] = useState(null);

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) {
      setFiles(prev => [...prev, ...selectedFiles]);
      const newPreviews = selectedFiles.map(f => f.type.includes("image") ? URL.createObjectURL(f) : null);
      setPreviews(prev => [...prev, ...newPreviews]);
    }
    e.target.value = null;
  };

  const removeFile = (index) => {
    const newFiles = [...files]; const newPreviews = [...previews];
    newFiles.splice(index, 1); newPreviews.splice(index, 1);
    setFiles(newFiles); setPreviews(newPreviews);
    if (results[index]) {
      const newResults = [...results]; newResults.splice(index, 1); setResults(newResults);
    }
    setCurrentIndex(Math.max(0, index - 1));
  };

  const clearAll = () => {
    if (window.confirm("Bạn có chắc chắn muốn xóa toàn bộ phiên làm việc này không?")) {
      setFiles([]); setPreviews([]); setResults([]); setCurrentIndex(0);
    }
  };

  const processDocument = async () => {
    if (files.length === 0 || files.length === results.length) return;
    setLoading(true);
    const startIndex = results.length;

    for (let i = startIndex; i < files.length; i++) {
      const formData = new FormData(); formData.append('file', files[i]);
      try {
        const response = await axios.post('http://localhost:8000/process', formData);
        setResults(prev => [...prev, {
          id: `doc_${Date.now()}_${i}`,
          fileName: files[i].name,
          text: response.data.text, label: response.data.label, confidence: response.data.confidence,
          docType: response.data.docType, date: response.data.date, soHieu: response.data.soHieu || '',
          noiBanHanh: response.data.noiBanHanh || '', trichYeu: response.data.trichYeu || '', content: response.data.content
        }]);
        setCurrentIndex(i);
      } catch (err) {
        setResults(prev => [...prev, {
          id: `err_${Date.now()}_${i}`, fileName: files[i].name,
          text: "⚠️ LỖI: Backend Python chưa phản hồi.", label: "ERROR", confidence: 0, docType: "KHONG_XAC_DINH", 
          date: "KHONG_XAC_DINH", soHieu: "", noiBanHanh: "", trichYeu: "", content: ""
        }]);
      }
    }
    setLoading(false);
  };

  const exportToCSV = () => { /* Giống code cũ */ };
  const exportToZIP = async () => { /* Giống code cũ */ };

  const openEditModal = (idx) => {
    if (!results[idx]) { alert("Vui lòng chạy trích xuất AI trước khi chỉnh sửa file này!"); return; }
    if (results[idx].label === "ERROR") { alert("File này bị lỗi, không có dữ liệu để sửa!"); return; }
    setEditingIndex(idx);
  };

  const handleSaveEdit = (updatedDoc) => {
    const updatedResults = [...results];
    updatedResults[editingIndex] = updatedDoc;
    setResults(updatedResults);
    onArchiveSave(updatedDoc); // Đẩy qua App.jsx lưu vào Kho
    setEditingIndex(null);
  };

  const currentResult = results[currentIndex] || null;

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 flex-1 overflow-hidden min-h-0 animate-in fade-in duration-300">
      <section className="flex flex-col gap-4 overflow-hidden min-h-0">
        <div className={`${t.panel} rounded-3xl ${t.border} border p-4 lg:p-6 flex-1 flex flex-col shadow-2xl overflow-hidden min-h-0`}>
          <div className="flex justify-between items-center mb-4 shrink-0">
            <h2 className={`text-xs font-black ${t.subtext} uppercase tracking-widest flex items-center gap-2`}><Upload size={16} className={t.accent} /> Nạp dữ liệu ({files.length} file)</h2>
            {files.length > 0 && !loading && <button onClick={clearAll} className="flex items-center gap-1 text-[10px] font-bold text-red-500 hover:text-red-400 bg-red-500/10 px-3 py-1.5 rounded-lg transition-colors uppercase"><Trash2 size={12} /> Xóa tất cả</button>}
          </div>
          <div className={`flex-1 min-h-0 border-2 border-dashed ${t.border} rounded-2xl relative bg-black/5 flex flex-col overflow-hidden transition-all`}>
            {files.length > 0 ? (
              <div className="flex-1 overflow-y-auto custom-scrollbar p-3">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 lg:gap-4 auto-rows-max">
                  {files.map((file, idx) => (
                    <div key={idx} onClick={() => openEditModal(idx)} className={`relative aspect-square rounded-xl overflow-hidden border ${t.border} group/item bg-black/20 cursor-pointer hover:ring-2 hover:ring-[#FFB7C5] transition-all`} title="Click để xem chi tiết & chỉnh sửa">
                      {previews[idx] ? <img src={previews[idx]} className="w-full h-full object-cover opacity-80 group-hover/item:opacity-100 transition-opacity" alt="Preview" /> : <div className="w-full h-full flex flex-col items-center justify-center"><FileText className={t.subtext} size={24} /><span className={`text-[9px] mt-2 font-bold truncate w-full px-2 text-center ${t.subtext}`}>PDF</span></div>}
                      {!loading && <button onClick={(e) => { e.stopPropagation(); removeFile(idx); }} className="absolute top-1 right-1 bg-red-500/80 hover:bg-red-500 text-white p-1 rounded-full opacity-0 group-hover/item:opacity-100 transition-opacity z-10"><X size={12} /></button>}
                      {results[idx] && <div className="absolute bottom-0 left-0 right-0 bg-green-500/90 text-white text-[9px] font-bold py-1 flex items-center justify-center gap-1 backdrop-blur-sm"><CheckCircle2 size={10} /> Đã xử lý</div>}
                      {results[idx] && results[idx].label !== "ERROR" && <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover/item:opacity-100 transition-opacity pointer-events-none"><Edit3 className="text-white drop-shadow-md" size={24} /></div>}
                    </div>
                  ))}
                  <label className={`aspect-square rounded-xl border border-dashed ${t.border} flex flex-col items-center justify-center bg-white/5 hover:bg-white/10 transition-colors cursor-pointer`}><Upload className={t.subtext} size={24} /><span className={`text-[10px] mt-2 ${t.subtext} text-center px-1`}>Thêm file mới</span><input type="file" multiple className="hidden" accept=".jpg,.jpeg,.png,.pdf" onChange={handleFileChange} /></label>
                </div>
              </div>
            ) : (
              <label className="text-center w-full h-full flex flex-col items-center justify-center cursor-pointer group-hover:scale-105 transition-transform"><div className={`w-20 h-20 lg:w-24 lg:h-24 rounded-full flex items-center justify-center mx-auto mb-4 lg:mb-6 bg-white/5 border ${t.border}`}><ImageIconUI className={`${t.subtext}`} size={40} /></div><p className={`${t.subtext} font-bold text-base lg:text-lg uppercase tracking-tighter`}>Kéo thả Ảnh / PDF</p><p className="text-[10px] opacity-40 mt-2">Hỗ trợ cộng dồn vô hạn số lượng file</p><input type="file" multiple className="hidden" accept=".jpg,.jpeg,.png,.pdf" onChange={handleFileChange} /></label>
            )}
          </div>
          <button onClick={processDocument} disabled={files.length === 0 || loading || results.length === files.length} className={`mt-4 lg:mt-6 w-full py-4 ${t.button} font-black rounded-2xl ${t.shadow} transition-all flex justify-center items-center gap-3 text-base lg:text-lg uppercase tracking-widest active:scale-95 disabled:opacity-30 shrink-0`}>
            {loading ? <Loader2 className="animate-spin" /> : <CheckCircle2 size={20} />}
            {loading ? `Đang xử lý (${results.length}/${files.length})...` : results.length === files.length && files.length > 0 ? "Tất cả file đã hoàn tất" : "Bắt đầu trích xuất"}
          </button>
        </div>
      </section>

      <section className="flex flex-col gap-4 overflow-hidden min-h-0">
        <div className="flex justify-between items-end gap-4 shrink-0">
          <div className={`flex gap-2 overflow-x-auto pb-2 custom-scrollbar flex-1`}>
            {results.map((res, idx) => <button key={idx} onClick={() => setCurrentIndex(idx)} className={`px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap border transition-colors ${currentIndex === idx ? `${t.button.split(' ')[0]} border-transparent ${t.shadow}` : `${t.panel} ${t.border} ${t.subtext} hover:bg-white/5`}`}>📄 File {idx + 1}</button>)}
          </div>
        </div>

        <div className={`${t.panel} rounded-3xl border ${t.border} p-4 lg:p-6 shadow-2xl shrink-0`}>
          <div className="flex justify-between items-center mb-4">
            <h2 className={`text-xs font-black ${t.subtext} uppercase flex items-center gap-2`}><FileText size={16} className={t.accent} />Nội dung trích xuất</h2>
            {currentResult && currentResult.label !== "ERROR" && <button onClick={() => openEditModal(currentIndex)} className={`flex items-center gap-1 text-[10px] uppercase font-bold px-3 py-1.5 ${t.button} rounded-lg transition-transform active:scale-95`}><Edit3 size={12} /> Kiểm tra & Lưu</button>}
          </div>
          {currentResult ? (
            <div className="w-full grid grid-cols-2 xl:grid-cols-3 gap-2.5 lg:gap-3">
              <div className={`flex flex-col justify-center bg-black/10 px-4 py-2 rounded-xl border ${t.border} border-white/5`}><div className={`flex items-center gap-1.5 text-[9px] font-black ${t.subtext} mb-0.5 uppercase`}><MapPin size={10} /> Nơi ban hành</div><span className={`font-bold text-sm tracking-wide ${currentResult.label === "ERROR" ? "text-red-500" : t.text} truncate`}>{currentResult.noiBanHanh || "Chưa xác định"}</span></div>
              <div className={`flex flex-col justify-center bg-black/10 px-4 py-2 rounded-xl border ${t.border} border-white/5`}><div className={`flex items-center gap-1.5 text-[9px] font-black ${t.subtext} mb-0.5 uppercase`}><Bookmark size={10} /> Loại văn bản</div><span className={`font-bold text-sm tracking-wide ${t.text} truncate`}>{currentResult.docType === "KHONG_XAC_DINH" ? "Chưa xác định" : currentResult.docType}</span></div>
              <div className={`flex flex-col justify-center bg-black/10 px-4 py-2 rounded-xl border ${t.border} border-white/5`}><div className={`flex items-center gap-1.5 text-[9px] font-black ${t.subtext} mb-0.5 uppercase`}><CalendarDays size={10} /> Ngày ban hành</div><span className={`font-bold text-sm tracking-wide ${t.text} truncate`}>{currentResult.date === "KHONG_XAC_DINH" ? "Không tìm thấy" : currentResult.date}</span></div>
              <div className={`flex flex-col justify-center bg-black/10 px-4 py-2 rounded-xl border ${t.border} border-white/5`}><div className={`flex items-center gap-1.5 text-[9px] font-black ${t.subtext} mb-0.5 uppercase`}><FileSearch size={10} /> Số hiệu</div><span className={`font-bold text-sm tracking-wide ${t.text} truncate`}>{currentResult.soHieu || "Chưa có số hiệu"}</span></div>
              <div className={`col-span-2 flex flex-col justify-center bg-black/10 px-4 py-2 rounded-xl border ${t.border} border-white/5`}><div className={`flex items-center gap-1.5 text-[9px] font-black ${t.subtext} mb-0.5 uppercase`}><FileText size={10} /> Trích yếu</div><span className={`font-bold text-sm tracking-wide ${t.text} truncate`}>{currentResult.trichYeu || "Chưa có trích yếu"}</span></div>
            </div>
          ) : <p className={`${t.subtext} italic py-4`}>{loading ? "Đang chờ kết quả từ AI..." : "Chọn file và chạy trích xuất để xem kết quả"}</p>}
        </div>

        <div className={`${t.panel} rounded-3xl border ${t.border} p-4 lg:p-6 flex-1 flex flex-col shadow-2xl overflow-hidden min-h-0`}>
          <h2 className={`text-xs font-black ${t.subtext} uppercase flex items-center gap-2 tracking-widest mb-3 lg:mb-4 shrink-0`}><Search size={16} className={t.accent} /> Nội dung số hóa (OCR) {currentResult && <span className="normal-case opacity-50 ml-2 truncate max-w-[200px]">- {currentResult.fileName}</span>}</h2>
          <textarea readOnly value={currentResult ? currentResult.content : ""} className={`flex-1 w-full ${t.inputBg} border ${t.border} rounded-2xl p-4 lg:p-6 text-sm font-mono leading-relaxed text-inherit outline-none resize-none shadow-inner transition-all overflow-y-auto whitespace-pre-wrap custom-scrollbar`} placeholder="Văn bản hành chính sau khi nhận dạng sẽ hiển thị ở đây..." />
        </div>
      </section>

      {editingIndex !== null && (
        <EditModal 
          docData={results[editingIndex]} 
          fileName={files[editingIndex]?.name}
          previewUrl={previews[editingIndex]}
          onClose={() => setEditingIndex(null)}
          onSave={handleSaveEdit}
          t={t}
        />
      )}
    </main>
  );
}