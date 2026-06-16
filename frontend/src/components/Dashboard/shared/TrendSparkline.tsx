interface TrendSparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
}

export function TrendSparkline({ data, color = 'var(--color-accent)', height = 32, width = 120 }: TrendSparklineProps) {
  if (data.length === 0) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const barWidth = Math.max(2, Math.floor(width / data.length) - 1);
  const gap = 1;

  return (
    <svg width={width} height={height} className="overflow-visible">
      {data.map((value, i) => {
        const barHeight = Math.max(2, ((value - min) / range) * height);
        const x = i * (barWidth + gap);
        const y = height - barHeight;
        return (
          <rect
            key={i}
            x={x}
            y={y}
            width={barWidth}
            height={barHeight}
            rx={1}
            fill={color}
            opacity={0.7 + (value - min) / range * 0.3}
          />
        );
      })}
    </svg>
  );
}
