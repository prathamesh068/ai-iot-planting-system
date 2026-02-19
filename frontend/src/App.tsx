import { useState } from 'react';
import {
    ConfigProvider, theme, Layout, Row, Col,
    Card, Statistic, Spin, Alert, Switch, Typography, Space, Button, Badge,
} from 'antd';
import {
    BulbOutlined, BulbFilled,
    ThunderboltOutlined, CloudOutlined,
    SunOutlined, ExperimentOutlined,
    ReloadOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { useSheetData } from './hooks/useSheetData';
import ChartCard from './components/ChartCard';
import DataTable from './components/DataTable';
import AIAnalysisCard from './components/AIAnalysisCard';
import {
    areaData,
    dualLineData,
    pieData,
    barData,
    COLORS,
    PIE_COLORS_SOIL,
} from './utils/chartConfig';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

export default function App() {
    const [isDark, setIsDark] = useState(true);
    const { data, loading, error, refetch } = useSheetData();

    const latestRow = data?.rows[data.rows.length - 1];

    const bgColor = isDark ? '#0f172a' : '#f1f5f9';
    const cardBg = isDark ? '#1e293b' : '#ffffff';
    const headerBg = isDark ? '#0f172a' : '#ffffff';
    const borderCol = isDark ? '#334155' : '#e2e8f0';

    return (
        <ConfigProvider
            theme={{
                algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
                token: {
                    colorPrimary: '#22c55e',
                    colorBgBase: isDark ? '#0f172a' : '#f8fafc',
                    colorBgContainer: cardBg,
                    colorBorder: borderCol,
                    borderRadius: 12,
                    fontFamily: 'Inter, system-ui, sans-serif',
                },
                components: {
                    Card: { headerBg: cardBg },
                    Table: { headerBg: isDark ? '#1e293b' : '#f8fafc' },
                },
            }}
        >
            <Layout style={{ minHeight: '100vh', background: bgColor }}>

                {/* ── Header ── */}
                <Header
                    style={{
                        background: headerBg,
                        borderBottom: `1px solid ${borderCol}`,
                        padding: '0 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        flexWrap: 'wrap',
                        gap: 8,
                        height: 'auto',
                        minHeight: 64,
                        lineHeight: 'normal',
                        position: 'sticky',
                        top: 0,
                        zIndex: 100,
                    }}
                >
                    {/* Title row */}
                    <Space align="center" size={10} style={{ paddingTop: 4, paddingBottom: 4 }}>
                        <span style={{ fontSize: 22 }}>🌱</span>
                        <Title level={5} style={{ margin: 0, color: isDark ? '#f1f5f9' : '#0f172a', fontSize: 14 }}>
                            AI + IoT Smart Agriculture System
                        </Title>
                    </Space>

                    {/* Controls row */}
                    <Space size={10} style={{ paddingTop: 4, paddingBottom: 4 }}>
                        <Badge
                            status="processing"
                            color="#22c55e"
                            text={
                                <Text style={{ fontSize: 12, color: isDark ? '#94a3b8' : '#64748b' }}>
                                    Live
                                </Text>
                            }
                        />
                        <Button
                            size="small"
                            icon={<ReloadOutlined />}
                            onClick={() => void refetch()}
                            type="text"
                            style={{ color: isDark ? '#94a3b8' : '#64748b' }}
                        />
                        <Switch
                            checked={isDark}
                            onChange={setIsDark}
                            checkedChildren={<BulbFilled />}
                            unCheckedChildren={<BulbOutlined />}
                        />
                    </Space>
                </Header>

                {/* ── Content ── */}
                <Content style={{ padding: '24px 20px', maxWidth: 1400, margin: '0 auto', width: '100%' }}>

                    {loading && (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
                            <Spin size="large" tip="Loading sensor data…" />
                        </div>
                    )}

                    {error && (
                        <Alert
                            type="error"
                            message="Data Fetch Error"
                            description={error}
                            showIcon
                            style={{ marginBottom: 24 }}
                        />
                    )}

                    {data && (
                        <>
                            {/* ── Stat Cards ── */}
                            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                                <Col xs={12} sm={6}>
                                    <Card
                                        style={{ borderRadius: 16, background: cardBg }}
                                        styles={{ body: { padding: '16px 20px' } }}
                                    >
                                        <Statistic
                                            title={
                                                <Text style={{ fontSize: 12, color: isDark ? '#94a3b8' : '#64748b' }}>
                                                    Temperature
                                                </Text>
                                            }
                                            value={latestRow?.temp ?? '—'}
                                            suffix={latestRow?.temp != null ? '°C' : ''}
                                            prefix={<ThunderboltOutlined style={{ color: COLORS.orange }} />}
                                            valueStyle={{ color: COLORS.orange, fontSize: 22 }}
                                        />
                                    </Card>
                                </Col>
                                <Col xs={12} sm={6}>
                                    <Card
                                        style={{ borderRadius: 16, background: cardBg }}
                                        styles={{ body: { padding: '16px 20px' } }}
                                    >
                                        <Statistic
                                            title={
                                                <Text style={{ fontSize: 12, color: isDark ? '#94a3b8' : '#64748b' }}>
                                                    Humidity
                                                </Text>
                                            }
                                            value={latestRow?.hum ?? '—'}
                                            suffix={latestRow?.hum != null ? '%' : ''}
                                            prefix={<CloudOutlined style={{ color: COLORS.blue }} />}
                                            valueStyle={{ color: COLORS.blue, fontSize: 22 }}
                                        />
                                    </Card>
                                </Col>
                                <Col xs={12} sm={6}>
                                    <Card
                                        style={{ borderRadius: 16, background: cardBg }}
                                        styles={{ body: { padding: '16px 20px' } }}
                                    >
                                        <Statistic
                                            title={
                                                <Text style={{ fontSize: 12, color: isDark ? '#94a3b8' : '#64748b' }}>
                                                    Light
                                                </Text>
                                            }
                                            value={latestRow?.light ?? '—'}
                                            prefix={<SunOutlined style={{ color: COLORS.yellow }} />}
                                            valueStyle={{ color: COLORS.yellow, fontSize: 22 }}
                                        />
                                    </Card>
                                </Col>
                                <Col xs={12} sm={6}>
                                    <Card
                                        style={{ borderRadius: 16, background: cardBg }}
                                        styles={{ body: { padding: '16px 20px' } }}
                                    >
                                        <Statistic
                                            title={
                                                <Text style={{ fontSize: 12, color: isDark ? '#94a3b8' : '#64748b' }}>
                                                    Soil
                                                </Text>
                                            }
                                            value={latestRow?.soil ?? '—'}
                                            prefix={<ExperimentOutlined style={{ color: COLORS.green }} />}
                                            valueStyle={{ color: COLORS.green, fontSize: 22 }}
                                        />
                                    </Card>
                                </Col>
                            </Row>

                            {/* ── Charts Grid ── */}
                            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="🌡 Temperature (°C)"
                                        type="area"
                                        data={areaData(data.labels, data.temps)}
                                        color={COLORS.orange}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="💧 Humidity (%)"
                                        type="area"
                                        data={areaData(data.labels, data.hums)}
                                        color={COLORS.blue}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="📊 Temp vs Humidity"
                                        type="dualLine"
                                        data={dualLineData(data.labels, data.temps, data.hums)}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="🌱 Soil Condition Over Time"
                                        type="area"
                                        data={areaData(data.labels, data.soilSeries)}
                                        color={COLORS.green}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="☀️ Light Distribution"
                                        type="pie"
                                        data={pieData(data.light)}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="🪴 Soil Distribution"
                                        type="pie"
                                        data={pieData(data.soil)}
                                        colors={PIE_COLORS_SOIL}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12}>
                                    <ChartCard
                                        title="⚡ Actions Count"
                                        type="bar"
                                        data={barData(data.actions)}
                                        color={COLORS.purple}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12}>
                                    <ChartCard
                                        title="🦠 Disease Count"
                                        type="bar"
                                        data={barData(data.diseases)}
                                        color={COLORS.red}
                                        isDark={isDark}
                                    />
                                </Col>
                            </Row>

                            {/* ── Data Table ── */}
                            <div style={{ marginBottom: 24 }}>
                                <DataTable rows={data.rows} isDark={isDark} />
                            </div>

                            {/* ── AI Analysis ── */}
                            <AIAnalysisCard
                                prompt={data.latestPrompt}
                                response={data.latestResponse}
                                isDark={isDark}
                            />
                        </>
                    )}
                </Content>

                {/* ── Footer ── */}
                <Footer
                    style={{
                        textAlign: 'center',
                        background: 'transparent',
                        padding: '16px 24px',
                        borderTop: `1px solid ${borderCol}`,
                    }}
                >
                    <Space direction="vertical" size={2}>
                        <Text style={{ fontSize: 12, color: isDark ? '#475569' : '#94a3b8' }}>
                            <ClockCircleOutlined style={{ marginRight: 4 }} />
                            Auto-refresh every 60 seconds
                        </Text>
                        <Text style={{ fontSize: 12, color: isDark ? '#475569' : '#94a3b8' }}>
                            Made with ❤️ by Prathamesh
                        </Text>
                    </Space>
                </Footer>
            </Layout>
        </ConfigProvider>
    );
}
