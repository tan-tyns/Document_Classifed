// src/pages/Employees.jsx
import React, { useState, useEffect } from 'react';
import { Users, Search, ShieldCheck, Mail, Phone, MapPin, Calendar, CheckCircle, XCircle, Edit3, X, Save, Lock, Trash2 } from 'lucide-react';

export default function Employees({ user, t, showToast }) {
  const [employees, setEmployees] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterRole, setFilterRole] = useState('ALL');

  const [editingEmp, setEditingEmp] = useState(null);
  const [editForm, setEditForm] = useState({
    fullName: '', email: '', phoneNumber: '', address: '', role: 'employee'
  });

  const fetchEmployees = async () => {
    try {
      const response = await fetch(`http://localhost:8000/users`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setEmployees(data);
    } catch (error) {
      console.error("Lỗi kết nối API danh sách nhân viên:", error);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  if (user?.role === 'employee') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full animate-in fade-in">
        <Lock size={64} className="text-red-500/50 mb-4" />
        <h2 className="text-2xl font-black uppercase tracking-widest text-red-500">Từ chối truy cập</h2>
        <p className={`${t.subtext} mt-2 font-bold`}>Bạn không có quyền hạn để xem trang Quản lý nhân sự.</p>
      </div>
    );
  }

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

  const handleEditClick = (emp) => {
    setEditingEmp(emp);
    setEditForm({
      fullName: emp.fullName || '',
      email: emp.email || '',
      phoneNumber: emp.phoneNumber || '',
      address: emp.address || '',
      role: emp.role || 'employee'
    });
  };

  const handleFormChange = (e) => {
    setEditForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSaveEdit = async () => {
    // Kiểm tra showToast có tồn tại không
    if (typeof showToast !== 'function') {
      console.error("showToast is not a function");
      alert("Không thể hiển thị thông báo. Vui lòng kiểm tra console.");
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/admin/users/${editingEmp.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...editForm,
          requestByRole: user?.role
        })
      });

      const data = await response.json();

      if (response.ok) {
        showToast("Cập nhật thông tin nhân viên thành công!", "success");
        setEditingEmp(null);
        fetchEmployees();
      } else {
        // Lấy thông báo lỗi từ server
        const errorMsg = data.detail || "Cập nhật thất bại. Vui lòng thử lại.";
        showToast(errorMsg, "error");
      }
    } catch (error) {
      console.error("Lỗi khi cập nhật nhân viên:", error);
      showToast("Lỗi kết nối đến máy chủ", "error");
    }
  };

  // HÀM XỬ LÝ XÓA NHÂN VIÊN
  const handleDeleteEmployee = async (empId, empUsername) => {
    if (user?.role !== 'admin') return;
    
    // Ngăn admin tự xóa chính mình
    if (empId === user?.id) {
      showToast("Bạn không thể tự xóa tài khoản của chính mình!", "error");
      return;
    }

    if (!window.confirm(`⚠️ BẠN CÓ CHẮC CHẮN MUỐN XÓA TÀI KHOẢN @${empUsername}?\n\nHành động này sẽ xóa hoàn toàn nhân viên khỏi hệ thống (các văn bản họ đã up vẫn sẽ được giữ lại trong kho).`)) return;

    try {
      const response = await fetch(`http://localhost:8000/admin/users/${empId}?requesterRole=${user?.role}`, {
        method: 'DELETE'
      });

      const data = await response.json();

      if (response.ok) {
        showToast(`Đã xóa nhân viên @${empUsername} thành công!`, "success");
        fetchEmployees();
      } else {
        const errorMsg = data.detail || "Xóa thất bại. Vui lòng thử lại.";
        showToast(errorMsg, "error");
      }
    } catch (error) {
      console.error("Lỗi khi xóa nhân viên:", error);
      showToast("Lỗi kết nối đến máy chủ", "error");
    }
  };

  return (
    <main className="max-w-[1600px] w-full mx-auto p-4 lg:p-6 flex flex-col flex-1 overflow-hidden min-h-0 animate-in fade-in duration-300 relative">
      <div className={`${t.panel} rounded-3xl ${t.border} border p-6 flex-1 flex flex-col shadow-2xl overflow-hidden min-h-0`}>
        
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 shrink-0 border-b pb-4 border-white/5 w-full">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl ${t.button.split(' ')[0]} ${t.shadow}`}>
              <Users size={24} className="text-inherit" />
            </div>
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight">Danh Sách Nhân Sự</h2>
              <p className={`text-xs ${t.subtext}`}>Quản lý và hiển thị thông tin thành viên (Quyền hiện tại: <span className="font-bold text-orange-500">{user?.role}</span>).</p>
            </div>
          </div>
          <div className="bg-black/5 border border-white/5 px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap self-end sm:self-auto">
            Tổng số nhân sự: <span className={t.accent}>{employees.length} thành viên</span>
          </div>
        </div>

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

        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
          {filteredEmployees.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {filteredEmployees.map((emp) => (
                <div key={emp.id} className="flex flex-col bg-black/5 rounded-2xl border border-white/5 p-5 relative overflow-hidden group hover:shadow-xl hover:border-current/20 transition-all duration-300">
                  
                  {/* CÁC NÚT HÀNH ĐỘNG (Hiện khi hover) */}
                  <div className="absolute top-4 left-4 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-all z-10">
                    <button 
                      onClick={() => handleEditClick(emp)}
                      className={`p-2 rounded-lg bg-black/30 backdrop-blur-md hover:${t.button.split(' ')[0]} hover:text-white transition-all`}
                      title="Chỉnh sửa thông tin"
                    >
                      <Edit3 size={14} />
                    </button>

                    {/* NÚT XÓA CHỈ HIỂN THỊ VỚI ADMIN */}
                    {user?.role === 'admin' && emp.id !== user?.id && (
                      <button 
                        onClick={() => handleDeleteEmployee(emp.id, emp.username)}
                        className={`p-2 rounded-lg bg-black/30 backdrop-blur-md hover:bg-red-500 hover:text-white transition-all`}
                        title="Xóa nhân viên"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>

                  <div className="flex gap-4 items-center mb-4 pl-16">
                    <img 
                      src={emp.avatarUrl || `https://ui-avatars.com/api/?name=${emp.fullName}&background=random&size=150`} 
                      alt="Avatar" 
                      className="w-16 h-16 rounded-full object-cover border-2 border-current shadow-md shrink-0"
                    />
                    <div className="min-w-0">
                      <h3 className="font-black text-base truncate" title={emp.fullName}>{emp.fullName}</h3>
                      <p className={`text-[10px] font-mono opacity-50`}>@{emp.username} (UID: #{emp.id})</p>
                      <span className={`text-[9px] font-black uppercase tracking-wider inline-flex items-center gap-1 mt-1.5 ${
                        emp.role === 'admin' ? 'text-red-500 bg-red-500/10' : emp.role === 'manager' ? 'text-amber-500 bg-amber-500/10' : 'text-blue-500 bg-blue-500/10'
                      } px-2 py-0.5 rounded-md`}>
                        <ShieldCheck size={10} /> {emp.role}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 text-xs border-t border-dashed border-white/5 pt-3 mt-1 flex-1">
                    <div className="flex items-center gap-2"><Mail size={12} className="opacity-40 shrink-0" /><span className="truncate opacity-75">{emp.email}</span></div>
                    <div className="flex items-center gap-2"><Phone size={12} className="opacity-40 shrink-0" /><span className="opacity-75">{emp.phoneNumber}</span></div>
                    <div className="flex items-center gap-2"><MapPin size={12} className="opacity-40 shrink-0" /><span className="truncate opacity-75" title={emp.address}>{emp.address}</span></div>
                    <div className="flex items-center gap-2"><Calendar size={12} className="opacity-40 shrink-0" /><span className="opacity-60">Gia nhập: {formatDate(emp.createdAt)}</span></div>
                  </div>

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
            </div>
          )}
        </div>
      </div>

      {editingEmp && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className={`${t.panel} w-full max-w-lg rounded-3xl shadow-2xl flex flex-col overflow-hidden border ${t.border} p-6 relative`}>
            <button 
              onClick={() => setEditingEmp(null)} 
              className="absolute top-4 right-4 text-gray-500 hover:text-red-500 transition-colors p-1"
            >
              <X size={20} />
            </button>
            
            <h3 className="text-lg font-black uppercase tracking-widest mb-4 flex items-center gap-2 border-b border-white/10 pb-4">
              <Edit3 size={20} className={t.accent} /> Cập nhật: @{editingEmp.username}
            </h3>

            <div className="flex flex-col gap-4 mt-2">
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest opacity-60">Họ và tên</label>
                <input name="fullName" value={editForm.fullName} onChange={handleFormChange} className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} text-sm font-bold outline-none`} />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-widest opacity-60">Số điện thoại</label>
                  <input name="phoneNumber" value={editForm.phoneNumber} onChange={handleFormChange} className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} text-sm font-bold outline-none`} />
                </div>
                
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-bold uppercase tracking-widest opacity-60">Vai trò (Phân quyền)</label>
                  <select 
                    name="role" 
                    value={editForm.role} 
                    onChange={handleFormChange}
                    disabled={user?.role !== 'admin'}
                    className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} text-sm font-bold outline-none ${user?.role !== 'admin' ? 'opacity-50 cursor-not-allowed grayscale' : ''}`}
                  >
                    <option value="employee">Nhân viên</option>
                    <option value="manager">Trưởng phòng</option>
                    <option value="admin">Quản trị viên</option>
                  </select>
                  {user?.role !== 'admin' && (
                    <p className="text-[9px] text-orange-500 mt-1 italic">* Tính năng giới hạn cho Admin.</p>
                  )}
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest opacity-60">Email</label>
                <input name="email" value={editForm.email} onChange={handleFormChange} className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} text-sm font-bold outline-none`} />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-bold uppercase tracking-widest opacity-60">Địa chỉ</label>
                <input name="address" value={editForm.address} onChange={handleFormChange} className={`w-full px-4 py-2.5 rounded-xl border ${t.border} ${t.inputBg} text-sm font-bold outline-none`} />
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-white/10 flex justify-end gap-3 shrink-0">
              <button 
                onClick={() => setEditingEmp(null)} 
                className={`px-6 py-2.5 rounded-xl text-sm font-bold border ${t.border} hover:bg-black/5 transition-colors`}
              >
                Hủy bỏ
              </button>
              <button 
                onClick={handleSaveEdit} 
                className={`px-6 py-2.5 rounded-xl text-sm font-black uppercase tracking-widest flex items-center gap-2 ${t.button} ${t.shadow} transition-transform active:scale-95`}
              >
                <Save size={16} /> Lưu thay đổi
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}