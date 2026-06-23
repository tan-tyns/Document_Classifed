// src/pages/Employees.jsx
import React, { useState, useEffect } from 'react';
import { Users, Search, ShieldCheck, Mail, Phone, MapPin, Calendar, CheckCircle, XCircle } from 'lucide-react';

export default function Employees({ user, t }) {
  const [employees, setEmployees] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('ALL');

  // Tự động fetch danh sách nhân viên từ Backend khi mở trang
  useEffect(() => {
  const fetchEmployees = async () => {
    try {
      const response = await fetch(`http://localhost:8000/users`); // Gọi thẳng endpoint sạch
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setEmployees(data);
    } catch (error) {
      console.error("Lỗi kết nối API danh sách nhân viên:", error);
    }
  };
  fetchEmployees();
}, []);

  // Bộ lọc tìm kiếm theo Tên thật, Username, Email, Số điện thoại và Vai trò
  const filteredEmployees = employees.filter(emp => {
    const matchesRole = filterRole === 'ALL' || emp.role.toLowerCase() === filterRole.toLowerCase();
    
    const searchLower = searchQuery.toLowerCase();
    const matchesSearch = 
      (emp.fullName || '').toLowerCase().includes(searchLower) ||
      (emp.username || '').toLowerCase().includes(searchLower) ||
      (emp.email || '').toLowerCase().includes(searchLower) ||
      (emp.phoneNumber || '').toLowerCase().includes(searchLower);

    return matchesRole && matchesSearch;
  });

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === "Chưa cập nhật") return "Chưa rõ";
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 flex flex-col flex-1 overflow-hidden min-h-0 animate-in fade-in duration-300">
      <div className={`${t.panel} rounded-3xl ${t.border} border p-6 flex-1 flex flex-col shadow-2xl overflow-hidden min-h-0`}>
        
        {/* TIÊU ĐỀ TRANG */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 shrink-0 border-b pb-4 border-white/5 w-full">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl ${t.button.split(' ')[0]} ${t.shadow}`}>
              <Users size={24} className="text-inherit" />
            </div>
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Danh Sách Nhân Sự</h2>
              <p className={`text-xs ${t.subtext}`}>Quản lý và hiển thị thông tin thành viên trong hệ thống Classify Doc AI.</p>
            </div>
          </div>

          {/* SỐ LƯỢNG BADGE */}
          <div className="bg-black/5 border border-white/5 px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap self-end sm:self-auto">
            Tổng số nhân sự: <span className={t.accent}>{employees.length} thành viên</span>
          </div>
        </div>

        {/* THANH BỘ LỌC TÌM KIẾM NHANH */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6 shrink-0">
          <div className="relative flex-1">
            <Search size={16} className={`absolute left-4 top-1/2 -translate-y-1/2 ${t.subtext}`} />
            <input 
              type="text" 
              value={searchQuery} 
              onChange={(e) => setSearchQuery(e.target.value)} 
              placeholder="Tìm theo họ tên, tên đăng nhập, email, số điện thoại..." 
              className={`w-full pl-11 pr-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-xs font-bold`} 
            />
          </div>
          
          <div className="w-full sm:w-48">
            <select 
              value={filterRole} 
              onChange={(e) => setFilterRole(e.target.value)} 
              className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} outline-none focus:ring-2 focus:ring-opacity-50 transition-all text-xs font-black cursor-pointer`}
            >
              <option value="ALL">Tất cả chức vụ</option>
              <option value="admin">Quản trị viên (Admin)</option>
              <option value="manager">Trưởng phòng (Manager)</option>
              <option value="employee">Nhân viên (Employee)</option>
            </select>
          </div>
        </div>

        {/* LƯỚI CARD HIỂN THỊ DANH SÁCH NHÂN VIÊN */}
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
          {filteredEmployees.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredEmployees.map((emp) => (
                <div key={emp.id} className="flex flex-col bg-black/5 rounded-2xl border border-white/5 p-5 relative overflow-hidden group hover:shadow-xl hover:border-current/20 transition-all duration-300">
                  
                  {/* ĐẦU CARD: AVATAR & HỌ TÊN VÀ CHỨC VỤ */}
                  <div className="flex gap-4 items-center mb-4">
                    <img 
                      src={emp.avatarUrl || `https://ui-avatars.com/api/?name=${emp.fullName}&background=random&size=150`} 
                      alt="Avatar" 
                      className="w-16 h-16 rounded-full object-cover border-2 border-current shadow-md shrink-0"
                    />
                    <div className="min-w-0">
                      <h3 className="font-black text-base truncate" title={emp.fullName}>{emp.fullName}</h3>
                      <p className={`text-[10px] font-mono opacity-50`}>@{emp.username} (UID: #{emp.id})</p>
                      
                      {/* BADGE QUYỀN HẠN */}
                      <span className={`text-[9px] font-black uppercase tracking-wider inline-flex items-center gap-1 mt-1.5 ${
                        emp.role === 'admin' ? 'text-red-500 bg-red-500/10' : emp.role === 'manager' ? 'text-amber-500 bg-amber-500/10' : 'text-blue-500 bg-blue-500/10'
                      } px-2 py-0.5 rounded-md`}>
                        <ShieldCheck size={10} /> {emp.role}
                      </span>
                    </div>
                  </div>

                  {/* THÂN CARD: THÔNG TIN CHI TIẾT */}
                  <div className="flex flex-col gap-2 text-xs border-t border-dashed border-white/5 pt-3 mt-1 flex-1">
                    <div className="flex items-center gap-2">
                      <Mail size={12} className="opacity-40 shrink-0" />
                      <span className="truncate opacity-75">{emp.email}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Phone size={12} className="opacity-40 shrink-0" />
                      <span className="opacity-75">{emp.phoneNumber}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin size={12} className="opacity-40 shrink-0" />
                      <span className="truncate opacity-75" title={emp.address}>{emp.address}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar size={12} className="opacity-40 shrink-0" />
                      <span className="opacity-60">Gia nhập: {formatDate(emp.createdAt)}</span>
                    </div>
                  </div>

                  {/* THÈ TRẠNG THÁI GÓC PHẢI CARD */}
                  <div className="absolute top-4 right-4">
                    {emp.isActive ? (
                      <span className="text-green-500 flex items-center gap-0.5 text-[10px] font-bold bg-green-500/10 px-2 py-0.5 rounded-full"><CheckCircle size={10}/> Online</span>
                    ) : (
                      <span className="text-gray-500 flex items-center gap-0.5 text-[10px] font-bold bg-black/10 px-2 py-0.5 rounded-full"><XCircle size={10}/> Offline</span>
                    )}
                  </div>

                </div>
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center opacity-40 py-12">
              <Users size={64} className="mb-4 text-dashed animate-pulse" />
              <h3 className="text-base font-black uppercase tracking-widest">Không tìm thấy thành viên phù hợp</h3>
              <p className="text-xs mt-1">Vui lòng điều chỉnh lại từ khóa hoặc bộ lọc quyền hạn cấp bậc phía trên.</p>
            </div>
          )}
        </div>

      </div>
    </main>
  );
}