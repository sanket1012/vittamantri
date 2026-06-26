import AddIcon from '@mui/icons-material/Add';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import DownloadIcon from '@mui/icons-material/Download';
import GroupIcon from '@mui/icons-material/Group';
import LogoutIcon from '@mui/icons-material/Logout';
import MenuIcon from '@mui/icons-material/Menu';
import { Avatar, Box, Button, IconButton, MenuItem, TextField, Tooltip, Typography } from '@mui/material';

export default function Header({ title, caption, users, selectedUser, onUserChange, onMenuClick, onExport, onClean, onAdd, invalidCount, showMenu, onLogout, currentUser, onManageMembers }) {
  const initials = currentUser?.display_name
    ? currentUser.display_name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  return (
    <Box sx={{ minHeight: 72, bgcolor: '#FAFBFF', borderBottom: '1px solid #EAECF0', px: 2.5, py: 1.25, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
        {showMenu && (
          <IconButton onClick={onMenuClick} sx={{ color: '#344054' }}>
            <MenuIcon />
          </IconButton>
        )}
        <Box>
          <Typography sx={{ fontSize: '1.675rem', fontWeight: 600, color: '#101828', lineHeight: 1.2 }}>{title}</Typography>
          {caption && <Typography sx={{ fontSize: '1rem', fontWeight: 400, color: '#667085', mt: 0.25 }}>{caption}</Typography>}
        </Box>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <TextField select size="small" value={selectedUser} onChange={(event) => onUserChange(event.target.value)} sx={{ minWidth: 160 }}>
          <MenuItem value="All">All Users</MenuItem>
          {users.map((user) => (
            <MenuItem key={user.logged_by_id} value={String(user.logged_by_id)}>
              {user.logged_by}
            </MenuItem>
          ))}
        </TextField>

        {currentUser?.role === 'admin' && (
          <Tooltip title="Manage family members">
            <Button variant="outlined" startIcon={<GroupIcon />} onClick={onManageMembers} size="small">
              Members
            </Button>
          </Tooltip>
        )}

        <Button variant="outlined" startIcon={<DownloadIcon />} onClick={onExport}>
          Export CSV
        </Button>
        <Tooltip title={`Remove invalid transactions${invalidCount ? ` (${invalidCount} found)` : ''}`}>
          <Button variant="outlined" startIcon={<DeleteSweepIcon />} onClick={onClean} sx={{ color: '#B54708', borderColor: '#F59E0B', '&:hover': { borderColor: '#F59E0B', bgcolor: '#FFFBEB' } }}>
            Clean Garbage
          </Button>
        </Tooltip>
        <Button variant="contained" startIcon={<AddIcon />} onClick={onAdd}>
          Add
        </Button>

        <Tooltip title={`${currentUser?.display_name || 'User'} — Logout`}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, cursor: 'pointer' }} onClick={onLogout}>
            <Avatar sx={{ width: 30, height: 30, bgcolor: '#004EEB', fontSize: '0.75rem', fontWeight: 700 }}>{initials}</Avatar>
            <Typography sx={{ fontSize: '0.875rem', color: '#344054', display: { xs: 'none', sm: 'block' } }}>
              {currentUser?.display_name || ''}
            </Typography>
            <IconButton size="small" sx={{ color: '#667085', p: 0.5 }}>
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Box>
        </Tooltip>
      </Box>
    </Box>
  );
}
