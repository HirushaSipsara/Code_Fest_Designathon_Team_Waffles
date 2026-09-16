# LIVLINK frontend analysis

## Source and scope

This analysis covers the complete approved source of truth, [`livlink-prototype.html`](../livlink-prototype.html) (2,459 lines). It remains unchanged. The document distinguishes executable browser simulation from backed implementation; a toast message alone is not treated as backend behaviour.

## Audiences and roles

| Audience | Source location | Purpose and represented journeys |
|---|---:|---|
| Resident | 493–955 | Home, device control, scenes, visitor passes, bills/energy and services. Role switcher previews Owner, Occupier and Tenant rights. |
| Visitor | 956–989 | Opens/uses a pass and submits a scanner verification outcome. |
| Operator | 990–1071 | Building overview, pass verification and maintenance queue. |
| Developer | 1072–1163 | Portfolio/device-health overview and seeded energy metrics. |

Resident role behaviour is explicit at 1335–1372: all three roles retain everyday device/scenes/visitor access; owner-only controls are maintenance-fee/billing/property-related. The scene backend therefore does not create a role distinction beyond validating that the requester is one of those resident roles. AI-created scenes additionally cannot unlock a door, a safety boundary not delegated to the LLM.

## Screens and interactions

| Area | Existing interactions | Classification | Backend needed |
|---|---|---|---|
| Home | room tabs, device toggles, quick scenes, notices, doorbell/gas expanders, accessibility comfort toggle, activity | working browser simulation; alerts/energy suggestions seeded | device state, commands, activity; alerts/event feed later |
| Devices | room/device selection, AC temperature, fan/flow sliders, level controls and device toggles | working browser simulation | device read/command/acknowledgement |
| Scenes | four seeded scene cards, run/pause/edit toasts, natural-language fixed phrase map, speech input, keyboard/tap/drag scene builder, AI suggestion | mixed: builder is simulation; NL map and automation rules are seeded examples | CP3 AI parse, proposal review, persistence, trigger/automation, device execution |
| Access | pass list, deterministic QR, new-pass form validation/link copy, visitor/operator scanner simulation | working browser simulation with seeded pass data | P1 pass/token/verification/audit APIs |
| Bills | usage chart, statement tabs | seeded/view-only | usage/statement provider integration, explicitly outside CP3 |
| Services | facility slot selection, cleaning recurrence suggestion, payment/membership timers, issue form | simulations; some source data seeded | booking/payment/maintenance APIs, P1/P2 |
| Operator | fleet filtering/detail, technician toast, maintenance rendering, verifier | fleet/maintenance seeded; verifier simulation | operator pass/maintenance APIs |
| Developer | portfolio table/detail, chart | seeded demo analytics | portfolio telemetry/analytics, P2 |

## Existing data and validation

Source data structures at 1171–1238 define: action palette (AC, lights, curtains, TV, lock), rooms/devices, four scene cards, seven passes, activity entries, eight fleet devices and three maintenance records. Important validation/feedback includes required scene name/actions (1735–1753), required visitor-pass fields (1888 onwards), pass scanner outcomes (1941–2051), required issue category (2280–2292), empty fleet state (2332–2344), browser speech availability/error messages (1626–1651), unavailable smart plug (1188), and role locks (1350–1372). Accessibility includes semantic navigation, aria labels/expanded states, keyboard scene-palette use and large-control mode.

## CP3 implementation mapping

The React app preserves the original information hierarchy and visual language for the Resident/Home/Devices/Scenes flow. The source remains the complete reference for the unconnected secondary simulations. The new connected route is deliberately confined to existing scene concepts: `resident_arrives`, `time_after`, and prototype device kinds/actions. It replaces only the old `NL_MAP` fixed phrase logic at 1593–1624; it does not make AI control a device.

## Classification summary

**Working browser simulation:** manual device controls, scene builder, pass creation/scanning, bookings, membership/payment timers, issue submission, filters and responsive/accessibility controls.

**Seeded example/data:** NL phrase mapping, automation-rule text, energy/bills/analytics, fleet status, initial passes/activity/maintenance, AI suggestion and portfolio metrics.

**UI-only or incomplete source behaviour:** scene Edit/Pause, technician scheduling, provider payments and some suggestion controls only display toasts; they do not have durable backend effects.
