import "./App.css";

import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

const API_BASE_URL = "http://127.0.0.1:8000";


const layoutPolish = `
.impact-banner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 32px;
  align-items: center;
  padding: 22px 24px;
  margin-bottom: 18px;
  border: 1px solid #242731;
  border-radius: 14px;
  background: linear-gradient(135deg, #111217 0%, #0d0e12 100%);
}
.impact-copy .section-label { display:block; margin-bottom:8px; }
.impact-copy h2 { margin:0; font-size:26px; line-height:1.2; letter-spacing:-.5px; }
.impact-copy p { margin:8px 0 0; max-width:760px; color:#858b99; font-size:13px; line-height:1.55; }
.impact-highlight { min-width:190px; padding-left:28px; border-left:1px solid #2a2d35; text-align:right; }
.impact-highlight span, .impact-highlight small { display:block; color:#777d8c; font-size:10px; letter-spacing:1.2px; }
.impact-highlight strong { display:block; margin:3px 0; font-size:27px; line-height:1; letter-spacing:-.5px; }
.impact-highlight small { letter-spacing:0; font-size:11px; }
.proof-grid { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(260px,.75fr); gap:16px; margin-bottom:18px; }
.proof-panel { min-height:0; }
.proof-flow { display:grid; grid-template-columns:1fr 28px 1fr 28px 1fr 28px 1fr; align-items:center; gap:6px; padding:18px 20px 20px; }
.proof-flow > div:not(.proof-arrow) { min-width:0; padding:12px 10px; border:1px solid #242731; border-radius:10px; background:#111217; }
.proof-flow span { display:block; color:#646b79; font-size:9px; letter-spacing:1px; margin-bottom:5px; }
.proof-flow strong { display:block; font-size:12px; letter-spacing:.4px; }
.proof-flow small { display:block; margin-top:3px; color:#777d8c; font-size:10px; line-height:1.3; }
.proof-arrow { color:#626977; text-align:center; font-size:16px; }
.safety-summary { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; padding:18px 20px 20px; }
.safety-summary > div { padding:14px 12px; border:1px solid #242731; border-radius:10px; background:#111217; }
.safety-summary strong { display:block; font-size:22px; line-height:1; }
.safety-summary span { display:block; margin-top:5px; color:#777d8c; font-size:10px; text-transform:uppercase; letter-spacing:.6px; }
.demo-panel { margin-top:18px; }
.demo-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; padding:0 20px 20px; }
.demo-card { min-width:0; padding:16px; border:1px solid #242731; border-radius:11px; background:#111217; }
.demo-status { display:inline-block; margin-bottom:9px; font-size:9px; font-weight:700; letter-spacing:1.1px; }
.demo-card strong { display:block; font-size:13px; }
.demo-card small { display:block; margin-top:5px; color:#777d8c; font-size:10px; line-height:1.4; }
.demo-action { display:flex; justify-content:space-between; align-items:center; margin-top:13px; padding-top:11px; border-top:1px solid #242731; font-size:10px; font-weight:700; letter-spacing:.4px; }
.demo-card em { display:block; margin-top:7px; color:#858b99; font-size:10px; line-height:1.35; }
.demo-success .demo-status { color:#69c38a; }
.demo-blocked .demo-status { color:#e47b7b; }
.demo-approval .demo-status { color:#d6a85c; }
@media (max-width: 900px) {
  .impact-banner, .proof-grid { grid-template-columns:1fr; }
  .impact-highlight { border-left:0; border-top:1px solid #2a2d35; padding:14px 0 0; text-align:left; }
  .proof-flow { grid-template-columns:1fr; }
  .proof-arrow { transform:rotate(90deg); }
  .demo-grid { grid-template-columns:1fr; }
  .safety-summary { grid-template-columns:1fr; }
}
`;

async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `API request failed: ${response.status}`;

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Keep the default message when the response is not JSON.
    }

    throw new Error(message);
  }

  return response.json();
}

function formatCurrency(value) {
  return `₹${Number(value || 0).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  })}`;
}

function formatCompactCurrency(value) {
  const amount = Number(value || 0);

  if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)}Cr`;
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)}L`;
  if (amount >= 1000) return `₹${(amount / 1000).toFixed(1)}K`;

  return formatCurrency(amount);
}

function getActionClass(action) {
  if (action === "RETRY_PAYMENT") return "action-retry";
  if (action === "CREATE_PAYMENT_LINK") return "action-link";
  if (action === "ESCALATE") return "action-escalate";
  return "action-neutral";
}

function getStatusClass(status) {
  if (status === "ALLOWED") return "status-allowed";
  if (status === "BLOCKED") return "status-blocked";
  if (status === "APPROVAL_REQUIRED") return "status-approval";
  return "status-neutral";
}

