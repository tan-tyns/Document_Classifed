import React, { useState } from 'react';
import { Flower2, FileSearch, Settings as SettingsIcon } from 'lucide-react';
import Auth from './pages/Auth';
import OCRStation from './pages/OCRStation';
import Archive from './pages/Archive';
import SettingsPage from './pages/Settings';
import Dashboard from './pages/Dashboard'; // <-- Import file mới
import Header from './components/Header';

// ... (themes config giữ nguyên) ...
const themes = {
  sakura: { name: "Sakura Dark", bg: "bg-[#F8F9FA]", panel: "bg-white", accent: "text-[#FFB7C5]", button: "bg-[#FFB7C5] hover:bg-[#F48FB1] text-[#1A1A1A]", border: "border-[#E0E0E0]", text: "text-[#212121]", subtext: "text-[#757575]", shadow: "shadow-[0_0_15px_rgba(255,183,197,0.3)]", inputBg: "bg-[#F8F9FA]", icon: <Flower2 size={20} /> },
  teal: { name: "Modern Teal", bg: "bg-[#F8F9FA]", panel: "bg-white", accent: "text-[#00796B]", button: "bg-[#00796B] hover:bg-[#00695C] text-white", border: "border-[#E0E0E0]", text: "text-[#212121]", subtext: "text-[#757575]", shadow: "shadow-lg shadow-[#00796B]/10", inputBg: "bg-[#F8F9FA]", icon: <FileSearch size={20} /> },
  ocean: { name: "Deep Ocean", bg: "bg-[#0F172A]", panel: "bg-[#1E293B]", accent: "text-[#38BDF8]", button: "bg-[#38BDF8] hover:bg-[#7DD3FC] text-[#0F172A]", border: "border-[#334155]", text: "text-[#F1F5F9]", subtext: "text-[#94A3B8]", shadow: "shadow-[0_0_20px_rgba(56,189,248,0.2)]", inputBg: "bg-[#0F172A]", icon: <SettingsIcon size={20} /> }
};
export default function App() {
  const [currentTheme, setCurrentTheme] = useState('sakura');
  const t = themes[currentTheme];

  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState({ username: '', email: '' });
  
  // Đổi tab mặc định khi đăng nhập thành 'dashboard' nếu bạn muốn, 
  // hoặc cứ để 'ocr' như cũ
  const [activeTab, setActiveTab] = useState('dashboard'); 
  const [archivedDocs, setArchivedDocs] = useState([]);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser({ username: '', email: '' });
    setArchivedDocs([]);
    setActiveTab('dashboard'); // Reset về tab chính
  };

  const handleArchiveSave = (finalDocData) => { /* Giữ nguyên logic */
    setArchivedDocs(prev => {
      const exists = prev.findIndex(doc => doc.id === finalDocData.id);
      if (exists !== -1) {
        const newArchive = [...prev]; 
        newArchive[exists] = finalDocData; 
        return newArchive;
      }
      return [finalDocData, ...prev];
    });
    alert("Đã lưu tài liệu thành công vào Kho Lưu Trữ!");
  };

  if (!isAuthenticated) {
    return <Auth onLogin={handleLogin} t={t} />;
  }

  return (
    <div className={`min-h-screen ${t.bg} ${t.text} transition-all duration-500 font-sans flex flex-col`}>
      <Header 
        user={user}
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        archivedCount={archivedDocs.length}
        onLogout={handleLogout}
        t={t}
        currentTheme={currentTheme}
        setCurrentTheme={setCurrentTheme}
        themes={themes}
      />

      {/* ĐIỀU HƯỚNG CÁC TRANG DỰA VÀO TAB */}
      {activeTab === 'dashboard' && (
        <Dashboard 
          archivedDocs={archivedDocs} 
          user={user}
          t={t} 
        />
      )}

      {activeTab === 'ocr' && (
        <OCRStation 
          onArchiveSave={handleArchiveSave} 
          t={t} 
        />
      )}

      {activeTab === 'archive' && (
        <Archive 
          archivedDocs={archivedDocs} 
          t={t} 
        />
      )}

      {activeTab === 'settings' && (
        <SettingsPage 
          user={user} 
          setUser={setUser} 
          t={t} 
          currentTheme={currentTheme} 
          setCurrentTheme={setCurrentTheme} 
          themes={themes} 
        />
      )}

      <style dangerouslySetInnerHTML={{__html: `... (Scrollbar style giữ nguyên) ...`}} />
    </div>
  );
}