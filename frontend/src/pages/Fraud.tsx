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
const featureDefaults = {
  amount: 1800,
  velocity: 12,
  device_risk: 0.8,
  geo_deviation: 0.7,
  account_age: 60,
  hour: 2,
};

export default function Fraud() {
  const [values, setValues] = useState(featureDefaults),
    [result, setResult] = useState<Row | null>(null),
    { data, error, load } = useData("/fraud/alerts");
  return (
    <>
      <Header
        eyebrow="LOCAL FRAUD DETECTION"
        title="From local signals to review."
        description="Score synthetic risk features with your bank’s trained logistic model. No raw inputs are persisted centrally."
      />
      <Card
        title="Synthetic transaction assessment"
        sub="Train a federated round first. Feature contributions are additive log-odds, not causal explanations."
      >
        <div className="form-grid">
          {Object.entries(values).map(([k, v]) => (
            <label key={k}>
              {k.replaceAll("_", " ")}
              <input
                type="number"
                step="any"
                value={v}
                onChange={(e) =>
                  setValues({ ...values, [k]: Number(e.target.value) })
                }
              />
            </label>
          ))}
        </div>
        <Action
          label="Assess local risk"
          run={async () => {
            const r = await api.post("/fraud/detect", values);
            setResult(r.data);
          }}
          done={load}
        />
      </Card>
      {result && (
        <Card title="Model assessment" sub={result.explanation}>
          <div className="risk-score">
            {pct(result.risk_score)}
            <Badge tone="amber">REQUIRES HUMAN REVIEW</Badge>
          </div>
          <div className="contributions">
            {Object.entries(result.contributions).map(([k, v]: any) => (
              <div key={k}>
                <span>{k}</span>
                <meter min={-4} max={4} value={v} />
                <b>{v.toFixed(3)}</b>
              </div>
            ))}
          </div>
          <Action
            label="Create investigation"
            run={() =>
              api.post("/investigations", {
                title: "Review " + result.transaction_reference,
                alert_id: result.id,
              })
            }
          />
        </Card>
      )}
      <ErrorBox error={error} />
      <Card title="Your institution’s alerts">
        {data?.length ? (
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Category</th>
                <th>Risk</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r: Row) => (
                <tr key={r.id}>
                  <td>{r.transaction_reference}</td>
                  <td>{r.category}</td>
                  <td>{pct(r.risk_score)}</td>
                  <td>
                    <Badge tone="amber">{r.review_status}</Badge>
                  </td>
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
