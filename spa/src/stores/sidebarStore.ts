import { defineStore } from 'pinia'
import type { SystemConfig } from '@/common/type-interface'

export const useSystemConfigStore = defineStore('systemConfig', {
    state: () => ({
        systemConfig: null as SystemConfig | null,
        updateAppearanceTheme: null as unknown as (theme: string) => void | null,
        updateSystemConfig: null as unknown as (systemConfig: SystemConfig) => void | null
    }),
    actions: {
        setAppearanceTheme(theme: string) {
            if (this.systemConfig && this.systemConfig.appearance.theme !== theme) {
                console.log('this.systemConfig.appearance.theme:', this.systemConfig.appearance.theme)
                console.log('theme:', theme)
                this.systemConfig.appearance.theme = theme
                this.updateSystemConfig(this.systemConfig)
            }
        },
        setSystemConfig(systemConfig: SystemConfig) {
            this.systemConfig = systemConfig
        },
        setUpdateAppearanceTheme(updateAppearanceTheme: (theme: string) => void) {
            this.updateAppearanceTheme = updateAppearanceTheme
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

