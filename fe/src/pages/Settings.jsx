import React, { useState } from 'react';
import { User, Lock, Palette, Save, CheckCircle2 } from 'lucide-react';

export default function Settings({ user, setUser, t, currentTheme, setCurrentTheme, themes }) {
  const [activeMenu, setActiveMenu] = useState('profile'); // profile, security, appearance
  const [savedStatus, setSavedStatus] = useState(false);

  // Form states
  const [profileForm, setProfileForm] = useState({ username: user.username, email: user.email });
  const [passwordForm, setPasswordForm] = useState({ current: '', new: '', confirm: '' });

  const handleSave = (e) => {
    e.preventDefault();
    if (activeMenu === 'profile') setUser({ ...user, ...profileForm });
    
    // Hiệu ứng lưu thành công
    setSavedStatus(true);
    setTimeout(() => setSavedStatus(false), 2000);
  };

  return (
    <main className="max-w-[1200px] w-full mx-auto p-4 lg:p-8 flex-1 flex gap-6 lg:gap-8 overflow-hidden min-h-0 animate-in fade-in duration-300">
      
      {/* CỘT TRÁI: MENU CÀI ĐẶT */}
      <aside className={`w-full max-w-[250px] ${t.panel} rounded-3xl border ${t.border} p-6 shadow-2xl shrink-0 hidden md:flex flex-col gap-2`}>
        <h2 className={`text-xs font-black ${t.subtext} uppercase tracking-widest mb-4`}>Cài đặt chung</h2>
        
        <button onClick={() => setActiveMenu('profile')} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeMenu === 'profile' ? `${t.button.split(' ')[0]} ${t.shadow}` : `hover:bg-black/5 ${t.subtext}`}`}>
          <User size={18} /> Hồ sơ cá nhân
        </button>
        <button onClick={() => setActiveMenu('security')} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeMenu === 'security' ? `${t.button.split(' ')[0]} ${t.shadow}` : `hover:bg-black/5 ${t.subtext}`}`}>
          <Lock size={18} /> Bảo mật
        </button>
        <button onClick={() => setActiveMenu('appearance')} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${activeMenu === 'appearance' ? `${t.button.split(' ')[0]} ${t.shadow}` : `hover:bg-black/5 ${t.subtext}`}`}>
          <Palette size={18} /> Giao diện
        </button>
      </aside>

      {/* CỘT PHẢI: NỘI DUNG FORM */}
      <div className={`${t.panel} rounded-3xl border ${t.border} p-6 lg:p-10 flex-1 shadow-2xl overflow-y-auto custom-scrollbar`}>
        
        {/* === 1. HỒ SƠ CÁ NHÂN === */}
        {activeMenu === 'profile' && (
          <form onSubmit={handleSave} className="max-w-xl flex flex-col gap-6 animate-in slide-in-from-right-4 duration-300">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Hồ sơ cá nhân</h2>
              <p className={`text-xs ${t.subtext} mt-1`}>Cập nhật thông tin hiển thị trên hệ thống của bạn.</p>
            </div>
            
            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Tên hiển thị</label>
              <div className="relative">
                <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 opacity-40" />
                <input 
                  type="text" value={profileForm.username} onChange={(e) => setProfileForm({...profileForm, username: e.target.value})}
                  className={`w-full pl-11 pr-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all font-bold`} 
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Địa chỉ Email</label>
              <div className="relative">
                <input 
                  type="email" value={profileForm.email} onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                  className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all font-bold`} 
                />
              </div>
            </div>

            <div className="pt-4 mt-2 border-t border-black/5 flex justify-end">
              <button type="submit" className={`px-8 py-3 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}>
                {savedStatus ? <><CheckCircle2 size={18} /> Đã lưu</> : <><Save size={18} /> Cập nhật</>}
              </button>
            </div>
          </form>
        )}

        {/* === 2. BẢO MẬT === */}
        {activeMenu === 'security' && (
          <form onSubmit={handleSave} className="max-w-xl flex flex-col gap-6 animate-in slide-in-from-right-4 duration-300">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Đổi mật khẩu</h2>
              <p className={`text-xs ${t.subtext} mt-1`}>Đảm bảo tài khoản của bạn đang sử dụng mật khẩu an toàn.</p>
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Mật khẩu hiện tại</label>
              <input type="password" placeholder="••••••••" value={passwordForm.current} onChange={(e) => setPasswordForm({...passwordForm, current: e.target.value})} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all`} />
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Mật khẩu mới</label>
              <input type="password" placeholder="••••••••" value={passwordForm.new} onChange={(e) => setPasswordForm({...passwordForm, new: e.target.value})} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all`} />
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Xác nhận mật khẩu mới</label>
              <input type="password" placeholder="••••••••" value={passwordForm.confirm} onChange={(e) => setPasswordForm({...passwordForm, confirm: e.target.value})} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all`} />
            </div>

            <div className="pt-4 mt-2 border-t border-black/5 flex justify-end">
              <button type="submit" className={`px-8 py-3 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}>
                {savedStatus ? <><CheckCircle2 size={18} /> Đã cập nhật</> : <><Save size={18} /> Đổi mật khẩu</>}
              </button>
            </div>
          </form>
        )}

        {/* === 3. GIAO DIỆN === */}
        {activeMenu === 'appearance' && (
          <div className="max-w-xl flex flex-col gap-6 animate-in slide-in-from-right-4 duration-300">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Cá nhân hóa giao diện</h2>
              <p className={`text-xs ${t.subtext} mt-1`}>Chọn màu sắc yêu thích cho không gian làm việc của bạn.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
              {Object.keys(themes).map((key) => {
                const isSelected = currentTheme === key;
                const themeData = themes[key];
                return (
                  <div 
                    key={key} 
                    onClick={() => setCurrentTheme(key)}
                    className={`cursor-pointer p-4 rounded-2xl border-2 transition-all flex flex-col gap-3 ${isSelected ? `border-current shadow-lg ${themeData.button.split(' ')[0]}` : `${t.border} hover:bg-black/5`}`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`font-black uppercase tracking-widest text-sm ${isSelected ? 'text-inherit' : t.text}`}>{themeData.name}</span>
                      {isSelected && <CheckCircle2 size={18} className="text-inherit" />}
                    </div>
                    {/* Bảng màu preview */}
                    <div className="flex gap-2">
                      <div className="w-8 h-8 rounded-full shadow-inner" style={{ backgroundColor: themeData.button.split(' ')[0].replace('bg-[', '').replace(']', '') }}></div>
                      <div className="w-8 h-8 rounded-full shadow-inner" style={{ backgroundColor: themeData.bg.replace('bg-[', '').replace(']', '') }}></div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}