# Trustify — Daily Development Log

This log records the major implementation, testing, deployment, and verification milestones shared during the Trustify project. Dates and results below reflect the project work documented for this submission.

## 8 November 2026 — Database and storage migration

- Prepared a PostgreSQL custom-format backup of the original Trustify database.
- Restored the database into the new Supabase PostgreSQL project.
- Verified key application record counts after restoration:
  - Users: 7 at the original migration checkpoint.
  - Documents: 5.
  - Document versions: 6.
  - Document permissions: 7.
  - Audit events: 71.
- Verified the restored audit chain using the application's audit verification service.
- Migrated six existing private document objects to the new Supabase Storage bucket.
- Downloaded the migrated objects and compared SHA-256 hashes against the original files; all six matched.
- Confirmed the Supabase bucket was private.

## 9 November 2026 — Private storage integration and deployment verification

- Integrated the Django document storage adapter with Supabase Storage.
- Added the pinned `supabase` Python dependency.
- Configured the backend to use the Supabase project URL, private service-role credential, and private bucket through environment variables.
- Added proxy HTTPS awareness to Django security settings.
- Ran backend document tests and frontend production builds during integration.
- Confirmed that newly uploaded documents could be downloaded through the deployed application.
- Investigated older documents that remained in the database but were unavailable in the new storage bucket. The likely cause was that some older uploads had been stored on the previous service filesystem and had not been migrated.
- Created a fresh production PostgreSQL custom-format backup:
  - File: `trustify_production_2026-11-09.dump`
  - Size reported by PowerShell: 391,564 bytes.
  - Archive inspection reported 584 table-of-contents entries.
  - Confirmed the archive included document, version, permission, user, and audit-event tables and data, plus audit immutability triggers.
- Inspected production foreign-key relationships and confirmed audit events reference document records with `NO ACTION`; physical deletion therefore requires special care.
- Inspected the existing `status` and `deleted_at` fields and the application’s active-document filtering.
- Implemented access-helper changes so inactive documents are rejected before platform-administrator access is granted.
- Added four regression tests covering administrator and owner/reader access to deleted documents.
- Ran the full document test suite using the existing local test database:
  - 41 tests discovered.
  - 41 tests passed.
- Built the React/Vite frontend successfully.
- Committed and pushed the access-control change:
  - Commit: `11e9293`
  - Message: `Harden deleted document access controls`
- Verified the deployed application’s guest login, document viewing, and permitted document download manually.
- Deferred the requested production document reset to avoid a risky destructive operation before submission. No production document records were cleared during this work.

## Submission verification snapshot

| Check | Result |
|---|---|
| Backend document tests | 41/41 passed |
| Frontend production build | Passed |
| Git commit and push | `11e9293` pushed to `main` |
| Administrator workflow | Previously verified working |
| Guest login | Manually verified working |
| Guest document viewing | Manually verified working |
| Guest permitted download | Manually verified working |
| New document upload/download | Manually verified working |
| Production document reset | Deferred; not performed |

## Follow-up items

- Confirm the Render backend deployment is Live on commit `11e9293`.
- Confirm the frontend is serving the intended production build.
- If clearing existing documents remains required, plan it separately:
  - Preserve users and immutable audit events.
  - Respect foreign-key relationships.
  - Decide whether soft deletion is sufficient.
  - Back up private Supabase Storage objects separately from the database.
  - Do not disable audit immutability triggers to force deletion.
- Keep database dumps, environment files, credentials, and private keys out of Git.
