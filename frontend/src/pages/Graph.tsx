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

export default function Graph() {
  const { data, error } = useData("/graph/patterns");
  return (
    <>
      <Header
        eyebrow="PATTERN KNOWLEDGE GRAPH"
        title="Explore the connections."
        description="Evidence-backed relationships across permitted intelligence. Associations are not proof of coordinated activity."
      />
      <ErrorBox error={error} />
      <Card
        title="Intelligence network"
        sub="NetworkX analysis · React Flow visualization"
      >
        <div className="graph">
          {data?.nodes.length ? (
            <ReactFlow
              nodes={data.nodes.map((n: Row, i: number) => ({
                id: n.id,
                data: { label: n.label },
                position: { x: (i % 4) * 240, y: Math.floor(i / 4) * 130 },
                style: {
                  background:
                    n.type === "bank"
                      ? "#14233f"
                      : n.type === "category"
                        ? "#e5f5f1"
                        : "white",
                  color: n.type === "bank" ? "white" : "#253451",
                  border: "1px solid #ccd7e8",
                  borderRadius: 9,
                  padding: 10,
                },
              }))}
              edges={data.edges.map((e: Row, i: number) => ({
                ...e,
                id: String(i),
                label: e.relation.split("_")[0].toLowerCase(),
                style: { stroke: "#9baecc" },
              }))}
              fitView
            >
              <Background />
              <Controls />
            </ReactFlow>
          ) : (
            <Empty text="No approved intelligence relationships available." />
          )}
        </div>
        <p className="hint">
          {data?.communities.length ?? 0} analytical communities · Degree
          centrality available through the graph API
        </p>
      </Card>
    </>
  );
}
