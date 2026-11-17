/**
 * character-sprites.js
 * 20个AI伙伴的Q版SVG角色视觉参数定义
 * 每个角色有独特的发型、眼型、服装和配饰
 * 不改动 ai-characters.js 的任何数据
 */

// ==================== 视觉分类常量 ====================

export const FACE_SHAPES = {
  ROUND: 'round',       // 圆脸（可爱型）
  OVAL: 'oval',         // 鹅蛋脸（优雅型）
  CHUBBY: 'chubby',     // 婴儿肥（软萌型）
  SOFT_SQUARE: 'softSquare' // 柔和方脸（清冷型）
}

export const EYE_STYLES = {
  ROUND: 'round',       // 大圆眼（可爱/元气）
  ALMOND: 'almond',     // 杏仁眼（温柔/优雅）
  DROOPY: 'droopy',     // 垂眼（治愈/软萌）
  CAT: 'cat',           // 猫眼（酷飒/赛博）
  SPARKLE: 'sparkle',   // 星星眼（活力/元气）
  NARROW: 'narrow'      // 细长眼（高冷/文艺）
}

export const HAIR_STYLES = {
  SHORT_BOB: 'shortBob',         // 齐耳短发
  LONG_STRAIGHT: 'longStraight',  // 长直发
  CURLY: 'curly',                 // 卷发
  TWIN_TAILS: 'twinTails',        // 双马尾
  PIXIE: 'pixie',                 // 精灵短发
  MEDIUM_WAVE: 'mediumWave',      // 中长波浪
  LONG_BRAID: 'longBraid',        // 长辫发
  HALF_UP: 'halfUp',              // 半扎发
  SPIKY: 'spiky',                 // 刺头
  MESSY: 'messy',                 // 蓬松乱发
  NEAT_SIDE: 'neatSide',          // 侧分短发
  ANCIENT_BUN: 'ancientBun'       // 古风发髻
}

export const OUTFIT_STYLES = {
  DRESS: 'dress',           // 连衣裙
  HOODIE: 'hoodie',         // 卫衣
  SHIRT: 'shirt',           // 衬衫
  HANFU: 'hanfu',           // 汉服
  TECH_SUIT: 'techSuit',    // 科技装
  SWEATER: 'sweater',       // 针织衫
  SPORTSWEAR: 'sportswear', // 运动服
  CROP_JACKET: 'cropJacket', // 短夹克
  TURTLENECK: 'turtleneck',  // 高领
  MAGIC_ROBE: 'magicRobe',   // 法袍
  ARMOR: 'armor',            // 轻甲
  CARDIGAN: 'cardigan'       // 开衫
}

// ==================== SVG形状库 ====================

/**
 * 生成头部SVG（大圆脸）
 */
function headSVG(shape, skinColor) {
  const shapes = {
    round: { rx: 38, ry: 40, cx: 50, cy: 52 },
    oval: { rx: 34, ry: 42, cx: 50, cy: 52 },
    chubby: { rx: 42, ry: 40, cx: 50, cy: 50 },
    softSquare: { rx: 30, ry: 36, cx: 50, cy: 52 }
  }
  const s = shapes[shape] || shapes.round
  return `<ellipse cx="${s.cx}" cy="${s.cy}" rx="${s.rx}" ry="${s.ry}" fill="${skinColor}" stroke="${darkenColor(skinColor, 0.08)}" stroke-width="1.5"/>`
}

/**
 * 生成眼睛SVG（不同眼型）
 */
function eyesSVG(eyeStyle, eyeColor, highlight, y = 48) {
  const styles = {
    round: `<ellipse cx="35" cy="${y}" rx="8" ry="9" fill="${eyeColor}"/><ellipse cx="65" cy="${y}" rx="8" ry="9" fill="${eyeColor}"/>`,
    almond: `<ellipse cx="35" cy="${y}" rx="7" ry="6" fill="${eyeColor}"/><ellipse cx="65" cy="${y}" rx="7" ry="6" fill="${eyeColor}"/>`,
    droopy: `<ellipse cx="35" cy="${y}" rx="7" ry="5" fill="${eyeColor}" transform="rotate(-10,35,${y})"/><ellipse cx="65" cy="${y}" rx="7" ry="5" fill="${eyeColor}" transform="rotate(10,65,${y})"/>`,
    cat: `<path d="M28,${y} Q35,${y-8} 42,${y} Q35,${y+3} 28,${y}Z" fill="${eyeColor}"/><path d="M58,${y} Q65,${y-8} 72,${y} Q65,${y+3} 58,${y}Z" fill="${eyeColor}"/>`,
    sparkle: `<ellipse cx="35" cy="${y}" rx="9" ry="10" fill="${eyeColor}"/><ellipse cx="65" cy="${y}" rx="9" ry="10" fill="${eyeColor}"/>`,
    narrow: `<ellipse cx="35" cy="${y}" rx="6" ry="3.5" fill="${eyeColor}"/><ellipse cx="65" cy="${y}" rx="6" ry="3.5" fill="${eyeColor}"/>`
  }
  let svg = styles[eyeStyle] || styles.round
  // Eye highlights
  if (highlight) {
    svg += `<circle cx="32" cy="${y-4}" r="3" fill="white" opacity="0.9"/><circle cx="62" cy="${y-4}" r="3" fill="white" opacity="0.9"/>`
    svg += `<circle cx="38" cy="${y-3}" r="1.5" fill="white" opacity="0.7"/><circle cx="68" cy="${y-3}" r="1.5" fill="white" opacity="0.7"/>`
  }
  return svg
}

/**
 * 生成眨眼动画的闭眼SVG
 */
function eyesClosedSVG(eyeStyle, eyeColor, y = 48) {
  if (eyeStyle === 'cat') {
    return `<path d="M28,${y} Q35,${y+3} 42,${y}" fill="none" stroke="${eyeColor}" stroke-width="2.5" stroke-linecap="round"/><path d="M58,${y} Q65,${y+3} 72,${y}" fill="none" stroke="${eyeColor}" stroke-width="2.5" stroke-linecap="round"/>`
  }
  return `<line x1="26" y1="${y}" x2="44" y2="${y}" stroke="${eyeColor}" stroke-width="2.8" stroke-linecap="round"/><line x1="56" y1="${y}" x2="74" y2="${y}" stroke="${eyeColor}" stroke-width="2.8" stroke-linecap="round"/>`
}

/**
 * 生成眉毛SVG
 */
