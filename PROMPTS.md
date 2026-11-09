# Trustify — AI and Development Prompts

Reusable prompts for developers and AI coding assistants working on Trustify. These prompts are guidance only; they do not replace code review, tests, or security review.

## 1. Understand the codebase

> Review the Trustify repository and explain the frontend, backend, database, authentication, document storage, permissions, versioning, and audit-log flows. Base conclusions on source code. Clearly identify anything that cannot be verified.

## 2. Implement a backend feature

> Inspect the relevant Django models, serializers, views, access-control helpers, URL routes, and tests before changing code. Propose the smallest safe change. Preserve existing API behaviour unless a change is explicitly requested. Add regression tests and run Django checks and relevant tests.

## 3. Review document authorization

> Audit every API endpoint that reads, downloads, edits, versions, archives, deletes, or shares a document. Check authentication, ownership, active permissions, revoked permissions, document status, and administrator behaviour. Add tests for administrator, owner, reader, editor, revoked user, and anonymous user.

## 4. Review upload and download security

> Inspect file validation, size limits, MIME handling, storage-key generation, private Supabase Storage access, checksum verification, download headers, and error handling. Do not expose storage credentials or public object URLs. Test invalid files, missing objects, checksum mismatch, and unauthorized downloads.

## 5. Review audit-log integrity

> Trace how audit events are created and protected. Inspect database constraints and triggers. Do not disable immutability protections or modify historical audit events to make another operation easier. Explain foreign-key and retention implications before proposing destructive changes.

## 6. Prepare a deployment

> Review the exact Git diff, configuration changes, dependencies, migrations, environment-variable requirements, and tests. Identify secrets or generated files that must not be committed. Do not commit, push, or deploy without explicit approval. Provide a rollback plan and post-deployment smoke tests.

## 7. Review a production database operation

> Treat this as a production operation. Start with read-only inspection and a verified backup. Identify foreign keys, triggers, cascading behaviour, storage-object dependencies, and audit implications. Do not execute DELETE, TRUNCATE, DROP, or schema changes until the impact and recovery plan have been reviewed and explicitly approved.

## Working rules
- Never invent repository behaviour; inspect the code.
- Never request or commit passwords, API keys, or service-role keys.
- Prefer minimal, testable changes.
- Preserve audit history and private storage.
- Use a dedicated test database, never production.
- Report test failures honestly; do not describe an unrun test as passing.
