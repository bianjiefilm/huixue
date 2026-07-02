<template>
  <div class="skill-constellation" ref="containerRef">
    <canvas 
      ref="canvasRef" 
      :width="canvasWidth" 
      :height="canvasHeight"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    />
    
    <!-- Tooltip -->
    <div 
      v-if="hoveredSkill" 
      class="skill-tooltip"
      :style="{ left: `${tooltipPosition.x}px`, top: `${tooltipPosition.y}px` }"
    >
      <div class="tooltip-header">
        <span class="tooltip-name">{{ hoveredSkill.name }}</span>
        <span class="tooltip-category">{{ hoveredSkill.category }}</span>
      </div>
      <div class="tooltip-mastery">
        <span class="mastery-label">Mastery</span>
        <div class="mastery-bar">
          <div class="mastery-fill" :style="{ width: `${hoveredSkill.mastery}%` }" />
        </div>
        <span class="mastery-value">{{ hoveredSkill.mastery }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import type { SkillNode } from '@/stores/aiCopilot'

interface Props {
  skills: SkillNode[]
}

const props = defineProps<Props>()

// Refs
const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const canvasWidth = ref(400)
const canvasHeight = ref(300)

// Computed positions for each skill
interface SkillPosition {
  skill: SkillNode
  x: number
  y: number
  radius: number
}

const skillPositions = ref<SkillPosition[]>([])

// Hover state
const hoveredSkill = ref<SkillNode | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })

// Animation
let animationFrameId: number | null = null
let time = 0

// Calculate positions based on skill connections
const calculatePositions = () => {
  if (!props.skills.length) return []
  
  const centerX = canvasWidth.value / 2
  const centerY = canvasHeight.value / 2
  const maxRadius = Math.min(centerX, centerY) - 40
  
  const positions: SkillPosition[] = []
  const angleStep = (2 * Math.PI) / props.skills.length
  
  props.skills.forEach((skill, index) => {
    // Position skills in a circular pattern with some variation
    const angle = angleStep * index - Math.PI / 2
    const radiusFactor = 0.6 + (skill.mastery / 100) * 0.3
    const distance = maxRadius * radiusFactor
    
    positions.push({
      skill,
      x: centerX + Math.cos(angle) * distance,
      y: centerY + Math.sin(angle) * distance,
      radius: 20 + (skill.mastery / 100) * 15
    })
  })
  
  return positions
}

// Draw the constellation
const draw = () => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // Clear canvas
  ctx.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  const positions = skillPositions.value
  if (!positions.length) return
  
  // Draw connections
  ctx.strokeStyle = 'rgba(0, 217, 255, 0.15)'
  ctx.lineWidth = 1
  
  positions.forEach((pos) => {
    const connectedSkills = pos.skill.connections || []
    connectedSkills.forEach((connId) => {
      const connPos = positions.find(p => p.skill.id === connId)
      if (connPos) {
        ctx.beginPath()
        ctx.moveTo(pos.x, pos.y)
        ctx.lineTo(connPos.x, connPos.y)
        ctx.stroke()
      }
    })
  })
  
  // Draw nodes
  positions.forEach((pos) => {
    const isHovered = hoveredSkill.value?.id === pos.skill.id
    const pulseOffset = Math.sin(time * 0.02 + positions.indexOf(pos)) * 2
    const currentRadius = pos.radius + (isHovered ? 5 : 0) + pulseOffset
    
    // Outer glow
    const gradient = ctx.createRadialGradient(
      pos.x, pos.y, 0,
      pos.x, pos.y, currentRadius * 2
    )
    
    const masteryColor = getMasteryColor(pos.skill.mastery)
    gradient.addColorStop(0, masteryColor.replace(')', ', 0.3)').replace('rgb', 'rgba'))
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0)')
    
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, currentRadius * 2, 0, Math.PI * 2)
    ctx.fillStyle = gradient
    ctx.fill()
    
    // Main node
    ctx.beginPath()
    ctx.arc(pos.x, pos.y, currentRadius, 0, Math.PI * 2)
    ctx.fillStyle = masteryColor
    ctx.fill()
    
    // Inner highlight
    ctx.beginPath()
    ctx.arc(pos.x - currentRadius * 0.3, pos.y - currentRadius * 0.3, currentRadius * 0.3, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
    ctx.fill()
    
    // Skill name (for larger nodes)
    if (currentRadius > 25 || isHovered) {
      ctx.font = `${isHovered ? '12' : '10'}px Inter, sans-serif`
      ctx.fillStyle = '#f0f6fc'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      
      // Background for text
      const textWidth = ctx.measureText(pos.skill.name).width
      ctx.fillStyle = 'rgba(13, 17, 23, 0.8)'
      ctx.fillRect(
        pos.x - textWidth / 2 - 4,
        pos.y + currentRadius + 8,
        textWidth + 8,
        16
      )
      
      ctx.fillStyle = '#f0f6fc'
      ctx.fillText(pos.skill.name, pos.x, pos.y + currentRadius + 16)
    }
  })
  
  time++
  animationFrameId = requestAnimationFrame(draw)
}