function getResultTitle(status) {
  if (status === "SUCCESS") return "Recovery Successful";
  if (status === "AWAITING_APPROVAL") return "Approval Required";
  if (status === "ESCALATED") return "Escalated to Merchant";
  if (status === "NO_ACTION") return "No Recovery Action";
  if (status === "FAILED") return "Recovery Attempt Failed";
  return "Recovery Attempt Completed";
}

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState("");
  const [activeView, setActiveView] = useState("overview");
  const [auditHistory, setAuditHistory] = useState([]);
  const [actionAnalytics, setActionAnalytics] = useState([]);
  const [failureAnalytics, setFailureAnalytics] = useState([]);
  const [policyAnalytics, setPolicyAnalytics] = useState([]);
  const [fraudAnalytics, setFraudAnalytics] = useState(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError("");

        const [
          dashboardData,
          transactionData,
          actionDataResponse,
          failureDataResponse,
          policyDataResponse,
          fraudDataResponse,
        ] = await Promise.all([
          apiRequest("/api/dashboard"),
          apiRequest("/api/transactions?limit=100&offset=0"),
          apiRequest("/api/analytics/actions"),
          apiRequest("/api/analytics/failure-reasons"),
          apiRequest("/api/analytics/policy"),
          apiRequest("/api/analytics/fraud"),
        ]);

        setDashboard(dashboardData);
        setTransactions(transactionData.transactions || []);
        setActionAnalytics(actionDataResponse.actions || []);
        setFailureAnalytics(failureDataResponse.failure_reasons || []);
        setPolicyAnalytics(policyDataResponse.policy || []);
        setFraudAnalytics(fraudDataResponse || null);
      } catch (err) {
        console.error(err);
        setError(
          "Unable to connect to ReviveAI backend. Make sure FastAPI is running on port 8000."
        );
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  async function handleExecuteRecovery() {
    if (!selectedTransaction || executing) return;

    try {
      setExecuting(true);
      setExecutionResult(null);
      setExecutionError("");

      const data = await apiRequest("/api/recovery/execute", {
        method: "POST",
        body: JSON.stringify({
          transaction_id: selectedTransaction.transaction_id,
        }),
      });

      const auditRecord = data.audit_record || data;
      setExecutionResult(auditRecord);
      setAuditHistory((current) => [auditRecord, ...current].slice(0, 25));
    } catch (err) {
      console.error(err);
      setExecutionError(
        err.message || "Unable to execute recovery action."
      );
    } finally {
      setExecuting(false);
    }
  }

  const filteredTransactions = useMemo(() => {
    return transactions.filter((transaction) => {
      const transactionId = transaction.transaction_id?.toLowerCase() || "";
      const failureReason = transaction.failure_reason?.toLowerCase() || "";
      const query = search.toLowerCase();

      return (
        (transactionId.includes(query) || failureReason.includes(query)) &&
        (filter === "ALL" || transaction.action === filter)
      );
    });
  }, [transactions, search, filter]);

  const actionData = useMemo(() => {
    const byAction = {};

    actionAnalytics.forEach((item) => {
      byAction[item.action] = item;
    });

    return [
      {
        name: "Retry",
        value: Number(byAction.RETRY_PAYMENT?.transactions || 0),
      },
      {
        name: "Payment Link",
        value: Number(byAction.CREATE_PAYMENT_LINK?.transactions || 0),
      },
      {
        name: "Escalate",
        value: Number(byAction.ESCALATE?.transactions || 0),
      },
    ];
  }, [actionAnalytics]);

  const failureReasonData = useMemo(() => {
    return failureAnalytics
      .map((item) => ({
        reason: item.failure_reason,
        risk: Number(item.revenue_at_risk || 0),
        count: Number(item.transactions || 0),
        recovered: Number(item.revenue_recovered || 0),
        label: item.failure_reason
          ?.replaceAll("_", " ")
          .replace("SUSPECTED", "")
          .trim(),
      }))
      .sort((a, b) => b.risk - a.risk);
  }, [failureAnalytics]);

  const safetyMetrics = useMemo(() => {
    const allowed = policyAnalytics.find((item) => item.policy_status === "ALLOWED");
    const blocked = policyAnalytics.find((item) => item.policy_status === "BLOCKED");

    return {
      allowed: Number(allowed?.transactions || 0),
      blocked: Number(blocked?.transactions || 0),
      fraudBlocked: Number(fraudAnalytics?.fraud_blocked || 0),
      fraudTransactions: Number(fraudAnalytics?.fraud_transactions || 0),
    };
  }, [policyAnalytics, fraudAnalytics]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo"><span>R</span></div>
        <h1>ReviveAI</h1>
        <p>Loading recovery intelligence...</p>
        <div className="loading-bar"><div /></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-screen">
        <div className="error-card">
          <div className="error-icon">!</div>
          <h1>ReviveAI</h1>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <style>{layoutPolish}</style>
      <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">R</div>
          <div>
            <div className="brand-name">ReviveAI</div>
            <div className="brand-subtitle">Revenue Intelligence</div>
          </div>
        </div>

        <nav className="navigation">
          <div className="nav-section-label">COMMAND CENTER</div>
          <button className={`nav-item ${activeView === "overview" ? "active" : ""}`} onClick={() => setActiveView("overview")}><span className="nav-icon">⌂</span>Overview</button>
          <button className={`nav-item ${activeView === "queue" ? "active" : ""}`} onClick={() => setActiveView("queue")}><span className="nav-icon">↻</span>Recovery Queue<span className="nav-count">{dashboard?.transactions_analyzed || transactions.length}</span></button>
          <button className={`nav-item ${activeView === "analytics" ? "active" : ""}`} onClick={() => setActiveView("analytics")}><span className="nav-icon">◈</span>Analytics</button>
          <div className="nav-section-label second">CONTROL</div>
          <button className={`nav-item ${activeView === "policies" ? "active" : ""}`} onClick={() => setActiveView("policies")}><span className="nav-icon">◇</span>Recovery Policies</button>
          <button className={`nav-item ${activeView === "audit" ? "active" : ""}`} onClick={() => setActiveView("audit")}><span className="nav-icon">✓</span>Audit Trail</button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="pulse-dot" />
            <div>
              <strong>System operational</strong>
              <small>AI recovery engine online</small>
            </div>
          </div>
          <div className="version">REVIVEAI · BUILD 01</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">COMMAND CENTER <span>/</span> {activeView.toUpperCase().replace("_", " ")}</div>
            <h1>{activeView === "overview" ? "Revenue Recovery" : activeView === "queue" ? "Recovery Queue" : activeView === "analytics" ? "Recovery Analytics" : activeView === "policies" ? "Recovery Policies" : "Audit Trail"}</h1>
            <p>{activeView === "overview" ? "AI-powered detection, decisioning and recovery of failed payments." : activeView === "queue" ? "Prioritized failed payments awaiting or eligible for recovery." : activeView === "analytics" ? "Measure recovery performance, exposure, and decision outcomes." : activeView === "policies" ? "Bounded rules that authorize or block automated recovery actions." : "Immutable-style execution records for every recovery workflow run."}</p>
          </div>
          <div className="header-status"><span className="pulse-dot" />Live</div>
        </header>

        {activeView === "overview" && (<>
        <section className="impact-banner">
          <div className="impact-copy">
            <span className="section-label">REVIVEAI REVENUE IMPACT</span>
            <h2>Turn failed payments into recoverable revenue.</h2>
            <p>
              ReviveAI analyzes failed payments, selects the safest permitted recovery action,
              executes it, and verifies the outcome.
            </p>
          </div>
          <div className="impact-highlight">
            <span>RECOVERED</span>
            <strong>{formatCompactCurrency(dashboard.revenue_recovered)}</strong>
            <small>{dashboard.recovery_rate_percent}% of revenue at risk</small>
          </div>
        </section>

        <section className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-top"><span>REVENUE AT RISK</span><span className="kpi-icon">₹</span></div>
            <div className="kpi-value">{formatCompactCurrency(dashboard.revenue_at_risk)}</div>
            <div className="kpi-description">Across {dashboard.transactions_analyzed} failed payments</div>
          </div>

          <div className="kpi-card recovery-card">
            <div className="kpi-top"><span>REVENUE RECOVERED</span><span className="kpi-icon">↗</span></div>
            <div className="kpi-value">{formatCompactCurrency(dashboard.revenue_recovered)}</div>
            <div className="kpi-description positive">Capital successfully revived</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-top"><span>RECOVERY RATE</span><span className="kpi-icon">%</span></div>
            <div className="kpi-value">{dashboard.recovery_rate_percent}%</div>
            <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(dashboard.recovery_rate_percent, 100)}%` }} /></div>
          </div>

          <div className="kpi-card">
            <div className="kpi-top"><span>SUCCESSFUL RECOVERIES</span><span className="kpi-icon">✓</span></div>
            <div className="kpi-value">{dashboard.successful_recoveries}</div>
            <div className="kpi-description">Payments successfully revived</div>
          </div>
        </section>

        <section className="proof-grid">
          <div className="panel proof-panel">
            <div className="panel-header">
              <div><h2>Bounded Autonomy</h2><p>AI intelligence is separated from financial authority.</p></div>
              <span className="panel-tag">CONTROLLED</span>
            </div>
            <div className="proof-flow">
              <div><span>01</span><strong>AI</strong><small>Predicts recovery</small></div>
              <div className="proof-arrow">→</div>
              <div><span>02</span><strong>POLICY</strong><small>Authorizes action</small></div>
              <div className="proof-arrow">→</div>
              <div><span>03</span><strong>AGENT</strong><small>Executes safely</small></div>
              <div className="proof-arrow">→</div>
              <div><span>04</span><strong>VERIFY</strong><small>Confirms outcome</small></div>
            </div>
          </div>
          <div className="panel proof-panel">
            <div className="panel-header">
              <div><h2>Safety Posture</h2><p>Recovery is optimized within explicit guardrails.</p></div>
            </div>
            <div className="safety-summary">
              <div><strong>{safetyMetrics.fraudBlocked}</strong><span>fraud blocked</span></div>
              <div><strong>{safetyMetrics.blocked}</strong><span>policy blocked</span></div>
              <div><strong>{safetyMetrics.allowed}</strong><span>policy allowed</span></div>
            </div>
          </div>
        </section>

        <section className="charts-grid">
          <div className="panel large-panel">
            <div className="panel-header">
              <div><h2>Revenue Exposure</h2><p>Failed payment exposure by failure reason</p></div>
              <span className="panel-tag">LIVE DATA</span>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={failureReasonData} margin={{ top: 10, right: 10, left: 10, bottom: 35 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" angle={-18} textAnchor="end" height={65} tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={(value) => `₹${(value / 100000).toFixed(0)}L`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(value) => [formatCurrency(value), "Revenue at risk"]} />
                  <Bar dataKey="risk" radius={[6, 6, 0, 0]} fill="currentColor" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel action-panel">
            <div className="panel-header">
              <div><h2>AI Action Mix</h2><p>Decisions generated by policy engine</p></div>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={actionData} margin={{ top: 15, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="value" stroke="currentColor" fill="currentColor" fillOpacity={0.12} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="action-legend">
              <div><span className="legend-dot retry" />Retry Payment<strong>{actionData[0].value}</strong></div>
              <div><span className="legend-dot link" />Payment Link<strong>{actionData[1].value}</strong></div>
              <div><span className="legend-dot escalate" />Escalation<strong>{actionData[2].value}</strong></div>
            </div>
          </div>
        </section>

        <section className="panel queue-panel">
          <div className="panel-header queue-header">
            <div><h2>AI Recovery Queue</h2><p>Transactions analyzed by ReviveAI decision engine</p></div>
            <div className="queue-controls">
              <div className="search-box">
                <span>⌕</span>
                <input type="text" placeholder="Search transaction..." value={search} onChange={(event) => setSearch(event.target.value)} />
              </div>
              <select value={filter} onChange={(event) => setFilter(event.target.value)}>
                <option value="ALL">All actions</option>
                <option value="RETRY_PAYMENT">Retry</option>
                <option value="CREATE_PAYMENT_LINK">Payment Link</option>
                <option value="ESCALATE">Escalate</option>
              </select>
            </div>
          </div>

          <div className="table-wrapper">
            <table>
              <thead><tr><th>TRANSACTION</th><th>AMOUNT</th><th>FAILURE REASON</th><th>AI CONFIDENCE</th><th>DECISION</th><th>POLICY</th><th /></tr></thead>
              <tbody>
                {filteredTransactions.slice(0, 12).map((transaction) => (
                  <tr key={transaction.transaction_id} onClick={() => {
                    setSelectedTransaction(transaction);
                    setExecutionResult(null);
                    setExecutionError("");
                  }}>
                    <td><div className="transaction-id">{transaction.transaction_id}</div><div className="transaction-method">{transaction.payment_method}</div></td>
                    <td className="amount">{formatCurrency(transaction.amount)}</td>
                    <td><span className="reason-badge">{transaction.failure_reason?.replaceAll("_", " ")}</span></td>
                    <td>
                      <div className="confidence">
                        <div className="confidence-track"><div className="confidence-fill" style={{ width: `${Math.min(Number(transaction.recovery_probability || 0) * 100, 100)}%` }} /></div>
                        <span>{(Number(transaction.recovery_probability || 0) * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td><span className={`action-badge ${getActionClass(transaction.action)}`}>{transaction.action === "RETRY_PAYMENT" ? "RETRY" : transaction.action === "CREATE_PAYMENT_LINK" ? "PAYMENT LINK" : "ESCALATE"}</span></td>
                    <td><span className={`status-badge ${getStatusClass(transaction.policy_status)}`}>{transaction.policy_status}</span></td>
                    <td>
                      <button className="row-button" onClick={(event) => {
                        event.stopPropagation();
                        setSelectedTransaction(transaction);
                        setExecutionResult(null);
                        setExecutionError("");
                      }}>→</button>
                    </td>
                  </tr>
                ))}
                {filteredTransactions.length === 0 && <tr><td colSpan="7"><div style={{ padding: "28px", textAlign: "center", color: "#666a74" }}>No matching transactions.</div></td></tr>}
              </tbody>
            </table>
          </div>

          <div className="queue-footer">Showing {Math.min(filteredTransactions.length, 12)} of {filteredTransactions.length} loaded transactions · {dashboard?.transactions_analyzed || 0} failed payments analyzed</div>
        </section>

        <section className="panel demo-panel">
          <div className="panel-header">
            <div>
              <h2>Recovery Decision Examples</h2>
              <p>Three outcomes demonstrate how ReviveAI balances recovery opportunity with financial safety.</p>
            </div>
            <span className="panel-tag">DEMO READY</span>
          </div>
          <div className="demo-grid">
            <div className="demo-card demo-success">
              <span className="demo-status">RECOVER</span>
              <strong>High-confidence recovery</strong>
              <small>TIMEOUT · 83.94% probability</small>
              <div className="demo-action">RETRY PAYMENT <span>→</span></div>
              <em>Verify success → recover revenue</em>
            </div>
            <div className="demo-card demo-blocked">
              <span className="demo-status">BLOCK</span>
              <strong>Fraud protection</strong>
              <small>FRAUD SUSPECTED · low recovery probability</small>
              <div className="demo-action">AUTOMATION BLOCKED <span>×</span></div>
              <em>Escalate to merchant instead</em>
            </div>
            <div className="demo-card demo-approval">
              <span className="demo-status">CONTROL</span>
              <strong>High-value approval</strong>
              <small>₹50K+ transaction</small>
              <div className="demo-action">APPROVAL REQUIRED <span>→</span></div>
              <em>Merchant retains final authority</em>
            </div>
          </div>
        </section>

        <section className="bottom-grid">
          <div className="panel architecture-panel">
            <div className="panel-header"><div><h2>Recovery Intelligence Pipeline</h2><p>Every recovery passes through bounded decisioning and verification.</p></div></div>
            <div className="pipeline">
              <div className="pipeline-step"><span>01</span><strong>Detect</strong><small>Failed payment</small></div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step"><span>02</span><strong>Diagnose</strong><small>AI probability</small></div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step"><span>03</span><strong>Decide</strong><small>Policy engine</small></div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step"><span>04</span><strong>Act</strong><small>Recovery tool</small></div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step"><span>05</span><strong>Verify</strong><small>Outcome check</small></div>
            </div>
          </div>

          <div className="panel guardrail-panel">
            <div className="panel-header"><div><h2>Safety Controls</h2><p>Automated recovery guardrails</p></div></div>
            <div className="guardrail-list">
              <div><span className="guardrail-check">✓</span><div><strong>Fraud Protection</strong><small>{safetyMetrics.fraudBlocked} of {safetyMetrics.fraudTransactions} suspicious transactions blocked</small></div></div>
              <div><span className="guardrail-check">✓</span><div><strong>Retry Limit</strong><small>Maximum automatic retries enforced</small></div></div>
              <div><span className="guardrail-check">✓</span><div><strong>High-Value Approval</strong><small>₹50K+ transactions require approval</small></div></div>
              <div><span className="guardrail-check">✓</span><div><strong>Policy Gate</strong><small>{safetyMetrics.allowed} allowed · {safetyMetrics.blocked} blocked</small></div></div>
            </div>
          </div>
        </section>
        </>)}

        {activeView === "queue" && (<>
          <section className="panel queue-panel">
            <div className="panel-header queue-header">
              <div><h2>AI Recovery Queue</h2><p>Click any transaction to inspect and execute its bounded recovery workflow.</p></div>
              <div className="queue-controls">
                <div className="search-box"><span>⌕</span><input type="text" placeholder="Search transaction..." value={search} onChange={(event) => setSearch(event.target.value)} /></div>
                <select value={filter} onChange={(event) => setFilter(event.target.value)}>
                  <option value="ALL">All actions</option><option value="RETRY_PAYMENT">Retry</option><option value="CREATE_PAYMENT_LINK">Payment Link</option><option value="ESCALATE">Escalate</option>
                </select>
              </div>
            </div>
            <div className="table-wrapper"><table><thead><tr><th>TRANSACTION</th><th>AMOUNT</th><th>FAILURE REASON</th><th>AI CONFIDENCE</th><th>DECISION</th><th>POLICY</th><th /></tr></thead><tbody>
              {filteredTransactions.map((transaction) => (
                <tr key={transaction.transaction_id} onClick={() => { setSelectedTransaction(transaction); setExecutionResult(null); setExecutionError(""); }}>
                  <td><div className="transaction-id">{transaction.transaction_id}</div><div className="transaction-method">{transaction.payment_method}</div></td>
                  <td className="amount">{formatCurrency(transaction.amount)}</td><td><span className="reason-badge">{transaction.failure_reason?.replaceAll("_", " ")}</span></td>
                  <td><div className="confidence"><div className="confidence-track"><div className="confidence-fill" style={{ width: `${Math.min(Number(transaction.recovery_probability || 0) * 100, 100)}%` }} /></div><span>{(Number(transaction.recovery_probability || 0) * 100).toFixed(1)}%</span></div></td>
                  <td><span className={`action-badge ${getActionClass(transaction.action)}`}>{transaction.action === "RETRY_PAYMENT" ? "RETRY" : transaction.action === "CREATE_PAYMENT_LINK" ? "PAYMENT LINK" : "ESCALATE"}</span></td>
                  <td><span className={`status-badge ${getStatusClass(transaction.policy_status)}`}>{transaction.policy_status}</span></td>
                  <td><button className="row-button" onClick={(event) => { event.stopPropagation(); setSelectedTransaction(transaction); setExecutionResult(null); setExecutionError(""); }}>→</button></td>
                </tr>
              ))}
            </tbody></table></div>
            <div className="queue-footer">Showing {filteredTransactions.length} loaded transactions • API queue sample: 100 of {dashboard.transactions_analyzed}</div>
          </section>
        </>)}

        {activeView === "analytics" && (<>
          <section className="kpi-grid">
            <div className="kpi-card"><div className="kpi-top"><span>REVENUE AT RISK</span><span className="kpi-icon">₹</span></div><div className="kpi-value">{formatCompactCurrency(dashboard.revenue_at_risk)}</div><div className="kpi-description">{dashboard.transactions_analyzed} failed payments</div></div>
            <div className="kpi-card recovery-card"><div className="kpi-top"><span>REVENUE RECOVERED</span><span className="kpi-icon">↗</span></div><div className="kpi-value">{formatCompactCurrency(dashboard.revenue_recovered)}</div><div className="kpi-description positive">{dashboard.successful_recoveries} successful recoveries</div></div>
            <div className="kpi-card"><div className="kpi-top"><span>AUTOMATED ACTIONS</span><span className="kpi-icon">⚡</span></div><div className="kpi-value">{dashboard.automated_actions}</div><div className="kpi-description">Bounded actions authorized automatically</div></div>
            <div className="kpi-card"><div className="kpi-top"><span>FRAUD BLOCKED</span><span className="kpi-icon">✓</span></div><div className="kpi-value">{safetyMetrics.fraudBlocked}</div><div className="kpi-description">of {safetyMetrics.fraudTransactions} flagged transactions</div></div>
          </section>
          <section className="charts-grid">
            <div className="panel large-panel"><div className="panel-header"><div><h2>Revenue Exposure by Failure</h2><p>Full-dataset exposure and realized recovery.</p></div></div><div className="chart-container"><ResponsiveContainer width="100%" height="100%"><BarChart data={failureReasonData} margin={{ top: 10, right: 10, left: 10, bottom: 35 }}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="label" angle={-18} textAnchor="end" height={65} tick={{fontSize:11}}/><YAxis tickFormatter={(value)=>`₹${(value/100000).toFixed(0)}L`} tick={{fontSize:11}}/><Tooltip formatter={(value)=>[formatCurrency(value),"Revenue at risk"]}/><Bar dataKey="risk" radius={[6,6,0,0]} fill="currentColor"/></BarChart></ResponsiveContainer></div></div>
            <div className="panel action-panel"><div className="panel-header"><div><h2>Decision Distribution</h2><p>978 failed payments classified by recovery action.</p></div></div><div className="chart-container"><ResponsiveContainer width="100%" height="100%"><AreaChart data={actionData} margin={{top:15,right:10,left:-20,bottom:5}}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="name" tick={{fontSize:11}}/><YAxis tick={{fontSize:11}}/><Tooltip/><Area type="monotone" dataKey="value" stroke="currentColor" fill="currentColor" fillOpacity={0.12} strokeWidth={2}/></AreaChart></ResponsiveContainer></div><div className="action-legend"><div><span className="legend-dot retry"/>Retry Payment<strong>{actionData[0].value}</strong></div><div><span className="legend-dot link"/>Payment Link<strong>{actionData[1].value}</strong></div><div><span className="legend-dot escalate"/>Escalation<strong>{actionData[2].value}</strong></div></div></div>
          </section>
          <section className="panel queue-panel"><div className="panel-header"><div><h2>Failure Performance</h2><p>Recovery rate and recovered revenue by failure reason.</p></div></div><div className="table-wrapper"><table><thead><tr><th>FAILURE REASON</th><th>TRANSACTIONS</th><th>REVENUE AT RISK</th><th>RECOVERED</th><th>RECOVERY RATE</th></tr></thead><tbody>{failureReasonData.map(item=><tr key={item.reason}><td><span className="reason-badge">{item.label}</span></td><td>{item.count}</td><td className="amount">{formatCurrency(item.risk)}</td><td className="amount">{formatCurrency(item.recovered)}</td><td>{item.count ? `${((item.recovered/item.risk)*100).toFixed(1)}%` : "0.0%"}</td></tr>)}</tbody></table></div></section>
        </>)}

        {activeView === "policies" && (<>
          <section className="panel queue-panel"><div className="panel-header"><div><h2>Recovery Authorization Matrix</h2><p>AI predictions never execute directly. Policy determines what the agent is allowed to do.</p></div><span className="panel-tag">GUARDED EXECUTION</span></div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(2,minmax(0,1fr))",gap:"14px",padding:"20px"}}>
            {policyAnalytics.map(item=><div key={item.policy_status} style={{border:"1px solid #242731",borderRadius:"12px",padding:"18px",background:"#111217"}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"12px"}}><strong>{item.policy_status}</strong><span className={`status-badge ${getStatusClass(item.policy_status)}`}>{item.transactions} TXNS</span></div><div style={{fontSize:"28px",fontWeight:700}}>{formatCompactCurrency(item.revenue_at_risk)}</div><div style={{color:"#777d8c",fontSize:"12px",marginTop:"5px"}}>Revenue governed • {((item.recovery_rate || 0)*100).toFixed(1)}% recovery rate</div></div>)}
          </div></section>
          <section className="bottom-grid"><div className="panel architecture-panel"><div className="panel-header"><div><h2>Guardrail Rules</h2><p>Hard controls applied before money-moving actions.</p></div></div><div className="guardrail-list"><div><span className="guardrail-check">✓</span><div><strong>Fraud Protection</strong><small>69 / 69 suspicious transactions blocked</small></div></div><div><span className="guardrail-check">✓</span><div><strong>Retry Limit</strong><small>Maximum automatic retries enforced</small></div></div><div><span className="guardrail-check">✓</span><div><strong>High-Value Approval</strong><small>₹50K+ transactions require merchant approval</small></div></div><div><span className="guardrail-check">✓</span><div><strong>Outcome Verification</strong><small>Recovery is never assumed after execution</small></div></div></div></div><div className="panel guardrail-panel"><div className="panel-header"><div><h2>Operating Principle</h2><p>The separation of intelligence and authority.</p></div></div><div style={{padding:"20px",lineHeight:1.8,color:"#a3a8b5"}}><strong style={{color:"#fff"}}>AI recommends.</strong> Policy authorizes.<br/><strong style={{color:"#fff"}}>Tool executes.</strong> Verification confirms.<br/><strong style={{color:"#fff"}}>Audit trail records.</strong> Merchant retains control.</div></div></section>
        </>)}

        {activeView === "audit" && (<>
          <section className="panel queue-panel"><div className="panel-header"><div><h2>Recovery Audit Trail</h2><p>Execution records generated during this dashboard session.</p></div><span className="panel-tag">SESSION LOG</span></div>
          {auditHistory.length === 0 ? <div style={{padding:"50px 24px",textAlign:"center",color:"#777d8c"}}><div style={{fontSize:"30px",marginBottom:"12px"}}>✓</div><strong style={{color:"#fff"}}>No executions yet</strong><p>Execute a recovery action from the queue to create the first audit record.</p></div> : <div className="table-wrapper"><table><thead><tr><th>TRANSACTION</th><th>ACTION</th><th>POLICY</th><th>EXECUTION</th><th>VERIFICATION</th><th>RECOVERED</th></tr></thead><tbody>{auditHistory.map((record,index)=><tr key={`${record.transaction_id}-${index}`}><td><div className="transaction-id">{record.transaction_id}</div><div className="transaction-method">{record.failure_reason?.replaceAll("_"," ")}</div></td><td><span className={`action-badge ${getActionClass(record.action)}`}>{record.action?.replaceAll("_"," ")}</span></td><td><span className={`status-badge ${getStatusClass(record.policy_status)}`}>{record.policy_status}</span></td><td>{record.execution_success ? "SUCCESS" : "FAILED"}</td><td>{record.verification_status}</td><td className="amount">{formatCurrency(record.recovered_amount)}</td></tr>)}</tbody></table></div>}
          </section>
        </>)}

      </main>

      {selectedTransaction && (
        <div className="drawer-overlay" onClick={() => {
          if (!executing) {
            setSelectedTransaction(null);
            setExecutionResult(null);
            setExecutionError("");
          }
        }}>
          <aside className="transaction-drawer" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-header">
              <div><span className="drawer-label">AI RECOVERY DECISION</span><h2>{selectedTransaction.transaction_id}</h2></div>
              <button className="close-button" disabled={executing} onClick={() => {
                setSelectedTransaction(null);
                setExecutionResult(null);
                setExecutionError("");
              }}>×</button>
            </div>

            <div className="drawer-amount">{formatCurrency(selectedTransaction.amount)}</div>
            <div className="drawer-meta"><span>{selectedTransaction.payment_method}</span><span>{selectedTransaction.failure_reason?.replaceAll("_", " ")}</span></div>

            <div className="diagnosis-card">
              <div className="diagnosis-label">AI RECOVERY PROBABILITY</div>
              <div className="diagnosis-score">{(Number(selectedTransaction.recovery_probability || 0) * 100).toFixed(2)}<span>%</span></div>
              <div className="diagnosis-track"><div style={{ width: `${Number(selectedTransaction.recovery_probability || 0) * 100}%` }} /></div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"10px",marginTop:"14px"}}>
                <div style={{padding:"10px 12px",border:"1px solid #242731",borderRadius:"8px"}}><span style={{display:"block",fontSize:"10px",color:"#777d8c",letterSpacing:"1px"}}>FAILURE SIGNAL</span><strong style={{fontSize:"12px"}}>{selectedTransaction.failure_reason?.replaceAll("_"," ")}</strong></div>
                <div style={{padding:"10px 12px",border:"1px solid #242731",borderRadius:"8px"}}><span style={{display:"block",fontSize:"10px",color:"#777d8c",letterSpacing:"1px"}}>PREVIOUS RETRIES</span><strong style={{fontSize:"12px"}}>{selectedTransaction.retry_count ?? 0}</strong></div>
              </div>
              <p>ReviveAI estimates the probability that this failed payment can be successfully recovered.</p>
            </div>

            <div className="decision-section">
              <span className="section-label">EXPECTED RECOVERY VALUE</span>
              <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",padding:"14px 0 4px"}}>
                <strong style={{fontSize:"28px",letterSpacing:"-0.5px"}}>{formatCurrency(Number(selectedTransaction.amount || 0) * Number(selectedTransaction.recovery_probability || 0))}</strong>
                <span style={{fontSize:"12px",color:"#777d8c"}}>amount × AI probability</span>
              </div>
              <p style={{margin:0,color:"#777d8c",fontSize:"12px",lineHeight:1.5}}>Risk-adjusted revenue ReviveAI expects to recover before execution.</p>
            </div>

            <div className="decision-section">
              <span className="section-label">RECOMMENDED ACTION</span>
              <div className={`decision-action ${getActionClass(selectedTransaction.action)}`}>
                <strong>{selectedTransaction.action === "RETRY_PAYMENT" ? "RETRY PAYMENT" : selectedTransaction.action === "CREATE_PAYMENT_LINK" ? "CREATE PAYMENT LINK" : "ESCALATE TO MERCHANT"}</strong>
                <span>{selectedTransaction.policy_status}</span>
              </div>
            </div>

            <div className="decision-section">
              <span className="section-label">POLICY CHECKS</span>
              <div className="policy-checks">
                <div><span>✓</span>Recovery probability evaluated</div>
                <div><span>✓</span>Fraud guardrail evaluated</div>
                <div><span>✓</span>Retry limit evaluated</div>
                <div><span>✓</span>Transaction value evaluated</div>
              </div>
            </div>

            <div className="reason-box">
              <span>WHY THIS DECISION?</span>
              <p>{selectedTransaction.reason || `ReviveAI selected ${selectedTransaction.action} based on the predicted recovery probability and configured recovery policy.`}</p>
            </div>

            {!executionResult && !executionError && (
              <button className="execute-button" onClick={handleExecuteRecovery} disabled={executing}>
                {executing ? "Executing Recovery..." : "Execute Recovery Action"}
                <span>{executing ? "..." : "→"}</span>
              </button>
            )}

            {executionError && (
              <div className="execution-result execution-error">
                <div className="execution-result-icon">!</div>
                <div className="execution-result-content">
                  <strong>Recovery execution failed</strong>
                  <p>{executionError}</p>
                </div>
              </div>
            )}

            {executionResult && (
              <div className={`execution-result ${executionResult.verification_status === "SUCCESS" ? "execution-success" : "execution-warning"}`}>
                <div className="execution-result-icon">{executionResult.verification_status === "SUCCESS" ? "✓" : "!"}</div>
                <div className="execution-result-content">
                  <strong>{getResultTitle(executionResult.verification_status)}</strong>
                  <p>{executionResult.execution_message || "Recovery workflow completed."}</p>
                  <div className="result-recovered"><span>REVENUE RECOVERED</span><strong>{formatCurrency(executionResult.recovered_amount)}</strong></div>
                  <div className="verification-row"><span>VERIFICATION</span><strong>{executionResult.verification_status}</strong></div>
                </div>
              </div>
            )}

            <div className="drawer-note">AI recommends. Policy authorizes. Tool executes. Outcome is independently verified.</div>
          </aside>
        </div>
      )}
      </div>
    </>
  );
}

export default App;
