<template>
    <div class="setting-container">
        <div>
            <p class="system-config-title">系统设置</p>
        </div>
        <div>
            <el-form v-if="localSystemConfig" :model="localSystemConfig" label-width="150px" class="config-form">

                <div class="config-class">
                    <p class="config-class-title">Avatar</p>
                    <p class="config-class-desc">
                        自定义头像
                    </p>
                    <el-avatar v-if="localSystemConfig.appearance.user_avatar_url" :src="userAvatarUrl" fit="cover"
                        size="large" @click="showUserPreview = true" />
                    <el-image-viewer v-if="showUserPreview" :url-list="[userAvatarUrl]" show-progress :initial-index="0"
                        @close="showUserPreview = false" />

                    <div>
                        <el-upload drag action="http://localhost:4999/api/upload/user_avatar" :show-file-list="false">
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
                </div>

                <div class="config-class">
                    <p class="config-class-title">Appearance</p>
                    <el-form-item label="主题">
                        <el-radio-group v-model="appTheme" size="large" fill="#6cf">
                            <el-radio-button value="light">
                                <div class="config-radio-button">
                                    <el-icon class="config-radio-icon">
                                        <Sunny />
                                    </el-icon>
                                    <span>浅色模式</span>
                                </div>
                            </el-radio-button>
                            <el-radio-button :icon="Moon" label="深色模式" value="dark">
                                <div class="config-radio-button">
                                    <el-icon class="config-radio-icon">
                                        <Moon />
                                    </el-icon>
                                    <span>深色模式</span>
                                </div>
                            </el-radio-button>
                            <el-radio-button :icon="SwitchFilled" label="跟随系统" value="auto">
                                <div class="config-radio-button">
                                    <el-icon class="config-radio-icon">
                                        <SwitchFilled />
                                    </el-icon>
                                    <span>跟随系统</span>
                                </div>
                            </el-radio-button>
                        </el-radio-group>
                    </el-form-item>
                </div>

                <div class="config-class">
                    <p class="config-class-title">Azure</p>
                    <p class="config-class-desc">
                        该配置用于语音合成和语音识别，
                        请参考 <a href="https://portal.azure.com/#create/Microsoft.CognitiveServicesAIFoundry"
                            target="_blank">Azure</a>
                        了解如何获取 Azure 语音服务的 API Key 和 Region。
                    </p>
                    <el-form-item label="azure key">
                        <el-input v-model="localSystemConfig.azure.key" />
                    </el-form-item>
                    <el-form-item label="azure region">
                        <el-input v-model="localSystemConfig.azure.region" />
                    </el-form-item>
                </div>

                <div class="config-class">
                    <p class="config-class-title">Session</p>
                    <p class="config-class-desc">
                        创建一个新会话时的默认配置
                    </p>
                    <el-form-item label="标题">
                        <el-input v-model="localSystemConfig.ai_assistant.default.chat_title" />
                    </el-form-item>
                    <el-form-item label="系统提示">
                        <el-input v-model="localSystemConfig.ai_assistant.default.system_prompt" type="textarea"
                            autosize placeholder="编辑设定..." />
                    </el-form-item>

                    <el-form-item label="API">
                        <el-select v-model="localSystemConfig.ai_assistant.default.ai_config_name" placeholder="请选择API">
                            <el-option v-for="item in apis" :key="item.id" :label="item.name" :value="item.name" />
                        </el-select>
                    </el-form-item>
                </div>

                <div class="config-class">
                    <p class="config-class-title">API</p>
                    <el-tabs v-model="editableTabsValue" type="card" editable @edit="handleTabsEdit">
                        <el-tab-pane v-for="(item, index) in apis" :key="item.id" :label="item.name" :name="item.id">
                            <el-form :model="item" label-width="150px" class="config-form">
                                <el-form-item label="name">
                                    <el-input v-model="item.name" />
                                </el-form-item>
                                <!-- 语言选择 -->
                                <el-form-item label="语言">
                                    <el-select v-model="item.language" placeholder="选择语言"
                                        @change="item.tts_voice = ttsVoicesStore.ttsVoices[item.language][0].ShortName">
                                        <el-option v-for="lang in ttsVoicesStore.languages" :key="lang" :label="lang"
                                            :value="lang" />
                                    </el-select>
                                </el-form-item>

                                <!-- TTS 语音 -->
                                <el-form-item label="语音合成">
                                    <el-select v-model="item.tts_voice" filterable placeholder="选择语音">
                                        <el-option v-for="voice in ttsVoicesStore.ttsVoices[item.language]"
                                            :key="voice.ShortName"
                                            :label="`${voice.LocalName} (${voice.Gender}) —— ${voice.LocaleName}`"
                                            :value="voice.ShortName" />
                                    </el-select>
                                </el-form-item>

                                <!-- 语速 -->
                                <el-form-item label="语速">
                                    <el-input-number v-model="item.speech_rate" :min="0.5" :max="2.0" :step="0.1" />
                                </el-form-item>

                                <!-- 自动播放 -->
                                <el-form-item label="自动播放">
                                    <el-switch v-model="item.auto_play" />
                                </el-form-item>

                                <el-form-item label="自动生成标题">
                                    <el-switch v-model="item.auto_gen_title" :active-value="true"
                                        :inactive-value="false" />
                                </el-form-item>

                                <!-- 其他配置项... -->
                                <el-form-item label="API 地址">
                                    <el-input v-model="item.base_url" />
                                </el-form-item>
                                <el-form-item label="API 密钥">
                                    <el-input v-model="item.api_key" />
                                </el-form-item>

                                <el-form-item label="模型">
                                    <el-select v-model="item.model" placeholder="选择模型"
                                        @change="item.tts_voice = ttsVoicesStore.ttsVoices[item.language][0].ShortName">
                                        <el-option v-for="model in item.modelsOptional" :key="model" :label="model"
                                            :value="model" />
                                    </el-select>
                                </el-form-item>

                                <el-form-item label="Temperature">
                                    <el-input-number v-model="item.temperature" :max="2.0" :min="0.0" :step="0.1" />
                                </el-form-item>
                                <el-form-item label="Max Tokens">
                                    <el-input-number v-model="item.max_tokens" :min="1" :step="100" />
                                </el-form-item>
                                <el-form-item label="Context Max Tokens">
                                    <el-input-number v-model="item.context_max_tokens" :min="1" :step="100" />
                                </el-form-item>
                                <el-form-item label="Max Messages">
                                    <el-input-number v-model="item.max_messages" :min="1" :step="1" />
                                </el-form-item>

                                <el-form-item label="可选模型">
                                    <el-select v-model="item.modelsOptional" multiple filterable allow-create
                                        default-first-option :reserve-keyword="false"
                                        placeholder="Choose tags for your article">
                                        <el-option v-for="model in item.modelsOptional" :key="model" :label="model"
                                            :value="model" />
                                    </el-select>
                                </el-form-item>

                            </el-form>
                        </el-tab-pane>
                    </el-tabs>
                </div>
            </el-form>
        </div>

        <div class="setting-footer-button-group">
            <el-affix position="bottom" :offset="20" style="text-align: right;">
                <el-button type="" @click="handleCancel">取消</el-button>
            </el-affix>

            <el-affix position="bottom" :offset="20" style="text-align: right;">
                <el-button type="primary" @click="handleConfirm">保存</el-button>
            </el-affix>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted, computed } from 'vue'
