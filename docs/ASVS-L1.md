# ASVS 5.0 Level 1 — tracked

Status is about *this tree*, not the poster. Update when code changes.

| ID (sense) | Requirement | Status | Evidence |
| --- | --- | --- | --- |
| Validation | HTTPS + host allowlist + redirect re-check | implemented | `allowlist.py`, `tests/test_allowlist.py` |
| Injection | No shell/eval from persona or URLs | implemented | persona is JSON; no subprocess in engines |
| Authorization | Status read-only; login cookie; no wake | implemented | POST 405 except `/login` `/logout` |
| Config | Loopback default; LAN needs token | implemented | `require_status_bind` |
| Config | Secrets not in git | implemented | `.env` gitignored; template only |
| Files | Slot install does not touch `/etc/lucy` | implemented | `install_from_dir` |
| Integrity | Slot requires SHA256SUMS | implemented | `verify_sums` |
| Integrity | Git pull is opt-in TOFU | implemented | `LUCY_AUTO_UPDATE=off` default; `consent-updates.sh` |
| Integrity | Cosign on GitHub releases | missing | `signed` mode fail-closed |
| Client | nosniff + DENY frame on hatch | implemented | `daemon.py` `_bytes` / `_json` |
| API | Small JSON, no mass assignment | implemented | hardcoded keys in status payload |
| Errors | Fail closed on bad sums / bad bind | implemented | SystemExit |
| Errors | Fail closed on unsigned origin pull | implemented | no consent → check only; `signed` exits |
| Supply chain | Lockfiles | partial | Python still ranges |
| Supply chain | CI verify | ready | `.github/workflows/verify.yml` unrun |
| Logging | No tokens or tracker query strings in JSONL | implemented | harvest stores host/vendor/kind only |
| LLM/MCP | Stubs stay inert | implemented | unread key; `LUCY_MCP_ENABLED=false` |

**Missing on purpose until origin exists:** cosign identity, SBOM in releases, hashed pip pins in CI cache.

**Missing until a Pi exists:** overnight `live_public`, thermal, Chromium OOM.
