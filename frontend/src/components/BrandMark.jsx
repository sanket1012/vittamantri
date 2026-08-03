import { Box } from '@mui/material';

/**
 * The "वि" household monogram — from वित्तमंत्री's opening syllables. Deliberately
 * typographic rather than a generic wallet/piggy-bank/₹ icon (see the brand
 * direction doc's "Logo Elements to Avoid" section).
 */
export default function BrandMark({ size = 40, radius, fontSize, bgcolor = '#E6EFEA', color = '#173F35' }) {
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
        fontWeight: 800,
        fontSize: fontSize || Math.round(size * 0.52),
        lineHeight: 1,
        userSelect: 'none',
      }}
    >
      वि
    </Box>
  );
}
