import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./AdministrationAuditActivity.css";

const ACTIONS = [
  "LOGIN_SUCCESS",
  "LOGIN_FAILED",
  "DOCUMENT_UPLOAD",
  "DOCUMENT_VIEW",
  "DOCUMENT_DOWNLOAD",
  "DOCUMENT_UPDATE",
  "DOCUMENT_DELETE",
  "VERSION_CREATED",
  "PERMISSION_GRANTED",
  "PERMISSION_REVOKED",
  "ACCESS_DENIED",
  "USER_ACTIVATED",
  "USER_DEACTIVATED",
  "STAFF_PRIVILEGE_CHANGED",
  "SUPERUSER_PRIVILEGE_CHANGED",
  "USER_DETAILS_UPDATED",
];

function formatDate(value) {
  if (!value) return "Not available";
  return new Date(value).toLocaleString();
}

function AdministrationAuditActivity() {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [integrity, setIntegrity] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
      });

      if (search) params.set("search", search);
      if (action) params.set("action", action);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);

      const result = await apiRequest(
        `/api/administration/audit-events/?${params.toString()}`
      );

      if (
        !result ||
        !Array.isArray(result.results) ||
        typeof result.count !== "number"
      ) {
        throw new Error("Unexpected audit event response.");
      }

      setEvents(result.results);
      setPagination({
        count: result.count,
        next: result.next,
        previous: result.previous,
      });
    } catch (err) {
      setEvents([]);
      setError(err.message || "Unable to load audit events.");
    } finally {
      setLoading(false);
    }
  }, [page, search, action, dateFrom, dateTo]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  async function verifyIntegrity() {
    setVerifying(true);
    setIntegrity(null);

    try {
      const result = await apiRequest(
        "/api/administration/audit-integrity/"
      );

      setIntegrity(result);
    } catch (err) {
      setIntegrity({
        valid: false,
        verification_error:
          err.message || "Unable to verify audit integrity.",
      });
    } finally {
      setVerifying(false);
    }
  }

  async function viewDetails(eventId) {
    setSelectedEvent(null);
    setDetailLoading(true);

    try {
      const result = await apiRequest(
        `/api/administration/audit-events/${eventId}/`
      );

      setSelectedEvent(result);
    } catch (err) {
      setError(err.message || "Unable to load event details.");
    } finally {
      setDetailLoading(false);
    }
  }

  function applyFilters(event) {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  function clearFilters() {
    setSearchInput("");
    setSearch("");
    setAction("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  }

  const totalPages = Math.max(
    1,
    Math.ceil(pagination.count / 20)
  );

  return (
    <section className="admin-audit">
      <div className="admin-audit-heading">
        <div>
          <h2>Audit Activity</h2>
          <p>
            Review recorded system events and security activity.
          </p>
        </div>

        <div className="admin-audit-actions">
          <button
            type="button"
            onClick={verifyIntegrity}
            disabled={verifying}
          >
            {verifying ? "Verifying..." : "Verify Integrity"}
          </button>

          <button
            type="button"
            onClick={loadEvents}
            disabled={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {integrity && (
        <div
          className={`admin-integrity-result ${
            integrity.valid ? "valid" : "invalid"
          }`}
          role="status"
        >
          <strong>
            {integrity.valid
              ? "Audit chain integrity verified"
              : "Audit chain verification failed"}
          </strong>

          {integrity.verification_error ? (
            <p>{integrity.verification_error}</p>
          ) : (
            <>
              <p>
                Events checked:{" "}
                {integrity.checked?.toLocaleString() ?? "Unavailable"}
              </p>

              {!integrity.valid && (
                <>
                  <p>
                    Invalid event ID:{" "}
                    {integrity.invalid_event_id ?? "Unavailable"}
                  </p>
                  <p>{integrity.reason || "Integrity verification failed."}</p>
                </>
              )}
            </>
          )}
        </div>
      )}

      <form
        className="admin-audit-filters"
        onSubmit={applyFilters}
      >
        <input
          type="search"
          value={searchInput}
          onChange={event => setSearchInput(event.target.value)}
          placeholder="Search description, user or document..."
          aria-label="Search audit events"
        />

        <select
          value={action}
          onChange={event => {
            setAction(event.target.value);
            setPage(1);
          }}
          aria-label="Filter by action"
        >
          <option value="">All event types</option>

          {ACTIONS.map(item => (
            <option key={item} value={item}>
              {item.replaceAll("_", " ")}
            </option>
          ))}
        </select>

        <label>
          From
          <input
            type="date"
            value={dateFrom}
            max={dateTo || undefined}
            onChange={event => {
              setDateFrom(event.target.value);
              setPage(1);
            }}
          />
        </label>

        <label>
          To
          <input
            type="date"
            value={dateTo}
            min={dateFrom || undefined}
            onChange={event => {
              setDateTo(event.target.value);
              setPage(1);
            }}
          />
        </label>

        <button type="submit" disabled={loading}>
          Search
        </button>

        <button
          type="button"
          onClick={clearFilters}
          disabled={loading}
        >
          Clear
        </button>
      </form>

      <div className="admin-audit-count">
        {pagination.count.toLocaleString()} audit event(s)
      </div>

      {error && (
        <div className="admin-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="admin-empty-state">
          Loading audit events...
        </div>
      ) : events.length === 0 ? (
        <div className="admin-empty-state">
          No audit events found.
        </div>
      ) : (
        <div className="admin-table-wrapper">
          <table className="admin-table admin-audit-table">
            <thead>
              <tr>
                <th>Date and time</th>
                <th>Action</th>
                <th>Actor</th>
                <th>Target user</th>
                <th>Document</th>
                <th>Description</th>
                <th>Details</th>
              </tr>
            </thead>

            <tbody>
              {events.map(item => (
                <tr key={item.id}>
                  <td>{formatDate(item.created_at)}</td>

                  <td>
                    <span className="admin-audit-action">
                      {item.action.replaceAll("_", " ")}
                    </span>
                  </td>

                  <td>{item.actor_username || "Anonymous"}</td>
                  <td>{item.target_username || "—"}</td>
                  <td>{item.document_title || "—"}</td>
                  <td>{item.description || "—"}</td>

                  <td>
                    <button
                      type="button"
                      className="admin-audit-detail-button"
                      onClick={() => viewDetails(item.id)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="admin-pagination">
        <button
          type="button"
          onClick={() => setPage(current => current - 1)}
          disabled={!pagination.previous || loading}
        >
          Previous
        </button>

        <span>
          Page {page} of {totalPages}
        </span>

        <button
          type="button"
          onClick={() => setPage(current => current + 1)}
          disabled={!pagination.next || loading}
        >
          Next
        </button>
      </div>

      {detailLoading && (
        <div className="admin-empty-state">
          Loading event details...
        </div>
      )}

      {selectedEvent && (
        <div className="admin-audit-detail">
          <div className="admin-audit-detail-heading">
            <div>
              <h3>Audit Event #{selectedEvent.id}</h3>
              <p>{selectedEvent.action.replaceAll("_", " ")}</p>
            </div>

            <button
              type="button"
              onClick={() => setSelectedEvent(null)}
            >
              Close
            </button>
          </div>

          <dl className="admin-audit-detail-grid">
            <dt>Date and time</dt>
            <dd>{formatDate(selectedEvent.created_at)}</dd>

            <dt>Actor</dt>
            <dd>{selectedEvent.actor_username || "Anonymous"}</dd>

            <dt>Target user</dt>
            <dd>{selectedEvent.target_username || "—"}</dd>

            <dt>Document</dt>
            <dd>{selectedEvent.document_title || "—"}</dd>

            <dt>IP address</dt>
            <dd>{selectedEvent.ip_address || "Not available"}</dd>

            <dt>User agent</dt>
            <dd>{selectedEvent.user_agent || "Not available"}</dd>

            <dt>Description</dt>
            <dd>{selectedEvent.description || "—"}</dd>
          </dl>

          <h4>Metadata</h4>
          <pre className="admin-audit-json">
            {JSON.stringify(selectedEvent.metadata, null, 2)}
          </pre>

          <h4>Previous hash</h4>
          <code className="admin-audit-hash">
            {selectedEvent.previous_hash || "(First event)"}
          </code>

          <h4>Event hash</h4>
          <code className="admin-audit-hash">
            {selectedEvent.event_hash}
          </code>
        </div>
      )}
    </section>
  );
}

export default AdministrationAuditActivity;