/**
 * uni CLI 跨平台包装脚本
 * 本项目为 HBuilderX 根目录布局（manifest.json / pages.json 均在 frontend 根目录，无 src/），
 * 而 uni CLI 默认把输入目录解析为 <cwd>/src，导致 ENOENT: src/manifest.json。
 * 此处在 CLI 启动前显式设置 UNI_INPUT_DIR / UNI_OUTPUT_DIR 指向项目根目录。
 */
const path = require('path')

// 输入目录：本脚本位于 frontend/scripts/，项目根即上一级
process.env.UNI_INPUT_DIR = process.env.UNI_INPUT_DIR || path.resolve(__dirname, '..')
// 输出目录：frontend/dist（保持默认约定）
process.env.UNI_OUTPUT_DIR = process.env.UNI_OUTPUT_DIR || path.resolve(__dirname, '..', 'dist')

// 透传命令行参数，交给官方 uni CLI 处理
require('@dcloudio/vite-plugin-uni/bin/uni.js')
