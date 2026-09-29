import { Box } from '@mui/material';

// Geometric "S" monogram for Samvitta — abstract rather than a
// wallet/coin/₹/leaf icon, and simple enough to read at 24px.
export default function BrandMark({ size = 40, radius, fontSize, bgcolor = '#15171C', color = '#CDAA6A' }) {
  return (
    <Box
      sx={{
        width: size,
        height: size,
        flexShrink: 0,
        borderRadius: radius || `${Math.round(size * 0.28)}px`,
        bgcolor,
        color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: '"Instrument Serif", Georgia, serif',
        fontStyle: 'italic',
        fontSize: fontSize || Math.round(size * 0.62),
        lineHeight: 1,
        userSelect: 'none',
      }}
    >
      S
    </Box>
  );
}
