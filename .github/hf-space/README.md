---
title: National Park Trip Planner
sdk: docker
app_port: 7860
pinned: false
---

# National Park Trip Planner

Portfolio-grade AI trip planner built with CrewAI + Gradio.

## Live Modes

- **Demo mode:** returns mocked itinerary data only (safe for public viewing).
- **Real mode:** requires a private access code and can invoke live CrewAI planning.

## Architecture (Summary)

1. User submits trip inputs in Gradio UI.
2. Run mode is evaluated:
   - Demo mode returns packaged mock output.
   - Real mode performs server-side access-code validation.
3. Valid real runs execute a sequential CrewAI workflow:
   - airport/flight research
   - lodging research
   - park-activity planning
   - final itinerary write-up
4. Output is generated as Markdown or PDF download.

Full architecture and implementation notes:
- [GitHub README](https://github.com/briankane/National_Park_Trip_Planner/blob/main/README.md)
