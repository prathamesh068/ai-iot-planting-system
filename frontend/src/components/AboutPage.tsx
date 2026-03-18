import { useEffect, useState } from 'react';
import {
    Row, Col, Card, Avatar, Tag, Typography, Space, Spin, Alert, Divider,
} from 'antd';
import {
    UserOutlined, BankOutlined, NumberOutlined, TagsOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface Creator {
    name: string;
    rollNo: string;
    college: string;
    photo: string;
    areas: string[];
    about?: string;
}

const AREA_COLORS = [
    'green', 'blue', 'purple', 'orange', 'cyan', 'geekblue', 'magenta', 'gold',
] as const;

interface Props {
    isDark: boolean;
}

export default function AboutPage({ isDark }: Props) {
    const [creators, setCreators] = useState<Creator[]>([]);
    const [loading, setLoading] = useState(true);
    const [fetchError, setFetchError] = useState<string | null>(null);

    useEffect(() => {
        fetch('/creators.json')
            .then((res) => {
                if (!res.ok) throw new Error(`Failed to load creators.json (${res.status})`);
                return res.json() as Promise<Creator[]>;
            })
            .then((data) => {
                setCreators(data);
            })
            .catch((err: unknown) => {
                setFetchError(err instanceof Error ? err.message : String(err));
            })
            .finally(() => setLoading(false));
    }, []);

    const cardBg = isDark ? '#1e293b' : '#ffffff';
    const mutedColor = isDark ? '#94a3b8' : '#64748b';
    const headingColor = isDark ? '#f1f5f9' : '#0f172a';
    const subColor = isDark ? '#cbd5e1' : '#334155';
    const dividerColor = isDark ? '#334155' : '#e2e8f0';

    return (
        <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 16px' }}>

            {/* ── Page heading ── */}
            <div style={{ textAlign: 'center', marginBottom: 40 }}>
                <div
                    style={{
                        position: 'relative',
                        width: 300,
                        height: 300,
                        margin: '0 auto 8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <div
                        style={{
                            position: 'absolute',
                            inset: 10,
                            borderRadius: 999,
                            background: isDark
                                ? 'radial-gradient(circle, rgba(34,197,94,0.34) 0%, rgba(56,189,248,0.22) 45%, transparent 75%)'
                                : 'radial-gradient(circle, rgba(34,197,94,0.24) 0%, rgba(56,189,248,0.2) 50%, transparent 76%)',
                            filter: 'blur(20px)',
                        }}
                    />
                    <div
                        style={{
                            position: 'absolute',
                            inset: 24,
                            borderRadius: 28,
                            background: isDark ? 'rgba(15, 23, 42, 0.4)' : 'rgba(255, 255, 255, 0.56)',
                            border: `1px solid ${isDark ? 'rgba(148,163,184,0.24)' : 'rgba(148,163,184,0.4)'}`,
                            backdropFilter: 'blur(14px)',
                            WebkitBackdropFilter: 'blur(14px)',
                        }}
                    />
                    <img
                        src={`${import.meta.env.BASE_URL}icon.png`}
                        alt="Project icon"
                        style={{
                            width: 250,
                            height: 250,
                            objectFit: 'contain',
                            position: 'relative',
                            zIndex: 1,
                            opacity: 0.94,
                            mixBlendMode: isDark ? 'screen' : 'multiply',
                            filter: isDark
                                ? 'drop-shadow(0 10px 24px rgba(15,23,42,0.35))'
                                : 'drop-shadow(0 10px 20px rgba(15,23,42,0.12))',
                        }}
                    />
                </div>
                <Title level={2} style={{ color: headingColor, margin: '8px 0 4px' }}>
                    About This Project
                </Title>
                <Text style={{ color: mutedColor, fontSize: 14 }}>
                    AI + IoT Smart Agriculture System — real-time plant monitoring powered by Raspberry Pi,
                    multiple DHT11 sensors, Google Gemini AI, and a live Supabase dashboard.
                </Text>
            </div>

            <Divider style={{ borderColor: dividerColor, marginBottom: 36 }} />

            {/* ── Project summary section ── */}
            <Row gutter={[24, 24]} style={{ marginBottom: 48 }}>
                {[
                    { emoji: '🤖', label: 'AI-Powered Analysis', desc: 'Google Gemini AI interprets sensor data and camera images to diagnose plant health in real time.' },
                    { emoji: '📡', label: 'IoT Sensor Network', desc: 'Multiple DHT11 temperature/humidity sensors, soil moisture probes, and a light sensor feed live data.' },
                    { emoji: '📊', label: 'Live Dashboard', desc: 'React + Ant Design frontend with Recharts visualisations, heatmaps, and data tables streamed from Supabase.' },
                    { emoji: '🔧', label: 'Automated Actuators', desc: 'Water pump and fan are triggered automatically by AI recommendations and sensor thresholds.' },
                ].map(({ emoji, label, desc }) => (
                    <Col key={label} xs={24} sm={12} md={6}>
                        <Card
                            style={{ background: cardBg, borderRadius: 16, height: '100%', textAlign: 'center' }}
                            styles={{ body: { padding: '20px 16px' } }}
                        >
                            <div style={{ fontSize: 28, marginBottom: 8 }}>{emoji}</div>
                            <Text strong style={{ color: subColor, display: 'block', marginBottom: 6, fontSize: 13 }}>
                                {label}
                            </Text>
                            <Text style={{ color: mutedColor, fontSize: 12, lineHeight: 1.6 }}>{desc}</Text>
                        </Card>
                    </Col>
                ))}
            </Row>

            {/* ── Creators section ── */}
            <Title level={4} style={{ color: headingColor, marginBottom: 24 }}>
                <Space>
                    <UserOutlined />
                    Project Creators
                </Space>
            </Title>

            {loading && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
                    <Spin tip="Loading team info…" />
                </div>
            )}

            {fetchError && (
                <Alert
                    type="error"
                    message="Could not load creators.json"
                    description={fetchError}
                    showIcon
                    style={{ marginBottom: 24 }}
                />
            )}

            {!loading && !fetchError && (
                <Row gutter={[24, 24]}>
                    {creators.map((creator) => (
                        <Col key={creator.name} xs={24} sm={12} md={12} lg={8}>
                            <Card
                                style={{ background: cardBg, borderRadius: 20, height: '100%' }}
                                styles={{ body: { padding: '28px 24px' } }}
                            >
                                {/* Avatar */}
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 20 }}>
                                    <Avatar
                                        src={creator.photo}
                                        size={200}
                                        icon={<UserOutlined />}
                                        style={{
                                            marginBottom: 14,
                                            border: `3px solid ${isDark ? '#22c55e' : '#16a34a'}`,
                                            boxShadow: '0 4px 16px rgba(34,197,94,0.25)',
                                        }}
                                    />
                                    <Title level={4} style={{ color: headingColor, margin: 0 }}>
                                        {creator.name}
                                    </Title>
                                </div>

                                <Divider style={{ borderColor: dividerColor, margin: '0 0 16px' }} />

                                {/* Details */}
                                <Space direction="vertical" size={10} style={{ width: '100%' }}>
                                    <Space size={8} align="start">
                                        <NumberOutlined style={{ color: '#22c55e', marginTop: 2 }} />
                                        <div>
                                            <Text style={{ color: mutedColor, fontSize: 11, display: 'block' }}>Roll / Year</Text>
                                            <Text strong style={{ color: subColor, fontSize: 13 }}>{creator.rollNo}</Text>
                                        </div>
                                    </Space>

                                    <Space size={8} align="start">
                                        <BankOutlined style={{ color: '#38bdf8', marginTop: 2 }} />
                                        <div>
                                            <Text style={{ color: mutedColor, fontSize: 11, display: 'block' }}>College / Department</Text>
                                            <Text strong style={{ color: subColor, fontSize: 13 }}>{creator.college}</Text>
                                        </div>
                                    </Space>

                                    {creator.about && (
                                        <div>
                                            <Text style={{ color: mutedColor, fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                Contribution Summary
                                            </Text>
                                            <Text style={{ color: subColor, fontSize: 13, lineHeight: 1.6 }}>
                                                {creator.about}
                                            </Text>
                                        </div>
                                    )}

                                    <div>
                                        <Space size={6} style={{ marginBottom: 8 }}>
                                            <TagsOutlined style={{ color: '#a78bfa' }} />
                                            <Text style={{ color: mutedColor, fontSize: 11 }}>Key Areas</Text>
                                        </Space>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                            {creator.areas.map((area, idx) => (
                                                <Tag
                                                    key={area}
                                                    color={AREA_COLORS[idx % AREA_COLORS.length]}
                                                    style={{ borderRadius: 20, fontSize: 11, padding: '1px 10px', margin: 0 }}
                                                >
                                                    {area}
                                                </Tag>
                                            ))}
                                        </div>
                                    </div>
                                </Space>
                            </Card>
                        </Col>
                    ))}
                </Row>
            )}

            {/* ── Guide section ── */}
            <Divider style={{ borderColor: dividerColor, margin: '48px 0 28px' }} />
            <Title level={4} style={{ color: headingColor, marginBottom: 20 }}>
                <Space>
                    <UserOutlined />
                    Project Guide
                </Space>
            </Title>
            <Row gutter={[24, 24]} style={{ marginBottom: 12 }}>
                <Col xs={24} md={16} lg={12}>
                    <Card
                        style={{ background: cardBg, borderRadius: 20 }}
                        styles={{ body: { padding: '24px 22px' } }}
                    >
                        <Space direction="vertical" size={8} style={{ width: '100%' }}>
                            <Title level={4} style={{ margin: 0, color: headingColor }}>Akshay Gaikwad</Title>
                            <Text strong style={{ color: subColor, fontSize: 14 }}>
                                Head of Software at Aituring Tech
                            </Text>
                            <Tag color="geekblue" style={{ width: 'fit-content', borderRadius: 14, margin: 0 }}>
                                8+ Years in Software Industry
                            </Tag>
                            <Text style={{ color: mutedColor, fontSize: 13, lineHeight: 1.7 }}>
                                Guided the software direction of the project and provided mentorship across
                                full-stack implementation and delivery.
                            </Text>
                        </Space>
                    </Card>
                </Col>
            </Row>

            {/* ── Tech stack section ── */}
            <Divider style={{ borderColor: dividerColor, margin: '48px 0 32px' }} />
            <Title level={4} style={{ color: headingColor, marginBottom: 20 }}>
                🛠 Tech Stack
            </Title>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {[
                    { label: 'Python 3', color: 'blue' },
                    { label: 'Raspberry Pi', color: 'red' },
                    { label: 'Google Gemini AI', color: 'purple' },
                    { label: 'Supabase / PostgreSQL', color: 'green' },
                    { label: 'React 18', color: 'cyan' },
                    { label: 'TypeScript', color: 'geekblue' },
                    { label: 'Ant Design 5', color: 'blue' },
                    { label: 'Recharts', color: 'orange' },
                    { label: 'Tailwind CSS', color: 'cyan' },
                    { label: 'Vite', color: 'gold' },
                    { label: 'DHT11 Sensors', color: 'green' },
                    { label: 'Soil Moisture Sensors', color: 'magenta' },
                ].map(({ label, color }) => (
                    <Tag
                        key={label}
                        color={color}
                        style={{ borderRadius: 20, fontSize: 12, padding: '3px 12px', margin: 0 }}
                    >
                        {label}
                    </Tag>
                ))}
            </div>
        </div>
    );
}
