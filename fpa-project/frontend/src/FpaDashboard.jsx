import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { 
  TrendingUp, AlertTriangle, CheckCircle, Database, ShieldAlert, 
  RefreshCw, Play, Pause, Send, Activity, DollarSign
} from 'lucide-react';

export default function FpaDashboard() {
  const [data, setData] = useState([]);
  const [recentEvents, setRecentEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedDep, setSelectedDep] = useState('D-202');
  const [amountInput, setAmountInput] = useState('15000');
  const [categoryInput, setCategoryInput] = useState('Software Licenses');
  const [vendorInput, setVendorInput] = useState('Google Cloud');
  const [formStatus, setFormStatus] = useState('');

  const [autoGenActive, setAutoGenActive] = useState(false);

  const fetchMetrics = () => {
    fetch('/api/v1/fpa/variance?days=30')
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch analytical reports from the backend.");
        return res.json();
      })
      .then((data) => {
        
        const sanitized = data.map(d => ({
          ...d,
          allocated_budget: parseFloat(d.allocated_budget || 0),
          actual_spent: parseFloat(d.actual_spent || 0),
          variance: parseFloat(d.variance || 0),
          burn_rate: parseFloat(d.burn_rate || 0)
        }));
        setData(sanitized);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMetrics();

    const interval = setInterval(() => {
      fetchMetrics();
    }, 4000); 

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!autoGenActive) return;

    const generator = setInterval(() => {
      const deps = ["D-101", "D-202", "D-303"];
      const categories = ["Payroll", "Software Licenses", "Travel", "Office Supplies"];
      const vendors = ["Workday", "AWS", "Google Cloud", "Stripe", "Uber", "WeWork"];
      
      const randomDep = deps[Math.floor(Math.random() * deps.length)];
      
      const randomAmount = randomDep === 'D-202' && Math.random() > 0.6 
        ? parseFloat((Math.random() * 45000 + 15000).toFixed(2))
        : parseFloat((Math.random() * 8000 + 500).toFixed(2));
      
      const payload = {
        transactionId: `tx-${Math.floor(Math.random() * 900000) + 100000}`,
        timestamp: (Date.now() / 1000).toString(),
        departmentId: randomDep,
        amount: randomAmount,
        currency: "USD",
        category: categories[Math.floor(Math.random() * categories.length)],
        vendor: vendors[Math.floor(Math.random() * vendors.length)]
      };

      fetch('/api/v1/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(() => {
        setRecentEvents(prev => [payload, ...prev].slice(0, 8));
      })
      .catch(() => {});
    }, 2500); 

    return () => clearInterval(generator);
  }, [autoGenActive]);

  const handleSubmitTransaction = (e) => {
    e.preventDefault();
    if (!amountInput || isNaN(amountInput) || parseFloat(amountInput) <= 0) {
      setFormStatus('Invalid amount');
      return;
    }

    const payload = {
      transactionId: `tx-${Math.floor(Math.random() * 900000) + 100000}`,
      timestamp: (Date.now() / 1000).toString(),
      departmentId: selectedDep,
      amount: parseFloat(amountInput),
      currency: "USD",
      category: categoryInput,
      vendor: vendorInput
    };

    setFormStatus('Submitting...');
    fetch('/api/v1/transactions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then((res) => {
        if (!res.ok) throw new Error("API rejection");
        return res.json();
      })
      .then((resData) => {
        setFormStatus(`Success! (Mode: ${resData.mode})`);
        setAmountInput('');
        setRecentEvents(prev => [payload, ...prev].slice(0, 8));
        fetchMetrics();
        setTimeout(() => setFormStatus(''), 3000);
      })
      .catch((err) => {
        setFormStatus(`Failed to connect to Ingestion API.`);
      });
  };

  const totalBudget = data.reduce((acc, curr) => acc + curr.allocated_budget, 0);
  const totalSpent = data.reduce((acc, curr) => acc + curr.actual_spent, 0);
  const totalVariance = totalBudget - totalSpent;
  const overallBurnRate = totalBudget > 0 ? (totalSpent / totalBudget) * 100 : 0;
  const breachedCount = data.filter(d => d.burn_rate > 100).length;

  const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444'];

  if (loading && data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 text-slate-100">
        <Activity className="w-12 h-12 text-indigo-500 animate-spin mb-4" />
        <p className="font-semibold text-lg tracking-wider">Syncing Corporate Ledger State...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-root">
      {}
      <header className="dashboard-header">
        <div className="header-title-area">
          <div className="app-logo">
            <Database className="logo-icon" />
          </div>
          <div>
            <h1>FP&A Real-Time Operations Console</h1>
            <p className="subtitle">Google Cloud Dataflow / Apache Beam Ledger Pipeline Demo</p>
          </div>
        </div>
        <div className="header-status-area">
          <div className="status-indicator">
            <span className="pulse-dot"></span>
            <span className="status-label">Active Streaming Channel</span>
          </div>
          <button onClick={() => { setLoading(true); fetchMetrics(); }} className="btn-refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </header>

      {}
      <main className="dashboard-content">
        
        {}
        <section className="metrics-grid">
          <div className="metric-card glass">
            <div className="metric-header">
              <span>TOTAL PORTFOLIO BUDGET</span>
              <DollarSign className="icon text-indigo" />
            </div>
            <h2>${totalBudget.toLocaleString()}</h2>
            <div className="metric-footer">
              <span className="tag text-indigo">Baseline Registry</span>
              <span>Allocated Limit</span>
            </div>
          </div>

          <div className="metric-card glass">
            <div className="metric-header">
              <span>AGGREGATED SPENT (30d)</span>
              <TrendingUp className="icon text-emerald" />
            </div>
            <h2 className={totalSpent > totalBudget ? "text-rose" : "text-emerald"}>
              ${totalSpent.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
            </h2>
            <div className="metric-footer">
              <span className={`tag ${overallBurnRate > 90 ? 'bg-rose' : 'bg-emerald'}`}>
                {overallBurnRate.toFixed(1)}% Burn
              </span>
              <span>Current Expenditure</span>
            </div>
          </div>

          <div className="metric-card glass">
            <div className="metric-header">
              <span>DEPARTMENT STATUS</span>
              {breachedCount > 0 ? (
                <ShieldAlert className="icon text-rose animate-bounce" />
              ) : (
                <CheckCircle className="icon text-emerald" />
              )}
            </div>
            <h2>{breachedCount} / {data.length}</h2>
            <div className="metric-footer">
              <span>{breachedCount > 0 ? 'Action Required' : 'All Divisions Compliant'}</span>
            </div>
          </div>
        </section>

        {}
        <section className="dashboard-split-row">
          
          {}
          <div className="panel-card glass chart-panel">
            <h3>Budget vs. Actual Variance</h3>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }} barGap={6}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e1e24" />
                  <XAxis dataKey="department_id" stroke="#71717a" fontSize={11} tickLine={false} />
                  <YAxis stroke="#71717a" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v/1000}k`} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0a0a0c', borderColor: '#27272a', borderRadius: '8px' }}
                    labelStyle={{ color: '#a1a1aa', fontWeight: 'bold' }}
                    itemStyle={{ color: '#fff' }}
                    formatter={(val) => [`$${parseFloat(val).toLocaleString()}`, '']}
                  />
                  <Legend verticalAlign="top" height={36} iconType="circle" />
                  <Bar dataKey="allocated_budget" name="Allocated Budget" fill="#27272a" radius={[3, 3, 0, 0]} barSize={16} />
                  <Bar dataKey="actual_spent" name="Actual Expenditure" fill="#7c3aed" radius={[3, 3, 0, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {}
          <div className="panel-card glass simulator-panel">
            <div className="panel-header-btn">
              <h3>Ingestion Load Simulator</h3>
              <button 
                onClick={() => setAutoGenActive(!autoGenActive)} 
                className={`btn-auto-gen ${autoGenActive ? 'active' : ''}`}
              >
                {autoGenActive ? (
                  <>
                    <Pause className="w-4 h-4 mr-1" /> Pause Stream
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-1" /> Auto-Generate Events
                  </>
                )}
              </button>
            </div>
            
            <form onSubmit={handleSubmitTransaction} className="simulator-form">
              <div className="form-group">
                <label>Target Cost Center</label>
                <select value={selectedDep} onChange={(e) => setSelectedDep(e.target.value)}>
                  {data.map(d => (
                    <option key={d.department_id} value={d.department_id}>
                      {d.department_id} - {d.department_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Amount (USD)</label>
                  <input 
                    type="number" 
                    value={amountInput} 
                    onChange={(e) => setAmountInput(e.target.value)} 
                    placeholder="e.g. 5000"
                  />
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <select value={categoryInput} onChange={(e) => setCategoryInput(e.target.value)}>
                    <option value="Software Licenses">Software Licenses</option>
                    <option value="Payroll">Payroll</option>
                    <option value="Travel">Travel</option>
                    <option value="Office Supplies">Office Supplies</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Vendor</label>
                <input 
                  type="text" 
                  value={vendorInput} 
                  onChange={(e) => setVendorInput(e.target.value)} 
                  placeholder="e.g. AWS, Zoom, Stripe"
                />
              </div>

              <button type="submit" className="btn-submit">
                <Send className="w-4 h-4 mr-2" /> Ingest Single Transaction
              </button>

              {formStatus && <p className="form-status-message">{formStatus}</p>}
            </form>
          </div>

        </section>

        {}
        <section className="dashboard-split-row">
          
          {}
          <div className="panel-card glass flex-2">
            <h3>Ledger Budget Compliance Status</h3>
            <div className="table-responsive">
              <table className="ledger-table">
                <thead>
                  <tr>
                    <th>Cost Center</th>
                    <th>Allotted Budget</th>
                    <th>Actual Spent</th>
                    <th>Variance Remaining</th>
                    <th>Burn Progress</th>
                    <th>Compliance</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((dep) => {
                    const isBreached = dep.burn_rate > 100;
                    const progressWidth = Math.min(dep.burn_rate, 100);
                    
                    let progressColor = 'bg-indigo';
                    if (dep.burn_rate > 90) progressColor = 'bg-rose';
                    else if (dep.burn_rate > 75) progressColor = 'bg-warning';

                    return (
                      <tr key={dep.department_id} className={isBreached ? "row-breached" : ""}>
                        <td>
                          <div className="dep-cell">
                            <span className="dep-id">{dep.department_id}</span>
                            <span className="dep-name">{dep.department_name}</span>
                          </div>
                        </td>
                        <td>${dep.allocated_budget.toLocaleString()}</td>
                        <td>${dep.actual_spent.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td className={dep.variance < 0 ? "text-rose text-bold" : "text-slate-400"}>
                          {dep.variance < 0 ? '-' : ''}${Math.abs(dep.variance).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                        </td>
                        <td>
                          <div className="progress-cell">
                            <span className="progress-value">{dep.burn_rate.toFixed(1)}%</span>
                            <div className="progress-track">
                              <div className={`progress-bar ${progressColor}`} style={{ width: `${progressWidth}%` }}></div>
                            </div>
                          </div>
                        </td>
                        <td>
                          {isBreached ? (
                            <span className="badge-breached">
                              <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Over Budget
                            </span>
                          ) : (
                            <span className="badge-compliant">
                              <CheckCircle className="w-3.5 h-3.5 mr-1" /> Safe
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {}
          <div className="panel-card glass flex-1 telemetry-panel">
            <div className="panel-header-row">
              <h3>Live Telemetry Stream</h3>
              <span className="live-pill">
                <span className="live-dot"></span> Live
              </span>
            </div>
            
            <div className="logs-scroller">
              {recentEvents.length === 0 ? (
                <div className="no-logs">
                  <p>No recent events. Use the simulator panel on the right to post events or trigger auto-load.</p>
                </div>
              ) : (
                recentEvents.map((evt, idx) => (
                  <div key={evt.transaction_id || idx} className="log-row animate-fade-in">
                    <div className="log-header">
                      <span className="log-id">{evt.transaction_id}</span>
                      <span className="log-time">{new Date().toLocaleTimeString()}</span>
                    </div>
                    <div className="log-body">
                      <span><strong>{evt.department_id}</strong> spent <strong>${parseFloat(evt.amount).toLocaleString()}</strong> in <em>{evt.category}</em></span>
                    </div>
                    <div className="log-footer">
                      <span>Vendor: {evt.vendor}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </section>

      </main>
    </div>
  );
}
