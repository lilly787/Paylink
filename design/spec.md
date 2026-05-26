# Paylink — Sapphire & Platinum Design Spec

## Overview
- **Base colors**: `#0B1528` (bg - Royal Navy), `#14223C` (surface - Deep Cobalt), `#2563EB` (brand - Electric Blue), `#3B82F6` (accent - Neon Cobalt), `#60A5FA` (credits/badges - Soft Ice Blue), `#F1F5F9` (text highlight/soft - Platinum/Silver)
- **Typography**: Headings `Plus Jakarta Sans` / `DM Sans` (500); Body `Inter` (400); Numbers `Space Grotesk` / `Syne` (600)
- **Radius**: 16px for main cards
- **Card border**: 0.5px solid `rgba(59, 130, 246, 0.25)` on `#14223C`

## CSS Variables (use in root)

```css
:root {
  --bg: #0B1528;
  --surface: #14223C;
  --brand: #2563EB;
  --accent: #3B82F6;
  --highlight-light: #EFF6FF;
  --gold-primary: #3B82F6;
  --gold-accent: #60A5FA;
  --gold-soft: #F1F5F9;
  --text: #F8FAFC;
  --muted: #94A3B8;
  --error: #EF4444;
  --divider: rgba(59, 130, 246, 0.2);
  --card-border: 0.5px solid rgba(59, 130, 246, 0.25);
  --overlay: rgba(11, 21, 40, 0.85);
}
```

## Landing page notes
- Hero uses `--bg` full screen. Badge uses `--surface` or `--accent` bg with `--text`.
- Primary Hero CTA: filled `--brand` (Electric Blue) with dark text or bright ice white text; secondary CTA: brand outline.
- Light landing-page sections use `#F8FAFC` background with `--bg` (#0B1528) text. Use `--highlight-light` (#EFF6FF) for subtle pale-platinum tints and accents.

## Mobile app notes
- Primary actions in-app use `--brand` (Electric Blue). Soft ice blue (`--gold-accent`) and platinum/silver are reserved for highlights, badges, credit amounts, and the hero CTA.
- Debit amounts: `--error` (#EF4444). Credit amounts: `--gold-accent` (#60A5FA).
- Bottom nav active color: `--gold-accent` or `--gold-primary` per emphasis.

## Handoff assets
- `design/tokens.json` (this repo)
- Provide SVG icons (filled `--brand`, outline `--muted`), Figma library frames, and phone mockups.

## Files changed/added
- Updated: `static/style.css`
- Updated: `design/tokens.json`, `design/spec.md`
