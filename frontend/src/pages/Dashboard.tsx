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

export default function Dashboard() {
  const { data: d, error } = useData("/analytics/dashboard", 5000),
    { data: trends } = useData("/intelligence/trends");
  const navigate = useNavigate();
  if (!d)
    return (
      <>
        <ErrorBox error={error} />
        <Empty text="Loading your workspace…" />
      </>
    );
  const chart = [...d.rounds]
    .reverse()
    .filter((r: Row) => r.metrics)
    .map((r: Row) => ({
      round: `v${r.version}`,
      auc: r.metrics.roc_auc * 100,
      pr: r.metrics.pr_auc * 100,
    }));
  return (
    <>
      <Header
        eyebrow="NETWORK INTELLIGENCE"
        title="A clearer view. A stronger defense."
        description="Your cross-bank fraud intelligence workspace, with privacy at its core."
        action={
          <Link className="btn" to="/federated">
            <Network size={17} /> Manage training <ArrowUpRight size={16} />
          </Link>
        }
      />
      <div className="status-banner">
        <span className="status-icon">
          <ShieldCheck size={22} />
        </span>
        <div>
          <b>Local data. Collective intelligence.</b>
          <p>
            Raw transaction records remain in each bank’s isolated environment.
          </p>
        </div>
        <Badge tone="amber">RESEARCH SIMULATION</Badge>
      </div>
      <div className="stats">
        {[
          [
            Building2,
            "Participating banks",
            d.banks,
            "Independent synthetic nodes",
            "blue",
          ],
          [
            Activity,
            "Global ROC-AUC",
            pct(d.metrics.roc_auc),
            `Model version ${d.model_version} · public synthetic holdout`,
            "green",
          ],
          [
            ScanLine,
            "Local fraud alerts",
            d.alerts,
            "Indicators awaiting human assessment",
            "orange",
          ],
          [
            Radio,
            "Intelligence records",
            d.intelligence,
            "Authorized records in your workspace",
            "purple",
          ],
        ].map(([Icon, label, value, caption, color]: any) => (
          <div className="stat" key={label}>
            <div>
              <span>{label}</span>
              <Icon className={color} size={19} />
            </div>
            <strong>{value}</strong>
            <small>{caption}</small>
          </div>
        ))}
      </div>
      <div className="dashboard-grid">
        <Card
          title="Federated model performance"
          sub="Measured across completed rounds · synthetic evaluation"
          action={
            <Link to="/analytics" className="text-link">
              View analytics <ArrowUpRight size={14} />
            </Link>
          }
        >
          <div className="chart-legend">
            <span>
              <i className="legend blue-bg" />
              ROC-AUC
            </span>
            <span>
              <i className="legend mint-bg" />
              PR-AUC
            </span>
            <Badge tone="gray">PUBLIC HOLDOUT</Badge>
          </div>
          {chart.length ? (
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chart}>
                  <defs>
                    <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#5278ec" stopOpacity={0.2} />
                      <stop offset="100%" stopColor="#5278ec" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} stroke="#e9eef5" />
                  <XAxis dataKey="round" axisLine={false} tickLine={false} />
                  <YAxis
                    domain={[0, 100]}
                    tickFormatter={(n) => n + "%"}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="auc"
                    stroke="#4269df"
                    strokeWidth={2.5}
                    fill="url(#area)"
                  />
                  <Area
                    type="monotone"
                    dataKey="pr"
                    stroke="#27a995"
                    strokeWidth={2}
                    fill="transparent"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty text="Run your first federated round to see measured performance." />
          )}
          <div className="card-bottom">
            <span>
              <span className="dot" />
              Flower FedAvg engine
            </span>
            <span>Plaintext aggregation simulation</span>
          </div>
        </Card>
        <Card
          title="Intelligence by category"
          sub="Approved, current advisories"
        >
          <div className="chart short">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={trends || []}
                layout="vertical"
                margin={{ left: 20, right: 30 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="category"
                  width={112}
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip />
                <Bar dataKey="count" radius={[0, 5, 5, 0]} barSize={20}>
                  {(trends || []).map((_: any, i: number) => (
                    <Cell
                      key={i}
                      fill={["#466ee0", "#63a1d5", "#8c7cce", "#38ab9a"][i % 4]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="quiet">
            Counts represent shared advisories, not transaction volume.
          </div>
        </Card>
      </div>
      <div className="dashboard-grid lower">
        <Card
          title="Network activity"
          sub="Your institution’s latest audit events"
          action={
            <Link className="text-link" to="/settings">
              View audit log <ArrowUpRight size={14} />
            </Link>
          }
        >
          <div className="activity-list">
            {d.activity.length ? (
              d.activity.map((a: Row) => (
                <div key={a.id}>
                  <span className="activity-icon">
                    <Check size={15} />
                  </span>
                  <div>
                    <b>{a.action.replaceAll(".", " · ")}</b>
                    <small>{date(a.created_at)}</small>
                  </div>
                  <Badge tone="gray">RECORDED</Badge>
                </div>
              ))
            ) : (
              <Empty />
            )}
          </div>
        </Card>
        <Card
          title="Your next investigation"
          sub="Move from signal to informed review"
        >
          <div className="next-case">
            <FolderSearch size={32} />
            <h3>Keep a human in the loop</h3>
            <p>
              {d.cases} cases in your institution’s workspace. Review supporting
              evidence and document your assessment.
            </p>
            <button
              className="btn light"
              onClick={() => navigate("/investigations")}
            >
              Open investigations <ArrowRight size={16} />
            </button>
          </div>
        </Card>
      </div>
    </>
  );
}
