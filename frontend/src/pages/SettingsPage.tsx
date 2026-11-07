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
import { api, message, Row } from "../api";
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
} from "../shared";

export default function SettingsPage() {
  const { data, error } = useData("/audit");
  const { data: health } = useData("/privacy/status");
  return (
    <>
      <Header
        eyebrow="GOVERNANCE & CONFIGURATION"
        title="Accountability by design."
        description="Institution-scoped audit history and transparent operational settings."
      />
      <div className="bank-grid">
        <Card title="Deployment configuration">
          <dl>
            <dt>AI provider</dt>
            <dd>Environment configured; demo default</dd>
            <dt>Secrets</dt>
            <dd>Environment variables only</dd>
            <dt>Memberships</dt>
            <dd>Invitation required</dd>
            <dt>Raw record access</dt>
            <dd>Bank-local process boundary</dd>
            <dt>Aggregation</dt>
            <dd>Plaintext academic simulation</dd>
          </dl>
        </Card>
        <Card title="Operational health">
          <p>{health?.data_locality || "Loading…"}</p>
          <p className="hint">
            Production deployment requires TLS at the reverse proxy, isolated
            volumes, institution-controlled secrets and independent security
            review. See the deployment runbook.
          </p>
        </Card>
      </div>
      <ErrorBox error={error} />
      <Card title="Your institution’s audit trail">
        {data?.length ? (
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Actor</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r: Row) => (
                <tr key={r.id}>
                  <td>{date(r.created_at)}</td>
                  <td>{r.action}</td>
                  <td>{r.actor.slice(0, 8)}</td>
                  <td>{r.target?.slice(0, 12) || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty />
        )}
      </Card>
    </>
  );
}
