import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import DownloadIcon from '@mui/icons-material/DownloadOutlined';
import GroupsOutlinedIcon from '@mui/icons-material/GroupsOutlined';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Box, Button, Card, Grid, Typography } from '@mui/material';
import heroImage from '../assets/hero-family.jpg';
import BrandMark from '../components/BrandMark.jsx';
import Reveal from '../components/Reveal.jsx';

// Samvitta design tokens (see theme/theme.js `tokens` for the shared version).
const C = {
  midnight: '#15171C',
  navy: '#20242D',
  ivory: '#F5F1E8',
  card: '#FBFAF7',
  champagne: '#C8A76A',
  amber: '#D99A3C',
  ink: '#18191C',
  warmGray: '#77736C',
  stone: '#DDD7CD',
  coral: '#D96767',
  indigo: '#6F78C9',
  mutedBlue: '#5E83A9',
};

const serif = '"Instrument Serif", Georgia, serif';

const NAV_LINKS = [
  { label: 'Product', href: '#household' },
  { label: 'Intelligence', href: '#intelligence' },
  { label: 'Family', href: '#family' },
  { label: 'Privacy', href: '#privacy' },
];

function Eyebrow({ children, dark = false }) {
  return (
    <Typography
      sx={{
        fontSize: '0.8125rem',
        fontWeight: 600,
        color: dark ? C.champagne : '#9A8452',
        textTransform: 'uppercase',
        letterSpacing: '0.14em',
        mb: 1.5,
      }}
    >
      {children}
    </Typography>
  );
}

function SectionShell({ id, bgcolor, children, py }) {
  return (
    <Box id={id} sx={{ bgcolor: bgcolor || C.ivory, px: { xs: 2.5, md: 6 }, py: py || { xs: 8, md: 12 } }}>
      <Box sx={{ maxWidth: 1160, mx: 'auto' }}>{children}</Box>
    </Box>
  );
}

// ── Intelligence mark — distinguishes Samvitta's interpretation from raw data.
function InsightMark({ color = C.champagne, size = 18 }) {
  return <Box component="span" sx={{ color, fontSize: size, lineHeight: 1, mr: 1 }}>✦</Box>;
}

function StatCell({ value, label, border = true }) {
  return (
    <Box sx={{ borderLeft: border ? `1px solid ${C.stone}` : 'none', pl: border ? { xs: 1.5, sm: 2.5 } : 0, flex: 1 }}>
      <Typography sx={{ fontSize: { xs: '1.125rem', sm: '1.375rem' }, fontWeight: 700, color: C.ink, lineHeight: 1.1 }}>
        {value}
      </Typography>
      <Typography sx={{ fontSize: '0.6875rem', color: C.warmGray, mt: 0.25, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{label}</Typography>
    </Box>
  );
}

// ── The one floating card in the hero — Household Overview + a single insight.
function HouseholdOverviewCard() {
  return (
    <Card
      variant="outlined"
      sx={{
        width: '100%',
        maxWidth: 720,
        borderRadius: '1.125rem',
        bgcolor: 'rgba(250,247,240,0.94)',
        backdropFilter: 'blur(14px)',
        border: '1px solid rgba(255,255,255,0.4)',
        boxShadow: '0px 20px 48px rgba(0,0,0,0.32)',
        px: { xs: 2.5, sm: 3.5 },
        py: { xs: 2, sm: 2.5 },
      }}
    >
      <Typography sx={{ fontSize: '0.6875rem', fontWeight: 700, color: C.warmGray, textTransform: 'uppercase', letterSpacing: '0.1em', mb: 1.5 }}>
        Household Overview
      </Typography>
      <Box sx={{ display: 'flex', gap: { xs: 1.5, sm: 2.5 }, mb: 1.75 }}>
        <StatCell value="₹2,48,500" label="Balance" border={false} />
        <StatCell value="₹67,320" label="Spending" />
        <StatCell value="28%" label="Savings" />
      </Box>
      <Box sx={{ borderTop: `1px solid ${C.stone}`, pt: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <InsightMark color={C.champagne} size={15} />
          <Typography sx={{ fontSize: '0.8125rem', color: C.ink }}>
            <Box component="span" sx={{ fontWeight: 700 }}>Dining</Box> is 12% above your average
          </Typography>
        </Box>
        <ArrowForwardIcon sx={{ fontSize: 16, color: C.warmGray, flexShrink: 0 }} />
      </Box>
    </Card>
  );
}

function IntelligenceCard({ eyebrow, title, value, sub, delay = 0 }) {
  return (
    <Reveal delay={delay} y={20}>
      <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.card, borderColor: C.stone, height: '100%', p: 3 }}>
        <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: C.indigo, textTransform: 'uppercase', letterSpacing: '0.1em', mb: 2 }}>
          {eyebrow}
        </Typography>
        <Typography sx={{ fontFamily: serif, fontSize: '1.75rem', color: C.ink, mb: 0.5, lineHeight: 1.15 }}>{title}</Typography>
        {sub && <Typography sx={{ fontSize: '0.875rem', color: C.warmGray, lineHeight: 1.6 }}>{sub}</Typography>}
        {value && (
          <Box sx={{ mt: 2.5, pt: 2, borderTop: `1px solid ${C.stone}` }}>
            {value.map((row) => (
              <Box key={row.label} sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.75 }}>
                <Typography sx={{ fontSize: '0.8125rem', color: C.warmGray }}>{row.label}</Typography>
                <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700, color: C.ink }}>{row.amount}</Typography>
              </Box>
            ))}
          </Box>
        )}
      </Card>
    </Reveal>
  );
}

