
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiRequest, apiUpload, apiDownload } from "../services/api";
import "./DocumentWorkspace.css";

const MAX_FILE_SIZE = 20 * 1024 * 1024;

const ALLOWED_EXTENSIONS = [
  "pdf",
  "jpg",
  "jpeg",
  "png",
  "txt",
];

function formatFileSize(bytes) {
  if (!bytes) return "0 Bytes";

  const units = ["Bytes", "KB", "MB", "GB"];
  const index = Math.floor(Math.log(bytes) / Math.log(1024));

  return `${(bytes / Math.pow(1024, index)).toFixed(2)} ${units[index]}`;
}

function formatDate(date) {
  if (!date) return "Not available";

  return new Date(date).toLocaleDateString();
}

function DocumentWorkspace({user}) {
  const [documents, setDocuments] = useState([]);
  const [search, setSearch] = useState("");
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [uploading, setUploading] = useState(false);
const [downloadingId, setDownloadingId] = useState(null);

const [activeVersionDocumentId, setActiveVersionDocumentId] = useState(null);
const [versions, setVersions] = useState([]);
const [loadingVersions, setLoadingVersions] = useState(false);
const [versionFile, setVersionFile] = useState(null);
const [changeNote, setChangeNote] = useState("");
const [uploadingVersion, setUploadingVersion] = useState(false);

  // Document permission management
  const [activePermissionDocumentId, setActivePermissionDocumentId] =
    useState(null);
  const [permissions, setPermissions] = useState([]);
  const [loadingPermissions, setLoadingPermissions] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [revokingPermissionId, setRevokingPermissionId] = useState(null);

  const [shareUsername, setShareUsername] = useState("");
  const [shareAccessLevel, setShareAccessLevel] = useState("READ");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadDocuments = useCallback(async () => {
    setLoadingDocuments(true);
    setError("");

    try {
      const result = await apiRequest("/api/documents/");

      if (!Array.isArray(result)) {
        throw new Error("Unexpected document list response.");
      }

      setDocuments(result);
    } catch (err) {
      setError(err.message || "Unable to load documents.");
    } finally {
      setLoadingDocuments(false);
    }
  }, []);
  // Check whether the current user can manage document permissions.
  function canManageDocument(documentItem) {
    return (
      documentItem.owner === user?.id ||
      user?.is_superuser === true
    );
  }

  // Load active permissions for a document.
  async function handleViewPermissions(documentItem) {
    setError("");
    setSuccess("");
    setShareUsername("");
    setShareAccessLevel("READ");

    if (activePermissionDocumentId === documentItem.id) {
      setActivePermissionDocumentId(null);
      setPermissions([]);
      return;
    }

    setActivePermissionDocumentId(documentItem.id);
    setLoadingPermissions(true);
    setPermissions([]);

    try {
      const result = await apiRequest(
        `/api/documents/${documentItem.id}/permissions/`
      );

      if (!Array.isArray(result)) {
        throw new Error("Unexpected permissions response.");
      }

      setPermissions(result);
    } catch (err) {
      setActivePermissionDocumentId(null);
      setError(err.message || "Unable to load document permissions.");
    } finally {
      setLoadingPermissions(false);
    }
  }

  // Grant or update document access.
  async function handleShareDocument(event, documentItem) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!shareUsername.trim()) {
      setError("Please enter the username of the person to share with.");
      return;
    }

    setSharing(true);

    try {
      await apiRequest(
        `/api/documents/${documentItem.id}/share/`,
        {
          method: "POST",
          body: JSON.stringify({
            username: shareUsername.trim(),
            access_level: shareAccessLevel,
          }),
        }
      );

      setShareUsername("");

      const updatedPermissions = await apiRequest(
        `/api/documents/${documentItem.id}/permissions/`
      );

      setPermissions(updatedPermissions);
      setSuccess("Document access granted or updated successfully.");
    } catch (err) {
      setError(err.message || "Unable to share document.");
    } finally {
      setSharing(false);
    }
  }

  // Revoke an existing document permission.
  async function handleRevokePermission(documentItem, permissionId) {
    const confirmed = window.confirm(
      "Are you sure you want to revoke this user's document access?"
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");
    setRevokingPermissionId(permissionId);

    try {
      await apiRequest(
        `/api/documents/${documentItem.id}/permissions/${permissionId}/revoke/`,
        {
          method: "DELETE",
        }
      );

      setPermissions(current =>
        current.filter(permission => permission.id !== permissionId)
      );

      setSuccess("Document access revoked successfully.");
    } catch (err) {
      setError(err.message || "Unable to revoke document access.");
    } finally {
      setRevokingPermissionId(null);
    }
  }

    useEffect(() => {
    const timer = setTimeout(() => {
      loadDocuments();
    }, 0);

    return () => clearTimeout(timer);
  }, [loadDocuments]);

  const filteredDocuments = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return documents;

    return documents.filter(document =>
      document.title.toLowerCase().includes(query) ||
      document.original_filename.toLowerCase().includes(query)
    );
  }, [documents, search]);

  function handleFileChange(event) {
    const file = event.target.files?.[0] || null;

    setSelectedFile(file);
    setError("");
    setSuccess("");
  }

  async function handleUpload(event) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!selectedFile) {
      setError("Please select a document file.");
      return;
    }

    const extension = selectedFile.name
      .split(".")
      .pop()
      .toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError("Only PDF, JPG, JPEG, PNG and TXT files are allowed.");
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setError("The maximum allowed file size is 20 MB.");
      return;
    }

    if (!title.trim()) {
      setError("Document title is required.");
      return;
    }

    const formData = new FormData();

    formData.append("file", selectedFile);
    formData.append("title", title.trim());
    formData.append("description", description.trim());

    setUploading(true);

    try {
      await apiUpload("/api/documents/upload/", formData);

      setTitle("");
      setDescription("");
      setSelectedFile(null);

      const fileInput = document.getElementById("document-file");
      if (fileInput) fileInput.value = "";

      setSuccess("Document uploaded successfully.");

      await loadDocuments();
    } catch (err) {
      setError(err.message || "Document upload failed.");
    } finally {
      setUploading(false);
    }
  }
  async function handleDownload(documentItem) {
    setError("");
    setSuccess("");
    setDownloadingId(documentItem.id);

    try {
      const blob = await apiDownload(
        `/api/documents/${documentItem.id}/download/`
      );

      const downloadUrl = URL.createObjectURL(blob);
      const link = window.document.createElement("a");

      link.href = downloadUrl;
      link.download = documentItem.original_filename;
      link.style.display = "none";

      window.document.body.appendChild(link);
      link.click();
      link.remove();

      setTimeout(() => {
        URL.revokeObjectURL(downloadUrl);
      }, 1000);

      setSuccess(`${documentItem.title} downloaded successfully.`);
    } catch (err) {
      setError(err.message || "Document download failed.");
    } finally {
      setDownloadingId(null);
    }
  }
  async function handleViewVersions(documentItem) {
    setError("");
    setSuccess("");
    setVersionFile(null);
    setChangeNote("");

    if (activeVersionDocumentId === documentItem.id) {
      setActiveVersionDocumentId(null);
      setVersions([]);
      return;
    }

    setActiveVersionDocumentId(documentItem.id);
    setLoadingVersions(true);
    setVersions([]);

    try {
      const result = await apiRequest(
        `/api/documents/${documentItem.id}/versions/`
      );

      if (!Array.isArray(result)) {
        throw new Error("Unexpected version history response.");
      }

      setVersions(result);
    } catch (err) {
      setError(err.message || "Unable to load version history.");
    } finally {
      setLoadingVersions(false);
    }
  }
  async function handleVersionUpload(event, documentItem) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!versionFile) {
      setError("Please select a file for the new version.");
      return;
    }

    const extension = versionFile.name
      .split(".")
      .pop()
      .toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError("Only PDF, JPG, JPEG, PNG and TXT files are allowed.");
      return;
    }

    if (versionFile.size > MAX_FILE_SIZE) {
      setError("The maximum allowed file size is 20 MB.");
      return;
    }

    const formData = new FormData();

    formData.append("file", versionFile);
    formData.append("change_note", changeNote.trim());

    setUploadingVersion(true);

    try {
      await apiUpload(
        `/api/documents/${documentItem.id}/versions/upload/`,
        formData
      );

      setVersionFile(null);
      setChangeNote("");

      const fileInput = window.document.getElementById(
        `version-file-${documentItem.id}`
      );

      if (fileInput) {
        fileInput.value = "";
      }

      const updatedVersions = await apiRequest(
        `/api/documents/${documentItem.id}/versions/`
      );

      setVersions(updatedVersions);

      await loadDocuments();

      setSuccess("New document version uploaded successfully.");
    } catch (err) {
      setError(err.message || "Version upload failed.");
    } finally {
      setUploadingVersion(false);
    }
  }
  return (
    <section className="document-workspace">

      <div className="workspace-heading">
        <div>
          <h2>My Documents</h2>
          <p>Securely manage your documents in Trustify.</p>
        </div>

        <button
          type="button"
          className="secondary-button"
          onClick={loadDocuments}
          disabled={loadingDocuments}
        >
          {loadingDocuments ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="workspace-message workspace-error">
          {error}
        </div>
      )}

      {success && (
        <div className="workspace-message workspace-success">
          {success}
        </div>
      )}

      <div className="upload-card">
        <h3>Upload a document</h3>

        <form onSubmit={handleUpload}>

          <label htmlFor="document-title">Document title</label>
          <input
            id="document-title"
            type="text"
            value={title}
            onChange={event => setTitle(event.target.value)}
            maxLength={255}
            placeholder="Enter document title"
            required
          />

          <label htmlFor="document-description">
            Description (optional)
          </label>
          <textarea
            id="document-description"
            value={description}
            onChange={event => setDescription(event.target.value)}
            placeholder="Describe this document"
            rows={3}
          />

          <label htmlFor="document-file">Choose file</label>
          <input
            id="document-file"
            type="file"
            accept=".pdf,.jpg,.jpeg,.png,.txt"
            onChange={handleFileChange}
            required
          />

          <p className="file-hint">
            PDF, JPG, JPEG, PNG or TXT. Maximum size: 20 MB.
          </p>

          {selectedFile && (
            <p className="selected-file">
              Selected: {selectedFile.name} (
              {formatFileSize(selectedFile.size)})
            </p>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={uploading}
          >
            {uploading ? "Uploading..." : "Upload Document"}
          </button>

        </form>
      </div>

      <div className="document-list-card">

        <div className="document-list-heading">
          <h3>Document Library</h3>
          <span>{documents.length} document(s)</span>
        </div>

        <input
          className="document-search"
          type="search"
          placeholder="Search by title or filename..."
          value={search}
          onChange={event => setSearch(event.target.value)}
        />

        {loadingDocuments ? (
          <p className="empty-state">Loading documents...</p>
        ) : filteredDocuments.length === 0 ? (
          <p className="empty-state">
            {documents.length === 0
              ? "No documents found. Upload your first document."
              : "No documents match your search."}
          </p>
        ) : (
          <div className="document-table-wrapper">
            <table className="document-table">
              <thead>
                <tr>
                  <th>Document</th>
		<th>Owner</th>
		<th>Size</th>
		<th>Status</th>
		<th>Uploaded</th>
		<th>Action</th>
                </tr>
              </thead>

              <tbody>
                {filteredDocuments.map(document => (
                  <tr key={document.id}>
                    <td>
                      <strong>{document.title}</strong>
                      <span className="document-filename">
                        {document.original_filename}
                      </span>
                    </td>

                    <td>{document.owner_username}</td>

                    <td>{formatFileSize(document.file_size)}</td>

                    <td>
                      <span className="document-status">
                        {document.status}
                      </span>
                    </td>

                    <td>{formatDate(document.created_at)}</td>
		<td>
<div className="document-actions">
  <button
    type="button"
    className="download-button"
    onClick={() => handleDownload(document)}
    disabled={downloadingId === document.id}
  >
    {downloadingId === document.id ? "Downloading..." : "Download"}
  </button>

  <button
    type="button"
    className="history-button"
    onClick={() => handleViewVersions(document)}
    disabled={loadingVersions}
  >
    {activeVersionDocumentId === document.id
      ? "Hide History"
      : "Version History"}
  </button>

  {canManageDocument(document) && (
    <button
      type="button"
      className="history-button"
      onClick={() => handleViewPermissions(document)}
      disabled={loadingPermissions}
    >
      {activePermissionDocumentId === document.id
        ? "Hide Access"
        : "Manage Access"}
    </button>
  )}

</div></td>
                  </tr>
                ))}
             </tbody>
            </table>

            {filteredDocuments.map(document => (
              activeVersionDocumentId === document.id && (
                <div className="version-panel" key={document.id}>
                  <div className="version-heading">
                    <h4>Version History — {document.title}</h4>
                  </div>

                  {loadingVersions ? (
                    <p className="empty-state">
                      Loading version history...
                    </p>
                  ) : versions.length === 0 ? (
                    <p className="empty-state">
                      No version history available.
                    </p>
                  ) : (
                    <div className="version-list">
                      {versions.map(version => (
                        <div className="version-item" key={version.id}>
                          <div>
                            <strong>Version {version.version_number}</strong>
                            <span>{version.filename}</span>
                          </div>

                          <div>
                            <span>Uploaded by: {version.uploaded_by}</span>
                            <span>Size: {formatFileSize(version.file_size)}</span>
                            <span>Date: {formatDate(version.created_at)}</span>
                          </div>

                          <p>
                            {version.change_note || "No change note provided."}
                          </p>

                          {version.version_number === 1 && (
                            <span className="version-current">
                              Original version
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <form
                    className="version-upload-form"
                    onSubmit={event =>
                      handleVersionUpload(event, document)
                    }
                  >
                    <h4>Upload a new version</h4>

                    <label htmlFor={`version-file-${document.id}`}>
                      Select replacement file
                    </label>

                    <input
                      id={`version-file-${document.id}`}
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png,.txt"
                      onChange={event =>
                        setVersionFile(event.target.files?.[0] || null)
                      }
                    />

                    <label htmlFor={`change-note-${document.id}`}>
                      Change note (optional)
                    </label>

                    <textarea
                      id={`change-note-${document.id}`}
                      rows={3}
                      value={changeNote}
                      onChange={event => setChangeNote(event.target.value)}
                      placeholder="Describe what changed in this version"
                    />

                    <button
                      type="submit"
                      className="primary-button"
                      disabled={uploadingVersion}
                    >
                      {uploadingVersion
                        ? "Uploading version..."
                        : "Upload New Version"}
                    </button>

                    <p className="file-hint">
                      Maximum file size: 20 MB. Editing permission is required.
                    </p>
                  </form>
                </div>
              )
            ))}
            <>
                       {filteredDocuments.map(document => (
              activePermissionDocumentId === document.id && (
                <div className="permission-panel" key={`permissions-${document.id}`}>
                  <h4>Manage Document Access — {document.title}</h4>

                  {loadingPermissions ? (
                    <p className="empty-state">Loading permissions...</p>
                  ) : (
                    <>
                      <form
                        className="permission-form"
                        onSubmit={event =>
                          handleShareDocument(event, document)
                        }
                      >
                        <label htmlFor={`share-username-${document.id}`}>
                          Username
                        </label>

                        <input
                          id={`share-username-${document.id}`}
                          type="text"
                          value={shareUsername}
                          onChange={event =>
                            setShareUsername(event.target.value)
                          }
                          placeholder="Enter registered username"
                          required
                        />

                        <label htmlFor={`share-level-${document.id}`}>
                          Access level
                        </label>

                        <select
                          id={`share-level-${document.id}`}
                          value={shareAccessLevel}
                          onChange={event =>
                            setShareAccessLevel(event.target.value)
                          }
                        >
                          <option value="READ">READ — View and download</option>
                          <option value="EDIT">EDIT — View and upload versions</option>
                        </select>

                        <button
                          type="submit"
                          className="primary-button"
                          disabled={sharing}
                        >
                          {sharing ? "Saving access..." : "Grant Access"}
                        </button>
                      </form>

                      <div className="permission-list">
                        <h5>Users with access</h5>

                        {permissions.length === 0 ? (
                          <p className="empty-state">
                            No users have been granted access yet.
                          </p>
                        ) : (
                          permissions.map(permission => (
                            <div
                              className="permission-item"
                              key={permission.id}
                            >
                              <div>
                                <strong>{permission.username}</strong>
                                <span>
                                  {permission.access_level} access
                                </span>
                              </div>

                              <button
                                type="button"
                                className="revoke-button"
                                onClick={() =>
                                  handleRevokePermission(
                                    document,
                                    permission.id
                                  )
                                }
                                disabled={
                                  revokingPermissionId === permission.id
                                }
                              >
                                {revokingPermissionId === permission.id
                                  ? "Revoking..."
                                  : "Revoke"}
                              </button>
                            </div>
                          ))
                        )}
                      </div>
                    </>
                  )}
                </div>
              )
                        ))}
          </>
          </div>
        )}
      </div>
    </section>
  );
}

export default DocumentWorkspace;
