<!-- src/views/ChatLayout.vue -->
<template>
    <div class="app-container">
        <sidebar style="display: none;" />
        <div class="main-content">
            <router-view />
        </div>
    </div>
</template>

<script lang="ts" setup>
import Sidebar from '@/components/Sidebar/Sidebar.vue'
import { onMounted } from 'vue'
onMounted(() => {
    setTimeout(() => {
        document.documentElement.style.setProperty('--main-content-left-margin', '0px');
    }, 100)
})
</script>
