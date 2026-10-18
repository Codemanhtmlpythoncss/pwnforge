import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { api } from "./api";
import { useAuth } from "./auth";
import { RankBadge, Spinner } from "./ui";
import { Icon } from "./icons";
import { Logo } from "./logo";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Courses from "./pages/Courses";
import CourseDetail from "./pages/CourseDetail";
import Machines from "./pages/Machines";
import Paths from "./pages/Paths";
import PathDetail from "./pages/PathDetail";
import Skills from "./pages/Skills";
import Labs from "./pages/Labs";
import LabWorkspace from "./pages/LabWorkspace";
import Achievements from "./pages/Achievements";
import Admin from "./pages/Admin";
import Settings from "./pages/Settings";

const GROUPS: { label: string; items: [string, string, string][] }[] = [
  { label: "Learn", items: [
    ["/", "Dashboard", "grid"],
    ["/courses", "Courses", "book"],
    ["/paths", "Learning Paths", "route"],
    ["/skills", "Skills", "chart"],
    ["/achievements", "Achievements", "trophy"],
  ]},
  { label: "Labs", items: [
    ["/machines", "Machines", "cpu"],
    ["/labs", "Labs", "box"],
  ]},
];
const ADMIN_ITEMS: [string, string, string][] = [
  ["/admin", "Administration", "sliders"],
  ["/settings", "Settings", "gear"],
];

const TITLES: Record<string, string> = {
  "/": "Dashboard", "/courses": "Course Catalogue", "/paths": "Learning Paths",
  "/skills": "Skills", "/achievements": "Achievements", "/machines": "Machine Catalogue",
  "/labs": "Labs", "/admin": "Administration", "/settings": "Settings",
};

function toggleTheme() {
  const el = document.documentElement;
  const next = el.getAttribute("data-theme") === "light" ? "dark" : "light";
  el.setAttribute("data-theme", next);
  try { localStorage.setItem("pwnforge-theme", next); } catch {}
}

export default function App() {
  const { user, loading } = useAuth();
  useEffect(() => {
    try {
      const t = localStorage.getItem("pwnforge-theme");
      if (t) document.documentElement.setAttribute("data-theme", t);
    } catch {}
  }, []);

  if (loading) return <div className="h-full grid place-items-center"><Spinner /></div>;
  if (!user) return <Login />;

  return (
    <div className="flex h-full">
      <Sidebar isAdmin={user.role === "administrator"} user={user} />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-6xl mx-auto px-6 py-6 fade-in">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/courses" element={<Courses />} />
              <Route path="/courses/:id" element={<CourseDetail />} />
              <Route path="/paths" element={<Paths />} />
              <Route path="/paths/:id" element={<PathDetail />} />
              <Route path="/machines" element={<Machines />} />
              <Route path="/labs" element={<Labs />} />
              <Route path="/labs/instance/:id" element={<LabWorkspace />} />
              <Route path="/skills" element={<Skills />} />
              <Route path="/achievements" element={<Achievements />} />
              {user.role === "administrator" && <Route path="/admin" element={<Admin />} />}
              {user.role === "administrator" && <Route path="/settings" element={<Settings />} />}
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
}

function Sidebar({ isAdmin, user }: { isAdmin: boolean; user: any }) {
  const { logout } = useAuth();
  const link = ({ isActive }: { isActive: boolean }) =>
    `group flex items-center gap-3 pl-3 pr-2 py-2 rounded-lg text-sm relative transition-colors ${
      isActive ? "bg-[var(--panel3)] text-ink font-semibold" : "text-muted hover:text-ink hover:bg-[var(--panel2)]"}`;
  const renderItem = ([to, label, icon]: [string, string, string]) => (
    <NavLink key={to} to={to} end={to === "/"} className={link}>
      {({ isActive }) => (<>
        {isActive && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-brand" />}
        <Icon name={icon} className={isActive ? "text-brand" : ""} />{label}
      </>)}
    </NavLink>
  );
  return (
    <aside className="w-[232px] shrink-0 border-r border-line bg-[var(--bg2)] flex flex-col">
      <div className="px-4 h-14 flex items-center border-b border-line">
        <Logo size={30} />
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-5">
        {GROUPS.map(g => (
          <div key={g.label}>
            <div className="px-3 mb-1 text-[10px] font-bold uppercase tracking-wider text-muted">{g.label}</div>
            <div className="space-y-0.5">{g.items.map(renderItem)}</div>
          </div>
        ))}
        {isAdmin && (
          <div>
            <div className="px-3 mb-1 text-[10px] font-bold uppercase tracking-wider text-muted">Admin</div>
            <div className="space-y-0.5">{ADMIN_ITEMS.map(renderItem)}</div>
          </div>
        )}
      </nav>
      <div className="p-3 border-t border-line">
        <div className="flex items-center gap-2 mb-3 px-1">
          <div className="w-8 h-8 rounded-lg bg-[var(--panel3)] grid place-items-center text-brand font-bold">
            {(user.display_name || user.username)[0]?.toUpperCase()}
          </div>
          <div className="leading-tight min-w-0">
            <div className="text-sm font-semibold truncate">{user.display_name || user.username}</div>
            <div className="text-[11px] text-muted">{user.role}</div>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-ghost flex-1 py-1.5 text-xs" onClick={toggleTheme}>
            <Icon name="sun" size={14} />Theme
          </button>
          <button className="btn btn-ghost flex-1 py-1.5 text-xs" onClick={() => logout()}>
            <Icon name="power" size={14} />Sign out
          </button>
        </div>
      </div>
    </aside>
  );
}

function TopBar() {
  const loc = useLocation();
  const { user } = useAuth();
  const [caps, setCaps] = useState<any>(null);
  useEffect(() => { api.get("/api/host/capabilities").then(setCaps).catch(() => {}); }, []);
  const title = TITLES[loc.pathname] ||
    (loc.pathname.startsWith("/courses/") ? "Course" :
     loc.pathname.startsWith("/paths/") ? "Learning Path" :
     loc.pathname.startsWith("/labs/") ? "Lab Workspace" : "Pwnforge");
  const sim = caps && !caps.real_virtualization;
  return (
    <header className="h-14 shrink-0 border-b border-line bg-[var(--bg2)] flex items-center justify-between px-6">
      <div className="flex items-center gap-2 text-sm">
        <span className="text-brand mono">~/</span>
        <span className="font-semibold">{title}</span>
      </div>
      <div className="flex items-center gap-4">
        {caps && (
          <span className="tag" title="Active virtualisation driver">
            <span className={`w-2 h-2 rounded-full ${sim ? "bg-[var(--warn)]" : "bg-[var(--brand)]"}`}
              style={{ boxShadow: `0 0 8px ${sim ? "var(--warn)" : "var(--brand)"}` }} />
            {caps.driver}{sim ? " · simulated" : ""}
          </span>
        )}
        {user && <RankBadge xp={user.xp} size={36} />}
      </div>
    </header>
  );
}
