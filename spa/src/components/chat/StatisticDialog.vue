<template>
    <div class="p-6 bg-white rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">聊天数据分析</h2>

        <div class="mb-10">
            <h3 class="text-xl font-semibold mb-4">每日字符数量统计</h3>
            <div class="bg-gray-50 p-4 rounded-lg">
                <canvas ref="messageChartRef" class="w-full"></canvas>
            </div>
        </div>

        <div>
            <h3 class="text-xl font-semibold mb-4">平均回复间隔时间趋势</h3>
            <div class="bg-gray-50 p-4 rounded-lg">
                <canvas ref="responseTimeChartRef" class="w-full"></canvas>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import Chart from 'chart.js/auto';
import type { Message } from '@/common/type-interface';

declare global {
    interface Window {
        messageChartInstance?: Chart;
        responseTimeChartInstance?: Chart;
    }
}

const props = defineProps({
    messages: {
        type: Array as () => Message[],
        required: true,
        default: () => []
    },
    language: {
        type: String,
        required: true,
        default: 'English'
    }
})

const chatMessage = ref<Message[]>(props.messages);

watch(() => props.messages, async () => {
    chatMessage.value = props.messages;
    await nextTick();
    initCharts();
})

// 消息图表引用
const messageChartRef = ref<HTMLCanvasElement | null>(null);
// 回复时间图表引用
const responseTimeChartRef = ref<HTMLCanvasElement | null>(null);

// 按日期分组消息
const messagesByDate = computed(() => {
    const groups: Record<string, Message[]> = {};

    chatMessage.value.forEach(message => {
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

// 计算字符总数
const countTotalChars = (text: string) => {
    return text.length;
};

// 准备消息图表数据
const prepareMessageChartData = () => {
    const dates = Object.keys(messagesByDate.value).sort();
    const userCharCounts = dates.map(date => {
        const userMessages = messagesByDate.value[date].filter(m => m.role === 'user');
        return userMessages.reduce((total, msg) => total + countTotalChars(msg.raw_text), 0);
    });

    const totalCharCounts = dates.map(date => {
        return messagesByDate.value[date].reduce((total, msg) => total + countTotalChars(msg.raw_text), 0);
    });

    return { dates, userCharCounts, totalCharCounts };
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

    const { dates, userCharCounts, totalCharCounts } = prepareMessageChartData();

    const ctx = messageChartRef.value.getContext('2d');
    if (!ctx) return;

    // 销毁旧图表
    if (window.messageChartInstance) {
        window.messageChartInstance.destroy();
    }

    window.messageChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                {
                    label: '用户发送字符数',
                    data: userCharCounts,
                    backgroundColor: '#3b82f6',
                    borderColor: '#2563eb',
                    borderWidth: 1
                },
                {
                    label: '总字符数',
                    data: totalCharCounts,
                    backgroundColor: '#f97316',
                    borderColor: '#ea580c',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: (context) => {
                            const dateIndex = context.dataIndex;
                            const datasetIndex = context.datasetIndex;

                            if (dateIndex === undefined || !dates[dateIndex]) return [];

                            const date = dates[dateIndex];
                            const messages = messagesByDate.value[date] || [];
                            const isUserDataset = datasetIndex === 0;
                            const filteredMessages = isUserDataset
                                ? messages.filter(m => m.role === 'user')
                                : messages;

                            if (!filteredMessages.length) return [];

                            // 合并所有消息文本
                            const allText = filteredMessages.map(m => m.raw_text).join('');
                            const { englishWords, chineseChars, japaneseKana, japaneseKanji } = countCharacters(allText);

                            return [
                                `消息条数: ${filteredMessages.length}`,
                                `英文单词: ${englishWords}`,
                                `中文: ${chineseChars}`,
                                `日语: ${japaneseKana + japaneseKanji}`,
                                `总字符数: ${countTotalChars(allText)}`
                            ];
                        }
                    }
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '每日字符数量统计'
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
                        text: '字符数量'
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

    // 销毁旧图表
    if (window.responseTimeChartInstance) {
        window.responseTimeChartInstance.destroy();
    }

    window.responseTimeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '平均回复间隔时间(分钟)',
                data: avgResponseTimes,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
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

// 监听窗口大小变化，调整图表
const handleResize = () => {
    initCharts();
};

onMounted(() => {
    initCharts();
    window.addEventListener('resize', handleResize);
});

// 组件卸载时移除事件监听
onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (window.messageChartInstance) {
        window.messageChartInstance.destroy();
    }
    if (window.responseTimeChartInstance) {
        window.responseTimeChartInstance.destroy();
    }
});
</script>