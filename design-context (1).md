# Design Context — वित्तमंत्री (VittaMantri)

Reference for developers building new pages or components in the app.
Reflects the household finance tracker brand direction (see
`vittamantri_landing_page_content.md`) as actually implemented in
`frontend/src`.

---

## Theme Foundation

- **UI Framework**: Material UI (MUI) v5
- **Font**: Inter, base size 14px (`1rem = 14px`)
- **Theme file**: `frontend/src/theme/theme.js`
- **Brand mark**: `frontend/src/components/BrandMark.jsx` — the "वि" household
  monogram (from वित्तमंत्री's opening syllables). Used instead of any generic
  finance icon (wallet, ₹, piggy bank) — see **Brand Voice** below.
- No separate colors/typography/dims files — everything lives in the one
  `theme.js` (`palette`, `shape`, `shadows`, `components` overrides) plus
  inline `sx` props on components. Keep it that way; don't split into a
  larger theme-file structure unless the app's complexity actually demands it.

---

## Color Palette

Brand direction: a warm household product, not a financial institution or
bank. Large whitespace, warm neutral background, rounded cards — not a dark
corporate dashboard.

### Primary — Deep Green
| Token | Hex | Usage |
|-------|-----|-------|
| primary.main | `#173F35` | Buttons, links, active nav state, primary CTAs |
| primary.dark | `#0F2A23` | Hover states |

### Accent — Muted Gold
| Token | Hex | Usage |
|-------|-----|-------|
| accent.main (`theme.palette.accent.main`) | `#D89B45` | **Sparingly** — final-CTA buttons on a dark section, small highlights, important numbers. Never as the default button color. |

### Background
| Token | Hex | Usage |
|-------|-----|-------|
| background.default | `#F6F1E7` | App/page background (warm ivory) |
| background.paper / card bg | `#FFFFFF` | Cards, modals, sidebar — kept white (not ivory) so data-dense surfaces (tables, forms) stay legible against the warm canvas |
| soft green | `#E6EFEA` | Feature-card backgrounds, icon-chip backgrounds, active nav item background, analytics tint |

### Text
| Token | Hex | Usage |
|-------|-----|-------|
| text.primary | `#202421` | Charcoal — page titles, card values, body text |
| text.secondary | `#454940` | Subtitles, form labels |
| — | `#5B5F54` | Section headers, table head, captions |
| — | `#6B6F63` | Muted descriptions, subtext |
| — | `#9A9C90` | Placeholder text, faint icons |

### Borders / Dividers
| Token | Hex | Usage |
|-------|-----|-------|
| — | `#E2DCC9` | Borders, dividers (warm, not cool gray) |
| — | `#CFC7AE` | Form input borders |
| — | `#F1ECDD` | Card/row hover background |
| — | `#EDE7D8` | Table head background |

### Status (semantic — unrelated to brand chrome, left as standard finance semantics)
| Status | Main | Background | Usage |
|--------|------|------------|-------|
| Success | `#059669` | `#E6EFEA` | Income, resolved states |
| Warning | `#F59E0B` | `#FFFBEB` | Attention needed |
| Error | `#DC2626` | `#FEF2F2` | Expense-adjacent errors, destructive actions |
| Info | `#2563EB` | `#EFF4FF`/`#DBEAFE` | Informational only |

### Data-viz / category colors
Category chips, per-member avatar colors, and category-legend swatches use a
distinct small palette (`#7C3AED`, `#0891B2`, `#DB2777`, `#EA580C`, `#D97706`,
`#65A30D`, `#4F46E5`, `#9333EA`, `#16A34A`, `#0D9488`, `#BE123C`, `#047857`,
`#0369A1`) kept intentionally separate from brand chrome — these exist purely
to visually distinguish N categories/members from each other, not to carry
brand meaning. Don't reassign these to brand tokens.

---

## Brand Voice — Do / Do Not

वित्तमंत्री should read as **calm, trustworthy, simple, modern, warm,
family-oriented** — never like a bank, investment platform, accounting
product, or corporate ERP tool.

**Avoid in UI copy and iconography:**
- ₹ symbol as a standalone icon, piggy banks, wallet icons, coin stacks,
  upward stock charts, bank buildings, credit cards, handshake icons
- Words: wealth, portfolio, financial freedom, optimize, AI-powered,
  revolutionary, fintech, budget discipline
- Corporate banking layouts, heavy dark dashboards, neon fintech colors,
  glassmorphism, dense accounting tables above the fold

**Prefer:**
- Household, family, spending, expenses, clarity, together, understand,
  track, simple, private
- The "वि" brand mark (`BrandMark.jsx`) over any generic finance icon
- Large whitespace, rounded cards (`0.75rem`–`1rem` radius), simple charts

---

## Typography Scale

All sizes in rem where `1rem = 14px` (MUI's `typography.fontSize: 14`).

| Usage | Size | Weight |
|-------|------|--------|
| Page title (Header) | 1.675rem (24px) | 600 |
| Landing hero heading | 2–3.25rem responsive (32–46px) | 700 |
| Section heading (Landing) | 1.86–2.29rem responsive (26–32px) | 700 |
| Card section title | 1.25rem (18px) | 600 |
| Card title / KPI value | 1.714rem (24px) | 700 |
| Body text | 0.875rem–1.0625rem (14–17px) | 400 |
| Caption / muted subtext | 0.75–0.875rem (12–14px) | 400–500 |
| Section eyebrow (uppercase label) | 0.8125rem (13px) | 600, letter-spacing 0.06em |
| Table head | 0.857rem (12px) | 500, uppercase, letter-spacing 0.05em |

---

## Spacing

Theme spacing unit = 8px (MUI default). Common values in this codebase:

| Usage | Value |
|-------|-------|
| Grid container gaps | `spacing={2}` (16px) or `spacing={2.5}` (20px) on Landing |
| Main content area padding (Dashboard) | `p: '20px'` |
| Card internal padding (large) | `p: 3` (24px) or `p: '1.71rem'` |
| Card internal padding (compact) | `p: 2.5` (20px) |
| Landing section vertical padding | `py: { xs: 7, md: 9 }` |
| Sidebar header height | `72px` (fixed, matches Header height so they align) |

---

## Dimensions

| Element | Value |
|---------|-------|
| Sidebar width (expanded) | 260px |
| Sidebar width (collapsed) | 80px |
| Header height | 72px |
| Input / button height | 44px |
| Input / button border-radius | 8px |
| Card border-radius | 0.75rem (12px) large cards; 1rem on Landing feature cards |

---

## Layout Patterns

### Authenticated app shell (`pages/Dashboard.jsx`)
```jsx
<Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: '#F6F1E7' }}>
  <Sidebar
    collapsed={sidebarCollapsed}
    onToggleCollapse={handleToggleCollapse}
    currentUser={currentUser}
    onLogout={onLogout}
    activeSection={activeSection}
    onNavigate={handleSidebarNavigate}
  />
  <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
    <Header title={...} caption={...} {...actionProps} />
    <Box sx={{ flex: 1, p: '20px', overflow: 'auto' }}>{/* page content */}</Box>
  </Box>
</Box>
```

### Sidebar (`components/Sidebar.jsx`)
- Collapsible: `collapsed` prop shrinks it to an 80px icon-only rail with
  tooltips; state lives in `Dashboard.jsx`, persisted to
  `localStorage['sidebar_collapsed']`.
- **User + logout footer lives at the bottom of the sidebar** (avatar, name,
  role, logout icon) — not in the Header. Don't move logout back to the
  header; it was deliberately relocated so it isn't sandwiched between
  action buttons.
- Desktop: fixed `Box`. Mobile (`xs`/`sm`): MUI `Drawer`, always full-width,
  never collapsed.

### Landing page (`pages/Landing.jsx`)
- Full pre-login marketing page, not just a login card. Sticky nav
  (`Overview` / `How it works` / `Analytics` / `Privacy` anchors + Login/Get
  started buttons) → 10 content sections → footer.
- `SectionShell` helper: alternates `bgcolor` between `transparent`
  (page background shows through) and `#FFFFFF` band, `maxWidth: 1100`,
  centered, `py: { xs: 7, md: 9 }`.
- Section structure: uppercase `Eyebrow` label → heading → supporting copy →
  bold highlight line in `primary.main`. Reuse this rhythm for any new
  marketing section rather than inventing a new one.
- The only section on a solid dark background is the final CTA
  (`bgcolor: '#173F35'`, white text, **gold** button) — that combination is
  reserved for the single closing CTA, not used elsewhere.

### Card patterns
**KPI / stat card** (`components/StatsCards.jsx`, Dashboard summary row):
```jsx
<Card variant="outlined" sx={{ borderRadius: '0.75rem', borderTop: '3px solid #059669' }}>
  <CardContent sx={{ p: 3 }}>
    <Typography sx={{ fontSize: '0.857rem', fontWeight: 500, color: '#5B5F54', textTransform: 'uppercase' }}>TITLE</Typography>
    <Typography sx={{ fontSize: '1.714rem', fontWeight: 700, color: '#202421' }}>VALUE</Typography>
    <Typography sx={{ fontSize: '0.857rem', color: '#6B6F63' }}>Subtitle</Typography>
  </CardContent>
</Card>
```

**Section card with header** (charts, tables):
```jsx
<Card variant="outlined" sx={{ borderRadius: '0.75rem' }}>
  <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #E2DCC9' }}>
    <Typography sx={{ fontSize: '1.25rem', fontWeight: 600, color: '#202421' }}>Section Title</Typography>
  </Box>
  <CardContent sx={{ p: 3 }}>{/* chart / table */}</CardContent>
</Card>
```

**Landing feature card:**
```jsx
<Card variant="outlined" sx={{ borderRadius: '1rem', bgcolor: '#FFFFFF' }}>
  <CardContent sx={{ p: 3.5 }}>
    <Box sx={{ width: 44, height: 44, borderRadius: '10px', bgcolor: '#E6EFEA', color: '#173F35', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Icon />
    </Box>
    {/* title, copy, checklist */}
  </CardContent>
</Card>
```

---

## Button Styling

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| contained | `primary.main` (#173F35) | white | none |
| outlined | white | `#454940` | 1px solid `#CFC7AE` |
| text | transparent | `primary.main` | none |
| Final-CTA exception (Landing, dark section only) | `#D89B45` (gold) | `#202421` | none |

Common props: `fontWeight: 600`, `borderRadius: 8px`, `textTransform: capitalize`, no elevation/shadow.

---

## Table Styling

| Element | Style |
|---------|-------|
| Head cell bg | `#EDE7D8` |
| Head cell text | `#5B5F54`, weight 500, 12px, uppercase |
| Body cell | 14px, padding `6px 16px`, height 60px |
| Row hover | `#FCF3DF` |
| Border color | `#E2DCC9` |

---

## Form Inputs

- Height: 44px, border-radius: 8px
- Border: `1px solid #CFC7AE`, hover border: `primary.main`
- Box-shadow: `0px 1px 2px 0px rgba(16,24,40,0.05)`
- Avoid `TextField select` for anything beyond the simple user/category
  filters already in `Header.jsx`/`FilterBar.jsx` — those are fine as-is;
  don't introduce a new dropdown pattern without reason.

---

## Do / Do Not

**Do:**
- Reference `theme.palette.*` tokens where the component already threads
  through the theme (MuiButton/MuiCard/MuiOutlinedInput overrides); use the
  documented hex values above for one-off `sx` colors elsewhere, matching
  the existing inline-hex convention in this codebase.
- Keep cards `variant="outlined"`, radius `0.75rem`–`1rem`.
- Keep the sidebar's user/logout footer at the bottom — don't reintroduce a
  header-based logout.
- Use the `SectionShell` + `Eyebrow` rhythm for any new Landing section.
- Use `BrandMark` for the app logo everywhere (sidebar, login, landing nav).
- Keep semantic status colors (success/error/warning) and the data-viz
  category palette separate from brand chrome — don't reuse `primary.main`
  for a category swatch or vice versa.

**Do Not:**
- Don't reintroduce the old blue (`#004EEB`) or cool-gray (`#EAECF0`,
  `#101828`) palette — this app is fully on the deep-green/ivory/gold
  system now.
- Don't use wallet/₹/piggy-bank icons for branding.
- Don't make the gold accent (`#D89B45`) a default action color — it's a
  highlight color, used sparingly (currently: one final-CTA button).
- Don't add dark corporate-dashboard styling, neon colors, or glassmorphism.
