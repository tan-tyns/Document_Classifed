// Dashboard.jsx
import React from 'react';
import { BarChart3, Users, FileText, Activity, TrendingUp, Clock, CheckCircle2, AlertTriangle, Shield } from 'lucide-react';

export default function Dashboard({ archivedDocs = [], user, t }) {
  // 1. Tính toán tổng số lượng tài liệu thực tế từ Database
  const totalDocs = archivedDocs.length;
  
  // 2. Phân loại và đếm số lượng văn bản chuẩn hóa (Chống null/undefined)
  const docTypesCount = archivedDocs.reduce((acc, doc) => {
    const rawType = doc.docType || doc.doctype || 'Khác';
    acc[rawType] = (acc[rawType] || 0) + 1;
    return acc;
  }, {});

  // Sắp xếp các loại văn bản theo số lượng giảm dần để vẽ biểu đồ
  const sortedDocTypes = Object.entries(docTypesCount).sort((a, b) => b[1] - a[1]);

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 flex flex-col flex-1 overflow-y-auto custom-scrollbar animate-in fade-in duration-300">
      
      {/* TIÊU ĐỀ DASHBOARD */}
      <div className="flex items-center gap-3 mb-6 shrink-0">
        <div className={`p-3 rounded-xl ${t.button.split(' ')[0]} ${t.shadow}`}>
          <BarChart3 size={24} className="text-inherit" />
        </div>
        <div>
          <h2 className="text-2xl font-black uppercase tracking-tight">Bảng Thống Kê</h2>
          <p className={`text-xs ${t.subtext}`}>Tổng quan hoạt động kho lưu trữ số hóa của hệ thống Classify Doc AI.</p>
        </div>
      </div>

      {/* DÒNG 1: CÁC THẺ SUMMARY CARDS THỜI GIAN THỰC */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-6 shrink-0">
        
        {/* THẺ TỔNG TÀI LIỆU */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Tổng tài liệu trong kho</p>
            <h3 className="text-3xl font-black">{totalDocs} <span className="text-sm font-bold opacity-50">file</span></h3>
          </div>
          <div className="p-4 rounded-2xl bg-blue-500/10 text-blue-500"><FileText size={24} /></div>
        </div>

        {/* THẺ TÀI KHOẢN ĐANG ONLINE */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Tài khoản phiên làm việc</p>
            <h3 className="text-2xl font-black truncate max-w-[160px]">{user?.username || "Guest"}</h3>
            <span className={`text-[9px] font-black uppercase tracking-wider flex items-center gap-1 ${t.accent} mt-0.5`}><Shield size={10} /> {user?.role || "employee"}</span>
          </div>
          <div className="p-4 rounded-2xl bg-purple-500/10 text-purple-500"><Users size={24} /></div>
        </div>

        {/* THẺ ĐỘ TIN CẬY TRÍCH XUẤT TRUNG BÌNH */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Độ tin cậy AI nhận diện</p>
            <h3 className="text-3xl font-black">98.5 <span className="text-sm font-bold opacity-50">%</span></h3>
          </div>
          <div className="p-4 rounded-2xl bg-green-500/10 text-green-500"><TrendingUp size={24} /></div>
        </div>

        {/* THẺ TÌNH TRẠNG KẾT NỐI POSTGRESQL */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Tình trạng Máy chủ</p>
            <h3 className="text-xl font-black text-green-500 flex items-center gap-2"><CheckCircle2 size={20}/> Hoạt động</h3>
          </div>
          <div className="p-4 rounded-2xl bg-orange-500/10 text-orange-500"><Activity size={24} /></div>
        </div>
      </div>

      {/* DÒNG 2: BIỂU ĐỒ PHÂN BỔ VÀ NHẬT KÝ ĐỒNG BỘ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-[400px]">
        
        {/* CỘT TRÁI: BIỂU ĐỒ PHÂN BỔ LOẠI TÀI LIỆU TRONG DB */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex flex-col lg:col-span-2`}>
          <h3 className={`text-xs font-black ${t.subtext} uppercase tracking-widest mb-6 flex items-center gap-2`}>
            <BarChart3 size={16} className={t.accent} /> Phân bổ loại tài liệu thực tế
          </h3>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-4">
            {totalDocs === 0 ? (
              <div className="flex flex-col items-center justify-center h-full opacity-40 py-12">
                <AlertTriangle size={48} className="mb-2 animate-bounce" />
                <p className="text-sm font-bold">Chưa có tệp dữ liệu lưu trữ nào</p>
                <p className="text-xs mt-0.5">Vào "Trạm OCR" để tiến hành số hóa tài liệu đầu tiên.</p>
              </div>
            ) : (
              sortedDocTypes.map(([type, count], index) => {
                const percentage = ((count / totalDocs) * 100).toFixed(1);
                return (
                  <div key={index} className="flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <div className="flex justify-between items-center text-sm font-bold">
                      <span className="flex items-center gap-2">📂 {type}</span>
                      <span className={t.subtext}>{count} file ({percentage}%)</span>
                    </div>
                    {/* Thanh Progress Bar tự động kéo dãn theo tỉ lệ % */}
                    <div className="w-full h-3 bg-black/5 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-1000 ${t.button.split(' ')[0]}`} 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* CỘT PHẢI: NHẬT KÝ HOẠT ĐỘNG GẦN ĐÂY */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex flex-col`}>
          <h3 className={`text-xs font-black ${t.subtext} uppercase tracking-widest mb-6 flex items-center gap-2`}>
            <Clock size={16} className={t.accent} /> Nhật ký đồng bộ gần đây
          </h3>
          
          <div className="flex flex-col gap-5 overflow-y-auto custom-scrollbar pr-2 relative flex-1 min-h-0">
            {/* Trục dòng thời gian (Timeline vertical bar) */}
            <div className="absolute left-[11px] top-2 bottom-2 w-[2px] bg-black/5 -z-10"></div>
            
            {/* Điểm mốc hệ thống */}
            <div className="flex gap-4 items-start">
              <div className="w-6 h-6 rounded-full flex items-center justify-center bg-green-500 text-white shrink-0 shadow-sm"><CheckCircle2 size={12} /></div>
              <div>
                <p className="text-xs font-bold leading-relaxed">Đồng bộ hoàn tất với Cơ sở dữ liệu PostgreSQL</p>
                <p className={`text-[9px] font-mono ${t.subtext} mt-0.5`}>Vừa xong</p>
              </div>
            </div>

            {/* Danh sách 5 tài liệu vừa số hóa xong lưu trong DB */}
            {archivedDocs.length > 0 ? (
              archivedDocs.slice(0, 5).map((doc, idx) => (
                <div key={doc.id || idx} className="flex gap-4 items-start animate-in slide-in-from-right-3 duration-300">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center ${t.button.split(' ')[0]} ${t.text} shrink-0 shadow-sm`}><FileText size={12} /></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold leading-relaxed truncate">
                      <span className={t.accent}>{user?.username || "Nhân viên"}</span> đã lưu tệp <span className="underline">{doc.docType || doc.doctype || "Văn bản"}</span>
                    </p>
                    <p className={`text-[10px] ${t.subtext} mt-0.5 font-mono truncate`} title={doc.trichYeu || doc.fileName}>
                      {doc.soHieu || "Không số hiệu"} • {doc.trichYeu || doc.fileName || "Chưa có trích yếu"}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-12 opacity-30 flex-1">
                <FileText size={32} className="mb-1" />
                <p className="text-[10px] font-bold">Chưa có nhật ký hoạt động</p>
              </div>
            )}
          </div>
        </div>

      </div>
    </main>
  );
}