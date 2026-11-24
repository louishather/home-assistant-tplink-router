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
- Releases: HACS installs the release ZIP (`hacs.json` has `zip_release`). Pushing a commit (any
  branch) that changes `version` in `custom_components/tplink_router/manifest.json` makes
  `release.yml` create tag `v<version>` and publish a release with the ZIP and that version's
  CHANGELOG section, so every push with a new version goes live in HACS straight away (Louis
  chose this over releasing from main). Versions are `<upstream version>-lh.<n>`: bump `<n>` for
  each fork release on the same upstream version, add a CHANGELOG section for it, and run the
  tests first. Never reuse a version: each release stays installable for rollback. Releases
  published by hand in the GitHub UI still work.
- Updating from upstream: haos-vibe's `tplink_router_fork` package alerts when upstream releases.
  Merge the upstream tag into the working branch, set the version to `<new upstream version>-lh.1`,
  run the tests and push.
- CI: workflows run on `main`, pull requests, published releases, version bumps (release) or by
  hand; nothing else runs on branch pushes.
  The HACS validation workflow is manual only (it fails on a fork).
