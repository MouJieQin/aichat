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
    // 英文单词及标点符号（仅包含ASCII范围）
    const englishWords = text.match(/[a-zA-Z]+/g)?.length || 0;
    const englishPunctuation = text.match(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g)?.length || 0;

    // 中文字符及标点符号（独立范围，不考虑重叠）
    const chineseChars = text.match(/[\u4e00-\u9fa5]/g)?.length || 0;
    const chinesePunctuation = text.match(/[\u3000-\u303F\uFF00-\uFFEF]/g)?.length || 0;

    // 日语字符及标点符号（独立范围，不考虑重叠）
    const japaneseKana = text.match(/[\u3040-\u309F\u30A0-\u30FF]/g)?.length || 0;
    const japaneseKanji = text.match(/[\u4E00-\u9FFF]/g)?.length || 0;
    // 修正日语标点符号范围，排除与英文重复的半角符号
    const japanesePunctuation = text.match(/[\u3000-\u303F\u30FB-\u30FC\uFF01-\uFF5E]/g)?.length || 0;

    // 合并日语统计
    const japaneseTotal = japaneseKana + japaneseKanji + japanesePunctuation;

    return {
        englishWords,
        englishPunctuation,
        chineseChars,
        chinesePunctuation,
        japaneseTotal,
        japanesePunctuation,
        // 保留单独统计项
        japaneseKana,
        japaneseKanji
    };
};

// 获取指定语言的字符数
const getLanguageChars = (text: string, language: string) => {
    const {
        englishWords,
        englishPunctuation,
        chineseChars,
        chinesePunctuation,
        japaneseTotal,
    } = countCharacters(text);

    switch (language) {
        case 'English':
            return englishWords + englishPunctuation;
        case '中文':
            return chineseChars + chinesePunctuation;
        case '日本語':
            return japaneseTotal;
        default:
            return text.length;
    }
};

// 准备消息图表数据
const prepareMessageChartData = () => {
    const dates = Object.keys(messagesByDate.value).sort();
    const userCharCounts = dates.map(date => {
        const userMessages = messagesByDate.value[date].filter(m => m.role === 'user');
        return userMessages.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
    });

    const totalCharCounts = dates.map(date => {
        return messagesByDate.value[date].reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
    });

    return { dates, userCharCounts, totalCharCounts };
};

// 准备回复时间图表数据
const prepareResponseTimeChartData = () => {
    const dates = Object.keys(messagesByDate.value).sort();
    let avgResponseTimes: number[] = [];
    let avgWordsPerMinute: number[] = [];

    dates.forEach(date => {
        const messages = messagesByDate.value[date];
        const userMessages = messages.filter(m => m.role === 'user');
        const assistantMessages = messages.filter(m => m.role === 'assistant');
        const reversedAssistantMsg = assistantMessages.reverse();

        if (userMessages.length === 0 || reversedAssistantMsg.length === 0) {
            avgResponseTimes.push(0);
            avgWordsPerMinute.push(0);
            return;
        }

        let totalResponseTime = 0;
        let totalWords = 0;
        let responseCount = 0;

        userMessages.forEach(userMsg => {
            // 查找该用户消息之前最近的assistant回复
            const prevAssistantMsg = reversedAssistantMsg.find(
                msg => new Date(msg.time) < new Date(userMsg.time)
            );

            if (prevAssistantMsg) {
                const timeDiff =
                    (new Date(userMsg.time).getTime() - new Date(prevAssistantMsg.time).getTime()) / 1000 / 60; // 分钟

                // 如果间隔不超过10分钟，视作同一会话
                if (timeDiff <= 10 && timeDiff > 0) {
                    totalResponseTime += timeDiff;
                    // 计算阅读的字数（上一条AI回复）和用户回复的字数
                    const readWords = getLanguageChars(prevAssistantMsg.raw_text, props.language);
                    const replyWords = getLanguageChars(userMsg.raw_text, props.language);
                    totalWords += readWords + replyWords;
                    responseCount++;
                }
            }
        });

        avgResponseTimes.push(responseCount > 0 ? totalResponseTime / responseCount : 0);
        // 计算平均每分钟读说字数
        avgWordsPerMinute.push(responseCount > 0 && totalResponseTime > 0
            ? totalWords / totalResponseTime
            : 0);
    });

    // 处理0值：使用前后平均值
    const processZeroValues = (values: number[]) => {
        return values.map((value, index) => {
            if (value !== 0) return value;

            // 查找前一个非零值
            let prevIndex = index - 1;
            while (prevIndex >= 0 && values[prevIndex] === 0) {
                prevIndex--;
            }

            // 查找后一个非零值
            let nextIndex = index + 1;
            while (nextIndex < values.length && values[nextIndex] === 0) {
                nextIndex++;
            }

            // 如果前后都有非零值，取平均值
            if (prevIndex >= 0 && nextIndex < values.length) {
                return (values[prevIndex] + values[nextIndex]) / 2;
            }

            // 如果只有前一个非零值
            if (prevIndex >= 0) {
                return values[prevIndex];
            }

            // 如果只有后一个非零值
            if (nextIndex < values.length) {
                return values[nextIndex];
            }

            // 没有非零值，保持0
            return 0;
        });
    };

    return {
        dates,
        avgResponseTimes: processZeroValues(avgResponseTimes),
        avgWordsPerMinute: processZeroValues(avgWordsPerMinute)
    };
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
                    label: '用户发送字数',
                    data: userCharCounts,
                    backgroundColor: '#3b82f6',
                    borderColor: '#2563eb',
                    borderWidth: 1
                },
                {
                    label: '总字数',
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
                            const charCount = getLanguageChars(allText, props.language);

                            return [
                                `消息条数: ${filteredMessages.length}`,
                                `${props.language}字数: ${charCount}`
                            ];
                        }
                    }
                },
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: `每日${props.language}字数统计`
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
                        text: `${props.language}字数`
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

    const { dates, avgResponseTimes, avgWordsPerMinute } = prepareResponseTimeChartData();

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
            datasets: [
                {
                    label: '平均回复间隔时间(分钟)',
                    data: avgResponseTimes,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: avgResponseTimes.map(time => time > 0 ? 4 : 0),
                    pointHoverRadius: avgResponseTimes.map(time => time > 0 ? 6 : 0),
                    yAxisID: 'y'
                },
                {
                    label: '平均每分钟读说字数',
                    data: avgWordsPerMinute,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: avgWordsPerMinute.map(words => words > 0 ? 4 : 0),
                    pointHoverRadius: avgWordsPerMinute.map(words => words > 0 ? 6 : 0),
                    yAxisID: 'y1'
                }
            ]
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
                    text: '平均回复间隔时间与读说速度趋势'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
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
                    beginAtZero: true,
                    position: 'left',
                },
                y1: {
                    title: {
                        display: true,
                        text: '平均每分钟读说字数'
                    },
                    beginAtZero: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false, // 只在自己的轴区域绘制网格线
                    },
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