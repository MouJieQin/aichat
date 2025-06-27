import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

// 懒加载组件
const Home = () => import('@/views/Home.vue')
const Page1 = () => import('@/views/Page1.vue')
const History = () => import('@/views/History.vue')

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        component: () => import('@/layouts/SidebarLayout.vue'),
        children: [
            {
                path: '',
                name: 'Home',
                component: Home
            },
            {
                path: 'page1',
                name: 'Page1',
                component: Page1
            },
            {
                path: 'history/:id',
                name: 'History',
                component: History
            }
        ]
    },
    // 不需要侧边栏的路由可以单独定义
    //   {
    //     path: '/login',
    //     name: 'Login',
    //     component: () => import('../views/Login.vue')
    //   }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router  