# Trustify

Trustify is a secure document-management application built with a Django REST backend and a React frontend. It supports authenticated document access, per-document permissions, version history, private file storage, and audit logging.

## Features
- Authenticated user access.
- Document upload and download through protected backend APIs.
- Document ownership and `READ` / `EDIT` permissions.
- Permission revocation.
- Document version history.
- Private Supabase Storage integration.
- SHA-256 checksum verification during downloads.
- Audit-event recording with database-level protections against mutation and truncation.

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React, JavaScript, Vite |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL |
| File storage | Private Supabase Storage bucket |
| Deployment | Render |

## Repository layout

```text
Trustify/
├── backend/
│   ├── config/
│   ├── documents/
│   ├── auditlog/
│   └── requirements.txt
├── frontend/
├── README.md
├── PERMISSIONS.md
├── THREATS.md
└── PROMPTS.md
```

Additional application files and Django apps may exist.

## Local development

### Requirements
- Python compatible with backend dependencies
- PostgreSQL
- Node.js and npm
- Supabase project and private storage bucket for storage-backed operations

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Configure the required environment variables before starting the backend. Production configuration includes Django secret/debug/host settings, database settings, CORS/CSRF origins, and Supabase URL, service-role key, and bucket name.

### Frontend

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` to the backend API base URL for the environment.

### Production build and checks

```powershell
cd frontend
npm run build
```

```powershell
cd backend
python manage.py check
python manage.py test documents
```

Use a dedicated test database. Never point automated tests at production.

## Storage and security
Uploaded files are stored in a private Supabase Storage bucket. The backend mediates access and verifies SHA-256 checksums during downloads. Do not make the bucket public or expose the Supabase service-role key to the frontend.

Never commit `.env` files, database passwords, Django secret keys, or Supabase service-role keys. Configure secrets through local environment variables and the hosting provider's secret settings.

## Deployment and operations
- Use HTTPS and restrict allowed hosts and CORS/CSRF origins.
- Back up the PostgreSQL database before destructive operations.
- Back up Supabase Storage objects separately; a database dump does not contain binary storage objects.
- Preserve audit history and immutability protections.
- Verify administrator and non-administrator workflows after deployment.
