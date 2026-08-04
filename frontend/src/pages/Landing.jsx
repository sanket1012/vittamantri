import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import BarChartIcon from '@mui/icons-material/BarChart';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import GroupsIcon from '@mui/icons-material/Groups';
import LockIcon from '@mui/icons-material/Lock';
import TelegramIcon from '@mui/icons-material/Telegram';
import { Box, Button, Card, CardContent, Grid, Typography } from '@mui/material';
import BrandMark from '../components/BrandMark.jsx';
import Reveal from '../components/Reveal.jsx';

const cardHoverSx = {
  transition: 'transform 220ms ease, box-shadow 220ms ease',
  '&:hover': { transform: 'translateY(-4px)', boxShadow: '0px 12px 28px rgba(23,63,53,0.12)' },
};

const NAV_LINKS = [
  { label: 'Overview', href: '#overview' },
  { label: 'How it works', href: '#how-it-works' },
  { label: 'Analytics', href: '#analytics' },
  { label: 'Privacy', href: '#privacy' },
];

const COMPARISON_ROWS = [
  { old: 'Open a spreadsheet', vitta: 'Send a message' },
  { old: 'Manually enter rows', vitta: 'Natural-language logging' },
  { old: 'Remember categories', vitta: 'Automatic categorization' },
  { old: 'Share files', vitta: 'Shared household workspace' },
  { old: 'Build charts manually', vitta: 'Ready-to-use analytics' },
  { old: 'Reconcile who paid', vitta: 'Member-level history' },
];

function Eyebrow({ children }) {
  return (
    <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, color: '#173F35', textTransform: 'uppercase', letterSpacing: '0.06em', mb: 1.5 }}>
      {children}
    </Typography>
  );
}

function SectionShell({ id, bgcolor, children }) {
  return (
    <Box id={id} sx={{ bgcolor: bgcolor || 'transparent', px: { xs: 2.5, md: 6 }, py: { xs: 7, md: 9 } }}>
      <Box sx={{ maxWidth: 1100, mx: 'auto' }}>{children}</Box>
    </Box>
  );
}

function ChatBubble({ children, align = 'left' }) {
  return (
    <Box
      sx={{
        alignSelf: align === 'left' ? 'flex-start' : 'flex-end',
        bgcolor: align === 'left' ? '#FFFFFF' : '#173F35',
        color: align === 'left' ? '#202421' : '#FFFFFF',
        border: align === 'left' ? '1px solid #E2DCC9' : 'none',
        borderRadius: '14px',
        px: 2.25,
        py: 1.25,
        fontSize: '0.9375rem',
        fontWeight: 500,
        maxWidth: 320,
      }}
    >
      {children}
    </Box>
  );
}