function eyebrowsSVG(style, y = 38) {
  const styles = {
    'soft-arch': `<path d="M26,${y} Q35,${y-4} 44,${y}" fill="none" stroke="#5D4037" stroke-width="2.2" stroke-linecap="round"/><path d="M56,${y} Q65,${y-4} 74,${y}" fill="none" stroke="#5D4037" stroke-width="2.2" stroke-linecap="round"/>`,
    'straight': `<line x1="26" y1="${y}" x2="44" y2="${y}" stroke="#4A3728" stroke-width="2.2" stroke-linecap="round"/><line x1="56" y1="${y}" x2="74" y2="${y}" stroke="#4A3728" stroke-width="2.2" stroke-linecap="round"/>`,
    'angled': `<path d="M26,${y} Q35,${y-6} 44,${y-2}" fill="none" stroke="#4A3728" stroke-width="2.2" stroke-linecap="round"/><path d="M56,${y} Q65,${y-6} 74,${y-2}" fill="none" stroke="#4A3728" stroke-width="2.2" stroke-linecap="round"/>`,
    'thick': `<line x1="25" y1="${y}" x2="45" y2="${y}" stroke="#3E2723" stroke-width="3" stroke-linecap="round"/><line x1="55" y1="${y}" x2="75" y2="${y}" stroke="#3E2723" stroke-width="3" stroke-linecap="round"/>`
  }
  return styles[style] || styles['soft-arch']
}

/**
 * 生成腮红SVG
 */
function blushSVG(color, opacity, y = 58) {
  return `<ellipse cx="28" cy="${y}" rx="7" ry="4" fill="${color}" opacity="${opacity}"/><ellipse cx="72" cy="${y}" rx="7" ry="4" fill="${color}" opacity="${opacity}"/>`
}

/**
 * 生成嘴巴SVG
 */
function mouthSVG(style, y = 62) {
  const styles = {
    'small-smile': `<path d="M45,${y} Q50,${y+4} 55,${y}" fill="none" stroke="#D4756B" stroke-width="2" stroke-linecap="round"/>`,
    'wide-smile': `<path d="M42,${y} Q50,${y+6} 58,${y}" fill="none" stroke="#D4756B" stroke-width="2" stroke-linecap="round"/>`,
    'gentle': `<path d="M44,${y} Q50,${y+2} 56,${y}" fill="none" stroke="#D4756B" stroke-width="1.8" stroke-linecap="round"/>`,
    'neutral': `<line x1="45" y1="${y}" x2="55" y2="${y}" stroke="#C49A8A" stroke-width="1.8" stroke-linecap="round"/>`
  }
  return styles[style] || styles['small-smile']
}

/**
 * 生成头发SVG（根据发型返回前层+后层）
 */
function hairSVG(hairStyle, hairColor, hairHighlight) {
  const hc = hairColor
  const hl = hairHighlight || lightenColor(hairColor, 0.15)

  const styles = {
    shortBob: {
      back: `<ellipse cx="50" cy="22" rx="40" ry="32" fill="${hc}"/>`,
      front: `<path d="M12,28 Q10,50 22,72 Q30,82 50,82 Q70,82 78,72 Q90,50 88,28 Q70,12 50,12 Q30,12 12,28Z" fill="${hc}"/><path d="M30,12 Q40,8 50,8 Q60,8 70,12" fill="none" stroke="${hl}" stroke-width="2" opacity="0.5"/><path d="M14,35 Q16,50 28,68" fill="none" stroke="${hl}" stroke-width="1.5" opacity="0.4"/><path d="M86,35 Q84,50 72,68" fill="none" stroke="${hl}" stroke-width="1.5" opacity="0.4"/>`
    },
    longStraight: {
      back: `<ellipse cx="50" cy="22" rx="40" ry="32" fill="${hc}"/><rect x="14" y="40" width="72" height="50" rx="8" fill="${hc}"/>`,
      front: `<path d="M10,30 Q8,55 18,85 Q24,95 35,98 L65,98 Q76,95 82,85 Q92,55 90,30 Q72,10 50,10 Q28,10 10,30Z" fill="${hc}"/><path d="M16,40 Q14,60 22,80" fill="none" stroke="${hl}" stroke-width="2" opacity="0.4"/><path d="M84,40 Q86,60 78,80" fill="none" stroke="${hl}" stroke-width="2" opacity="0.4"/>`
    },
    curly: {
      back: `<ellipse cx="50" cy="20" rx="42" ry="34" fill="${hc}"/>`,
      front: `<path d="M8,30 Q6,50 16,78 Q24,98 50,100 Q76,98 84,78 Q94,50 92,30 Q74,8 50,8 Q26,8 8,30Z" fill="${hc}"/><circle cx="20" cy="25" r="8" fill="${hl}" opacity="0.3"/><circle cx="80" cy="25" r="8" fill="${hl}" opacity="0.3"/><circle cx="50" cy="15" r="10" fill="${hl}" opacity="0.3"/>`
    },
    twinTails: {
      back: `<ellipse cx="50" cy="22" rx="38" ry="30" fill="${hc}"/><rect x="12" y="30" width="22" height="50" rx="10" fill="${hc}"/><rect x="66" y="30" width="22" height="50" rx="10" fill="${hc}"/>`,
      front: `<path d="M12,30 Q10,55 20,80 Q26,92 32,95 L68,95 Q74,92 80,80 Q90,55 88,30 Q70,12 50,12 Q30,12 12,30Z" fill="${hc}"/><circle cx="24" cy="18" r="5" fill="${hl}" opacity="0.6"/><circle cx="76" cy="18" r="5" fill="${hl}" opacity="0.6"/>`
    },
    pixie: {
      back: `<ellipse cx="50" cy="24" rx="36" ry="28" fill="${hc}"/>`,
      front: `<path d="M16,30 Q14,50 24,68 Q30,78 50,78 Q70,78 76,68 Q86,50 84,30 Q72,14 50,14 Q28,14 16,30Z" fill="${hc}"/><path d="M34,16 Q40,12 50,12 Q60,12 66,16" fill="none" stroke="${hl}" stroke-width="2" opacity="0.5"/>`
    },
    mediumWave: {
      back: `<ellipse cx="50" cy="22" rx="40" ry="32" fill="${hc}"/><rect x="16" y="38" width="68" height="38" rx="6" fill="${hc}"/>`,
      front: `<path d="M10,30 Q8,55 18,80 Q26,96 50,98 Q74,96 82,80 Q92,55 90,30 Q72,10 50,10 Q28,10 10,30Z" fill="${hc}"/><path d="M20,35 Q16,50 24,72 Q26,78 30,82" fill="none" stroke="${hl}" stroke-width="2" opacity="0.5"/><path d="M80,35 Q84,50 76,72 Q74,78 70,82" fill="none" stroke="${hl}" stroke-width="2" opacity="0.5"/>`
    },
    longBraid: {
      back: `<ellipse cx="50" cy="22" rx="38" ry="30" fill="${hc}"/><rect x="18" y="40" width="64" height="55" rx="6" fill="${hc}"/>`,
      front: `<path d="M12,32 Q10,55 20,82 Q28,98 50,100 Q72,98 80,82 Q90,55 88,32 Q70,12 50,12 Q30,12 12,32Z" fill="${hc}"/><path d="M50,82 Q48,88 50,94 Q52,88 50,82" fill="none" stroke="${hl}" stroke-width="2"/>`
    },
    halfUp: {
      back: `<ellipse cx="50" cy="22" rx="38" ry="30" fill="${hc}"/><rect x="18" y="38" width="64" height="42" rx="6" fill="${hc}"/>`,
      front: `<path d="M14,30 Q12,50 22,76 Q28,94 50,96 Q72,94 78,76 Q88,50 86,30 Q70,12 50,12 Q30,12 14,30Z" fill="${hc}"/><circle cx="50" cy="18" r="12" fill="${hc}"/><circle cx="50" cy="18" r="8" fill="${hl}" opacity="0.5"/>`
    },
    spiky: {
      back: `<ellipse cx="50" cy="24" rx="36" ry="28" fill="${hc}"/>`,
      front: `<path d="M18,34 L10,14 L24,28 L16,6 L34,24 L30,4 L44,22 L44,2 L54,22 L54,4 L62,24 L76,6 L70,28 L88,14 L80,34 Q88,54 78,72 Q72,82 50,82 Q28,82 22,72 Q12,54 18,34Z" fill="${hc}"/>`
    },
    messy: {
      back: `<ellipse cx="50" cy="20" rx="42" ry="34" fill="${hc}"/>`,
      front: `<path d="M6,32 Q4,54 14,76 Q22,96 50,98 Q78,96 86,76 Q96,54 94,32 Q76,8 50,8 Q24,8 6,32Z" fill="${hc}"/><path d="M24,14 Q30,8 36,16" fill="none" stroke="${hl}" stroke-width="2" opacity="0.6"/><path d="M64,12 Q70,6 78,14" fill="none" stroke="${hl}" stroke-width="2" opacity="0.6"/>`
    },
    neatSide: {
      back: `<ellipse cx="50" cy="24" rx="36" ry="28" fill="${hc}"/>`,
      front: `<path d="M18,28 Q14,48 24,68 Q30,80 50,80 Q70,80 76,68 Q86,48 82,28 Q70,14 50,14 Q30,14 18,28Z" fill="${hc}"/><path d="M24,20 Q32,14 50,14" fill="none" stroke="${hl}" stroke-width="2" opacity="0.6"/>`
    },
    ancientBun: {
      back: `<ellipse cx="50" cy="22" rx="38" ry="30" fill="${hc}"/><rect x="18" y="38" width="64" height="50" rx="6" fill="${hc}"/>`,
      front: `<path d="M12,32 Q10,55 20,82 Q28,98 50,100 Q72,98 80,82 Q90,55 88,32 Q70,12 50,12 Q30,12 12,32Z" fill="${hc}"/><circle cx="50" cy="14" r="14" fill="${hc}"/><circle cx="50" cy="14" r="10" fill="${hl}" opacity="0.4"/><line x1="38" y1="14" x2="28" y2="14" stroke="${hc}" stroke-width="3" stroke-linecap="round"/>`
    }
  }

  return styles[hairStyle] || styles.shortBob
}

