import React, { useState, useEffect } from 'react';
import { User, Lock, Palette, Save, CheckCircle2, Shield, Calendar, Activity, Mail, Phone, MapPin } from 'lucide-react';

export default function Settings({ user, setUser, t, currentTheme, setCurrentTheme, themes }) {
  const [activeMenu, setActiveMenu] = useState('profile'); // profile, security, appearance
  const [savedStatus, setSavedStatus] = useState(false);

  // Form states - Map toàn bộ các trường dữ liệu từ database truyền vào thông qua prop user
  const [profileForm, setProfileForm] = useState({ 
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || '',
    date_of_birth: user?.date_of_birth || '',
    phone_number: user?.phone_number || '',
    gender: user?.gender || 'Khác',
    address: user?.address || ''
  });
  
  const [passwordForm, setPasswordForm] = useState({ current: '', new: '', confirm: '' });

  // Đồng bộ lại dữ liệu form khi Object user từ component cha thay đổi (ví dụ sau khi login thành công)
  useEffect(() => {
    if (user) {
      setProfileForm({ 
        username: user.username,
        email: user.email,
        full_name: user.full_name || '',
        date_of_birth: user.date_of_birth || '',
        phone_number: user.phone_number || '',
        gender: user.gender || 'Khác',
        address: user.address || ''
      });
    }
  }, [user]);

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/users/${user.id}/avatar`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Không thể upload ảnh");

      // Cập nhật lại state user của App để hiển thị ảnh mới trên toàn hệ thống
      setUser({ ...user, avatar_url: data.avatar_url });
      alert("✅ Cập nhật ảnh đại diện thành công!");
    } catch (error) {
      alert("❌ Lỗi: " + error.message);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    const API_BASE_URL = "http://localhost:8000";
    
    if (activeMenu === 'profile') {
      if (!profileForm.full_name.trim() || !profileForm.email.trim()) {
        alert("❌ Họ tên thật và địa chỉ Email không được phép để trống!");
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/users/${user.id}/profile`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: profileForm.email,
            full_name: profileForm.full_name,
            date_of_birth: profileForm.date_of_birth || null,
            phone_number: profileForm.phone_number,
            gender: profileForm.gender,
            address: profileForm.address
          })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Cập nhật hồ sơ thất bại");

        setUser({ ...user, ...profileForm });
        setSavedStatus(true);
        setTimeout(() => setSavedStatus(false), 2000);
      } catch (error) {
        alert("❌ Lỗi: " + error.message);
      }
    }

    if (activeMenu === 'security') {
      if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
        alert("❌ Vui lòng nhập đầy đủ thông tin mật khẩu!");
        return;
      }
      if (passwordForm.new !== passwordForm.confirm) {
        alert("❌ Mật khẩu mới và mật khẩu xác nhận không trùng khớp!");
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/users/${user.id}/password`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            current_password: passwordForm.current,
            new_password: passwordForm.new
          })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Đổi mật khẩu thất bại");

        alert("✅ Đổi mật khẩu thành công!");
        setPasswordForm({ current: '', new: '', confirm: '' });
        setSavedStatus(true);
        setTimeout(() => setSavedStatus(false), 2000);
      } catch (error) {
        alert("❌ Lỗi: " + error.message);
      }
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Chưa rõ";
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  return (
    <main className="max-w-[1200px] w-full mx-auto p-4 lg:p-8 flex-1 flex flex-col md:flex-row gap-6 lg:gap-8 overflow-hidden min-h-0 animate-in fade-in duration-300">
      
      {/* CỘT TRÁI: MENU CHUYỂN TAB */}
      <aside className={`w-full md:max-w-[260px] ${t.panel} rounded-3xl border ${t.border} p-5 shadow-2xl shrink-0 flex flex-row md:flex-col gap-1.5 overflow-x-auto md:overflow-x-visible custom-scrollbar`}>
        <div className="hidden md:block px-3 mb-3">
          <h2 className={`text-[10px] font-black ${t.subtext} uppercase tracking-widest`}>Hệ thống chung</h2>
        </div>
        
        <button type="button" onClick={() => setActiveMenu('profile')} className={`flex items-center justify-center md:justify-start gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all whitespace-nowrap flex-1 md:flex-none ${activeMenu === 'profile' ? `${t.button.split(' ')[0]} ${t.shadow}` : `hover:bg-black/5 ${t.subtext}`}`}>
          <User size={18} /> <span className="text-xs md:text-sm">Hồ sơ cá nhân</span>
        </button>
        <button type="button" onClick={() => setActiveMenu('security')} className={`flex items-center justify-center md:justify-start gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all whitespace-nowrap flex-1 md:flex-none ${activeMenu === 'security' ? `${t.button.split(' ')[0]} ${t.shadow}` : `hover:bg-black/5 ${t.subtext}`}`}>
          <Lock size={18} /> <span className="text-xs md:text-sm">Bảo mật</span>
        </button>
        <button type="button" onClick={() => setActiveMenu('appearance')} className={`flex items-center justify-center md:justify-start gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all whitespace-nowrap flex-1 md:flex-none ${activeMenu === 'appearance' ? `${t.button.split(' ')[0]} ${t.shadow}` : `hover:bg-black/5 ${t.subtext}`}`}>
          <Palette size={18} /> <span className="text-xs md:text-sm">Giao diện</span>
        </button>
      </aside>

      {/* CỘT PHẢI: CHI TIẾT NỘI DUNG TỪNG TAB */}
      <div className={`${t.panel} rounded-3xl border ${t.border} p-6 lg:p-8 flex-1 shadow-2xl overflow-y-auto custom-scrollbar flex flex-col`}>
        
        {/* === 1. TAB HỒ SƠ CÁ NHÂN === */}
        {activeMenu === 'profile' && (
          <form onSubmit={handleSave} className="w-full flex flex-col gap-6 animate-in slide-in-from-right-4 duration-300">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Hồ sơ cá nhân</h2>
              <p className={`text-xs ${t.subtext} mt-1`}>Thông tin nhân sự kết nối đồng bộ tới cơ sở dữ liệu hệ thống.</p>
            </div>

            {/* AVATAR & THÔNG TIN HỆ THỐNG GỘP CHUNG 1 DÒNG TỐI ƯU KHÔNG GIAN */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center bg-black/5 border border-white/5 p-5 rounded-2xl">
              <div className="flex flex-col items-center gap-2 lg:border-r border-dashed border-white/10 pr-0 lg:pr-4">
                <div className="relative group cursor-pointer w-20 h-20 shadow-md rounded-full">
                  <img 
                    src={user.avatar_url || `https://ui-avatars.com/api/?name=${user.username}&background=random&size=150`} 
                    alt="Avatar" 
                    className="w-20 h-20 rounded-full object-cover border-4 border-current transition-transform group-hover:scale-105"
                  />
                  <label htmlFor="avatar-upload" className="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center text-white text-[10px] font-black uppercase opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer">
                    Thay đổi
                  </label>
                  <input id="avatar-upload" type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
                </div>
                <span className="text-[10px] opacity-40 font-mono">Định dạng: JPG, PNG</span>
              </div>

              <div className="lg:col-span-2 grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
                <div className="flex flex-col">
                  <span className={`text-[9px] font-black uppercase tracking-widest ${t.subtext} mb-0.5`}>Mã định danh (UID)</span>
                  <span className="font-mono font-bold opacity-70">#{user?.id || 'N/A'}</span>
                </div>
                <div className="flex flex-col">
                  <span className={`text-[9px] font-black uppercase tracking-widest ${t.subtext} mb-0.5`}>Tên tài khoản</span>
                  <span className="font-mono font-bold opacity-70">{profileForm.username}</span>
                </div>
                <div className="flex flex-col">
                  <span className={`text-[9px] font-black uppercase tracking-widest ${t.subtext} mb-0.5`}>Chức vụ / Quyền hạn</span>
                  <span className={`font-black uppercase flex items-center gap-1 ${t.accent}`}><Shield size={12} /> {user?.role || 'employee'}</span>
                </div>
                <div className="flex flex-col">
                  <span className={`text-[9px] font-black uppercase tracking-widest ${t.subtext} mb-0.5`}>Trạng thái máy chủ</span>
                  <span className="font-bold text-green-500 flex items-center gap-1"><Activity size={12} /> {user?.is_active !== false ? 'Đang hoạt động' : 'Bị khóa'}</span>
                </div>
                <div className="flex flex-col col-span-2 border-t border-white/5 pt-2 mt-1">
                  <span className={`text-[9px] font-black uppercase tracking-widest ${t.subtext} mb-0.5`}>Ngày khởi tạo thành viên</span>
                  <span className="font-bold flex items-center gap-1 opacity-60"><Calendar size={12} /> {formatDate(user?.created_at)}</span>
                </div>
              </div>
            </div>
            
            {/* PHÂN VÙNG NHẬP LIỆU CHI TIẾT */}
            <div className="flex flex-col gap-4">
              <h3 className={`text-[10px] font-black uppercase tracking-widest border-l-4 pl-2 ${t.accent.split(' ')[0]}`}>Thông tin lý lịch</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Họ và tên thật</label>
                  <div className="relative">
                    <User size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 opacity-40" />
                    <input type="text" value={profileForm.full_name} onChange={(e) => setProfileForm({...profileForm, full_name: e.target.value})} className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-sm font-bold`} placeholder="Nguyễn Văn A" />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Giới tính</label>
                  <select value={profileForm.gender} onChange={(e) => setProfileForm({...profileForm, gender: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-sm font-bold cursor-pointer`}>
                    <option value="Nam">Nam</option>
                    <option value="Nữ">Nữ</option>
                    <option value="Khác">Khác</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1.5 col-span-1 sm:col-span-2">
                  <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Ngày sinh</label>
                  <input type="date" value={profileForm.date_of_birth} onChange={(e) => setProfileForm({...profileForm, date_of_birth: e.target.value})} className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-sm font-bold`} />
                </div>
              </div>

              <h3 className={`text-[10px] font-black uppercase tracking-widest border-l-4 pl-2 ${t.accent.split(' ')[0]} mt-2`}>Thông tin liên hệ</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5 col-span-2 sm:col-span-1">
                  <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Số điện thoại liên lạc</label>
                  <div className="relative">
                    <Phone size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 opacity-40" />
                    <input type="text" value={profileForm.phone_number} onChange={(e) => setProfileForm({...profileForm, phone_number: e.target.value})} className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-sm font-bold`} placeholder="0912xxxxxx" />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5 col-span-2 sm:col-span-1">
                  <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Địa chỉ Email công vụ</label>
                  <div className="relative">
                    <Mail size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 opacity-40" />
                    <input type="email" value={profileForm.email} onChange={(e) => setProfileForm({...profileForm, email: e.target.value})} className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-sm font-bold`} placeholder="name@company.com" />
                  </div>
                </div>

                <div className="flex flex-col gap-1.5 col-span-2">
                  <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Địa chỉ cư trú hiện tại</label>
                  <div className="relative">
                    <MapPin size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 opacity-40" />
                    <input type="text" value={profileForm.address} onChange={(e) => setProfileForm({...profileForm, address: e.target.value})} className={`w-full pl-10 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none text-sm font-bold`} placeholder="Số nhà, Tên đường, Tỉnh / Thành phố..." />
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-black/5 flex justify-end">
              <button type="submit" className={`px-8 py-3 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}>
                {savedStatus ? <><CheckCircle2 size={18} /> Đã lưu</> : <><Save size={18} /> Cập nhật hồ sơ</>}
              </button>
            </div>
          </form>
        )}

        {/* === 2. TAB ĐỔI MẬT KHẨU === */}
        {activeMenu === 'security' && (
          <form onSubmit={handleSave} className="w-full max-w-xl flex flex-col gap-6 source-file animate-in slide-in-from-right-4 duration-300">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Đổi mật khẩu</h2>
              <p className={`text-xs ${t.subtext} mt-1`}>Đảm bảo tài khoản hệ thống của bạn đang được cấu hình mật khẩu độ bảo mật cao.</p>
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Mật khẩu hiện tại</label>
              <input type="password" placeholder="••••••••" value={passwordForm.current} onChange={(e) => setPasswordForm({...passwordForm, current: e.target.value})} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} />
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Mật khẩu mới</label>
              <input type="password" placeholder="••••••••" value={passwordForm.new} onChange={(e) => setPasswordForm({...passwordForm, new: e.target.value})} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} />
            </div>

            <div className="flex flex-col gap-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext}`}>Xác nhận lại mật khẩu mới</label>
              <input type="password" placeholder="••••••••" value={passwordForm.confirm} onChange={(e) => setPasswordForm({...passwordForm, confirm: e.target.value})} className={`w-full px-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} />
            </div>

            <div className="pt-4 mt-2 border-t border-black/5 flex justify-end">
              <button type="submit" className={`px-8 py-3 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}>
                {savedStatus ? <><CheckCircle2 size={18} /> Đã cập nhật</> : <><Save size={18} /> Thay đổi mật khẩu</>}
              </button>
            </div>
          </form>
        )}

        {/* === 3. TAB CÁ NHÂN HÓA GIAO DIỆN === */}
        {activeMenu === 'appearance' && (
          <div className="w-full flex flex-col gap-6 animate-in slide-in-from-right-4 duration-300">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Cá nhân hóa giao diện</h2>
              <p className={`text-xs ${t.subtext} mt-1`}>Chọn hệ màu chủ đạo yêu thích cho bảng làm việc số hóa của bạn.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
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