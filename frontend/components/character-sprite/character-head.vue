<template>
  <character-sprite
    :character-id="characterId"
    mode="head"
    :size="size"
    :width="width"
    :animation="animation"
    :blink-interval="blinkInterval"
    :disable-blink="disableBlink"
  />
</template>

<script>
import CharacterSprite from './character-sprite.vue'

export default {
  name: 'CharacterHead',
  components: { CharacterSprite },
  props: {
    characterId: { type: String, default: 'linxi' },
    size: { type: String, default: 'medium' },
    width: { type: Number, default: 0 },
    animation: { type: String, default: 'float' },
    blinkInterval: { type: Number, default: 3000 },
    disableBlink: { type: Boolean, default: false }
  }
}
</script>