/**
 * 生成服装SVG
 */
function outfitSVG(outfitStyle, color, accent, isMale) {
  const c = color
  const a = accent || lightenColor(color, 0.2)

  const styles = {
    dress: `<path d="M30,100 L20,180 Q20,190 35,190 L65,190 Q80,190 80,180 L70,100 Q65,95 50,95 Q35,95 30,100Z" fill="${c}"/><path d="M30,100 Q50,108 70,100" fill="none" stroke="${a}" stroke-width="2" opacity="0.6"/><rect x="40" y="160" width="20" height="25" rx="5" fill="${a}" opacity="0.4"/>`,
    hoodie: `<path d="M28,100 L18,185 Q18,192 32,192 L68,192 Q82,192 82,185 L72,100 Q65,95 50,95 Q35,95 28,100Z" fill="${c}"/><path d="M28,100 Q22,80 26,65 Q30,52 45,55 L50,65 Q52,58 55,55 Q70,52 74,65 Q78,80 72,100" fill="${c}"/><rect x="30" y="125" width="40" height="25" rx="8" fill="${a}" opacity="0.4"/>`,
    shirt: `<path d="M30,100 L22,188 Q22,195 35,195 L50,195 L50,100 Q35,98 30,100Z" fill="${c}"/><path d="M70,100 L78,188 Q78,195 65,195 L50,195 L50,100 Q65,98 70,100Z" fill="${c}"/><line x1="50" y1="98" x2="50" y2="195" stroke="${a}" stroke-width="1" opacity="0.3"/><circle cx="50" cy="108" r="6" fill="${a}" opacity="0.5"/>`,
    hanfu: `<path d="M25,100 L15,185 Q15,192 30,192 L50,192 L50,100 Q35,96 25,100Z" fill="${c}"/><path d="M75,100 L85,185 Q85,192 70,192 L50,192 L50,100 Q65,96 75,100Z" fill="${c}"/><path d="M25,100 Q50,110 75,100" fill="none" stroke="${a}" stroke-width="3" opacity="0.6"/><path d="M30,130 L20,160" stroke="${a}" stroke-width="2" opacity="0.4"/>`,
    techSuit: `<path d="M28,100 L20,185 Q20,192 30,192 L70,192 Q80,192 80,185 L72,100 Q65,95 50,95 Q35,95 28,100Z" fill="${c}"/><path d="M28,100 L20,130 L28,160" fill="none" stroke="${a}" stroke-width="1.5" opacity="0.7"/><path d="M72,100 L80,130 L72,160" fill="none" stroke="${a}" stroke-width="1.5" opacity="0.7"/><circle cx="50" cy="110" r="8" fill="${a}" opacity="0.5"/><circle cx="50" cy="110" r="4" fill="#fff" opacity="0.8"/>`,
    sweater: `<path d="M26,100 L18,188 Q18,195 30,195 L70,195 Q82,195 82,188 L74,100 Q65,95 50,95 Q35,95 26,100Z" fill="${c}"/><rect x="28" y="130" width="44" height="15" rx="4" fill="${a}" opacity="0.3"/><rect x="28" y="155" width="44" height="15" rx="4" fill="${a}" opacity="0.2"/>`,
    sportswear: `<path d="M28,100 L18,185 Q18,192 30,192 L70,192 Q82,192 82,185 L72,100 Q65,95 50,95 Q35,95 28,100Z" fill="${c}"/><line x1="36" y1="100" x2="28" y2="192" stroke="${a}" stroke-width="2" opacity="0.5"/><line x1="64" y1="100" x2="72" y2="192" stroke="${a}" stroke-width="2" opacity="0.5"/><circle cx="50" cy="108" r="5" fill="${a}" opacity="0.6"/>`,
    cropJacket: `<path d="M28,100 L20,150 L28,160 L72,160 L80,150 L72,100 Q65,95 50,95 Q35,95 28,100Z" fill="${c}"/><path d="M28,100 L20,120 L26,140" fill="none" stroke="${a}" stroke-width="1.5" opacity="0.5"/><path d="M72,100 L80,120 L74,140" fill="none" stroke="${a}" stroke-width="1.5" opacity="0.5"/>`,
    turtleneck: `<path d="M26,95 L18,188 Q18,195 30,195 L70,195 Q82,195 82,188 L74,95 Q68,90 50,90 Q32,90 26,95Z" fill="${c}"/><path d="M34,90 Q50,100 66,90" fill="none" stroke="${a}" stroke-width="2" opacity="0.5"/>`,
    magicRobe: `<path d="M22,100 L10,188 Q10,196 28,196 L72,196 Q90,196 90,188 L78,100 Q65,94 50,94 Q35,94 22,100Z" fill="${c}"/><path d="M22,100 Q50,115 78,100" fill="none" stroke="${a}" stroke-width="2.5" opacity="0.6"/><circle cx="35" cy="160" r="3" fill="${a}" opacity="0.5"/><circle cx="50" cy="170" r="3" fill="${a}" opacity="0.5"/><circle cx="65" cy="160" r="3" fill="${a}" opacity="0.5"/>`,
    armor: `<path d="M26,100 L18,185 Q18,192 30,195 L70,195 Q82,192 82,185 L74,100 Q65,94 50,94 Q35,94 26,100Z" fill="${c}"/><path d="M30,100 L26,140 L32,160" fill="none" stroke="${a}" stroke-width="3" opacity="0.6"/><path d="M70,100 L74,140 L68,160" fill="none" stroke="${a}" stroke-width="3" opacity="0.6"/><rect x="38" y="110" width="24" height="20" rx="3" fill="${a}" opacity="0.4"/>`,
    cardigan: `<path d="M28,100 L18,188 Q18,195 30,195 L70,195 Q82,195 82,188 L74,100 Q65,95 50,95 Q35,95 28,100Z" fill="${c}"/><line x1="50" y1="95" x2="50" y2="195" stroke="${a}" stroke-width="1.5" opacity="0.4"/><rect x="35" y="115" width="30" height="20" rx="3" fill="${a}" opacity="0.3"/>`
  }

  return styles[outfitStyle] || styles.dress
}

