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
import { defineProps, defineEmits } from 'vue'
import { Right } from '@element-plus/icons-vue'

const props = defineProps({
    suggestions: {
        type: Array as () => string[],
        default: () => []
    }
})

const emits = defineEmits(['send'])
</script>

<style scoped>
.suggestions-container {
    max-width: clamp(300px, 80vw, 800px);
    margin: 0 auto 20px;
}

.suggestion-item {
    margin-bottom: 8px;
}

.suggestion-btn {
    width: 100%;
    justify-content: space-between;
    border-radius: 8px;
    text-align: left;
}
</style>