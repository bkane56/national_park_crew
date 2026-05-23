# Changelog

All notable changes to this project are documented in this file.

## 2026-05-23

### Security hardening and public demo safety

- Added input normalization and validation guardrails for planner request fields.
- Added prompt-injection pattern checks for untrusted instruction-like input.
- Added log redaction and truncation before UI log exposure.
- Replaced raw exception echoing with user-safe internal error messages.
- Added runtime timeout enforcement with killable worker-process execution for real runs.
- Added public security documentation in `SECURITY.md` and linked it from `README.md`.
- Updated `.env.example` templates with safer placeholders and runtime guardrail configuration.
- Documented demo-safe guardrails in `README.md` and `national_park_crew/README.md`.
