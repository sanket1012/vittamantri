# Design Context 
Reference for developers building new pages or components in the portal.

---

## Theme Foundation

- **UI Framework**: Material UI (MUI) v5
- **Font**: Inter (TTF), base size 14px (1rem = 14px)
- **Theme file**: `src/theme/theme.js`
- **Colors**: `src/theme/colors.styles.js`
- **Typography**: `src/theme/font.js`
- **Dimensions**: `src/theme/dims.js`
- **Form controls**: `src/theme/form-controls.styles.js`
- **Table styles**: `src/theme/table.styles.js`

---

## Color Palette

### Primary
| Token | Hex | Usage |
|-------|-----|-------|
| primary.main | #004EEB | Buttons, links, active states |
| primary.dark600 | #155EEF | Hover states |
| primary.darker | #00359E | Pressed states |

### Text
| Token | Hex | Usage |
|-------|-----|-------|
| text.primary | #101828 | Page titles, card values, body text |
| text.secondary | #344054 | Subtitles, form labels |
| text.caption | #475467 | Section headers, table head, captions |
| text.disabled | #787486 | Disabled text |
| text.label | #5D5E74 | Form field labels |
| — | #667085 | Muted descriptions, subtext |
| — | #98A2B3 | Placeholder text, icons |

### Backgrounds
| Token | Hex | Usage |
|-------|-----|-------|
| background.default | #F6F6F6 | App background |
| gray.50 | #F9FAFB | Card hover, subtle backgrounds |
| gray.100 | #F2F4F7 | Table head, accordion, sticky header bg |
| gray.200 | #EAECF0 | Borders, dividers |
| gray.300 | #D0D5DD | Form input borders |

### Status
| Status | Main | Background | Usage |
|--------|------|------------|-------|
| Success | #059669 | #F0FDF4 | On track, resolved |
| Warning | #F59E0B | #FFFBEB | Attention needed |
| Error | #DC2626 | #FEF2F2 | Critical, breached |
| Info | #2563EB | #EFF6FF | Informational |

### Extended Status (chips, badges)
| Type | Background | Text | Border |
|------|-----------|------|--------|
| Primary chip | #EFF8FF | #004EEB | #B2DDFF |
| Success chip | #ECFDF3 | #067647 | #ABEFC6 |
| Warning chip | #FEDF89 | #B54708 | — |
| Error chip | #FEF2F2 | #D92D20 | — |

---

## Typography Scale

All sizes in rem where 1rem = 14px.

| Variant | Size | Weight | Usage |
|---------|------|--------|-------|
| subtitle1 | 1.675rem (24px) | 600 | Page titles (PageHeader default) |
| subtitle2 | 1.25rem (18px) | 600 | Section titles (DashSection) |
| subtitle3 | 1rem (14px) | 600 | Card titles, bold labels |
| caption | 0.875rem (12px) | 400 | Small labels |
| caption2 | 1rem (14px) | 400 | PageHeader caption, descriptions |
| caption3 | 1rem (14px) | 600 | Bold captions |
| h1 | 1.714rem (24px) | 700 | Large headings |
| h2 | 1.571rem (22px) | 600 | Card headers (DashCard) |
| overline | — | 500 | Section labels (uppercase) |

---

## Spacing

Theme spacing unit = 8px. Common values:

| Usage | Value |
|-------|-------|
| Grid container gaps | `spacing={2}` (16px) |
| Page padding (PageContainer) | `1.43rem` (20px) |
| Card internal padding (large) | `1.71rem` (24px) |
| Card internal padding (compact) | `p: 2.5` (20px) |
| Section bottom margin | `mb={2}` (16px) |
| PageHeader bottom margin | `30px` |

---

## Dimensions

| Element | Value |
|---------|-------|
| Sidebar width | 260px (desktop), 240px (mobile) |
| Sidebar collapsed | 5.78571rem (~82px) |
| Header height | 66px (desktop only) |
| Input height | 2.75rem (44px) |
| Input border-radius | 0.57rem (8px) |
| Button height | 2.75rem (44px) |
| Tab height | 40px |

---

## Page Structure

Every page follows this exact wrapper pattern to ensure headers are flush with the sidebar:

```jsx
import PageContainer from '../../shared/components/PageContainer';
import PageHeader from '../../shared/components/PageHeader';
import PageContent from '../../shared/components/PageContent';

const MyPage = () => (
  <PageContainer sx={{ pt: 0 }}>
    <PageHeader title="Page Title" caption="Description text">
      {/* Action buttons go here as children */}
      <Button variant="outlined">Action</Button>
    </PageHeader>

    <PageContent sx={{ p: 2, top: 20 }}>
      {/* Scrollable page content goes here */}
    </PageContent>
  </PageContainer>
);
```

