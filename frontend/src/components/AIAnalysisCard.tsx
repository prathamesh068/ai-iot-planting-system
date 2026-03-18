import { Card, Tabs, Empty, Typography, List, Tag } from 'antd';
import { RobotOutlined, SendOutlined, MessageOutlined, OrderedListOutlined } from '@ant-design/icons';
import { syntaxHighlightJson } from '../utils/htmlHelpers';
import type { TodoItem } from '../types';

const { Text } = Typography;

interface Props {
    prompt: string | null;
    response: string | null;
    todos: TodoItem[];
    isDark: boolean;
}

function priorityColor(priority: TodoItem['priority']): string {
    if (priority === 'HIGH') return 'red';
    if (priority === 'MEDIUM') return 'orange';
    return 'blue';
}

export default function AIAnalysisCard({ prompt, response, todos, isDark }: Props) {
    if (!prompt && !response && todos.length === 0) return null;

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
        {
            key: 'todos',
            label: (
                <span>
                    <OrderedListOutlined style={{ marginRight: 6 }} />
                    TODOs
                </span>
            ),
            children: todos.length > 0 ? (
                <div style={panelStyle}>
                    <List
                        size="small"
                        dataSource={todos}
                        renderItem={(todo, index) => (
                            <List.Item>
                                <div style={{ width: '100%' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                        <Text strong style={{ color: textC }}>
                                            {index + 1}. {todo.action}
                                        </Text>
                                        <Tag color={priorityColor(todo.priority)} style={{ marginInlineEnd: 0 }}>
                                            {todo.priority}
                                        </Tag>
                                    </div>
                                    <Text style={{ color: mutedC, fontSize: 12 }}>{todo.reason}</Text>
                                </div>
                            </List.Item>
                        )}
                    />
                </div>
            ) : (
                <Empty
                    description={<Text style={{ color: mutedC }}>No TODO data</Text>}
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
                defaultActiveKey="todos"
                items={items}
                size="small"
                style={{ marginTop: 2 }}
            />
        </Card>
    );
}
