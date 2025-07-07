<!-- src/views/ChatLayout.vue -->
<template>
    <div class="app-container">
        <sidebar />
        <div class="main-content">
            <router-view />
        </div>
    </div>
</template>

<script lang="ts" setup>
import Sidebar from '@/components/Sidebar/Sidebar.vue'
</script>
