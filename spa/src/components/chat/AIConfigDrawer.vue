<template>
    <el-drawer v-model="visible" title="AI 配置" direction="rtl" size="40%">
        <el-avatar v-if="localConfig.ai_avatar_url" :src="aiAvatarUrl" fit="cover" size="large"
            @click="showPreview = true" />
        <el-image-viewer v-if="showPreview" :url-list="[aiAvatarUrl]" show-progress :initial-index="0"
            @close="showPreview = false" />

        <el-form :model="localConfig" label-width="150px" class="config-form">
            <el-form-item label="头像">
                <div>
                    <el-upload class="upload-demo" drag action="http://localhost:4999/api/upload/avatar"
                        :show-file-list="false" :data="{ 'session_id': chatId }">
                        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                        <div class="el-upload__text">
                            Drop file here or <em>click to upload</em>
                        </div>
                        <template #tip>
                            <div class="el-upload__tip">
                                jpg/png files with a size less than 10MB
                            </div>
                        </template>
                    </el-upload>
                </div>
            </el-form-item>

            <!-- 语言选择 -->
            <el-form-item label="语言">
                <el-select v-model="localConfig.language" placeholder="选择语言"
                    @change="localConfig.tts_voice = ttsVoices[localConfig.language][0].ShortName">
                    <el-option v-for="lang in languages" :key="lang" :label="lang" :value="lang" />
                </el-select>
            </el-form-item>

            <!-- TTS 语音 -->
            <el-form-item label="语音合成">
                <el-select v-model="localConfig.tts_voice" filterable placeholder="选择语音">
                    <el-option v-for="voice in filteredVoices" :key="voice.ShortName"
                        :label="`${voice.LocalName} (${voice.Gender}) —— ${voice.LocaleName}`"
                        :value="voice.ShortName" />
                </el-select>
            </el-form-item>

            <!-- 语速 -->
            <el-form-item label="语速">
                <el-input-number v-model="localConfig.speech_rate" :min="0.5" :max="2.0" :step="0.1" />
            </el-form-item>

            <!-- 自动播放 -->
            <el-form-item label="自动播放">
                <el-switch v-model="localConfig.auto_play" />
            </el-form-item>

            <el-form-item label="自动生成标题">
                <el-switch v-model="localConfig.auto_gen_title" :active-value="true" :inactive-value="false" />
            </el-form-item>

            <!-- 其他配置项... -->
            <el-form-item label="API 地址">
                <el-input v-model="localConfig.base_url" />
            </el-form-item>
            <el-form-item label="API 密钥">
                <el-input v-model="localConfig.api_key" />
            </el-form-item>

            <el-form-item label="模型">
                <el-input v-model="localConfig.model" />
            </el-form-item>

            <el-form-item label="Temperature">
                <el-input-number v-model="localConfig.temperature" :max="2.0" :min="0.0" :step="0.1" />
            </el-form-item>

            <el-form-item label="Max Tokens">
                <el-input-number v-model="localConfig.max_tokens" :max="4096" :min="1" :step="100" />
            </el-form-item>
            <el-form-item label="Context Max Tokens">
                <el-input-number v-model="localConfig.context_max_tokens" :max="4096" :min="1" :step="100" />
            </el-form-item>
            <el-form-item label="Max Messages">
                <el-input-number v-model="localConfig.max_messages" :max="100" :min="1" :step="1" />
            </el-form-item>
        </el-form>


        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleConfirm">确认</el-button>
        </template>
    </el-drawer>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { loadJsonFile } from '@/common/json-loader'
import { AIConfig } from '@/common/type-interface'
import { UploadFilled } from '@element-plus/icons-vue'
import { getAiAvatarUrl } from '@/common/utils'


const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false
    },
    config: {
        type: Object as () => AIConfig,
        required: true
    },
    chatId: {
        type: Number,
        required: true
    }
})

const emits = defineEmits(['update:modelValue', 'update-config'])

// 状态
const visible = ref(props.modelValue)
const localConfig = ref<AIConfig>(JSON.parse(JSON.stringify(props.config)))
const ttsVoices = ref<Record<string, any[]>>({})
const languages = ref<string[]>([])
const showPreview = ref(false)


const aiAvatarUrl = computed(() => {
    return getAiAvatarUrl(props.config.ai_avatar_url)
})

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
        localConfig.value = JSON.parse(JSON.stringify(val))
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
    if (val) {
        localConfig.value = JSON.parse(JSON.stringify(props.config))
    }
    emits('update:modelValue', val)
})
</script>
