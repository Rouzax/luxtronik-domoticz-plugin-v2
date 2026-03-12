# GitHub Hero Page Design

## Overview

A standalone GitHub Pages landing page for the Luxtronik Domoticz Plugin v2, deployed via `gh-pages` branch. Goal: attract new Domoticz users with heat pumps to install the plugin.

## Tech Stack

- Plain HTML/CSS/JS — no build step, no dependencies
- Files: `index.html`, `style.css`, `script.js` (lightbox only)
- Deployed on `gh-pages` branch

## Visual Style

- **Dark & techy** theme
- Background: deep charcoal to near-black gradient with subtle grid/circuit-board pattern overlay
- Accent color: cyan / electric blue (energy/cooling theme)
- Subtle glow effects on accent elements
- Responsive: mobile-first, graceful degradation

## Page Sections

### 1. Hero Banner (viewport height)

- Project name in large bold text with subtle glow
- Tagline: "Real-time heat pump monitoring & control for Domoticz"
- Two CTA buttons: "View on GitHub" (primary filled) + "Download Latest Release" (outline)
- Version badge (v2.0.2)
- Dark gradient background with faint grid pattern overlay

### 2. Key Stats Bar

- Horizontal strip on slightly lighter dark surface
- 4 stats with large numbers and small labels:
  - **62** Devices & Sensors
  - **5** Languages
  - **14** Device Groups
  - **Real-time** Monitoring
- Subtle dividers between stats

### 3. Feature Highlights

- 2-3 column grid (stacks on mobile)
- 6 feature cards on elevated dark surface with hover glow:
  1. **Smart COP Tracking** — Separate efficiency metrics for heating, hot water, and combined — only measured during steady-state operation
  2. **Intelligent Gating** — Blocks sensor updates when compressor is idle, preventing misleading readings
  3. **Secure Write Control** — All commands validated against an explicit allowlist before touching your heat pump
  4. **Multi-Instance Support** — Run multiple plugin instances for homes with multiple heat pumps
  5. **5 Languages** — Full translations for EN, NL, DE, FR, PL including device names and descriptions
  6. **Stable Device IDs** — Hardware-based identifiers that persist across IP changes and renames

### 4. Screenshots Gallery

- 3 existing screenshots (utility, temperature, switch devices)
- Rounded corners, subtle accent border/glow
- Captions below each image
- Clickable for full-size view (vanilla JS lightbox)
- Mobile: stacked vertically

### 5. Footer

- Project name + "Made for Domoticz"
- Links: GitHub Repo | Releases | Issues | License
- Version number in small text
