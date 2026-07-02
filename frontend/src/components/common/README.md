# TextExplainer 文本解释组件使用说明

## 功能描述

TextExplainer 组件实现了"帮我讲讲这段"功能，允许用户选中任意文本后通过右键菜单获得通俗易懂的解释。

## 主要特性

- 🎯 **智能文本选择**: 自动检测用户选中的文本
- 📝 **上下文菜单**: 选中文本后显示操作菜单（复制、高亮、解释）
- 🤖 **AI驱动解释**: 调用后端API生成通俗易懂的文本解释
- 📊 **多难度级别**: 支持初学者、中等、高级三种解释难度
- 💡 **结构化展示**: 包含核心解释、关键要点、实例说明
- 🎨 **文本高亮**: 支持对选中文本进行高亮标记

## 使用方法

### 1. 在页面中引入组件

```vue
<template>
  <div class="page-content">
    <!-- 你的页面内容 -->
    <div class="text-content">
      <p>这里是一些复杂的技术文本，用户可以选中任意部分获得解释。</p>
    </div>
    
    <!-- 引入文本解释组件 -->
    <TextExplainer />
  </div>
</template>

<script>
import TextExplainer from '@/components/common/TextExplainer.vue'

export default {
  components: {
    TextExplainer
  }
}
</script>
```

### 2. 用户操作流程

1. **选中文本**: 用鼠标选中页面中任意文本
2. **打开菜单**: 选中后会自动显示上下文菜单
3. **选择操作**: 
   - 点击"复制"复制选中文本
   - 点击"高亮"对文本进行高亮标记
   - 点击"帮我讲讲这段"获得AI解释
4. **查看解释**: 在弹出的模态窗口中查看详细解释
5. **调整难度**: 可以切换不同的解释难度级别
6. **复制解释**: 可以复制完整的解释内容

## API 端点

组件依赖以下后端API端点：

### POST /api/v1/text-explain/explain

**请求参数:**
```json
{
  "text": "要解释的文本内容",
  "level": "beginner|intermediate|advanced",
  "context": "可选的上下文信息"
}
```

**响应格式:**
```json
{
  "code": "0000",
  "message": "文本解释生成成功",
  "data": {
    "original_text": "原文内容",
    "explanation": "核心解释内容",
    "key_points": ["关键要点1", "关键要点2"],
    "examples": ["实例1", "实例2"]
  }
}
```

## 自定义样式

组件提供了完整的CSS样式，你可以通过以下方式进行自定义：

```css
/* 自定义上下文菜单样式 */
.context-menu {
  /* 你的自定义样式 */
}

/* 自定义高亮文本样式 */
.highlighted-text {
  background-color: #your-color !important;
}

/* 自定义弹窗样式 */
.explanation-modal {
  /* 你的自定义样式 */
}
```

## 配置选项

目前组件使用默认配置，未来可以扩展以下配置选项：

- `maxTextLength`: 最大可解释文本长度
- `menuTheme`: 菜单主题样式
- `highlightColor`: 高亮颜色
- `enableKeyboard`: 是否启用键盘快捷键

## 注意事项

1. **依赖项**: 组件依赖 Vue 3 Composition API
2. **API要求**: 需要后端提供文本解释API支持
3. **浏览器兼容**: 使用了现代浏览器API（如 Clipboard API）
4. **权限**: 复制功能需要用户允许clipboard访问权限

## 扩展功能

可以考虑的未来扩展功能：

- 🔍 **历史记录**: 保存用户的解释历史
- 🌐 **多语言支持**: 支持不同语言的文本解释
- 🎯 **领域专业化**: 针对不同领域提供专业解释
- 📚 **知识图谱**: 关联相关概念和知识点
- 🗣️ **语音播放**: 支持解释内容的语音朗读

## 技术实现

- **前端**: Vue 3 + Composition API
- **后端**: FastAPI + Python
- **AI集成**: 可接入 OpenAI、Claude 等 AI 服务
- **样式**: 原生CSS，支持主题定制