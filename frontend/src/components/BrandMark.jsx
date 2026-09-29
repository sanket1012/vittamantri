import { Box } from '@mui/material';
import logoMark from '../assets/logo-mark.png';

// Samvitta's house + "S" monogram.
export default function BrandMark({ size = 40 }) {
  return (
    <Box
      component="img"
      src={logoMark}
      alt="Samvitta"
      sx={{ width: size, height: size, flexShrink: 0, display: 'block', userSelect: 'none' }}
    />
  );
}
