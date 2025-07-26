<template>
    <el-dialog v-model="visible_" fullscreen>
        <ChatStatistic class="statistic-dialog" :visible="visible_" :messages="messages" :language="language" />
        <template #footer>
            <div class="dialog-footer">
                <el-button @click="visible_ = false">Cancel</el-button>
                <el-button type="primary" @click="visible_ = false">
                    Confirm
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import type { Message } from '@/common/type-interface';
import ChatStatistic from '@/components/Chat/ChatStatistic.vue';

const props = defineProps({
    visible: {
        type: Boolean,
        required: true,
        default: false
    },
    messages: {
        type: Array as () => Message[],
        required: true,
        default: () => []
    },
    language: {
        type: String,
        required: true,
        default: 'English'
    }
})

// 使用计算属性实现双向绑定
const visible_ = computed({
    get() {
        return props.visible;
    },
    set(value) {
        emit('update:visible', value);
    }
});

const emit = defineEmits(['update:visible']);
</script>