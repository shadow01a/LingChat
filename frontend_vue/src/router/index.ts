import { createRouter, createWebHistory } from "vue-router";

// 导入你的组件
// 为了性能，这里我们使用路由懒加载 (lazy-loading)
// 这意味着 Credits.vue 组件只会在用户访问 /credit 路径时才会被加载
const Credits = () => import("../components/views/Credits.vue");
const ComapionMode = () => import("../components/views/CompanionMode.vue");
const MainMenu = () => import("../components/views/MainMenu.vue");

// 1. 定义路由表
const routes = [
  {
    path: "/", // 这是你想要的URL路径
    name: "LingChat",
    component: ComapionMode, // 当访问 /credit 时，显示 Credits.vue 组件
  },
  {
    path: "/menu", // 这是你想要的URL路径
    name: "Menu",
    component: MainMenu, // 当访问 /credit 时，显示 Credits.vue 组件
  },
  {
    path: "/credit", // 这是你想要的URL路径
    name: "Credits",
    component: Credits, // 当访问 /credit 时，显示 Credits.vue 组件
  },
];

// 2. 创建路由实例
const router = createRouter({
  // 使用 HTML5 History 模式，URL会更美观（例如：http://localhost:5173/credit）
  // 而不是 hash 模式 (http://localhost:5173/#/credit)
  history: createWebHistory(),
  routes, // `routes: routes` 的缩写
});

// 3. 导出路由实例
export default router;