function ChatRow({ align, children }) {
  const isAsk = align === 'right';
  return (
    <Box sx={{ display: 'flex', justifyContent: isAsk ? 'flex-end' : 'flex-start' }}>
      <Box
        sx={{
          maxWidth: 480,
          bgcolor: isAsk ? C.midnight : C.ivory,
          color: isAsk ? '#FFFFFF' : C.ink,
          border: isAsk ? 'none' : `1px solid ${C.stone}`,
          borderRadius: '14px',
          px: 2.5,
          py: 1.75,
        }}
      >
        {children}
      </Box>
    </Box>
  );
}

// ── Editorial trend chart — thin gridline, one annotated line, a callout.
function TrendChart() {
  const months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];
  return (
    <Box>
      <Box component="svg" viewBox="0 0 600 220" sx={{ width: '100%', height: 220, display: 'block' }}>
        {[40, 100, 160].map((y) => (
          <line key={y} x1="0" y1={y} x2="600" y2={y} stroke={C.stone} strokeWidth="1" />
        ))}
        <path
          d="M0,150 L100,130 L200,140 L300,95 L400,70 L500,30 L580,18"
          fill="none"
          stroke={C.champagne}
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="580" cy="18" r="5" fill={C.amber} />
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', px: 0.5, mb: 1 }}>
        {months.map((m) => (
          <Typography key={m} sx={{ fontSize: '0.75rem', color: C.warmGray }}>{m}</Typography>
        ))}
      </Box>
      <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: '#4F9D6E' }}>↑ 8.2% vs last month</Typography>
    </Box>
  );
}

