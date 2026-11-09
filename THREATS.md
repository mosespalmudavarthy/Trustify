# Trustify Threat Model

## Scope
This is a practical project-level threat overview, not a formal penetration-test report or security certification. It describes important assets, trust boundaries, threats, and controls relevant to Trustify.

## Assets
- Uploaded documents and document versions.
- User accounts and authentication credentials.
- Document ownership and permission records.
- File metadata and SHA-256 checksums.
- Audit events and their integrity.
- Django, database, and Supabase credentials.
- Production database and private storage configuration.

## Trust boundaries
1. **Browser to frontend:** client-side state and input are untrusted.
2. **Frontend to backend:** requests must be authenticated and authorized server-side.
3. **Backend to PostgreSQL:** database access and credentials remain server-side.
4. **Backend to Supabase Storage:** the service-role key is privileged and must never reach the browser.
5. **Backend to downloaded file:** existence, access, and integrity must be checked before content is returned.

## Threats and controls

| Threat | Potential impact | Controls / recommended practice |
|---|---|---|
| Unauthorized document access | Confidentiality breach | Authenticated APIs, ownership checks, active `READ` / `EDIT` permissions |
| Privilege escalation | Unauthorized editing or sharing | Separate view, edit, and permission-management checks; regression tests |
| Revoked permission still works | Former recipient retains access | Active permission queries require `revoked_at IS NULL` |
| Inactive document access | Exposure or modification | Access helpers reject non-`ACTIVE` status; keep endpoint checks consistent |
| File tampering or corruption | Altered file delivered | SHA-256 verification during download |
| Public file exposure | Direct unauthorized downloads | Private Supabase bucket and backend-mediated access |
| Credential leakage | Database or storage compromise | Keep secrets in server environment variables; never commit them |
| Audit-log tampering | Loss of accountability | Database triggers protect audit events against UPDATE, DELETE, and TRUNCATE |
| Unsafe uploads | Malicious or unsupported content stored | Validate file type, extension, size, and file signature |
| Data loss | Outage or permanent loss | Verified database backups and separate storage-object backups |
| Upload resource exhaustion | Service degradation | Enforce upload-size limits and monitor resource use |

## Security assumptions to verify
- Production HTTPS is enabled.
- The Supabase document bucket is private.
- Supabase service-role credentials exist only on the backend.
- Production secrets are not committed to the repository.
- Document access is mediated by authenticated backend endpoints.

## Residual risks and follow-up
- Review dependencies and vulnerabilities periodically.
- Consider rate limiting and monitoring for authentication and upload endpoints.
- Test detail, download, version, and permission endpoints whenever lifecycle rules change.
- Test administrator, owner, reader, editor, revoked-user, and anonymous identities.
- Back up Supabase Storage independently from PostgreSQL.
- Review retention and recovery procedures before physically deleting documents.
- Conduct a security review or penetration test before handling highly sensitive production data.

## Incident response basics
If a credential may have leaked:
1. Rotate the affected credential.
2. Update hosting-provider secret variables and redeploy.
3. Review authentication, database, storage, and audit activity.
4. Preserve relevant logs and backups during investigation.
