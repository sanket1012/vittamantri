import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import BarChartIcon from '@mui/icons-material/BarChart';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DownloadIcon from '@mui/icons-material/Download';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import { Box, Drawer, Typography } from '@mui/material';

const navItems = [
  { label: 'Dashboard', icon: DashboardIcon, target: 'dashboard' },
  { label: 'Transactions', icon: ReceiptLongIcon, target: 'transactions' },
  { label: 'Analytics', icon: BarChartIcon, target: 'analytics' },
  { label: 'Export', icon: DownloadIcon, target: 'export' },
];

function SidebarContent({ userCount, activeSection, onNavigate }) {
  return (
    <Box sx={{ width: 260, minHeight: '100vh', bgcolor: '#FFFFFF', borderRight: '1px solid #EAECF0', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ height: 72, px: 2.5, display: 'flex', alignItems: 'center', gap: 1.5, borderBottom: '1px solid #EAECF0' }}>
        <Box sx={{ width: 40, height: 40, borderRadius: '10px', bgcolor: '#EFF6FF', color: '#004EEB', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <AccountBalanceWalletIcon />
        </Box>
        <Box>
          <Typography sx={{ fontSize: 18, fontWeight: 700, color: '#101828', lineHeight: 1.2 }}>वित्तमंत्री</Typography>
          <Typography sx={{ fontSize: 12, color: '#667085' }}>Finance Tracker</Typography>
        </Box>
      </Box>

      <Box sx={{ flex: 1, py: 2 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.target === activeSection;
          return (
            <Box
              key={item.label}
              component="button"
              type="button"
              onClick={() => onNavigate(item.target)}
              sx={{
                width: 'calc(100% - 24px)',
                mx: 1.5,
                mb: 0.5,
                px: 2,
                py: '10px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                color: active ? '#004EEB' : '#344054',
                bgcolor: active ? '#EFF6FF' : 'transparent',
                border: 0,
                borderLeft: active ? '3px solid #004EEB' : '3px solid transparent',
                borderRadius: '8px',
                fontSize: 14,
                fontWeight: 500,
                fontFamily: 'Inter, sans-serif',
                textAlign: 'left',
                cursor: 'pointer',
                transition: 'all 150ms ease',
                '&:hover': { bgcolor: active ? '#EFF6FF' : '#F9FAFB', transform: 'translateX(1px)' },
              }}
            >
              <Icon sx={{ fontSize: 20 }} />
              <Typography sx={{ fontSize: 14, fontWeight: 500 }}>{item.label}</Typography>
            </Box>
          );
        })}
      </Box>

      <Box sx={{ p: 2.5, borderTop: '1px solid #EAECF0' }}>
        <Typography sx={{ fontSize: 12, color: '#667085' }}>👥 {userCount} users active</Typography>
      </Box>
    </Box>
  );
}

export default function Sidebar({ userCount, mobileOpen, onClose, activeSection = 'dashboard', onNavigate = () => {} }) {
  return (
    <>
      <Box sx={{ display: { xs: 'none', md: 'block' }, flexShrink: 0 }}>
        <SidebarContent userCount={userCount} activeSection={activeSection} onNavigate={onNavigate} />
      </Box>
      <Drawer open={mobileOpen} onClose={onClose} ModalProps={{ keepMounted: true }} sx={{ display: { xs: 'block', md: 'none' } }}>
        <SidebarContent userCount={userCount} activeSection={activeSection} onNavigate={onNavigate} />
      </Drawer>
    </>
  );
}
