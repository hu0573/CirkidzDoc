# Backend API Usage Guide

This document describes the public endpoints exposed by the FastAPI backend, including sample requests and notes for frontend or third-party integrations.

## Basic Information
- Service base URL: `http://<host>:<port>`
- OpenAPI documentation: `/docs` (Swagger UI), `/redoc`
- All endpoints return JSON except for the file download endpoint.

## Authentication
Authentication is currently disabled because the service runs as an internal MVP. Add a unified Token/Session mechanism at the API layer when security becomes necessary.

## Endpoints

### 1. List Templates
- **Endpoint**: `GET /api/templates`
- **Description**: Return summary information for all available templates.
- **Response Example**
```json
[
  {
    "id": "example_contract",
    "name": "Sample Contract",
    "description": "Basic contract template",
    "entry": "template.docx",
    "field_count": 4
  }
]
```

### 2. Get Template Detail
- **Endpoint**: `GET /api/templates/{template_id}`
- **Description**: Return the full metadata of the specified template. Metadata now only contains the template identity, entry file, description, and a simplified `fields` collection (`name` + `type`).
- **Response Example**
```json
{
  "template": {
    "id": "example_contract",
    "name": "Sample Contract",
    "description": "Basic contract template",
    "entry": "template.docx",
    "fields": [
      { "name": "party_a_name", "type": "string" },
      { "name": "party_b_name", "type": "string" },
      { "name": "sign_date", "type": "date" }
    ]
  }
}
```

### 3. Upload Template
- **Endpoint**: `POST /api/templates/upload`
- **Description**: Accept a DOCX template upload, create a new template directory, and generate a starter `metadata.json` by scanning `{{placeholder}}` variables.
- **Request**: `multipart/form-data` with a single `file` field (`.docx`, ≤ 20 MB).
- **Response Example**
```json
{
  "template": {
    "id": "partner-contract",
    "name": "Partner Contract",
    "description": "",
    "entry": "Partner Contract.docx",
    "fields": [
      { "name": "client_name", "type": "string" },
      { "name": "sign_date", "type": "string" }
    ]
  },
  "metadata_path": "partner-contract/metadata.json",
  "message": "Template created. Update the generated metadata.json to confirm field types."
}
```
- **Notes**
  - Template IDs are derived from the filename (kebab-case). If a directory already exists, a numeric suffix is appended automatically.
  - All extracted fields default to type `string`; adjust the generated `metadata.json` if you require other types (such as `date` or `number`).
  - Newly uploaded templates automatically expose the full set of system-supported output formats—no additional `options` configuration is required.

### 4. Query Supported Output Formats
- **Endpoint**: `GET /api/formats`
- **Description**: List the output formats supported by the DOCX conversion pipeline and the available advanced PDF options.
- **Response Example**
```json
{
  "formats": [
    { "id": "docx", "label": "DOCX", "description": "Available export format for DOCX templates" },
    { "id": "html", "label": "HTML", "description": "Available export format for DOCX templates" }
  ],
  "advanced_options": {
    "pdf": {
      "allow_flatten": true,
      "allow_pdfa": true,
      "allow_password": true,
      "description": "PDF rendering supports flattening, PDF/A compliance, and password protection"
    }
  }
}
```

### 5. Submit a Render Task
- **Endpoint**: `POST /api/templates/render`
- **Status Code**: `202 Accepted`
- **Description**: Create an asynchronous render task; the backend processes it and stores the results in the database.
- **Request Body**
```json
{
  "template_id": "example_contract",
  "data": {
    "party_a_name": "Alpha Tech",
    "party_b_name": "Beta Partner",
    "sign_date": "2025-11-11"
  },
  "formats": ["docx", "pdf"],
  "options": {
    "pdf": {
      "flatten": true,
      "password": "Secret123"
    }
  }
}
```
- **Response Body**
```json
{
  "task_id": "4df5c4a0f5f34e64af3f2b6f1a4e2c51",
  "status": "queued",
  "expires_at": "2025-11-11T14:30:00Z"
}
```
- **Error Codes**
  - `404`: Template does not exist.
  - `422`: Request validation failed.

### 6. Get Task Status
- **Endpoint**: `GET /api/templates/tasks/{task_id}`
- **Description**: Return the task status, progress, and list of generated results.
- **Response Example**
```json
{
  "task_id": "4df5c4a0f5f34e64af3f2b6f1a4e2c51",
  "status": "succeeded",
  "progress": 100,
  "error": null,
  "results": [
    {
      "format": "docx",
      "download_url": "/api/templates/tasks/4df5c4a0f5f34e64af3f2b6f1a4e2c51/files/docx?token=af2db4f5...",
      "file_size": 143256,
      "checksum": "8f5d3d...",
      "expires_at": "2025-11-11T15:30:00Z"
    }
  ]
}
```
- **Status Values**
  - `queued`: Waiting in the queue.
  - `processing`: Rendering or converting files.
  - `succeeded`: All results generated successfully.
  - `failed`: Task failed, and `error` contains the reason.

### 7. Download Task Result
- **Endpoint**: `GET /api/templates/tasks/{task_id}/files/{format}?token=<download_token>`
- **Description**: Download a generated file by providing the task ID, desired format, and download token.
- **Response**: Binary stream with the default media type `application/octet-stream`.
- **Error Codes**
  - `404`: Task not found, token invalid, or file expired.

## Task Lifecycle & Cleanup
- Task expiration is controlled by `BACKEND_TASK_EXPIRY_MINUTES` (60 minutes by default).
- Expired tasks and their associated files are cleaned up automatically when new tasks are created.
- Result files are stored under `results/<task_id>/`. Override `BACKEND_RESULTS_ROOT_RELATIVE` to change the location.

## Database Storage
- SQLite is used by default (`BackEnd/data/backend.db`). Set `BACKEND_DATABASE_URL` to switch to PostgreSQL or another database.
- The service creates three tables (`templates`, `tasks`, `task_results`) on first start-up.

## Debugging Tips
- Visit `/docs` after start-up to verify the OpenAPI definition.
- Run `uv run pytest` to execute the built-in tests and ensure the rendering/conversion pipeline works as expected.
- If external dependencies are missing, implement `/health/deps` (TBD) or inspect the logs to identify failing commands.


