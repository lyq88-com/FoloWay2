#!/usr/bin/env node
/**
 * 一键同步本机局域网 IP 到前端配置
 *
 * 用法：
 *   node tools/sync-lan-host.js
 *   （Windows 也可双击 tools/sync-lan-host.bat）
 *
 * 做了两件事：
 *   1. 取本机当前 IPv4（优先 Wi-Fi / 以太网这类真实网卡，跳过 127.x、169.254.x、虚拟机网卡）
 *   2. 把 ../frontend/common/env.js 里 LAN_HOST_VALUE 那一行改写成新 IP
 *
 * 为什么需要：App / 真机调试必须用局域网绝对地址访问后端，换 WiFi 后 172.20.10.3 这类
 * 旧 IP 就废了。以前要手改代码，现在跑一下这个脚本就行（改完记得重新运行/重新打包）。
 */
const os = require('os')
const fs = require('fs')
const path = require('path')

const SKIP_PREFIX = ['127.', '169.254.', '0.0.0.0']
// 虚拟机/容器/热点类网卡，通常不是手机能连到的那张
const SKIP_NAME = ['virtualbox', 'vmware', 'hyper-v', 'docker', 'wsl', 'vethernet', 'loopback', 'teredo', 'isatap']

function pickLanIp() {
  const ifaces = os.networkInterfaces()
  const candidates = []

  for (const name of Object.keys(ifaces)) {
    const lower = name.toLowerCase()
    if (SKIP_NAME.some((k) => lower.includes(k))) continue

    for (const net of ifaces[name] || []) {
      if (net.family !== 'IPv4' || net.internal) continue
      if (SKIP_PREFIX.some((p) => net.address.startsWith(p))) continue
      candidates.push({ name, address: net.address })
    }
  }

  if (!candidates.length) return null
  // 优先 Wi-Fi / WLAN / 以太网，其次任意候选
  const preferred = candidates.find((c) => /wi-?fi|wlan|ethernet|以太网/.test(c.name.toLowerCase()))
  return preferred || candidates[0]
}

function main() {
  const picked = pickLanIp()
  if (!picked) {
    console.error('✗ 没找到可用的局域网 IPv4 地址，请检查网络连接')
    process.exit(1)
  }

  const target = path.resolve(__dirname, '..', 'frontend', 'common', 'env.js')
  if (!fs.existsSync(target)) {
    console.error('✗ 找不到目标文件: ' + target)
    process.exit(1)
  }

  const src = fs.readFileSync(target, 'utf8')
  // 支持两种写法：直接赋值，或 `import.meta.env.VITE_API_ORIGIN || '...'` 兜底形式
  const re = /(const LAN_HOST_VALUE = (?:import\.meta\.env\.VITE_API_ORIGIN \|\| )?)'[^']*'/
  if (!re.test(src)) {
    console.error('✗ env.js 里没找到 LAN_HOST_VALUE 定义，文件可能被改过')
    process.exit(1)
  }

  const oldLine = src.match(re)[0]
  const newLine = oldLine.replace(/'[^']*'$/, `'http://${picked.address}:8000'`)
  if (oldLine === newLine) {
    console.log(`✓ 已是最新：${picked.address}（网卡 ${picked.name}），无需修改`)
    return
  }

  fs.writeFileSync(target, src.replace(re, newLine), 'utf8')
  const old = oldLine.match(/'([^']*)'$/)[1]
  console.log(`✓ 已更新：${old} -> http://${picked.address}:8000（网卡 ${picked.name}）`)
  console.log('  改完请重新运行 H5 / 重新打包 App，旧进程读的是旧值。')
}

main()
