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

export default function Assistant() {
  const [question, setQuestion] = useState(
      "What patterns are associated with suspicious transaction velocity?",
    ),
    [answer, setAnswer] = useState<Row | null>(null);
  return (
    <>
      <Header
        eyebrow="GROUNDED INTELLIGENCE"
        title="Ask the evidence."
        description="An investigation assistant that retrieves authorized sources and makes uncertainty visible."
      />
      <Card
        title="Intelligence assistant"
        sub="Local extractive demo by default. External providers require configuration."
      >
        <div className="assistant-greeting">
          <span className="ai-icon">
            <MessagesSquare size={27} />
          </span>
          <h3>What would you like to investigate?</h3>
          <p>Start with a fraud typology, an indicator, or a procedure.</p>
        </div>
        <label>
          Your question
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
        </label>
        <Action
          label="Retrieve & explain"
          run={async () => {
            const r = await api.post("/ai/chat", { question });
            setAnswer(r.data);
          }}
        />
        {answer && (
          <div className="answer">
            <Badge tone="blue">{answer.provider.toUpperCase()}</Badge>
            <p className="preserve">{answer.answer}</p>
            <small>{answer.retrieval_mode}</small>
            <h3>Supporting evidence</h3>
            {answer.evidence.map((e: Row) => (
              <details key={e.chunk_id}>
                <summary>
                  {e.citation} {e.title} · page {e.page ?? "unavailable"}
                </summary>
                <p>{e.text}</p>
                <code>
                  {e.document_id} / {e.chunk_id}
                </code>
              </details>
            ))}
            <p className="hint">{answer.citation_validation}</p>
            <Action
              label="Download report"
              run={async () => {
                const blob = new Blob(
                  [
                    answer.answer +
                      "\n\n" +
                      answer.evidence
                        .map(
                          (e: Row) =>
                            `${e.citation} ${e.title} ${e.document_id}`,
                        )
                        .join("\n"),
                  ],
                  { type: "text/plain" },
                );
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = "federguard-investigation-summary.txt";
                a.click();
                URL.revokeObjectURL(a.href);
              }}
            />
          </div>
        )}
      </Card>
    </>
  );
}
