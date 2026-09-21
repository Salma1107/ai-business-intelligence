import { useWindowDimensions } from 'react-native';
import Svg, { Circle, Line, Path, Text as SvgText } from 'react-native-svg';

import type { SalesTimeSeriesPoint } from '@/services/api';

type SalesLineChartProps = {
  series: SalesTimeSeriesPoint[];
};

function formatCompactNumber(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1).replace('.', ',')} M`;
  }

  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(0)} k`;
  }

  return Math.round(value).toString();
}

export function SalesLineChart({ series }: SalesLineChartProps) {
  const { width } = useWindowDimensions();
  const chartWidth = Math.max(width - 64, 280);
  const chartHeight = 220;
  const padding = { top: 18, right: 14, bottom: 38, left: 52 };
  const plotWidth = chartWidth - padding.left - padding.right;
  const plotHeight = chartHeight - padding.top - padding.bottom;
  const values = series.map((point) => point.total_sales);
  const maxValue = Math.max(...values, 1);
  const minValue = Math.min(...values, 0);
  const range = Math.max(maxValue - minValue, 1);

  const points = series.map((point, index) => {
    const x =
      padding.left + (series.length === 1 ? plotWidth / 2 : (index / (series.length - 1)) * plotWidth);
    const y = padding.top + ((maxValue - point.total_sales) / range) * plotHeight;
    return { ...point, x, y };
  });

  const path = points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(' ');
  const labelIndexes = [...new Set([0, Math.floor((series.length - 1) / 2), series.length - 1])];
  const midValue = minValue + range / 2;

  return (
    <Svg accessibilityLabel="Courbe des ventes mensuelles" height={chartHeight} width={chartWidth}>
      {[maxValue, midValue, minValue].map((value, index) => {
        const y = padding.top + (index / 2) * plotHeight;
        return (
          <Line
            key={`grid-${index}`}
            stroke="#E2E8F0"
            strokeDasharray="4 4"
            x1={padding.left}
            x2={chartWidth - padding.right}
            y1={y}
            y2={y}
          />
        );
      })}

      {[maxValue, midValue, minValue].map((value, index) => {
        const y = padding.top + (index / 2) * plotHeight + 4;
        return (
          <SvgText
            fill="#64748B"
            fontSize="10"
            key={`scale-${index}`}
            textAnchor="end"
            x={padding.left - 8}
            y={y}>
            {formatCompactNumber(value)}
          </SvgText>
        );
      })}

      <Path d={path} fill="none" stroke="#2563EB" strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} />

      {points.map((point) => (
        <Circle cx={point.x} cy={point.y} fill="#FFFFFF" key={point.period} r={3} stroke="#2563EB" strokeWidth={2} />
      ))}

      {labelIndexes.map((index) => {
        const point = points[index];
        if (!point) {
          return null;
        }

        return (
          <SvgText
            fill="#64748B"
            fontSize="10"
            key={`period-${point.period}`}
            textAnchor="middle"
            x={point.x}
            y={chartHeight - 12}>
            {point.period}
          </SvgText>
        );
      })}
    </Svg>
  );
}
