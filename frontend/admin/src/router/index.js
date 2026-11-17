import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '管理员登录' }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/Index.vue'), meta: { title: '数据看板' } },
      { path: 'user', name: 'UserManage', component: () => import('@/views/user/Index.vue'), meta: { title: '用户管理' } },
      { path: 'role', name: 'RoleManage', component: () => import('@/views/role/Index.vue'), meta: { title: 'AI角色素材管理' } },
      { path: 'template', name: 'TemplateManage', component: () => import('@/views/template/Index.vue'), meta: { title: '任务模板管理' } },
      { path: 'content', name: 'ContentManage', component: () => import('@/views/content/Index.vue'), meta: { title: '内容管理' } }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - AI习惯伙伴后台` : 'AI习惯伙伴后台'
  const token = localStorage.getItem('admin_token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
