import { Area, AreaChart, ResponsiveContainer } from 'recharts';

/** Tiny trend chart for stat cards — no axes/grid/tooltip, just the shape. */
export default function Sparkline({ data, dataKey = 'value', color = '#243044', height = 40 }) {
  if (!data?.length) return null;
  const gradientId = `spark-${dataKey}-${color.replace('#', '')}`;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} fill={`url(#${gradientId})`} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
