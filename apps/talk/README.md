# UniFi Talk MCP Server

Read-only MCP server for [UniFi Talk](https://ui.com/talk): phones, users, phone numbers, call history, voicemail metadata, and call routing.

> **Status: experimental.** UniFi Talk has no documented API. This server uses the same private endpoints as the Talk web UI (`/proxy/talk/api/...`), verified against Talk 5.4.4. Endpoints may change between Talk releases.

## Requirements

- A UniFi OS console running the Talk application
- A **local** admin account with Talk view permission (cloud SSO accounts with 2FA cannot log in over the local API). Some Talk data, such as the system log and per-area settings, needs Talk manage permission; Talk reports a missing permission as HTTP 500, which this server surfaces as a permission error
- Python 3.13+

Talk has no API-key surface, so username and password are required.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `UNIFI_TALK_HOST` / `UNIFI_HOST` | — | Console IP or hostname |
| `UNIFI_TALK_USERNAME` / `UNIFI_USERNAME` | — | Local admin username |
| `UNIFI_TALK_PASSWORD` / `UNIFI_PASSWORD` | — | Local admin password |
| `UNIFI_TALK_PORT` / `UNIFI_PORT` | `443` | Console HTTPS port |
| `UNIFI_TALK_VERIFY_SSL` / `UNIFI_VERIFY_SSL` | `false` | Verify the console TLS certificate |
| `UNIFI_TALK_REDACT_SENSITIVE_FIELDS` | `true` | Redact secret-bearing fields in responses |
| `UNIFI_MCP_PORT` | `3003` | Port for the optional HTTP transport |

Server-specific `UNIFI_TALK_*` variables take precedence over the shared `UNIFI_*` ones.

## Run

```bash
make -C apps/talk run
```

## Tools

| Category | Tools |
|---|---|
| `system` | `talk_get_system_info`, `talk_get_dashboard`, `talk_get_service_health`, `talk_get_settings`, `talk_get_usage` |
| `devices` | `talk_list_devices`, `talk_get_device` |
| `users` | `talk_list_users` |
| `numbers` | `talk_list_numbers`, `talk_list_blocked_numbers` |
| `calls` | `talk_list_all_calls`, `talk_list_calls`, `talk_get_call_flow`, `talk_get_voicemail`, `talk_get_call_transcript` |
| `callflow` | `talk_list_groups`, `talk_get_switchboard`, `talk_list_ring_flows`, `talk_list_call_queues`, `talk_list_parking_lots`, `talk_list_contacts`, `talk_list_recording_rules` |

All tools are read-only.

### Call log and voicemail

`talk_list_all_calls` returns every call on the console, 50 per zero-based `page`, and flags calls that left a voicemail with `has_voicemail`. `talk_list_calls` returns one user's history: it takes a `user_id` (the `unique_id` from `talk_list_users`) and paginates with `limit`/`offset`. A voicemail shares its `uuid` with the call that left it, so pass a call's `uuid` to `talk_get_voicemail`. Voicemail audio is not returned.

### Privacy

Device, user, and number responses are built from an allowlist of fields, so SIP passwords, device keys, API keys, and permission scopes held by the controller are never returned. Call history contains phone numbers and names; treat tool output accordingly.

## Not yet supported

- Mutations (blocking numbers, restarting phones, editing users, groups, or settings)
- SMS conversations
- Voicemail and call-recording audio
- Support bundles, the REST/GraphQL API server, and the agent plugin
