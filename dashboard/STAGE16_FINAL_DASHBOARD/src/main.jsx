import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import { api } from "./api.js";

const states = [
  { pos: 2, station: "LLH", delay: 15, dep: 17, time: "2024-09-26T08:10:00" },
  { pos: 3, station: "BEQ", delay: 16, dep: 18, time: "2024-09-26T08:14:00" },
  { pos: 4, station: "BLY", delay: 19, dep: 21, time: "2024-09-26T08:18:00" },
  { pos: 5, station: "BZL", delay: 17, dep: 19, time: "2024-09-26T08:22:00" },
  { pos: 6, station: "DKAE", delay: 20, dep: 22, time: "2024-09-26T08:27:00" }
];

const fallbackEtas = [
  ["BLY", "08:18", "8.65"], ["BZL", "08:22", "10.87"],
  ["DKAE", "08:31", "19.10"], ["GBRA", "08:34", "22.70"], ["JOX", "08:41", "29.40"]
];

const TRAIN = "12303";
const ROUTE_TOTAL = 231;

const DEMO_USERS = {
  PASSENGER: { username: "passenger123", password: "passenger123", name: "Passenger" },
  CONTROL_ROOM: { username: "control123", password: "control123", name: "Control Room" },
  CO_PILOT: { username: "copilot123", password: "copilot123", name: "Co-Pilot" }
};

const DELAY_REASONS = [
  "SIGNAL_ISSUE", "TRACK_OBSTRUCTION", "TECHNICAL_ISSUE", "OPERATIONAL_ISSUE",
  "PASSENGER_ISSUE", "WEATHER_ISSUE", "OTHER"
];

const ROLE_LABELS = { PASSENGER: "PASSENGER", CONTROL_ROOM: "CONTROL ROOM", CO_PILOT: "CO-PILOT" };

const SESSION_KEY = "sih26028_session";

function loadSession() {
  try { return JSON.parse(sessionStorage.getItem(SESSION_KEY)); } catch (err) { return null; }
}

function delayStatus(delay) {
  if (delay <= 0) return "ON TIME";
  if (delay <= 15) return "SLIGHTLY DELAYED";
  if (delay <= 60) return "DELAYED";
  return "HEAVILY DELAYED";
}

function delaySeverity(delay) {
  if (delay <= 5) return "LOW";
  if (delay <= 15) return "MODERATE";
  if (delay <= 60) return "HIGH";
  return "CRITICAL";
}

function delayTrend(delay) {
  if (delay > 60) return "WORSENING";
  if (delay > 15 && delay <= 30) return "STABLE";
  return "IMPROVING";
}

function confLevel(score) {
  if (score >= 80) return "HIGH";
  if (score >= 60) return "MEDIUM";
  return "LOW";
}

function viewForRole(role) {
  if (role === "CONTROL_ROOM") return "control";
  if (role === "CO_PILOT") return "copilot";
  return "passenger";
}

/* ============================== APP ============================== */

function App() {
  const [session, setSession] = useState(loadSession);
  const [view, setView] = useState(null);
  const [picker, setPicker] = useState(null);
  const [health, setHealth] = useState("CHECKING");

  useEffect(() => { setView(session ? viewForRole(session.role) : "landing"); }, [session]);

  useEffect(() => {
    api.checkHealth().then(() => setHealth("LIVE")).catch(() => setHealth("SIM"));
  }, []);

  function handleLogin(nextSession) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
  }

  function handleLogout() {
    if (session) api.logout(session.token).catch(() => {});
    sessionStorage.removeItem(SESSION_KEY);
    setSession(null);
  }

  if (!session || !view) {
    if (view === "login") {
      return <LoginView picker={picker} onLogin={handleLogin} onBack={() => setView("landing")} />;
    }
    return <LandingView health={health} onPick={(role) => { setPicker(role); setView("login"); }} />;
  }

  return (
    <DashboardShell session={session} health={health} onLogout={handleLogout}>
      {session.role === "CONTROL_ROOM" && <ControlRoomDashboard session={session} />}
      {session.role === "CO_PILOT" && <CoPilotDashboard session={session} />}
      {session.role === "PASSENGER" && <PassengerDashboard session={session} />}
    </DashboardShell>
  );
}

/* ========================= LANDING + LOGIN ========================= */

