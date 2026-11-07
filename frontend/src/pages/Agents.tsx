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

export default function Agents() {
  const [question, setQuestion] = useState(
      "Explain suspicious velocity patterns",
    ),
    [result, setResult] = useState<Row | null>(null),
    { data, error, load } = useData("/agents/executions");
  return (
    <>
      <Header
        eyebrow="LANGGRAPH ORCHESTRATION"
        title="A traceable path to intelligence."
        description="A typed, permission-scoped analyst workflow. Bank-local tasks are explicitly delegated to bank endpoints."
      />
      <Card
        title="Run investigation support workflow"
        sub="Local training and aggregation are separate explicit operations; this workflow does not trigger them."
      >
        <div className="form-row">
          <input
            aria-label="Agent question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Action
            label="Run workflow"
            run={async () => {
              const r = await api.post("/agents/run", { question });
              setResult(r.data);
            }}
            done={load}
          />
        </div>
      </Card>
      <ErrorBox error={error} />
      {result && (
        <Card title="Execution trace" sub={result.status}>
          {result.error && <ErrorBox error={result.error} />}
          <div className="agent-trace">
            {result.trace?.map((s: Row, i: number) => (
              <details key={i}>
                <summary>
                  <span className="step">{i + 1}</span>
                  {s.agent}
                  <Badge>{s.status}</Badge>
                </summary>
                <pre>{JSON.stringify(s.result, null, 2)}</pre>
              </details>
            ))}
          </div>
        </Card>
      )}
      <Card title="Previous executions">
        {data?.length ? (
          data.map((r: Row) => (
            <button
              className="case-item"
              key={r.id}
              onClick={() => setResult(r)}
            >
              <Bot size={18} />
              <div>
                <b>{r.question}</b>
                <small>{date(r.created_at)}</small>
              </div>
              <Badge>{r.status}</Badge>
            </button>
          ))
        ) : (
          <Empty />
        )}
      </Card>
    </>
  );
}