import type { SystemConfig } from '@/common/type-interface'
import { useSystemConfigStore, useTtsVoiceStore } from '@/stores/sidebarStore'
import type { TabPaneName } from 'element-plus'
import { Sunny, Moon, SwitchFilled, UploadFilled } from '@element-plus/icons-vue'
import { getUserAvatarUrl } from '@/common/utils'
import short from 'short-uuid';


const systemConfigStore = useSystemConfigStore()
// const appTheme = ref(systemConfigStore.systemConfig?.appearance.theme)
const ttsVoicesStore = useTtsVoiceStore()
const localSystemConfig = ref<SystemConfig>(JSON.parse(JSON.stringify(systemConfigStore.systemConfig)))
const editableTabsValue = ref('')
const showUserPreview = ref(false)

const initApis = () => {
    editableTabsValue.value = apis.value?.[0]?.id
}

onMounted(() => {
    initApis()
})


const userAvatarUrl = computed(() => {
    return getUserAvatarUrl(localSystemConfig.value?.appearance.user_avatar_url)
})

const apis = computed({
    get: () => localSystemConfig.value?.ai_assistant.apis,
    set: (val) => localSystemConfig.value.ai_assistant.apis = val
})

const appTheme = computed({
    get: () => localSystemConfig.value?.appearance.theme,
    set: (val) => {
        localSystemConfig.value.appearance.theme = val
        systemConfigStore.setAppearanceTheme(val)
    }
})

watch(() => systemConfigStore.systemConfig, (newVal) => {
    localSystemConfig.value = JSON.parse(JSON.stringify(newVal))
    initApis()
})

const handleCancel = () => {
    localSystemConfig.value = JSON.parse(JSON.stringify(systemConfigStore.systemConfig))
    initApis()
}

const handleConfirm = () => {
    systemConfigStore.updateSystemConfig?.(localSystemConfig.value)
}

const handleTabsEdit = (
    targetName: TabPaneName | undefined,
    action: 'remove' | 'add'
) => {
    if (action === 'add') {
        const id = short.generate()
        apis.value.push({
            id: id,
            name: id,
            base_url: '',
            api_key: '',
            model: '',
            temperature: 0.7,
            max_tokens: 800,
            context_max_tokens: 3000,
            max_messages: 20,
            language: '中文',
            tts_voice: 'zh-CN-XiaochenNeural',
            auto_play: false,
            auto_gen_title: true,
            speech_rate: 1,
            modelsOptional: [],
        })
        editableTabsValue.value = id
    } else if (action === 'remove') {
        const tabs = apis.value
        let activeName = editableTabsValue.value
        if (activeName === targetName) {
            tabs.forEach((tab, index) => {
                if (tab.name === targetName) {
                    const nextTab = tabs[index + 1] || tabs[index - 1]
                    if (nextTab) {
                        activeName = nextTab.name
                    }
                }
            })
        }

        editableTabsValue.value = activeName
        apis.value = tabs.filter((tab) => tab.id !== targetName)
    }
}


</script>