const roleCards = [
  { role: "PASSENGER", letter: "P", title: "Passenger Journeys",
    desc: "Real-time ETA, delay status, arrival assistance and journey advisories for train 12303." },
  { role: "CONTROL_ROOM", letter: "C", title: "Control Room",
    desc: "Delay control desk: active trains, delay severity alerts and co-pilot delay reports." },
  { role: "CO_PILOT", letter: "CP", title: "Co-Pilot",
    desc: "Report operational delays from the cab directly to the Control Room." }
];

function LandingView({ health, onPick }) {
  return (
    <div className="authView">
      <Topbar health={health} />
      <div className="facade">
        <div className="fTitle">DYNAMIC ETA CONTROL CENTER</div>
        <div className="fSub">SIH26028 role-based prototype • Train 12303 (LLH - DKAE) • FastAPI + LightGBM + React</div>
        <div className="roleCards">
          {roleCards.map((card) => (
            <button key={card.role} className="roleCard" onClick={() => onPick(card.role)}>
              <div className="roleLetter">{card.letter}</div>
              <h2>{card.title}</h2>
              <p>{card.desc}</p>
              <div className="roleGo">SIGN IN FOR {ROLE_LABELS[card.role]}</div>
            </button>
          ))}
        </div>
        <div className="loginHint">Demo accounts: passenger123 / control123 / copilot123 (password = username)</div>
      </div>
    </div>
  );
}

function LoginView({ picker, onLogin, onBack }) {
  const demo = DEMO_USERS[picker];
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function submit(ev) {
    ev.preventDefault();
    setBusy(true);
    setError("");
    api.login(username.trim(), password)
      .then((sess) => onLogin(sess))
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false));
  }

  return (
    <div className="authView">
      <Topbar health="LIVE" />
      <div className="facade">
        <div className="fTitle">ROLE SIGN IN — {ROLE_LABELS[picker]}</div>
        <div className="fSub">Prototype authentication • accounts are demo only</div>
        <div className="loginCard">
          <form onSubmit={submit}>
            <label>Username</label>
            <input className="formInput" value={username} onChange={(ev) => setUsername(ev.target.value)} autoFocus />
            <label>Password</label>
            <input className="formInput" type="password" value={password} onChange={(ev) => setPassword(ev.target.value)} />
            {error && <div className="formError">{error}</div>}
            <button className="btnPrimary" disabled={busy}>{busy ? "SIGNING IN..." : `SIGN IN ${ROLE_LABELS[picker]}`}</button>
          </form>
          <div className="demoPrompt">
            Demo credentials:
            {Object.entries(DEMO_USERS).map(([role, d]) => (
              <button
                key={role}
                type="button"
                onClick={() => { setUsername(d.username); setPassword(d.password); setError(""); }}
              >
                {d.name}: {d.username}
              </button>
            ))}
          </div>
          <button className="btnGhost" onClick={onBack}>BACK</button>
        </div>
      </div>
    </div>
  );
}

/* ======================== DASHBOARD SHELL ========================= */

function DashboardShell({ session, health, onLogout, children }) {
  const role = session.role;
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">SIH<span>26028</span></div>
        <div className="brandSub">DYNAMIC ETA CONTROL</div>
        <div className="roleBadge roleBadgeActive">{ROLE_LABELS[role]}</div>
        <div className="sideUser">{session.display_name || session.username}</div>
        <nav>
          <div className="navTitle">SESSION</div>
          <div className="navMuted">Token active</div>
        </nav>
        <button className="logoutBtn" onClick={onLogout}>LOGOUT</button>
        <div className="sideFooter">Prototype • Railway Intelligence</div>
      </aside>
      <main className="content">
        <header>
          <div>
            <h1>{headerTitle(role)}</h1>
            <p>{headerSub(role)}</p>
          </div>
          <div className="headerRight">
            <div className={`liveBadge ${health === "LIVE" ? "live" : ""}`}>
              <i /> {health === "LIVE" ? "LIVE API" : health === "SIM" ? "DEMO SIMULATION" : "CHECKING API"}
            </div>
            <div className="roleBadge">{ROLE_LABELS[role]}</div>
          </div>
        </header>
        {children}
        <footer>Prototype data: simulated/recorded train states • ETA model: validated LightGBM (unmodified by reports) • Role auth: demo only • Backend: FastAPI</footer>
      </main>
    </div>
  );
}