### PageContainer (`src/shared/components/PageContainer.js`)
- Wraps full page
- Adds `padding: 1.43rem`, `height: 100vh`, `overflow: auto`
- **MUST include `sx={{ pt: 0 }}`** when used with `PageHeader` to align the header flush to the top viewport edge.

### PageHeader (`src/shared/components/PageHeader.js`)
- **CRITICAL**: Do NOT wrap `PageHeader` in a `<Stack>`, `<Box>`, or breadcrumb component. Doing so breaks the full-bleed edge-to-edge layout. It must be a direct child of `PageContainer`.
- Fixed height: `72px` to exactly match the sidebar logo header height.
- Flat background (`#FAFBFF`), no shadows or gradients. 
- Props: `title`, `caption`, `subTitle`, `icon`, `onBack`, `children` (action buttons)
- Title: `variant="subtitle1"` (1.675rem, weight 600)
- Caption: `variant="caption2"` (1rem, weight 400)
- Bottom border: `1px solid #EAECF0`
- Action buttons placed via `children` (right-aligned)

---

## Card Patterns

### Large Summary Card (Dashboard command centre)

Used for KPI-style metrics with status border and subtitle.

```jsx
<Card variant="outlined" sx={{
  borderRadius: '0.75rem',
  border: '1px solid #EAECF0',
  boxShadow: '0px 1px 2px 0px rgba(16, 24, 40, 0.05)',
  borderTop: '3px solid #059669',  // green/amber/red by status
}}>
  <CardContent sx={{ p: '1.71rem', '&:last-child': { pb: '1.71rem' } }}>
    <Box display="flex" justifyContent="space-between" alignItems="flex-start">
      <Box>
        <Typography sx={{ fontSize: '0.857rem', fontWeight: 500, color: '#475467',
          textTransform: 'uppercase', letterSpacing: '0.05em', mb: 1 }}>
          TITLE
        </Typography>
        <Typography sx={{ fontSize: '1.714rem', fontWeight: 700, color: '#101828' }}>
          VALUE
        </Typography>
        <Typography sx={{ fontSize: '0.857rem', color: '#667085', mt: 0.5 }}>
          Subtitle
        </Typography>
      </Box>
      <Box sx={{ width: 44, height: 44, borderRadius: '10px',
        backgroundColor: '#05966910', color: '#059669',
        display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon />
      </Box>
    </Box>
  </CardContent>
</Card>
```

### Compact Metric Card (Exception Hub, Task Manager)

Used for clickable filter cards with counts. Horizontal icon + text layout.

```jsx
<Card elevation={0} onClick={handleClick} sx={{
  p: 2.5,
  cursor: 'pointer',
  border: isSelected ? `2px solid ${color}` : '1px solid #EAECF0',
  borderRadius: 2,
  transition: 'all 150ms ease',
  backgroundColor: isSelected ? `${color}08` : '#fff',
  '&:hover': { borderColor: color, transform: 'translateY(-1px)',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)' },
}}>
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
    <Box sx={{ width: 44, height: 44, borderRadius: 1.5,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      bgcolor: `${color}18`, color }}>
      <Icon />
    </Box>
    <Box>
      <Typography sx={{ fontSize: '0.75rem', fontWeight: 600,
        textTransform: 'uppercase', color: '#475467', letterSpacing: '0.05em' }}>
        LABEL
      </Typography>
      <Typography sx={{ fontSize: '2rem', fontWeight: 700,
        lineHeight: 1.1, color: '#101828' }}>
        COUNT
      </Typography>
    </Box>
  </Box>
</Card>
```

Grid for compact cards (auto-width columns):
```jsx
<Grid container spacing={2}>
  <Grid item xs={6} sm={3} md> {/* md with no value = auto-fill */}
    <CompactMetricCard />
  </Grid>
</Grid>
```

### Card with Header Section (Regional Status, Team Performance)

```jsx
<Card variant="outlined" sx={{ borderRadius: '0.75rem', border: '1px solid #EAECF0' }}>
  <Box sx={{ px: 3, py: 2.5, borderBottom: '1px solid #EAECF0' }}>
    <Typography sx={{ fontSize: '1.125rem', fontWeight: 600, color: '#101828' }}>
      Section Title
    </Typography>
  </Box>
  <TableContainer>
    <Table size="small">...</Table>
  </TableContainer>
</Card>
```

### Action Required Banner

