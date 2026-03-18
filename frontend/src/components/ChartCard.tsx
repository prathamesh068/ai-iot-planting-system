import { Card } from 'antd';
import {
    AreaChart, Area,
    LineChart, Line,
    BarChart, Bar,
    PieChart, Pie, Cell,
    ScatterChart, Scatter,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer,
} from 'recharts';
import type { AreaPoint, DualPoint, HeatmapPoint, PiePoint, BarPoint } from '../utils/chartConfig';
import { COLORS, PIE_COLORS_LIGHT } from '../utils/chartConfig';
import { formatDateFull, formatDateShort } from '../utils/htmlHelpers';

// ── Shared axis / grid colours per theme ──────────────────────────────────
const axisColor = (dark: boolean) => dark ? '#475569' : '#94a3b8';
const gridColor = (dark: boolean) => dark ? '#1e293b' : '#e2e8f0';
const labelColor = (dark: boolean) => dark ? '#94a3b8' : '#64748b';

// ── Discriminated-union props ─────────────────────────────────────────────
interface BaseProps { title: string; isDark: boolean }

interface AreaProps extends BaseProps { type: 'area'; data: AreaPoint[]; color: string }
interface DualLineProps extends BaseProps { type: 'dualLine'; data: DualPoint[] }
interface HeatmapProps extends BaseProps { type: 'heatmap'; data: HeatmapPoint[] }
interface PieProps extends BaseProps { type: 'pie'; data: PiePoint[]; colors?: string[] }
interface BarProps extends BaseProps { type: 'bar'; data: BarPoint[]; color?: string }
interface BarTimeSeriesProps extends BaseProps { type: 'barTimeSeries'; data: AreaPoint[]; color?: string }

type Props = AreaProps | DualLineProps | HeatmapProps | PieProps | BarProps | BarTimeSeriesProps;

type TooltipKind = Props['type'];

interface TooltipPayloadItem {
    color?: string;
    dataKey?: string | number;
    name?: string | number;
    value?: string | number;
    payload?: Record<string, unknown>;
}

interface CustomTooltipProps {
    kind: TooltipKind;
    active?: boolean;
    payload?: TooltipPayloadItem[];
    label?: string | number;
}

const tooltipWrapStyle: React.CSSProperties = {
    background: '#ffffff',
    borderRadius: 10,
    boxShadow: '0 10px 24px rgba(15, 23, 42, 0.2)',
    color: '#0f172a',
    fontSize: 12,
    minWidth: 180,
    overflow: 'hidden',
};

const tooltipHeaderStyle: React.CSSProperties = {
    background: '#0f172a',
    color: '#f8fafc',
    fontWeight: 700,
    fontSize: 13,
    padding: '6px 12px',
};

const tooltipBodyStyle: React.CSSProperties = {
    padding: '8px 12px 10px',
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
};

const tooltipRowStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
};

const tooltipKeyStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    color: '#475569',
};

const tooltipValueStyle: React.CSSProperties = {
    color: '#0f172a',
    fontWeight: 700,
};

function prettySeriesName(rawName: string): string {
    if (rawName === 'temp') return 'Temperature';
    if (rawName === 'hum') return 'Humidity';
    if (rawName === 'count') return 'Count';
    if (rawName === 'value') return 'Value';
    return rawName;
}

function formatTooltipValue(rawValue: string | number | undefined, kind: TooltipKind): string {
    const numeric = Number(rawValue);
    if (!Number.isFinite(numeric)) {
        return String(rawValue ?? '—');
    }

    if (kind === 'heatmap') {
        return String(Math.round(numeric));
    }

    if (kind === 'barTimeSeries') {
        return `${Number.isInteger(numeric) ? numeric : numeric.toFixed(1)}%`;
    }

    return Number.isInteger(numeric) ? String(numeric) : numeric.toFixed(2);
}

function resolveTooltipColor(item: TooltipPayloadItem, kind: TooltipKind): string {
    const p = item.payload as Record<string, unknown> | undefined;

    if (typeof item.color === 'string' && item.color) {
        return item.color;
    }
    if (typeof p?.fill === 'string' && p.fill) {
        return p.fill;
    }
    if (typeof p?.color === 'string' && p.color) {
        return p.color;
    }
    if (kind === 'pie') {
        return COLORS.blue;
    }
    if (kind === 'heatmap') {
        return '#0ea5e9';
    }
    return '#94a3b8';
}

function tooltipHeader(kind: TooltipKind, label: string | number | undefined, payload?: TooltipPayloadItem[]): string {
    if (kind === 'heatmap') {
        const point = payload?.[0]?.payload;
        const temp = Number(point?.temp);
        const hum = Number(point?.hum);
        if (Number.isFinite(temp) && Number.isFinite(hum)) {
            return `${Math.round(temp)}°C | ${Math.round(hum)}%`;
        }
        return 'Temp/Humidity';
    }
    if (kind === 'bar') {
        return label != null ? String(label) : 'Details';
    }
    return label != null ? formatDateFull(String(label)) : 'Details';
}

