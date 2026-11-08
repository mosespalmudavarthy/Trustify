
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./AdministrationUserDirectory.css";
import AdministrationUserDetails from "./AdministrationUserDetails";

function formatDate(value) {
  if (!value) return "Never";

  return new Date(value).toLocaleDateString();
}

function AdministrationUserDirectory({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null,
    previous: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedUserId, setSelectedUserId] = useState(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20",
      });

      if (search) {
        params.set("search", search);
      }

      const result = await apiRequest(
        `/api/administration/users/?${params.toString()}`
      );

      if (
        !result ||
        !Array.isArray(result.results) ||
        typeof result.count !== "number"
      ) {
        throw new Error("Unexpected user directory response.");
      }

      setUsers(result.results);
      setPagination({
        count: result.count,
        next: result.next,
        previous: result.previous,
      });
    } catch (err) {
      setUsers([]);
      setError(err.message || "Unable to load users.");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const params = new URLSearchParams({
          page: String(page),
          page_size: "20",
        });

        if (search) {
          params.set("search", search);
        }

        const result = await apiRequest(
          `/api/administration/users/?${params.toString()}`
        );

        if (
          !result ||
          !Array.isArray(result.results) ||
          typeof result.count !== "number"
        ) {
          throw new Error("Unexpected user directory response.");
        }

        if (active) {
          setUsers(result.results);
          setPagination({
            count: result.count,
            next: result.next,
            previous: result.previous,
          });
        }
      } catch (err) {
        if (active) {
          setUsers([]);
          setError(err.message || "Unable to load users.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [page, search]);

  function handleSearch(event) {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  }

  function clearSearch() {
    setSearchInput("");
    setSearch("");
    setPage(1);
  }

  const totalPages = Math.max(
    1,
    Math.ceil(pagination.count / 20)
  );

  return (
    <section className="admin-users">
      <div className="admin-users-heading">
        <div>
          <h2>User Directory</h2>
          <p>Search and review registered Trustify accounts.</p>
        </div>

        <button
          type="button"
          className="admin-refresh-button"
          onClick={loadUsers}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <form className="admin-user-search" onSubmit={handleSearch}>
        <input
          type="search"
          value={searchInput}
          onChange={event => setSearchInput(event.target.value)}
          placeholder="Search username, email or name..."
          aria-label="Search users"
        />

        <button type="submit" disabled={loading}>
          Search
        </button>

        {search && (
          <button
            type="button"
            className="admin-clear-search"
            onClick={clearSearch}
          >
            Clear
          </button>
        )}
      </form>

      <div className="admin-user-count">
        {pagination.count.toLocaleString()} registered user(s)
      </div>

      {error && (
        <div className="admin-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="admin-empty-state">Loading users...</div>
      ) : users.length === 0 ? (
        <div className="admin-empty-state">
          {search
            ? "No users match your search."
            : "No registered users found."}
        </div>
      ) : (
        <div className="admin-table-wrapper">
          <table className="admin-table admin-user-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Account status</th>
                <th>Privileges</th>
                <th>Joined</th>
                <th>Last login</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {users.map(user => (
                <tr key={user.id}>
                  <td>
                    <strong>{user.username}</strong>
                    <span className="admin-user-name">
                      {[user.first_name, user.last_name]
                        .filter(Boolean)
                        .join(" ") || "Name not provided"}
                    </span>
                    <span className="admin-user-id">
                      ID: {user.id}
                    </span>
                  </td>

                  <td>{user.email || "Not provided"}</td>

                  <td>
                    <span
                      className={`admin-account-status ${
                        user.is_active ? "active" : "inactive"
                      }`}
                    >
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>

                  <td>
                    {user.is_superuser
                      ? "Superuser"
                      : user.is_staff
                        ? "Staff"
                        : "Standard"}
                  </td>

                  <td>{formatDate(user.date_joined)}</td>
                  <td>{formatDate(user.last_login)}</td>

                  <td>
                    <button
                      type="button"
                      className="admin-view-user-button"
                      onClick={() => setSelectedUserId(user.id)}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {selectedUserId !== null && (
        <AdministrationUserDetails
          userId={selectedUserId}
          currentUser={currentUser}
          onClose={() => setSelectedUserId(null)}
          onUpdated={loadUsers}
        />
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
    </section>
  );
}

export default AdministrationUserDirectory;
