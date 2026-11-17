// 校验：pages.json 注册的每个页面都存在对应的 .vue 文件
const fs = require('fs')
const path = require('path')
const root = 'C:/Users/小青/Desktop/新建文件夹/liyeqing/frontend'
const pagesJson = JSON.parse(fs.readFileSync(path.join(root, 'pages.json'), 'utf8'))

let missing = []
let ok = 0
pagesJson.pages.forEach(p => {
  const file = path.join(root, p.path + '.vue')
  if (fs.existsSync(file)) {
    ok++
  } else {
    missing.push(p.path)
  }
})

// tabBar 图标校验
let iconMissing = []
;(pagesJson.tabBar.list || []).forEach(t => {
  ;[t.iconPath, t.selectedIconPath].forEach(ip => {
    if (ip && !fs.existsSync(path.join(root, ip))) iconMissing.push(ip)
  })
})

console.log(`pages.json 共注册 ${pagesJson.pages.length} 个页面，${ok} 个存在，${missing.length} 个缺失`)
if (missing.length) console.log('缺失:', missing.join(', '))
console.log(`tabBar 图标 ${iconMissing.length === 0 ? '全部存在' : '缺失: ' + iconMissing.join(', ')}`)

// 抽查关键新页面内容完整性
const checks = [
  'pages/companion/companion.vue',
  'pages/companion/companion-running.vue',
  'pages/role-select/role-select.vue'
]
checks.forEach(f => {
  const s = fs.readFileSync(path.join(root, f), 'utf8')
  const hasTpl = s.includes('</template>')
  const hasScript = s.includes('</script>')
  const hasStyle = s.includes('</style>')
  console.log(`${f}: template=${hasTpl} script=${hasScript} style=${hasStyle}`)
})

if (missing.length === 0 && iconMissing.length === 0) console.log('ALL CHECKS PASSED')
