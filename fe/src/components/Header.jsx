// Header.jsx
import React from 'react';
import { LayoutGrid, Library, LogOut, Settings as SettingsIcon, BarChart3, Users } from 'lucide-react'; // <-- Đã import thêm Users

export default function Header({ 
  user, activeTab, setActiveTab, archivedCount, 
  onLogout, t, currentTheme, setCurrentTheme, themes 
}) {
  return (
    <header className={`${t.panel} border-b ${t.border} px-4 lg:px-8 py-4 flex justify-between items-center shadow-xl sticky top-0 z-40 shrink-0`}>
      <div className="flex items-center gap-3">
        <div className={`${t.button.split(' ')[0]} p-2 rounded-lg ${t.shadow}`}>{t.icon}</div>
        <div className="hidden sm:block">
          <h1 className={`font-black text-xl tracking-tight ${t.accent} uppercase italic`}>Classify Doc AI</h1>
          <p className={`text-[10px] ${t.subtext} font-bold tracking-widest uppercase`}>Xin chào, {user?.username || "Admin"}</p>
        </div>
      </div>

      {/* MENU TABS CẬP NHẬT ĐẦY ĐỦ ĐIỀU HƯỚNG */}
      <div className="flex bg-black/5 p-1 rounded-xl border border-white/10 overflow-x-auto custom-scrollbar max-w-[50vw] sm:max-w-none gap-0.5">
        
        {/* NÚT THỐNG KÊ (DASHBOARD) */}
        <button 
          type="button"
          onClick={() => setActiveTab('dashboard')} 
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'dashboard' ? `${t.panel} shadow-md text-inherit` : `${t.subtext} hover:text-inherit`}`}
        >
          <BarChart3 size={16} /> Tổng quan
        </button>

        {/* NÚT TRẠM OCR */}
        <button 
          type="button"
          onClick={() => setActiveTab('ocr')} 
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'ocr' ? `${t.panel} shadow-md text-inherit` : `${t.subtext} hover:text-inherit`}`}
        >
          <LayoutGrid size={16} /> Trạm OCR
        </button>
        
        {/* NÚT KHO LƯU TRỮ */}
        <button 
          type="button"
          onClick={() => setActiveTab('archive')} 
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'archive' ? `${t.panel} shadow-md text-inherit` : `${t.subtext} hover:text-inherit`}`}
        >
          <Library size={16} /> Kho Lưu Trữ
          {archivedCount > 0 && <span className={`ml-1 px-1.5 py-0.5 rounded-md text-[9px] ${t.button.split(' ')[0]}`}>{archivedCount}</span>}
        </button>

        {/* NÚT DANH SÁCH NHÂN SỰ (MỚI BỔ SUNG) */}
        {user?.role !== 'employee' && (
          <button 
            type="button"
            onClick={() => setActiveTab('employees')} 
            className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'employees' ? `${t.panel} shadow-md text-inherit` : `${t.subtext} hover:text-inherit`}`}
          >
            <Users size={16} /> Nhân sự
          </button>
        )}

        {/* NÚT CÀI ĐẶT */}
        <button 
          type="button"
          onClick={() => setActiveTab('settings')} 
          className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${activeTab === 'settings' ? `${t.panel} shadow-md text-inherit` : `${t.subtext} hover:text-inherit`}`}
        >
          <SettingsIcon size={16} /> Cài đặt
        </button>
      </div>

      {/* KHU VỰC THAY ĐỔI THEME & ĐĂNG XUẤT */}
      <div className="flex items-center gap-4">
        <div className="hidden md:flex items-center gap-2 bg-black/10 p-1.5 rounded-full border border-white/5">
          {Object.keys(themes).map((key) => (
            <button 
              key={key} 
              type="button"
              onClick={() => setCurrentTheme(key)} 
              className={`w-5 h-5 rounded-full border-2 transition-transform ${currentTheme === key ? 'scale-125 border-white shadow-md' : 'border-transparent opacity-40 hover:opacity-100'}`} 
              style={{ backgroundColor: themes[key].button.split(' ')[0].replace('bg-[', '').replace(']', '') }} 
            />
          ))}
        </div>
        
        <button type="button" onClick={onLogout} className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold text-red-500 hover:bg-red-500/10 transition-colors">
          <LogOut size={14} className="hidden lg:block" /> Đăng xuất
        </button>
      </div>
    </header>
  );
}