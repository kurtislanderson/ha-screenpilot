# ha-screenpilot

Home Assistant custom integration for ScreenPilot kiosk players. Distributed via HACS,
installed as `custom_components/screenpilot/`. Domain `screenpilot`, `local_polling`,
config-flow only (no YAML config).

**This repo owns** the HA-side integration. It does **not** own the ScreenPilot server or
its `/api/*` contract — that lives in `~/Developer/tekworks/ScreenPilot`.

## File structure

| Path | What lives there |
|---|---|
| `custom_components/screenpilot/` | The integration. One module per HA platform. |
| `custom_components/screenpilot/api.py` | Async HTTP client for the ScreenPilot server. All network I/O funnels through here. |
| `custom_components/screenpilot/coordinator.py` | `DataUpdateCoordinator` — single poll, all entities read its `ScreenPilotData`. |
| `custom_components/screenpilot/entity.py` | `ScreenPilotEntity` base: device_info + `data` property with `_DEFAULT_DATA` fallback. |
| `custom_components/screenpilot/const.py` | Domain, service/attr names, `HDMI_INPUTS`, `SESSION_MODES`, `UPDATE_INTERVAL`. |
| `custom_components/screenpilot/__init__.py` | Setup/unload + **all 9 service registrations and their voluptuous schemas**. |
| `custom_components/screenpilot/services.yaml` | Service UI descriptors. Must stay in sync with the schemas in `__init__.py`. |
| `custom_components/screenpilot/manifest.json` | Version lives here — bump it on every release. |
| `tests/test_integration.py` | Stdlib-only structural validator (AST + JSON parsing). No HA, no pytest. |
| `docs/plans/` | Implementation plans, `YYYY-MM-DD-<topic>.md`. |
| `hacs.json` | HACS metadata. `homeassistant` key = minimum supported HA version. |

## Services

`load_url`, `execute_javascript`, `send_cec_command`, `clear_data`, `set_zoom`,
`show_overlay`, `raise_alert`, `clear_alert`, `set_alert_source`.

Each accepts an optional `device_id` to target specific players; omitted = all configured
players. A service added in `__init__.py` needs a matching entry in `services.yaml` and a
matching `ATTR_*` in `const.py` — three files, always together.

## Verify before pushing

CI (`.github/workflows/validate.yml`) runs four jobs: HACS validation, hassfest, Ruff, and
the test script. Reproduce all of the blocking ones locally:

```bash
uvx ruff@0.16.1 check custom_components/screenpilot
uvx ruff@0.16.1 format --check custom_components/screenpilot
python3 tests/test_integration.py          # expects N/N passed
```

**Use the pinned version.** The workflow pins `ruff==0.16.1`; a floating local ruff will
disagree with CI. Ruff widens its *default* rule set between minor releases — 0.16 enabled
`I`, `RUF`, and `BLE` without anyone opting in, which turned a green CI red overnight with
zero source changes. The repo has no `pyproject.toml` or `ruff.toml`, so ruff's defaults
*are* the config, and the version is therefore load-bearing.

When bumping the pin, run the two commands above first and fix the fallout in the same
commit — never let CI discover it. See
[[Unpinned linters - the green build that breaks overnight]].

Ruff runs against `custom_components/screenpilot` only; `tests/` is not linted.

## Conventions

- **Exceptions:** catch specific types, never bare `Exception` (`BLE001`). `api.py` raises
  `ScreenPilotConnectionError` / `ScreenPilotAuthError`; the network layer catches
  `(TimeoutError, aiohttp.ClientError)`.
- **Mutable class attributes** need `ClassVar[...]` (`RUF012`) — e.g. `_attr_options`.
- **Imports** are ruff-`I001`-sorted. `voluptuous` and `homeassistant` are both
  third-party and share a block.
- **New entities** subclass `ScreenPilotEntity` and read `self.data`, never call the API
  for state — the coordinator owns polling.

## Safety

1. **Never bump `manifest.json` version without a matching git tag** — HACS serves
   releases by tag; a version bump with no tag is invisible to users.
2. **Never add to `requirements`** in the manifest unless the dep is genuinely needed. HA
   installs these into the user's environment at setup.
3. **`execute_javascript` runs arbitrary JS on the player.** Keep it, but don't build
   features that pass user-supplied strings into it unreviewed.
4. `docs/` and `.codegraph/` — `.codegraph/` is a local index, never commit it.

## Commits

Conventional Commits (`feat:`, `fix:`, `ci:`, `docs:`, `chore:`). Body explains *why*.
Release flow: `chore: bump to X.Y.Z` → tag `vX.Y.Z` → push tag.
