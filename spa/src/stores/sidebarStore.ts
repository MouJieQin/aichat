import { defineStore } from 'pinia'
import type { SystemConfig } from '@/common/type-interface'

export const useSystemConfigStore = defineStore('systemConfig', {
    state: () => ({
        systemConfig: null as SystemConfig | null,
        updateSystemConfig: null as unknown as (systemConfig: SystemConfig) => void | null
    }),
    actions: {
        setSystemConfig(systemConfig: SystemConfig) {
            this.systemConfig = systemConfig
        },
        setUpdateSystemConfig(updateSystemConfig: (systemConfig: SystemConfig) => void) {
            this.updateSystemConfig = updateSystemConfig
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

