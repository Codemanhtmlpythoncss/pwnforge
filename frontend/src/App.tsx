import { useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";
import { Spinner } from "./ui";
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

const NAV = [
  ["/", "Dashboard", "▚"],
  ["/courses", "Courses", "▤"],
  ["/paths", "Learning Paths", "⇗"],
  ["/machines", "Machine Catalogue", "▦"],
  ["/labs", "Labs", "▣"],
  ["/skills", "Skills", "◈"],
  ["/achievements", "Achievements", "★"],
];

function toggleTheme() {
  const el = document.documentElement;
  const next = el.getAttribute("data-theme") === "light" ? "dark" : "light";
  el.setAttribute("data-theme", next);
  try { localStorage.setItem("hacklab-theme", next); } catch {}
}

export default function App() {
  const { user, loading } = useAuth();
  const nav = useNavigate();
  useEffect(() => {
    try {
      const t = localStorage.getItem("hacklab-theme");
      if (t) document.documentElement.setAttribute("data-theme", t);
    } catch {}
  }, []);

  if (loading) return <div className="h-full grid place-items-center"><Spinner /></div>;
  if (!user) return <Login />;

  return (
    <div className="flex h-full">
      <aside className="w-60 shrink-0 border-r border-line bg-panel2 flex flex-col">
        <div className="px-5 py-4 text-xl font-extrabold tracking-tight">
          Hack<span className="text-brand">Lab</span>
        </div>
        <nav className="flex-1 px-2 space-y-1">
          {NAV.map(([to, label, icon]) => (
            <NavLink key={to} to={to} end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                  isActive ? "bg-panel text-ink font-semibold" : "text-muted hover:text-ink"
                }`}>
              <span className="opacity-70 w-4 text-center">{icon}</span>{label}
            </NavLink>
          ))}
          {user.role === "administrator" && (
            <>
              <NavLink to="/admin" className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${isActive ? "bg-panel font-semibold" : "text-muted hover:text-ink"}`}>
                <span className="opacity-70 w-4 text-center">⚙</span>Administration</NavLink>
              <NavLink to="/settings" className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${isActive ? "bg-panel font-semibold" : "text-muted hover:text-ink"}`}>
                <span className="opacity-70 w-4 text-center">⛭</span>Settings</NavLink>
            </>
          )}
        </nav>
        <div className="p-3 border-t border-line text-xs text-muted">
          <div className="flex items-center justify-between mb-2">
            <span>{user.display_name || user.username}</span>
            <span className="tag">{user.role}</span>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-ghost flex-1 justify-center" onClick={toggleTheme}>Theme</button>
            <LogoutBtn />
          </div>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-6">
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
  );
}

function LogoutBtn() {
  const { logout } = useAuth();
  return <button className="btn btn-ghost flex-1 justify-center" onClick={() => logout()}>Sign out</button>;
}
