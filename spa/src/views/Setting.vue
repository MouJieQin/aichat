<template>
    <div class="setting-container">
        <div>
            <p class="system-config-title">系统设置</p>
        </div>
        <div>
            <el-form v-if="localSystemConfig" :model="localSystemConfig" label-width="150px" class="config-form">

                <div class="config-class">
                    <p class="config-class-title">Azure</p>
                    <el-form-item label="azure key">
                        <el-input v-model="localSystemConfig.azure.key" />
                    </el-form-item>
                    <el-form-item label="azure region">
                        <el-input v-model="localSystemConfig.azure.region" />
                    </el-form-item>
                </div>

                <div class="config-class">
                    <p class="config-class-title">Session</p>
                    <el-form-item label="标题">
                        <el-input v-model="localSystemConfig.ai_assistant.default.chat_title" />
                    </el-form-item>
                    <el-form-item label="系统提示">
                        <el-input v-model="localSystemConfig.ai_assistant.default.system_prompt" type="textarea"
                            autosize placeholder="编辑设定..." />
                    </el-form-item>
                    <el-form-item label="模型">
                        <el-input v-model="localSystemConfig.ai_assistant.default.ai_config_name" />
                    </el-form-item>
                </div>

                <div class="config-class">
                    <p class="config-class-title">API</p>
                    <el-tabs v-model="editableTabsValue" type="card" editable @edit="handleTabsEdit">
                        <el-tab-pane v-for="(item, index) in apis" :key="item.name" :label="item.name"
                            :name="item.name">
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

                                <!-- <div class="config-class">
                                    <p>可选模型</p>
                                    <el-tabs v-model="editableModelTabsValue" type="card" closable stretch
                                        tab-position="bottom"
                                        @tab-remove="(targetName: TabPaneName) => { removeModelTab(index, targetName) }"
                                        @tab-click="() => { }">
                                        <el-tab-pane v-for="model in item.modelsOptional" :key="model" :label="model"
                                            :name="model">
                                        </el-tab-pane>
                                    </el-tabs>
                                </div>
                                <el-form-item label="增加可选模型">
                                    <el-input v-model="newModelTabName" />
                                    <div style="margin-bottom: 20px">
                                        <el-button :icon="Plus" size="small" @click="addModelTab(index)">
                                        </el-button>
                                    </div>
                                </el-form-item> -->

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
        <el-affix position="bottom" :offset="20" style="text-align: right;">
            <el-button type="primary" @click="updateSystemConfig">保存</el-button>
        </el-affix>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue'
import type { AiApiConfig, SystemConfig } from '@/common/type-interface'
import { useSystemConfigStore, useTtsVoiceStore } from '@/stores/sidebarStore'
import type { TabPaneName } from 'element-plus'

const systemConfigStore = useSystemConfigStore()
const ttsVoicesStore = useTtsVoiceStore()
const localSystemConfig = ref<SystemConfig>(JSON.parse(JSON.stringify(systemConfigStore.systemConfig)))
const newModelTabName = ref('')
const editableTabsValue = ref('')
const editableModelTabsValue = ref('')
const apis = ref<AiApiConfig[]>()


const initApis = () => {
    if (localSystemConfig.value) {
        apis.value = localSystemConfig.value.ai_assistant.apis
        editableTabsValue.value = apis.value?.[0]?.name
        editableModelTabsValue.value = apis.value?.[0]?.modelsOptional?.[0]
    }
}

onMounted(() => {
    initApis()
})

watch(() => systemConfigStore.systemConfig, (newVal) => {
    localSystemConfig.value = JSON.parse(JSON.stringify(newVal))
    initApis()
})

const updateSystemConfig = () => {
    systemConfigStore.updateSystemConfig?.(localSystemConfig.value)
}

const handleTabsEdit = (
    targetName: TabPaneName | undefined,
    action: 'remove' | 'add'
) => {
    if (!apis.value) {
        return
    }
    if (action === 'add') {
        const newTabName = `api_${apis.value.length + 1}`
        apis.value.push({
            name: newTabName,
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
        editableTabsValue.value = newTabName
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
        apis.value = tabs.filter((tab) => tab.name !== targetName)
    }
}



const addModelTab = (index: number) => {
    if (!apis.value) return
    if (apis.value[index].modelsOptional.includes(newModelTabName.value)) {
        console.log('模型已存在')
        return
    }
    apis.value[index].modelsOptional.push(newModelTabName.value)
    editableModelTabsValue.value = newModelTabName.value
    newModelTabName.value = ''
}

const removeModelTab = (index: number, targetName: TabPaneName) => {
    if (!apis.value) return
    const tabs = apis.value[index].modelsOptional
    let activeName = editableModelTabsValue.value
    if (activeName === targetName) {
        tabs.forEach((model, index) => {
            if (model === targetName) {
                const nextTab = tabs[index + 1] || tabs[index - 1]
                if (nextTab) {
                    activeName = nextTab
                }
            }
        })
    }

    editableModelTabsValue.value = activeName
    apis.value[index].modelsOptional = tabs.filter((tab) => tab !== targetName)
}

</script>
