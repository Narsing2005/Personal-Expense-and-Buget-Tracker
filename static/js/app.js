const { useState, useEffect, useRef } = React;

// --- Categories Configuration ---
const CATEGORIES = [
  "Salary", "Freelance", "Investments",
  "Food & Dining", "Groceries", "Housing & Rent",
  "Utilities", "Transportation", "Healthcare",
  "Entertainment", "Shopping", "Education",
  "Personal Care", "Travel", "Savings & Investments", "Other"
];

// --- API Service Helper ---
const API = {
  getToken: () => localStorage.getItem("finora_token"),
  setToken: (token) => localStorage.setItem("finora_token", token),
  removeToken: () => localStorage.removeItem("finora_token"),

  headers: () => {
    const headers = { "Content-Type": "application/json" };
    const token = API.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  },

  async request(endpoint, options = {}) {
    const config = {
      ...options,
      headers: { ...API.headers(), ...(options.headers || {}) }
    };
    try {
      const res = await fetch(endpoint, config);
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || (data.errors && data.errors.join(", ")) || "Request failed");
      }
      return data;
    } catch (err) {
      throw err;
    }
  }
};

// ==========================================
// Main Finora App Component
// ==========================================
function FinoraApp() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(API.getToken());
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard"); // dashboard, transactions, budgets, reports
  const [toast, setToast] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationModalOpen, setNotificationModalOpen] = useState(false);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState(0);

  // Global Toast Dispatcher
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Check auth session on startup
  useEffect(() => {
    const verifyUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await API.request("/api/auth/me");
        setUser(res.user);
      } catch (err) {
        API.removeToken();
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    verifyUser();
  }, [token]);

  // Sync notifications count
  const refreshUnreadCount = async () => {
    if (!token) return;
    try {
      const res = await API.request("/api/notifications");
      setUnreadAlertsCount(res.unread_count || 0);
    } catch (err) {
      // ignore silently
    }
  };

  useEffect(() => {
    if (user) {
      refreshUnreadCount();
      const interval = setInterval(refreshUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleLogout = async () => {
    try {
      await API.request("/api/auth/logout", { method: "POST" });
    } catch (e) {}
    API.removeToken();
    setToken(null);
    setUser(null);
    showToast("You have been securely logged out.", "info");
  };

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center min-vh-100 bg-light">
        <div className="spinner-border text-teal" style={{ color: "#0d9488", width: "3rem", height: "3rem" }}></div>
      </div>
    );
  }

  if (!user) {
    return <AuthScreen onLoginSuccess={(u, t) => { setUser(u); setToken(t); showToast(`Welcome back, ${u.name}!`); }} showToast={showToast} />;
  }

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: "fixed", top: "20px", right: "20px", zIndex: 9999,
          background: toast.type === "danger" ? "#ef4444" : toast.type === "warning" ? "#f59e0b" : "#0d9488",
          color: "white", padding: "12px 20px", borderRadius: "10px",
          boxShadow: "0 10px 15px -3px rgba(0,0,0,0.2)", display: "flex", alignItems: "center", gap: "10px",
          fontWeight: 600, animation: "fadeIn 0.2s"
        }}>
          <i className={`fas ${toast.type === "danger" ? "fa-circle-exclamation" : toast.type === "warning" ? "fa-triangle-exclamation" : "fa-circle-check"}`}></i>
          {toast.message}
        </div>
      )}

      {/* Sidebar Navigation */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-brand">
          <div className="brand-icon">
            <i className="fas fa-wallet"></i>
          </div>
          <div className="brand-name">Fin<span>ora</span></div>
        </div>

        <ul className="sidebar-nav">
          <li>
            <button className={`nav-link-btn ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => { setActiveTab("dashboard"); setSidebarOpen(false); }}>
              <i className="fas fa-chart-pie"></i>
              <span>Dashboard</span>
            </button>
          </li>
          <li>
            <button className={`nav-link-btn ${activeTab === "transactions" ? "active" : ""}`} onClick={() => { setActiveTab("transactions"); setSidebarOpen(false); }}>
              <i className="fas fa-receipt"></i>
              <span>Transactions</span>
            </button>
          </li>
          <li>
            <button className={`nav-link-btn ${activeTab === "budgets" ? "active" : ""}`} onClick={() => { setActiveTab("budgets"); setSidebarOpen(false); }}>
              <i className="fas fa-bullseye"></i>
              <span>Monthly Budgets</span>
            </button>
          </li>
          <li>
            <button className={`nav-link-btn ${activeTab === "reports" ? "active" : ""}`} onClick={() => { setActiveTab("reports"); setSidebarOpen(false); }}>
              <i className="fas fa-chart-line"></i>
              <span>Reports & Analytics</span>
            </button>
          </li>
        </ul>

        <div className="sidebar-footer">
          <div className="user-profile-widget">
            <div className="d-flex align-items-center overflow-hidden">
              <div className="user-avatar">{user.name ? user.name[0].toUpperCase() : "U"}</div>
              <div className="user-info">
                <div className="user-name">{user.name}</div>
                <div className="user-email">{user.email}</div>
              </div>
            </div>
            <button onClick={handleLogout} title="Log Out" style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer", fontSize: "16px", padding: "4px" }}>
              <i className="fas fa-sign-out-alt"></i>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Wrapper */}
      <div className="main-wrapper">
        {/* Top Navbar */}
        <header className="top-navbar">
          <div className="d-flex align-items-center gap-3">
            <button className="btn btn-sm d-lg-none" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <i className="fas fa-bars fs-5"></i>
            </button>
            <h1 className="page-header-title m-0">
              {activeTab === "dashboard" && "Financial Dashboard"}
              {activeTab === "transactions" && "Transaction Records"}
              {activeTab === "budgets" && "Monthly Budget Management"}
              {activeTab === "reports" && "Financial Reports & Analytics"}
            </h1>
          </div>

          <div className="top-navbar-actions">
            {/* Notification Bell */}
            <button className="notification-bell-btn" onClick={() => setNotificationModalOpen(true)} title="Budget Alerts & Notifications">
              <i className="fas fa-bell"></i>
              {unreadAlertsCount > 0 && (
                <span className="badge-counter">{unreadAlertsCount}</span>
              )}
            </button>

            {/* Quick Add Button */}
            <button className="btn-fin-primary d-none d-sm-inline-flex" onClick={() => setActiveTab("transactions")}>
              <i className="fas fa-plus"></i> New Transaction
            </button>
          </div>
        </header>

        {/* Content Body */}
        <main className="content-body">
          {activeTab === "dashboard" && <DashboardView setActiveTab={setActiveTab} refreshUnreadCount={refreshUnreadCount} />}
          {activeTab === "transactions" && <TransactionsView showToast={showToast} refreshUnreadCount={refreshUnreadCount} />}
          {activeTab === "budgets" && <BudgetsView showToast={showToast} refreshUnreadCount={refreshUnreadCount} />}
          {activeTab === "reports" && <ReportsView />}
        </main>
      </div>

      {/* Notifications Drawer / Modal */}
      {notificationModalOpen && (
        <NotificationModal
          onClose={() => { setNotificationModalOpen(false); refreshUnreadCount(); }}
          onRefreshCount={refreshUnreadCount}
        />
      )}
    </div>
  );
}

// ==========================================
// Auth Screen Component (Login / Register / Demo)
// ==========================================
function AuthScreen({ onLoginSuccess, showToast }) {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const endpoint = isRegister ? "/api/auth/register" : "/api/auth/login";
    try {
      const res = await API.request(endpoint, {
        method: "POST",
        body: JSON.stringify(formData)
      });
      API.setToken(res.token);
      onLoginSuccess(res.user, res.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      // Trigger demo seed to ensure data exists
      await API.request("/api/seed", { method: "POST" });
      const res = await API.request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: "alex@finora.io", password: "Finora2026!" })
      });
      API.setToken(res.token);
      onLoginSuccess(res.user, res.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0d9488 100%)", padding: "20px"
    }}>
      <div style={{
        background: "#ffffff", borderRadius: "20px", maxWidth: "440px", width: "100%",
        padding: "36px", boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.25)"
      }}>
        <div className="text-center mb-4">
          <div style={{
            width: "56px", height: "56px", background: "linear-gradient(135deg, #14b8a6, #0d9488)",
            borderRadius: "14px", display: "inline-flex", alignItems: "center", justifyContent: "center",
            color: "#ffffff", fontSize: "28px", boxShadow: "0 10px 15px -3px rgba(13, 148, 136, 0.4)",
            marginBottom: "12px"
          }}>
            <i className="fas fa-wallet"></i>
          </div>
          <h2 style={{ fontWeight: 800, color: "#0f172a", fontSize: "26px", margin: 0 }}>
            Fin<span style={{ color: "#0d9488" }}>ora</span>
          </h2>
          <p style={{ color: "#64748b", fontSize: "14px", marginTop: "4px" }}>
            Personal Expense & Budget Tracker
          </p>
        </div>

        {error && (
          <div className="alert alert-danger py-2 px-3 small rounded-3 mb-3">
            <i className="fas fa-circle-exclamation me-2"></i>{error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <div className="mb-3">
              <label className="form-label small fw-bold text-muted">Full Name</label>
              <input
                type="text"
                className="form-control"
                placeholder="Alex Morgan"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
          )}

          <div className="mb-3">
            <label className="form-label small fw-bold text-muted">Email Address</label>
            <input
              type="email"
              className="form-control"
              placeholder="alex@finora.io"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>

          <div className="mb-4">
            <label className="form-label small fw-bold text-muted">Password</label>
            <input
              type="password"
              className="form-control"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>

          <button
            type="submit"
            className="btn w-100 fw-bold py-2 mb-3"
            style={{ background: "#0d9488", color: "white", borderRadius: "10px" }}
            disabled={loading}
          >
            {loading ? "Processing..." : (isRegister ? "Create Free Account" : "Sign In to Finora")}
          </button>
        </form>

        <div className="text-center mb-3">
          <button
            onClick={handleDemoLogin}
            className="btn btn-outline-secondary w-100 fw-semibold py-2 rounded-3 small"
            disabled={loading}
            style={{ borderColor: "#cbd5e1" }}
          >
            <i className="fas fa-sparkles text-warning me-2"></i> Explore with Preloaded Demo Account
          </button>
        </div>

        <div className="text-center pt-2 border-top">
          <span className="small text-muted">
            {isRegister ? "Already have an account?" : "Don't have an account yet?"}{" "}
          </span>
          <button
            onClick={() => { setIsRegister(!isRegister); setError(null); }}
            className="btn btn-link p-0 small fw-bold"
            style={{ color: "#0d9488", textDecoration: "none" }}
          >
            {isRegister ? "Sign In" : "Register now"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Dashboard View Component
// ==========================================
function DashboardView({ setActiveTab, refreshUnreadCount }) {
  const [data, setData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  const barChartRef = useRef(null);
  const pieChartRef = useRef(null);
  const lineChartRef = useRef(null);

  const chartInstances = useRef({});

  const fetchDashboardData = async () => {
    try {
      const [sumRes, anaRes] = await Promise.all([
        API.request("/api/dashboard/summary"),
        API.request("/api/dashboard/analytics")
      ]);
      setData(sumRes);
      setAnalytics(anaRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Render Charts when analytics data is loaded
  useEffect(() => {
    if (!analytics) return;

    // Destroy prior instances
    Object.values(chartInstances.current).forEach(c => c && c.destroy());

    // 1. Income vs Expense Bar Chart
    if (barChartRef.current && analytics.income_vs_expense) {
      const ctx = barChartRef.current.getContext("2d");
      chartInstances.current.bar = new Chart(ctx, {
        type: "bar",
        data: {
          labels: analytics.income_vs_expense.labels,
          datasets: [
            {
              label: "Income ($)",
              data: analytics.income_vs_expense.income,
              backgroundColor: "rgba(16, 185, 129, 0.85)",
              borderColor: "#10b981",
              borderRadius: 6
            },
            {
              label: "Expense ($)",
              data: analytics.income_vs_expense.expense,
              backgroundColor: "rgba(239, 68, 68, 0.85)",
              borderColor: "#ef4444",
              borderRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top", labels: { font: { family: "Plus Jakarta Sans", weight: "600" } } }
          },
          scales: {
            x: { grid: { display: false } },
            y: { ticks: { callback: (v) => `$${v}` }, grid: { color: "#f1f5f9" } }
          }
        }
      });
    }

    // 2. Category Pie / Doughnut Chart
    if (pieChartRef.current && analytics.category_breakdown) {
      const ctx = pieChartRef.current.getContext("2d");
      chartInstances.current.pie = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: analytics.category_breakdown.labels,
          datasets: [{
            data: analytics.category_breakdown.data,
            backgroundColor: [
              "#0d9488", "#3b82f6", "#f59e0b", "#ec4899",
              "#8b5cf6", "#10b981", "#64748b", "#f97316"
            ],
            borderWidth: 2,
            borderColor: "#ffffff"
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "right", labels: { boxWidth: 12, font: { family: "Plus Jakarta Sans", size: 11 } } }
          },
          cutout: "65%"
        }
      });
    }

    // 3. Monthly Spending Trend Line Chart
    if (lineChartRef.current && analytics.monthly_trend) {
      const ctx = lineChartRef.current.getContext("2d");
      chartInstances.current.line = new Chart(ctx, {
        type: "line",
        data: {
          labels: analytics.monthly_trend.labels,
          datasets: [{
            label: "Monthly Spending ($)",
            data: analytics.monthly_trend.expense,
            borderColor: "#0d9488",
            backgroundColor: "rgba(13, 148, 136, 0.12)",
            tension: 0.35,
            fill: true,
            pointBackgroundColor: "#0d9488",
            pointRadius: 5
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            x: { grid: { display: false } },
            y: { ticks: { callback: (v) => `$${v}` }, grid: { color: "#f1f5f9" } }
          }
        }
      });
    }

    return () => {
      Object.values(chartInstances.current).forEach(c => c && c.destroy());
    };
  }, [analytics]);

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-teal" style={{ color: "#0d9488" }}></div>
        <p className="mt-2 text-muted fw-semibold">Loading dashboard insights...</p>
      </div>
    );
  }

  const s = data?.summary || {};

  return (
    <div>
      {/* KPI Cards Row */}
      <div className="row g-4 mb-4">
        {/* Total Income */}
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="fin-card kpi-card kpi-income">
            <div className="kpi-header">
              <span className="kpi-title">Total Income</span>
              <div className="kpi-icon-box"><i className="fas fa-arrow-down-left"></i></div>
            </div>
            <div className="kpi-value">${s.total_income?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div className="kpi-subtext text-success">
              <i className="fas fa-calendar-check me-1"></i> Current Month: ${s.monthly_income?.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Total Expenses */}
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="fin-card kpi-card kpi-expense">
            <div className="kpi-header">
              <span className="kpi-title">Total Expenses</span>
              <div className="kpi-icon-box"><i className="fas fa-arrow-up-right"></i></div>
            </div>
            <div className="kpi-value">${s.total_expenses?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div className="kpi-subtext text-danger">
              <i className="fas fa-receipt me-1"></i> Current Month: ${s.monthly_expenses?.toLocaleString()}
            </div>
          </div>
        </div>

        {/* Current Balance */}
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="fin-card kpi-card kpi-balance">
            <div className="kpi-header">
              <span className="kpi-title">Net Balance</span>
              <div className="kpi-icon-box"><i className="fas fa-wallet"></i></div>
            </div>
            <div className="kpi-value" style={{ color: s.current_balance < 0 ? "#ef4444" : "#0f172a" }}>
              ${s.current_balance?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="kpi-subtext">
              <i className="fas fa-shield-alt text-teal me-1"></i> Overall Liquidity
            </div>
          </div>
        </div>

        {/* Monthly Savings & Rate */}
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="fin-card kpi-card kpi-savings">
            <div className="kpi-header">
              <span className="kpi-title">Monthly Savings</span>
              <div className="kpi-icon-box"><i className="fas fa-piggy-bank"></i></div>
            </div>
            <div className="kpi-value">${s.monthly_savings?.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div className="kpi-subtext text-teal">
              <i className="fas fa-percentage me-1"></i> Savings Rate: {s.savings_rate}%
            </div>
          </div>
        </div>
      </div>

      {/* Budget Utilization Banner */}
      <div className="fin-card mb-4">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-2">
          <div>
            <h5 className="m-0 fw-bold text-navy">Monthly Budget Utilization</h5>
            <small className="text-muted">
              ${s.budget_spent?.toLocaleString()} spent out of ${s.total_budgeted?.toLocaleString()} total budgeted limit
            </small>
          </div>
          <div className="d-flex align-items-center gap-3">
            <span className={`status-pill ${
              s.budget_utilization > 100 ? "status-danger" :
              s.budget_utilization >= 80 ? "status-warning" : "status-income"
            }`}>
              {s.budget_utilization}% Utilized
            </span>
            <button className="btn btn-sm btn-outline-secondary" onClick={() => setActiveTab("budgets")}>
              Manage Budgets <i className="fas fa-arrow-right ms-1"></i>
            </button>
          </div>
        </div>
        <div className="fin-progress-container">
          <div
            className={`fin-progress-bar ${
              s.budget_utilization > 100 ? "progress-danger" :
              s.budget_utilization >= 80 ? "progress-warning" :
              s.budget_utilization >= 50 ? "progress-info" : "progress-safe"
            }`}
            style={{ width: `${Math.min(100, s.budget_utilization || 0)}%` }}
          ></div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="row g-4 mb-4">
        {/* Income vs Expense Bar Chart */}
        <div className="col-12 col-lg-8">
          <div className="fin-card chart-card">
            <div className="chart-header">
              <h6 className="chart-title"><i className="fas fa-chart-column text-teal me-2"></i>Income vs. Expenses (Last 6 Months)</h6>
            </div>
            <div style={{ height: "280px" }}>
              <canvas ref={barChartRef}></canvas>
            </div>
          </div>
        </div>

        {/* Category Expense Doughnut Chart */}
        <div className="col-12 col-lg-4">
          <div className="fin-card chart-card">
            <div className="chart-header">
              <h6 className="chart-title"><i className="fas fa-chart-pie text-teal me-2"></i>Expense by Category</h6>
            </div>
            <div style={{ height: "280px" }}>
              {analytics?.category_breakdown?.data?.length > 0 ? (
                <canvas ref={pieChartRef}></canvas>
              ) : (
                <div className="d-flex align-items-center justify-content-center h-100 text-muted">
                  No expense records this month
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Monthly Spending Trend & Recent Transactions */}
      <div className="row g-4">
        {/* Monthly Trend Line */}
        <div className="col-12 col-lg-6">
          <div className="fin-card">
            <div className="chart-header">
              <h6 className="chart-title"><i className="fas fa-wave-square text-teal me-2"></i>Spending Trend Over Time</h6>
            </div>
            <div style={{ height: "240px" }}>
              <canvas ref={lineChartRef}></canvas>
            </div>
          </div>
        </div>

        {/* Recent Transactions List */}
        <div className="col-12 col-lg-6">
          <div className="fin-card">
            <div className="d-flex align-items-center justify-content-between mb-3">
              <h6 className="chart-title m-0"><i className="fas fa-clock-rotate-left text-teal me-2"></i>Recent Transactions</h6>
              <button className="btn btn-sm text-teal fw-bold p-0" onClick={() => setActiveTab("transactions")}>
                View All <i className="fas fa-chevron-right ms-1"></i>
              </button>
            </div>

            <div className="table-responsive">
              <table className="fin-table">
                <thead>
                  <tr>
                    <th>Title & Category</th>
                    <th>Date</th>
                    <th className="text-end">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.recent_transactions?.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <div className="fw-bold">{t.title}</div>
                        <small className="text-muted">{t.category}</small>
                      </td>
                      <td className="text-muted small">{t.date}</td>
                      <td className={`text-end fw-bold ${t.type === "Income" ? "text-success" : "text-danger"}`}>
                        {t.type === "Income" ? "+" : "-"}${t.amount.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                  {(!data?.recent_transactions || data?.recent_transactions.length === 0) && (
                    <tr>
                      <td colSpan="3" className="text-center py-4 text-muted">
                        No transactions recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// Transactions View Component (CRUD, Search, Filter)
// ==========================================
function TransactionsView({ showToast, refreshUnreadCount }) {
  const [transactions, setTransactions] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTx, setEditingTx] = useState(null);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (typeFilter !== "all") params.append("type", typeFilter);
      if (categoryFilter !== "all") params.append("category", categoryFilter);
      if (startDate) params.append("start_date", startDate);
      if (endDate) params.append("end_date", endDate);

      const res = await API.request(`/api/transactions?${params.toString()}`);
      setTransactions(res.transactions);
      setTotalCount(res.total);
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTransactions();
    }, 250);
    return () => clearTimeout(timer);
  }, [search, typeFilter, categoryFilter, startDate, endDate]);

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this transaction?")) return;
    try {
      await API.request(`/api/transactions/${id}`, { method: "DELETE" });
      showToast("Transaction deleted successfully");
      fetchTransactions();
      refreshUnreadCount();
    } catch (err) {
      showToast(err.message, "danger");
    }
  };

  return (
    <div>
      {/* Header and Filter Controls */}
      <div className="fin-card mb-4">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-3">
          <div>
            <h5 className="fw-bold m-0 text-navy">All Financial Transactions</h5>
            <small className="text-muted">{totalCount} records found</small>
          </div>
          <button className="btn-fin-primary" onClick={() => { setEditingTx(null); setModalOpen(true); }}>
            <i className="fas fa-plus"></i> Add Transaction
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="row g-2">
          {/* Search */}
          <div className="col-12 col-md-4">
            <div className="input-group">
              <span className="input-group-text bg-white border-end-0 text-muted">
                <i className="fas fa-search"></i>
              </span>
              <input
                type="text"
                className="form-control border-start-0"
                placeholder="Search by title or description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          {/* Type Filter */}
          <div className="col-6 col-md-2">
            <select className="form-select" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="all">All Types</option>
              <option value="Income">Income</option>
              <option value="Expense">Expense</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="col-6 col-md-2">
            <select className="form-select" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              <option value="all">All Categories</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Start Date */}
          <div className="col-6 col-md-2">
            <input
              type="date"
              className="form-control"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              title="Start Date"
            />
          </div>

          {/* End Date */}
          <div className="col-6 col-md-2">
            <input
              type="date"
              className="form-control"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              title="End Date"
            />
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="fin-card">
        <div className="table-responsive">
          <table className="fin-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Category</th>
                <th>Date</th>
                <th>Description</th>
                <th className="text-end">Amount</th>
                <th className="text-end">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="text-center py-4">
                    <div className="spinner-border text-teal spinner-border-sm me-2"></div>
                    Loading records...
                  </td>
                </tr>
              ) : transactions.length > 0 ? (
                transactions.map((t) => (
                  <tr key={t.id}>
                    <td className="fw-bold">{t.title}</td>
                    <td>
                      <span className={`status-pill ${t.type === "Income" ? "status-income" : "status-expense"}`}>
                        <i className={`fas ${t.type === "Income" ? "fa-arrow-down" : "fa-arrow-up"}`}></i>
                        {t.type}
                      </span>
                    </td>
                    <td><span className="badge bg-light text-dark border">{t.category}</span></td>
                    <td className="text-muted">{t.date}</td>
                    <td className="text-muted small" style={{ maxWidth: "220px", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                      {t.description || "—"}
                    </td>
                    <td className={`text-end fw-bold fs-6 ${t.type === "Income" ? "text-success" : "text-danger"}`}>
                      {t.type === "Income" ? "+" : "-"}${t.amount.toFixed(2)}
                    </td>
                    <td className="text-end">
                      <button
                        className="btn btn-sm btn-outline-secondary me-2"
                        title="Edit"
                        onClick={() => { setEditingTx(t); setModalOpen(true); }}
                      >
                        <i className="fas fa-pencil"></i>
                      </button>
                      <button
                        className="btn btn-sm btn-outline-danger"
                        title="Delete"
                        onClick={() => handleDelete(t.id)}
                      >
                        <i className="fas fa-trash-can"></i>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="text-center py-5 text-muted">
                    <i className="fas fa-folder-open fs-2 mb-2 d-block text-secondary"></i>
                    No matching transactions found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Transaction Modal */}
      {modalOpen && (
        <TransactionModal
          transaction={editingTx}
          onClose={() => setModalOpen(false)}
          onSuccess={() => {
            setModalOpen(false);
            fetchTransactions();
            refreshUnreadCount();
            showToast(editingTx ? "Transaction updated successfully!" : "New transaction recorded!");
          }}
          showToast={showToast}
        />
      )}
    </div>
  );
}

// ==========================================
// Transaction Form Modal
// ==========================================
function TransactionModal({ transaction, onClose, onSuccess, showToast }) {
  const [formData, setFormData] = useState({
    title: transaction?.title || "",
    amount: transaction?.amount || "",
    type: transaction?.type || "Expense",
    category: transaction?.category || "Food & Dining",
    date: transaction?.date || new Date().toISOString().split("T")[0],
    description: transaction?.description || ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const isEdit = !!transaction;
    const endpoint = isEdit ? `/api/transactions/${transaction.id}` : "/api/transactions";
    const method = isEdit ? "PUT" : "POST";

    try {
      await API.request(endpoint, {
        method,
        body: JSON.stringify(formData)
      });
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop-custom">
      <div className="modal-content-custom">
        <div className="modal-header-custom">
          <h3>{transaction ? "Edit Transaction" : "Record New Transaction"}</h3>
          <button className="btn-close" onClick={onClose}></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body-custom">
            {error && <div className="alert alert-danger py-2 small mb-3">{error}</div>}

            <div className="mb-3">
              <label className="form-label small fw-bold">Title</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Whole Foods Groceries"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>

            <div className="row g-2 mb-3">
              <div className="col-6">
                <label className="form-label small fw-bold">Type</label>
                <select
                  className="form-select"
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                >
                  <option value="Expense">Expense</option>
                  <option value="Income">Income</option>
                </select>
              </div>
              <div className="col-6">
                <label className="form-label small fw-bold">Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className="form-control"
                  placeholder="0.00"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="row g-2 mb-3">
              <div className="col-6">
                <label className="form-label small fw-bold">Category</label>
                <select
                  className="form-select"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="col-6">
                <label className="form-label small fw-bold">Date</label>
                <input
                  type="date"
                  className="form-control"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                />
              </div>
            </div>

            <div className="mb-2">
              <label className="form-label small fw-bold">Description (Optional)</label>
              <textarea
                className="form-control"
                rows="2"
                placeholder="Additional notes..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              ></textarea>
            </div>
          </div>

          <div className="modal-footer-custom">
            <button type="button" className="btn-fin-outline" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-fin-primary" disabled={loading}>
              {loading ? "Saving..." : (transaction ? "Update Record" : "Save Transaction")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ==========================================
// Budgets View Component
// ==========================================
function BudgetsView({ showToast, refreshUnreadCount }) {
  const [month, setMonth] = useState(new Date().toISOString().substring(0, 7));
  const [budgetData, setBudgetData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);

  const fetchBudgets = async () => {
    setLoading(true);
    try {
      const res = await API.request(`/api/budgets?month=${month}`);
      setBudgetData(res);
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBudgets();
  }, [month]);

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this category budget?")) return;
    try {
      await API.request(`/api/budgets/${id}`, { method: "DELETE" });
      showToast("Budget limit deleted.");
      fetchBudgets();
      refreshUnreadCount();
    } catch (err) {
      showToast(err.message, "danger");
    }
  };

  const sum = budgetData?.summary || {};
  const budgets = budgetData?.budgets || [];

  return (
    <div>
      {/* Overview & Month Picker */}
      <div className="fin-card mb-4">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
          <div>
            <h5 className="fw-bold m-0 text-navy">Category Budget Planner</h5>
            <small className="text-muted">Set spending targets and receive automatic utilization alerts</small>
          </div>
          <div className="d-flex align-items-center gap-2">
            <input
              type="month"
              className="form-control"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              style={{ width: "auto" }}
            />
            <button className="btn-fin-primary" onClick={() => { setEditingBudget(null); setModalOpen(true); }}>
              <i className="fas fa-plus"></i> Set Budget
            </button>
          </div>
        </div>

        {/* Aggregate KPI Grid */}
        <div className="row g-3">
          <div className="col-6 col-md-3">
            <div className="p-3 rounded-3 bg-light border">
              <small className="text-muted fw-bold d-block text-uppercase">Total Budgeted</small>
              <span className="fs-4 fw-bold text-navy">${sum.total_budgeted?.toLocaleString()}</span>
            </div>
          </div>
          <div className="col-6 col-md-3">
            <div className="p-3 rounded-3 bg-light border">
              <small className="text-muted fw-bold d-block text-uppercase">Total Spent</small>
              <span className="fs-4 fw-bold text-danger">${sum.total_spent?.toLocaleString()}</span>
            </div>
          </div>
          <div className="col-6 col-md-3">
            <div className="p-3 rounded-3 bg-light border">
              <small className="text-muted fw-bold d-block text-uppercase">Remaining</small>
              <span className={`fs-4 fw-bold ${sum.total_remaining < 0 ? "text-danger" : "text-success"}`}>
                ${sum.total_remaining?.toLocaleString()}
              </span>
            </div>
          </div>
          <div className="col-6 col-md-3">
            <div className="p-3 rounded-3 bg-light border">
              <small className="text-muted fw-bold d-block text-uppercase">Utilization</small>
              <span className={`fs-4 fw-bold ${sum.overall_utilization > 100 ? "text-danger" : sum.overall_utilization >= 80 ? "text-warning" : "text-teal"}`}>
                {sum.overall_utilization}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Category Budgets Grid */}
      <div className="row g-4">
        {loading ? (
          <div className="col-12 text-center py-5">
            <div className="spinner-border text-teal"></div>
            <p className="mt-2 text-muted fw-semibold">Calculating budget metrics...</p>
          </div>
        ) : budgets.length > 0 ? (
          budgets.map((b) => {
            const isOver = b.spent > b.limit_amount;
            const progressColor =
              b.utilization_percentage > 100 ? "progress-danger" :
              b.utilization_percentage >= 80 ? "progress-warning" :
              b.utilization_percentage >= 50 ? "progress-info" : "progress-safe";

            const badgeStatus =
              b.utilization_percentage > 100 ? { label: "Overspent!", class: "status-danger" } :
              b.utilization_percentage === 100 ? { label: "100% Limit Reached", class: "status-danger" } :
              b.utilization_percentage >= 80 ? { label: "80% Warning", class: "status-warning" } :
              b.utilization_percentage >= 50 ? { label: "50% Utilized", class: "status-info" } :
              { label: "On Track", class: "status-income" };

            return (
              <div className="col-12 col-md-6 col-xl-4" key={b.id}>
                <div className="fin-card h-100 d-flex flex-direction-column justify-content-between">
                  <div>
                    <div className="d-flex align-items-center justify-content-between mb-2">
                      <h6 className="fw-bold m-0 fs-5 text-navy">{b.category}</h6>
                      <span className={`status-pill ${badgeStatus.class}`}>
                        {badgeStatus.label}
                      </span>
                    </div>

                    <div className="d-flex justify-content-between align-items-baseline mt-3">
                      <div>
                        <span className="fs-4 fw-bold text-navy">${b.spent.toFixed(2)}</span>
                        <span className="text-muted small"> / ${b.limit_amount.toFixed(2)}</span>
                      </div>
                      <span className="fw-bold small text-muted">{b.utilization_percentage}%</span>
                    </div>

                    {/* Progress Bar */}
                    <div className="fin-progress-container">
                      <div
                        className={`fin-progress-bar ${progressColor}`}
                        style={{ width: `${Math.min(100, b.utilization_percentage)}%` }}
                      ></div>
                    </div>

                    <div className="d-flex justify-content-between align-items-center mt-2 small">
                      <span className="text-muted">Remaining Balance:</span>
                      <span className={`fw-bold ${isOver ? "text-danger" : "text-success"}`}>
                        {isOver ? `-$${Math.abs(b.remaining).toFixed(2)}` : `$${b.remaining.toFixed(2)}`}
                      </span>
                    </div>
                  </div>

                  <div className="d-flex justify-content-end gap-2 mt-4 pt-3 border-top">
                    <button
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => { setEditingBudget(b); setModalOpen(true); }}
                      title="Edit Budget Limit"
                    >
                      <i className="fas fa-pencil me-1"></i> Edit
                    </button>
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleDelete(b.id)}
                      title="Delete Budget"
                    >
                      <i className="fas fa-trash-can me-1"></i> Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="col-12">
            <div className="fin-card text-center py-5">
              <i className="fas fa-bullseye fs-1 text-teal mb-3"></i>
              <h5 className="fw-bold text-navy">No Budgets Created for {month}</h5>
              <p className="text-muted small">Create spending limits for your frequent categories to unlock automated threshold alerts.</p>
              <button className="btn-fin-primary" onClick={() => { setEditingBudget(null); setModalOpen(true); }}>
                <i className="fas fa-plus"></i> Set First Budget
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Budget Modal */}
      {modalOpen && (
        <BudgetModal
          budget={editingBudget}
          defaultMonth={month}
          onClose={() => setModalOpen(false)}
          onSuccess={() => {
            setModalOpen(false);
            fetchBudgets();
            refreshUnreadCount();
            showToast(editingBudget ? "Budget limit updated!" : "New budget target activated!");
          }}
        />
      )}
    </div>
  );
}

// ==========================================
// Budget Form Modal
// ==========================================
function BudgetModal({ budget, defaultMonth, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    category: budget?.category || "Food & Dining",
    limit_amount: budget?.limit_amount || "",
    month: budget?.month || defaultMonth,
    notes: budget?.notes || ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const isEdit = !!budget;
    const endpoint = isEdit ? `/api/budgets/${budget.id}` : "/api/budgets";
    const method = isEdit ? "PUT" : "POST";

    try {
      await API.request(endpoint, {
        method,
        body: JSON.stringify(formData)
      });
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop-custom">
      <div className="modal-content-custom">
        <div className="modal-header-custom">
          <h3>{budget ? "Edit Budget Limit" : "Create Monthly Budget"}</h3>
          <button className="btn-close" onClick={onClose}></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body-custom">
            {error && <div className="alert alert-danger py-2 small mb-3">{error}</div>}

            <div className="mb-3">
              <label className="form-label small fw-bold">Month</label>
              <input
                type="month"
                className="form-control"
                value={formData.month}
                onChange={(e) => setFormData({ ...formData, month: e.target.value })}
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label small fw-bold">Category</label>
              <select
                className="form-select"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="mb-3">
              <label className="form-label small fw-bold">Monthly Limit Amount ($)</label>
              <input
                type="number"
                step="0.01"
                min="1"
                className="form-control"
                placeholder="500.00"
                value={formData.limit_amount}
                onChange={(e) => setFormData({ ...formData, limit_amount: e.target.value })}
                required
              />
            </div>

            <div className="mb-2">
              <label className="form-label small fw-bold">Notes (Optional)</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Target grocery cap"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </div>
          </div>

          <div className="modal-footer-custom">
            <button type="button" className="btn-fin-outline" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-fin-primary" disabled={loading}>
              {loading ? "Saving..." : (budget ? "Update Budget" : "Save Budget")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ==========================================
// Reports & Analytics View Component
// ==========================================
function ReportsView() {
  const [activeReportTab, setActiveReportTab] = useState("monthly"); // monthly, category, summary
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [monthlyData, setMonthlyData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const [mRes, cRes, sRes] = await Promise.all([
        API.request(`/api/reports/monthly?year=${year}`),
        API.request(`/api/reports/category?start_date=${startDate}&end_date=${endDate}`),
        API.request(`/api/reports/summary?start_date=${startDate}&end_date=${endDate}`)
      ]);
      setMonthlyData(mRes);
      setCategoryData(cRes);
      setSummaryData(sRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [year, startDate, endDate]);

  return (
    <div>
      {/* Filter and Switcher */}
      <div className="fin-card mb-4">
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3">
          {/* Sub-nav Tabs */}
          <div className="btn-group">
            <button
              className={`btn btn-sm ${activeReportTab === "monthly" ? "btn-secondary" : "btn-outline-secondary"}`}
              style={{ background: activeReportTab === "monthly" ? "#0d9488" : "", borderColor: "#0d9488", color: activeReportTab === "monthly" ? "white" : "#0d9488" }}
              onClick={() => setActiveReportTab("monthly")}
            >
              <i className="fas fa-calendar-alt me-1"></i> Monthly Breakdown
            </button>
            <button
              className={`btn btn-sm ${activeReportTab === "category" ? "btn-secondary" : "btn-outline-secondary"}`}
              style={{ background: activeReportTab === "category" ? "#0d9488" : "", borderColor: "#0d9488", color: activeReportTab === "category" ? "white" : "#0d9488" }}
              onClick={() => setActiveReportTab("category")}
            >
              <i className="fas fa-pie-chart me-1"></i> Category Analytics
            </button>
            <button
              className={`btn btn-sm ${activeReportTab === "summary" ? "btn-secondary" : "btn-outline-secondary"}`}
              style={{ background: activeReportTab === "summary" ? "#0d9488" : "", borderColor: "#0d9488", color: activeReportTab === "summary" ? "white" : "#0d9488" }}
              onClick={() => setActiveReportTab("summary")}
            >
              <i className="fas fa-list-check me-1"></i> Daily Spending Log
            </button>
          </div>

          {/* Date Pickers */}
          <div className="d-flex align-items-center gap-2">
            {activeReportTab === "monthly" ? (
              <select className="form-select form-select-sm" value={year} onChange={(e) => setYear(e.target.value)}>
                <option value="2026">Year 2026</option>
                <option value="2025">Year 2025</option>
                <option value="2024">Year 2024</option>
              </select>
            ) : (
              <div className="d-flex align-items-center gap-2">
                <input
                  type="date"
                  className="form-control form-control-sm"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  placeholder="Start"
                />
                <span className="text-muted">to</span>
                <input
                  type="date"
                  className="form-control form-control-sm"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  placeholder="End"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-teal"></div>
        </div>
      ) : (
        <div>
          {/* TAB 1: Monthly Breakdown */}
          {activeReportTab === "monthly" && (
            <div className="fin-card">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h5 className="fw-bold m-0 text-navy">Annual Monthly Performance ({year})</h5>
                <div className="d-flex gap-3">
                  <span className="badge bg-success-subtle text-success p-2">Total Income: ${monthlyData?.summary?.total_income?.toLocaleString()}</span>
                  <span className="badge bg-danger-subtle text-danger p-2">Total Expenses: ${monthlyData?.summary?.total_expense?.toLocaleString()}</span>
                  <span className="badge bg-teal-subtle text-teal p-2" style={{ backgroundColor: "#ccfbf1", color: "#0f766e" }}>Net Savings: ${monthlyData?.summary?.net_savings?.toLocaleString()}</span>
                </div>
              </div>

              <div className="table-responsive">
                <table className="fin-table">
                  <thead>
                    <tr>
                      <th>Month</th>
                      <th className="text-end">Income</th>
                      <th className="text-end">Expenses</th>
                      <th className="text-end">Net Savings</th>
                      <th className="text-end">Savings Rate</th>
                      <th className="text-end">Transactions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyData?.monthly_breakdown?.map((m) => (
                      <tr key={m.month}>
                        <td className="fw-bold">{m.month}</td>
                        <td className="text-end text-success fw-bold">${m.income.toFixed(2)}</td>
                        <td className="text-end text-danger fw-bold">${m.expenses.toFixed(2)}</td>
                        <td className={`text-end fw-bold ${m.savings < 0 ? "text-danger" : "text-navy"}`}>
                          ${m.savings.toFixed(2)}
                        </td>
                        <td className="text-end">
                          <span className={`badge ${m.savings_rate >= 20 ? "bg-success" : m.savings_rate > 0 ? "bg-info" : "bg-secondary"}`}>
                            {m.savings_rate}%
                          </span>
                        </td>
                        <td className="text-end text-muted">{m.transaction_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 2: Category Breakdown */}
          {activeReportTab === "category" && (
            <div className="fin-card">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                  <h5 className="fw-bold m-0 text-navy">Category-Wise Expense Distribution</h5>
                  <small className="text-muted">Total Expense Volume: ${categoryData?.total_expense?.toLocaleString()}</small>
                </div>
              </div>

              <div className="table-responsive">
                <table className="fin-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th className="text-end">Total Spent</th>
                      <th className="text-end">Share (%)</th>
                      <th className="text-end">Count</th>
                      <th className="text-end">Average / Tx</th>
                      <th className="text-end">Peak Tx</th>
                    </tr>
                  </thead>
                  <tbody>
                    {categoryData?.categories?.map((c) => (
                      <tr key={c.category}>
                        <td className="fw-bold">{c.category}</td>
                        <td className="text-end text-danger fw-bold">${c.total_amount.toFixed(2)}</td>
                        <td className="text-end">
                          <div className="d-flex align-items-center justify-content-end gap-2">
                            <span>{c.percentage}%</span>
                            <div style={{ width: "60px", height: "6px", background: "#e2e8f0", borderRadius: "3px" }}>
                              <div style={{ width: `${c.percentage}%`, height: "100%", background: "#0d9488", borderRadius: "3px" }}></div>
                            </div>
                          </div>
                        </td>
                        <td className="text-end text-muted">{c.transaction_count}</td>
                        <td className="text-end text-muted">${c.avg_transaction.toFixed(2)}</td>
                        <td className="text-end text-muted">${c.max_transaction.toFixed(2)}</td>
                      </tr>
                    ))}
                    {(!categoryData?.categories || categoryData?.categories.length === 0) && (
                      <tr>
                        <td colSpan="6" className="text-center py-4 text-muted">
                          No category expense records found in this range.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: Daily Summary Log */}
          {activeReportTab === "summary" && (
            <div className="fin-card">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <div>
                  <h5 className="fw-bold m-0 text-navy">Daily Expense & Income Summary</h5>
                  <small className="text-muted">Net savings across active days: ${summaryData?.summary?.net_savings?.toLocaleString()}</small>
                </div>
              </div>

              <div className="table-responsive">
                <table className="fin-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th className="text-end">Income</th>
                      <th className="text-end">Expenses</th>
                      <th className="text-end">Net Daily</th>
                      <th className="text-end">Activity Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summaryData?.daily_summary?.map((d) => (
                      <tr key={d.date}>
                        <td className="fw-bold">{d.date}</td>
                        <td className="text-end text-success">${d.income.toFixed(2)}</td>
                        <td className="text-end text-danger">${d.expense.toFixed(2)}</td>
                        <td className={`text-end fw-bold ${d.net < 0 ? "text-danger" : "text-navy"}`}>
                          ${d.net.toFixed(2)}
                        </td>
                        <td className="text-end text-muted">{d.count}</td>
                      </tr>
                    ))}
                    {(!summaryData?.daily_summary || summaryData?.daily_summary.length === 0) && (
                      <tr>
                        <td colSpan="5" className="text-center py-4 text-muted">
                          No daily transactions in selected timeframe.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ==========================================
// Notifications & Budget Alerts Modal
// ==========================================
function NotificationModal({ onClose, onRefreshCount }) {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const res = await API.request("/api/notifications");
      setNotifications(res.notifications);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleMarkRead = async (id) => {
    try {
      await API.request(`/api/notifications/${id}/read`, { method: "POST" });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
      onRefreshCount();
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearAll = async () => {
    try {
      await API.request("/api/notifications/clear", { method: "POST" });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      onRefreshCount();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="modal-backdrop-custom">
      <div className="modal-content-custom" style={{ maxWidth: "600px" }}>
        <div className="modal-header-custom">
          <div className="d-flex align-items-center gap-2">
            <i className="fas fa-bell text-teal fs-5"></i>
            <h3 className="m-0">Budget Alerts & Notifications</h3>
          </div>
          <button className="btn-close" onClick={onClose}></button>
        </div>

        <div className="modal-body-custom" style={{ maxHeight: "420px", overflowY: "auto" }}>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <small className="text-muted fw-bold">Automated 50%, 80%, 100%, and Overspending Triggers</small>
            {notifications.some(n => !n.read) && (
              <button className="btn btn-sm text-teal p-0 fw-bold" onClick={handleClearAll}>
                Mark All as Read
              </button>
            )}
          </div>

          {loading ? (
            <div className="text-center py-4">
              <div className="spinner-border text-teal spinner-border-sm"></div>
            </div>
          ) : notifications.length > 0 ? (
            <div className="d-flex flex-column gap-3">
              {notifications.map((n) => {
                const borderClass =
                  n.level === "danger" ? "border-danger bg-danger-subtle" :
                  n.level === "warning" ? "border-warning bg-warning-subtle" : "border-info bg-info-subtle";

                const icon =
                  n.level === "danger" ? "fa-circle-exclamation text-danger" :
                  n.level === "warning" ? "fa-triangle-exclamation text-warning" : "fa-circle-info text-info";

                return (
                  <div
                    key={n.id}
                    className={`p-3 rounded-3 border d-flex gap-3 align-items-start ${borderClass}`}
                    style={{ opacity: n.read ? 0.65 : 1 }}
                  >
                    <i className={`fas ${icon} fs-4 mt-1`}></i>
                    <div className="flex-grow-1">
                      <div className="d-flex justify-content-between align-items-center mb-1">
                        <span className="fw-bold text-navy small">{n.title}</span>
                        <span className="badge bg-white text-dark border small">{n.month}</span>
                      </div>
                      <p className="m-0 small text-dark mb-2">{n.message}</p>
                      <div className="d-flex justify-content-between align-items-center small text-muted">
                        <span>Spent: ${n.spent?.toFixed(2)} / ${n.limit_amount?.toFixed(2)} ({n.percentage}%)</span>
                        {!n.read && (
                          <button
                            className="btn btn-sm btn-link p-0 text-decoration-none fw-semibold"
                            onClick={() => handleMarkRead(n.id)}
                          >
                            Mark Read
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-5 text-muted">
              <i className="fas fa-check-circle fs-2 text-success mb-2 d-block"></i>
              No active budget alerts. Your spending is in great shape!
            </div>
          )}
        </div>

        <div className="modal-footer-custom">
          <button className="btn-fin-outline" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

// Render Application into root DOM
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<FinoraApp />);
