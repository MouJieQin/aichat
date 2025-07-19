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
