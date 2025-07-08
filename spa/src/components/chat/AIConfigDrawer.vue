<template>
    <el-drawer v-model="visible" title="AI 配置" direction="rtl" size="60%">
        <el-form :model="config" label-width="150px" class="config-form">
            <!-- 语言选择 -->
            <el-form-item label="语言">
                <el-select v-model="config.language" placeholder="选择语言">
                    <el-option v-for="lang in languages" :key="lang" :label="lang" :value="lang" />
                </el-select>
            </el-form-item>

            <!-- TTS 语音 -->
            <el-form-item label="语音合成">
                <el-select v-model="config.tts_voice" filterable placeholder="选择语音">
                    <el-option v-for="voice in filteredVoices" :key="voice.ShortName"
                        :label="`${voice.LocalName} (${voice.Gender})`" :value="voice.ShortName" />
                </el-select>
            </el-form-item>

            <!-- 语速 -->
            <el-form-item label="语速">
                <el-input-number v-model="config.speech_rate" :min="0.5" :max="2.0" :step="0.1" />
            </el-form-item>

            <!-- 自动播放 -->
            <el-form-item label="自动播放">
                <el-switch v-model="config.auto_play" />
            </el-form-item>

            <!-- 其他配置项... -->
            <el-form-item label="API 地址">
                <el-input v-model="config.base_url" />
            </el-form-item>

            <el-form-item label="模型">
                <el-input v-model="config.model" />
            </el-form-item>
        </el-form>

        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleConfirm">确认</el-button>
        </template>
    </el-drawer>
</template>

<script lang="ts" setup>
import { defineProps, defineEmits, ref, computed, watch } from 'vue'
import { loadJsonFile } from '@/common/json-loader'

// 定义配置类型
interface AIConfig {
    base_url: string;
    api_key: string;
    model: string;
    temperature: number;
    max_tokens: number;
    context_max_tokens: number;
    max_messages: number;
    language: string;
    tts_voice: string;
    auto_play: boolean;
    auto_gen_title: boolean;
    speech_rate: number;
}

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false
    },
    config: {
        type: Object as () => AIConfig,
        required: true
    }
})

const emits = defineEmits(['update:modelValue', 'update-config'])

// 状态
const visible = ref(props.modelValue)
const localConfig = ref<AIConfig>({ ...props.config })
const ttsVoices = ref<Record<string, any[]>>({})
const languages = ref<string[]>([])

// 加载语音数据
const loadVoiceData = async () => {
    ttsVoices.value = await loadJsonFile('/tts_voices.json')
    languages.value = Object.keys(ttsVoices.value)
}

// 初始化
loadVoiceData()

// 过滤当前语言的语音
const filteredVoices = computed(() => {
    return ttsVoices.value[localConfig.value.language] || []
})

// 监听外部可见性变化
watch(
    () => props.modelValue,
    (val) => {
        visible.value = val
    }
)

// 监听配置变化
watch(
    () => props.config,
    (val) => {
        localConfig.value = { ...val }
    },
    { deep: true }
)

// 处理确认
const handleConfirm = () => {
    emits('update-config', { ...localConfig.value })
    visible.value = false
}

// 同步可见性
watch(visible, (val) => {
    emits('update:modelValue', val)
})
</script>

<style scoped>
.config-form {
    margin-top: 20px;
}

.el-form-item {
    margin-bottom: 16px;
}
</style>