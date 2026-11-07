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

export default function Knowledge() {
  const { data, error, load } = useData("/rag/documents"),
    [file, setFile] = useState<File | null>(null),
    [title, setTitle] = useState(""),
    [sharing, setSharing] = useState("private"),
    { user } = useContext(Auth);
  return (
    <>
      <Header
        eyebrow="EVIDENCE LIBRARY"
        title="A foundation for grounded answers."
        description="Permission-aware document retrieval with source provenance and passage citations."
      />
      <Card
        title="Add knowledge"
        sub="PDF, DOCX, TXT or Markdown · 5 MB maximum · text extraction only; OCR not configured"
      >
        <div className="form-row">
          <input
            aria-label="Document title"
            placeholder="Document title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <input
            aria-label="Document file"
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <select
            aria-label="Sharing permission"
            value={sharing}
            onChange={(e) => setSharing(e.target.value)}
          >
            <option value="private">Private to institution</option>
            <option value="consortium">Consortium / review required</option>
          </select>
          <Action
            label="Ingest document"
            run={() => {
              if (!file) throw Error("Select a document");
              const form = new FormData();
              form.append("file", file);
              form.append("title", title);
              form.append("sharing", sharing);
              return api.post("/rag/ingest", form);
            }}
            done={load}
          />
        </div>
      </Card>
      <ErrorBox error={error} />
      <Card
        title="Authorized documents"
        sub="Demo retrieval: BM25 + TF-IDF. Configure SentenceTransformers / FAISS and a cross-encoder for neural retrieval."
      >
        {data?.length ? (
          <table>
            <thead>
              <tr>
                <th>Document</th>
                <th>Source</th>
                <th>Version</th>
                <th>Permission</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.map((r: Row) => (
                <tr key={r.id}>
                  <td>
                    <FileText size={15} /> {r.title}
                  </td>
                  <td>{r.bank_id}</td>
                  <td>{r.version}</td>
                  <td>{r.sharing}</td>
                  <td>
                    <Badge tone={r.status === "pending" ? "amber" : "green"}>
                      {r.status}
                    </Badge>
                    {r.status === "pending" &&
                      r.bank_id === user?.bank_id &&
                      user?.role !== "analyst" && (
                        <Action
                          label="Approve"
                          run={() =>
                            api.post(`/rag/documents/${r.id}/review`, {
                              status: "approved",
                            })
                          }
                          done={load}
                        />
                      )}
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
