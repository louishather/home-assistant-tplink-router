# Working in this repo (louishather fork)

Fork of AlexandrErohin/home-assistant-tplink-router, installed in Louis's Home Assistant through
HACS as a custom repository. It adds a DHCP Leases sensor (`get_ipv4_dhcp_leases`), used by the
DHCP dashboard in louishather/haos-vibe, and a wait after a failed update (`failure_cooldown`) for
routers that lock out logins, and a slow poll interval (`slow_scan_interval`) for everything but
status/clients, and an optional held login (`hold_session`) that backs off for `yield_minutes`
when another login takes the session, to cut router CPU. Shared rules for Louis's repos (CI, branches, working
pattern) are in haos-vibe's `CONVENTIONS.md`.

- Keep the diff from upstream small so upstream merges stay easy: add, don't restructure.
- Work on a branch (`feat/<thing>`, `fix/<thing>`). Run the tests locally before pushing:
  Python 3.14 (`uv venv -p 3.14`), `pip install -r requirements_test.txt`, `pytest`.
- Releases: HACS installs the release ZIP (`hacs.json` has `zip_release`). Louis publishes a
  GitHub release named and tagged `<upstream tag>-lh.<n>` (e.g. `v2.47.0-lh.1`) in the web UI,
  creating the tag there (Claude's sessions can't push tags); `release.yml` then sets the
  manifest version and attaches `tplink_router.zip`. Bump `<n>` for fork-only changes on the
  same upstream version.
- Updating from upstream: haos-vibe's `tplink_router_fork` package alerts when upstream releases.
  Merge the upstream tag into `main`, run the tests, then publish release `<new upstream tag>-lh.1`.
- CI: workflows run on `main`, pull requests, published releases or by hand, never on branch pushes.
  The HACS validation workflow is manual only (it fails on a fork).
