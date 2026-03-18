import { Card, Table, Tag, Tooltip, Popover, Typography } from 'antd';
import { SendOutlined, MessageOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { PlantRow } from '../types';
import { formatDateFull, syntaxHighlightJson } from '../utils/htmlHelpers';

const { Link } = Typography;

interface Props {
    rows: PlantRow[];
    isDark: boolean;
}

type RowWithKey = PlantRow & { key: number };

export default function DataTable({ rows, isDark }: Props) {
    const cardBg = isDark ? '#1e293b' : '#ffffff';

    const columns: ColumnsType<RowWithKey> = [
        {
            title: 'Time',
            dataIndex: 'time',
            key: 'time',
            width: 190,
            fixed: 'left',
            render: (v: string) => (
                <span style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{formatDateFull(v)}</span>
            ),
        },
        {
            title: 'Temp °C',
            dataIndex: 'temp',
            key: 'temp',
            width: 100,
            sorter: (a, b) => (a.temp ?? 0) - (b.temp ?? 0),
            render: (v: number | null, record: RowWithKey) => {
                const readings = record.tempReadings ?? [];
                const tag = v != null ? (
                    <Tag color="orange" style={{ fontWeight: 600 }}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                );
                if (readings.length === 0) return tag;
                const tipContent = (
                    <div style={{ minWidth: 120 }}>
                        <div style={{ marginBottom: 4, fontWeight: 600, borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: 4 }}>All Temp Sensors</div>
                        {readings.map((r, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '1px 0' }}>
                                <span style={{ color: '#94a3b8' }}>Sensor {i + 1}</span>
                                <span style={{ fontWeight: 600 }}>{r != null ? `${r}°C` : '—'}</span>
                            </div>
                        ))}
                        <div style={{ marginTop: 4, borderTop: '1px solid rgba(255,255,255,0.2)', paddingTop: 4, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                            <span style={{ color: '#94a3b8' }}>Average</span>
                            <span style={{ fontWeight: 700, color: '#fb923c' }}>{v != null ? `${v}°C` : '—'}</span>
                        </div>
                    </div>
                );
                return <Tooltip title={tipContent} overlayStyle={{ maxWidth: 220 }}>{tag}</Tooltip>;
            },
        },
        {
            title: 'Hum %',
            dataIndex: 'hum',
            key: 'hum',
            width: 100,
            sorter: (a, b) => (a.hum ?? 0) - (b.hum ?? 0),
            render: (v: number | null, record: RowWithKey) => {
                const readings = record.humReadings ?? [];
                const tag = v != null ? (
                    <Tag color="blue" style={{ fontWeight: 600 }}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                );
                if (readings.length === 0) return tag;
                const tipContent = (
                    <div style={{ minWidth: 120 }}>
                        <div style={{ marginBottom: 4, fontWeight: 600, borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: 4 }}>All Humidity Sensors</div>
                        {readings.map((r, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '1px 0' }}>
                                <span style={{ color: '#94a3b8' }}>Sensor {i + 1}</span>
                                <span style={{ fontWeight: 600 }}>{r != null ? `${r}%` : '—'}</span>
                            </div>
                        ))}
                        <div style={{ marginTop: 4, borderTop: '1px solid rgba(255,255,255,0.2)', paddingTop: 4, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                            <span style={{ color: '#94a3b8' }}>Average</span>
                            <span style={{ fontWeight: 700, color: '#60a5fa' }}>{v != null ? `${v}%` : '—'}</span>
                        </div>
                    </div>
                );
                return <Tooltip title={tipContent} overlayStyle={{ maxWidth: 220 }}>{tag}</Tooltip>;
            },
        },
        {
            title: 'Light',
            dataIndex: 'light',
            key: 'light',
            width: 90,
            filters: [
                { text: 'BRIGHT', value: 'BRIGHT' },
                { text: 'DARK', value: 'DARK' },
            ],
            onFilter: (value, record) => record.light === value,
            render: (v: string | null) =>
                v ? (
                    <Tag color={v === 'BRIGHT' ? 'gold' : 'default'}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
        {
            title: 'Soil',
            dataIndex: 'soil',
            key: 'soil',
            width: 100,
            filters: [
                { text: 'WET', value: 'WET' },
                { text: 'DRY', value: 'DRY' },
            ],
            onFilter: (value, record) => record.soil === value,
            render: (v: string | null, record: RowWithKey) => {
                const readings = record.soilReadings ?? [];
                const tag = v ? (
                    <Tag color={v === 'WET' ? 'cyan' : 'volcano'}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                );
                if (readings.length === 0) return tag;
                const dryCount = readings.filter(r => r === 'DRY').length;
                const wetCount = readings.filter(r => r === 'WET').length;
                const tipContent = (
                    <div style={{ minWidth: 140 }}>
                        <div style={{ marginBottom: 4, fontWeight: 600, borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: 4 }}>All Soil Sensors</div>
                        {readings.map((r, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '1px 0' }}>
                                <span style={{ color: '#94a3b8' }}>Sensor {i + 1}</span>
                                <span style={{ fontWeight: 600, color: r === 'WET' ? '#22d3ee' : '#fb7185' }}>{r}</span>
                            </div>
                        ))}
                        <div style={{ marginTop: 4, borderTop: '1px solid rgba(255,255,255,0.2)', paddingTop: 4, display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                            <span style={{ color: '#94a3b8' }}>DRY / WET</span>
                            <span style={{ fontWeight: 700 }}>{dryCount} / {wetCount}</span>
                        </div>
                    </div>
                );
                return <Tooltip title={tipContent} overlayStyle={{ maxWidth: 240 }}>{tag}</Tooltip>;
            },
        },
        {
            title: 'Image',
            dataIndex: 'img',
            key: 'img',
            width: 70,
            render: (v: string | null) =>
                v ? (
                    <Popover
                        trigger="hover"
                        content={
                            <img
                                src={v}
                                alt="Plant"
                                style={{ maxWidth: 260, maxHeight: 260, borderRadius: 8, display: 'block' }}
                                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                        }
                        overlayInnerStyle={{ padding: 6 }}
                    >
                        <Link href={v} target="_blank" style={{ fontSize: 12 }}>View</Link>
                    </Popover>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
        {
            title: 'Disease',
            dataIndex: 'disease',
            key: 'disease',
            width: 110,
            render: (v: string | null) =>
                v ? (
                    <Tag color="red" style={{ fontSize: 11 }}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
        {
            title: 'Action',
            dataIndex: 'action',
            key: 'action',
            width: 100,
            render: (v: string) => (
                <Tag color="green" style={{ fontSize: 11 }}>{v}</Tag>
            ),
        },
        {
            title: 'Plant',
            dataIndex: 'plant',
            key: 'plant',
            width: 100,
            render: (v: string) => (
                <span style={{ fontSize: 12 }}>{v || '—'}</span>
            ),
        },
        {
            title: 'Prompt',
            dataIndex: 'prompt',
            key: 'prompt',
            width: 160,
            render: (v: string | null) => {
                if (!v) return <span style={{ color: '#475569' }}>—</span>;
                const panelBg = isDark ? '#0f172a' : '#f8fafc';
                const borderC = isDark ? '#334155' : '#e2e8f0';
                const textC = isDark ? '#cbd5e1' : '#334155';
                const content = (
                    <div style={{ background: panelBg, border: `1px solid ${borderC}`, borderRadius: 10, padding: '14px 16px', maxWidth: 420 }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: "'Fira Mono','Cascadia Code','Consolas',monospace", fontSize: '0.72rem', lineHeight: 1.6, color: textC, maxHeight: 320, overflowY: 'auto', background: 'transparent', padding: 0 }}>
                            {v}
                        </pre>
                    </div>
                );
                return (
                    <Popover trigger="hover" title={<span><SendOutlined style={{ marginRight: 6 }} />Prompt</span>} content={content} >
                        <span className="snip" style={{ color: isDark ? '#94a3b8' : '#64748b', cursor: 'default' }}>{v.slice(0, 50)}…</span>
                    </Popover>
                );
            },
        },
        {
            title: 'AI Response',
            dataIndex: 'response',
            key: 'response',
            width: 160,
            render: (v: string | null) => {
                if (!v) return <span style={{ color: '#475569' }}>—</span>;
                const panelBg = isDark ? '#0f172a' : '#f8fafc';
                const borderC = isDark ? '#334155' : '#e2e8f0';
                const textC = isDark ? '#cbd5e1' : '#334155';
                const content = (
                    <div style={{ background: panelBg, border: `1px solid ${borderC}`, borderRadius: 10, padding: '14px 16px', maxWidth: 420 }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontFamily: "'Fira Mono','Cascadia Code','Consolas',monospace", fontSize: '0.72rem', lineHeight: 1.6, color: textC, maxHeight: 320, overflowY: 'auto', background: 'transparent', padding: 0 }}
                            dangerouslySetInnerHTML={{ __html: syntaxHighlightJson(v) }}
                        />
                    </div>
                );
                return (
                    <Popover trigger="hover" title={<span><MessageOutlined style={{ marginRight: 6 }} />AI Response</span>} content={content} >
                        <span className="snip" style={{ color: isDark ? '#94a3b8' : '#64748b', cursor: 'default' }}>{v.slice(0, 50)}…</span>
                    </Popover>
                );
            },
        },
    ];

    // Reverse so the latest reading appears first
    const dataSource: RowWithKey[] = rows.slice().reverse().map((r, i) => ({ ...r, key: i }));

    return (
        <Card
            title="📋 Latest Readings"
            style={{ borderRadius: 16, background: cardBg }}
            styles={{ body: { padding: 10 } }}
        >
            <Table
                columns={columns}
                dataSource={dataSource}
                size="small"
                scroll={{ x: 1100 }}
                pagination={{
                    pageSize: 10,
                    showSizeChanger: false,
                    showTotal: (total) => `${total} readings`,
                    style: { padding: '8px 16px' },
                }}
                style={{ borderRadius: '0 0 16px 16px', overflow: 'hidden' }}
            />
        </Card>
    );
}
