import { Card, Table, Tag, Tooltip, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import type { SheetRow } from '../types';

const { Link } = Typography;

interface Props {
    rows: SheetRow[];
    isDark: boolean;
}

type RowWithKey = SheetRow & { key: number };

export default function DataTable({ rows, isDark }: Props) {
    const cardBg = isDark ? '#1e293b' : '#ffffff';

    const columns: ColumnsType<RowWithKey> = [
        {
            title: 'Time',
            dataIndex: 'time',
            key: 'time',
            width: 130,
            fixed: 'left',
            render: (v: string) => (
                <span style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{v || '—'}</span>
            ),
        },
        {
            title: 'Temp °C',
            dataIndex: 'temp',
            key: 'temp',
            width: 90,
            sorter: (a, b) => (a.temp ?? 0) - (b.temp ?? 0),
            render: (v: number | null) =>
                v != null ? (
                    <Tag color="orange" style={{ fontWeight: 600 }}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
        {
            title: 'Hum %',
            dataIndex: 'hum',
            key: 'hum',
            width: 90,
            sorter: (a, b) => (a.hum ?? 0) - (b.hum ?? 0),
            render: (v: number | null) =>
                v != null ? (
                    <Tag color="blue" style={{ fontWeight: 600 }}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
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
            width: 90,
            filters: [
                { text: 'WET', value: 'WET' },
                { text: 'DRY', value: 'DRY' },
            ],
            onFilter: (value, record) => record.soil === value,
            render: (v: string | null) =>
                v ? (
                    <Tag color={v === 'WET' ? 'cyan' : 'volcano'}>{v}</Tag>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
        {
            title: 'Image',
            dataIndex: 'img',
            key: 'img',
            width: 70,
            render: (v: string | null) =>
                v ? (
                    <Link href={v} target="_blank" style={{ fontSize: 12 }}>
                        View
                    </Link>
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
            render: (v: string | null) =>
                v ? (
                    <Tooltip title={v} overlayStyle={{ maxWidth: 400 }}>
                        <span className="snip" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
                            {v.slice(0, 50)}…
                        </span>
                    </Tooltip>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
        {
            title: 'AI Response',
            dataIndex: 'response',
            key: 'response',
            width: 160,
            render: (v: string | null) =>
                v ? (
                    <Tooltip title={v} overlayStyle={{ maxWidth: 400 }}>
                        <span className="snip" style={{ color: isDark ? '#94a3b8' : '#64748b' }}>
                            {v.slice(0, 50)}…
                        </span>
                    </Tooltip>
                ) : (
                    <span style={{ color: '#475569' }}>—</span>
                ),
        },
    ];

    const dataSource: RowWithKey[] = rows.map((r, i) => ({ ...r, key: i }));

    return (
        <Card
            title="📋 Latest Readings"
            style={{ borderRadius: 16, background: cardBg }}
            styles={{ body: { padding: 0 } }}
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
