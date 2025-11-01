<template>
    <div class="p-6 bg-white rounded-lg shadow-lg">
        <h2 class="text-2xl font-bold mb-6 text-center">聊天数据分析</h2>

        <el-select v-model="lastPeriod" placeholder="请选择时间范围" @change="initCharts" style="max-width: 150px;">
            <el-option v-for="item in dateRangeOptions" :key="item" :label="item" :value="dateRange[item]" />
        </el-select>

        <div class="chart-container">
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
                                    <span class="green">{{ totalMessageCounts }}</span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每天</span>
                                    <span class="green">{{ (totalCharCounts_ / totalDays).toFixed(0) }}</span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="5">
                        <div class="statistic-card">
                            <el-statistic :value="totalUserCharCounts">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">用户发送总字数</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">{{ totalUserMessageCounts }}</span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每天</span>
                                    <span class="green">{{ (totalUserCharCounts / totalDays).toFixed(0) }}</span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="4">
                        <div class="statistic-card">
                            <el-statistic :value="totalDays">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">总天数</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>平均发送消息条数</span>
                                    <span class="green">{{ (totalUserMessageCounts / totalDays).toFixed(0) }}</span>
                                </div>
                                <div class="footer-item">
                                    <span>平均消息条数</span>
                                    <span class="green">{{ (totalMessageCounts / totalDays).toFixed(0) }}</span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="5">
                        <div class="statistic-card">
                            <el-statistic :value="totalTodayCharCounts">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">今日总对话字数</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">{{ totalTodayMessageCounts }}</span>
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
                            <el-statistic :value="totalTodayUserCharCounts">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">今日用户发送总字数</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>总消息条数</span>
                                    <span class="green">{{ totalTodayUserMessageCounts }}</span>
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

            <div class="card-container">
                <el-row :gutter="16">
                    <el-col :span="8">
                        <div class="statistic-card">
                            <el-statistic :value="totalResponseTime_" :formatter="formatMinutesToHHMM">
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
                                        {{ totalResponseTimeCounts <= 0 ? 0 : (totalResponseTime_ /
                                            totalResponseTimeCounts).toFixed(2) }} </span>
                                </div>
                                <div class="footer-item">
                                    <span>平均每分钟读写字数</span>
                                    <span class="green">
                                        {{ totalResponseTimeCounts <= 0 ? 0 : (totalCharReadAndWriteCounts /
                                            totalResponseTime_).toFixed(2) }} </span>
                                </div>
                            </div>
                        </div>
                    </el-col>
                    <el-col :span="4">
                        <div class="statistic-card">
                            <el-statistic :value="responseTimePerDay" :formatter="formatMinutesToHHMM">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">平均每天读写时间</div>
                                </template>
                            </el-statistic>
                        </div>
                    </el-col>
                    <el-col :span="4">
                        <div class="statistic-card">
                            <el-statistic
                                :value="Number(todayTotalResponseTimeCounts <= 0 ? 0 : (todayTotalResponseTime_ / todayTotalResponseTimeCounts).toFixed(2))">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">今日平均回复间隔时间</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>比平均</span>
                                    <span :class="diffTodayResponseTimeThanAverage < 0 ? 'green' : 'red'">
                                        {{ diffTodayResponseTimeThanAverage.toFixed(2) }}%
                                        <el-icon v-if="diffTodayResponseTimeThanAverage > 0">
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
                    <el-col :span="4">
                        <div class="statistic-card">
                            <el-statistic
                                :value="Number(todayTotalResponseTimeCounts <= 0 ? 0 : (todayTotalCharReadAndWriteCounts / todayTotalResponseTime_).toFixed(2))">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">今日平均每分钟读写字数</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>比平均</span>
                                    <span :class="diffTodayCharReadAndWriteCountsThanAverage > 0 ? 'green' : 'red'">
                                        {{ diffTodayCharReadAndWriteCountsThanAverage.toFixed(2) }}%
                                        <el-icon v-if="diffTodayCharReadAndWriteCountsThanAverage >= 0">
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
                    <el-col :span="4">
                        <div class="statistic-card">
                            <el-statistic :value="todayTotalResponseTime_" :formatter="formatMinutesToHHMM">
                                <template #title>
                                    <div style="display: inline-flex; align-items: center">今日读写时间</div>
                                </template>
                            </el-statistic>
                            <div class="statistic-footer">
                                <div class="footer-item">
                                    <span>比平均</span>
                                    <span :class="todayTotalResponseTime_ - responseTimePerDay >= 0 ? 'green' : 'red'">
                                        {{ formatMinutesToHHMM(todayTotalResponseTime_ - responseTimePerDay) }}
                                        <el-icon v-if="todayTotalResponseTime_ - responseTimePerDay >= 0">
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
        </div>

        <div class="chart-container">
            <h3 class="text-xl font-semibold mb-4">每日字符数量统计</h3>
            <div class="bg-gray-50 p-4 rounded-lg" style="height: 80vh">
                <canvas ref="messageChartRef" class="w-full"></canvas>
            </div>
        </div>

        <div class="chart-container">
            <h3 class="text-xl font-semibold mb-4">平均回复间隔时间趋势</h3>
            <div class="bg-gray-50 p-4 rounded-lg" style="height: 80vh">
                <canvas ref="responseTimeChartRef" class="w-full"></canvas>
            </div>
        </div>

        <!-- 新增：今日回复间隔时间趋势图表 -->
        <div class="chart-container">
            <h3 class="text-xl font-semibold mb-4">今日回复间隔时间趋势</h3>
            <div class="bg-gray-50 p-4 rounded-lg" style="height: 80vh">
                <canvas ref="todayResponseTimeChartRef" class="w-full"></canvas>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import Chart from 'chart.js/auto';
