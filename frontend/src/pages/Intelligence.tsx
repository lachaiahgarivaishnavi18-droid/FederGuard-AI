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

export default function Intelligence() {
  const { data, error, load } = useData("/intelligence"),
    { data: docs } = useData("/rag/documents"),
    { user } = useContext(Auth),
    [title, setTitle] = useState(""),
    [summary, setSummary] = useState(""),
    [category, setCategory] = useState("Velocity"),
    [ref, setRef] = useState(""),
    [sharing, setSharing] = useState("private");
  return (
    <>
      <Header
        eyebrow="CROSS-BANK COLLABORATION"
        title="Share patterns. Preserve boundaries."
        description="Only approved, unexpired consortium records are available to other banks."
      />
      <Card
        title="Contribute an advisory"
        sub="Minimized synthetic or aggregate intelligence only. A second authorized reviewer must approve sharing."
      >
        <div className="form-grid">
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label>
            Category
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {[
                "Velocity",
                "Account takeover",
                "Card-not-present",
                "Merchant anomaly",
              ].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Evidence document
            <select value={ref} onChange={(e) => setRef(e.target.value)}>
              <option value="">Select document</option>
              {docs?.map((d: Row) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Sharing
            <select
              value={sharing}
              onChange={(e) => setSharing(e.target.value)}
            >
              <option value="private">Private to institution</option>
              <option value="consortium">Consortium after approval</option>
            </select>
          </label>
        </div>
        <label>
          Pattern summary
          <textarea
            value={summary}
            onChange={(e) => setSummary(e.target.value)}
          />
        </label>
        <Action
          label="Submit for review"
          run={() =>
            api.post("/intelligence/contribute", {
              title,
              category,
              summary,
              evidence_refs: [ref],
              confidence: 0.75,
              sharing,
              privacy_classification: "synthetic",
              expires_at: new Date(Date.now() + 90 * 86400000).toISOString(),
            })
          }
          done={load}
        />
      </Card>
      <ErrorBox error={error} />
      <div className="bank-grid">
        {data?.map((r: Row) => (
          <Card
            key={r.id}
            title={r.title}
            sub={`${r.bank_id} · ${r.category}`}
            action={
              <Badge tone={r.status === "approved" ? "green" : "amber"}>
                {r.status}
              </Badge>
            }
          >
            <p>{r.summary}</p>
            <div className="meta">
              Confidence {pct(r.confidence)} · {r.sharing}
              <br />
              Review by {date(r.expires_at)}
            </div>
            {r.status === "pending" &&
              r.bank_id === user?.bank_id &&
              user?.role !== "analyst" && (
                <div className="actions">
                  <Action
                    label="Approve"
                    run={() =>
                      api.post(`/intelligence/${r.id}/review`, {
                        status: "approved",
                      })
                    }
                    done={load}
                  />
                  <Action
                    label="Reject"
                    run={() =>
                      api.post(`/intelligence/${r.id}/review`, {
                        status: "rejected",
                      })
                    }
                    done={load}
                  />
                </div>
              )}
          </Card>
        ))}
      </div>
    </>
  );
}
