
import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "../services/api";
import "./AdministrationUserDetails.css";

function formatDate(value) {
  if (!value) return "Never";

  return new Date(value).toLocaleString();
}

function AdministrationUserDetails({
  userId,
  currentUser,
  onClose,
  onUpdated,
}) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadUser = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await apiRequest(
        `/api/administration/users/${userId}/`
      );

      if (!result || result.id !== userId) {
        throw new Error("Unexpected user details response.");
      }

      setUser(result);
    } catch (err) {
      setError(err.message || "Unable to load user details.");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  async function updateStatus() {
    if (!user) return;

    const newStatus = !user.is_active;
    const action = newStatus ? "activate" : "deactivate";

    const confirmed = window.confirm(
      `Are you sure you want to ${action} the account for ${user.username}?`
    );

    if (!confirmed) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const result = await apiRequest(
        `/api/administration/users/${user.id}/status/`,
        {
          method: "PATCH",
          body: JSON.stringify({
            is_active: newStatus,
          }),
        }
      );

      setUser(result.user);
      setSuccess(result.message || "Account status updated successfully.");

      await onUpdated();
    } catch (err) {
      setError(err.message || "Unable to update account status.");
    } finally {
      setSaving(false);
    }
  }

  async function updatePrivileges(changes, description) {
    if (!user) return;

    const confirmed = window.confirm(
      `Are you sure you want to ${description} for ${user.username}?`
    );

    if (!confirmed) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const result = await apiRequest(
        `/api/administration/users/${user.id}/privileges/`,
        {
          method: "PATCH",
          body: JSON.stringify(changes),
        }
      );

      setUser(result.user);
      setSuccess(result.message || "User privileges updated successfully.");

      await onUpdated();
    } catch (err) {
      setError(err.message || "Unable to update user privileges.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="admin-user-details">
        <div className="admin-user-details-header">
          <h3>User Details</h3>
          <button type="button" onClick={onClose}>
            Close
          </button>
        </div>
        <p className="admin-details-loading">Loading user information...</p>
      </section>
    );
  }

  if (!user) {
    return (
      <section className="admin-user-details">
        <div className="admin-user-details-header">
          <h3>User Details</h3>
          <button type="button" onClick={onClose}>
            Close
          </button>
        </div>
        {error && (
          <div className="admin-error" role="alert">
            {error}
          </div>
        )}
        <button
          type="button"
          className="admin-detail-button"
          onClick={loadUser}
        >
          Retry
        </button>
      </section>
    );
  }

  const isCurrentUser = user.id === currentUser?.id;

  const canDemoteSuperuser =
    user.is_superuser && !isCurrentUser;
  const canChangeStaff =
    !user.is_superuser || canDemoteSuperuser;
  return (
    <section className="admin-user-details">
      <div className="admin-user-details-header">
        <div>
          <span className="admin-eyebrow">ACCOUNT MANAGEMENT</span>
          <h3>{user.username}</h3>
          <p>Review and manage this account.</p>
        </div>

        <button
          type="button"
          className="admin-detail-close"
          onClick={onClose}
          disabled={saving}
        >
          Close
        </button>
      </div>

      {error && (
        <div className="admin-error" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="admin-detail-success" role="status">
          {success}
        </div>
      )}

      <div className="admin-detail-information">
        <div>
          <span>User ID</span>
          <strong>{user.id}</strong>
        </div>
        <div>
          <span>Username</span>
          <strong>{user.username}</strong>
        </div>
        <div>
          <span>Email</span>
          <strong>{user.email || "Not provided"}</strong>
        </div>
        <div>
          <span>First name</span>
          <strong>{user.first_name || "Not provided"}</strong>
        </div>
        <div>
          <span>Last name</span>
          <strong>{user.last_name || "Not provided"}</strong>
        </div>
        <div>
          <span>Account status</span>
          <strong>{user.is_active ? "Active" : "Inactive"}</strong>
        </div>
        <div>
          <span>Staff privileges</span>
          <strong>{user.is_staff ? "Enabled" : "Disabled"}</strong>
        </div>
        <div>
          <span>Superuser privileges</span>
          <strong>{user.is_superuser ? "Enabled" : "Disabled"}</strong>
        </div>
        <div>
          <span>Date joined</span>
          <strong>{formatDate(user.date_joined)}</strong>
        </div>
        <div>
          <span>Last login</span>
          <strong>{formatDate(user.last_login)}</strong>
        </div>
      </div>

      <div className="admin-detail-actions">
        <h4>Account status controls</h4>

        <button
          type="button"
          className={user.is_active ? "admin-danger-button" : "admin-detail-button"}
          onClick={updateStatus}
          disabled={saving || (user.is_active && isCurrentUser)}
        >
          {saving
            ? "Please wait..."
            : user.is_active
              ? "Deactivate account"
              : "Activate account"}
        </button>

        {isCurrentUser && user.is_active && (
          <p className="admin-detail-note">
            You cannot deactivate your own account.
          </p>
        )}
      </div>

      <div className="admin-detail-actions">
        <h4>Privilege controls</h4>

        <div className="admin-privilege-control">
          <div>
            <strong>Staff privileges</strong>
            <p>
              {user.is_staff
                ? "This user has staff privileges."
                : "This user does not have staff privileges."}
            </p>
          </div>

          <button
            type="button"
            className="admin-detail-button"
            disabled={saving || !canChangeStaff}
            onClick={() =>
              updatePrivileges(
                { is_staff: !user.is_staff },
                user.is_staff
                  ? "remove staff privileges"
                  : "grant staff privileges"
              )
            }
          >
            {user.is_staff ? "Remove Staff" : "Grant Staff"}
          </button>
        </div>

        <div className="admin-privilege-control">
          <div>
            <strong>Superuser privileges</strong>
            <p>
              {user.is_superuser
                ? "This user has full administrative privileges."
                : "This user does not have superuser privileges."}
            </p>
          </div>

          <button
            type="button"
            className={
              user.is_superuser
                ? "admin-danger-button"
                : "admin-detail-button"
            }
            disabled={
              saving ||
              (user.is_superuser && !canDemoteSuperuser)
            }
            onClick={() =>
              updatePrivileges(
                { is_superuser: !user.is_superuser },
                user.is_superuser
                  ? "remove superuser privileges"
                  : "grant superuser privileges"
              )
            }
          >
            {user.is_superuser ? "Remove Superuser" : "Grant Superuser"}
          </button>
        </div>

        {isCurrentUser && (
          <p className="admin-detail-note">
            You cannot remove your own superuser privileges.
          </p>
        )}

        <p className="admin-detail-note">
          Granting superuser privileges also grants staff privileges.
          Removing superuser privileges without specifying staff status
          removes both privileges, as enforced by the backend.
        </p>
      </div>
    </section>
  );
}

export default AdministrationUserDetails;