```jsx
<Card variant="outlined" sx={{
  mb: 2,
  border: '1px solid #FEDF89',
  backgroundColor: '#FFFAEB',
  borderRadius: '0.75rem',
}}>
```

---

## Clickable Card Filter Pattern

Used in Exception Hub and Task Manager. Cards act as filters for a table below.

```jsx
const [activeCard, setActiveCard] = useState(null);

const handleCardClick = (key) => {
  setActiveCard(activeCard === key ? null : key);
};

// In the card:
const isSelected = activeCard === card.key;
// border: isSelected ? `2px solid ${color}` : '1px solid #EAECF0'
// backgroundColor: isSelected ? `${color}08` : '#fff'

// Show active filter chip:
{activeCard && (
  <Chip
    label={`Filtered: ${label} (${count})`}
    onDelete={() => setActiveCard(null)}
    color="primary" size="small"
  />
)}

// Filter table data:
const filtered = useMemo(() => {
  let data = allData;
  if (activeCard) {
    data = data.filter((item) => item.status === cardStatusMap[activeCard]);
  }
  return data;
}, [allData, activeCard]);
```

---

## Dropdown / Select Pattern

When building filters or form controls requiring standard dropdowns, **ALWAYS use the custom shared `DropdownSelect` component** (`src/shared/components/Forms/Dropdowns/DropdownSelect.js`).

For filter cards or inline layouts, use the `labelAlignment="left"` prop to place the label horizontally next to the input. This prevents the label text from becoming tiny and squished at the top of the input box:

```jsx
import DropdownSelect from '../../shared/components/Forms/Dropdowns/DropdownSelect';

<DropdownSelect
  labelAlignment="left"
  label="Domain"
  value={filter}
  options={[
    { id: 'ALL', label: 'All' },
    { id: 'FRAUD', label: 'Fraud' },
    { id: 'RVM_FLEET', label: 'RVM Fleet' }
  ]}
  onChange={(op) => setFilter(op ? op.id : 'ALL')}
  containerStyle={{ minWidth: 200 }}
  disableClearBtn
/>
```

Do NOT use standard Material `TextField select` or `FormControl + Select` directly, as their default floating labels break styling consistency, shrink text too small, or clip with the portal theme:

```jsx
// AVOID: Very small stacked/floating label
<TextField select size="small" label="Domain" />

// AVOID: Label clipping
<FormControl size="small">
  <InputLabel>Domain</InputLabel>
  <Select value={filter} label="Domain" onChange={...}>
    <MenuItem value="ALL">All</MenuItem>
  </Select>
</FormControl>
```

Exception: `FormControl` + `InputLabel` + `Select` is acceptable inside Dialogs where full-width layout prevents clipping.

---

## Table Styling

Tables inherit from theme (`src/theme/table.styles.js`):

| Element | Style |
|---------|-------|
| Head cell bg | #F2F4F7 |
| Head cell text | #475467, weight 500, 12px |
| Head cell height | 2.75rem (44px) |
| Body cell | 14px, padding 6px 16px, height 3.75rem |
| Row hover | #FCF3DF |
| Border color | #EAECF0 |

---

## Button Styling

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| contained | primary.main | white | none |
| outlined | white | #344054 | 1px solid #D0D5DD |
| text | transparent | primary.main | none |

Common props:
- `fontWeight: 600`
- `borderRadius: 0.57rem (8px)`
- `textTransform: capitalize`
- No elevation (shadows disabled)

---

## Form Inputs

- Height: 2.75rem (44px)
- Border-radius: 0.57rem (8px)
- Border: 1px solid #D0D5DD
- Box-shadow: 0px 1px 2px 0px rgba(16, 24, 40, 0.05)
- Label: weight 500, 0.857rem, color #344054
- Disabled bg: #F0F3F6

---

## Grid Layouts

### Dashboard — 4-column metrics (large cards)
```jsx
<Grid container spacing={2}>
  <Grid item xs={12} sm={6} md={3}>
    <SummaryCard />
  </Grid>
</Grid>
```

### Dashboard — auto-width columns (compact cards)
```jsx
<Grid container spacing={2}>
  <Grid item xs={6} sm={3} md>
    <CompactMetricCard />
  </Grid>
</Grid>
```

### Dashboard — 3-column metrics
```jsx
<Grid container spacing={2}>
  <Grid item xs={12} sm={4}>
    <SummaryCard />
  </Grid>
</Grid>
```

### Content with sidebar
```jsx
<Grid container spacing={2}>
  <Grid container item xs={9} rowGap={2} columnSpacing={2}>
    {/* Main */}
  </Grid>
  <Grid container item xs={3} rowGap={2}>
    {/* Sidebar */}
  </Grid>
</Grid>
```

