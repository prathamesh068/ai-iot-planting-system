import { useState } from 'react';
import {
    ConfigProvider, theme, Layout, Row, Col,
    Card, Statistic, Spin, Alert, Switch, Typography, Space, Button, Badge, message, Tooltip,
} from 'antd';
import {
    BulbOutlined, BulbFilled,
    ThunderboltOutlined, CloudOutlined,
    SunOutlined, ExperimentOutlined,
    ReloadOutlined, ClockCircleOutlined, TeamOutlined, BarChartOutlined,
    PlayCircleOutlined,
} from '@ant-design/icons';
import { useSupabaseData } from './hooks/useSupabaseData';
import { useDeviceHeartbeat } from './hooks/useDeviceHeartbeat';
import ChartCard from './components/ChartCard';
import DataTable from './components/DataTable';
import AIAnalysisCard from './components/AIAnalysisCard';
import AboutPage from './components/AboutPage';
import {
    areaData,
    tempHumidityHeatmapData,
    pieData,
    barData,
    COLORS,
    PIE_COLORS_SOIL,
} from './utils/chartConfig';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

export default function App() {
    const [isDark, setIsDark] = useState(true);
    const [page, setPage] = useState<'dashboard' | 'about'>('dashboard');
    const [activeCommand, setActiveCommand] = useState<'start' | null>(null);
    const [messageApi, messageContextHolder] = message.useMessage();
    const {
        data,
        loading,
        error,
        refetch,
        broadcastStartReading,
    } = useSupabaseData();
    const { isLive, secondsSinceHeartbeat, isDeviceRunning } = useDeviceHeartbeat();

    const latestRow = data?.rows[data.rows.length - 1];

    // Recent soil distribution: from the latest reading's per-sensor readings
    const recentSoilReadings = latestRow?.soilReadings ?? [];
    const recentSoilDist: Record<string, number> =
        recentSoilReadings.length > 0
            ? {
                DRY: recentSoilReadings.filter((r) => r === 'DRY').length,
                WET: recentSoilReadings.filter((r) => r === 'WET').length,
            }
            : (data?.soil ?? { DRY: 0, WET: 0 });

    const bgColor = isDark ? '#0f172a' : '#f1f5f9';
    const cardBg = isDark ? '#1e293b' : '#ffffff';
    const headerBg = isDark ? '#0f172a' : '#ffffff';
    const borderCol = isDark ? '#334155' : '#e2e8f0';

    const handleStartReading = async () => {
        setActiveCommand('start');
        try {
            await broadcastStartReading();
            messageApi.success('Reading cycle started.');
        } catch (err) {
            const text = err instanceof Error ? err.message : 'Unknown error';
            messageApi.error(`Failed to send command: ${text}`);
        } finally {
            setActiveCommand(null);
        }
    };

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
            {messageContextHolder}
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
                        <div
                            style={{
                                position: 'relative',
                                width: 28,
                                height: 28,
                                borderRadius: 10,
                                background: isDark ? 'rgba(30, 41, 59, 0.55)' : 'rgba(255, 255, 255, 0.72)',
                                border: `1px solid ${isDark ? 'rgba(148,163,184,0.24)' : 'rgba(148,163,184,0.4)'}`,
                                backdropFilter: 'blur(8px)',
                                WebkitBackdropFilter: 'blur(8px)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                overflow: 'hidden',
                            }}
                        >
                            <div
                                style={{
                                    position: 'absolute',
                                    inset: -8,
                                    background: isDark
                                        ? 'radial-gradient(circle, rgba(34,197,94,0.35) 0%, rgba(56,189,248,0.18) 45%, transparent 75%)'
                                        : 'radial-gradient(circle, rgba(34,197,94,0.25) 0%, rgba(56,189,248,0.2) 48%, transparent 75%)',
                                    filter: 'blur(10px)',
                                }}
                            />
                            <img
                                src="./icon.png"
                                alt="Project icon"
                                style={{
                                    width: 19,
                                    height: 19,
                                    objectFit: 'contain',
                                    position: 'relative',
                                    zIndex: 1,
                                    opacity: 0.95,
                                    mixBlendMode: isDark ? 'screen' : 'multiply',
                                }}
                            />
                        </div>
                        <Title level={5} style={{ margin: 0, color: isDark ? '#f1f5f9' : '#0f172a', fontSize: 14 }}>
                            AI + IoT Smart Agriculture System
                        </Title>
                    </Space>

                    {/* Controls row */}
                    <Space size={10} style={{ paddingTop: 4, paddingBottom: 4 }}>
                        {page === 'dashboard' && (
                            <Tooltip title={isDeviceRunning ? 'Backend running cycle' : isLive ? `Backend alive (${secondsSinceHeartbeat}s ago)` : 'Backend disconnected or not running listener mode'}>
                                <Badge
                                    status={isDeviceRunning ? 'processing' : isLive ? 'processing' : 'error'}
                                    color={isDeviceRunning ? '#f59e0b' : isLive ? '#22c55e' : '#ef4444'}
                                    text={
                                        <Text style={{ fontSize: 12, color: isDark ? '#94a3b8' : '#64748b' }}>
                                            {isDeviceRunning ? 'Running' : isLive ? 'Live' : 'Disconnected'}
                                        </Text>
                                    }
                                />
                            </Tooltip>
                        )}
                        {page === 'dashboard' && (
                            <Button
                                size="small"
                                icon={<ReloadOutlined />}
                                onClick={() => void refetch()}
                                type="text"
                                style={{ color: isDark ? '#94a3b8' : '#64748b' }}
                            />
                        )}
                        {page === 'dashboard' && (
                            <Tooltip title={!isLive ? 'Backend is offline' : isDeviceRunning ? 'Cycle in progress' : 'Start reading cycle'}>
                                <Button
                                    size="small"
                                    type="primary"
                                    icon={<PlayCircleOutlined />}
                                    loading={activeCommand === 'start'}
                                    disabled={!isLive || isDeviceRunning || activeCommand === 'start'}
                                    onClick={() => void handleStartReading()}
                                    style={{ borderRadius: 8, fontSize: 12 }}
                                >
                                    Start
                                </Button>
                            </Tooltip>
                        )}
                        <Button
                            size="small"
                            icon={page === 'about' ? <BarChartOutlined /> : <TeamOutlined />}
                            onClick={() => setPage(page === 'about' ? 'dashboard' : 'about')}
                            type={page === 'about' ? 'primary' : 'default'}
                            style={{ borderRadius: 8, fontSize: 12 }}
                        >
                            {page === 'about' ? 'Dashboard' : 'About'}
                        </Button>
                        <Switch
                            checked={isDark}
                            onChange={setIsDark}
                            checkedChildren={<BulbFilled />}
                            unCheckedChildren={<BulbOutlined />}
                        />
                    </Space>
                </Header>

                {/* ── Content ── */}
                <Content style={{ padding: page === 'about' ? '0' : '24px 20px', maxWidth: page === 'about' ? '100%' : 1400, margin: '0 auto', width: '100%' }}>

                    {/* ── About Page ── */}
                    {page === 'about' && <AboutPage isDark={isDark} />}

                    {page === 'dashboard' && loading && (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
                            <Spin size="large" tip="Loading sensor data…" />
                        </div>
                    )}

                    {page === 'dashboard' && error && (
                        <Alert
                            type="error"
                            message="Data Fetch Error"
                            description={error}
                            showIcon
                            style={{ marginBottom: 24 }}
                        />
                    )}

                    {page === 'dashboard' && data && (
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
                                        title="📊 Temp vs Humidity Heatmap"
                                        type="heatmap"
                                        data={tempHumidityHeatmapData(data.temps, data.hums)}
                                        isDark={isDark}
                                    />
                                </Col>
                                <Col xs={24} md={12} xl={8}>
                                    <ChartCard
                                        title="🌱 Soil Wetness Condition Over Time"
                                        type="barTimeSeries"
                                        data={areaData(data.labels, data.wetnessSeries)}
                                        color={COLORS.blue}
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
                                        title="🪤 Recent Soil Distribution"
                                        type="pie"
                                        data={pieData(recentSoilDist)}
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
                                todos={data.latestTodos}
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
