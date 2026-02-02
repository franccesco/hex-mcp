# hex-mcp MCP server
[![smithery badge](https://smithery.ai/badge/@franccesco/hex-mcp)](https://smithery.ai/server/@franccesco/hex-mcp)

A MCP server for Hex that implements orchestration, monitoring, cell content access, permission management, collection organization, and group management tools.

## What This Does (And Doesn't Do)

### Practical Use Cases

**Orchestration and Automation**:
- Trigger Hex project runs from external systems (Airflow DAGs, CI/CD pipelines)
- Monitor run status programmatically
- Cancel long-running or stuck executions
- Discover and search projects across workspaces

**Operational Monitoring**:
- Check if scheduled runs completed successfully
- Get run history for auditing
- Programmatic access to project metadata (owner, last edited, description)

**Cell Content Access** (NEW):
- Read notebook structure and cell metadata
- Read SQL query source code from SQL cells
- Read Python/R code from CODE cells
- Good for query migration, code analysis, and content auditing

**Permission Management** (NEW):
- Programmatically manage user and group access to projects
- Bulk update permissions across multiple projects
- Manage workspace-wide and public access settings
- Add or remove projects from collections

**Collection Organization** (NEW):
- Create and manage collections for organizing projects
- Organize projects by department, team, or topic
- Control collection visibility and access
- Bulk organize projects into collections

**Group Management** (NEW):
- Create and manage user groups for permission management
- Add and remove users from groups in bulk
- Use groups to simplify permission management across projects
- Maintain organized team structures

**Data Connection Management** (NEW):
- List and manage database and warehouse connections
- Create connections for BigQuery, Snowflake, Postgres, Redshift, Athena, Databricks
- Update connection configurations and credentials
- Control data connection sharing across workspace

### Critical Limitations

**Limited notebook content access**:
- ✅ Can read SQL and CODE cell source content
- ❌ Cannot read MARKDOWN, INPUT, or visualization cells
- ❌ Cannot create or delete cells
- ❌ Cannot modify notebook structure
- ❌ Cannot view query results or charts
- ❌ Cannot manage notebook dependencies or parameters

**Not suitable for**:
- Building or authoring notebooks from scratch
- Collaborative notebook development
- Debugging queries or code execution
- Full notebook backup (only SQL/CODE cells accessible)
- Reading markdown documentation or input parameters

### When to Use This

Use hex-mcp when you need to:
- **Orchestrate** Hex executions from external systems
- **Monitor** run status and history
- **Read** SQL queries and code from existing notebooks
- **Audit** or **migrate** SQL/CODE content across projects
- **Manage** permissions and access control across projects
- **Automate** bulk permission updates for users, groups, and collections
- **Organize** projects into collections by department, team, or topic
- **Maintain** user groups for simplified permission management
- **Standardize** workspace organization across your Hex instance
- **Manage** data connections and database integrations programmatically
- **Automate** connection setup for new workspaces or environments

For full notebook development and editing, use the Hex web UI directly.

## Available Tools

### Project Operations
- `list_hex_projects`: Lists available Hex projects
- `search_hex_projects`: Search for Hex projects by pattern
- `get_hex_project`: Get detailed information about a specific project

### Project Execution
- `run_hex_project`: Execute a Hex project
- `get_hex_run_status`: Check the status of a project run
- `get_hex_project_runs`: Get the history of project runs
- `cancel_hex_run`: Cancel a running project

### Cell Operations (NEW)
- `list_hex_cells`: List all cells in a project with source code for SQL/CODE cells
- `update_hex_cell`: Update SQL or CODE cell source and/or data connection

### Permission Management (NEW)
- `update_hex_project_user_sharing`: Grant or revoke user access to projects
- `update_hex_project_group_sharing`: Grant or revoke group access to projects
- `update_hex_project_collection_sharing`: Add or remove projects from collections
- `update_hex_project_workspace_sharing`: Update workspace-wide and public access

### Collection Management (NEW)
- `list_hex_collections`: List all collections in the workspace
- `get_hex_collection`: Get detailed information about a specific collection
- `create_hex_collection`: Create a new collection with optional sharing settings
- `update_hex_collection`: Update collection name, description, or sharing settings

### Group Management (NEW)
- `list_hex_groups`: List all groups in the workspace
- `get_hex_group`: Get detailed information about a specific group
- `create_hex_group`: Create a new group with optional initial members
- `update_hex_group`: Update group name and/or membership (add/remove users)
- `delete_hex_group`: Delete a group from the workspace

### Data Connection Management (NEW)
- `list_hex_data_connections`: List all data connections in the workspace
- `get_hex_data_connection`: Get detailed information about a specific data connection
- `create_hex_data_connection`: Create a new database/warehouse connection
- `update_hex_data_connection`: Update connection configuration, credentials, or sharing

## Installation

### Installing via Smithery

To install Hex MCP Server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@franccesco/hex-mcp):

```bash
npx -y @smithery/cli install @franccesco/hex-mcp --client claude
```

### Installing Manually
Using uv is the recommended way to install hex-mcp:

```bash
uv add hex-mcp
```

Or using pip:

```bash
pip install hex-mcp
```

To confirm it's working, you can run:

```bash
hex-mcp --version
```

## Configuration

### Using the config command (recommended)

The easiest way to configure hex-mcp is by using the `config` command and passing your API key and API URL (optional and defaults to `https://app.hex.tech/api/v1`):

```bash
hex-mcp config --api-key "your_hex_api_key" --api-url "https://app.hex.tech/api/v1"
```

> [!NOTE]
> This saves your configuration to a file in your home directory (e.g. `~/.hex-mcp/config.yml`), making it available for all hex-mcp invocations.

### Using environment variables

Alternatively, the Hex MCP server can be configured with environment variables:

- `HEX_API_KEY`: Your Hex API key
- `HEX_API_URL`: The Hex API base URL

When setting up environment variables for MCP servers they need to be either global for Cursor to pick them up or make use of uv's `--env-file` flag when invoking the server.

## Using with Cursor

Cursor allows AI agents to interact with Hex via the MCP protocol. Follow these steps to set up and use hex-mcp with Cursor. You can create a `.cursor/mcp.json` file in your project root with the following content:

```json
{
  "mcpServers": {
    "hex-mcp": {
      "command": "uv",
      "args": ["run", "hex-mcp", "run"]
    }
  }
}
```

Alternatively, you can use the `hex-mcp` command directly if it's in your PATH:

```json
{
  "mcpServers": {
    "hex-mcp": {
      "command": "hex-mcp",
      "args": ["run"]
    }
  }
}
```

Once it's up and running, you can use it in Cursor by initiating a new AI (Agent) conversation and ask it to list or run a Hex project.

> [!IMPORTANT]
> The MCP server and CLI is still in development and subject to breaking changes.

## Usage Examples

### Reading Cell Content

Use `list_hex_cells` to read the structure and source code of a Hex notebook:

```python
# List all cells in a project
cells = list_hex_cells(project_id="your-project-uuid")

# The response includes cell metadata and source code for SQL/CODE cells
# Example response structure:
{
    "values": [
        {
            "id": "cell-uuid-123",
            "staticId": "static-id-456",
            "cellType": "SQL",
            "label": "Load Customer Data",
            "dataConnectionId": "connection-uuid-789",
            "contents": {
                "sqlCell": {
                    "source": "SELECT * FROM customers WHERE active = true"
                },
                "codeCell": null
            }
        },
        {
            "id": "cell-uuid-456",
            "cellType": "CODE",
            "label": "Process Data",
            "dataConnectionId": null,
            "contents": {
                "sqlCell": null,
                "codeCell": {
                    "source": "import pandas as pd\ndf = df.dropna()"
                }
            }
        },
        {
            "id": "cell-uuid-789",
            "cellType": "MARKDOWN",
            "label": "Documentation",
            "dataConnectionId": null,
            "contents": {
                "sqlCell": null,
                "codeCell": null
            }
        }
    ],
    "pagination": {
        "next": null,
        "previous": null
    }
}
```

**Note**: Only SQL and CODE cells include source content. MARKDOWN, INPUT, and visualization cells return null for both `sqlCell` and `codeCell`.

### Pagination

For projects with many cells, use pagination:

```python
# First page
page1 = list_hex_cells(project_id="your-project-uuid", limit=50)

# Next page using cursor
if page1["pagination"]["next"]:
    page2 = list_hex_cells(
        project_id="your-project-uuid",
        limit=50,
        after=page1["pagination"]["next"]
    )

# Previous page
if page2["pagination"]["previous"]:
    page1_again = list_hex_cells(
        project_id="your-project-uuid",
        limit=50,
        before=page2["pagination"]["previous"]
    )
```

### Updating Cell Content

Update SQL or CODE cells programmatically:

```python
# Update SQL cell source code
result = update_hex_cell(
    cell_id="cell-uuid-123",
    sql_source="SELECT * FROM updated_table WHERE active = true"
)

# Update CODE cell source code
result = update_hex_cell(
    cell_id="cell-uuid-456",
    code_source="import pandas as pd\ndf = df.dropna()"
)

# Update SQL cell data connection (without changing source)
result = update_hex_cell(
    cell_id="cell-uuid-123",
    data_connection_id="new-connection-uuid"
)

# Update both SQL source and connection in one call
result = update_hex_cell(
    cell_id="cell-uuid-123",
    sql_source="SELECT * FROM production.customers",
    data_connection_id="production-connection-uuid"
)
```

**Important**:
- Can only update SQL and CODE cell types
- Cannot update MARKDOWN, INPUT, or visualization cells
- Requires `EDIT_PROJECT_CONTENTS` permission
- Cannot update both `sql_source` and `code_source` in same call (cells are either SQL or CODE)

### Query Migration Example

Extract and update SQL queries across projects:

```python
import json

# Get all cells from source project
cells_response = list_hex_cells(project_id="source-project-uuid")
cells = json.loads(cells_response)

# Filter for SQL cells
sql_cells = [
    cell for cell in cells["values"]
    if cell["cellType"] == "SQL" and cell["contents"]["sqlCell"]
]

# Migrate queries to new data connection
new_connection_id = "production-bigquery-connection"

for cell in sql_cells:
    original_query = cell["contents"]["sqlCell"]["source"]

    # Update table references (example: dev -> prod)
    updated_query = original_query.replace("dev.schema", "prod.schema")

    # Update the cell with new query and connection
    result = update_hex_cell(
        cell_id=cell["id"],
        sql_source=updated_query,
        data_connection_id=new_connection_id
    )

    print(f"Updated cell: {cell['label']}")

print(f"Migrated {len(sql_cells)} SQL cells to production")
```

### Code Refactoring Example

Bulk update Python code across multiple cells:

```python
import json

# Get all CODE cells
cells_response = list_hex_cells(project_id="project-uuid")
cells = json.loads(cells_response)

code_cells = [
    cell for cell in cells["values"]
    if cell["cellType"] == "CODE" and cell["contents"]["codeCell"]
]

# Update import statements
for cell in code_cells:
    original_code = cell["contents"]["codeCell"]["source"]

    # Replace deprecated import
    if "from old_library" in original_code:
        updated_code = original_code.replace(
            "from old_library import func",
            "from new_library import func"
        )

        # Update the cell
        result = update_hex_cell(
            cell_id=cell["id"],
            code_source=updated_code
        )

        print(f"Updated cell: {cell['label']}")
```

### Managing Project Permissions

Control access to Hex projects programmatically using the sharing endpoints.

#### Grant User Access

```python
from hex_mcp.server import update_hex_project_user_sharing

# Grant edit access to a single user
result = update_hex_project_user_sharing(
    project_id="project-123",
    user_permissions=[
        {"user_id": "user-456", "access": "CAN_EDIT"}
    ]
)

# Grant access to multiple users with different permissions
result = update_hex_project_user_sharing(
    project_id="project-123",
    user_permissions=[
        {"user_id": "user-001", "access": "CAN_VIEW"},
        {"user_id": "user-002", "access": "CAN_EDIT"},
        {"user_id": "user-003", "access": "FULL_ACCESS"}
    ]
)

# Revoke user access
result = update_hex_project_user_sharing(
    project_id="project-123",
    user_permissions=[
        {"user_id": "user-456", "access": "NONE"}
    ]
)
```

**Access Levels**:
- `NONE`: Revoke all access
- `APP_ONLY`: Access only within apps (published versions)
- `CAN_VIEW`: View project in logic view (read-only)
- `CAN_EDIT`: Edit project contents
- `FULL_ACCESS`: Edit contents and manage project settings/permissions

#### Grant Group Access

```python
from hex_mcp.server import update_hex_project_group_sharing

# Grant access to a group
result = update_hex_project_group_sharing(
    project_id="project-123",
    group_permissions=[
        {"group_id": "group-789", "access": "CAN_VIEW"}
    ]
)

# Grant access to multiple groups
result = update_hex_project_group_sharing(
    project_id="project-123",
    group_permissions=[
        {"group_id": "analytics-team", "access": "CAN_EDIT"},
        {"group_id": "leadership-team", "access": "CAN_VIEW"}
    ]
)
```

#### Add Projects to Collections

```python
from hex_mcp.server import update_hex_project_collection_sharing

# Add project to a collection
result = update_hex_project_collection_sharing(
    project_id="project-123",
    collection_permissions=[
        {"collection_id": "collection-456", "access": "CAN_VIEW"}
    ]
)

# Add to multiple collections with different access levels
result = update_hex_project_collection_sharing(
    project_id="project-123",
    collection_permissions=[
        {"collection_id": "public-dashboards", "access": "APP_ONLY"},
        {"collection_id": "internal-analytics", "access": "CAN_EDIT"}
    ]
)

# Remove from collection
result = update_hex_project_collection_sharing(
    project_id="project-123",
    collection_permissions=[
        {"collection_id": "collection-456", "access": "NONE"}
    ]
)
```

#### Manage Workspace and Public Access

```python
from hex_mcp.server import update_hex_project_workspace_sharing

# Make project viewable by entire workspace
result = update_hex_project_workspace_sharing(
    project_id="project-123",
    workspace_access="CAN_VIEW"
)

# Make project publicly accessible
result = update_hex_project_workspace_sharing(
    project_id="project-123",
    public_access="APP_ONLY"
)

# Update both workspace and public access
result = update_hex_project_workspace_sharing(
    project_id="project-123",
    workspace_access="CAN_EDIT",
    public_access="APP_ONLY"
)

# Revoke public access (keep workspace access)
result = update_hex_project_workspace_sharing(
    project_id="project-123",
    public_access="NONE"
)
```

#### Bulk Permission Management Example

Standardize permissions across multiple projects:

```python
import json
from hex_mcp.server import (
    list_hex_projects,
    update_hex_project_user_sharing,
    update_hex_project_workspace_sharing
)

# Get all projects
projects_response = list_hex_projects()
projects = json.loads(projects_response)

# Define standard access policies
analytics_team_users = ["user-001", "user-002", "user-003"]
leadership_users = ["user-100", "user-101"]

for project in projects:
    project_id = project["projectId"]

    # Grant analytics team edit access
    update_hex_project_user_sharing(
        project_id=project_id,
        user_permissions=[
            {"user_id": user_id, "access": "CAN_EDIT"}
            for user_id in analytics_team_users
        ]
    )

    # Grant leadership view access
    update_hex_project_user_sharing(
        project_id=project_id,
        user_permissions=[
            {"user_id": user_id, "access": "CAN_VIEW"}
            for user_id in leadership_users
        ]
    )

    # Make viewable by workspace, not public
    update_hex_project_workspace_sharing(
        project_id=project_id,
        workspace_access="CAN_VIEW",
        public_access="NONE"
    )

    print(f"Updated permissions for: {project['name']}")
```

**Important Notes**:
- All sharing operations require appropriate workspace permissions
- User/group IDs must exist in your Hex workspace
- Collection IDs must be valid collections you have access to
- Workspace access applies to all workspace members
- Public access (`publicWeb`) allows anyone with the link to access

### Managing Collections

Organize projects into collections for better workspace organization.

#### List Collections

```python
from hex_mcp.server import list_hex_collections
import json

# List all collections
collections = list_hex_collections()
data = json.loads(collections)

for collection in data["values"]:
    print(f"{collection['name']}: {collection['id']}")
    print(f"  Created by: {collection.get('creator', {}).get('email', 'N/A')}")

# List with pagination
page1 = list_hex_collections(limit=10)
data = json.loads(page1)

if data["pagination"]["next"]:
    page2 = list_hex_collections(limit=10, after=data["pagination"]["next"])
```

#### Get Collection Details

```python
from hex_mcp.server import get_hex_collection
import json

# Get specific collection
collection = get_hex_collection(collection_id="collection-123")
data = json.loads(collection)

print(f"Collection: {data['name']}")
print(f"Description: {data.get('description', 'No description')}")
print(f"Sharing with {len(data['sharing'].get('users', []))} users")
print(f"Sharing with {len(data['sharing'].get('groups', []))} groups")
```

#### Create Collections

```python
from hex_mcp.server import create_hex_collection
import json

# Create simple collection
collection = create_hex_collection(
    name="Q4 2026 Analytics",
    description="Analytics projects for Q4 2026"
)
data = json.loads(collection)
print(f"Created collection: {data['id']}")

# Create with sharing settings
collection = create_hex_collection(
    name="Executive Dashboards",
    description="Dashboards for executive team",
    sharing_users=[
        {"id": "user-ceo", "access": "CAN_VIEW"},
        {"id": "user-cfo", "access": "CAN_VIEW"}
    ],
    workspace_access="NONE"  # Only specified users can access
)

# Create with group access
collection = create_hex_collection(
    name="Finance Reports",
    description="Financial reporting and analysis",
    sharing_groups=[
        {"id": "finance-team", "access": "CAN_EDIT"}
    ],
    workspace_access="CAN_VIEW"
)
```

#### Update Collections

```python
from hex_mcp.server import update_hex_collection
import json

# Update collection name and description
result = update_hex_collection(
    collection_id="collection-123",
    name="Q1 2027 Analytics",
    description="Updated for Q1 2027"
)

# Update sharing settings
result = update_hex_collection(
    collection_id="collection-123",
    sharing_users=[
        {"id": "user-456", "access": "CAN_EDIT"}
    ],
    workspace_access="CAN_VIEW"
)

# Update multiple fields at once
result = update_hex_collection(
    collection_id="collection-123",
    name="Updated Collection Name",
    description="Updated description",
    sharing_groups=[
        {"id": "analytics-team", "access": "CAN_EDIT"}
    ],
    workspace_access="CAN_VIEW"
)
```

#### Collection Organization Example

Organize all projects by department:

```python
import json
from hex_mcp.server import (
    list_hex_projects,
    list_hex_collections,
    create_hex_collection,
    update_hex_project_collection_sharing
)

# Define department structure
departments = {
    "Engineering": ["user-eng-lead", "group-engineering"],
    "Finance": ["user-fin-lead", "group-finance"],
    "Marketing": ["user-mkt-lead", "group-marketing"]
}

# Create collections for each department
collection_ids = {}
for dept_name, members in departments.items():
    # Create collection
    collection = create_hex_collection(
        name=f"{dept_name} Projects",
        description=f"All {dept_name} department projects",
        workspace_access="CAN_VIEW"
    )
    data = json.loads(collection)
    collection_ids[dept_name] = data["id"]
    print(f"Created collection for {dept_name}: {data['id']}")

# Get all projects
projects = list_hex_projects()
projects_data = json.loads(projects)

# Organize projects into collections based on name patterns
for project in projects_data:
    project_id = project["projectId"]
    project_name = project["name"].lower()

    # Determine which collection(s) this project belongs to
    if "engineering" in project_name or "technical" in project_name:
        update_hex_project_collection_sharing(
            project_id=project_id,
            collection_permissions=[
                {"collection_id": collection_ids["Engineering"], "access": "CAN_EDIT"}
            ]
        )
        print(f"Added '{project['name']}' to Engineering collection")

    elif "finance" in project_name or "revenue" in project_name:
        update_hex_project_collection_sharing(
            project_id=project_id,
            collection_permissions=[
                {"collection_id": collection_ids["Finance"], "access": "CAN_EDIT"}
            ]
        )
        print(f"Added '{project['name']}' to Finance collection")

    elif "marketing" in project_name or "campaign" in project_name:
        update_hex_project_collection_sharing(
            project_id=project_id,
            collection_permissions=[
                {"collection_id": collection_ids["Marketing"], "access": "CAN_EDIT"}
            ]
        )
        print(f"Added '{project['name']}' to Marketing collection")

print("Collection organization complete!")
```

**Collection Management Notes**:
- Collections help organize projects by team, department, or topic
- Collections can have their own sharing settings independent of projects
- A project can belong to multiple collections
- Workspace access on collections controls who can see the collection exists
- Creating collections requires appropriate workspace permissions

### Managing Groups

Organize users into groups for simplified permission management.

#### List Groups

```python
from hex_mcp.server import list_hex_groups
import json

# List all groups
groups = list_hex_groups()
data = json.loads(groups)

for group in data["values"]:
    print(f"{group['name']}: {group['id']}")
    print(f"  Created: {group['createdAt']}")

# List with pagination and sorting
page1 = list_hex_groups(
    limit=10,
    sort_by="name",
    sort_direction="asc"
)
data = json.loads(page1)

if data["pagination"]["next"]:
    page2 = list_hex_groups(limit=10, after=data["pagination"]["next"])
```

#### Get Group Details

```python
from hex_mcp.server import get_hex_group
import json

# Get specific group
group = get_hex_group(group_id="group-123")
data = json.loads(group)

print(f"Group: {data['name']}")
print(f"ID: {data['id']}")
print(f"Created: {data['createdAt']}")
```

#### Create Groups

```python
from hex_mcp.server import create_hex_group
import json

# Create simple group
group = create_hex_group(name="Analytics Team")
data = json.loads(group)
print(f"Created group: {data['id']}")

# Create with initial members
group = create_hex_group(
    name="Finance Team",
    member_user_ids=[
        "user-123",
        "user-456",
        "user-789"
    ]
)
data = json.loads(group)
print(f"Created group with 3 members: {data['id']}")
```

#### Update Groups

```python
from hex_mcp.server import update_hex_group
import json

# Update group name
result = update_hex_group(
    group_id="group-123",
    name="Senior Analytics Team"
)

# Add members to group
result = update_hex_group(
    group_id="group-123",
    add_member_user_ids=["user-new-1", "user-new-2"]
)

# Remove members from group
result = update_hex_group(
    group_id="group-123",
    remove_member_user_ids=["user-old-1"]
)

# Update name and membership together
result = update_hex_group(
    group_id="group-123",
    name="Lead Analytics Team",
    add_member_user_ids=["user-lead"],
    remove_member_user_ids=["user-junior"]
)
```

#### Delete Groups

```python
from hex_mcp.server import delete_hex_group

# Delete a group (does not delete the users, only the group)
result = delete_hex_group(group_id="group-old-team")
print(result)  # "Group deleted successfully"
```

#### Bulk Group Management Example

Create department-based groups and assign users:

```python
import json
from hex_mcp.server import (
    create_hex_group,
    update_hex_group,
    update_hex_project_group_sharing
)

# Define department structure with user lists
departments = {
    "Engineering": {
        "leads": ["user-eng-lead-1", "user-eng-lead-2"],
        "members": ["user-eng-1", "user-eng-2", "user-eng-3"]
    },
    "Data Science": {
        "leads": ["user-ds-lead"],
        "members": ["user-ds-1", "user-ds-2", "user-ds-3", "user-ds-4"]
    },
    "Analytics": {
        "leads": ["user-analytics-lead"],
        "members": ["user-analyst-1", "user-analyst-2"]
    }
}

# Create groups for each department
group_ids = {}
for dept_name, users in departments.items():
    # Create main department group
    all_members = users["leads"] + users["members"]
    group = create_hex_group(
        name=f"{dept_name} Team",
        member_user_ids=all_members
    )
    data = json.loads(group)
    group_ids[dept_name] = data["id"]
    print(f"Created {dept_name} Team: {data['id']} ({len(all_members)} members)")

    # Create leadership sub-group
    lead_group = create_hex_group(
        name=f"{dept_name} Leadership",
        member_user_ids=users["leads"]
    )
    lead_data = json.loads(lead_group)
    group_ids[f"{dept_name}_Leadership"] = lead_data["id"]
    print(f"Created {dept_name} Leadership: {lead_data['id']} ({len(users['leads'])} members)")

# Grant group access to relevant projects
# Engineering team gets edit access to technical projects
update_hex_project_group_sharing(
    project_id="technical-project-123",
    group_permissions=[
        {"group_id": group_ids["Engineering"], "access": "CAN_EDIT"}
    ]
)

# Analytics team gets view access to all dashboards
update_hex_project_group_sharing(
    project_id="dashboard-project-456",
    group_permissions=[
        {"group_id": group_ids["Analytics"], "access": "CAN_VIEW"}
    ]
)

# Leadership groups get view access to executive dashboards
for dept in ["Engineering", "Data Science", "Analytics"]:
    leadership_group_id = group_ids[f"{dept}_Leadership"]
    update_hex_project_group_sharing(
        project_id="executive-dashboard-789",
        group_permissions=[
            {"group_id": leadership_group_id, "access": "CAN_VIEW"}
        ]
    )

print("Group-based permission management complete!")
```

#### Team Reorganization Example

Handle team changes by updating group memberships:

```python
import json
from hex_mcp.server import (
    list_hex_groups,
    update_hex_group
)

# Get all groups
groups = list_hex_groups()
groups_data = json.loads(groups)

# Find specific groups that need updates
engineering_group = None
for group in groups_data["values"]:
    if group["name"] == "Engineering Team":
        engineering_group = group
        break

if engineering_group:
    # New hires joining
    new_engineers = ["user-new-eng-1", "user-new-eng-2"]

    # Engineers leaving
    departing_engineers = ["user-old-eng-1"]

    # Update group membership
    result = update_hex_group(
        group_id=engineering_group["id"],
        add_member_user_ids=new_engineers,
        remove_member_user_ids=departing_engineers
    )

    print(f"Updated {engineering_group['name']}")
    print(f"  Added: {len(new_engineers)} members")
    print(f"  Removed: {len(departing_engineers)} members")
```

**Group Management Notes**:
- Groups simplify permission management by allowing you to grant access to multiple users at once
- A user can belong to multiple groups
- Maximum 100 users can be added or removed in a single update operation
- Deleting a group does not delete the users, only the group itself
- Group permissions are inherited by all group members
- Use groups with project sharing endpoints to grant team-wide access

### Managing Data Connections

Manage database and warehouse connections for Hex projects.

#### List Data Connections

```python
from hex_mcp.server import list_hex_data_connections
import json

# List all data connections
connections = list_hex_data_connections()
data = json.loads(connections)

for conn in data["values"]:
    print(f"{conn['name']} ({conn['type']}): {conn['id']}")
    if conn.get('description'):
        print(f"  Description: {conn['description']}")

# List with pagination and sorting
page1 = list_hex_data_connections(
    limit=10,
    sort_by="NAME",
    sort_direction="asc"
)
data = json.loads(page1)

if data["pagination"]["next"]:
    page2 = list_hex_data_connections(limit=10, after=data["pagination"]["next"])
```

#### Get Data Connection Details

```python
from hex_mcp.server import get_hex_data_connection
import json

# Get specific connection
connection = get_hex_data_connection(connection_id="conn-123")
data = json.loads(connection)

print(f"Connection: {data['name']}")
print(f"Type: {data['type']}")
print(f"Description: {data.get('description', 'N/A')}")
print(f"Include Magic: {data.get('includeMagic', False)}")
print(f"Allow Writeback: {data.get('allowWritebackCells', False)}")

# Check sharing settings
if 'sharing' in data:
    workspace = data['sharing'].get('workspace', {})
    print(f"Workspace Access: {workspace.get('members', 'None')}")
```

#### Create Data Connections

```python
from hex_mcp.server import create_hex_data_connection
import json

# Create BigQuery connection
bigquery_conn = create_hex_data_connection(
    name="Production BigQuery",
    connection_type="bigquery",
    connection_details={
        "bigquery": {
            "serviceAccountJsonConfig": json.dumps(service_account_config),
            "projectId": "my-gcp-project",
            "enableStorageApi": True,
            "enableDriveAccess": False
        }
    },
    description="Production data warehouse for analytics",
    include_magic=True,
    allow_writeback_cells=False,
    sharing={
        "workspace": {
            "members": "CAN_USE"
        }
    }
)
data = json.loads(bigquery_conn)
print(f"Created BigQuery connection: {data['id']}")

# Create Snowflake connection
snowflake_conn = create_hex_data_connection(
    name="Snowflake Analytics",
    connection_type="snowflake",
    connection_details={
        "snowflake": {
            "account": "my-account",
            "warehouse": "ANALYTICS_WH",
            "database": "ANALYTICS_DB",
            "schema": "PUBLIC",
            "username": "hex_service",
            "password": "secure_password"
        }
    },
    description="Snowflake warehouse for analytics",
    include_magic=True
)
data = json.loads(snowflake_conn)
print(f"Created Snowflake connection: {data['id']}")

# Create Postgres connection
postgres_conn = create_hex_data_connection(
    name="Application Database",
    connection_type="postgres",
    connection_details={
        "postgres": {
            "hostname": "db.example.com",
            "port": 5432,
            "database": "app_db",
            "username": "readonly_user",
            "password": "secure_password",
            "ssl": True
        }
    },
    description="Production application database (read-only)",
    connect_via_ssh=False,
    include_magic=True,
    allow_writeback_cells=False
)
data = json.loads(postgres_conn)
print(f"Created Postgres connection: {data['id']}")
```

#### Update Data Connections

```python
from hex_mcp.server import update_hex_data_connection
import json

# Update connection name and description
result = update_hex_data_connection(
    connection_id="conn-123",
    name="Updated Production BigQuery",
    description="Updated production data warehouse for analytics and reporting"
)
data = json.loads(result)
print(f"Updated connection: {data['name']}")

# Update connection settings
result = update_hex_data_connection(
    connection_id="conn-123",
    include_magic=False,
    allow_writeback_cells=True
)
print("Updated connection settings")

# Update connection sharing
result = update_hex_data_connection(
    connection_id="conn-123",
    sharing={
        "workspace": {
            "members": "CAN_USE",
            "guests": "NONE"
        },
        "groups": {
            "upsert": [
                {"group": {"id": "analytics-team-group-id"}, "access": "CAN_USE"},
                {"group": {"id": "data-eng-group-id"}, "access": "CAN_ADMIN"}
            ]
        }
    }
)
print("Updated connection sharing")

# Rotate credentials by updating connection details
result = update_hex_data_connection(
    connection_id="conn-123",
    connection_details={
        "bigquery": {
            "serviceAccountJsonConfig": json.dumps(new_service_account),
            "projectId": "my-gcp-project",
            "enableStorageApi": True,
            "enableDriveAccess": False
        }
    }
)
print("Rotated connection credentials")
```

#### Bulk Connection Setup

Automate connection setup for new workspaces or environments:

```python
from hex_mcp.server import create_hex_data_connection
import json

# Define standard connections for a workspace
connection_configs = {
    "Production BigQuery": {
        "type": "bigquery",
        "details": {
            "bigquery": {
                "serviceAccountJsonConfig": json.dumps(prod_bq_creds),
                "projectId": "prod-project",
                "enableStorageApi": True
            }
        },
        "description": "Production BigQuery warehouse"
    },
    "Staging BigQuery": {
        "type": "bigquery",
        "details": {
            "bigquery": {
                "serviceAccountJsonConfig": json.dumps(staging_bq_creds),
                "projectId": "staging-project",
                "enableStorageApi": True
            }
        },
        "description": "Staging BigQuery warehouse"
    },
    "Production Snowflake": {
        "type": "snowflake",
        "details": {
            "snowflake": {
                "account": "prod-account",
                "warehouse": "PROD_WH",
                "database": "PROD_DB",
                "username": "hex_prod",
                "password": prod_sf_password
            }
        },
        "description": "Production Snowflake warehouse"
    },
    "Application DB": {
        "type": "postgres",
        "details": {
            "postgres": {
                "hostname": "prod-db.example.com",
                "port": 5432,
                "database": "app_db",
                "username": "readonly",
                "password": postgres_password,
                "ssl": True
            }
        },
        "description": "Application database (read-only)"
    }
}

# Create all connections
created_connections = {}
for name, config in connection_configs.items():
    connection = create_hex_data_connection(
        name=name,
        connection_type=config["type"],
        connection_details=config["details"],
        description=config["description"],
        include_magic=True,
        allow_writeback_cells=False,
        sharing={
            "workspace": {
                "members": "CAN_USE"
            }
        }
    )
    data = json.loads(connection)
    created_connections[name] = data["id"]
    print(f"Created {name}: {data['id']}")

print(f"\nCreated {len(created_connections)} data connections")
```

**Data Connection Management Notes**:
- Supported connection types: BigQuery, Snowflake, Postgres, Redshift, Athena, Databricks
- Each connection type has specific configuration requirements in `connection_details`
- Connection credentials are stored securely by Hex
- Use sharing settings to control who can use each connection
- `CAN_USE` access allows users to query data, `CAN_ADMIN` allows configuration changes
- SSH tunneling supported via `connect_via_ssh` parameter for secure connections
- Consider using connection-level access control for sensitive data sources

## About This Fork

This fork extends the upstream hex-mcp package with bug fixes and new cell operations functionality.

### Bug Fixes (v0.1.10 upstream)
- Five tools declared `-> str` return type but returned Python dicts/lists
- Caused pydantic validation errors in Claude Code MCP integration
- Fixed by adding `json.dumps()` to return statements in `src/hex_mcp/server.py`

**Fixed Tools** (lines 74, 172, 187, 206, 229):
- `list_hex_projects()`
- `get_hex_project()`
- `get_hex_run_status()`
- `get_hex_project_runs()`
- `run_hex_project()`

### New Features

**Cell Operations** (Phase 1 of complete Hex API implementation):
- `list_hex_cells()` - Read notebook structure and cell source code (SQL/CODE cells)
- `update_hex_cell()` - Update SQL/CODE cell source and data connections
- Comprehensive test suite with 29 passing tests (all mocked, no credentials required)
- Full documentation with usage examples for query migration and code refactoring

**Permission Management** (Phase 2 of complete Hex API implementation):
- `update_hex_project_user_sharing()` - Grant or revoke user access to projects
- `update_hex_project_group_sharing()` - Grant or revoke group access to projects
- `update_hex_project_collection_sharing()` - Add or remove projects from collections
- `update_hex_project_workspace_sharing()` - Manage workspace-wide and public access
- 18 additional passing tests for all sharing scenarios
- Complete examples for bulk permission management

**Collection Management** (Phase 3 of complete Hex API implementation):
- `list_hex_collections()` - List all collections in workspace
- `get_hex_collection()` - Get collection details with sharing settings
- `create_hex_collection()` - Create collections with optional sharing
- `update_hex_collection()` - Update collection metadata and sharing
- 18 additional passing tests for collection CRUD operations
- Complete examples for workspace organization by department

**Group Management** (Phase 4 of complete Hex API implementation):
- `list_hex_groups()` - List all groups in workspace
- `get_hex_group()` - Get group details
- `create_hex_group()` - Create groups with optional initial members
- `update_hex_group()` - Update group name and membership (add/remove up to 100 users)
- `delete_hex_group()` - Delete groups from workspace
- 21 additional passing tests for full group CRUD operations
- Complete examples for department-based group management and team reorganization
- All functions include comprehensive Google-style docstrings

**Data Connection Management** (Phase 5 of complete Hex API implementation):
- `list_hex_data_connections()` - List all data connections with pagination and sorting
- `get_hex_data_connection()` - Get connection details including credentials and sharing
- `create_hex_data_connection()` - Create BigQuery, Snowflake, Postgres, Redshift, Athena, Databricks connections
- `update_hex_data_connection()` - Update connection configuration, credentials, and sharing settings
- 18 additional passing tests for data connection CRUD operations
- Complete examples for connection setup, credential rotation, and bulk deployment
- Support for all 6 major database/warehouse connection types
- Full Google-style docstrings with detailed connection type specifications

**Testing Infrastructure**:
- Comprehensive test fixtures with mocked authentication
- 105 passing tests, 0 skipped (all mocked, no credentials required)
- Test coverage growing with each phase
- Security checks to prevent production credentials in tests
- pytest, pytest-asyncio, pytest-cov integration
- Fixed backoff handler to work in both production and test environments

**Documentation**:
- Complete OpenAPI spec analysis (see `OPENAPI-VALIDATION.md`)
- Detailed implementation plan (see `IMPLEMENTATION-PLAN.md`)
- Test strategy guide (see `TEST-STRATEGY.md`)
- Usage examples for all new features

**Upstream**: https://github.com/franccesco/hex-mcp

**Status**: Branch `bugfix/fast-mcp-return-types` includes both bug fixes and new cell operations functionality. Ready for upstream PR submission if desired.