/**
 * 生成配饰SVG
 */
function accessorySVG(accessory, color, primaryColor) {
  const acc = {
    'leaf-crown': `<path d="M30,14 Q40,4 50,10 Q60,4 70,14" fill="none" stroke="#4CAF50" stroke-width="2"/><ellipse cx="30" cy="14" rx="5" ry="3" fill="#66BB6A" transform="rotate(-30,30,14)"/><ellipse cx="70" cy="14" rx="5" ry="3" fill="#66BB6A" transform="rotate(30,70,14)"/><ellipse cx="50" cy="10" rx="5" ry="3" fill="#81C784"/>`,
    'star-hairpin': `<polygon points="70,15 72,21 78,21 73,25 75,31 70,27 65,31 67,25 62,21 68,21" fill="${color || '#FFD700'}"/>`,
    'glasses': `<circle cx="35" cy="44" r="11" fill="none" stroke="${color || '#333'}" stroke-width="2.5"/><circle cx="65" cy="44" r="11" fill="none" stroke="${color || '#333'}" stroke-width="2.5"/><line x1="46" y1="44" x2="54" y2="44" stroke="${color || '#333'}" stroke-width="2.5"/>`,
    'cat-ears': `<path d="M20,30 L12,8 L32,25Z" fill="${primaryColor}" stroke="${darkenColor(primaryColor, 0.15)}" stroke-width="1"/><path d="M80,30 L88,8 L68,25Z" fill="${primaryColor}" stroke="${darkenColor(primaryColor, 0.15)}" stroke-width="1"/><path d="M16,24 L22,10 L30,22" fill="#FFB6C1" opacity="0.6"/><path d="M84,24 L78,10 L70,22" fill="#FFB6C1" opacity="0.6"/>`,
    'dragon-horns': `<path d="M28,18 Q20,0 32,-8 Q36,0 36,12" fill="${color || '#E63946'}" stroke="${darkenColor(color || '#E63946', 0.2)}" stroke-width="1"/><path d="M72,18 Q80,0 68,-8 Q64,0 64,12" fill="${color || '#E63946'}" stroke="${darkenColor(color || '#E63946', 0.2)}" stroke-width="1"/>`,
    'tiger-ears': `<path d="M22,28 L10,4 L32,22Z" fill="${color || '#FFD700'}" stroke="#DAA520" stroke-width="1.5"/><path d="M78,28 L90,4 L68,22Z" fill="${color || '#FFD700'}" stroke="#DAA520" stroke-width="1.5"/><path d="M16,20 L22,8 L30,20" fill="#FFF" opacity="0.5"/><path d="M84,20 L78,8 L70,20" fill="#FFF" opacity="0.5"/>`,
    'feather-wings': `<path d="M10,60 Q-5,40 8,20 Q15,40 20,55 Q25,80 15,95Z" fill="${color || '#2E8B57'}" opacity="0.5"/><path d="M8,45 Q-2,30 10,15" fill="${color || '#3CB371'}" opacity="0.6"/><path d="M90,60 Q105,40 92,20 Q85,40 80,55 Q75,80 85,95Z" fill="${color || '#2E8B57'}" opacity="0.5"/><path d="M92,45 Q102,30 90,15" fill="${color || '#3CB371'}" opacity="0.6"/>`,
    'circuit-lines': `<path d="M20,40 L30,40 L35,50 L45,50 L50,70" fill="none" stroke="${color || '#00FF7F'}" stroke-width="1.5" opacity="0.6"/><path d="M80,40 L70,40 L65,55 L60,55" fill="none" stroke="${color || '#00FF7F'}" stroke-width="1.5" opacity="0.6"/><circle cx="20" cy="40" r="2" fill="${color || '#00FF7F'}" opacity="0.8"/><circle cx="80" cy="40" r="2" fill="${color || '#00FF7F'}" opacity="0.8"/>`,
    'flame-aura': `<path d="M35,8 Q30,0 38,-6 Q42,0 45,-4 Q48,0 50,-6 Q52,0 55,-4 Q58,0 62,-6 Q70,0 65,8Z" fill="#FF4500" opacity="0.3"/><path d="M38,12 Q34,4 40,-2 Q44,4 46,0 Q48,4 50,-2 Q52,4 54,0 Q56,4 60,-2 Q66,4 62,12Z" fill="#FFD700" opacity="0.2"/>`,
    'shell-cloak': `<path d="M23,100 L18,140 L28,160 L50,165 L72,160 L82,140 L77,100Z" fill="${color || '#191970'}" opacity="0.3"/><path d="M28,110 L25,140 L35,155" fill="none" stroke="${color || '#483D8B'}" stroke-width="1.5" opacity="0.5"/><path d="M72,110 L75,140 L65,155" fill="none" stroke="${color || '#483D8B'}" stroke-width="1.5" opacity="0.5"/>`,
    'leaf-wings': `<ellipse cx="8" cy="55" rx="12" ry="25" fill="${color || '#228B22'}" opacity="0.3" transform="rotate(-20,8,55)"/><ellipse cx="92" cy="55" rx="12" ry="25" fill="${color || '#228B22'}" opacity="0.3" transform="rotate(20,92,55)"/><line x1="12" y1="40" x2="18" y2="70" stroke="${color || '#32CD32'}" stroke-width="1" opacity="0.5"/><line x1="88" y1="40" x2="82" y2="70" stroke="${color || '#32CD32'}" stroke-width="1" opacity="0.5"/>`,
    'ribbon': `<path d="M32,12 Q28,4 22,8 Q26,16 30,18Z" fill="${color || '#FFB7B2'}"/><path d="M68,12 Q72,4 78,8 Q74,16 70,18Z" fill="${color || '#FFB7B2'}"/>`,
    'choker': `<rect x="38" y="92" width="24" height="4" rx="2" fill="${color || '#333'}"/><circle cx="50" cy="94" r="2" fill="${color || '#FFD700'}"/>`,
    'headband': `<path d="M16,18 Q50,10 84,18" fill="none" stroke="${color || '#FFA500'}" stroke-width="4" stroke-linecap="round"/>`,
    'hair-clips': `<circle cx="24" cy="18" r="4" fill="${color || '#FF69B4'}"/><circle cx="76" cy="18" r="4" fill="${color || '#FF69B4'}"/>`,
    'visor': `<path d="M28,42 Q50,48 72,42 L72,50 Q50,56 28,50Z" fill="${color || '#00CED1'}" opacity="0.5"/>`,
    'flower-clip': `<circle cx="24" cy="16" r="6" fill="${color || '#FFB7C5'}"/><circle cx="24" cy="16" r="3" fill="${color || '#FFD700'}"/>`,
    'fan': `<path d="M75,30 L90,40 L80,50Z" fill="${color || '#DEB887'}" opacity="0.6"/><line x1="78" y1="35" x2="82" y2="45" stroke="${color || '#8B6914'}" stroke-width="1"/>`
  }
  return acc[accessory] || ''
}

