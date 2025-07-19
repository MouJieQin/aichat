<template>
    <div>
        <div>
            <div>
                <h1>系统设置</h1>
            </div>
            <div>
                <el-form v-if="localSystemConfig" :model="localSystemConfig" label-width="150px" class="config-form">
                    <div class="config-class">
                        <p style="text-align: left;">Azure</p>
                        <el-form-item label="azure key">
                            <el-input v-model="localSystemConfig.azure.key" />
                        </el-form-item>
                        <el-form-item label="azure region">
                            <el-input v-model="localSystemConfig.azure.region" />
                        </el-form-item>
                    </div>
                </el-form>
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue'
import type { SystemConfig } from '@/common/type-interface'
import { useSystemConfigStore } from '@/stores/sidebarStore'

const systemConfigStore = useSystemConfigStore()
const localSystemConfig = ref<SystemConfig>(JSON.parse(JSON.stringify(systemConfigStore.systemConfig)))
watch(() => systemConfigStore.systemConfig, (newVal) => {
    localSystemConfig.value = JSON.parse(JSON.stringify(newVal))
})

</script>