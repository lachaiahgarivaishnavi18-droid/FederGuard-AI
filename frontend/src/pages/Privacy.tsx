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

export default function Privacy() {
  const { data: d, error, load } = useData("/privacy/status", 5000),
    [config, setConfig] = useState<Row | null>(null),
    { user } = useContext(Auth);
  useEffect(() => {
    if (d && !config) setConfig(d.configuration);
  }, [d]);
  return (
    <>
      <Header
        eyebrow="PRIVACY CENTER"
        title="Make the protection measurable."
        description="Inspect the mechanism, assumptions and composed privacy spending for your bank."
      />
      <ErrorBox error={error} />
      {d && (
        <>
          <div className="stats">
            <div className="stat">
              <span>Latest composed epsilon</span>
              <strong>{d.latest_epsilon?.toFixed(2) ?? "—"}</strong>
              <small>RDP accountant · bank-local release history</small>
            </div>
            <div className="stat">
              <span>Delta</span>
              <strong>{d.configuration.delta}</strong>
              <small>Configured failure probability</small>
            </div>
            <div className="stat">
              <span>Bank-local releases</span>
              <strong>{d.completed_releases}</strong>
              <small>
                Includes standalone training; failures may spend privacy
              </small>
            </div>
          </div>
          <div className="notice amber-notice">{d.secure_aggregation}</div>
          <Card
            title="Differential privacy configuration"
            sub="Research mechanism: full-batch clipped gradients, Gaussian noise, sample rate 1, add/remove adjacency."
          >
            {config && (
              <>
                <div className="form-grid">
                  {[
                    "clipping_norm",
                    "noise_multiplier",
                    "delta",
                    "max_epsilon",
                  ].map((k) => (
                    <label key={k}>
                      {k.replaceAll("_", " ")}
                      <input
                        type="number"
                        step="any"
                        value={config[k]}
                        onChange={(e) =>
                          setConfig({ ...config, [k]: Number(e.target.value) })
                        }
                      />
                    </label>
                  ))}
                  <label className="check">
                    <input
                      type="checkbox"
                      checked={config.enabled}
                      onChange={(e) =>
                        setConfig({ ...config, enabled: e.target.checked })
                      }
                    />
                    Enable DP mechanism
                  </label>
                </div>
                {user?.role === "admin" && (
                  <Action
                    label="Save privacy configuration"
                    run={() => api.put("/privacy/config", config)}
                    done={load}
                  />
                )}
              </>
            )}
            <p className="hint">
              Non-cryptographic random generation is used in this prototype. Any
              unprotected release prevents an end-to-end DP claim for the
              training history. Local accounting also includes standalone
              training. See the documented assumptions.
            </p>
          </Card>
        </>
      )}
    </>
  );
}