// ==================== 颜色工具 ====================

// ↓↓↓ 修复 ↓↓↓ 角色数据缺字段时会传进来 undefined，原实现直接 hex.replace() 抛
// "Cannot read properties of undefined (reading 'replace')"，整个精灵组件渲染崩掉（角色画廊页实测复现过）。
// 现在非法值一律回退到灰色占位，保证页面不崩。
function normalizeHex(hex) {
  const s = typeof hex === 'string' ? hex.trim() : ''
  const raw = s.charAt(0) === '#' ? s.slice(1) : s
  return /^[0-9a-fA-F]{6}$/.test(raw) ? raw : 'CCCCCC'
}

function lightenColor(hex, amount) {
  const num = parseInt(normalizeHex(hex), 16)
  const r = Math.min(255, (num >> 16) + 40)
  const g = Math.min(255, ((num >> 8) & 0x00FF) + 40)
  const b = Math.min(255, (num & 0x0000FF) + 40)
  return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`
}

function darkenColor(hex, amount) {
  const num = parseInt(normalizeHex(hex), 16)
  const r = Math.max(0, (num >> 16) - Math.floor((num >> 16) * amount))
  const g = Math.max(0, ((num >> 8) & 0x00FF) - Math.floor(((num >> 8) & 0x00FF) * amount))
  const b = Math.max(0, (num & 0x0000FF) - Math.floor((num & 0x0000FF) * amount))
  return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`
}

export { lightenColor, darkenColor }

// ==================== 20个角色视觉参数定义 ====================

