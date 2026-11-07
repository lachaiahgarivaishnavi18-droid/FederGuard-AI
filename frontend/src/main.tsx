import React, { useState, useEffect, createContext, useContext } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Link,
  useNavigate,
} from "react-router-dom";
import {
  ShieldCheck,
  LayoutDashboard,
  Building2,
  Network,
  LockKeyhole,
  ScanLine,
  Radio,
  BookOpen,
  MessagesSquare,
  Waypoints,
  FolderSearch,
  Bot,
  ChartNoAxesCombined,
  Settings,
  LogOut,
  ArrowUpRight,
  ArrowRight,
  Activity,
  Search,
  ChevronRight,
  Play,
  Plus,
  Check,
  RefreshCw,
  Upload,
  FileText,
  Menu,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";
import { ReactFlow, Background, Controls } from "@xyflow/react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api, message, Row } from "./api";
import "@xyflow/react/dist/style.css";
import "./styles.css";
import {
  Auth,
  pct,
  date,
  useData,
  Badge,
  Empty,
  ErrorBox,
  Header,
  Card,
  Action,
} from "./shared";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Banks from "./pages/Banks";
import Federated from "./pages/Federated";
import Privacy from "./pages/Privacy";
import Fraud from "./pages/Fraud";
import Intelligence from "./pages/Intelligence";
import Knowledge from "./pages/Knowledge";
import Assistant from "./pages/Assistant";
import Graph from "./pages/Graph";
import Investigations from "./pages/Investigations";
import Agents from "./pages/Agents";
import Analytics from "./pages/Analytics";
import SettingsPage from "./pages/SettingsPage";

function App() {
  const [user, setUser] = useState<Row | null>(null),
    [ready, setReady] = useState(false);
  useEffect(() => {
    api
      .get("/auth/me")
      .then((r) => setUser(r.data))
      .finally(() => setReady(true))
      .catch(() => {});
  }, []);
  return (
    <Auth.Provider value={{ user, setUser }}>
      <BrowserRouter>
        {!ready ? (
          <div className="loading">Connecting to FederGuard…</div>
        ) : (
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/*" element={user ? <Shell /> : <Login />} />
          </Routes>
        )}
      </BrowserRouter>
    </Auth.Provider>
  );
}

const links = [
  [
    "WORKSPACE",
    [
      ["dashboard", "Overview", LayoutDashboard],
      ["banks", "Bank network", Building2],
      ["federated", "Federated learning", Network],
      ["privacy", "Privacy center", LockKeyhole],
    ],
  ],
  [
    "INTELLIGENCE",
    [
      ["fraud", "Fraud detection", ScanLine],
      ["intelligence", "Shared intelligence", Radio],
      ["knowledge", "Knowledge base", BookOpen],
      ["assistant", "AI assistant", MessagesSquare],
      ["graph", "Pattern graph", Waypoints],
    ],
  ],
  [
    "OPERATIONS",
    [
      ["investigations", "Investigations", FolderSearch],
      ["agents", "Agent workflows", Bot],
      ["analytics", "Analytics", ChartNoAxesCombined],
      ["settings", "Governance & settings", Settings],
    ],
  ],
] as const;

function Shell() {
  const { user, setUser } = useContext(Auth),
    [open, setOpen] = useState(false);
  return (
    <div className="app">
      <aside className={open ? "open" : ""}>
        <Link className="brand" to="/">
          <span className="logo">
            <ShieldCheck size={24} />
          </span>
          <span>
            FederGuard <b>AI</b>
            <small>COLLABORATIVE DEFENSE</small>
          </span>
        </Link>
        <div className="workspace">
          <span className="bank-avatar">A</span>
          <div>
            Research consortium<small>3 simulated institutions</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <nav>
          {links.map(([group, items]) => (
            <div key={group}>
              <div className="nav-label">{group}</div>
              {items.map(([path, label, Icon]) => (
                <NavLink
                  key={path}
                  to={"/" + path}
                  onClick={() => setOpen(false)}
                >
                  <Icon size={18} />
                  {label}
                  {path === "assistant" && <span className="new">AI</span>}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="local">
            <span className="dot" />
            Data stays at the source
          </div>
          <p>
            Independent bank stores.
            <br />
            Shared model intelligence.
          </p>
          <button
            onClick={async () => {
              await api.post("/auth/logout");
              setUser(null);
            }}
          >
            <span className="avatar">
              {user?.bank_id?.slice(-1).toUpperCase()}
            </span>
            <span>
              {user?.bank_id}
              <small>{user?.role}</small>
            </span>
            <LogOut size={16} />
          </button>
        </div>
      </aside>
      <div className="main">
        <header className="topbar">
          <div>
            <button
              className="mobile-menu"
              onClick={() => setOpen(!open)}
              aria-label="Toggle navigation"
            >
              <Menu />
            </button>
            <span className="breadcrumb">
              Workspace <ChevronRight size={14} /> <b>Intelligence console</b>
            </span>
          </div>
          <div>
            <span className="demo-indicator">
              <span className="dot" />
              SYNTHETIC DEMO
            </span>
            <span className="top-divider" />
            <ShieldCheck size={17} />
            <span className="top-user">{user?.bank_id}</span>
          </div>
        </header>
        <main className="content">
          <Routes>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="banks" element={<Banks />} />
            <Route path="federated" element={<Federated />} />
            <Route path="privacy" element={<Privacy />} />
            <Route path="fraud" element={<Fraud />} />
            <Route path="intelligence" element={<Intelligence />} />
            <Route path="knowledge" element={<Knowledge />} />
            <Route path="assistant" element={<Assistant />} />
            <Route path="graph" element={<Graph />} />
            <Route path="investigations" element={<Investigations />} />
            <Route path="agents" element={<Agents />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Dashboard />} />
          </Routes>
          <footer className="content-footer">
            <ShieldCheck size={14} /> Synthetic data only · Research & decision
            support <span>FederGuard AI / v0.1</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
