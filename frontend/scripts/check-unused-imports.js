/**
 * 无用 import / 未使用变量粗扫描（启发式）
 * 用法：node scripts/check-unused-imports.js
 * 规则：
 *   1. 提取 <script> 块中所有 import 语句的绑定名
 *   2. 检查绑定名在 import 行之后的代码中出现次数（剔除注释行）
 *   3. 出现 0 次即报告为疑似无用 import
 * 注意：仅静态文本匹配，动态使用（字符串拼接）可能误报，人工确认后再删。
 */
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')
const SKIP = /node_modules|dist|_cli_backup|unpackage|admin[\\/]/

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const full = path.join(dir, name)
    const stat = fs.statSync(full)
    if (stat.isDirectory()) {
      if (!SKIP.test(full + path.sep)) walk(full, out)
    } else if (/\.(vue|js)$/.test(name)) {
      out.push(full)
    }
  }
  return out
}

const files = walk(ROOT)
const report = []

for (const file of files) {
  let src = fs.readFileSync(file, 'utf8')
  let script = src
  let baseLine = 0
  const m = /<script[^>]*>([\s\S]*?)<\/script>/.exec(src)
  if (m) {
    script = m[1]
    baseLine = src.slice(0, m.index).split('\n').length
  }
  const lines = script.split('\n')
  // 收集 import 行
  lines.forEach((line, i) => {
    const im = /^\s*import\s+(?:([\w$]+)\s*,?\s*)?(?:\{([^}]*)\}\s*|([\w$]+)\s+from\s+|\*\s+as\s+([\w$]+)\s+from\s+)?.*$/.exec(line)
    if (!im || !/^\s*import\s/.test(line)) return
    const names = []
    if (im[1]) names.push(im[1])                     // import defaultExport from ...
    if (im[2]) {                                      // import { a, b as c }
      for (const seg of im[2].split(',')) {
        const n = seg.trim().split(/\s+as\s+/).pop().trim()
        if (n) names.push(n)
      }
    }
    if (im[3]) names.push(im[3])                      // import fs from ...
    if (im[4]) names.push(im[4])                      // import * as X
    if (!names.length) return
    // 检查 import 行之后（剔除注释）是否使用
    const rest = lines.slice(i + 1)
      .filter(l => !/^\s*(\/\/|\/\*|\*)/.test(l))
      .join('\n')
    for (const n of names) {
      const re = new RegExp('\\b' + n.replace(/[$]/g, '\\$') + '\\b')
      if (!re.test(rest)) {
        report.push(`${path.relative(ROOT, file).replace(/\\/g, '/')}:${baseLine + i + 1} [${n}]`)
      }
    }
  })
}

if (report.length === 0) {
  console.log('NO UNUSED IMPORTS FOUND')
} else {
  console.log(`疑似无用 import ${report.length} 处（人工确认后再删除）：`)
  report.forEach(r => console.log('  ' + r))
}
