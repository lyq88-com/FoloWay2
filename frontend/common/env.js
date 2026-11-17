/**
 * 运行环境地址配置 —— 全项目「电脑 IP」的唯一出处
 *
 * 背景：
 *   后端地址原先硬编码在 common/request.js（H5 分支用相对路径，App 分支写死
 *   http://172.20.10.3:8000），同一个 IP 还散落在别处。换 WiFi / 换电脑后手机端
 *   全部连不上，且要人肉去好几个文件里找。
 *
 * 现在：
 *   - 只在这里写一次 LAN_HOST，request.js 等统一从这里取。
 *   - H5 一律用相对路径（走 vite devServer proxy，不经局域网，永远不会因为 IP 变而挂）。
 *   - App / 微信小程序 必须用局域网绝对地址，换网络时执行：
 *       node tools/sync-lan-host.js
 *     （或双击 tools/sync-lan-host.bat）自动把本机当前 IPv4 写回本文件。
 *
 * 注意：uni-app 的条件编译（#ifdef / #ifndef）在 .js 文件里同样生效，
 *       所以 H5 / 非 H5 两套值各自只会保留一份。
 */

// #ifdef H5
// H5：相对路径，由 vite devServer proxy 转发到 127.0.0.1:8000（见 vite.config.js / manifest.json）
export const API_BASE = '/api/v1'
export const STATIC_BASE = '/uploads'
// 独立 AI 聊天后端（Flask 5001），同样走 proxy 的 /ai 规则
export const AI_BASE = '/ai'
export const LAN_HOST = ''
// #endif

// #ifndef H5
// ↓↓↓ 换 WiFi 后改这一行即可（或跑 tools/sync-lan-host.js 自动改） ↓↓↓
const LAN_HOST_VALUE = 'http://172.20.10.3:8000'
export const LAN_HOST = LAN_HOST_VALUE
export const API_BASE = LAN_HOST_VALUE + '/api/v1'
export const STATIC_BASE = LAN_HOST_VALUE + '/uploads'
export const AI_BASE = LAN_HOST_VALUE.replace(':8000', ':5001') + '/ai'
// #endif

export default { API_BASE, STATIC_BASE, AI_BASE, LAN_HOST }
