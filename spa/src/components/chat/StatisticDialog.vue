<template>

    <div class="p-6 bg-white rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">聊天数据分析</h2>

        <el-select v-model="lastPeriod" placeholder="请选择时间范围" @change="initCharts" style="max-width: 150px;">
            <el-option v-for="item in dateRangeOptions" :key="item" :label="item" :value="dateRange[item]" />
        </el-select>

        <div class="chart-container">
            <h3 class="text-xl font-semibold mb-4">每日字符数量统计</h3>

            <div class="card-container">
                <el-row :gutter="16">

                    <el-col :span="5">
                        <div class="statistic-card">
                            <el-statistic :value="totalCharCounts_">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        总对话字数
                                        <el-tooltip effect="dark" content="所有用户发送的字数和AI回复的字数和" placement="top">
                                            <el-icon style="margin-left: 4px" :size="12">
                                                <Warning />
                                            </el-icon>
                                        </el-tooltip>
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">
                                        {{ totalMessageCounts }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每天</span>
                                    <span class="green">
                                        {{ (totalCharCounts_ / totalDays).toFixed(0) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="5">
                        <div class="statistic-card">
                            <el-statistic :value="totalUserCharCounts">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        用户发送总字数
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">
                                        {{ totalUserMessageCounts }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每天</span>
                                    <span class="green">
                                        {{ (totalUserCharCounts / totalDays).toFixed(0) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>

                    <el-col :span="4">
                        <div class="statistic-card">
                            <el-statistic :value="totalDays">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        总天数
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>平均发送消息条数</span>
                                    <span class="green">
                                        {{ (totalUserMessageCounts / totalDays).toFixed(0) }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>平均消息条数</span>
                                    <span class="green">
                                        {{ (totalMessageCounts / totalDays).toFixed(0) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>

                    <el-col :span="5">
                        <div class="statistic-card">
                            <el-statistic :value="totalTodayCharCounts" title="New transactions today">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        今日总对话字数
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">
                                        {{ totalTodayMessageCounts }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>比平均</span>
                                    <span :class="diffTodayCharCountsThanAverage > 0 ? 'green' : 'red'">
                                        {{ diffTodayCharCountsThanAverage.toFixed(0) }}
                                        <el-icon v-if="diffTodayCharCountsThanAverage >= 0">
                                            <CaretTop />
                                        </el-icon>
                                        <el-icon v-else>
                                            <CaretBottom />
                                        </el-icon>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="5">
                        <div class="statistic-card">
                            <el-statistic :value="totalTodayUserCharCounts" title="New transactions today">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        今日用户发送总字数
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">
                                        {{ totalTodayUserMessageCounts }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>比平均</span>
                                    <span :class="diffTodayUserCharCountsThanAverage > 0 ? 'green' : 'red'">
                                        {{ diffTodayUserCharCountsThanAverage.toFixed(0) }}
                                        <el-icon v-if="diffTodayUserCharCountsThanAverage >= 0">
                                            <CaretTop />
                                        </el-icon>
                                        <el-icon v-else>
                                            <CaretBottom />
                                        </el-icon>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>

                </el-row>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg" style="height: 80vh">
                <canvas ref="messageChartRef" class="w-full"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h3 class="text-xl font-semibold mb-4">平均回复间隔时间趋势</h3>
            <div class="card-container">
                <el-row :gutter="16">

                    <el-col :span="8">
                        <div class="statistic-card">
                            <el-statistic :value="totalResponseTimeHHMM">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        总读写时间
                                        <el-tooltip effect="dark" content="所有用户发送的字数和AI回复的字数和" placement="top">
                                            <el-icon style="margin-left: 4px" :size="12">
                                                <Warning />
                                            </el-icon>
                                        </el-tooltip>
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>平均回复间隔时间</span>
                                    <span class="green">
                                        {{ (totalResponseTime_ / totalResponseTimeCounts).toFixed(2) }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每分钟读写字数</span>
                                    <span class="green">
                                        {{ (totalCharReadAndWriteCounts / totalResponseTime_).toFixed(2) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>

                    <el-col :span="8">
                        <div class="statistic-card">
                            <el-statistic :value="responseTimeHHMMperDay">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        平均每天读写时间
                                    </div>
                                </template>
                            </el-statistic>
                        </div>
                    </el-col>


                    <el-col :span="8">
                        <div class="statistic-card">
                            <el-statistic :value="todayTotalResponseTimeHHMM">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">
                                        今日读写时间
                                    </div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>平均回复间隔时间</span>
                                    <span class="green">
                                        {{ (todayTotalResponseTime_ / todayTotalResponseTimeCounts).toFixed(2) }}
                                    </span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每分钟读写字数</span>
                                    <span class="green">
                                        {{ (todayTotalCharReadAndWriteCounts / todayTotalResponseTime_).toFixed(2) }}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                </el-row>
            </div>
            <div class="bg-gray-50 p-4 rounded-lg" style="height: 80vh">
                <canvas ref="responseTimeChartRef" class="w-full"></canvas>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import Chart from 'chart.js/auto';
import type { Message } from '@/common/type-interface';
import { ArrowRight, CaretBottom, CaretTop, Warning } from '@element-plus/icons-vue'

const dateRange: Record<string, number> = { "最近7天": 7, "最近30天": 30, "全部": -1 };
const dateRangeOptions = Object.keys(dateRange);
const lastPeriod = ref<number>(7);
const totalUserCharCounts = ref<number>(0);
const totalCharCounts_ = ref<number>(0);
const totalUserMessageCounts = ref<number>(0);
const totalMessageCounts = ref<number>(0);
const totalTodayUserCharCounts = ref<number>(0);
const totalTodayUserMessageCounts = ref<number>(0);
const totalTodayCharCounts = ref<number>(0);
const totalTodayMessageCounts = ref<number>(0);
const totalDays = ref<number>(0);

const totalResponseTime_ = ref<number>(0);
const totalResponseTimeCounts = ref<number>(0);
const totalCharReadAndWriteCounts = ref<number>(0);
const todayTotalResponseTime_ = ref<number>(0);
const todayTotalResponseTimeCounts = ref<number>(0);
const todayTotalCharReadAndWriteCounts = ref<number>(0);

const diffTodayUserCharCountsThanAverage = computed(() => {
    return (totalTodayUserCharCounts.value - (totalUserCharCounts.value / totalDays.value));
})

const diffTodayCharCountsThanAverage = computed(() => {
    return (totalTodayCharCounts.value - (totalCharCounts_.value / totalDays.value));
})

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

const formatDataToLocalString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // 月份从 0 开始
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`; // 本地日期
}

const formatMinutesToHHMM = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const minutes_ = (minutes % 60).toFixed(0);
    return `${hours.toString().padStart(2, '0')} 小时 ${minutes_.toString().padStart(2, '0')} 分钟`;
}

const totalResponseTimeHHMM = computed(() => {
    return formatMinutesToHHMM(totalResponseTime_.value);
})

const responseTimeHHMMperDay = computed(() => {
    return formatMinutesToHHMM(totalResponseTime_.value / totalDays.value);
})

const todayTotalResponseTimeHHMM = computed(() => {
    return formatMinutesToHHMM(todayTotalResponseTime_.value);
})

// 生成从开始日期到结束日期的所有日期
const generateDateRange = (startDate: string, endDate: string): string[] => {
    const dates: string[] = [];
    const currentDate = new Date(startDate);
    const finalDate = new Date(endDate);

    while (currentDate <= finalDate) {
        // 格式化日期为 YYYY-MM-DD
        dates.push(formatDataToLocalString(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }

    return dates;
};

// 获取完整日期范围（从最早有数据日期到今天）
const getFullDateRange = (): string[] => {
    const existingDates = Object.keys(messagesByDate.value);
    const today = formatDataToLocalString(new Date()); // 今天的日期（YYYY-MM-DD）
    let startData: string = today
    if (lastPeriod.value === -1) {
        const earliestDate = existingDates.reduce((a, b) => (new Date(a) < new Date(b) ? a : b));
        startData = earliestDate
    } else {
        const lastDate = new Date();
        lastDate.setDate(lastDate.getDate() - lastPeriod.value + 1);
        startData = formatDataToLocalString(lastDate)
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
    totalDays.value = fullDates.length;
    const userCharCounts: number[] = [];
    const totalCharCounts: number[] = [];

    totalMessageCounts.value = 0;
    totalUserMessageCounts.value = 0;
    totalTodayMessageCounts.value = 0;
    totalTodayUserMessageCounts.value = 0;

    fullDates.forEach(date => {
        const messages = messagesByDate.value[date] || [];
        // 用户发送字数（无数据则为0）
        const userMsgs = messages.filter(m => m.role === 'user');
        totalUserMessageCounts.value += userMsgs.length;
        const userCount = userMsgs.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
        userCharCounts.push(userCount);

        // 总字数（无数据则为0）
        const totalCount = messages.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
        totalMessageCounts.value += messages.length;
        totalCharCounts.push(totalCount);
    });

    totalTodayUserMessageCounts.value = messagesByDate.value[fullDates[fullDates.length - 1]]?.filter(m => m.role === 'user').length || 0;
    totalTodayMessageCounts.value = messagesByDate.value[fullDates[fullDates.length - 1]]?.length || 0;

    return { dates: fullDates, userCharCounts, totalCharCounts };
};

// 准备回复时间图表数据（无数据日期用前后平均值填充）
const prepareResponseTimeChartData = () => {
    const fullDates = getFullDateRange();
    // 先收集有数据的日期及其对应值
    const rawResponseTimes: Record<string, number> = {};
    const rawWordsPerMinute: Record<string, number> = {};
    const readAndWriteTimeCounts: Record<string, number> = {};

    totalResponseTime_.value = 0;
    totalResponseTimeCounts.value = 0;
    totalCharReadAndWriteCounts.value = 0;
    todayTotalResponseTime_.value = 0;
    todayTotalResponseTimeCounts.value = 0;
    todayTotalCharReadAndWriteCounts.value = 0;
    const todayDate = fullDates[fullDates.length - 1];

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

        totalResponseTime_.value += totalResponseTime;
        totalResponseTimeCounts.value += responseCount;
        totalCharReadAndWriteCounts.value += totalWords;
        if (date === todayDate) {
            todayTotalResponseTime_.value = totalResponseTime;
            todayTotalResponseTimeCounts.value = responseCount;
            todayTotalCharReadAndWriteCounts.value = totalWords;
        }

        readAndWriteTimeCounts[date] = totalResponseTime;
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

    return { dates: fullDates, avgResponseTimes, avgWordsPerMinute, readAndWriteTimeCounts };
};

// 创建消息图表
const createMessageChart = () => {
    if (!messageChartRef.value) return;

    const { dates, userCharCounts, totalCharCounts } = prepareMessageChartData();
    totalUserCharCounts.value = userCharCounts.reduce((total, count) => total + count, 0);
    totalCharCounts_.value = totalCharCounts.reduce((total, count) => total + count, 0);
    totalTodayUserCharCounts.value = userCharCounts[userCharCounts.length - 1];
    totalTodayCharCounts.value = totalCharCounts[totalCharCounts.length - 1];

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

    const { dates, avgResponseTimes, avgWordsPerMinute, readAndWriteTimeCounts } = prepareResponseTimeChartData();

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
                    callbacks: {
                        afterLabel: (context) => {
                            const dateIndex = context.dataIndex;
                            const date = dates[dateIndex];

                            return [
                                `总读写时间: ${formatMinutesToHHMM(readAndWriteTimeCounts[date])}`,
                            ];
                        }
                    }
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

<style scoped></style>