export default function Landing({ onGetStarted }) {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: '#F6F1E7', display: 'flex', flexDirection: 'column' }}>
      {/* Nav */}
      <Box sx={{ px: { xs: 2.5, md: 6 }, py: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #E2DCC9', position: 'sticky', top: 0, bgcolor: '#F6F1E7', zIndex: 10 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <BrandMark size={40} radius="10px" />
          <Typography sx={{ fontSize: 18, fontWeight: 700, color: '#202421' }}>वित्तमंत्री</Typography>
        </Box>
        <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center', gap: 3.5 }}>
          {NAV_LINKS.map((link) => (
            <Typography
              key={link.label}
              component="a"
              href={link.href}
              sx={{ fontSize: '0.9375rem', fontWeight: 500, color: '#454940', textDecoration: 'none', '&:hover': { color: '#173F35' } }}
            >
              {link.label}
            </Typography>
          ))}
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5 }}>
          <Button variant="outlined" onClick={() => onGetStarted(0)}>
            Login
          </Button>
          <Button variant="contained" onClick={() => onGetStarted(1)} sx={{ display: { xs: 'none', sm: 'inline-flex' } }}>
            Get started
          </Button>
        </Box>
      </Box>

      {/* 1. Hero */}
      <SectionShell id="overview">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Reveal>
              <Eyebrow>Family finance, made simple</Eyebrow>
              <Typography sx={{ fontSize: { xs: 32, md: 46 }, fontWeight: 700, color: '#202421', lineHeight: 1.15, mb: 2.5 }}>
                Your family's money, finally in one place.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.7, mb: 3 }}>
                वित्तमंत्री helps your household track everyday spending, understand where the money goes, and manage
                finances together — without maintaining another spreadsheet. Log expenses simply by messaging the
                Telegram bot in natural language.
              </Typography>
              <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap', mb: 3 }}>
                <Button variant="contained" size="large" onClick={() => onGetStarted(1)} sx={{ px: 4 }}>
                  Start tracking
                </Button>
                <Button variant="outlined" size="large" component="a" href="#how-it-works" sx={{ px: 4 }}>
                  See how it works
                </Button>
              </Box>
              <Typography sx={{ fontSize: '0.875rem', color: '#6B6F63', fontWeight: 500 }}>
                Simple to use. Built for families. Private by design.
              </Typography>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={6}>
            <Reveal delay={0.1} y={28}>
              <Card variant="outlined" sx={{ borderRadius: '1rem', p: 3, bgcolor: '#FFFFFF', ...cardHoverSx }}>
                <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, color: '#6B6F63', textTransform: 'uppercase', letterSpacing: '0.05em', mb: 2 }}>
                  Telegram message
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25, mb: 3 }}>
                  <Reveal delay={0.5} y={10} duration={0.4}>
                    <ChatBubble align="right">₹450 groceries at Dmart</ChatBubble>
                  </Reveal>
                </Box>
                <Reveal delay={1.1} y={10} duration={0.4}>
                  <Box sx={{ borderTop: '1px dashed #E2DCC9', pt: 2.5, mb: 2.5 }}>
                    <Typography sx={{ fontSize: '0.8125rem', fontWeight: 600, color: '#6B6F63', textTransform: 'uppercase', letterSpacing: '0.05em', mb: 1.5 }}>
                      Transaction recognized
                    </Typography>
                    <Box sx={{ bgcolor: '#E6EFEA', borderRadius: '0.75rem', p: 2.25, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                      <Box>
                        <Typography sx={{ fontSize: '0.75rem', color: '#6B6F63' }}>Amount</Typography>
                        <Typography sx={{ fontSize: '1.125rem', fontWeight: 700, color: '#173F35' }}>₹450</Typography>
                      </Box>
                      <Box>
                        <Typography sx={{ fontSize: '0.75rem', color: '#6B6F63' }}>Category</Typography>
                        <Typography sx={{ fontSize: '1.125rem', fontWeight: 700, color: '#202421' }}>Groceries</Typography>
                      </Box>
                      <Box>
                        <Typography sx={{ fontSize: '0.75rem', color: '#6B6F63' }}>Merchant</Typography>
                        <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: '#202421' }}>Dmart</Typography>
                      </Box>
                      <Box>
                        <Typography sx={{ fontSize: '0.75rem', color: '#6B6F63' }}>Date</Typography>
                        <Typography sx={{ fontSize: '0.9375rem', fontWeight: 600, color: '#202421' }}>Today</Typography>
                      </Box>
                    </Box>
                  </Box>
                </Reveal>
                <Reveal delay={1.7} y={8} duration={0.4}>
                  <Typography sx={{ fontSize: '0.9375rem', color: '#454940', fontWeight: 500 }}>
                    वित्तमंत्री understands it, categorizes it, and adds it to your household automatically.
                  </Typography>
                </Reveal>
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* 2. Problem / Value proposition */}
      <SectionShell bgcolor="#FFFFFF">
        <Reveal>
          <Box sx={{ maxWidth: 720 }}>
            <Eyebrow>Why वित्तमंत्री</Eyebrow>
            <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25, mb: 2.5 }}>
              Money management shouldn't feel like accounting.
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.75, mb: 2 }}>
              Most families already talk about expenses in messages, remember purchases mentally, save receipts, or
              maintain spreadsheets that eventually stop getting updated.
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.75, mb: 3 }}>
              वित्तमंत्री turns everyday expense tracking into something as simple as sending a message. Your household
              contributes to one shared financial picture while smart categorization and analytics take care of the
              repetitive work.
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35' }}>
              Less tracking effort. More financial clarity.
            </Typography>
          </Box>
        </Reveal>
      </SectionShell>

      {/* 3. Built for the whole family */}
      <SectionShell>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={5}>
            <Reveal>
              <Eyebrow>Shared household</Eyebrow>
              <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25, mb: 2.5 }}>
                One family. One financial picture.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.7, mb: 2 }}>
                Create a private household space and invite the people you manage money with. Everyone can record
                expenses while the household gets one clear view of where the money is going.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35' }}>
                Everyone contributes. Everyone stays informed.
              </Typography>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={7}>
            <Reveal delay={0.15}>
              <Card variant="outlined" sx={{ borderRadius: '1rem', bgcolor: '#FFFFFF', ...cardHoverSx }}>
                <CardContent sx={{ p: 3.5 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2.5 }}>
                    <Box sx={{ width: 44, height: 44, borderRadius: '10px', bgcolor: '#E6EFEA', color: '#173F35', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <GroupsIcon />
                    </Box>
                    <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#202421' }}>What your household gets</Typography>
                  </Box>
                  <Grid container spacing={1.5}>
                    {[
                      'See who recorded each transaction',
                      'Track household-wide spending',
                      'Understand where your money goes',
                      'Compare spending across months',
                      'Review expenses by family member',
                      'Keep everyone financially informed',
                    ].map((point) => (
                      <Grid item xs={12} sm={6} key={point}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <CheckIcon sx={{ fontSize: 18, color: '#173F35', mt: 0.25 }} />
                          <Typography sx={{ fontSize: '0.9375rem', color: '#454940' }}>{point}</Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* 4. Telegram expense logging */}
      <SectionShell id="how-it-works" bgcolor="#FFFFFF">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Reveal>
              <Eyebrow>Fast expense entry</Eyebrow>
              <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25, mb: 2.5 }}>
                Just text your expenses.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.7, mb: 2 }}>
                No forms. No complicated expense-entry screens. Send a natural message to the वित्तमंत्री Telegram bot
                and the transaction is recorded for you — with amount, merchant, category, subcategory, family member,
                and date and time all filled in.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35' }}>Text it. Done.</Typography>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={6}>
            <Reveal delay={0.15}>
              <Card variant="outlined" sx={{ borderRadius: '1rem', bgcolor: '#F6F1E7', border: '1px solid #E2DCC9', ...cardHoverSx }}>
                <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 1.25 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <TelegramIcon sx={{ color: '#173F35', fontSize: 20 }} />
                    <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#6B6F63' }}>वित्तमंत्री bot</Typography>
                  </Box>
                  {['₹450 groceries at Dmart', '2800 electricity bill', '650 petrol', '1200 dinner at Absolute Barbecue', '350 medicines'].map((msg, index) => (
                    <Reveal key={msg} delay={0.2 + index * 0.15} y={10} duration={0.4}>
                      <ChatBubble align="right">{msg}</ChatBubble>
                    </Reveal>
                  ))}
                </CardContent>
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* 5. Smart categorization */}
      <SectionShell>
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6} order={{ xs: 2, md: 1 }}>
            <Reveal>
              <Card variant="outlined" sx={{ borderRadius: '1rem', bgcolor: '#FFFFFF', ...cardHoverSx }}>
                <CardContent sx={{ p: 3.5 }}>
                  <Box sx={{ width: 44, height: 44, borderRadius: '10px', bgcolor: '#E6EFEA', color: '#173F35', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                    <AutoAwesomeIcon />
                  </Box>
                  <Grid container spacing={1.5}>
                    {['Automatic transaction categorization', 'Custom categories', 'Custom subcategories', 'Easy category corrections', 'Consistent expense organization'].map((point) => (
                      <Grid item xs={12} key={point}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <CheckIcon sx={{ fontSize: 18, color: '#173F35', mt: 0.25 }} />
                          <Typography sx={{ fontSize: '0.9375rem', color: '#454940' }}>{point}</Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={6} order={{ xs: 1, md: 2 }}>
            <Reveal delay={0.15}>
              <Eyebrow>Automatic organization</Eyebrow>
              <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25, mb: 2.5 }}>
                Smart enough to organize itself.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.7, mb: 2 }}>
                Groceries stay under groceries. Fuel stays under transport. Bills stay where they belong. वित्तमंत्री
                automatically categorizes transactions while giving your household complete control over categories
                and subcategories.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35' }}>
                Your finances should adapt to your life — not the other way around.
              </Typography>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* 6. Analytics */}
      <SectionShell id="analytics" bgcolor="#FFFFFF">
        <Reveal>
          <Box sx={{ textAlign: 'center', maxWidth: 680, mx: 'auto', mb: 5 }}>
            <Eyebrow>Useful insights</Eyebrow>
            <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25, mb: 2 }}>
              See the story behind your spending.
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.7 }}>
              Numbers are useful only when they help you understand something. वित्तमंत्री turns everyday transactions
              into simple insights your family can actually use.
            </Typography>
          </Box>
        </Reveal>
        <Grid container spacing={2.5}>
          {[
            { title: 'Monthly spending trends', desc: 'See how household spending changes from month to month.' },
            { title: 'Category breakdown', desc: 'Understand exactly where the money is going.' },
            { title: 'Member summaries', desc: 'See how expenses are distributed across household members.' },
            { title: 'Transaction history', desc: 'Search, review, and understand previous expenses whenever needed.' },
            { title: 'CSV export', desc: 'Download your transaction data whenever you want to analyze it elsewhere.' },
          ].map((card, index) => (
            <Grid item xs={12} sm={6} md={4} key={card.title}>
              <Reveal delay={index * 0.08}>
                <Card variant="outlined" sx={{ borderRadius: '0.75rem', height: '100%', bgcolor: '#F6F1E7', ...cardHoverSx }}>
                  <CardContent sx={{ p: 3 }}>
                    <Box sx={{ width: 40, height: 40, borderRadius: '10px', bgcolor: '#E6EFEA', color: '#173F35', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                      <BarChartIcon fontSize="small" />
                    </Box>
                    <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: '#202421', mb: 0.75 }}>{card.title}</Typography>
                    <Typography sx={{ fontSize: '0.875rem', color: '#6B6F63', lineHeight: 1.6 }}>{card.desc}</Typography>
                  </CardContent>
                </Card>
              </Reveal>
            </Grid>
          ))}
        </Grid>
        <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35', textAlign: 'center', mt: 4 }}>
          No complicated financial reports. No spreadsheet maintenance. Just clarity.
        </Typography>
      </SectionShell>

      {/* 7. Privacy */}
      <SectionShell id="privacy">
        <Grid container spacing={6} alignItems="center">
          <Grid item xs={12} md={6}>
            <Reveal>
              <Eyebrow>Private by design</Eyebrow>
              <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25, mb: 2.5 }}>
                Your family's finances stay your family's finances.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', color: '#454940', lineHeight: 1.7, mb: 2 }}>
                Privacy is part of the foundation of वित्तमंत्री. Every household has its own isolated workspace.
                Transactions, categories, members, and financial information belong only to that household.
              </Typography>
              <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35' }}>
                Your household. Your data. Your numbers.
              </Typography>
            </Reveal>
          </Grid>
          <Grid item xs={12} md={6}>
            <Reveal delay={0.15}>
              <Card variant="outlined" sx={{ borderRadius: '1rem', bgcolor: '#FFFFFF', ...cardHoverSx }}>
                <CardContent sx={{ p: 3.5 }}>
                  <Box sx={{ width: 44, height: 44, borderRadius: '10px', bgcolor: '#E6EFEA', color: '#173F35', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
                    <LockIcon />
                  </Box>
                  <Grid container spacing={1.5}>
                    {['Separate household workspaces', 'Household-level data isolation', 'Private transaction history', 'Controlled family membership', 'Your financial data stays within your household'].map((point) => (
                      <Grid item xs={12} key={point}>
                        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                          <CheckIcon sx={{ fontSize: 18, color: '#173F35', mt: 0.25 }} />
                          <Typography sx={{ fontSize: '0.9375rem', color: '#454940' }}>{point}</Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Reveal>
          </Grid>
        </Grid>
      </SectionShell>

      {/* 8. How it works — 3 steps */}
      <SectionShell bgcolor="#FFFFFF">
        <Reveal>
          <Box sx={{ textAlign: 'center', mb: 5 }}>
            <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25 }}>
              Expense tracking in three simple steps.
            </Typography>
          </Box>
        </Reveal>
        <Grid container spacing={3}>
          {[
            { step: '1', title: 'Create your household', desc: 'Set up your private family space and invite household members.' },
            { step: '2', title: 'Send an expense', desc: 'Message the Telegram bot naturally — "₹850 groceries at Reliance Smart".' },
            { step: '3', title: 'See the bigger picture', desc: 'वित्तमंत्री records, categorizes, and reflects it in your household dashboard automatically.' },
          ].map((item, index) => (
            <Grid item xs={12} md={4} key={item.step}>
              <Reveal delay={index * 0.12}>
                <Box sx={{ textAlign: 'center', px: 2 }}>
                  <Box sx={{ width: 48, height: 48, borderRadius: '50%', bgcolor: '#173F35', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.25rem', fontWeight: 700, mx: 'auto', mb: 2 }}>
                    {item.step}
                  </Box>
                  <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#202421', mb: 1 }}>{item.title}</Typography>
                  <Typography sx={{ fontSize: '0.9375rem', color: '#6B6F63', lineHeight: 1.6 }}>{item.desc}</Typography>
                </Box>
              </Reveal>
            </Grid>
          ))}
        </Grid>
        <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35', textAlign: 'center', mt: 5 }}>
          From message to insight in seconds.
        </Typography>
      </SectionShell>

      {/* 9. Why वित्तमंत्री — comparison */}
      <SectionShell>
        <Reveal>
          <Box sx={{ textAlign: 'center', mb: 5 }}>
            <Typography sx={{ fontSize: { xs: 26, md: 32 }, fontWeight: 700, color: '#202421', lineHeight: 1.25 }}>
              Built around how families actually manage money.
            </Typography>
          </Box>
        </Reveal>
        <Card variant="outlined" sx={{ borderRadius: '1rem', maxWidth: 780, mx: 'auto', overflow: 'hidden', bgcolor: '#FFFFFF' }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
            <Box sx={{ px: 3, py: 2, borderBottom: '1px solid #E2DCC9', borderRight: '1px solid #E2DCC9' }}>
              <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#6B6F63', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Traditional tracking
              </Typography>
            </Box>
            <Box sx={{ px: 3, py: 2, borderBottom: '1px solid #E2DCC9', bgcolor: '#E6EFEA' }}>
              <Typography sx={{ fontSize: '0.875rem', fontWeight: 600, color: '#173F35', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                वित्तमंत्री
              </Typography>
            </Box>
          </Box>
          {COMPARISON_ROWS.map((row, index) => (
            <Reveal key={row.old} delay={index * 0.06} y={12} duration={0.4}>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', borderBottom: index < COMPARISON_ROWS.length - 1 ? '1px solid #E2DCC9' : 'none' }}>
                <Box sx={{ px: 3, py: 2, borderRight: '1px solid #E2DCC9', display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CloseIcon sx={{ fontSize: 16, color: '#9A9C90' }} />
                  <Typography sx={{ fontSize: '0.9375rem', color: '#6B6F63' }}>{row.old}</Typography>
                </Box>
                <Box sx={{ px: 3, py: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckIcon sx={{ fontSize: 16, color: '#173F35' }} />
                  <Typography sx={{ fontSize: '0.9375rem', color: '#202421', fontWeight: 500 }}>{row.vitta}</Typography>
                </Box>
              </Box>
            </Reveal>
          ))}
        </Card>
        <Typography sx={{ fontSize: '1.0625rem', fontWeight: 600, color: '#173F35', textAlign: 'center', mt: 4 }}>
          Expense tracking should fit into your family's life, not become another task.
        </Typography>
      </SectionShell>

      {/* 10. Final CTA */}
      <SectionShell bgcolor="#173F35">
        <Reveal>
          <Box sx={{ textAlign: 'center', maxWidth: 640, mx: 'auto' }}>
            <Typography sx={{ fontSize: { xs: 26, md: 34 }, fontWeight: 700, color: '#FFFFFF', lineHeight: 1.25, mb: 2.5 }}>
              One family. One financial picture.
            </Typography>
            <Typography sx={{ fontSize: '1.0625rem', color: '#D9E6DF', lineHeight: 1.7, mb: 4 }}>
              From a ₹20 chai to the monthly electricity bill, every expense adds up to the bigger picture.
              वित्तमंत्री helps your household capture it effortlessly, understand it clearly, and manage money
              better — together.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => onGetStarted(1)}
              sx={{
                px: 5,
                bgcolor: '#D89B45',
                color: '#202421',
                transition: 'transform 200ms ease, background-color 200ms ease',
                '&:hover': { bgcolor: '#C88B38', transform: 'translateY(-2px)' },
              }}
            >
              Create your household
            </Button>
            <Typography sx={{ fontSize: '0.875rem', color: '#AEC2B8', mt: 2 }}>No spreadsheets required.</Typography>
          </Box>
        </Reveal>
      </SectionShell>

      {/* Footer */}
      <Box sx={{ px: { xs: 2.5, md: 6 }, py: 4, borderTop: '1px solid #E2DCC9', bgcolor: '#F6F1E7' }}>
        <Box sx={{ maxWidth: 1100, mx: 'auto', display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, gap: 2 }}>
          <Box>
            <Typography sx={{ fontSize: '0.9375rem', fontWeight: 700, color: '#202421' }}>वित्तमंत्री</Typography>
            <Typography sx={{ fontSize: '0.8125rem', color: '#6B6F63' }}>
              वित्तमंत्री is a personal project built to make family expense tracking simpler, faster, and more collaborative.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 3 }}>
            {NAV_LINKS.map((link) => (
              <Typography
                key={link.label}
                component="a"
                href={link.href}
                sx={{ fontSize: '0.8125rem', color: '#6B6F63', textDecoration: 'none', '&:hover': { color: '#173F35' } }}
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
