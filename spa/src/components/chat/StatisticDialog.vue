<template>
    <div class="p-6 bg-white rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">聊天数据分析</h2>

        <div class="mb-10">
            <h3 class="text-xl font-semibold mb-4">每日消息数量统计</h3>
            <div class="bg-gray-50 p-4 rounded-lg">
                <canvas ref="messageChartRef" height="300"></canvas>
            </div>
        </div>

        <div>
            <h3 class="text-xl font-semibold mb-4">平均回复间隔时间趋势</h3>
            <div class="bg-gray-50 p-4 rounded-lg">
                <canvas ref="responseTimeChartRef" height="300"></canvas>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import Chart from 'chart.js/auto';
import type { Message } from '@/common/type-interface';


const props = defineProps({
    messages: {
        type: Array as () => Message[],
        required: true,
        default: () => []
    }
})

// 消息图表引用
const messageChartRef = ref<HTMLCanvasElement | null>(null);
// 回复时间图表引用
const responseTimeChartRef = ref<HTMLCanvasElement | null>(null);

// 按日期分组消息
const messagesByDate = computed(() => {
    const groups: Record<string, Message[]> = {};

    props.messages.forEach(message => {
        const date = message.time.split(' ')[0];
        if (!groups[date]) groups[date] = [];
        groups[date].push(message);
    });

    return groups;
});

// 计算文本中各类字符数量
const countCharacters = (text: string) => {
    const englishWords = text.match(/[a-zA-Z]+/g)?.length || 0;
    const chineseChars = text.match(/[\u4e00-\u9fa5]/g)?.length || 0;
    const japaneseKana = text.match(/[\u3040-\u309F\u30A0-\u30FF]/g)?.length || 0;
    const japaneseKanji = text.match(/[\u4E00-\u9FFF]/g)?.length || 0;

    return { englishWords, chineseChars, japaneseKana, japaneseKanji };
};

// 准备消息图表数据
const prepareMessageChartData = () => {
    const dates = Object.keys(messagesByDate.value).sort();
    const userCounts = dates.map(date =>
        messagesByDate.value[date].filter(m => m.role === 'user').length
    );
    const assistantCounts = dates.map(date =>
        messagesByDate.value[date].filter(m => m.role === 'assistant').length
    );

    return { dates, userCounts, assistantCounts };
};

// 准备回复时间图表数据
const prepareResponseTimeChartData = () => {
    const dates = Object.keys(messagesByDate.value).sort();
    const avgResponseTimes: number[] = [];

    dates.forEach(date => {
        const messages = messagesByDate.value[date];
        const userMessages = messages.filter(m => m.role === 'user');
        const assistantMessages = messages.filter(m => m.role === 'assistant');

        if (userMessages.length === 0 || assistantMessages.length === 0) {
            avgResponseTimes.push(0);
            return;
        }

        let totalResponseTime = 0;
        let responseCount = 0;

        userMessages.forEach(userMsg => {
            // 查找该用户消息之后最近的assistant回复
            const nextAssistantMsg = assistantMessages.find(
                msg => new Date(msg.time) > new Date(userMsg.time)
            );

            if (nextAssistantMsg) {
                const timeDiff =
                    (new Date(nextAssistantMsg.time).getTime() - new Date(userMsg.time).getTime()) / 1000 / 60; // 分钟

                // 如果间隔不超过10分钟，视作同一会话
                if (timeDiff <= 10) {
                    totalResponseTime += timeDiff;
                    responseCount++;
                }
            }
        });

        avgResponseTimes.push(responseCount > 0 ? totalResponseTime / responseCount : 0);
    });

    return { dates, avgResponseTimes };
};

// 创建消息图表
const createMessageChart = () => {
    if (!messageChartRef.value) return;

    const { dates, userCounts, assistantCounts } = prepareMessageChartData();

    const ctx = messageChartRef.value.getContext('2d');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: '用户消息数',
                    data: userCounts,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'AI回复数',
                    data: assistantCounts,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: (context) => {
                            const dateIndex = context.dataIndex;
                            if (dateIndex === undefined || !dates[dateIndex]) return [];

                            const date = dates[dateIndex];
                            const messages = messagesByDate.value[date] || [];

                            if (!messages.length) return [];

                            const userMessages = messages.filter(m => m.role === 'user');
                            const assistantMessages = messages.filter(m => m.role === 'assistant');

                            // 合并所有消息文本
                            const allText = messages.map(m => m.raw_text).join('');
                            const { englishWords, chineseChars, japaneseKana, japaneseKanji } = countCharacters(allText);

                            return [
                                `用户消息: ${userMessages.length} 条`,
                                `AI回复: ${assistantMessages.length} 条`,
                                `英文单词: ${englishWords} 个`,
                                `中文汉字: ${chineseChars} 个`,
                                `日语假名: ${japaneseKana} 个`,
                                `日语汉字: ${japaneseKanji} 个`
                            ];
                        }
                    }
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '每日消息数量统计'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '消息数量'
                    },
                    beginAtZero: true
                }
            }
        }
    });
};

// 创建回复时间图表
const createResponseTimeChart = () => {
    if (!responseTimeChartRef.value) return;

    const { dates, avgResponseTimes } = prepareResponseTimeChartData();

    const ctx = responseTimeChartRef.value.getContext('2d');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [{
                label: '平均回复间隔时间(分钟)',
                data: avgResponseTimes,
                backgroundColor: '#8b5cf6',
                borderColor: '#7c3aed',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '平均回复间隔时间趋势'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '日期'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '平均回复间隔时间(分钟)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
};

// 初始化图表
const initCharts = () => {
    createMessageChart();
    createResponseTimeChart();
};

onMounted(() => {
    initCharts();
});

</script>