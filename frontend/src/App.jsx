
import { useEffect, useState } from "react";
import { apiRequest } from "./services/api";
import "./App.css";

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
          <span className="brand-icon">T</span>
          <span>Trustify</span>
        </div>

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

      <main className="main-content">

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
        )}

        {!user && page === "register" && (
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
        )}

        {user && page === "dashboard" && (
          <section className="dashboard-card">

            <div className="dashboard-heading">
              <span className="status-indicator"></span>
              <span>Authenticated successfully</span>
            </div>

            <h1>Welcome, {user.first_name || user.username}!</h1>

            <p className="dashboard-description">
              Your Trustify account is active.
            </p>

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
                  {user.is_staff ? "Staff" : "Standard User"}
                </strong>
              </div>
            </div>

            <button
              className="primary-button"
              onClick={handleLogout}
              disabled={loading}
            >
              {loading ? "Signing out..." : "Sign Out"}
            </button>

          </section>
        )}

      </main>

      <footer className="app-footer">
        Trustify © 2026 · Secure Document Management
      </footer>

    </div>
  );
}

export default App;
