<template>
    <div class="p-6 bg-white rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">聊天数据分析</h2>

        <el-select v-model="lastPeriod" placeholder="请选择时间范围" @change="initCharts" style="max-width: 150px;">
            <el-option v-for="item in dateRangeOptions" :key="item" :label="item" :value="dateRange[item]" />
        </el-select>

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

const dateRange: Record<string, number> = { "最近7天": 7, "最近30天": 30, "全部": -1 };
const dateRangeOptions = Object.keys(dateRange);
const lastPeriod = ref<number>(7);

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

// 生成从开始日期到结束日期的所有日期
const generateDateRange = (startDate: string, endDate: string): string[] => {
    const dates: string[] = [];
    const currentDate = new Date(startDate);
    const finalDate = new Date(endDate);

    while (currentDate <= finalDate) {
        // 格式化日期为 YYYY-MM-DD
        const year = currentDate.getFullYear();
        const month = String(currentDate.getMonth() + 1).padStart(2, '0');
        const day = String(currentDate.getDate()).padStart(2, '0');
        dates.push(`${year}-${month}-${day}`);

        currentDate.setDate(currentDate.getDate() + 1);
    }

    return dates;
};

// 获取完整日期范围（从最早有数据日期到今天）
const getFullDateRange = (): string[] => {
    const existingDates = Object.keys(messagesByDate.value);
    const today = new Date().toISOString().split('T')[0]; // 今天的日期（YYYY-MM-DD）
    let startData: string = today
    if (lastPeriod.value === -1) {
        const earliestDate = existingDates.reduce((a, b) => (new Date(a) < new Date(b) ? a : b));
        startData = earliestDate
    } else {
        const lastDate = new Date();
        lastDate.setDate(lastDate.getDate() - lastPeriod.value);
        startData = lastDate.toISOString().split('T')[0]
    }
    return generateDateRange(startData, today);
};

// 计算文本中各类字符数量
const countCharacters = (text: string) => {
    // 英文单词及标点符号
    const englishWords = text.match(/[a-zA-Z]+/g)?.length || 0;
    const englishPunctuation = text.match(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g)?.length || 0;

    // 中文字符及标点符号
    const chineseChars = text.match(/[\u4e00-\u9fa5]/g)?.length || 0;
    const chinesePunctuation = text.match(/[\u3000-\u303F\uFF00-\uFFEF]/g)?.length || 0;

    // 日语字符及标点符号
    const japaneseKana = text.match(/[\u3040-\u309F\u30A0-\u30FF]/g)?.length || 0;
    const japaneseKanji = text.match(/[\u4E00-\u9FFF]/g)?.length || 0;
    const japanesePunctuation = text.match(/[\u3000-\u303F\u30FB-\u30FC\uFF01-\uFF5E]/g)?.length || 0;

    // 合并日语统计
    const japaneseTotal = japaneseKana + japaneseKanji + japanesePunctuation;

    return {
        englishWords,
        englishPunctuation,
        chineseChars,
        chinesePunctuation,
        japaneseTotal
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

// 准备消息图表数据（无数据日期用0填充）
const prepareMessageChartData = () => {
    const fullDates = getFullDateRange();
    const userCharCounts: number[] = [];
    const totalCharCounts: number[] = [];

    fullDates.forEach(date => {
        const messages = messagesByDate.value[date] || [];
        // 用户发送字数（无数据则为0）
        const userMsgs = messages.filter(m => m.role === 'user');
        const userCount = userMsgs.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
        userCharCounts.push(userCount);

        // 总字数（无数据则为0）
        const totalCount = messages.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
        totalCharCounts.push(totalCount);
    });

    return { dates: fullDates, userCharCounts, totalCharCounts };
};

// 准备回复时间图表数据（无数据日期用前后平均值填充）
const prepareResponseTimeChartData = () => {
    const fullDates = getFullDateRange();
    // 先收集有数据的日期及其对应值
    const rawResponseTimes: Record<string, number> = {};
    const rawWordsPerMinute: Record<string, number> = {};

    // 初始化原始数据
    fullDates.forEach(date => {
        const messages = messagesByDate.value[date] || [];
        const userMessages = messages.filter(m => m.role === 'user');
        const assistantMessages = messages.filter(m => m.role === 'assistant');
        const reversedAssistantMsg = [...assistantMessages].reverse(); // 复制后反转，避免修改原数组

        let totalResponseTime = 0;
        let totalWords = 0;
        let responseCount = 0;

        userMessages.forEach(userMsg => {
            const prevAssistantMsg = reversedAssistantMsg.find(
                msg => new Date(msg.time) < new Date(userMsg.time)
            );

            if (prevAssistantMsg) {
                const timeDiff =
                    (new Date(userMsg.time).getTime() - new Date(prevAssistantMsg.time).getTime()) / 1000 / 60; // 分钟

                if (timeDiff <= 10 && timeDiff > 0) {
                    totalResponseTime += timeDiff;
                    const readWords = getLanguageChars(prevAssistantMsg.raw_text, props.language);
                    const replyWords = getLanguageChars(userMsg.raw_text, props.language);
                    totalWords += readWords + replyWords;
                    responseCount++;
                }
            }
        });

        // 只有有有效数据时才记录（避免0值干扰后续计算）
        if (responseCount > 0) {
            rawResponseTimes[date] = totalResponseTime / responseCount;
            rawWordsPerMinute[date] = totalWords / totalResponseTime;
        }
    });

    // 处理空数据：用前后最近的非空值的平均值填充
    const fillMissingValues = (rawData: Record<string, number>, dates: string[]): number[] => {
        return dates.map((date, index) => {
            if (rawData[date] !== undefined) {
                return rawData[date]; // 有数据直接返回
            }

            // 查找前一个有数据的日期
            let prevValue: number | null = null;
            for (let i = index - 1; i >= 0; i--) {
                if (rawData[dates[i]] !== undefined) {
                    prevValue = rawData[dates[i]];
                    break;
                }
            }

            // 查找后一个有数据的日期
            let nextValue: number | null = null;
            for (let i = index + 1; i < dates.length; i++) {
                if (rawData[dates[i]] !== undefined) {
                    nextValue = rawData[dates[i]];
                    break;
                }
            }

            // 计算填充值
            if (prevValue !== null && nextValue !== null) {
                return (prevValue + nextValue) / 2; // 前后都有数据，取平均
            } else if (prevValue !== null) {
                return prevValue; // 只有前有数据，用前值
            } else if (nextValue !== null) {
                return nextValue; // 只有后有数据，用后值
            } else {
                return 0; // 完全没有数据，用0
            }
        });
    };

    // 填充空值
    const avgResponseTimes = fillMissingValues(rawResponseTimes, fullDates);
    const avgWordsPerMinute = fillMissingValues(rawWordsPerMinute, fullDates);

    return { dates: fullDates, avgResponseTimes, avgWordsPerMinute };
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
                            const date = dates[dateIndex];
                            const messages = messagesByDate.value[date] || [];

                            const isUserDataset = datasetIndex === 0;
                            const filteredMessages = isUserDataset
                                ? messages.filter(m => m.role === 'user')
                                : messages;

                            return [
                                `消息条数: ${filteredMessages.length}`,
                                `${props.language}字数: ${context.raw}`
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
                    },
                    ticks: {
                        // 日期较多时自动旋转标签，避免重叠
                        maxRotation: 45,
                        minRotation: 45
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
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: '平均每分钟读说字数',
                    data: avgWordsPerMinute,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
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
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
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
                        drawOnChartArea: false,
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
    // initCharts();
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