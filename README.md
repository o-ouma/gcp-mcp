# GCP-MCP Server

A modular, type-safe MCP (Model Context Protocol) server for managing Google Cloud Platform (GCP) resources with AI tooling.

This server exposes typed tools for storage, compute, networking, and billing/monitoring via FastMCP. It’s organized for maintainability with clear modules, Pydantic models for validation, and robust authentication.

## What’s New

- Modular tools under `tools/` (storage, compute, network, billing/monitoring)
- Strong typing and input validation using Pydantic models in `models.py`
- Centralized and hardened GCP authentication (`auth.py`) with `GCPAuthError`
- Consistent, structured responses (`SuccessResponse`, `ErrorResponse`, and typed response models)
- Clean server wrapper (`mcp_server.py`) that registers tools and serializes responses
- Docker support and example Claude Desktop MCP config

## Features

- Storage
  - List buckets
  - Create bucket (with versioning option)
  - Delete bucket
- Compute
  - List instances (by zone or across zones)
  - List persistent disks (with attachment info)
  - List IP addresses (internal/external, global/regional)
  - Delete instance
  - Create instance (API contract validated; implementation is a placeholder)
- Network
  - List VPC networks and subnets (with details per region)
  - List load balancers (forwarding rules, regional and global)
- Billing & Monitoring
  - Get billing account linkage and time window metadata (simplified cost payload)
  - Get metrics (placeholder contract; ready for expansion)

## Requirements

- Python 3.10+
- Google Cloud project with the relevant APIs enabled (Compute Engine, Cloud Storage, etc.)
- Service account with sufficient permissions
- Docker (optional)

## Setup

1) Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Provide credentials

- Place your service account key in `keys/` (or anywhere accessible)
- Set the env var so the server can load credentials:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/keys/gcp-key.json"
```

On Windows/PowerShell:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "$PWD/keys/gcp-key.json"
```

## Run the MCP server

```bash
python mcp_server.py
```

This starts the FastMCP server and registers all tools. Integrate it with an MCP-compatible client (e.g., using claude_desktop_config.json as a reference) or import tools directly in Python for scripting.

## Configure an MCP client (Claude Desktop)

Add or update your Claude Desktop config to launch this server as an MCP tool. Minimal examples:

- macOS/Linux, direct Python

```json
{
  "mcpServers": {
    "gcp_mcp": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/home/USER/projects/mcp-tools/gcp-mcp",
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/home/USER/projects/mcp-tools/gcp-mcp/keys/gcp-key.json"
      }
    }
  }
}
```

- Windows using WSL

```json
{
  "mcpServers": {
    "gcp_mcp": {
      "command": "wsl",
      "args": [
        "bash",
        "-lc",
        "cd /home/USER/projects/mcp-tools/gcp-mcp && source venv/bin/activate && python mcp_server.py"
      ]
    }
  }
}
```

Notes:
- Replace `USER` and paths as appropriate for your machine.
- Ensure your virtualenv is activated (or remove `source venv/bin/activate` if running system Python with deps installed).
- You can also use the provided `claude_desktop_config.json` as a template and adjust paths.

## Docker

Build the image:

```bash
docker build -t gcp-mcp:latest .
```

Run the container with credentials mounted:

```bash
docker run --rm \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/keys/gcp-key.json \
  -v $(pwd)/keys:/app/keys \
  -p 3000:3000 \
  gcp-mcp:latest
```

Note: Adjust the exposed port to match your MCP client configuration if needed.

## Tools API Summary

All tools are registered via `@mcp.tool` and exposed by `mcp_server.py`. Inputs are validated; errors return `{ error, success: false, details? }`.

- Storage
  - `list_buckets(project_id: str) -> List[str] | Error`
  - `create_bucket(project_id: str, bucket_name: str, location: str, storage_class?: str, versioning?: bool) -> { message, success } | Error`
  - `delete_bucket(project_id: str, bucket_name: str) -> { message, success } | Error`
- Compute
  - `list_instances(project_id: str, zone?: str) -> List[str] | Error`
  - `list_persistent_disks(project_id: str, zone?: str) -> PersistentDisk[] | Error`
  - `list_ip_addresses(project_id: str, region?: str) -> IPAddress[] | Error`
  - `delete_instance(project_id: str, zone: str, instance_name: str) -> { message, success } | Error`
  - `create_instance(project_id: str, zone: str, instance_name: str, machine_type: str, image_family: str, disk_size_gb?: int, network?: str, subnetwork?: str, tags?: string[], service_account?: string) -> { message, success } | Error` (placeholder)
- Network
  - `list_vpc_networks_and_subnets(project_id: str) -> VPCNetwork[] | Error`
  - `list_load_balancers(project_id: str, region?: str) -> LoadBalancer[] | Error`
- Billing & Monitoring
  - `get_billing_cost(project_id: str, start_date?: ISODate, end_date?: ISODate, group_by?: string[]) -> BillingCost | Error`
  - `get_metrics(project_id: str, metric_type: str, interval?: string, aggregation?: string) -> Metrics | Error`

See `models.py` for full schemas:
- PersistentDiskResponse, IPAddressResponse, VPCNetworkResponse, LoadBalancerResponse
- BillingCostResponse, MetricsResponse, SuccessResponse, ErrorResponse

## Quick Examples (direct Python usage)

List disks in a zone:

```python
from tools.compute_tools import list_persistent_disks
res = list_persistent_disks("my-project", "us-central1-a")
print(res)
```

List VPC networks and subnets:

```python
from tools.network_tools import list_vpc_networks_and_subnets
res = list_vpc_networks_and_subnets("my-project")
print(res)
```

Create a bucket:

```python
from tools.storage_tools import create_bucket
res = create_bucket("my-project", "my-bucket-123", "US", storage_class="STANDARD", versioning=True)
print(res)
```

## Project Structure

```
.
├─ auth.py                # Centralized GCP auth (with GCPAuthError)
├─ models.py              # Pydantic request/response models and enums
├─ mcp_server.py          # Registers MCP tools, serializes responses
├─ tools/
│  ├─ storage_tools.py    # Buckets
│  ├─ compute_tools.py    # Instances, disks, IPs
│  ├─ network_tools.py    # VPCs, subnets, load balancers
│  └─ billing_tools.py    # Billing, monitoring
├─ requirements.txt
├─ Dockerfile
├─ gcp_mcp.sh             # Helper script (optional)
└─ keys/                  # Place service account JSON here (do not commit)
```

## Permissions & API Enablement

Make sure your service account/project has required IAM roles and APIs enabled:
- Compute Engine API, Cloud Storage, Cloud Billing API (as needed), Cloud Monitoring API
- Roles like `compute.viewer`, `storage.admin`, etc., depending on operations

## Notes & Limitations

- `create_instance` currently validates the request and returns a success message placeholder; implement full instance creation as needed.
- `get_billing_cost` returns a simplified payload for now; extend with actual cost queries as appropriate.
- Some network/load balancer fields differ between global/regional resources; the tool normalizes common fields.

## Troubleshooting

- Auth errors: verify `GOOGLE_APPLICATION_CREDENTIALS` path and key file permissions.
- Permission denied: check IAM roles on the service account.
- Empty results: confirm correct `project_id`, region/zone strings (e.g., `us-central1`, `us-central1-a`).
- API not enabled: enable the specific Google API in the Cloud Console.

## Contributing

- Keep tools small and focused; add/extend Pydantic models in `models.py`.
- Prefer returning typed responses and consistent `ErrorResponse` on failures.
- Add docstrings for public functions and keep README up to date.
