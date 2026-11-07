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

export default function Investigations() {
  const { data, error, load } = useData("/investigations"),
    [title, setTitle] = useState(""),
    [selected, setSelected] = useState<string | null>(null),
    [note, setNote] = useState(""),
    { user } = useContext(Auth);
  const current = data?.find((r: Row) => r.id === selected);
  return (
    <>
      <Header
        eyebrow="HUMAN REVIEW WORKSPACE"
        title="Every conclusion needs an investigator."
        description="Organize evidence, record notes and document a review. No automated account or transaction actions."
      />
      <Card title="Open investigation">
        <div className="form-row">
          <input
            aria-label="Case title"
            placeholder="Investigation title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Action
            label="Create case"
            run={() => api.post("/investigations", { title })}
            done={load}
          />
        </div>
      </Card>
      <ErrorBox error={error} />
      <div className="case-grid">
        <Card title="Your bank’s cases">
          {data?.length ? (
            data.map((r: Row) => (
              <button
                className={`case-item ${r.id === selected ? "selected" : ""}`}
                key={r.id}
                onClick={() => setSelected(r.id)}
              >
                <FolderSearch size={20} />
                <div>
                  <b>{r.title}</b>
                  <small>
                    {r.id.slice(0, 10)} · {date(r.created_at)}
                  </small>
                </div>
                <Badge tone={r.status === "CLOSED" ? "gray" : "amber"}>
                  {r.status}
                </Badge>
              </button>
            ))
          ) : (
            <Empty />
          )}
        </Card>
        <Card
          title={current?.title || "Select an investigation"}
          sub="Evidence and review history"
        >
          {current ? (
            <>
              <dl>
                <dt>Assigned reviewer</dt>
                <dd>{current.assigned_to || "Unassigned"}</dd>
                <dt>Evidence references</dt>
                <dd>{current.evidence_refs?.join(", ") || "None attached"}</dd>
              </dl>
              {user?.role !== "analyst" && (
                <label>
                  Human review outcome
                  <select
                    value={current.status}
                    onChange={async (e) => {
                      try {
                        await api.put(`/investigations/${current.id}/status`, {
                          status: e.target.value,
                        });
                        load();
                      } catch (err) {
                        alert(message(err));
                      }
                    }}
                  >
                    {[
                      "NEW",
                      "UNDER_REVIEW",
                      "ADDITIONAL_INFORMATION_REQUIRED",
                      "ESCALATED",
                      "CLOSED",
                      "FALSE_POSITIVE",
                      "INCONCLUSIVE",
                    ].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </label>
              )}
              <h3>Investigation notes</h3>
              {current.notes.map((n: Row, i: number) => (
                <div className="note" key={i}>
                  <p>{n.text}</p>
                  <small>{date(n.created_at)}</small>
                </div>
              ))}
              <textarea
                aria-label="New investigation note"
                placeholder="Record your assessment…"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <Action
                label="Add note"
                run={() =>
                  api.post(`/investigations/${current.id}/notes`, {
                    text: note,
                  })
                }
                done={() => {
                  setNote("");
                  load();
                }}
              />
              <details>
                <summary>Review history ({current.history.length})</summary>
                {current.history.map((h: Row, i: number) => (
                  <p key={i}>
                    {h.from} → {h.to}
                    <small>
                      {date(h.created_at)} · {h.reviewer}
                    </small>
                  </p>
                ))}
              </details>
            </>
          ) : (
            <Empty text="Choose a case to review its evidence and add notes." />
          )}
        </Card>
      </div>
    </>
  );
}
