
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./AdministrationDashboard.css";
import AdministrationUserDirectory from "./AdministrationUserDirectory";
import AdministrationAuditActivity from "./AdministrationAuditActivity";

function formatBytes(bytes) {
  if (!bytes) return "0 Bytes";

  const units = ["Bytes", "KB", "MB", "GB", "TB"];
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );

  return `${(bytes / Math.pow(1024, index)).toFixed(2)} ${units[index]}`;
}

function formatDate(date) {
  if (!date) return "Not available";

  return new Date(date).toLocaleString();
}

function StatCard({ label, value, description }) {
  return (
    <article className="admin-stat-card">
      <span className="admin-stat-label">{label}</span>
      <strong className="admin-stat-value">
        {typeof value === "number" ? value.toLocaleString() : value}
      </strong>
      {description && (
        <span className="admin-stat-description">{description}</span>
      )}
    </article>
  );
}

function AdministrationDashboard({ user }) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [showUserDirectory, setShowUserDirectory] = useState(false);

  const loadDashboard = useCallback(async (showRefresh = false) => {
    setError("");

    if (showRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const result = await apiRequest(
        "/api/administration/dashboard/"
      );

      if (
        !result ||
        !result.users ||
        !result.documents ||
        !result.versions ||
        !result.storage ||
        !result.audit ||
        !Array.isArray(result.recent_security_events)
      ) {
        throw new Error("Unexpected administration dashboard response.");
      }

      setDashboard(result);
    } catch (err) {
      setError(
        err.message || "Unable to load administration dashboard."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <section className="admin-dashboard">
        <div className="admin-loading">Loading administration dashboard...</div>
      </section>
    );
  }

  if (!dashboard) {
    return (
      <section className="admin-dashboard">
        <div className="admin-header">
          <div>
            <span className="admin-eyebrow">TRUSTIFY ADMINISTRATION</span>
            <h1>Administration Dashboard</h1>
          </div>
          <button
            type="button"
            className="admin-refresh-button"
            onClick={() => loadDashboard()}
          >
            Retry
          </button>
        </div>

        {error && (
          <div className="admin-error" role="alert">
            {error}
          </div>
        )}
      </section>
    );
  }

  const { users, documents, versions, storage, audit } = dashboard;

  return (
    <section className="admin-dashboard">
      <div className="admin-header">
        <div>
          <span className="admin-eyebrow">TRUSTIFY ADMINISTRATION</span>
          <h1>Administration Dashboard</h1>
          <p>Monitor users, documents, storage and security activity.</p>
        </div>

        <button
          type="button"
          className="admin-refresh-button"
          onClick={() => setShowUserDirectory(current => !current)}
          aria-expanded={showUserDirectory}
        >
          {showUserDirectory ? "Hide User Directory" : "User Directory"}
        </button>

        <button
          type="button"
          className="admin-refresh-button"
          onClick={() => loadDashboard(true)}
          disabled={refreshing}
        >
          {refreshing ? "Refreshing..." : "Refresh data"}
        </button>
      </div>

      {error && (
        <div className="admin-error" role="alert">
          {error}
        </div>
      )}
      {showUserDirectory && (
        <AdministrationUserDirectory currentUser={user} />
      )}
      <AdministrationAuditActivity />

      <div className="admin-section">
        <div className="admin-section-heading">
          <h2>User overview</h2>
          <span>Account statistics</span>
        </div>

        <div className="admin-stat-grid">
          <StatCard label="Total users" value={users.total} />
          <StatCard label="Active users" value={users.active} />
          <StatCard label="Inactive users" value={users.inactive} />
          <StatCard label="Staff members" value={users.staff} />
          <StatCard label="Superusers" value={users.superusers} />
        </div>
      </div>

      <div className="admin-section">
        <div className="admin-section-heading">
          <h2>Document overview</h2>
          <span>Document library statistics</span>
        </div>

        <div className="admin-stat-grid">
          <StatCard label="Total documents" value={documents.total} />
          <StatCard label="Active documents" value={documents.active} />
          <StatCard label="Archived documents" value={documents.archived} />
          <StatCard label="Deleted documents" value={documents.deleted} />
          <StatCard label="Document versions" value={versions.total} />
        </div>
      </div>

      <div className="admin-section">
        <div className="admin-section-heading">
          <h2>Storage overview</h2>
          <span>Logical file-size totals</span>
        </div>

        <div className="admin-stat-grid admin-storage-grid">
          <StatCard
            label="Original documents"
            value={formatBytes(storage.document_bytes)}
          />
          <StatCard
            label="Version files"
            value={formatBytes(storage.version_bytes)}
          />
          <StatCard
            label="Combined storage"
            value={formatBytes(storage.total_bytes)}
          />
        </div>
      </div>

      <div className="admin-section">
        <div className="admin-section-heading">
          <h2>Audit overview</h2>
          <span>Recorded security and system events</span>
        </div>

        <div className="admin-stat-grid admin-storage-grid">
          <StatCard
            label="Total audit events"
            value={audit.total_events}
          />
        </div>
      </div>

      <div className="admin-section">
        <div className="admin-section-heading">
          <h2>Recent security activity</h2>
          <span>Latest failed logins and denied access events</span>
        </div>

        {dashboard.recent_security_events.length === 0 ? (
          <div className="admin-empty-state">
            No recent security events were found.
          </div>
        ) : (
          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Description</th>
                  <th>Actor</th>
                  <th>Target user</th>
                  <th>IP address</th>
                  <th>Date and time</th>
                </tr>
              </thead>

              <tbody>
                {dashboard.recent_security_events.map(event => (
                  <tr key={event.id}>
                    <td>
                      <span className={`admin-event-type ${event.action === "LOGIN_FAILED" ? "failed" : "denied"}`}>
                        {event.action.replaceAll("_", " ")}
                      </span>
                    </td>
                    <td>{event.description || "—"}</td>
                    <td>{event.actor__username || "Anonymous"}</td>
                    <td>{event.target_user__username || "—"}</td>
                    <td>{event.ip_address || "—"}</td>
                    <td>{formatDate(event.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

export default AdministrationDashboard;
