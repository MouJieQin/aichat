<template>
    <el-drawer v-model="visible" title="AI 配置" direction="rtl" size="40%">
        <el-avatar v-if="localConfig.ai_avatar_url" :src="aiAvatarUrl" fit="cover" size="large"
            @click="showPreview = true" />
        <el-image-viewer v-if="showPreview" :url-list="[aiAvatarUrl]" show-progress :initial-index="0"
            @close="showPreview = false" />

        <el-form :model="localConfig" label-width="150px" class="config-form">

            <div class="config-class">
                <p class="config-class-title">Chat</p>
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

                <el-form-item v-if="systemPrompt.role === 'system' && systemPromptAutoResize" label="系统设定">
                    <el-input v-model="localSystemPrompt" type="textarea" autosize placeholder="编辑设定..." />
                </el-form-item>


                <!-- 语言选择 -->
                <el-form-item label="语言">
                    <el-select v-model="localConfig.language" placeholder="选择语言"
                        @change="localConfig.tts_voice = ttsVoicesStore.ttsVoices[localConfig.language][0].ShortName">
                        <el-option v-for="lang in ttsVoicesStore.languages" :key="lang" :label="lang" :value="lang" />
                    </el-select>
                </el-form-item>

                <!-- TTS 语音 -->
                <el-form-item label="语音合成">
                    <el-select v-model="localConfig.tts_voice" filterable placeholder="选择语音">
                        <el-option v-for="voice in ttsVoicesStore.ttsVoices[localConfig.language]"
                            :key="voice.ShortName"
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
            </div>

            <div class="config-class">
                <p class="config-class-title">API</p>

                <el-form-item label="API">
                    <el-select v-model="selectedApiName" placeholder="选择API" @change="handleApiChange">
                        <el-option v-for="api in systemConfigStore.systemConfig?.ai_assistant.apis" :key="api.id"
                            :label="api.name" :value="api.name" />
                    </el-select>
                </el-form-item>


                <!-- 其他配置项... -->
                <el-form-item label="API 地址">
                    <el-input v-model="localConfig.base_url" />
                </el-form-item>
                <el-form-item label="API 密钥">
                    <el-input v-model="localConfig.api_key" />
                </el-form-item>

                <el-form-item label="模型">
                    <el-select v-model="localConfig.model" placeholder="选择模型" :options="modelsOptional">
                        <el-option v-for="model in modelsOptional" :key="model" :label="model" :value="model" />
                    </el-select>
                </el-form-item>

                <el-form-item label="Temperature">
                    <el-input-number v-model="localConfig.temperature" :max="2.0" :min="0.0" :step="0.1" />
                </el-form-item>

                <el-form-item label="Max Tokens">
                    <el-input-number v-model="localConfig.max_tokens" :min="1" :step="100" />
                </el-form-item>
                <el-form-item label="Context Max Tokens">
                    <el-input-number v-model="localConfig.context_max_tokens" :min="1" :step="100" />
                </el-form-item>
                <el-form-item label="Max Messages">
                    <el-input-number v-model="localConfig.max_messages" :min="1" :step="1" />
                </el-form-item>
            </div>

        </el-form>


        <template #footer>
            <el-button @click="visible = false">取消</el-button>
            <el-button type="primary" @click="handleConfirm">确认</el-button>
        </template>
    </el-drawer>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { AIConfig, Message } from '@/common/type-interface'
import { UploadFilled } from '@element-plus/icons-vue'
import { getAiAvatarUrl } from '@/common/utils'
import { useSystemConfigStore, useTtsVoiceStore } from '@/stores/sidebarStore'

const props = defineProps({
    modelValue: {
        type: Boolean,
        default: false
    },
    systemPrompt: {
        type: Object as () => Message,
        required: true,
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

const systemConfigStore = useSystemConfigStore()
const ttsVoicesStore = useTtsVoiceStore()
// 状态
const visible = ref(props.modelValue)
const localConfig = ref<AIConfig>(JSON.parse(JSON.stringify(props.config)))
const localSystemPrompt = ref<string>(props.systemPrompt.raw_text)
const showPreview = ref(false)
// workaround triggering autoresize for systemp prompt input
const systemPromptAutoResize = ref(false)
const selectedApiName = ref<string>('')


const aiAvatarUrl = computed(() => {
    return getAiAvatarUrl(props.config.ai_avatar_url)
})

const modelsOptional = computed((): string[] => {
    if (!systemConfigStore.systemConfig) {
        return []
    }
    let models: string[] = []
    for (const api of systemConfigStore.systemConfig?.ai_assistant.apis) {
        if (api.base_url === localConfig.value.base_url) {
            for (const model of api.modelsOptional) {
                if (!models.includes(model)) {
                    models.push(model)
                }
            }
        }
    }
    return models
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

watch(
    () => props.systemPrompt,
    (val) => {
        localSystemPrompt.value = val.raw_text
    }
)

const handleApiChange = () => {
    const api = systemConfigStore.systemConfig?.ai_assistant.apis.find(api => api.name === selectedApiName.value)
    if (api) {
        localConfig.value.base_url = api.base_url
        localConfig.value.api_key = api.api_key
        if (!modelsOptional.value.includes(localConfig.value.model)) {
            if (modelsOptional.value.length > 0) {
                localConfig.value.model = modelsOptional.value[0]
            }
            else {
                localConfig.value.model = ""
            }
        }
    }
}

// 处理确认
const handleConfirm = () => {
    emits('update-config', { ...localConfig.value }, props.systemPrompt.message_id, localSystemPrompt.value, props.systemPrompt.raw_text)
    visible.value = false
}

// 同步可见性
watch(visible, (val) => {
    systemPromptAutoResize.value = val
    if (val) {
        localSystemPrompt.value = props.systemPrompt.raw_text
        localConfig.value = JSON.parse(JSON.stringify(props.config))
    }
    emits('update:modelValue', val)
})
</script>
