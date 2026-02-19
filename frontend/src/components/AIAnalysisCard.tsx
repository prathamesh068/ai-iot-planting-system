import { Card, Tabs, Empty, Typography } from 'antd';
import { RobotOutlined, SendOutlined, MessageOutlined } from '@ant-design/icons';
import { syntaxHighlightJson } from '../utils/htmlHelpers';

const { Text } = Typography;

interface Props {
    prompt: string | null;
    response: string | null;
    isDark: boolean;
}

export default function AIAnalysisCard({ prompt, response, isDark }: Props) {
    if (!prompt && !response) return null;

    const cardBg = isDark ? '#1e293b' : '#ffffff';
    const panelBg = isDark ? '#0f172a' : '#f8fafc';
    const borderC = isDark ? '#334155' : '#e2e8f0';
    const textC = isDark ? '#cbd5e1' : '#334155';
    const mutedC = isDark ? '#64748b' : '#94a3b8';

    const preStyle: React.CSSProperties = {
        margin: 0,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        fontFamily: "'Fira Mono', 'Cascadia Code', 'Consolas', monospace",
        fontSize: '0.72rem',
        lineHeight: 1.6,
        color: textC,
        maxHeight: 360,
        overflowY: 'auto',
        background: 'transparent',
        padding: 0,
    };

    const panelStyle: React.CSSProperties = {
        background: panelBg,
        border: `1px solid ${borderC}`,
        borderRadius: 10,
        padding: '14px 16px',
    };

    const items = [
        {
            key: 'prompt',
            label: (
                <span>
                    <SendOutlined style={{ marginRight: 6 }} />
                    Prompt
                </span>
            ),
            children: prompt ? (
                <div style={panelStyle}>
                    <pre style={preStyle}>{prompt}</pre>
                </div>
            ) : (
                <Empty
                    description={<Text style={{ color: mutedC }}>No prompt data</Text>}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ),
        },
        {
            key: 'response',
            label: (
                <span>
                    <MessageOutlined style={{ marginRight: 6 }} />
                    Response
                </span>
            ),
            children: response ? (
                <div style={panelStyle}>
                    <pre
                        style={preStyle}
                        dangerouslySetInnerHTML={{ __html: syntaxHighlightJson(response) }}
                    />
                </div>
            ) : (
                <Empty
                    description={<Text style={{ color: mutedC }}>No response data</Text>}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ),
        },
    ];

    return (
        <Card
            title={
                <span>
                    <RobotOutlined style={{ marginRight: 8, color: '#a78bfa' }} />
                    Latest Gemini AI Analysis
                </span>
            }
            style={{ borderRadius: 16, background: cardBg }}
            styles={{ body: { paddingTop: 0 } }}
        >
            <Tabs
                defaultActiveKey="response"
                items={items}
                size="small"
                style={{ marginTop: -8 }}
            />
        </Card>
    );
}
