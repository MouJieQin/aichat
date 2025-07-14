<template>
    <div class="suggestions-container" v-if="suggestions.length">
        <div class="suggestion-item" v-for="(item, index) in suggestions" :key="index">
            <el-button type="info" plain @click="$emit('send', item)" class="suggestion-btn">
                {{ item }}
                <el-icon style="margin-left: 8px;">
                    <Right />
                </el-icon>
            </el-button>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { Right } from '@element-plus/icons-vue'

const props = defineProps({
    suggestions: {
        type: Array as () => string[],
        default: () => []
    }
})

const emits = defineEmits(['send'])
</script>
