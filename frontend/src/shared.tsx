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

export const Auth = createContext<{
  user: Row | null;
  setUser: (u: Row | null) => void;
}>({ user: null, setUser: () => {} });

export const pct = (n: number | undefined) =>
  n == null ? "—" : `${(n * 100).toFixed(1)}%`;

export const date = (s: string) => new Date(s).toLocaleString();

export function useData(path: string, interval = 0) {
  const [data, setData] = useState<any>(null),
    [error, setError] = useState("");
  const load = () =>
    api
      .get(path)
      .then((r) => {
        setData(r.data);
        setError("");
      })
      .catch((e) => setError(message(e)));
  useEffect(() => {
    load();
    if (interval) {
      const id = setInterval(load, interval);
      return () => clearInterval(id);
    }
  }, [path, interval]);
  return { data, error, load };
}

export function Badge({
  children,
  tone = "green",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

export function Empty({
  text = "No records yet. Complete the workflow to see results here.",
}: {
  text?: string;
}) {
  return (
    <div className="empty">
      <Search size={24} />
      <p>{text}</p>
    </div>
  );
}

export function ErrorBox({ error }: { error: string }) {
  return error ? (
    <div role="alert" className="error">
      {error}
    </div>
  ) : null;
}

export function Header({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

export function Card({
  title,
  sub,
  children,
  action,
}: {
  title: string;
  sub?: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="card">
      <div className="card-title">
        <div>
          <h2>{title}</h2>
          {sub && <p>{sub}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function Action({
  label,
  run,
  done,
}: {
  label: string;
  run: () => Promise<any>;
  done?: () => void;
}) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  return (
    <>
      <button
        className="btn"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError("");
          try {
            await run();
            done?.();
          } catch (e) {
            setError(message(e));
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? <RefreshCw size={16} /> : <Play size={15} />}{" "}
        {busy ? "Working…" : label}
      </button>
      <ErrorBox error={error} />
    </>
  );
}
