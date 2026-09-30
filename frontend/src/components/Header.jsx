import { useState } from 'react';
import AddIcon from '@mui/icons-material/Add';
import CleaningServicesIcon from '@mui/icons-material/CleaningServices';
import DownloadIcon from '@mui/icons-material/Download';
import GroupIcon from '@mui/icons-material/Group';
import MenuIcon from '@mui/icons-material/Menu';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { Box, Button, IconButton, ListItemIcon, ListItemText, Menu, MenuItem, TextField, Tooltip, Typography } from '@mui/material';

const currentMonthLabel = () => new Date().toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });

export default function Header({ title, caption, greeting = false, users, selectedUser, onUserChange, onMenuClick, onExport, onClean, onAdd, invalidCount, showMenu, currentUser, onManageMembers }) {
  const [menuAnchor, setMenuAnchor] = useState(null);

  const handleMenuAction = (action) => {
    setMenuAnchor(null);
    action?.();
  };

  return (
    <Box sx={{ minHeight: 76, bgcolor: '#FFFFFF', borderBottom: '1px solid #E3DDD4', px: 2.5, py: 1.5, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'stretch', sm: 'center' }, justifyContent: 'space-between', gap: { xs: 1.25, sm: 2 } }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
        {showMenu && (
          <IconButton onClick={onMenuClick} sx={{ color: '#20242C', flexShrink: 0, ml: -1 }}>
            <MenuIcon />
          </IconButton>
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography
            sx={{
              fontFamily: greeting ? '"Instrument Serif", Georgia, serif' : 'inherit',
              fontSize: greeting ? '1.75rem' : '1.5rem',
              fontWeight: greeting ? 400 : 700,
              color: '#20242C',
              lineHeight: 1.2,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {title}
          </Typography>
          {caption && (
            <Typography sx={{ fontSize: '0.9375rem', fontWeight: 400, color: '#77736D', mt: 0.25, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {caption}
            </Typography>
          )}
        </Box>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', justifyContent: 'flex-end', flexShrink: 0 }}>
        <Typography sx={{ fontSize: '0.875rem', color: '#77736D', display: { xs: 'none', sm: 'block' } }}>{currentMonthLabel()}</Typography>

        <TextField select size="small" value={selectedUser} onChange={(event) => onUserChange(event.target.value)} sx={{ minWidth: 150 }}>
          <MenuItem value="All">All Users</MenuItem>
          {users.map((user) => (
            <MenuItem key={user.logged_by_id} value={String(user.logged_by_id)}>
              {user.logged_by}
            </MenuItem>
          ))}
        </TextField>

        <Button variant="contained" startIcon={<AddIcon />} onClick={onAdd}>
          Add
        </Button>

        <Tooltip title="More options">
          <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)} sx={{ color: '#20242C' }}>
            <MoreVertIcon />
          </IconButton>
        </Tooltip>
        <Menu anchorEl={menuAnchor} open={!!menuAnchor} onClose={() => setMenuAnchor(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }} transformOrigin={{ vertical: 'top', horizontal: 'right' }}>
          {currentUser?.role === 'admin' && (
            <MenuItem onClick={() => handleMenuAction(onManageMembers)}>
              <ListItemIcon><GroupIcon fontSize="small" /></ListItemIcon>
              <ListItemText>Manage Members</ListItemText>
            </MenuItem>
          )}
          <MenuItem onClick={() => handleMenuAction(onExport)}>
            <ListItemIcon><DownloadIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Export CSV</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => handleMenuAction(onClean)}>
            <ListItemIcon><CleaningServicesIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Data Cleanup{invalidCount ? ` (${invalidCount})` : ''}</ListItemText>
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );
}
