import { Card } from 'antd';
import {
    AreaChart, Area,
    LineChart, Line,
    BarChart, Bar,
    PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend,
    ResponsiveContainer,
} from 'recharts';
import type { AreaPoint, DualPoint, PiePoint, BarPoint } from '../utils/chartConfig';
import { COLORS, PIE_COLORS_LIGHT } from '../utils/chartConfig';

// ── Shared axis / grid colours per theme ──────────────────────────────────
const axisColor = (dark: boolean) => dark ? '#475569' : '#94a3b8';
const gridColor = (dark: boolean) => dark ? '#1e293b' : '#e2e8f0';
const labelColor = (dark: boolean) => dark ? '#94a3b8' : '#64748b';

// ── Discriminated-union props ─────────────────────────────────────────────
interface BaseProps { title: string; isDark: boolean }

interface AreaProps extends BaseProps { type: 'area'; data: AreaPoint[]; color: string }
interface DualLineProps extends BaseProps { type: 'dualLine'; data: DualPoint[] }
interface PieProps extends BaseProps { type: 'pie'; data: PiePoint[]; colors?: string[] }
interface BarProps extends BaseProps { type: 'bar'; data: BarPoint[]; color?: string }

type Props = AreaProps | DualLineProps | PieProps | BarProps;

// ── Shared tooltip style ──────────────────────────────────────────────────
const tooltipStyle = (dark: boolean) => ({
    backgroundColor: dark ? '#1e293b' : '#ffffff',
    border: `1px solid ${dark ? '#334155' : '#e2e8f0'}`,
    borderRadius: 8,
    fontSize: 12,
    color: dark ? '#e2e8f0' : '#1e293b',
});

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
                        <Tooltip contentStyle={tooltipStyle(isDark)} />
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
                        <Tooltip contentStyle={tooltipStyle(isDark)} />
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
                        <Tooltip contentStyle={tooltipStyle(isDark)} />
                        <Legend wrapperStyle={{ fontSize: 11, color: lc }} />
                    </PieChart>
                ) : (
                    /* bar */
                    <BarChart data={props.data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid {...gridProps} />
                        <XAxis
                            dataKey="name"
                            tick={{ fill: lc, fontSize: 10 }}
                            axisLine={{ stroke: ac }}
                            tickLine={false}
                        />
                        <YAxis {...yAxisProps} />
                        <Tooltip contentStyle={tooltipStyle(isDark)} />
                        <Bar
                            dataKey="value"
                            fill={props.color ?? COLORS.blue}
                            radius={[6, 6, 0, 0]}
                            maxBarSize={48}
                        />
                    </BarChart>
                )}
            </ResponsiveContainer>
        </Card>
    );
}
