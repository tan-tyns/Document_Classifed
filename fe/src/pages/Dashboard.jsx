import React from 'react';
import { BarChart3, Users, FileText, Activity, TrendingUp, Clock, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function Dashboard({ archivedDocs, user, t }) {
  // Tính toán số liệu thống kê từ Kho lưu trữ thực tế
  const totalDocs = archivedDocs.length;
  
  // Phân loại văn bản
  const docTypesCount = archivedDocs.reduce((acc, doc) => {
    acc[doc.docType] = (acc[doc.docType] || 0) + 1;
    return acc;
  }, {});

  // Sắp xếp các loại văn bản theo số lượng giảm dần
  const sortedDocTypes = Object.entries(docTypesCount).sort((a, b) => b[1] - a[1]);

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 flex flex-col flex-1 overflow-y-auto custom-scrollbar animate-in fade-in duration-300">
      
      <div className="flex items-center gap-3 mb-6 shrink-0">
        <div className={`p-3 rounded-xl ${t.button.split(' ')[0]} ${t.shadow}`}>
          <BarChart3 size={24} className="text-inherit" />
        </div>
        <div>
          <h2 className="text-2xl font-black uppercase tracking-tight">Bảng Thống Kê</h2>
          <p className={`text-xs ${t.subtext}`}>Tổng quan hoạt động hệ thống Classify Doc AI.</p>
        </div>
      </div>

      {/* DÒNG 1: CÁC THẺ SUMMARY CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-6 shrink-0">
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Tổng tài liệu đã lưu</p>
            <h3 className="text-3xl font-black">{totalDocs} <span className="text-sm font-bold opacity-50">file</span></h3>
          </div>
          <div className={`p-4 rounded-2xl bg-blue-500/10 text-blue-500`}><FileText size={24} /></div>
        </div>

        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Người dùng hệ thống</p>
            <h3 className="text-3xl font-black">12 <span className="text-sm font-bold opacity-50">user</span></h3>
          </div>
          <div className={`p-4 rounded-2xl bg-purple-500/10 text-purple-500`}><Users size={24} /></div>
        </div>

        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Tỷ lệ nhận diện thành công</p>
            <h3 className="text-3xl font-black">98.5 <span className="text-sm font-bold opacity-50">%</span></h3>
          </div>
          <div className={`p-4 rounded-2xl bg-green-500/10 text-green-500`}><TrendingUp size={24} /></div>
        </div>

        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex items-center justify-between`}>
          <div>
            <p className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} mb-1`}>Tình trạng Máy chủ</p>
            <h3 className="text-xl font-black text-green-500 flex items-center gap-2"><CheckCircle2 size={20}/> Ổn định</h3>
          </div>
          <div className={`p-4 rounded-2xl bg-orange-500/10 text-orange-500`}><Activity size={24} /></div>
        </div>
      </div>

      {/* DÒNG 2: BIỂU ĐỒ VÀ HOẠT ĐỘNG */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-[400px]">
        
        {/* CỘT TRÁI: Phân bổ loại tài liệu */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex flex-col lg:col-span-2`}>
          <h3 className={`text-xs font-black ${t.subtext} uppercase tracking-widest mb-6 flex items-center gap-2`}>
            <BarChart3 size={16} className={t.accent} /> Phân bổ loại tài liệu
          </h3>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 flex flex-col gap-4">
            {totalDocs === 0 ? (
              <div className="flex flex-col items-center justify-center h-full opacity-50">
                <AlertTriangle size={48} className="mb-2" />
                <p className="text-sm font-bold">Chưa có dữ liệu thống kê</p>
              </div>
            ) : (
              sortedDocTypes.map(([type, count], index) => {
                const percentage = ((count / totalDocs) * 100).toFixed(1);
                return (
                  <div key={index} className="flex flex-col gap-2">
                    <div className="flex justify-between items-center text-sm font-bold">
                      <span>{type}</span>
                      <span className={t.subtext}>{count} file ({percentage}%)</span>
                    </div>
                    {/* Thanh Progress Bar */}
                    <div className="w-full h-3 bg-black/5 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${t.button.split(' ')[0]}`} 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* CỘT PHẢI: Nhật ký hoạt động gần đây */}
        <div className={`${t.panel} p-6 rounded-3xl border ${t.border} shadow-lg flex flex-col`}>
          <h3 className={`text-xs font-black ${t.subtext} uppercase tracking-widest mb-6 flex items-center gap-2`}>
            <Clock size={16} className={t.accent} /> Hoạt động gần đây
          </h3>
          
          <div className="flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2 relative">
            <div className="absolute left-[11px] top-2 bottom-2 w-[2px] bg-black/5 -z-10"></div>
            
            <div className="flex gap-4">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center bg-green-500 text-white shrink-0`}><CheckCircle2 size={12} /></div>
              <div>
                <p className="text-sm font-bold">Hệ thống khởi động thành công</p>
                <p className={`text-[10px] ${t.subtext} mt-0.5`}>Vừa xong</p>
              </div>
            </div>

            {archivedDocs.slice(0, 5).map((doc, idx) => (
              <div key={idx} className="flex gap-4">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center ${t.button.split(' ')[0]} ${t.text} shrink-0`}><FileText size={12} /></div>
                <div>
                  <p className="text-sm font-bold line-clamp-1">{user?.username || "Admin"} đã lưu {doc.docType}</p>
                  <p className={`text-[10px] ${t.subtext} mt-0.5 line-clamp-1`}>{doc.soHieu || "Không số hiệu"}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </main>
  );
}