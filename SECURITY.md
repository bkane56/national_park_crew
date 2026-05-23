# Security Policy

## Overview

This repository is a public, portfolio-focused demo of an AI travel planner.
It includes protective controls for untrusted inputs, real-run access gating,
and runtime guardrails to reduce misuse risk and unbounded API spend.

## Supported Scope

Security reports are welcome for:

- The code in this repository.
- The deployed demo behavior documented in `README.md`.
- Input validation, prompt-injection handling, access-gating behavior, and
  runtime safety controls.

Out of scope:

- Issues requiring physical access to local developer machines.
- Social engineering attempts.
- Denial-of-service testing against public infrastructure.

## Reporting a Vulnerability

Please report suspected vulnerabilities privately by email:

- `briankane56@gmail.com`

Include:

- A clear description of the issue.
- Reproduction steps and expected vs. observed behavior.
- Impact assessment (data exposure, cost abuse, privilege escalation, etc.).
- Optional proof-of-concept (safe/minimal).

Do not open public issues for unpatched security vulnerabilities.

## Response Expectations

Target response times:

- Initial acknowledgment: within 3 business days.
- Triage decision: within 7 business days.
- Status updates: at least every 14 days while remediation is in progress.

These are best-effort targets for a personal portfolio project.

## Disclosure Guidelines

- Practice responsible disclosure and allow reasonable remediation time.
- Avoid accessing or exfiltrating non-public data.
- Keep testing minimal and non-destructive.

## Secret and Environment Handling

- Never commit real secrets to source control.
- Use `.env.example` templates only; keep real values in untracked `.env`.
- Rotate `OPENAI_API_KEY` and `REAL_RUN_ACCESS_CODE` periodically.
- Share access codes only out of band with trusted reviewers.

## Current Security Controls (High Level)

- Demo-first mode with mock fallback for unauthorized real-run requests.
- Validation and normalization of untrusted request fields.
- Prompt-injection pattern checks on instruction-like user input.
- Log redaction/truncation before UI exposure.
- Timeout enforcement with killable worker-process execution for real runs.