function headerTitle(role) {
  if (role === "CONTROL_ROOM") return "Control Room — Delay Control Desk";
  if (role === "CO_PILOT") return "Co-Pilot — Cab Delay Report";
  return "Passenger — Journey & ETA";
}

function headerSub(role) {
  if (role === "CONTROL_ROOM") return "Active trains • severity alerts • co-pilot delay reports";
  if (role === "CO_PILOT") return "Report operational delays from the cab to the Control Room";
  return "Live ETA • delay status • arrival assistance (train 12303)";
}

/* ====================== COMMON UI PIECES ========================= */

function Metric({ value, label }) {
  return <div className="metric"><strong>{value}</strong><span>{label}</span></div>;
}

function Badge({ label }) {
  return <span className={`badge badge${String(label).toUpperCase()}`}>{label}</span>;
}

function Topbar({ health }) {
  return (
    <div className="topbar">
      <div className="topbarBrand">SIH <b>26028</b> — Dynamic ETA Control Center</div>
      <div className={`liveBadge ${health === "LIVE" ? "live" : ""}`}>
        <i /> {health === "LIVE" ? "LIVE API" : health === "SIM" ? "DEMO SIMULATION" : "CHECKING API"}
      </div>
    </div>
  );
}

/* ====================== PASSENGER DASHBOARD ====================== */