// Get color based on mastery level
const getMasteryColor = (mastery: number): string => {
  if (mastery >= 80) return 'rgb(63, 185, 80)' // Green
  if (mastery >= 60) return 'rgb(0, 217, 255)' // Cyan
  if (mastery >= 40) return 'rgb(210, 153, 34)' // Yellow
  return 'rgb(139, 148, 158)' // Gray
}

// Handle mouse move for hover detection
const handleMouseMove = (event: MouseEvent) => {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  // Check if hovering over a skill node
  let found: SkillNode | null = null
  for (const pos of skillPositions.value) {
    const distance = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2)
    if (distance <= pos.radius + 10) {
      found = pos.skill
      tooltipPosition.value = { x: event.clientX - rect.left + 15, y: event.clientY - rect.top - 10 }
      break
    }
  }
  
  hoveredSkill.value = found
}

const handleMouseLeave = () => {
  hoveredSkill.value = null
}

// Resize handler
const handleResize = () => {
  if (containerRef.value) {
    canvasWidth.value = containerRef.value.clientWidth
    canvasHeight.value = containerRef.value.clientHeight
    skillPositions.value = calculatePositions()
  }
}

// Lifecycle
onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  skillPositions.value = calculatePositions()
  draw()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId)
  }
})

// Watch for skill changes
watch(() => props.skills, () => {
  skillPositions.value = calculatePositions()
}, { deep: true })
</script>

<style scoped>
.skill-constellation {
  width: 100%;
  height: 100%;
  min-height: 250px;
  position: relative;
  background: radial-gradient(ellipse at center, rgba(0, 217, 255, 0.03) 0%, transparent 70%);
}

canvas {
  display: block;
}

.skill-tooltip {
  position: absolute;
  background: var(--copilot-bg-elevated);
  border: 1px solid var(--copilot-border-accent);
  border-radius: var(--copilot-radius-md);
  padding: 12px;
  pointer-events: none;
  z-index: 100;
  min-width: 150px;
  box-shadow: var(--copilot-shadow-lg);
  animation: tooltip-appear 0.15s ease;
}

@keyframes tooltip-appear {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.tooltip-name {
  font-weight: 600;
  color: var(--copilot-text-primary);
}

.tooltip-category {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-tertiary);
  background: var(--copilot-bg-tertiary);
  padding: 2px 6px;
  border-radius: var(--copilot-radius-sm);
}

.tooltip-mastery {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mastery-label {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-tertiary);
}

.mastery-bar {
  flex: 1;
  height: 4px;
  background: var(--copilot-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.mastery-fill {
  height: 100%;
  background: var(--copilot-gradient-progress);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.mastery-value {
  font-size: var(--copilot-font-size-xs);
  font-weight: 600;
  color: var(--copilot-accent-cyan);
  min-width: 32px;
  text-align: right;
}
</style>

