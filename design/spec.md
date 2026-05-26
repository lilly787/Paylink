 Paylink — Violet + Gold Design Spec
 
 Overview
 - Base colors: `#1C1033` (bg), `#2D1B69` (surface), `#7C3AED` (brand violet), `#A78BFA` (accent), `#D4A017` (gold CTA), `#F5C842` (gold highlight), `#FEF3C7` (cream gold)
 - Typography: Headings `Plus Jakarta Sans` / `DM Sans` (500); Body `Inter` (400); Numbers `Space Grotesk` / `Syne` (600)
 - Radius: 16px for main cards
 - Card border: 0.5px solid `rgba(124,58,237,0.3)` on `#2D1B69`
 
 CSS Variables (use in root)
 
 :root {
   --bg: #1C1033;
   --surface: #2D1B69;
   --brand: #7C3AED;
   --accent: #A78BFA;
   --highlight-light: #EDE9FE;
   --gold-primary: #D4A017;
   --gold-accent: #F5C842;
   --gold-soft: #FEF3C7;
   --text: #FAF7FF;
   --muted: #A78BFA;
   --error: #F87171;
   --divider: rgba(124,58,237,0.25);
   --card-border: 0.5px solid rgba(124,58,237,0.3);
   --overlay: rgba(28,16,51,0.85);
 }
 
 Landing page notes
 - Hero uses `--bg` full screen. Badge uses `--surface` or `--accent` bg with `--text`.
 - Primary Hero CTA: filled `--gold-primary` with dark text; secondary CTA: violet outline.
 - Light landing-page sections use `#FAF7FF` background with `--bg` (#1C1033) text. Use `--highlight-light` (#EDE9FE) for subtle pale-violet tints and accents.
 
 Mobile app notes
 - Primary actions in-app use `--brand` (rich violet). Gold (`--gold-primary` / `--gold-accent`) is reserved for highlights, badges, credit amounts, and the hero CTA.
 - Debit amounts: `--error` (#F87171). Credit amounts: `--gold-accent` (#F5C842).
 - Bottom nav active color: `--gold-accent` or `--gold-primary` per emphasis.
 
 Handoff assets
 - `design/tokens.json` (this repo)
 - Provide SVG icons (filled `--brand`, outline `--muted`), Figma library frames, and phone mockups.
 
 Files changed/added
 - Updated: `static/style.css`
 - Updated: `design/tokens.json`, `design/spec.md`
 
 Next steps
 - Export Figma/Sketch components and SVG icon set.
 - Generate a Storybook or simple component HTML preview if you want a functional UI kit.
