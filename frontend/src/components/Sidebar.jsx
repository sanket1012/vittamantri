import BarChartIcon from '@mui/icons-material/BarChart';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DownloadIcon from '@mui/icons-material/Download';
import LabelIcon from '@mui/icons-material/Label';
import LogoutIcon from '@mui/icons-material/Logout';
import PersonIcon from '@mui/icons-material/Person';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import { Avatar, Box, Drawer, IconButton, Tooltip, Typography } from '@mui/material';
import BrandMark from './BrandMark.jsx';

const navItems = [
  { label: 'Overview', icon: DashboardIcon, target: 'dashboard' },
  { label: 'Transactions', icon: ReceiptLongIcon, target: 'transactions' },
  { label: 'Analytics', icon: BarChartIcon, target: 'analytics' },
  { label: 'Categories', icon: LabelIcon, target: 'categories' },
];

const secondaryNavItems = [
  { label: 'Export', icon: DownloadIcon, target: 'export' },
  { label: 'Profile', icon: PersonIcon, target: 'profile' },
];

const EXPANDED_WIDTH = 260;
const COLLAPSED_WIDTH = 80;

function NavButton({ item, active, collapsed, onNavigate }) {
  const Icon = item.icon;
  const button = (
    <Box
      key={item.label}
      component="button"
      type="button"
      onClick={() => onNavigate(item.target)}
      sx={{
        width: collapsed ? 44 : 'calc(100% - 24px)',
        mx: collapsed ? 'auto' : 1.5,
        mb: 0.5,
        px: collapsed ? 0 : 2,
        py: '10px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'flex-start',
        gap: '10px',
        color: active ? '#111827' : '#77736D',
        bgcolor: active ? '#F0EBE2' : 'transparent',
        border: 0,
        borderLeft: collapsed ? '3px solid transparent' : active ? '3px solid #111827' : '3px solid transparent',
        borderRadius: '8px',
        fontSize: 14,
        fontWeight: 500,
        fontFamily: 'Inter, sans-serif',
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'all 150ms ease',
        '&:hover': { bgcolor: active ? '#F0EBE2' : '#F0EBE2', transform: collapsed ? 'none' : 'translateX(1px)' },
      }}
    >
      <Icon sx={{ fontSize: 20 }} />
      {!collapsed && <Typography sx={{ fontSize: 14, fontWeight: 500 }}>{item.label}</Typography>}
    </Box>
  );
  return collapsed ? (
    <Tooltip key={item.label} title={item.label} placement="right">
      {button}
    </Tooltip>
  ) : (
    button
  );
}

function SidebarContent({ userCount, activeSection, onNavigate, collapsed, onToggleCollapse, collapsible, currentUser, onLogout }) {
  const initials = currentUser?.display_name
    ? currentUser.display_name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  return (
    <Box sx={{ width: collapsed ? COLLAPSED_WIDTH : EXPANDED_WIDTH, minHeight: '100vh', bgcolor: '#FFFFFF', borderRight: '1px solid #E3DDD4', display: 'flex', flexDirection: 'column', transition: 'width 180ms ease' }}>
      <Box sx={{ height: 72, px: collapsed ? 1.5 : 2.5, display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between', gap: 1.5, borderBottom: '1px solid #E3DDD4' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
          <BrandMark size={40} />
          {!collapsed && (
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: 18, fontWeight: 700, color: '#20242C', lineHeight: 1.2 }}>Samvitta</Typography>
              <Typography sx={{ fontSize: 12, color: '#77736D' }}>Finance Tracker</Typography>
            </Box>
          )}
        </Box>
        {collapsible && !collapsed && (
          <Tooltip title="Collapse sidebar">
            <IconButton size="small" onClick={onToggleCollapse} sx={{ color: '#77736D', flexShrink: 0 }}>
              <ChevronLeftIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {collapsible && collapsed && (
        <Box sx={{ display: 'flex', justifyContent: 'center', pt: 1 }}>
          <Tooltip title="Expand sidebar" placement="right">
            <IconButton size="small" onClick={onToggleCollapse} sx={{ color: '#77736D' }}>
              <ChevronRightIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      <Box sx={{ flex: 1, py: 2 }}>
        {navItems.map((item) => (
          <NavButton key={item.label} item={item} active={item.target === activeSection} collapsed={collapsed} onNavigate={onNavigate} />
        ))}

        {!collapsed && (
          <Typography sx={{ fontSize: 11, fontWeight: 600, color: '#77736D', textTransform: 'uppercase', letterSpacing: '0.06em', px: 2.5, mt: 2, mb: 0.5 }}>
            Settings
          </Typography>
        )}
        {collapsed && <Box sx={{ borderTop: '1px solid #E3DDD4', mx: 1.5, my: 1.5 }} />}
        {secondaryNavItems.map((item) => (
          <NavButton key={item.label} item={item} active={item.target === activeSection} collapsed={collapsed} onNavigate={onNavigate} />
        ))}
      </Box>

      {!collapsed && (
        <Box sx={{ px: 2.5, pb: 1.5 }}>
          <Typography sx={{ fontSize: 12, color: '#77736D' }}>👥 {userCount} users active</Typography>
        </Box>
      )}

      <Box sx={{ p: collapsed ? 1.5 : 2, borderTop: '1px solid #E3DDD4', display: 'flex', alignItems: 'center', gap: 1, justifyContent: collapsed ? 'center' : 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
          <Avatar sx={{ width: 32, height: 32, bgcolor: '#111827', fontSize: '0.75rem', fontWeight: 700 }}>{initials}</Avatar>
          {!collapsed && (
            <Box sx={{ minWidth: 0 }}>
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#20242C', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {currentUser?.display_name || 'User'}
              </Typography>
              <Typography sx={{ fontSize: 11, color: '#77736D', textTransform: 'capitalize' }}>{currentUser?.role || 'member'}</Typography>
            </Box>
          )}
        </Box>
        <Tooltip title="Logout" placement={collapsed ? 'right' : 'top'}>
          <IconButton size="small" onClick={onLogout} sx={{ color: '#77736D', flexShrink: 0, '&:hover': { color: '#D96B67', bgcolor: '#FBEDED' } }}>
            <LogoutIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
}

export default function Sidebar({ userCount, mobileOpen, onClose, activeSection = 'dashboard', onNavigate = () => {}, collapsed = false, onToggleCollapse = () => {}, currentUser, onLogout }) {
  return (
    <>
      <Box sx={{ display: { xs: 'none', md: 'block' }, flexShrink: 0 }}>
        <SidebarContent
          userCount={userCount}
          activeSection={activeSection}
          onNavigate={onNavigate}
          collapsed={collapsed}
          onToggleCollapse={onToggleCollapse}
          collapsible
          currentUser={currentUser}
          onLogout={onLogout}
        />
      </Box>
      <Drawer open={mobileOpen} onClose={onClose} ModalProps={{ keepMounted: true }} sx={{ display: { xs: 'block', md: 'none' } }}>
        <SidebarContent
          userCount={userCount}
          activeSection={activeSection}
          onNavigate={onNavigate}
          collapsed={false}
          collapsible={false}
          currentUser={currentUser}
          onLogout={onLogout}
        />
      </Drawer>
    </>
  );
}
