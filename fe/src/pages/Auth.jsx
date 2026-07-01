import React, { useState } from 'react';
import { User, Lock, Mail } from 'lucide-react';

export default function Auth({ onLogin, t, showToast }) {
  const [authMode, setAuthMode] = useState('login'); 
  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setAuthForm({ ...authForm, [e.target.name]: e.target.value });

// Auth.jsx (Rút gọn phần logic handleSubmit)
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const API_BASE_URL = "http://localhost:8000";

    try {
      if (authMode === 'login') {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: authForm.username, password: authForm.password })
        });

        const data = await response.json();
        if (!response.ok) {
          showToast(data.detail || "❌ Tài khoản hoặc mật khẩu không chính xác!", "error");
          setLoading(false);
          return;
        }

        // 🔥 ĐÃ XÓA ALERT ĐĂNG NHẬP THÀNH CÔNG THEO YÊU CẦU
        onLogin(data.user); 

      } else {
        if (!authForm.email) {
          alert("Vui lòng điền thêm Email để đăng ký!");
          setLoading(false);
          return;
        }

        const response = await fetch(`${API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: authForm.username,
            email: authForm.email,
            password: authForm.password,
            role: authForm.role || 'employee' // Mặc định nếu không chọn là nhân viên
          })
        });

        const data = await response.json();
        if (!response.ok){
          showToast(data.detail || "❌ Đăng ký tài khoản thất bại!", "error");
        } else {
          showToast("🎉 Tạo tài khoản thành công! Bạn có thể đăng nhập ngay.", "success");
          setAuthMode('login');
        }
      }
    } catch (error) {
      alert("Lỗi: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen ${t.bg} ${t.text} flex items-center justify-center p-4 font-sans transition-all duration-500`}>
      <div className={`${t.panel} w-full max-w-md p-8 rounded-3xl shadow-2xl border ${t.border} animate-in fade-in zoom-in duration-300`}>
        <div className="flex flex-col items-center mb-8">
          <div className={`${t.button.split(' ')[0]} p-4 rounded-2xl mb-4 ${t.shadow}`}>{t.icon}</div>
          <h1 className={`text-2xl font-black uppercase tracking-widest ${t.accent} italic`}>Classify Doc AI</h1>
          <p className={`text-xs font-bold tracking-widest uppercase mt-2 ${t.subtext}`}>Hệ thống Số hóa Văn bản</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} ml-1`}>Tài khoản</label>
            <div className="relative">
              <User size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 opacity-40`} />
              <input type="text" name="username" required value={authForm.username} onChange={handleChange} className={`w-full pl-11 pr-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} placeholder="Nhập tên đăng nhập" />
            </div>
          </div>
          
          {authMode === 'register' && (
            <div className="flex flex-col gap-1.5 animate-in slide-in-from-top-2">
              <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} ml-1`}>Email</label>
              <div className="relative">
                <Mail size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 opacity-40`} />
                <input type="email" name="email" required={authMode === 'register'} value={authForm.email} onChange={handleChange} className={`w-full pl-11 pr-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} placeholder="name@company.com" />
              </div>
            </div>
          )}
          
          <div className="flex flex-col gap-1.5">
            <label className={`text-[10px] font-bold uppercase tracking-widest ${t.subtext} ml-1`}>Mật khẩu</label>
            <div className="relative">
              <Lock size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 opacity-40`} />
              <input type="password" name="password" required value={authForm.password} onChange={handleChange} className={`w-full pl-11 pr-4 py-3 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-sm font-bold`} placeholder="••••••••" />
            </div>
          </div>
          
          <button type="submit" disabled={loading} className={`mt-4 w-full py-4 ${t.button} font-black rounded-xl ${t.shadow} transition-transform active:scale-95 text-sm uppercase tracking-widest flex justify-center items-center gap-2 disabled:opacity-50`}>
            {loading ? "Đang xử lý..." : (authMode === 'login' ? "Đăng Nhập" : "Tạo Tài Khoản")}
          </button>
        </form>
        
        <div className="mt-8 text-center">
          <button onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')} className={`text-xs font-bold ${t.subtext} hover:${t.accent.split('-')[1]} transition-colors`}>
            {authMode === 'login' ? "Chưa có tài khoản? Đăng ký ngay" : "Đã có tài khoản? Quay lại Đăng nhập"}
          </button>
        </div>
      </div>
    </div>
  );
}