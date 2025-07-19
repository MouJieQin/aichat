import { defineStore } from 'pinia'
import type { SystemConfig } from '@/common/type-interface'

export const useSystemConfigStore = defineStore('systemConfig', {
    state: () => ({
        systemConfig: null as SystemConfig | null
    }),
    actions: {
        setSystemConfig(systemConfig: SystemConfig) {
            this.systemConfig = systemConfig
        }
    }
})

export const useTtsVoiceStore = defineStore('ttsVoices', {
    state: () => ({
        ttsVoices: {} as Record<string, any[]>,
        languages: [] as string[]
    }),
    actions: {
        setTtsVoices(ttsVoices: Record<string, any[]>) {
            this.ttsVoices = ttsVoices
            this.languages = Object.keys(ttsVoices)
        }
    }
})

