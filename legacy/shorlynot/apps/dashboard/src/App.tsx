import { useEffect, useState, useRef } from 'react';
import { Shield, ShieldAlert, Cpu, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

import './index.css';

type QBERData = {
  time: string;
  qber: number;
};

type EventLog = {
  id: string;
  title: string;
  time: string;
  detail: string;
};

function App() {
  const [executionMode] = useState('SIMULATION');
  const [qber, setQber] = useState(0.0214);
  const [eveActive, setEveActive] = useState(false);
  const [escalationLevel, setEscalationLevel] = useState(0);
  const [escalationLabel, setEscalationLabel] = useState('L0 — Normal');
  const [qberHistory, setQberHistory] = useState<QBERData[]>([]);
  const [events, setEvents] = useState<EventLog[]>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initial history
    const history = [];
    const now = new Date();
    for (let i = 20; i >= 0; i--) {
      history.push({
        time: new Date(now.getTime() - i * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}),
        qber: 0.02 + Math.random() * 0.01
      });
    }
    setQberHistory(history);

    // Fetch initial status
    fetch('http://127.0.0.1:8000/api/v1/security/status')
      .then(r => r.json())
      .then(d => {
        setQber(d.qber);
        setEveActive(d.eve_active);
        setEscalationLevel(d.escalation_level);
        setEscalationLabel(d.escalation_label);
      })
      .catch(e => console.error("Could not fetch initial status", e));

    // Connect to WebSocket
    ws.current = new WebSocket('ws://127.0.0.1:8000/api/v1/ws/events');
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const type = data.event_type;
        const payload = data.payload;
        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});

        if (type === 'attack') {
          if (payload.action === 'eve_activated') {
            setEveActive(true);
            addEvent('Eve Activated', time, payload.message);
          } else {
            setQber(payload.qber);
            setEscalationLevel(payload.escalation_level);
            setEscalationLabel(payload.escalation_label);
            addEvent('Attack Detected', time, `QBER spike to ${(payload.qber*100).toFixed(2)}%`);
            updateChart(time, payload.qber);
          }
        } else if (type === 'session' && payload.action === 'eve_deactivated') {
          setEveActive(false);
          addEvent('Eve Deactivated', time, 'Channel clear');
        } else if (type === 'session' && payload.action === 'system_reset') {
          setEveActive(false);
          setEscalationLevel(0);
          setEscalationLabel('L0 — Normal');
          setQber(0.02);
          addEvent('System Reset', time, 'Security status restored to SECURE');
          updateChart(time, 0.02);
        } else if (type === 'escalation' || type === 'lockdown') {
          addEvent(`Escalation L${payload.level}`, time, `${payload.action} (Port: ${payload.port}, IP: ${payload.ip})`);
        }
      } catch (e) {
        console.error("Error parsing WS message", e);
      }
    };

    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const addEvent = (title: string, time: string, detail: string) => {
    setEvents(prev => [{ id: Math.random().toString(), title, time, detail }, ...prev].slice(0, 15));
  };

  const updateChart = (time: string, newQber: number) => {
    setQberHistory(prev => [...prev.slice(1), { time, qber: newQber }]);
  };

  const getEscalationClass = () => {
    if (escalationLevel >= 4) return 'escalation-4';
    if (escalationLevel === 3) return 'escalation-3';
    if (escalationLevel === 2) return 'escalation-2';
    if (escalationLevel === 1) return 'escalation-1';
    return 'escalation-0';
  };

  const isDanger = qber > 0.08 || eveActive;

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="title-container">
          <h1>
            <Shield className="title-icon" size={36} />
            SHORLYNOT Q-EDGE
          </h1>
          <p className="subtitle">Quantum-Key-Bound Network Lease Enforcement Platform</p>
        </div>
        
        <div className="mode-badge">
          {executionMode} MODE
        </div>
      </header>

      {/* Escalation Strip */}
      <div className={`escalation-strip ${getEscalationClass()}`}>
        <AlertTriangle size={28} className={escalationLevel >= 4 ? 'bounce' : ''} />
        <span>SECURITY ESCALATION: {escalationLabel}</span>
      </div>

      <main className="dashboard-grid">
        
        {/* Quantum Operations Panel */}
        <section className="glass-panel" style={{ gridColumn: 'span 2' }}>
          <h2 className="panel-header">
            <Cpu className="panel-icon" size={24} />
            Live Quantum Telemetry
          </h2>
          
          <div className="metrics-grid">
             <div className="metric-card">
                <div className="metric-label">Eve Mode</div>
                <div className={`metric-value ${eveActive ? 'value-danger' : 'value-safe'}`}>
                  {eveActive ? '🔴 ACTIVE' : '🟢 OFF'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Current QBER</div>
                <div className={`metric-value ${qber > 0.08 ? 'value-danger' : 'value-safe'}`}>
                  {(qber * 100).toFixed(2)}%
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Status</div>
                <div className={`metric-value ${escalationLevel > 0 ? 'value-danger' : 'value-safe'}`}>
                  {escalationLevel > 0 ? 'COMPROMISED' : 'SECURE'}
                </div>
              </div>
          </div>

          {/* QBER Chart */}
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={qberHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="time" stroke="#8892b0" fontSize={12} tickMargin={10} />
                <YAxis stroke="#8892b0" fontSize={12} domain={[0, 0.3]} tickFormatter={(val) => `${(val*100).toFixed(0)}%`} tickMargin={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'rgba(15, 20, 30, 0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', backdropFilter: 'blur(10px)' }}
                  itemStyle={{ color: '#00f0ff', fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}
                  formatter={(val: any) => [`${(val*100).toFixed(2)}%`, 'QBER']}
                />
                <Line 
                  type="monotone" 
                  dataKey="qber" 
                  stroke={isDanger ? "#ff003c" : "#00f0ff"} 
                  strokeWidth={3} 
                  dot={false} 
                  activeDot={{ r: 6, fill: isDanger ? "#ff003c" : "#00f0ff", stroke: "#fff", strokeWidth: 2 }}
                  isAnimationActive={false} 
                  style={{ filter: `drop-shadow(0 0 8px ${isDanger ? 'rgba(255,0,60,0.5)' : 'rgba(0,240,255,0.5)'})` }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Security Events Panel */}
        <section className="glass-panel" style={{ maxHeight: 'calc(100vh - 250px)' }}>
          <h2 className="panel-header">
            <ShieldAlert className="panel-icon" size={24} />
            Security Events
          </h2>
          
          <div className="events-list">
            {events.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#8892b0', marginTop: '3rem', fontSize: '0.9rem' }}>Waiting for security events...</div>
            ) : (
              events.map((ev) => {
                const isEvDanger = ev.title.includes('Eve') || ev.title.includes('Attack') || ev.title.includes('Escalation');
                return (
                  <div key={ev.id} className={`event-item ${isEvDanger ? 'event-danger' : 'event-safe'}`}>
                    <div className="event-header">
                      <span className="event-title">{ev.title}</span>
                      <span className="event-time">{ev.time}</span>
                    </div>
                    <div className="event-detail">{ev.detail}</div>
                  </div>
                );
              })
            )}
          </div>
        </section>

      </main>
    </div>
  );
}

export default App;
