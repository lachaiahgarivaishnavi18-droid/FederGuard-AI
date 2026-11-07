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

export default function Analytics() {
  const { data, error } = useData("/analytics/federated-performance");
  return (
    <>
      <Header
        eyebrow="MODEL EVALUATION"
        title="Measure the tradeoffs."
        description="Metrics from an independent public synthetic holdout. These results do not establish real-bank performance."
      />
      <ErrorBox error={error} />
      <Card title="Model registry & evaluation">
        {data?.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Accuracy</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>ROC-AUC</th>
                  <th>PR-AUC</th>
                  <th>Noise</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r: Row) => (
                  <tr key={r.id}>
                    <td>v{r.version}</td>
                    {[
                      "accuracy",
                      "precision",
                      "recall",
                      "f1",
                      "roc_auc",
                      "pr_auc",
                    ].map((k) => (
                      <td key={k}>{pct(r.metrics[k])}</td>
                    ))}
                    <td>{r.privacy?.noise_multiplier ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty text="Complete a training round to populate measured analytics." />
        )}
      </Card>
      {data?.[0] && (
        <Card
          title="Latest confusion matrix"
          sub="Rows: actual [normal, fraud] · Columns: predicted [normal, fraud]"
        >
          <div className="matrix">
            {data[0].metrics.confusion_matrix
              .flat()
              .map((n: number, i: number) => (
                <div key={i}>
                  <small>
                    {
                      [
                        "True negative",
                        "False positive",
                        "False negative",
                        "True positive",
                      ][i]
                    }
                  </small>
                  <strong>{n}</strong>
                </div>
              ))}
          </div>
          <p>
            False positive rate {pct(data[0].metrics.false_positive_rate)} ·
            False negative rate {pct(data[0].metrics.false_negative_rate)} ·
            Brier score {data[0].metrics.brier_score.toFixed(4)}
          </p>
        </Card>
      )}
      <div className="notice">
        Use the evaluation CLI for local-only versus federated versus
        centralized synthetic benchmarks and privacy-utility experiments. Each
        experiment writes measured JSON reports.
      </div>
    </>
  );
}
