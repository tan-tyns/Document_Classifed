import React, { useState } from 'react';
import { X, FileText, Edit3, Save, AlertCircle } from 'lucide-react';

export default function EditModal({ docData, fileName, previewUrl, onClose, onSave, t }) {
  const [editForm, setEditForm] = useState({
    docType: docData.docType || '',
    soHieu: docData.soHieu || '',
    date: docData.date || '',
    noiBanHanh: docData.noiBanHanh || '',
    trichYeu: docData.trichYeu || '',
    content: docData.content || ''
  });

  const handleFormChange = (e) => setEditForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = () => {
    onSave({ ...docData, ...editForm });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 lg:p-8 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className={`${t.panel} w-full max-w-[1600px] h-full max-h-[90vh] rounded-3xl shadow-2xl flex flex-col lg:flex-row overflow-hidden border ${t.border} relative`}>
        <button onClick={onClose} className="absolute top-4 right-4 z-50 bg-black/20 hover:bg-red-500 text-white p-2 rounded-full backdrop-blur-md transition-colors"><X size={20} /></button>
        
        <div className={`w-full lg:w-1/2 bg-black/10 border-r ${t.border} flex items-center justify-center p-4 overflow-hidden relative`}>
          <div className="absolute top-4 left-4 bg-black/50 text-white text-[10px] font-bold px-3 py-1.5 rounded-lg backdrop-blur-md z-10 uppercase tracking-wider">Bản gốc: {fileName}</div>
          {previewUrl ? (
            <div className="w-full h-full overflow-auto custom-scrollbar flex items-start justify-center"><img src={previewUrl} className="max-w-full h-auto object-contain shadow-lg" alt="Document original" /></div>
          ) : (
            <div className="flex flex-col items-center justify-center opacity-50"><FileText size={64} /><p className="mt-4 font-bold tracking-widest uppercase">Định dạng PDF</p></div>
          )}
        </div>

        <div className={`w-full lg:w-1/2 flex flex-col p-6 lg:p-8 overflow-y-auto custom-scrollbar ${t.text}`}>
          <div className="flex items-center gap-3 mb-6 shrink-0">
            <div className={`p-3 rounded-xl ${t.button.split(' ')[0]} ${t.shadow}`}><Edit3 size={24} className="text-inherit" /></div>
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Đối chiếu & Lưu trữ</h2>
              <p className={`text-xs ${t.subtext}`}>Dữ liệu sau khi kiểm tra sẽ được đẩy thẳng vào Kho Lưu Trữ.</p>
            </div>
          </div>

          <div className="flex flex-col gap-4 flex-1">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5"><label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Loại văn bản</label><input name="docType" value={editForm.docType} onChange={handleFormChange} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} /></div>
              <div className="flex flex-col gap-1.5"><label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Số hiệu văn bản</label><input name="soHieu" value={editForm.soHieu} onChange={handleFormChange} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} /></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5"><label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Ngày ban hành</label><input name="date" value={editForm.date} onChange={handleFormChange} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} /></div>
              <div className="flex flex-col gap-1.5"><label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Nơi ban hành</label><input name="noiBanHanh" value={editForm.noiBanHanh} onChange={handleFormChange} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} /></div>
            </div>
            <div className="flex flex-col gap-1.5"><label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Trích yếu / Tiêu đề</label><textarea name="trichYeu" value={editForm.trichYeu} onChange={handleFormChange} rows="2" className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold resize-none custom-scrollbar`} /></div>
            <div className="flex flex-col gap-1.5 flex-1 min-h-[200px]"><label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} flex items-center justify-between`}><span>Nội dung chi tiết (Văn bản số hóa)</span><span className="flex items-center gap-1 text-orange-500 normal-case tracking-normal"><AlertCircle size={10} /> Dò lỗi chính tả tại đây</span></label><textarea name="content" value={editForm.content} onChange={handleFormChange} className={`w-full h-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-mono leading-relaxed resize-none custom-scrollbar shadow-inner`} /></div>
          </div>

          <div className="mt-6 pt-4 border-t border-black/10 flex justify-end gap-3 shrink-0">
            <button onClick={onClose} className={`px-6 py-3 rounded-xl text-sm font-bold border ${t.border} hover:bg-black/5 transition-colors`}>Hủy bỏ</button>
            <button onClick={handleSubmit} className={`px-8 py-3 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}><Save size={18} /> Lưu vào Kho</button>
          </div>
        </div>
      </div>
    </div>
  );
}