function CustomTooltip({ kind, active, payload, label }: CustomTooltipProps) {
    if (!active || !payload?.length) return null;

    return (
        <div style={tooltipWrapStyle}>
            <div style={tooltipHeaderStyle}>{tooltipHeader(kind, label, payload)}</div>
            <div style={tooltipBodyStyle}>
                {payload.map((item) => {
                    const rawName = String(item.name ?? item.dataKey ?? 'Value');
                    const name = kind === 'heatmap' && rawName === 'temp'
                        ? 'Temperature (°C)'
                        : kind === 'heatmap' && rawName === 'hum'
                            ? 'Humidity (%)'
                            : prettySeriesName(rawName);

                    return (
                        <div key={String(item.dataKey ?? item.name ?? rawName)} style={tooltipRowStyle}>
                            <div style={tooltipKeyStyle}>
                                <span
                                    style={{
                                        width: 10,
                                        height: 10,
                                        borderRadius: 999,
                                        backgroundColor: resolveTooltipColor(item, kind),
                                        display: 'inline-block',
                                    }}
                                />
                                <span>{name}</span>
                            </div>
                            <span style={tooltipValueStyle}>{formatTooltipValue(item.value, kind)}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default function ChartCard(props: Props) {
    const { title, isDark } = props;
    const gc = gridColor(isDark);
    const ac = axisColor(isDark);
    const lc = labelColor(isDark);

    const xAxisProps = {
        dataKey: 'time',
        tick: { fill: lc, fontSize: 10 },
        axisLine: { stroke: ac },
        tickLine: false,
        interval: 'preserveStartEnd' as const,
        tickFormatter: formatDateShort,
    };

    const yAxisProps = {
        tick: { fill: lc, fontSize: 10 },
        axisLine: false,
        tickLine: false,
        width: 36,
    };

    const gridProps = {
        stroke: gc,
        strokeDasharray: '3 3',
        vertical: false,
    };

    const cardStyle: React.CSSProperties = {
        borderRadius: 16,
        height: '100%',
    };

    const heatPoints = props.type === 'heatmap' ? props.data : [];
    const heatTempTicks = [...new Set(heatPoints.map((point) => point.temp))].sort((a, b) => a - b);
    const heatHumTicks = [...new Set(heatPoints.map((point) => point.hum))].sort((a, b) => a - b);
    const heatCols = Math.max(heatTempTicks.length, 1);
    const heatRows = Math.max(heatHumTicks.length, 1);
    const heatTempStep = heatTempTicks.length > 1 ? heatTempTicks[1] - heatTempTicks[0] : 1;
    const heatHumStep = heatHumTicks.length > 1 ? heatHumTicks[1] - heatHumTicks[0] : 1;
    const heatMaxCount = heatPoints.length ? Math.max(...heatPoints.map((point) => point.count), 0) : 0;
    const estimatedCellWidth = Math.floor(280 / heatCols);
    const estimatedCellHeight = Math.floor(165 / heatRows);
    const heatCellSide = Math.max(12, Math.min(36, Math.min(estimatedCellWidth, estimatedCellHeight) + 2));

    const heatCellColor = (count: number, maxCount: number): string => {
        if (count <= 0 || maxCount <= 0) {
            return isDark ? '#334155' : '#e2e8f0';
        }

        const ratio = Math.max(0, Math.min(1, count / maxCount));
        if (ratio < 0.25) return '#65a30d';
        if (ratio < 0.5) return '#a3c836';
        if (ratio < 0.7) return '#facc15';
        if (ratio < 0.85) return '#f59e0b';
        return '#ef4444';
    };

    return (
        <Card title={title} size="small" style={cardStyle} styles={{ body: { paddingTop: 8 } }}>
            <ResponsiveContainer width="100%" height={240}>
                {props.type === 'area' ? (
                    <AreaChart data={props.data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={props.color} stopOpacity={0.35} />
                                <stop offset="95%" stopColor={props.color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid {...gridProps} />
                        <XAxis {...xAxisProps} />
                        <YAxis {...yAxisProps} />
                        <Tooltip content={<CustomTooltip kind="area" />} />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={props.color}
                            strokeWidth={2}
                            fill={`url(#grad-${title})`}
                            dot={false}
                            activeDot={{ r: 4 }}
                            connectNulls
                        />
                    </AreaChart>
                ) : props.type === 'dualLine' ? (
                    <LineChart data={props.data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid {...gridProps} />
                        <XAxis {...xAxisProps} />
                        <YAxis {...yAxisProps} />
                        <Tooltip content={<CustomTooltip kind="dualLine" />} />
                        <Legend
                            wrapperStyle={{ fontSize: 11, color: lc }}
                            formatter={(value) => value === 'temp' ? 'Temp °C' : 'Humidity %'}
                        />
                        <Line
                            type="monotone"
                            dataKey="temp"
                            stroke={COLORS.green}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4 }}
                            connectNulls
                        />
                        <Line
                            type="monotone"
                            dataKey="hum"
                            stroke={COLORS.blue}
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4 }}
                            connectNulls
                        />
                    </LineChart>
                ) : props.type === 'heatmap' ? (
                    <ScatterChart data={props.data} margin={{ top: 8, right: 12, left: 4, bottom: 8 }}>
                        <CartesianGrid stroke={gc} strokeDasharray="0 0" />
                        <XAxis
                            type="number"
                            dataKey="temp"
                            name="Temperature"
                            unit="°C"
                            tick={{ fill: lc, fontSize: 10 }}
                            axisLine={{ stroke: ac }}
                            tickLine={false}
                            ticks={heatTempTicks}
                            domain={
                                heatTempTicks.length
                                    ? [
                                        heatTempTicks[0] - heatTempStep / 2,
                                        heatTempTicks[heatTempTicks.length - 1] + heatTempStep / 2,
                                    ]
                                    : ['auto', 'auto']
                            }
                            label={{ value: 'Temperature (°C)', position: 'insideBottom', offset: -6, fill: lc, fontSize: 11 }}
                        />
                        <YAxis
                            type="number"
                            dataKey="hum"
                            name="Humidity"
                            unit="%"
                            tick={{ fill: lc, fontSize: 10 }}
                            axisLine={{ stroke: ac }}
                            tickLine={false}
                            width={44}
                            ticks={heatHumTicks}
                            domain={
                                heatHumTicks.length
                                    ? [
                                        heatHumTicks[0] - heatHumStep / 2,
                                        heatHumTicks[heatHumTicks.length - 1] + heatHumStep / 2,
                                    ]
                                    : ['auto', 'auto']
                            }
                            label={{ value: 'Humidity (%)', angle: -90, position: 'insideLeft', fill: lc, fontSize: 11 }}
                        />
                        <Tooltip content={<CustomTooltip kind="heatmap" />} />
                        <Scatter
                            data={props.data}
                            shape={(shapeProps: { cx?: number; cy?: number; payload?: HeatmapPoint }) => {
                                const cx = shapeProps.cx ?? 0;
                                const cy = shapeProps.cy ?? 0;
                                const count = shapeProps.payload?.count ?? 0;
                                const half = heatCellSide / 2;
                                const showValue = heatCellSide >= 16;
                                const fill = heatCellColor(count, heatMaxCount);
                                return (
                                    <g>
                                        <rect
                                            x={cx - half}
                                            y={cy - half}
                                            width={heatCellSide}
                                            height={heatCellSide}
                                            rx={2}
                                            fill={fill}
                                            stroke={isDark ? '#0b1220' : '#ffffff'}
                                            strokeWidth={1}
                                        />
                                        {showValue && (
                                            <text
                                                x={cx}
                                                y={cy + 4}
                                                textAnchor="middle"
                                                fill={count > 0 ? '#ffffff' : (isDark ? '#e2e8f0' : '#475569')}
                                                fontSize={10}
                                                fontWeight={700}
                                            >
                                                {count}
                                            </text>
                                        )}
                                    </g>
                                );
                            }}
                        />
                    </ScatterChart>
                ) : props.type === 'pie' ? (
                    <PieChart>
                        <Pie
                            data={props.data}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={90}
                            paddingAngle={3}
                            dataKey="value"
                            label={({ name, percent }) =>
                                `${name} ${(percent * 100).toFixed(0)}%`
                            }
                            labelLine={false}
                        >
                            {props.data.map((_, idx) => (
                                <Cell
                                    key={idx}
                                    fill={(props.colors ?? PIE_COLORS_LIGHT)[idx % (props.colors ?? PIE_COLORS_LIGHT).length]}
                                />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip kind="pie" />} />
                        <Legend wrapperStyle={{ fontSize: 11, color: lc }} />
                    </PieChart>
                ) : props.type === 'bar' ? (
                    /* categorical bar */
                    <BarChart data={props.data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid {...gridProps} />
                        <XAxis
                            dataKey="name"
                            tick={{ fill: lc, fontSize: 10 }}
                            axisLine={{ stroke: ac }}
                            tickLine={false}
                        />
                        <YAxis {...yAxisProps} />
                        <Tooltip content={<CustomTooltip kind="bar" />} />
                        <Bar
                            dataKey="value"
                            fill={props.color ?? COLORS.blue}
                            radius={[6, 6, 0, 0]}
                            maxBarSize={48}
                        />
                    </BarChart>
                ) : (
                    /* barTimeSeries — time on x-axis, 0–100% on y-axis */
                    <BarChart data={props.data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid {...gridProps} />
                        <XAxis {...xAxisProps} />
                        <YAxis
                            {...yAxisProps}
                            domain={[0, 100]}
                            tickFormatter={(v: number) => `${v}%`}
                            width={42}
                        />
                        <Tooltip content={<CustomTooltip kind="barTimeSeries" />} />
                        <Bar
                            dataKey="value"
                            fill={props.color ?? COLORS.green}
                            radius={[4, 4, 0, 0]}
                            maxBarSize={40}
                        />
                    </BarChart>
                )}
            </ResponsiveContainer>
        </Card>
    );
}
