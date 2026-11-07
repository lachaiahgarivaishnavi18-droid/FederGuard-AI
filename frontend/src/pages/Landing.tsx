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

export default function Landing() {
  return (
    <div className="landing">
      <nav>
        <Link className="brand" to="/">
          <span className="logo">
            <ShieldCheck />
          </span>
          FederGuard <b>AI</b>
        </Link>
        <Link className="btn" to="/login">
          Open workspace <ArrowUpRight size={16} />
        </Link>
      </nav>
      <main>
        <div className="eyebrow">COLLABORATIVE INTELLIGENCE. LOCAL DATA.</div>
        <h1>
          A stronger network.
          <br />
          <span>A private foundation.</span>
        </h1>
        <p>
          A research platform for financial institutions to learn from shared
          fraud patterns while customer records stay within each bank.
        </p>
        <Link className="btn" to="/login">
          Explore the platform <ArrowRight size={18} />
        </Link>
        <div className="landing-grid">
          {[
            [
              Building2,
              "Train locally",
              "Each bank maintains an independent synthetic data store.",
            ],
            [
              Network,
              "Learn together",
              "Flower FedAvg combines model updates across participants.",
            ],
            [
              ShieldCheck,
              "Investigate with evidence",
              "Permission-aware intelligence supports human review.",
            ],
          ].map(([Icon, title, text]: any) => (
            <article key={title}>
              <Icon />
              <h2>{title}</h2>
              <p>{text}</p>
            </article>
          ))}
        </div>
        <div className="notice">
          Synthetic research prototype · Aggregation is a plaintext simulation ·
          No automated adverse decisions
        </div>
      </main>
    </div>
  );
}