import type { Message } from '@/common/type-interface';
import { CaretBottom, CaretTop, Warning } from '@element-plus/icons-vue'

// 日期范围配置
const dateRange: Record<string, number> = { "最近7天": 7, "最近30天": 30, "全部": -1 };
const dateRangeOptions = Object.keys(dateRange);
const lastPeriod = ref<number>(7);

// 统计数据响应式变量
const totalUserCharCounts = ref<number>(0);
const totalCharCounts_ = ref<number>(0);
const totalUserMessageCounts = ref<number>(0);
const totalMessageCounts = ref<number>(0);
const totalTodayUserCharCounts = ref<number>(0);
const totalTodayUserMessageCounts = ref<number>(0);
const totalTodayCharCounts = ref<number>(0);
const totalTodayMessageCounts = ref<number>(0);
const totalDays = ref<number>(0);

// 响应时间统计变量
const totalResponseTime_ = ref<number>(0);
const totalResponseTimeCounts = ref<number>(0);
const totalCharReadAndWriteCounts = ref<number>(0);
const todayTotalResponseTime_ = ref<number>(0);
const todayTotalResponseTimeCounts = ref<number>(0);
const todayTotalCharReadAndWriteCounts = ref<number>(0);

// 差异计算
const diffTodayUserCharCountsThanAverage = computed(() => {
    return (totalTodayUserCharCounts.value - (totalUserCharCounts.value / totalDays.value));
})
const diffTodayCharCountsThanAverage = computed(() => {
    return (totalTodayCharCounts.value - (totalCharCounts_.value / totalDays.value));
})
const diffTodayResponseTimeThanAverage = computed(() => {
    return todayTotalResponseTimeCounts.value <= 0 ? 0 :
        ((todayTotalResponseTime_.value / todayTotalResponseTimeCounts.value) - (totalResponseTime_.value / totalResponseTimeCounts.value))
        / (totalResponseTime_.value / totalResponseTimeCounts.value);
})
const diffTodayCharReadAndWriteCountsThanAverage = computed(() => {
    return todayTotalResponseTime_.value <= 0 ? 0 :
        ((todayTotalCharReadAndWriteCounts.value / todayTotalResponseTime_.value) - (totalCharReadAndWriteCounts.value / totalResponseTime_.value))
        / (totalCharReadAndWriteCounts.value / totalResponseTime_.value);
})

// 图表实例全局声明
declare global {
    interface Window {
        messageChartInstance?: Chart;
        responseTimeChartInstance?: Chart;
        todayResponseTimeChartInstance?: Chart; // 新增今日图表实例
    }
}