export default function Landing({ onGetStarted }) {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: C.ivory, display: 'flex', flexDirection: 'column' }}>
      {/* ── Hero — full-bleed cinematic photo, transparent nav, centered
          wordmark, one floating card near the bottom edge. */}
      <Box sx={{ position: 'relative', minHeight: { xs: '100vh', md: '92vh' }, display: 'flex', flexDirection: 'column', overflow: 'hidden', bgcolor: '#08111C' }}>
        {/* Blurred, darkened backdrop — the same photo stretched full-bleed so
            there's no empty margin, but blurred enough that the distortion
            from stretching a portrait crop this wide doesn't read. */}
        <Box
          sx={{
            position: 'absolute',
            inset: -40,
            backgroundImage: `url(${heroImage})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center 20%',
            filter: 'blur(50px) brightness(0.5) saturate(0.85)',
            transform: 'scale(1.1)',
          }}
        />
        {/* The real, undistorted photo — centered at its natural aspect
            ratio so the family reads clearly, not stretched to fill width. */}
        <Box
          component="img"
          src={heroImage}
          alt=""
          sx={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: '50%',
            transform: 'translateX(-50%)',
            height: '100%',
            width: 'auto',
            maxWidth: 'none',
            objectFit: 'cover',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(180deg, rgba(8,15,27,0.55) 0%, rgba(8,15,27,0.15) 22%, rgba(8,15,27,0.15) 60%, rgba(8,15,27,0.7) 100%)',
          }}
        />
        <Box sx={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 60% 55% at 50% 40%, rgba(8,15,27,0.45) 0%, rgba(8,15,27,0.72) 100%)' }} />

        {/* Nav — transparent, floats directly over the photo */}
        <Box sx={{ position: 'relative', zIndex: 2, px: { xs: 2.5, md: 6 }, py: { xs: 2.5, md: 3.5 }, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
            <BrandMark size={40} />
            <Typography sx={{ fontFamily: serif, fontSize: 24, color: '#FFFFFF', letterSpacing: '0.01em' }}>Samvitta</Typography>
          </Box>
          <Box sx={{ display: { xs: 'none', lg: 'flex' }, alignItems: 'center', gap: 4 }}>
            {NAV_LINKS.map((link) => (
              <Typography
                key={link.label}
                component="a"
                href={link.href}
                sx={{ fontSize: '0.875rem', fontWeight: 500, color: 'rgba(255,255,255,0.78)', textDecoration: 'none', '&:hover': { color: '#FFFFFF' } }}
              >
                {link.label}
              </Typography>
            ))}
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography
              component="a"
              onClick={() => onGetStarted(0)}
              sx={{ fontSize: '0.875rem', fontWeight: 500, color: 'rgba(255,255,255,0.85)', cursor: 'pointer', display: { xs: 'none', sm: 'block' } }}
            >
              Sign in
            </Typography>
            <Button
              variant="contained"
              onClick={() => onGetStarted(1)}
              sx={{ bgcolor: C.champagne, color: C.ink, '&:hover': { bgcolor: '#B79457' } }}
            >
              Get started
            </Button>
          </Box>
        </Box>

        {/* Hero copy — centered, minimal, lets the image and wordmark carry it */}
        <Box sx={{ position: 'relative', zIndex: 2, flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', px: { xs: 2.5, md: 6 } }}>
          <Reveal>
            <Typography
              sx={{
                fontFamily: serif,
                fontSize: { xs: 64, sm: 88, md: 112 },
                lineHeight: 1,
                color: '#FFFFFF',
                mb: { xs: 2, md: 2.5 },
              }}
            >
              Samvitta
            </Typography>
          </Reveal>
          <Reveal delay={0.1}>
            <Typography
              sx={{
                fontSize: { xs: 17, sm: 19, md: 21 },
                fontWeight: 500,
                lineHeight: 1.4,
                color: 'rgba(255,255,255,0.9)',
                maxWidth: 560,
                mb: 1.5,
              }}
            >
              Smart Financial Analytics for the Whole Family
            </Typography>
          </Reveal>
          <Reveal delay={0.18}>
            <Typography sx={{ fontSize: '1rem', color: 'rgba(255,255,255,0.62)', lineHeight: 1.6, maxWidth: 460, mb: 4 }}>
              Understand your household money. Know what changed. See what comes next.
            </Typography>
          </Reveal>
          <Reveal delay={0.26}>
            <Button
              variant="contained"
              size="large"
              onClick={() => onGetStarted(1)}
              sx={{ px: 4.5, bgcolor: C.champagne, color: C.ink, '&:hover': { bgcolor: '#B79457' } }}
            >
              Explore Samvitta
            </Button>
          </Reveal>
        </Box>

        {/* The one floating card */}
        <Box sx={{ position: 'relative', zIndex: 2, display: 'flex', justifyContent: 'center', px: 2.5, pb: { xs: 4, md: 5.5 } }}>
          <Reveal delay={0.35} y={24}>
            <HouseholdOverviewCard />
          </Reveal>
        </Box>
      </Box>

      {/* ── Household View */}
      <SectionShell id="household">
        <Reveal>
          <Eyebrow>Household View</Eyebrow>
          <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 44 }, color: C.ink, lineHeight: 1.15, mb: 2, maxWidth: 640 }}>
            See your family's finances as one picture.
          </Typography>
          <Typography sx={{ fontSize: '1.0625rem', color: C.warmGray, lineHeight: 1.7, maxWidth: 560, mb: 6 }}>
            Income, expenses, balance, savings, and household activity — brought together in one shared view, instead
            of scattered across statements and spreadsheets.
          </Typography>
        </Reveal>
        <Grid container spacing={2.5}>
          <Grid item xs={12} md={7}>
            <Reveal delay={0.05} y={20}>
              <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.midnight, border: 'none', p: 4, height: '100%' }}>
                <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.1em', mb: 1.5 }}>
                  Household Balance
                </Typography>
                <Typography sx={{ fontFamily: serif, fontSize: { xs: 36, md: 48 }, color: '#FFFFFF', mb: 1 }}>₹2,48,500</Typography>
                <Typography sx={{ fontSize: '0.9375rem', color: C.champagne, fontWeight: 600 }}>+₹18,400 this month</Typography>
              </Card>
            </Reveal>
          </Grid>
          <Grid item xs={6} md={2.5}>
            <Reveal delay={0.12} y={20}>
              <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.card, borderColor: C.stone, p: 3, height: '100%' }}>
                <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: C.warmGray, textTransform: 'uppercase', letterSpacing: '0.08em', mb: 1.5 }}>
                  Spending
                </Typography>
                <Typography sx={{ fontFamily: serif, fontSize: 30, color: C.ink }}>₹67,320</Typography>
              </Card>
            </Reveal>
          </Grid>
          <Grid item xs={6} md={2.5}>
            <Reveal delay={0.18} y={20}>
              <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.card, borderColor: C.stone, p: 3, height: '100%' }}>
                <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: C.warmGray, textTransform: 'uppercase', letterSpacing: '0.08em', mb: 1.5 }}>
                  Savings Rate
                </Typography>
                <Typography sx={{ fontFamily: serif, fontSize: 30, color: C.ink }}>28%</Typography>
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* ── Intelligence */}
      <SectionShell id="intelligence" bgcolor={C.navy}>
        <Reveal>
          <Eyebrow dark>Intelligence</Eyebrow>
          <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 44 }, color: '#FFFFFF', lineHeight: 1.2, mb: 2, maxWidth: 640 }}>
            Your numbers tell a story. Samvitta helps you understand it.
          </Typography>
          <Typography sx={{ fontSize: '1.0625rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.7, maxWidth: 560, mb: 6 }}>
            Not another chart to read — an explanation of what changed and why, in plain language.
          </Typography>
        </Reveal>
        <Grid container spacing={2.5}>
          <Grid item xs={12} md={4}>
            <IntelligenceCard
              eyebrow="Unusual spending"
              title="Dining is 23% higher than your 3-month average."
              value={[
                { label: 'This month', amount: '₹8,400' },
                { label: 'Typical', amount: '₹6,820' },
              ]}
              delay={0}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <IntelligenceCard
              eyebrow="Month-end forecast"
              title="Estimated savings: ₹18,400"
              sub="Based on your current income and spending pattern."
              delay={0.1}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <IntelligenceCard
              eyebrow="Recurring change"
              title="Subscriptions are up ₹1,260 over 4 months."
              sub="Samvitta tracks recurring charges so quiet increases don't go unnoticed."
              delay={0.2}
            />
          </Grid>
        </Grid>
      </SectionShell>

      {/* ── Ask Samvitta */}
      <SectionShell bgcolor="#FFFFFF">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={5}>
            <Reveal>
              <Eyebrow>Ask Samvitta</Eyebrow>
              <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 40 }, color: C.ink, lineHeight: 1.2, mb: 2.5 }}>
                Ask your finances.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: C.warmGray, lineHeight: 1.7, mb: 2 }}>
                Skip the dashboard-hunting. Ask a plain question and get a household-specific answer, with the numbers
                behind it.
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {['Can we afford a ₹1 lakh vacation in December?', 'What subscriptions are recurring?', 'Are we likely to exceed our budget?'].map((q) => (
                  <Typography key={q} sx={{ fontSize: '0.875rem', color: C.warmGray, '&::before': { content: '"— "', color: C.champagne } }}>
                    {q}
                  </Typography>
                ))}
              </Box>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={7}>
            <Reveal delay={0.12} y={20}>
              <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.ivory, borderColor: C.stone, p: { xs: 2.5, sm: 3.5 } }}>
                <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: C.warmGray, textTransform: 'uppercase', letterSpacing: '0.1em', mb: 2.5 }}>
                  Ask Samvitta
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <ChatRow align="right">
                    <Typography sx={{ fontSize: '0.9375rem' }}>"Why did we spend more this month?"</Typography>
                  </ChatRow>
                  <ChatRow align="left">
                    <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, mb: 1 }}>
                      Your household spending increased by ₹8,420.
                    </Typography>
                    <Box sx={{ mb: 1 }}>
                      {[
                        { label: 'Dining', amount: '+₹3,100' },
                        { label: 'Shopping', amount: '+₹2,450' },
                        { label: 'Utilities', amount: '+₹1,320' },
                      ].map((row) => (
                        <Box key={row.label} sx={{ display: 'flex', justifyContent: 'space-between', maxWidth: 280 }}>
                          <Typography sx={{ fontSize: '0.875rem', color: C.warmGray }}>{row.label}</Typography>
                          <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: C.coral }}>{row.amount}</Typography>
                        </Box>
                      ))}
                    </Box>
                    <Typography sx={{ fontSize: '0.8125rem', color: C.warmGray }}>
                      Dining is also 18% above your 3-month average.
                    </Typography>
                  </ChatRow>
                </Box>
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* ── Family */}
      <SectionShell id="family">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Reveal>
              <Eyebrow>Family</Eyebrow>
              <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 40 }, color: C.ink, lineHeight: 1.2, mb: 2.5 }}>
                Plan together, not around each other.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: C.warmGray, lineHeight: 1.7, mb: 2 }}>
                Create a private household space and invite the people you manage money with. Everyone logs their own
                spending; the household sees one shared, accurate picture.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: C.ink }}>
                Everyone contributes. Everyone stays informed.
              </Typography>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={6}>
            <Reveal delay={0.12} y={20}>
              <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.card, borderColor: C.stone, p: 3.5 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  {['S', 'V'].map((initial, i) => (
                    <Box
                      key={initial}
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        bgcolor: i === 0 ? C.midnight : C.champagne,
                        color: i === 0 ? C.champagne : C.ink,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 700,
                        ml: i === 0 ? 0 : -1.25,
                        border: '2px solid #FBFAF7',
                      }}
                    >
                      {initial}
                    </Box>
                  ))}
                  <Box sx={{ width: 40, height: 40, borderRadius: '50%', border: `1px dashed ${C.stone}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: C.warmGray, ml: -1.25, fontSize: 18 }}>
                    +
                  </Box>
                </Box>
                <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: C.warmGray, textTransform: 'uppercase', letterSpacing: '0.08em', mb: 1.5 }}>
                  Household
                </Typography>
                {['Everyone', 'Sanket', 'Vaishnavi'].map((name, i) => (
                  <Box key={name} sx={{ display: 'flex', alignItems: 'center', gap: 1.25, py: 1, borderBottom: i < 2 ? `1px solid ${C.stone}` : 'none' }}>
                    <Box sx={{ width: 16, height: 16, borderRadius: '50%', border: `1.5px solid ${i === 0 ? C.champagne : C.stone}`, bgcolor: i === 0 ? C.champagne : 'transparent', flexShrink: 0 }} />
                    <Typography sx={{ fontSize: '0.9375rem', color: C.ink, fontWeight: i === 0 ? 600 : 400 }}>{name}</Typography>
                  </Box>
                ))}
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* ── Financial Story */}
      <SectionShell bgcolor="#FFFFFF">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={5}>
            <Reveal>
              <Eyebrow>Financial Story</Eyebrow>
              <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 40 }, color: C.ink, lineHeight: 1.2, mb: 2.5 }}>
                Patterns, not just numbers.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: C.warmGray, lineHeight: 1.7 }}>
                See how household spending moves month over month, and which categories are driving the change —
                without building a single chart yourself.
              </Typography>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={7}>
            <Reveal delay={0.12} y={20}>
              <Card variant="outlined" sx={{ borderRadius: '1.25rem', bgcolor: C.ivory, borderColor: C.stone, p: 3.5 }}>
                <Typography sx={{ fontSize: '0.75rem', fontWeight: 700, color: C.warmGray, textTransform: 'uppercase', letterSpacing: '0.1em', mb: 2 }}>
                  Monthly Spending
                </Typography>
                <TrendChart />
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* ── Privacy */}
      <SectionShell id="privacy">
        <Reveal>
          <Box sx={{ textAlign: 'center', maxWidth: 620, mx: 'auto', mb: 6 }}>
            <Eyebrow>Privacy</Eyebrow>
            <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 40 }, color: C.ink, lineHeight: 1.2 }}>
              Your family's financial data stays yours.
            </Typography>
          </Box>
        </Reveal>
        <Grid container spacing={3}>
          {[
            { icon: LockOutlinedIcon, title: 'Private by design', desc: 'Financial data stays private to your household — never shared or shown across workspaces.' },
            { icon: GroupsOutlinedIcon, title: 'Controlled family access', desc: 'You decide who joins your household and what they can see.' },
            { icon: DownloadIcon, title: 'Export when you want', desc: 'View, export, or delete your records whenever you want. Nothing is locked away.' },
          ].map((pillar, index) => {
            const Icon = pillar.icon;
            return (
              <Grid item xs={12} sm={4} key={pillar.title}>
                <Reveal delay={index * 0.08}>
                  <Box sx={{ textAlign: 'center', px: 2 }}>
                    <Icon sx={{ fontSize: 26, color: C.champagne, mb: 1.5 }} />
                    <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: C.ink, mb: 0.75 }}>{pillar.title}</Typography>
                    <Typography sx={{ fontSize: '0.9375rem', color: C.warmGray, lineHeight: 1.6 }}>{pillar.desc}</Typography>
                  </Box>
                </Reveal>
              </Grid>
            );
          })}
        </Grid>
      </SectionShell>

      {/* ── Final CTA */}
      <SectionShell bgcolor={C.midnight}>
        <Reveal>
          <Box sx={{ textAlign: 'center', maxWidth: 640, mx: 'auto' }}>
            <Typography sx={{ fontFamily: serif, fontSize: { xs: 32, md: 44 }, color: '#FFFFFF', lineHeight: 1.2, mb: 2.5 }}>
              Plan together. Make better money decisions as a family.
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', color: 'rgba(255,255,255,0.65)', lineHeight: 1.7, mb: 4 }}>
              See where your money goes. Understand what changed. Know what's coming next.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => onGetStarted(1)}
              sx={{ px: 5, bgcolor: C.champagne, color: C.ink, '&:hover': { bgcolor: '#BE9A5A' } }}
            >
              Create your household
            </Button>
          </Box>
        </Reveal>
      </SectionShell>

      {/* Footer */}
      <Box sx={{ px: { xs: 2.5, md: 6 }, py: 4, borderTop: `1px solid ${C.stone}`, bgcolor: C.ivory }}>
        <Box sx={{ maxWidth: 1160, mx: 'auto', display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2 }}>
          <Box>
            <Typography sx={{ fontFamily: serif, fontSize: '1.25rem', color: C.ink }}>Samvitta</Typography>
            <Typography sx={{ fontSize: '0.8125rem', color: C.warmGray, mt: 0.5 }}>
              Smart financial analytics for the whole family.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 3 }}>
            {NAV_LINKS.map((link) => (
              <Typography
                key={link.label}
                component="a"
                href={link.href}
                sx={{ fontSize: '0.8125rem', color: C.warmGray, textDecoration: 'none', '&:hover': { color: C.ink } }}
              >
                {link.label}
              </Typography>
            ))}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