function PassengerDashboard({ session }) {
  const [index, setIndex] = useState(0);
  const [apiResult, setApiResult] = useState(null);
  const [assistResult, setAssistResult] = useState(null);
  const [engineLive, setEngineLive] = useState(false);
  const [crewReport, setCrewReport] = useState(null);
  const state = states[index];

  useEffect(() => {
    api.fetchTrainStatus(TRAIN, session.token)
      .then((data) => setCrewReport(data.latest_delay_report || null))
      .catch(() => setCrewReport(null));
  }, [session]);

  const confidence = useMemo(() => {
    let score = 100;
    if (state.delay > 60) score -= 5;
    if (state.delay > 120) score -= 15;
    if (state.delay > 180) score -= 25;
    if (state.pos < 5) score -= 10;
    return Math.max(0, Math.min(100, score));
  }, [state]);

  const etas = apiResult?.prediction?.upcoming_stations?.length
    ? apiResult.prediction.upcoming_stations
    : fallbackEtas.map(([station, eta, remaining]) => ({
        station, eta, remaining_minutes: Number(remaining), route_position: null
      }));

  async function refreshFromApi() {
    try {
      const data = await api.fetchEta({
        train_number: TRAIN,
        current_station: state.station,
        current_route_position: state.pos,
        current_arrival_delay: state.delay,
        current_departure_delay: state.dep,
        current_time: state.time
      }, session.token);
      setApiResult(data);
      setEngineLive(true);
    } catch (err) {
      setApiResult(null);
      setEngineLive(false);
      alert(`FastAPI ETA engine unreachable (${err.message}). Showing built-in demo simulation.`);
    }
  }

  async function refreshAssistFromApi() {
    try {
      const data = await api.fetchAssistance({
        train_number: TRAIN,
        boarding_station: "LLH",
        destination_station: "BZL",
        current_route_position: state.pos,
        current_arrival_delay: state.delay,
        current_departure_delay: state.dep,
        current_time: state.time
      }, session.token);
      setAssistResult(data);
    } catch (err) {
      setAssistResult(null);
      alert(`FastAPI passenger-assistance unreachable (${err.message}). Showing built-in demo.`);
    }
  }

  function nextState() {
    setIndex((i) => (i + 1) % states.length);
    setApiResult(null);
    setAssistResult(null);
    setEngineLive(false);
  }

  const destinationEta = assistResult?.predicted_eta || etas[1]?.eta || "08:22";
  const destinationRemaining = assistResult?.remaining_minutes ?? etas[1]?.remaining_minutes ?? 10.87;
  const destinationDelay = assistResult?.current_delay_minutes ?? state.delay;

  return (
    <>
      <section className="panel overview">
        <div className="panelTitle">
          <div><span className="eyebrow">CURRENT TRAIN STATE</span><h2>Train {TRAIN} — LLH → BZL</h2></div>
          <span className="status">{delayStatus(state.delay)}</span>
        </div>
        <div className="metrics">
          <Metric value={state.station} label="CURRENT STATION" />
          <Metric value={`${state.delay} min`} label="CURRENT DELAY" />
          <Metric value={`${Math.max(0, ROUTE_TOTAL - state.pos)}`} label="STATIONS AHEAD" />
          <Metric value={`P${state.pos}`} label="ROUTE POSITION" />
          <Metric value={engineLive ? "CONNECTED" : "SIMULATION"} label="ETA ENGINE" />
        </div>
      </section>

      {crewReport && (
        <section className="panel alertPanel">
          <div className="panelTitle">
            <div><span className="eyebrow">CREW ADVISORY</span><h2>Operational Delay Report</h2></div>
            <Badge label={crewReport.priority} />
          </div>
          <div className="alertCard">
            <div><span>At {crewReport.current_station}</span><b>{crewReport.reason}</b></div>
            <p>{crewReport.message}</p>
            <div className="streamNote">Reported by the train crew — {new Date(crewReport.timestamp).toLocaleString()}.</div>
          </div>
        </section>
      )}

      <section className="panel">
        <div className="panelTitle">
          <div><span className="eyebrow">PREDICTION STREAM</span><h2>Dynamic ETA Timeline</h2></div>
          <span className="updated">State {index + 1} / {states.length}</span>
        </div>
        <div className="timeline">
          {etas.slice(0, 5).map((item, i) => (
            <div className="etaRow" key={item.station || i}>
              <div className="station"><b>{i + 1}</b><strong>{item.station}</strong></div>
              <div><span className="muted">Predicted ETA</span><strong>{item.eta || "—"}</strong></div>
              <div><span className="muted">Remaining</span><strong>{Number(item.remaining_minutes ?? 0).toFixed(2)} min</strong></div>
            </div>
          ))}
        </div>
        <div className="streamNote">● ETA values refresh when train station, route position, or delay state changes.</div>
        <div className="controls">
          <button onClick={nextState}>SIMULATE NEXT STATE</button>
          <button onClick={refreshFromApi}>REFRESH ETA FROM API</button>
        </div>
      </section>

      <div className="bottomGrid">
        <section className="panel">
          <div className="panelTitle"><div><span className="eyebrow">PASSENGER JOURNEY</span><h2>LLH → BZL</h2></div></div>
          <div className="journey">
            <div><span>Destination ETA</span><b>{destinationEta}</b></div>
            <div><span>Remaining</span><b>{Number(destinationRemaining).toFixed(2)} min</b></div>
            <div><span>Arrival status</span><b>{delayStatus(destinationDelay) === "ON TIME" ? "ON TIME" : "APPROACHING"}</b></div>
            <div><span>Connection</span><b>AVAILABLE</b></div>
          </div>
          <div className="passengerMessage">
            {assistResult?.message || `Train ${TRAIN} is currently ${delayStatus(state.delay).toLowerCase()} with a ${state.delay} minute delay.`}
          </div>
        </section>

        <section className="panel">
          <div className="panelTitle"><div><span className="eyebrow">OPERATIONAL INTELLIGENCE</span><h2>System Health</h2></div></div>
          <div className="ops">
            <div><span>ETA Confidence</span><b>{confLevel(confidence)} <small>{confidence}/100</small></b></div>
            <div><span>Delay Status</span><b>{delaySeverity(state.delay)}</b></div>
            <div><span>Delay Trend</span><b>{delayTrend(state.delay)}</b></div>
            <div><span>Passenger Assist</span><b>{assistResult ? "API" : "SIMULATION"}</b></div>
          </div>
          <div className="controls">
            <button onClick={refreshAssistFromApi}>REFRESH ASSISTANCE FROM API</button>
          </div>
        </section>
      </div>
    </>
  );
}

/* ==================== CONTROL ROOM DASHBOARD ===================== */

