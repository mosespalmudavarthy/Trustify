# Trustify Permissions

## Purpose
This document describes Trustify's application-level document access rules for reviewers and maintainers.

## Roles
- **Platform administrator:** Django superuser with platform-wide access, subject to inactive-document restrictions in the access-control helpers.
- **Document owner:** User recorded as the document owner.
- **Reader:** User with an active `READ` permission.
- **Editor:** User with an active `EDIT` permission.
- **Unauthenticated visitor:** Cannot access protected document APIs.

## Permission summary

| Action | Administrator | Owner | Reader | Editor |
|---|---:|---:|---:|---:|
| View active document | Yes | Yes | Yes | Yes |
| Download active document | Yes, subject to endpoint checks | Yes | Yes | Yes |
| Edit active document | Yes | Yes | No | Yes |
| Manage permissions | Yes | Yes | No | No |
| View archived/deleted document | No, through access helpers | No | No | No |
| Upload a new version | Subject to endpoint checks | Yes | No | Yes |

Individual API endpoints may impose additional validation.

## Permission lifecycle
- Permissions belong to a specific document and user.
- A permission is active when `revoked_at` is `NULL`.
- Revoked permissions do not grant access.
- The access-control helpers recognize `READ` and `EDIT`.
- Viewing and editing require document status `ACTIVE`.
- `ARCHIVED` and `DELETED` documents are rejected by the access-control helpers.

## Security practices
- Enforce authorization on the backend; frontend visibility is not a security boundary.
- Keep the Supabase Storage bucket private.
- Keep service-role credentials on the server only.
- Verify file integrity during downloads.
- Record relevant actions through the audit logging service.
- Preserve audit history and database immutability protections.

## When changing permissions
1. Check authentication, ownership, permission level, revocation state, and document status.
2. Test administrator, owner, reader, editor, revoked-user, and anonymous cases.
3. Inspect foreign keys and audit implications before destructive database operations.