// Props定义
const props = defineProps({
    visible: {
        type: Boolean,
        required: true,
        default: false
    },
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

// 消息数据处理
const chatMessage = ref<Message[]>(props.messages);
watch(() => props.visible, async (newVal) => {
    if (newVal) {
        chatMessage.value = props.messages.filter(message => message.role !== 'system');
        await nextTick();
        initCharts();
    }
})

// 图表引用
const messageChartRef = ref<HTMLCanvasElement | null>(null);
const responseTimeChartRef = ref<HTMLCanvasElement | null>(null);
const todayResponseTimeChartRef = ref<HTMLCanvasElement | null>(null); // 新增今日图表引用

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

// 工具函数：日期格式化
const formatDataToLocalString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// 工具函数：分钟转时分格式
const formatMinutesToHHMM = (minutes: number) => {
    const isNegative = minutes < 0;
    if (isNegative) minutes = -minutes
    const hours = Math.floor(minutes / 60);
    const minutes_ = (minutes % 60).toFixed(0);
    return (isNegative ? '-' : '') + `${hours.toString().padStart(2, '0')} 小时 ${minutes_.toString().padStart(2, '0')} 分钟`;
}

// 每日平均响应时间
const responseTimePerDay = computed(() => {
    return totalResponseTime_.value / totalDays.value;
})

// 生成日期范围
const generateDateRange = (startDate: string, endDate: string): string[] => {
    const dates: string[] = [];
    const currentDate = new Date(startDate);
    const finalDate = new Date(endDate);
    while (currentDate <= finalDate) {
        dates.push(formatDataToLocalString(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }
    return dates;
};

// 获取完整日期范围
const getFullDateRange = (): string[] => {
    const existingDates = Object.keys(messagesByDate.value);
    const today = formatDataToLocalString(new Date());
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

// 字符统计工具
const countCharacters = (text: string) => {
    const englishWords = text.match(/[a-zA-Z]+/g)?.length || 0;
    const englishPunctuation = text.match(/[!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~]/g)?.length || 0;
    const chineseChars = text.match(/[\u4e00-\u9fa5]/g)?.length || 0;
    const chinesePunctuation = text.match(/[\u3000-\u303F\uFF00-\uFFEF]/g)?.length || 0;
    const japaneseKana = text.match(/[\u3040-\u309F\u30A0-\u30FF]/g)?.length || 0;
    const japaneseKanji = text.match(/[\u4E00-\u9FFF]/g)?.length || 0;
    const japanesePunctuation = text.match(/[\u3000-\u303F\u30FB-\u30FC\uFF01-\uFF5E]/g)?.length || 0;
    const japaneseTotal = japaneseKana + japaneseKanji + japanesePunctuation;
    return { englishWords, englishPunctuation, chineseChars, chinesePunctuation, japaneseTotal };
};

// 按语言获取字符数
const getLanguageChars = (text: string, language: string) => {
    const { englishWords, englishPunctuation, chineseChars, chinesePunctuation, japaneseTotal } = countCharacters(text);
    switch (language) {
        case 'English': return englishWords + englishPunctuation;
        case '中文': return chineseChars + chinesePunctuation;
        case '日本語': return japaneseTotal;
        default: return text.length;
    }
};

// 准备消息图表数据
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
        const userMsgs = messages.filter(m => m.role === 'user');
        totalUserMessageCounts.value += userMsgs.length;
        const userCount = userMsgs.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
        userCharCounts.push(userCount);

        const totalCount = messages.reduce((total, msg) => total + getLanguageChars(msg.raw_text, props.language), 0);
        totalMessageCounts.value += messages.length;
        totalCharCounts.push(totalCount);
    });

    totalTodayUserMessageCounts.value = messagesByDate.value[fullDates[fullDates.length - 1]]?.filter(m => m.role === 'user').length || 0;
    totalTodayMessageCounts.value = messagesByDate.value[fullDates[fullDates.length - 1]]?.length || 0;

    return { dates: fullDates, userCharCounts, totalCharCounts };
};

// 准备回复时间图表数据
const prepareResponseTimeChartData = () => {
    const fullDates = getFullDateRange();
    const rawResponseTimes: Record<string, number> = {};
    const rawWordsPerMinute: Record<string, number> = {};
    const readAndWriteTime: Record<string, number> = {};

    totalResponseTime_.value = 0;
    totalResponseTimeCounts.value = 0;
    totalCharReadAndWriteCounts.value = 0;
    todayTotalResponseTime_.value = 0;
    todayTotalResponseTimeCounts.value = 0;
    todayTotalCharReadAndWriteCounts.value = 0;
    const todayDate = fullDates[fullDates.length - 1];

    fullDates.forEach(date => {
        const messages = messagesByDate.value[date] || [];
        const userMessages = messages.filter(m => m.role === 'user');
        const assistantMessages = messages.filter(m => m.role === 'assistant');
        const reversedAssistantMsg = [...assistantMessages].reverse();

        let totalResponseTime = 0;
        let totalWords = 0;
        let responseCount = 0;

        userMessages.forEach(userMsg => {
            const prevAssistantMsg = reversedAssistantMsg.find(
                msg => new Date(msg.time) < new Date(userMsg.time)
            );

            if (prevAssistantMsg) {
                const timeDiff = (new Date(userMsg.time).getTime() - new Date(prevAssistantMsg.time).getTime()) / 1000 / 60;
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

        readAndWriteTime[date] = totalResponseTime;
        if (responseCount > 0) {
            rawResponseTimes[date] = totalResponseTime / responseCount;
            rawWordsPerMinute[date] = totalWords / totalResponseTime;
        }
    });

    const fillMissingValues = (rawData: Record<string, number>, dates: string[]): number[] => {
        return dates.map((date, index) => {
            if (rawData[date] !== undefined) return rawData[date];

            let prevValue: number | null = null;
            for (let i = index - 1; i >= 0; i--) {
                if (rawData[dates[i]] !== undefined) {
                    prevValue = rawData[dates[i]];
                    break;
                }
            }

            let nextValue: number | null = null;
            for (let i = index + 1; i < dates.length; i++) {
                if (rawData[dates[i]] !== undefined) {
                    nextValue = rawData[dates[i]];
                    break;
                }
            }

            if (prevValue !== null && nextValue !== null) return (prevValue + nextValue) / 2;
            else if (prevValue !== null) return prevValue;
            else if (nextValue !== null) return nextValue;
            else return 0;
        });
    };

    const avgResponseTimes = fillMissingValues(rawResponseTimes, fullDates);
    const avgWordsPerMinute = fillMissingValues(rawWordsPerMinute, fullDates);

    return { dates: fullDates, avgResponseTimes, avgWordsPerMinute, readAndWriteTime };
};

// 新增：准备今日回复间隔数据
const prepareTodayResponseTimeData = () => {
    const todayDate = formatDataToLocalString(new Date());
    const todayMessages = messagesByDate.value[todayDate] || [];
    const userMessages = todayMessages.filter(m => m.role === 'user');
    const assistantMessages = todayMessages.filter(m => m.role === 'assistant');
    const reversedAssistantMsg = [...assistantMessages].reverse();

    const replyTimes: string[] = []; // 横坐标：HH:MM格式
    const responseIntervals: number[] = []; // 回复间隔时间（分钟）
    const wordsPerMinuteList: number[] = []; // 读说速度（字/分钟）

    userMessages.forEach(userMsg => {
        // 提取HH:MM时间格式
        const fullTime = userMsg.time;
        const hhmm = fullTime.split(' ')[1].slice(0, 5);
        replyTimes.push(hhmm);

        // 计算间隔时间
        const prevAssistantMsg = reversedAssistantMsg.find(
            msg => new Date(msg.time) < new Date(userMsg.time)
        );

        if (prevAssistantMsg) {
            const timeDiff = (new Date(userMsg.time).getTime() - new Date(prevAssistantMsg.time).getTime()) / 1000 / 60;
            const validDiff = timeDiff > 0 && timeDiff <= 10 ? timeDiff : 0;
            responseIntervals.push(validDiff);

            // 计算读说速度
            const readWords = getLanguageChars(prevAssistantMsg.raw_text, props.language);
            const replyWords = getLanguageChars(userMsg.raw_text, props.language);
            const totalWords = readWords + replyWords;
            const wordsPerMinute = validDiff > 0 ? (totalWords / validDiff).toFixed(2) : 0;
            wordsPerMinuteList.push(Number(wordsPerMinute));
        } else {
            responseIntervals.push(0);
            wordsPerMinuteList.push(0);
        }
    });

    return { replyTimes, responseIntervals, wordsPerMinuteList };
};

// 创建消息图表
const createMessageChart = () => {
    if (!messageChartRef.value) return;

    const { dates, userCharCounts, totalCharCounts } = prepareMessageChartData();
    totalUserCharCounts.value = userCharCounts.reduce((total, count) => total + count, 0);
    totalCharCounts_.value = totalCharCounts.reduce((total, count) => total + count, 0);
    totalTodayUserCharCounts.value = userCharCounts[userCharCounts.length - 1];
    totalTodayCharCounts.value = totalCharCounts[totalCharCounts.length - 1];

    const { readAndWriteTime } = prepareResponseTimeChartData();
    const readAndWriteTimeValues = Object.values(readAndWriteTime)

    const ctx = messageChartRef.value.getContext('2d');
    if (!ctx) return;

    if (window.messageChartInstance) window.messageChartInstance.destroy();
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
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: '总字数',
                    data: totalCharCounts,
                    backgroundColor: '#f97316',
                    borderColor: '#ea580c',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: '读写时间(分钟)',
                    data: readAndWriteTimeValues,
                    backgroundColor: '#10b981',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    yAxisID: 'y1'
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
                            if (datasetIndex === 2) {
                                return [`读写时间: ${formatMinutesToHHMM(readAndWriteTimeValues[dateIndex])}`];
                            }
                            const messages = messagesByDate.value[date] || [];
                            const filteredMessages = datasetIndex === 0
                                ? messages.filter(m => m.role === 'user')
                                : messages;
                            return [`消息条数: ${filteredMessages.length}`];
                        }
                    }
                },
                legend: { position: 'top' },
                title: { display: true, text: `每日${props.language}字数统计` }
            },
            scales: {
                x: { title: { display: true, text: '日期' }, ticks: { maxRotation: 45, minRotation: 0 } },
                y: { title: { display: true, text: `${props.language}字数` }, beginAtZero: true },
                y1: { title: { display: true, text: '每日读说时间' }, beginAtZero: true, position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
};

// 创建回复时间图表
const createResponseTimeChart = () => {
    if (!responseTimeChartRef.value) return;

    const { dates, avgResponseTimes, avgWordsPerMinute, readAndWriteTime } = prepareResponseTimeChartData();

    const ctx = responseTimeChartRef.value.getContext('2d');
    if (!ctx) return;

    if (window.responseTimeChartInstance) window.responseTimeChartInstance.destroy();
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
                legend: { position: 'top' },
                title: { display: true, text: '平均回复间隔时间与读说速度趋势' },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        afterLabel: (context) => {
                            const dateIndex = context.dataIndex;
                            const date = dates[dateIndex];
                            return [`总读写时间: ${formatMinutesToHHMM(readAndWriteTime[date])}`];
                        }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: '日期' }, ticks: { maxRotation: 45, minRotation: 0 } },
                y: { title: { display: true, text: '平均回复间隔时间(分钟)' }, beginAtZero: true, position: 'left' },
                y1: { title: { display: true, text: '平均每分钟读说字数' }, beginAtZero: true, position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
};

// 新增：创建今日回复间隔图表
const createTodayResponseTimeChart = () => {
    if (!todayResponseTimeChartRef.value) return;

    const { replyTimes, responseIntervals, wordsPerMinuteList } = prepareTodayResponseTimeData();

    const ctx = todayResponseTimeChartRef.value.getContext('2d');
    if (!ctx) return;

    if (window.todayResponseTimeChartInstance) window.todayResponseTimeChartInstance.destroy();
    window.todayResponseTimeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: replyTimes,
            datasets: [
                {
                    label: '单次回复间隔时间(分钟)',
                    data: responseIntervals,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    tension: 0.3,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: '单次回复读说速度(字/分钟)',
                    data: wordsPerMinuteList,
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
                legend: { position: 'top' },
                title: { display: true, text: `今日${props.language}回复间隔时间趋势` },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        afterLabel: (context) => {
                            const index = context.dataIndex;
                            const interval = responseIntervals[index].toFixed(2);
                            const speed = wordsPerMinuteList[index].toFixed(2);
                            return [
                                `间隔时间：${interval} 分钟`,
                                `读说速度：${speed} 字/分钟`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: '用户回复时间（HH:MM）' }, ticks: { maxRotation: 45, minRotation: 0 } },
                y: { title: { display: true, text: '回复间隔时间(分钟)' }, beginAtZero: true, position: 'left' },
                y1: { title: { display: true, text: '读说速度(字/分钟)' }, beginAtZero: true, position: 'right', grid: { drawOnChartArea: false } }
            }
        }
    });
};

// 初始化图表
const initCharts = () => {
    createMessageChart();
    createResponseTimeChart();
    createTodayResponseTimeChart(); // 新增今日图表初始化
};

// 窗口大小调整处理
const handleResize = () => {
    initCharts();
};

// 生命周期
onMounted(() => {
    initCharts();
    window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (window.messageChartInstance) window.messageChartInstance.destroy();
    if (window.responseTimeChartInstance) window.responseTimeChartInstance.destroy();
    if (window.todayResponseTimeChartInstance) window.todayResponseTimeChartInstance.destroy(); // 新增今日图表销毁
});
</script>

<style scoped></style>