function ControlRoomDashboard({ session }) {
  const [reports, setReports] = useState([]);
  const [reportsError, setReportsError] = useState("");
  const [trainStatus, setTrainStatus] = useState(null);
  const [busyId, setBusyId] = useState(null);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;
    const load = async () => {
      try {
        const data = await api.fetchReports(session.token);
        if (!cancelled) { setReports(data.reports || []); setReportsError(""); }
      } catch (err) { if (!cancelled) setReportsError(err.message); }
    };
    load();
    const id = setInterval(load, 3000);
    return () => { cancelled = true; clearInterval(id); };
  }, [session]);

  useEffect(() => {
    api.fetchTrainStatus(TRAIN, session.token)
      .then(setTrainStatus)
      .catch(() => setTrainStatus(null));
  }, [session]);

  function acknowledge(reportId) {
    setBusyId(reportId);
    api.acknowledgeReport(reportId, session.token)
      .then(() => api.fetchReports(session.token))
      .then((data) => setReports(data.reports || []))
      .catch((err) => setReportsError(err.message))
      .finally(() => setBusyId(null));
  }

  const cs = trainStatus?.current_state || { current_station: "UNKNOWN", current_delay_minutes: 0 };
  const delay = cs.current_delay_minutes;
  const alerts = [
    { label: "DELAY SEVERITY", value: delaySeverity(delay), tone: delay >= 60 ? "severe" : "ok" },
    { label: "TREND", value: delayTrend(delay) },
    { label: "UNACKNOWLEDGED REPORTS", value: reports.filter((r) => r.status === "NEW").length },
    { label: "TOTAL REPORTS", value: reports.length }
  ];

  return (
    <>
      <section className="panel overview">
        <div className="panelTitle">
          <div><span className="eyebrow">OFFICIAL TRAIN STATE</span><h2>Train {TRAIN}</h2></div>
          <span className="status">{delayStatus(delay)}</span>
        </div>
        <div className="metrics">
          <Metric value={cs.current_station} label="CURRENT STATION" />
          <Metric value={`${delay} min`} label="CURRENT DELAY" />
          <Metric value={trainStatus?.route?.route_length ?? "—"} label="ROUTE STATIONS" />
          <Metric value={alerts[2].value} label="UNACKNOWLEDGED" />
          <Metric value={cs.source || "recorded_demo"} label="STATE SOURCE" />
        </div>
      </section>

      <section className="panel">
        <div className="panelTitle">
          <div><span className="eyebrow">DELAY ALERTS</span><h2>Control Desk Priority Ladder</h2></div>
          <span className="updated">Auto-refresh 3s</span>
        </div>
        <div className="alertRow">
          <Badge label={delaySeverity(delay)} />
          <div>
            <b>{delayStatus(delay)}</b>
            <span>Train {TRAIN} at {cs.current_station} is {delay} min behind schedule.</span>
          </div>
        </div>
        <div className="ops">
          {alerts.map((a) => (
            <div key={a.label}><span>{a.label}</span><b>{a.value}</b></div>
          ))}
        </div>
      </section>

      <section className="panel">
        <div className="panelTitle">
          <div><span className="eyebrow">CO-PILOT DELAY REPORTS</span><h2>Incoming Crew Reports</h2></div>
          <span className="updated">{reports.length} total</span>
        </div>
        {reportsError && <div className="formError">API: {reportsError}</div>}
        {reports.length === 0 && !reportsError && (
          <div className="emptyState">NO CO-PILOT REPORTS YET — reports sent from the Co-Pilot dashboard appear here and auto-refresh every 3 seconds.</div>
        )}
        <div className="reportList">
          {reports.map((report) => (
            <ReportCard
              key={report.report_id}
              report={report}
              busy={busyId === report.report_id}
              onAck={() => acknowledge(report.report_id)}
            />
          ))}
        </div>
      </section>
    </>
  );
}

function ReportCard({ report, busy, onAck }) {
  const isNew = report.status === "NEW";
  return (
    <div className={isNew ? "reportCard reportNew" : "reportCard"}>
      <div className="reportHead">
        <Badge label={report.priority} />
        <span className={isNew ? "reportTag reportTagNew" : "reportTag"}>{report.status}</span>
        <span className="reportBy">Train {report.train_number} • {report.copilot_id}</span>
      </div>
      <div className="reportMeta">
        <span>At {report.current_station}</span>
        <span>{report.current_delay_minutes} min delay</span>
        <span>{report.reason}</span>
        <span>{new Date(report.timestamp).toLocaleString()}</span>
      </div>
      <p className="reportMsg">{report.message}</p>
      {report.acknowledged_by && (
        <div className="reportAck">ACKNOWLEDGED BY {report.acknowledged_by} {report.acknowledged_at && `at ${new Date(report.acknowledged_at).toLocaleString()}`}</div>
      )}
      <div className="controls">
        <button className="ghost" disabled={!isNew || busy} onClick={onAck}>
          {busy ? "ACKNOWLEDGING..." : isNew ? "ACKNOWLEDGE" : "ACKNOWLEDGED"}
        </button>
      </div>
    </div>
  );
}

