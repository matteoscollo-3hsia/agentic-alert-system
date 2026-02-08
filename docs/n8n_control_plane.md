# n8n Control Plane

This document describes how to run the local n8n control plane and how to import the versioned workflows stored in this repo.

## Start n8n (Docker Compose)
From the repo root:
```bash
cd n8n-control-plane
cp .env.example .env
# edit .env with your real values

docker compose up -d
```
Open n8n at http://localhost:5678

## Import workflows
Workflow JSON files are stored in `n8n/workflows/`:
- `n8n/workflows/dispatch_daily_pipeline.json`
- `n8n/workflows/dispatch_daily_pipeline_with_run_link.json`

In the n8n UI:
1. Go to Workflows.
2. Use **Import from File** (or the Import menu in the canvas).
3. Select the JSON file and save the workflow.
4. Update credentials and the Slack channel.

## Required credentials (UI)
### GitHub PAT (HTTP Header Auth)
Create a credential of type **HTTP Header Auth**:
- Name: `GITHUB_PAT` (or any name you will reference in the workflow)
- Header Name: `Authorization`
- Header Value: `Bearer <YOUR_PAT>`

Permissions (minimum):
- Fine-grained PAT: repo access only to `agentic-alert-system`, permissions `Actions: Read and write`, `Contents: Read`.
- Classic PAT: `repo` (private) or `public_repo` (public). Add `workflow` if dispatch fails with 403.

### Slack
Create a credential of type **Slack API** (Bot token with `chat:write`).
If you prefer Slack webhook, switch the node type and store the webhook URL in its credential (never in Git).

## Troubleshooting 401 (GitHub)
- Missing `Bearer ` prefix in the `Authorization` header.
- Token has insufficient scopes (Actions read/write for fine-grained; `repo`/`workflow` for classic).
- PAT does not have access to the repo.

## Secrets in git
Never commit `.env` or exported credential files. Keep secrets only in n8n credentials.
