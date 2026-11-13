<script setup>
import SceneView from './components/SceneView.vue'
import SceneViewV2 from './components/SceneViewV2.vue'
import SceneViewCar from './components/SceneViewCar.vue'

// 页面路由：?scene=v2 参考图复现场（models-v2）；?scene=car 汽车制造车间（models-car）；默认老场景
const scene = new URLSearchParams(window.location.search).get('scene')
</script>

<template>
  <SceneViewCar v-if="scene === 'car'" />
  <SceneViewV2 v-else-if="scene === 'v2'" />
  <SceneView v-else />
</template>