/* ======================= CO-PILOT DASHBOARD ======================= */

function CoPilotDashboard({ session }) {
  const [state, setState] = useState(null);
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.fetchTrainStatus(TRAIN, session.token)
      .then(setState)
      .catch(() => setState(null));
  }, [session]);

  const cs = state?.current_state || { current_station: "BEQ", current_delay_minutes: 16 };

  async function sendReport() {
    if (!reason) { setError("Select a delay reason."); return; }
    if (!message.trim()) { setError("Enter a message for the Control Room."); return; }
    setBusy(true);
    setError("");
    try {
      const report = await api.submitDelayReport({
        train_number: TRAIN,
        current_station: cs.current_station,
        current_delay_minutes: cs.current_delay_minutes,
        reason,
        message: message.trim()
      }, session.token);
      setSent(report);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <section className="panel overview">
        <div className="panelTitle">
          <div><span className="eyebrow">REPORT SENT</span><h2>Control Room Notified</h2></div>
          <Badge label={sent.priority} />
        </div>
        <div className="metrics">
          <Metric value={`Train ${sent.train_number}`} label="TRAIN" />
          <Metric value={sent.current_station} label="STATION" />
          <Metric value={`${sent.current_delay_minutes} min`} label="DELAY" />
          <Metric value={sent.reason} label="REASON" />
          <Metric value={sent.status} label="STATUS" />
        </div>
        <div className="alertCard">
          <p>{sent.message}</p>
          <div className="reportMeta">
            <span>Report ID: {sent.report_id}</span>
            <span>{new Date(sent.timestamp).toLocaleString()}</span>
          </div>
        </div>
        <div className="streamNote">
          {sent.ml_models_modified === false
            ? "The trained LightGBM models were NOT modified. This event is recorded for the Control Room; any ETA refresh still uses the existing Dynamic ETA Engine."
            : "Report submitted."}
        </div>
        <div className="controls">
          <button onClick={() => { setSent(null); setMessage(""); setReason(""); }}>FILE ANOTHER REPORT</button>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="panel overview">
        <div className="panelTitle">
          <div><span className="eyebrow">MY TRAIN</span><h2>Train {TRAIN} — Position</h2></div>
          <span className="status">AT {cs.current_station}</span>
        </div>
        <div className="metrics">
          <Metric value={cs.current_station} label="CURRENT STATION" />
          <Metric value={`${cs.current_delay_minutes} min`} label="CURRENT DELAY" />
          <Metric value={state?.route?.route_length ?? "—"} label="ROUTE STATIONS" />
          <Metric value={cs.source || "recorded_demo"} label="STATE SOURCE" />
        </div>
      </section>

      <section className="panel">
        <div className="panelTitle">
          <div><span className="eyebrow">CAB DELAY REPORT</span><h2>Notify Control Room of a Delay</h2></div>
        </div>
        <div className="reasonGrid">
          {DELAY_REASONS.map((r) => (
            <button key={r} className={reason === r ? "reasonBtn reasonBtnActive" : "reasonBtn"} onClick={() => setReason(r)}>{r}</button>
          ))}
        </div>
        <label>Message to Control Room (max 500)</label>
        <textarea
          className="formInput formArea"
          rows="4"
          maxLength={500}
          value={message}
          placeholder="e.g. Signal clearing delayed at BEQ; starting off 16 minutes behind schedule."
          onChange={(ev) => setMessage(ev.target.value)}
        />
        {error && <div className="formError">{error}</div>}
        <div className="controls">
          <button className="btnPrimary" disabled={busy} onClick={sendReport}>
            {busy ? "SENDING TO CONTROL ROOM..." : "SEND TO CONTROL ROOM"}
          </button>
        </div>
        <div className="streamNote">● The report is recorded with a {delaySeverity(cs.current_delay_minutes)} priority (based on the current delay). It appears immediately on the Control Room dashboard.</div>
      </section>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);