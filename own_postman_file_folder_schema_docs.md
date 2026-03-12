## Folder Table Schema

Represents folders that can contain files or other folders within Collections.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / PK | Primary key |
| workspace_id | UUID / FK -> Workspaces.id | Owning workspace |
| parent_folder_id | UUID / FK -> Folder.id | Parent folder (null if top-level) |
| name | VARCHAR(100) | Folder name |
| description | TEXT | Optional folder description or auth scripts |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |

---

## File Table Schema

Represents API request files within folders.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID / PK | Primary key |
| folder_id | UUID / FK -> Folder.id | Parent folder |
| name | VARCHAR(100) | File (API request) name |
| api_request_id | UUID / FK -> API Requests.id | Link to API request details |
| description | TEXT | Optional file description |
| created_at | TIMESTAMP | Default now() |
| updated_at | TIMESTAMP | Auto-updated on change |

**Notes:**
- Folders can have child folders.
- Files are linked to API Requests table via `api_request_id`.
- CRUD operations can be applied separately to folders and files.