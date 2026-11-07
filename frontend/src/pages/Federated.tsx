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

export default function Federated() {
  const { data, error, load } = useData("/federated/rounds", 4000),
    [strategy, setStrategy] = useState("FedAvg"),
    [dropout, setDropout] = useState(""),
    { user } = useContext(Auth);
  return (
    <>
      <Header
        eyebrow="FEDERATED LEARNING"
        title="Train together. Keep data local."
        description="Actual local model optimization across three bank processes; coordinator receives model updates only."
      />
      <div className="notice amber-notice">
        Plaintext aggregation simulation. The coordinator can inspect individual
        updates. This is not cryptographic secure aggregation.
      </div>
      <Card
        title="Round configuration"
        sub="Equal, public client weights · fixed public feature transforms"
      >
        <div className="form-row">
          <label>
            Strategy
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option>FedAvg</option>
              <option>FedProx</option>
            </select>
          </label>
          <label>
            Dropout scenario
            <select
              value={dropout}
              onChange={(e) => setDropout(e.target.value)}
            >
              <option value="">All clients</option>
              <option value="bank_c">Simulate Bank C dropout</option>
            </select>
          </label>
          {user?.role === "admin" && (
            <Action
              label="Start federated round"
              run={() =>
                api.post("/federated/rounds/start", {
                  strategy,
                  dropout_bank: dropout || null,
                })
              }
              done={load}
            />
          )}
        </div>
      </Card>
      <ErrorBox error={error} />
      <Card
        title="Training rounds"
        sub="Version history, participation and measured public-holdout performance"
      >
        {data?.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Round</th>
                  <th>Strategy</th>
                  <th>Clients</th>
                  <th>ROC-AUC</th>
                  <th>Duration</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r: Row) => (
                  <React.Fragment key={r.id}>
                    <tr>
                      <td>
                        <b>{r.id.slice(0, 8)}</b>
                        <small>{date(r.created_at)}</small>
                      </td>
                      <td>{r.strategy}</td>
                      <td>
                        {r.successful ?? 0} / {r.selected.length}
                      </td>
                      <td>{pct(r.metrics?.roc_auc)}</td>
                      <td>{r.duration?.toFixed(2) ?? "—"} s</td>
                      <td>
                        <Badge
                          tone={
                            r.status === "failed"
                              ? "red"
                              : r.status === "running"
                                ? "amber"
                                : "green"
                          }
                        >
                          {r.status}
                        </Badge>
                      </td>
                    </tr>
                    {r.error && (
                      <tr>
                        <td colSpan={6} className="error">
                          {r.error}
                        </td>
                      </tr>
                    )}
                    {r.clients?.map((c: Row) => (
                      <tr key={c.bank_id} className="client-row">
                        <td>↳ {c.bank_id}</td>
                        <td colSpan={2}>
                          {c.status} {c.error || ""}
                        </td>
                        <td>ε {c.epsilon?.toFixed(2) ?? "—"}</td>
                        <td colSpan={2}>
                          {c.duration?.toFixed(2) ?? "—"} s local training
                        </td>
                      </tr>
                    ))}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="No training rounds yet. Start the bank nodes and launch a round." />
        )}
      </Card>
    </>
  );
}
