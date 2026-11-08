
import { useEffect, useState } from "react";

import DocumentWorkspace from "./components/DocumentWorkspace";
import AdministrationDashboard from "./components/AdministrationDashboard";

import { apiRequest } from "./services/api";
import "./App.css";

function TrustifyMark({ compact = false }) {
  return (
    <span className={`brand-mark${compact ? " brand-mark-compact" : ""}`} aria-hidden="true">
      <svg viewBox="0 0 48 48" role="img" focusable="false">
        <path d="M24 4 40 10v12c0 10.5-6.8 17.5-16 22C14.8 39.5 8 32.5 8 22V10L24 4Z" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinejoin="round" />
        <rect x="16.5" y="21" width="15" height="12" rx="2.8" fill="none" stroke="currentColor" strokeWidth="2.6" />
        <path d="M20 21v-3.5a4 4 0 0 1 8 0V21" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
        <circle cx="24" cy="26.5" r="1.4" fill="currentColor" />
        <path d="M24 28v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    </span>
  );
}

function App() {
  const [page, setPage] = useState("login");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [loginData, setLoginData] = useState({
    username: "",
    password: "",
  });

  const [registerData, setRegisterData] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });

  // Restore the current browser session.
  useEffect(() => {
    async function restoreSession() {
      const access = sessionStorage.getItem("access_token");

      if (!access) {
        setCheckingSession(false);
        return;
      }

      try {
        const profile = await apiRequest("/api/auth/profile/", {
          headers: {
            Authorization: `Bearer ${access}`,
          },
        });

        setUser(profile);
        setPage("dashboard");
      } catch {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("refresh_token");
      } finally {
        setCheckingSession(false);
      }
    }

    restoreSession();
  }, []);

  function handleLoginChange(event) {
    setLoginData({
      ...loginData,
      [event.target.name]: event.target.value,
    });
  }

  function handleRegisterChange(event) {
    setRegisterData({
      ...registerData,
      [event.target.name]: event.target.value,
    });
  }

  // User login.
  async function handleLogin(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const result = await apiRequest("/api/auth/login/", {
        auth: false,
        method: "POST",
        body: JSON.stringify(loginData),
      });

      sessionStorage.setItem("access_token", result.access);
      sessionStorage.setItem("refresh_token", result.refresh);

      const profile = await apiRequest("/api/auth/profile/", {
        headers: {
          Authorization: `Bearer ${result.access}`,
        },
      });

      setUser(profile);
      setPage("dashboard");
      setLoginData({ username: "", password: "" });

    } catch (err) {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");
      setError(err.message || "Unable to log in.");
    } finally {
      setLoading(false);
    }
  }

  // User registration.
  async function handleRegister(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      await apiRequest("/api/auth/register/", {
        auth: false,
        method: "POST",
        body: JSON.stringify(registerData),
      });

      setSuccess("Account created successfully. Please log in.");

      setLoginData({
        username: registerData.username,
        password: "",
      });

      setRegisterData({
        username: "",
        email: "",
        first_name: "",
        last_name: "",
        password: "",
        password_confirm: "",
      });

      setPage("login");

    } catch (err) {
      setError(err.message || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  // User logout.
  async function handleLogout() {
    setLoading(true);
    setError("");

    const refresh = sessionStorage.getItem("refresh_token");
    const access = sessionStorage.getItem("access_token");

    try {
      if (refresh && access) {
        await apiRequest("/api/auth/logout/", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${access}`,
          },
          body: JSON.stringify({ refresh }),
        });
      }
    } catch {
      setError("Server logout failed. Your local session was cleared.");
    } finally {
      sessionStorage.removeItem("access_token");
      sessionStorage.removeItem("refresh_token");

      setUser(null);
      setPage("login");
      setLoading(false);
    }
  }

  if (checkingSession) {
    return <div className="loading-screen">Loading Trustify...</div>;
  }

  return (
    <div className="app-container">

      <header className="navbar">
        <div className="brand">
          <TrustifyMark />
          <span>Trustify</span>
        </div>

        {user && user.is_superuser === true && (
          <button
            type="button"
            className="logout-button admin-nav-button"
            onClick={() => {
              setError("");
              setSuccess("");
              setPage(
                page === "administration"
                  ? "dashboard"
                  : "administration"
              );
            }}
          >
            {page === "administration"
              ? "My Workspace"
              : "Administration"}
          </button>
        )}

        {user && (
          <button
            className="logout-button"
            onClick={handleLogout}
            disabled={loading}
          >
            {loading ? "Please wait..." : "Logout"}
          </button>
        )}
      </header>

      <main
        className={`main-content ${
          user ? "main-content-authenticated" : "main-content-public"
        }`}
      >

        {error && (
          <div className="message error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="message success-message">
            {success}
          </div>
        )}

        {!user && page === "login" && (
          <div className="auth-layout">
            <aside className="auth-intro" aria-label="About Trustify">
              <div className="auth-intro-brand"><TrustifyMark compact /><span>TRUSTIFY</span></div>
              <p className="auth-kicker">YOUR DOCUMENTS. YOUR CONTROL.</p>
              <h1>Confidence in every document.</h1>
              <p className="auth-intro-copy">A secure workspace to organize important files, control access and keep track of document activity.</p>
              <div className="auth-feature-list">
                <div><span className="auth-feature-icon">▣</span><span><strong>Protected storage</strong><small>Keep important documents in a private workspace.</small></span></div>
                <div><span className="auth-feature-icon">⌑</span><span><strong>Controlled access</strong><small>Share documents with permissions you manage.</small></span></div>
                <div><span className="auth-feature-icon">↺</span><span><strong>History and accountability</strong><small>Review document versions and recorded activity.</small></span></div>
              </div>
              <p className="auth-intro-foot">A clearer, more controlled way to manage documents.</p>
            </aside>
            <section className="auth-card">

            <div className="auth-heading">
              <h1>Welcome back</h1>
              <p>Sign in to access your Trustify account.</p>
            </div>

            <form onSubmit={handleLogin}>

              <label>Username</label>
              <input
                type="text"
                name="username"
                value={loginData.username}
                onChange={handleLoginChange}
                placeholder="Enter your username"
                autoComplete="username"
                required
              />

              <label>Password</label>
              <input
                type="password"
                name="password"
                value={loginData.password}
                onChange={handleLoginChange}
                placeholder="Enter your password"
                autoComplete="current-password"
                required
              />

              <button
                type="submit"
                className="primary-button"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In"}
              </button>

            </form>

            <p className="auth-footer">
              Don't have an account?{" "}
              <button
                className="text-button"
                onClick={() => {
                  setError("");
                  setSuccess("");
                  setPage("register");
                }}
              >
                Register
              </button>
            </p>

            </section>
          </div>
        )}

        {!user && page === "register" && (
          <div className="auth-layout auth-layout-register">
            <aside className="auth-intro" aria-label="About Trustify">
              <div className="auth-intro-brand"><TrustifyMark compact /><span>TRUSTIFY</span></div>
              <p className="auth-kicker">SECURE DOCUMENT MANAGEMENT</p>
              <h1>Make space for what matters.</h1>
              <p className="auth-intro-copy">Create your account to organize documents, manage sharing and keep important activity visible.</p>
              <div className="auth-feature-list">
                <div><span className="auth-feature-icon">▣</span><span><strong>Private workspace</strong><small>Your documents stay organized in one place.</small></span></div>
                <div><span className="auth-feature-icon">⌑</span><span><strong>Permission-based sharing</strong><small>Keep control over who can access your files.</small></span></div>
                <div><span className="auth-feature-icon">↺</span><span><strong>Document history</strong><small>Follow versions and important activity.</small></span></div>
              </div>
            </aside>
            <section className="auth-card">

            <div className="auth-heading">
              <h1>Create your account</h1>
              <p>Join Trustify to manage your documents securely.</p>
            </div>

            <form onSubmit={handleRegister}>

              <label>Username</label>
              <input
                name="username"
                value={registerData.username}
                onChange={handleRegisterChange}
                autoComplete="username"
                required
              />

              <label>Email</label>
              <input
                type="email"
                name="email"
                value={registerData.email}
                onChange={handleRegisterChange}
                autoComplete="email"
                required
              />

              <div className="form-row">
                <div>
                  <label>First name</label>
                  <input
                    name="first_name"
                    value={registerData.first_name}
                    onChange={handleRegisterChange}
                    autoComplete="given-name"
                  />
                </div>

                <div>
                  <label>Last name</label>
                  <input
                    name="last_name"
                    value={registerData.last_name}
                    onChange={handleRegisterChange}
                    autoComplete="family-name"
                  />
                </div>
              </div>

              <label>Password</label>
              <input
                type="password"
                name="password"
                value={registerData.password}
                onChange={handleRegisterChange}
                autoComplete="new-password"
                minLength="8"
                required
              />

              <label>Confirm password</label>
              <input
                type="password"
                name="password_confirm"
                value={registerData.password_confirm}
                onChange={handleRegisterChange}
                autoComplete="new-password"
                required
              />

              <button
                type="submit"
                className="primary-button"
                disabled={loading}
              >
                {loading ? "Creating account..." : "Create Account"}
              </button>

            </form>

            <p className="auth-footer">
              Already registered?{" "}
              <button
                className="text-button"
                onClick={() => {
                  setError("");
                  setSuccess("");
                  setPage("login");
                }}
              >
                Sign In
              </button>
            </p>

            </section>
          </div>
        )}

        {user && page === "dashboard" && (
          <section className="dashboard-card">

            <div className="dashboard-welcome">
              <div className="dashboard-heading">
                <span className="status-indicator"></span>
                <span>Authenticated successfully</span>
              </div>

              <h1>Welcome, {user.first_name || user.username}!</h1>

              <p className="dashboard-description">
                Your Trustify account is active. Your documents and account tools are ready.
              </p>

              <div className="dashboard-welcome-note">
                <TrustifyMark compact />
                <span>Secure document management, with control and accountability.</span>
              </div>

            </div>

            <div className="profile-section">
              <h2>Account Information</h2>

              <div className="profile-row">
                <span>Username</span>
                <strong>{user.username}</strong>
              </div>

              <div className="profile-row">
                <span>Email</span>
                <strong>{user.email || "Not provided"}</strong>
              </div>

              <div className="profile-row">
                <span>First name</span>
                <strong>{user.first_name || "Not provided"}</strong>
              </div>

              <div className="profile-row">
                <span>Last name</span>
                <strong>{user.last_name || "Not provided"}</strong>
              </div>

              <div className="profile-row">
                <span>Account type</span>
                <strong>
                  {user.is_superuser
                    ? "Superuser"
                    : user.is_staff
                      ? "Staff"
                      : "Standard User"}
                </strong>
              </div>
            </div>

          </section>
        )}
        {user && page === "dashboard" && (
          <DocumentWorkspace user={user} />
        )}
        {user &&
          page === "administration" &&
          user.is_superuser === true && (
            <AdministrationDashboard user={user} />
          )}

      </main>

      <footer className="app-footer">
        Trustify © 2026 · Secure Document Management
      </footer>

    </div>
  );
}

export default App;