---

## Section Headers

```jsx
<Typography
  variant="overline"
  sx={{ color: '#475467', fontWeight: 500, mb: 1, display: 'block', fontSize: '0.857rem' }}
>
  SECTION TITLE
</Typography>
```

---

## Shadows

| Usage | Value |
|-------|-------|
| Standard card | `0px 1px 2px 0px rgba(16, 24, 40, 0.05)` |
| Hover/elevated | `0px 4px 12px rgba(0, 0, 0, 0.08)` |
| Compact card hover | `0 2px 8px rgba(0,0,0,0.08)` |
| Form inputs | `0px 1px 2px 0px rgba(16, 24, 40, 0.05)` |

---

## Domain / Enum Values

When building dropdowns or filters, use these values to match backend enums.

### Exception Domains
`RVM_FLEET`, `COLLECTIONS`, `FINANCE`, `COMPLIANCE`, `DISPUTES`, `FRAUD`, `RETAILER_OPS`

### Exception Severity
`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`

### Exception Status
`OPEN`, `ACKNOWLEDGED`, `ASSIGNED`, `IN_PROGRESS`, `PARTIALLY_RESOLVED`, `RESOLVED`, `ESCALATED`, `CLOSED`

### Task Status
`OPEN`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `OVERDUE`, `CANCELLED`

### Task Types
`EXCEPTION_RESOLUTION`, `APPROVAL`, `REVIEW`, `INVESTIGATION`, `FOLLOW_UP`, `GENERAL`, `ACTION`, `RESPONSE`, `REPORT`

### Notification Severity
`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `WARNING`, `INFO`

### Notification Status
`UNREAD`, `READ`, `ACKNOWLEDGED`, `SNOOZED`, `DELEGATED`, `DISMISSED`

---

## RTK Query — Operations Centre API

API file: `src/redux/operationsCentre/opsCentre.api.js`

Key settings:
- `keepUnusedDataFor: 0` — no caching, data dropped on unmount
- `refetchOnMountOrArgChange: true` — fresh API call on every page navigation
- Base URL: `process.env.REACT_APP_OPS_CENTRE_URL || 'http://localhost:8096'`
- Service prefix: `/api/v1`

---

## Shared Components

| Component | Path | Usage |
|-----------|------|-------|
| PageContainer | `src/shared/components/PageContainer.js` | Page wrapper |
| PageHeader | `src/shared/components/PageHeader.js` | Page title bar |
| PageContent | `src/shared/components/PageContent.js` | Content Paper wrapper |
| AppChip | `src/shared/components/AppChip.js` | Styled chip |
| AppCard | `src/shared/components/AppCard.js` | Card wrapper |
| CanShow | `src/shared/components/CanShow.js` | Conditional rendering |
| Loader | `src/shared/components/Loader.js` | Loading spinner |
| DashCard | `src/pages/Dashboard/components/DashCard.js` | Dashboard card with header |
| DashSection | `src/pages/Dashboard/components/DashSection.js` | Dashboard section with title + divider |

---

## Do / Do Not

**Do:**
- Use `PageContainer sx={{ pt: 0 }}` + `PageHeader` + `PageContent sx={{ p: 2, top: 20 }}` on every page.
- Use `variant="outlined"` on Cards (or `elevation={0}` for compact cards).
- Use `DropdownSelect` with `labelAlignment="left"` for filter dropdowns to ensure legible side-by-side labels.
- Use theme color tokens instead of hardcoded hex.
- Use `spacing={2}` for Grid containers.
- Use `0.75rem` border-radius on large cards, `borderRadius: 2` on compact cards.
- Use `#EAECF0` for borders and dividers.
- Use `#475467` for section headers and table heads.
- Use `#101828` for primary text, `#667085` for muted text.
- Use compact card pattern (p: 2.5, horizontal layout) for clickable metric filters.
- Use large card pattern (p: 1.71rem, vertical layout) for dashboard KPI summaries.

**Do Not:**
- Wrap `PageHeader` in any parent component like `<Stack>` or `<Box>` (this breaks the full screen bleed width calculations).
- Use custom Box wrappers instead of PageContainer/PageContent.
- Use standard `TextField select` or `FormControl + InputLabel` for dropdowns (causes tiny squished floating labels or clipping).
- Use `spacing={3}` (portal standard is 2).
- Use hardcoded colors like `#6B7280`, `#9CA3AF`, `#111827` — use `#475467`, `#667085`, `#101828`.
- Add box-shadow to cards manually (theme handles it)
- Use `variant="elevation"` on cards
- Mix card patterns — use compact for filters, large for KPI summaries