export const CHARACTER_SPRITES = {
  // 1. 林夕 - 松弛治愈少女，温柔如水
  linxi: {
    head: { shape: 'oval', skinColor: '#FEF0E0' },
    eyes: { style: 'droopy', color: '#6B8E6B', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'gentle',
    blush: { color: '#FFB6B0', opacity: 0.35 },
    hair: { style: 'mediumWave', color: '#7BA08B', highlight: '#A8C9B5' },
    outfit: { style: 'dress', color: '#7BA08B', accent: '#C8E6C9' },
    accessories: ['leaf-crown', 'ribbon'],
    special: null
  },

  // 2. 绵绵 - 棉花糖般柔软的女孩
  mianmian: {
    head: { shape: 'chubby', skinColor: '#FFF5EE' },
    eyes: { style: 'round', color: '#C97B7B', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'wide-smile',
    blush: { color: '#FFB7B2', opacity: 0.45 },
    hair: { style: 'curly', color: '#FFB7B2', highlight: '#FFD5D2' },
    outfit: { style: 'sweater', color: '#FFB7B2', accent: '#FFDAC1' },
    accessories: ['ribbon'],
    special: null
  },

  // 3. Yuki - Y2K元气少女
  yuki: {
    head: { shape: 'round', skinColor: '#FFF0F0' },
    eyes: { style: 'sparkle', color: '#FF6B9D', highlight: true },
    eyebrows: 'angled',
    mouth: 'wide-smile',
    blush: { color: '#FF9EC1', opacity: 0.4 },
    hair: { style: 'twinTails', color: '#FF6B9D', highlight: '#FF9EC1' },
    outfit: { style: 'hoodie', color: '#C44DFF', accent: '#FFD700' },
    accessories: ['star-hairpin', 'hair-clips'],
    special: null
  },

  // 4. Kira - 甜酷辣妹
  kira: {
    head: { shape: 'oval', skinColor: '#FFF0F3' },
    eyes: { style: 'cat', color: '#CC2952', highlight: true },
    eyebrows: 'angled',
    mouth: 'neutral',
    blush: { color: '#FF9A9E', opacity: 0.3 },
    hair: { style: 'longStraight', color: '#FF3D68', highlight: '#FF7093' },
    outfit: { style: 'cropJacket', color: '#FF3D68', accent: '#FECFEF' },
    accessories: ['choker'],
    special: null
  },

  // 5. 月清 - 新中式国风少女
  yueqing: {
    head: { shape: 'oval', skinColor: '#FEF5ED' },
    eyes: { style: 'almond', color: '#6B4423', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'gentle',
    blush: { color: '#E8C4B8', opacity: 0.3 },
    hair: { style: 'longBraid', color: '#4A3728', highlight: '#6B4A3A' },
    outfit: { style: 'hanfu', color: '#C4A77D', accent: '#E8DCC4' },
    accessories: ['flower-clip'],
    special: null
  },

  // 6. 枫夜 - 古风少年
  fengye: {
    head: { shape: 'oval', skinColor: '#FEF0E4' },
    eyes: { style: 'narrow', color: '#5D4E12', highlight: true },
    eyebrows: 'straight',
    mouth: 'gentle',
    blush: { color: '#DEB887', opacity: 0.15 },
    hair: { style: 'ancientBun', color: '#3E2723', highlight: '#5D4037' },
    outfit: { style: 'hanfu', color: '#8B6914', accent: '#DAA520' },
    accessories: ['fan'],
    special: null
  },

  // 7. Nova - 轻赛博少女
  nova: {
    head: { shape: 'oval', skinColor: '#F0FAFA' },
    eyes: { style: 'cat', color: '#00CED1', highlight: true },
    eyebrows: 'straight',
    mouth: 'neutral',
    blush: { color: '#00FFFF', opacity: 0.15 },
    hair: { style: 'pixie', color: '#00CED1', highlight: '#66FFFF' },
    outfit: { style: 'techSuit', color: '#008B8B', accent: '#00FFFF' },
    accessories: ['visor'],
    special: null
  },

  // 8. Zero - 赛博朋克少年
  zero: {
    head: { shape: 'softSquare', skinColor: '#F5F0FA' },
    eyes: { style: 'narrow', color: '#483D8B', highlight: true },
    eyebrows: 'angled',
    mouth: 'neutral',
    blush: { color: '#9370DB', opacity: 0.1 },
    hair: { style: 'spiky', color: '#C0C0C0', highlight: '#E8E8E8' },
    outfit: { style: 'armor', color: '#483D8B', accent: '#7B68EE' },
    accessories: ['circuit-lines'],
    special: 'circuit-lines'
  },

  // 9. 星尘 - 文艺氛围感少女
  xingchen: {
    head: { shape: 'oval', skinColor: '#FEF5F7' },
    eyes: { style: 'sparkle', color: '#9B59B6', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'gentle',
    blush: { color: '#EE82EE', opacity: 0.3 },
    hair: { style: 'mediumWave', color: '#DDA0DD', highlight: '#EEB8EE' },
    outfit: { style: 'dress', color: '#DDA0DD', accent: '#FFB6C1' },
    accessories: ['star-hairpin'],
    special: null
  },

  // 10. 慕寒 - 文艺青年
  muhan: {
    head: { shape: 'softSquare', skinColor: '#F8F6F0' },
    eyes: { style: 'narrow', color: '#4A5568', highlight: true },
    eyebrows: 'straight',
    mouth: 'gentle',
    blush: { color: '#A9A9A9', opacity: 0.15 },
    hair: { style: 'neatSide', color: '#4A3728', highlight: '#6B4A3A' },
    outfit: { style: 'cardigan', color: '#708090', accent: '#DCDCDC' },
    accessories: ['glasses'],
    special: null
  },

  // 11. 清禾 - 中性清冷
  qinghe: {
    head: { shape: 'softSquare', skinColor: '#F5F7FA' },
    eyes: { style: 'almond', color: '#4682B4', highlight: true },
    eyebrows: 'straight',
    mouth: 'neutral',
    blush: { color: '#B0C4DE', opacity: 0.2 },
    hair: { style: 'pixie', color: '#778899', highlight: '#A0B0C0' },
    outfit: { style: 'turtleneck', color: '#B0C4DE', accent: '#E6E6FA' },
    accessories: [],
    special: null
  },

  // 12. 晨风 - 清冷少年
  chenfeng: {
    head: { shape: 'softSquare', skinColor: '#F8F8F5' },
    eyes: { style: 'almond', color: '#363636', highlight: true },
    eyebrows: 'straight',
    mouth: 'gentle',
    blush: { color: '#A9A9A9', opacity: 0.1 },
    hair: { style: 'neatSide', color: '#2C2C2C', highlight: '#4A4A4A' },
    outfit: { style: 'shirt', color: '#A9A9A9', accent: '#D3D3D3' },
    accessories: [],
    special: null
  },

  // 13. Sunny - 元气少年
  sunny: {
    head: { shape: 'round', skinColor: '#FFF8ED' },
    eyes: { style: 'sparkle', color: '#CC7700', highlight: true },
    eyebrows: 'thick',
    mouth: 'wide-smile',
    blush: { color: '#FFB347', opacity: 0.3 },
    hair: { style: 'messy', color: '#FFA500', highlight: '#FFC04D' },
    outfit: { style: 'sportswear', color: '#FFA500', accent: '#FFD700' },
    accessories: ['headband'],
    special: null
  },

  // 14. 乐乐 - 活力少女
  lele: {
    head: { shape: 'round', skinColor: '#FFF5F5' },
    eyes: { style: 'sparkle', color: '#CC5599', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'wide-smile',
    blush: { color: '#FF85C0', opacity: 0.4 },
    hair: { style: 'twinTails', color: '#FF69B4', highlight: '#FF99CC' },
    outfit: { style: 'sportswear', color: '#FF69B4', accent: '#FFB7C5' },
    accessories: ['hair-clips'],
    special: null
  },

  // 15. 玲珑 - 瑞兽龙少女
  linglong: {
    head: { shape: 'oval', skinColor: '#FFF9F3' },
    eyes: { style: 'almond', color: '#B52B27', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'gentle',
    blush: { color: '#E63946', opacity: 0.2 },
    hair: { style: 'longBraid', color: '#8B0000', highlight: '#CC3333' },
    outfit: { style: 'magicRobe', color: '#E63946', accent: '#F1FAEE' },
    accessories: ['dragon-horns'],
    special: 'dragon-horns'
  },

  // 16. 白虎 - 瑞兽白虎少年
  baihu: {
    head: { shape: 'round', skinColor: '#FFFDE7' },
    eyes: { style: 'cat', color: '#B8860B', highlight: true },
    eyebrows: 'thick',
    mouth: 'wide-smile',
    blush: { color: '#FFD700', opacity: 0.25 },
    hair: { style: 'spiky', color: '#E8E8E8', highlight: '#FFFFFF' },
    outfit: { style: 'armor', color: '#FFD700', accent: '#FFFFFF' },
    accessories: ['tiger-ears'],
    special: 'tiger-ears'
  },

  // 17. 青鸾 - 瑞兽青鸟少女
  qinglan: {
    head: { shape: 'oval', skinColor: '#F5FFF5' },
    eyes: { style: 'droopy', color: '#1A5D32', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'gentle',
    blush: { color: '#90EE90', opacity: 0.25 },
    hair: { style: 'longStraight', color: '#2E8B57', highlight: '#4CAF79' },
    outfit: { style: 'magicRobe', color: '#2E8B57', accent: '#90EE90' },
    accessories: ['feather-wings'],
    special: 'feather-wings'
  },

  // 18. 玄武 - 瑞兽玄武少年
  xuanwu: {
    head: { shape: 'softSquare', skinColor: '#F0F0FA' },
    eyes: { style: 'narrow', color: '#0D0D3B', highlight: true },
    eyebrows: 'straight',
    mouth: 'neutral',
    blush: { color: '#483D8B', opacity: 0.15 },
    hair: { style: 'neatSide', color: '#0D0D3B', highlight: '#1A1A5E' },
    outfit: { style: 'armor', color: '#191970', accent: '#9370DB' },
    accessories: ['shell-cloak'],
    special: 'shell-cloak'
  },

  // 19. 火云 - 火麒麟少年
  huoyun: {
    head: { shape: 'round', skinColor: '#FFF5EE' },
    eyes: { style: 'sparkle', color: '#CC3700', highlight: true },
    eyebrows: 'thick',
    mouth: 'wide-smile',
    blush: { color: '#FF6347', opacity: 0.3 },
    hair: { style: 'messy', color: '#FF4500', highlight: '#FF7744' },
    outfit: { style: 'armor', color: '#FF4500', accent: '#FFD700' },
    accessories: ['flame-aura'],
    special: 'flame-aura'
  },

  // 20. 灵灵 - 森林精灵
  linling: {
    head: { shape: 'round', skinColor: '#F5FFF0' },
    eyes: { style: 'sparkle', color: '#1A5D1A', highlight: true },
    eyebrows: 'soft-arch',
    mouth: 'wide-smile',
    blush: { color: '#90EE90', opacity: 0.35 },
    hair: { style: 'longStraight', color: '#228B22', highlight: '#44BB44' },
    outfit: { style: 'dress', color: '#32CD32', accent: '#90EE90' },
    accessories: ['leaf-wings', 'leaf-crown'],
    special: 'leaf-wings'
  }
}

// ==================== SVG渲染函数 ====================

/**
 * 渲染头像SVG (只显示头部，60x60 viewBox)
 */
export function renderHeadSVG(spriteData, options = {}) {
  const { size = 60, showBlush = true } = options
  const s = spriteData
  const h = s.head
  const pad = 4
  const scale = size / (100 + pad * 2)

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-pad} ${-pad} ${100 + pad * 2} ${100 + pad * 2}" width="${size}" height="${size}">`
  svg += `<defs><clipPath id="headClip"><circle cx="50" cy="52" r="38"/></clipPath></defs>`

  // 背景光晕
  svg += `<circle cx="50" cy="52" r="46" fill="${s.hair.highlight}" opacity="0.15"/>`

  // 头发后层
  const hair = hairSVG(s.hair.style, s.hair.color, s.hair.highlight)
  svg += `<g clip-path="url(#headClip)">${hair.back}</g>`

  // 头部
  svg += headSVG(h.shape, h.skinColor)

  // 腮红
  if (showBlush) {
    svg += blushSVG(s.blush.color, s.blush.opacity)
  }

  // 眼睛
  svg += eyesSVG(s.eyes.style, s.eyes.color, s.eyes.highlight)

  // 眉毛
  svg += eyebrowsSVG(s.eyebrows)

  // 嘴巴
  svg += mouthSVG(s.mouth)

  // 头发前层
  svg += `<g clip-path="url(#headClip)">${hair.front || ''}</g>`

  // 配饰
  if (s.accessories && s.accessories.length > 0) {
    s.accessories.forEach(acc => {
      svg += accessorySVG(acc, s.hair.highlight, s.hair.color)
    })
  }

  // 特殊特征（仅头部相关）
  if (s.special === 'dragon-horns') svg += accessorySVG('dragon-horns', s.hair.color)
  if (s.special === 'tiger-ears') svg += accessorySVG('tiger-ears', s.hair.color)
  if (s.special === 'circuit-lines') svg += accessorySVG('circuit-lines', '#00FF7F', s.hair.color)
  if (s.special === 'flame-aura') svg += accessorySVG('flame-aura', s.hair.color)

  svg += `</svg>`
  return svg
}

/**
 * 渲染全身立绘SVG (160x200 viewBox)
 */
export function renderFullBodySVG(spriteData, options = {}) {
  const { width = 160, height = 200, showGlow = true } = options
  const s = spriteData

  // viewBox: 0 0 100 140 (head 0-90, body 90-140)
  const vbX = -10
  const vbY = -5
  const vbW = 120
  const vbH = 145

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${vbX} ${vbY} ${vbW} ${vbH}" width="${width}" height="${height}">`

  // 背景光晕
  if (showGlow) {
    svg += `<ellipse cx="50" cy="75" rx="55" ry="65" fill="${s.hair.highlight}" opacity="0.08"/>`
  }

  // 身体阴影
  svg += `<ellipse cx="50" cy="135" rx="20" ry="4" fill="#000" opacity="0.08"/>`

  // 头发后层
  const hair = hairSVG(s.hair.style, s.hair.color, s.hair.highlight)
  svg += hair.back

  // 头部
  svg += headSVG(s.head.shape, s.head.skinColor)

  // 腮红
  svg += blushSVG(s.blush.color, s.blush.opacity)

  // 眼睛
  svg += eyesSVG(s.eyes.style, s.eyes.color, s.eyes.highlight)

  // 眉毛
  svg += eyebrowsSVG(s.eyebrows)

  // 嘴巴
  svg += mouthSVG(s.mouth)

  // 服装
  svg += outfitSVG(s.outfit.style, s.outfit.color, s.outfit.accent)

  // 头发前层
  svg += hair.front || ''

  // 配饰
  if (s.accessories && s.accessories.length > 0) {
    s.accessories.forEach(acc => {
      svg += accessorySVG(acc, s.hair.highlight, s.hair.color)
    })
  }

  // 特殊特征
  if (s.special) {
    svg += accessorySVG(s.special, s.hair.color, s.hair.highlight)
  }

  svg += `</svg>`
  return svg
}

// ==================== 自定义角色sprite注册表 ====================
// 运行时注册表：存放在工坊创建的自定义角色视觉参数
// 不修改 CHARACTER_SPRITES（保持20个固定角色数据不变）
const CUSTOM_SPRITES = {}

/**
 * 注册自定义角色视觉参数
 * @param {String} id - 自定义角色ID（建议使用 'custom_' 前缀）
 * @param {Object} spriteData - 完整的视觉参数（结构同 CHARACTER_SPRITES 项）
 */
export function registerCustomSprite(id, spriteData) {
  if (!id || !spriteData) return
  // 规范化字段，避免缺字段导致渲染崩溃
  CUSTOM_SPRITES[id] = normalizeSpriteData(spriteData)
}

/**
 * 注销自定义角色视觉参数
 * @param {String} id
 */
export function unregisterCustomSprite(id) {
  if (id && CUSTOM_SPRITES[id]) {
    delete CUSTOM_SPRITES[id]
  }
}

/**
 * 批量注册自定义角色（用于从存储恢复时）
 * @param {Array} list - [{ id, sprite }, ...]
 */
export function registerCustomSprites(list) {
  if (!Array.isArray(list)) return
  list.forEach(item => {
    if (item && item.id && item.sprite) {
      registerCustomSprite(item.id, item.sprite)
    }
  })
}

/**
 * 规范化 spriteData，确保所有字段存在，避免渲染崩溃
 */
function normalizeSpriteData(raw) {
  const fallback = CHARACTER_SPRITES['linxi']
  const s = raw || {}
  return {
    head: {
      shape: (s.head && s.head.shape) || fallback.head.shape,
      skinColor: (s.head && s.head.skinColor) || fallback.head.skinColor
    },
    eyes: {
      style: (s.eyes && s.eyes.style) || fallback.eyes.style,
      color: (s.eyes && s.eyes.color) || fallback.eyes.color,
      highlight: s.eyes ? (s.eyes.highlight !== false) : true
    },
    eyebrows: s.eyebrows || fallback.eyebrows,
    mouth: s.mouth || fallback.mouth,
    blush: {
      color: (s.blush && s.blush.color) || fallback.blush.color,
      opacity: (s.blush && typeof s.blush.opacity === 'number') ? s.blush.opacity : fallback.blush.opacity
    },
    hair: {
      style: (s.hair && s.hair.style) || fallback.hair.style,
      color: (s.hair && s.hair.color) || fallback.hair.color,
      highlight: (s.hair && s.hair.highlight) || fallback.hair.highlight
    },
    outfit: {
      style: (s.outfit && s.outfit.style) || fallback.outfit.style,
      color: (s.outfit && s.outfit.color) || fallback.outfit.color,
      accent: (s.outfit && s.outfit.accent) || fallback.outfit.accent
    },
    accessories: Array.isArray(s.accessories) ? s.accessories : [],
    special: s.special || null
  }
}

/**
 * 根据工坊DIY配置构建 spriteData
 * @param {Object} diy - { faceShape, eyeStyle, eyeColor, hairStyle, hairColor, outfitStyle, outfitColor, accessory, skinColor, blushColor }
 * @returns {Object} spriteData
 */
export function buildSpriteFromConfig(diy) {
  const d = diy || {}
  const hairColor = d.hairColor || '#7BA08B'
  // 自动生成高光色（比主色浅）
  const hairHighlight = lightenColor(hairColor, 0.2)
  const outfitColor = d.outfitColor || '#7BA08B'
  const outfitAccent = lightenColor(outfitColor, 0.25)

  return normalizeSpriteData({
    head: {
      shape: d.faceShape || FACE_SHAPES.OVAL,
      skinColor: d.skinColor || '#FEF0E0'
    },
    eyes: {
      style: d.eyeStyle || EYE_STYLES.ALMOND,
      color: d.eyeColor || '#6B8E6B',
      highlight: true
    },
    eyebrows: d.eyebrowStyle || 'soft-arch',
    mouth: d.mouthStyle || 'gentle',
    blush: {
      color: d.blushColor || '#FFB6B0',
      opacity: 0.35
    },
    hair: {
      style: d.hairStyle || HAIR_STYLES.MEDIUM_WAVE,
      color: hairColor,
      highlight: hairHighlight
    },
    outfit: {
      style: d.outfitStyle || OUTFIT_STYLES.DRESS,
      color: outfitColor,
      accent: outfitAccent
    },
    accessories: d.accessory ? [d.accessory] : [],
    special: null
  })
}

/**
 * 根据角色ID获取视觉参数
 * 优先查找自定义注册表，再查固定角色表，最后回退到 linxi
 */
export function getSpriteData(characterId) {
  if (characterId && CUSTOM_SPRITES[characterId]) {
    return CUSTOM_SPRITES[characterId]
  }
  return CHARACTER_SPRITES[characterId] || CHARACTER_SPRITES['linxi']
}

/**
 * 获取所有角色视觉参数（仅固定角色，不含自定义）
 */
export function getAllSprites() {
  return CHARACTER_SPRITES
}

/**
 * 检查角色是否有自定义视觉参数（含自定义注册表）
 */
export function hasSprite(characterId) {
  if (characterId && CUSTOM_SPRITES[characterId]) return true
  return !!CHARACTER_SPRITES[characterId]
}

/**
 * 判断是否为自定义角色ID
 */
export function isCustomCharacterId(characterId) {
  return !!(characterId && CUSTOM_SPRITES[characterId])
}

/**
 * 渲染闭眼版（用于眨眼动画）
 */
export function renderBlinkSVG(spriteData, size = 60) {
  const s = spriteData
  const pad = 4

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-pad} ${-pad} ${100 + pad * 2} ${100 + pad * 2}" width="${size}" height="${size}">`

  // 头部
  svg += headSVG(s.head.shape, s.head.skinColor)
  // 腮红
  svg += blushSVG(s.blush.color, s.blush.opacity)
  // 闭眼
  svg += eyesClosedSVG(s.eyes.style, s.eyes.color)
  // 眉毛
  svg += eyebrowsSVG(s.eyebrows)
  // 嘴巴
  svg += mouthSVG(s.mouth)

  // 头发前层
  const hair = hairSVG(s.hair.style, s.hair.color, s.hair.highlight)
  svg += hair.back
  svg += hair.front || ''

  svg += `</svg>`
  return svg
}
