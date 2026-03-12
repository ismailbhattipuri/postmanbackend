## Own Postman Backend Schemas Documentation

This document defines the database schemas for Own Postman, integrating the **Folder** and **File** structure into **Collections**.

---

### 1. Users Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / BIGINT PK | Primary key |
| username | VARCHAR(50) | Unique, required |
| email | VARCHAR(100) | Unique, required |
| password_hash | VARCHAR(255) | Required |
| role | ENUM(user, admin) | Role-based access control |
| last_online | TIMESTAMP | Updated via WebSocket ping |
| last_activity | TIMESTAMP | Updated on any action |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |

---

### 2. Workspaces Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / BIGINT PK | Primary key |
| name | VARCHAR(100) | Workspace name |
| owner_id | UUID / FK -> Users.id | Workspace owner |
| type | ENUM(personal, organisation) | Type of workspace |
| online_users | JSON / Redis | Online users list; optional |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |

---

### 3. Collections Table (Folders & Files Integrated)

Collections now support **folders and files** in a hierarchical structure.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / PK | Primary key |
| workspace_id | UUID / FK -> Workspaces.id | Owning workspace |
| parent_id | UUID / FK -> Collections.id | Parent folder (null if top-level) |
| name | VARCHAR(100) | Folder or file name |
| type | ENUM(folder, file) | 'folder' for folder, 'file' for API request |
| api_request_id | UUID / FK -> API Requests.id | Set if type='file' |
| description | TEXT | Folder or file description, optional per folder (like auth scripts) |
| shared | BOOLEAN | Is collection/folder shared in workspace |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |
| metadata | JSON | Optional extra info (tags, version) |

**Example Hierarchy:**
```
collection/
  users/ (folder)
    get_user_api (file, api_request_id=<UUID>)
    update_user (file, api_request_id=<UUID>)
    delete_user (file, api_request_id=<UUID>)
  auth/ (folder)
    login (file, api_request_id=<UUID>)
    register (file, api_request_id=<UUID>)
```
- Folders can contain child folders or files.
- Files link directly to `API Requests` using `api_request_id`.
- Folder-level `description` or scripts apply to all child files.
- CRUD operations are applied on this table for both folders and files.

---

### 4. API Requests Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / PK | Primary key |
| name | VARCHAR(100) | Request name |
| method | ENUM(GET, POST, PUT, DELETE, PATCH) | HTTP method |
| url | TEXT | Request URL |
| headers | JSON | Optional headers |
| body | JSON / TEXT | Request body |
| auth | JSON | Authentication info |
| script | JSON / TEXT | Pre/post request script |
| doc | JSON / TEXT | Auto-generated doc for preview/export |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |
| last_run_at | TIMESTAMP | Optional last execution time |
| last_run_result | JSON | Optional last execution output |

---

### 5. Environment Variables Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / PK | Primary key |
| workspace_id | UUID / FK -> Workspaces.id | Workspace-scoped environment |
| name | VARCHAR(50) | Variable name |
| value | TEXT | Variable value |
| type | ENUM(string, secret, number, bool) | Optional type hint |
| desc | TEXT | Description for the variable |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |

---

### 6. Plugins Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / PK | Primary key |
| workspace_id | UUID / FK -> Workspaces.id | Optional scoping |
| name | VARCHAR(100) | Plugin name |
| module_path | VARCHAR(255) | Python import path |
| enabled | BOOLEAN | True/False |
| config | JSON | Plugin configuration |
| desc | TEXT | Plugin description for display |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |

---

### Notes
- The **Collections table now integrates folders and files**, eliminating the need for separate Folder/File tables.
- Each file links to the API Requests table via `api_request_id`.
- Folder-level scripts and descriptions apply to all contained files.
- Full CRUD operations (create, read, update, delete, move) apply to both folders and files using `parent_id` and `type`.

