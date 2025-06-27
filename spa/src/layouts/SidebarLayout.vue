<template>
    <div class="app-container">
        <!-- 侧边栏区域 -->
        <div class="sidebar">
            <el-radio-group v-model="isCollapse" style="margin-bottom: 20px">
                <el-radio-button :value="false">expand</el-radio-button>
                <el-radio-button :value="true">collapse</el-radio-button>
            </el-radio-group>
            <el-menu :default-active="activeMenu" class="el-menu-vertical-demo" :collapse="isCollapse"
                @open="handleOpen" @close="handleClose">
                <!-- 其他一级菜单 -->
                <el-sub-menu index="navigator">
                    <template #title>
                        <el-icon>
                            <location />
                        </el-icon>
                        <span>导航</span>
                    </template>
                    <el-menu-item v-for="item in navigatorItems" :key="item.path" :index="item.path"
                        @click="navigateTo(item.path)">
                        {{ item.title }}
                    </el-menu-item>
                </el-sub-menu>

                <!-- 历史对话菜单 -->
                <el-sub-menu index="history">
                    <template #title>
                        <el-icon><icon-menu /></el-icon>
                        <span>历史对话</span>
                    </template>
                    <el-menu-item v-for="item in historyItems" :key="item.path" :index="item.path"
                        @click="navigateTo(item.path)">
                        {{ item.title }}
                    </el-menu-item>
                </el-sub-menu>
            </el-menu>
        </div>

        <!-- 主内容区域 -->
        <div class="main-content">
            <router-view />
        </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, Menu as IconMenu } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 侧边栏折叠状态
const isCollapse = ref(false)

// 当前活动菜单项
const activeMenu = computed(() => {
    return route.path
})

// 菜单项数据
const navigatorItems = ref([
    { path: '/', title: '首页' },
    { path: '/page1', title: '内容页面1' },
])

const historyItems = ref([
    { path: '/history/1', title: '历史对话1' },
    { path: '/history/2', title: '历史对话2' },
    { path: '/history/3', title: '历史对话3' },
    { path: '/history/4', title: '历史对话4' },
    { path: '/history/5', title: '历史对话5' },
])

// 导航方法
const navigateTo = (path: string) => {
    router.push(path)
}

// 菜单事件处理
const handleOpen = (key: string, keyPath: string[]) => {
    console.log('Menu opened:', key, keyPath)
}

const handleClose = (key: string, keyPath: string[]) => {
    console.log('Menu closed:', key, keyPath)
}
</script>

<style scoped>
.app-container {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

.sidebar {
    width: 200px;
    border-right: 1px solid #e6e6e6;
    padding: 10px;
    box-sizing: border-box;
    overflow-y: auto;
    max-height: 100vh;
}

.main-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
}
</style>