# Credit Burners

JunctionX Lisbon 2026

## The idea

A store assistant that uses existing cameras to identify produce shelves needing attention. Staff get a prioritised list of actions, with images explaining each alert.

Our goal is a phone-friendly app judges can open through a public link and QR code: explore a recorded store day, inspect shelf alerts and their evidence, and see measured results. Fresh analysis and single-tray photo uploads are stretch features.

## Planned stack

- Python / PyTorch on knuth: Qwen3.8-27B, with SAM 3 and DINOv3 evaluated as supporting signals.
- Java / Spring Boot API; React + Tailwind interface.
- JSON results and image files; Cloudflare Tunnel for public HTTPS access, subject to permission and connectivity.
- Saved results for immediate browsing and a laptop demo fallback.

## Current status

Planning scaffold; model weights and setup smoke scripts are on knuth. The application, public deployment and end-to-end smoke test are not implemented yet. No public demo URL exists yet.

- [Plan, roles and milestones](docs/PLAN.md)
- [Data and API contract](docs/CONTRACT.md)
- [Demo script and fallbacks](docs/DEMO.md)
- [Measured results](docs/RESULTS.md)

## How to run

Application commands will be added when the first runnable version exists. `scripts/smoke_test.sh` is currently a placeholder, not evidence that the app works.
