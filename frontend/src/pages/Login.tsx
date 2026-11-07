import React, { useState, useEffect, createContext, useContext } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Link,
  useNavigate,
  useLocation,
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
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, "Enter your password."),
});

export default function Login() {
  const location = useLocation();
  const registeredEmail = location.state?.registeredEmail as string | undefined;
  const { setUser } = useContext(Auth),
    navigate = useNavigate(),
    [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { isSubmitting, errors },
  } = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: registeredEmail || "bank_a@federguard.demo" },
  });
  return (
    <div className="login">
      <div className="login-intro">
        <Link className="brand" to="/">
          <span className="logo">
            <ShieldCheck />
          </span>
          FederGuard AI
        </Link>
        <div>
          <div className="eyebrow">TRUST IS A NETWORK EFFECT</div>
          <h1>
            Shared intelligence.
            <br />
            Sovereign data.
          </h1>
          <p>Connect to your institution’s investigation workspace.</p>
        </div>
        <small>Academic demonstration · All records are synthetic</small>
      </div>
      <form
        onSubmit={handleSubmit(async (values) => {
          try {
            const r = await api.post("/auth/login", values);
            setUser(r.data);
            navigate("/dashboard");
          } catch (e) {
            setError(message(e));
          }
        })}
      >
        <Badge>SECURE WORKSPACE</Badge>
        <h1>Welcome back</h1>
        <p>Sign in with your institution credentials.</p>
        {registeredEmail && (
          <p className="auth-success" role="status">
            Account created successfully. Sign in to continue.
          </p>
        )}
        <label>
          Email address
          <input {...register("email")} autoComplete="username" />
        </label>
        <label>
          Password
          <input
            {...register("password")}
            type="password"
            autoComplete="current-password"
          />
        </label>
        <ErrorBox
          error={
            error || errors.email?.message || errors.password?.message || ""
          }
        />
        <button className="btn" disabled={isSubmitting}>
          Sign in <ArrowRight size={17} />
        </button>
        <p className="auth-switch">
          New to FederGuard? <Link to="/register">Create account</Link>
        </p>
        <p className="hint">
          Demo credentials are configured by your local administrator in{" "}
          <code>.env</code>.
        </p>
      </form>
    </div>
  );
}
