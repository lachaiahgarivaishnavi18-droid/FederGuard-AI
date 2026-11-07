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

export default function Banks() {
  const { data, error, load } = useData("/banks"),
    [name, setName] = useState(""),
    [id, setId] = useState("");
  const { user } = useContext(Auth);
  return (
    <>
      <Header
        eyebrow="PARTICIPANT NETWORK"
        title="Independent banks. Connected defense."
        description="Manage participation and consent without accessing another bank’s local dataset."
      />
      <ErrorBox error={error} />
      <div className="bank-grid">
        {data?.map((b: Row, i: number) => (
          <Card key={b.id} title={b.name} sub={b.id}>
            <div className="bank-node">
              <Building2 size={36} />
              <Badge tone={b.active ? "green" : "gray"}>
                {b.active ? "ENROLLED" : "INACTIVE"}
              </Badge>
            </div>
            <dl>
              <dt>Data environment</dt>
              <dd>Isolated local store</dd>
              <dt>Sharing consent</dt>
              <dd>{b.consent ? "Enabled" : "Disabled"}</dd>
              <dt>Deployment</dt>
              <dd>Simulated node {i + 1}</dd>
            </dl>
            {user?.role === "admin" && (
              <div className="actions">
                <Action
                  label={b.active ? "Revoke" : "Activate"}
                  run={() =>
                    api.put("/banks/" + b.id, {
                      active: !b.active,
                      consent: b.consent,
                    })
                  }
                  done={load}
                />
                <Action
                  label={b.consent ? "Withdraw consent" : "Enable consent"}
                  run={() =>
                    api.put("/banks/" + b.id, {
                      active: b.active,
                      consent: !b.consent,
                    })
                  }
                  done={load}
                />
              </div>
            )}
          </Card>
        ))}
      </div>
      {user?.role === "admin" && (
        <Card
          title="Register institution"
          sub="Configure its endpoint and separate credentials in your environment before enrollment."
        >
          <div className="form-row">
            <input
              aria-label="Bank identifier"
              placeholder="bank_d"
              value={id}
              onChange={(e) => setId(e.target.value)}
            />
            <input
              aria-label="Bank display name"
              placeholder="Display name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Action
              label="Register bank"
              run={() => api.post("/banks", { id, name })}
              done={load}
            />
            <Action
              label="Enroll client"
              run={() => api.post(`/banks/${id}/enroll-client`)}
              done={load}
            />
          </div>
        </Card>
      )}
    </>
  );
}
