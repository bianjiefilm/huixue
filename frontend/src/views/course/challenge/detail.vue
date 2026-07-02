<template>
  <div class="challenge-detail-page">
    <!-- 内容区域 -->
    <a-spin :spinning="loading" tip="加载中...">
      <template v-if="challengeInfo">
        <div class="challenge-container">
          <!-- 左侧任务手册区 -->
          <div class="task-manual-area">
            <div class="task-manual-header">
              <div class="task-navigation">
                <a-button 
                  type="text" 
                  @click="navigateToPrevTask"
                  :disabled="!hasPrevTask"
                >
                  <template #icon><ArrowLeftOutlined /></template>
                  上一关
                </a-button>
                <span class="task-title">
                  {{ challengeInfo.title }}
                  <!-- 通关状态标签 -->
                  <a-tag 
                    v-if="taskStatus === 'completed' || evaluationState.status === 'pass'" 
                    color="success" 
                    style="margin-left: 8px;"
                  >
                    ✅ 已通关
                  </a-tag>
                  <a-tag 
                    v-else-if="evaluationState.submitted && evaluationState.status === 'fail'" 
                    color="warning"
                    style="margin-left: 8px;"
                  >
                    ⏳ 未通关
                  </a-tag>
                </span>
                <a-button 
                  type="text" 
                  @click="navigateToNextTask"
                  :disabled="!hasNextTask"
                  :type="hasNextTask ? 'primary' : 'default'"
                >
                  下一关
                  <template #icon><ArrowRightOutlined /></template>
                </a-button>
              </div>
            </div>
            
            <a-tabs v-model:activeKey="activeTaskTab" class="task-tabs" size="large" @change="handleTabChange">
              <a-tab-pane key="task">
                <template #tab>
                  <span class="tab-title">
                    <BookOutlined style="margin-right: 6px;" />
                    过关任务
                  </span>
                </template>
                <div class="task-content-wrapper">
                  <!-- 任务信息头部 -->
                  <div class="task-header">
                    <div class="task-meta">
                      <a-tag color="blue" v-if="challengeInfo.difficulty">
                        {{ challengeInfo.difficulty === 'easy' ? '初级' : challengeInfo.difficulty === 'medium' ? '中级' : '高级' }}
                      </a-tag>
                      <a-tag color="gold" v-if="challengeInfo.coin">
                        <TrophyOutlined /> {{ challengeInfo.coin }} 金币
                      </a-tag>
                      <a-tag v-for="skill in (challengeInfo.skills || []).slice(0, 3)" :key="skill" color="cyan">
                        {{ skill }}
                      </a-tag>
                    </div>
                  </div>
                  
                  <!-- 输入输出格式提示 -->
                  <div class="task-tips" v-if="challengeInfo.envType === 'code'">
                    <a-alert type="info" show-icon class="tips-alert">
                      <template #icon><BulbOutlined style="color: #1890ff;" /></template>
                      <template #message>
                        <span style="font-weight: 600; color: #1890ff;">📋 编程要求</span>
                      </template>
                      <template #description>
                        <div class="tips-content">
                          <p style="margin-bottom: 8px; color: #666;">{{ envTypeDescription.title }}</p>
                          <ul class="tips-list">
                            <li v-for="requirement in envTypeDescription.requirements" :key="requirement">
                              <CheckCircleOutlined style="color: #52c41a; margin-right: 6px;" />
                              {{ requirement }}
                            </li>
                          </ul>
                          <a-button type="link" size="small" @click="showTestCaseExamples" class="view-example-btn">
                            <EyeOutlined /> 查看输入输出示例
                          </a-button>
                        </div>
                      </template>
                    </a-alert>
                  </div>
                  
                  <!-- 任务描述内容 -->
                  <div class="task-description markdown-body">
                    <div v-html="renderedTaskContent"></div>
                  </div>
                </div>
              </a-tab-pane>
              
              <a-tab-pane key="answer" :disabled="!canViewAnswer">
                <template #tab>
                  <span class="tab-title">
                    <CodeOutlined style="margin-right: 6px;" />
                    参考答案
                    <LockOutlined v-if="!canViewAnswer" style="margin-left: 6px; color: #999; font-size: 12px;" />
                    <UnlockOutlined v-else-if="isTaskCompleted || evaluationState.status === 'pass'" style="margin-left: 6px; color: #52c41a; font-size: 12px;" />
                  </span>
                </template>
                <div class="reference-answer-wrapper">
                  <!-- 参考答案头部 -->
                  <div class="answer-header">
                    <div class="answer-title">
                      <CodeOutlined style="margin-right: 8px; color: #1890ff;" />
                      <span>标准答案</span>
                    </div>
                    <div class="answer-actions">
                      <a-button size="small" type="text" @click="copyReferenceAnswer">
                        <CopyOutlined /> 复制代码
                      </a-button>
                    </div>
                  </div>
                  
                  <!-- 代码区域 -->
                  <div class="answer-code-container">
                    <div class="code-language-tag">Python</div>
                    <pre class="answer-code"><code class="language-python">{{ challengeInfo.referenceAnswer }}</code></pre>
                  </div>
                  
                  <!-- 解题思路（如果有） -->
                  <div class="answer-explanation" v-if="challengeInfo.referenceAnswer && challengeInfo.referenceAnswer.includes('解题思路')">
                    <div class="explanation-title">
                      <BulbOutlined style="margin-right: 8px; color: #faad14;" />
                      <span>解题思路</span>
                    </div>
                    <div class="explanation-content">
                      <p>理解题目要求，按步骤实现功能。</p>
                    </div>
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>
          </div>
          
          <!-- 右侧实验环境区 -->
          <div class="practice-environment-area">
            <!-- 判断题区域 -->
            <div v-if="challengeInfo.taskType === 'TRUE_FALSE'" class="question-area">
              <h3>判断题</h3>
              <div class="question-content">
                <p>{{ challengeInfo.question }}</p>
              </div>
              <a-radio-group v-model:value="judgmentAnswer">
                <a-radio :value="true">正确</a-radio>
                <a-radio :value="false">错误</a-radio>
              </a-radio-group>
              <a-button
                type="primary"
                @click="submitJudgment"
                style="margin-top: 16px;"
                :disabled="judgmentAnswer === null"
              >
                提交答案
              </a-button>
            </div>

            <!-- 选择题区域（支持多题目：单选+多选） -->
            <div v-else-if="challengeInfo.taskType === 'SINGLE_CHOICE' || challengeInfo.taskType === 'MULTIPLE_CHOICE'" class="question-area">
              <h3>选择题</h3>
              
              <!-- 多题目模式 -->
              <div v-if="challengeInfo.questions && challengeInfo.questions.length > 0">
                <div 
                  v-for="(q, qIndex) in challengeInfo.questions" 
                  :key="q.id || qIndex" 
                  class="question-item" 
                  :style="[{ marginBottom: '24px', padding: '16px', borderRadius: '8px', transition: 'all 0.3s' }, getQuestionBorderStyle(qIndex)]"
                >
                  <div class="question-header" style="display: flex; align-items: center; margin-bottom: 12px;">
                    <span style="font-weight: bold; color: #1890ff; margin-right: 8px;">题目{{ qIndex + 1 }}</span>
                    <a-tag :color="q.type === 'single' ? 'blue' : 'green'">{{ q.type === 'single' ? '单选' : '多选' }}</a-tag>
                    <!-- 评测后显示对错标记 -->
                    <span v-if="getQuestionResult(qIndex)" style="margin-left: 8px; font-size: 16px;">
                      <span v-if="getQuestionResult(qIndex)?.correct" style="color: #52c41a;">✅ 正确</span>
                      <span v-else style="color: #ff4d4f;">❌ 错误</span>
                    </span>
                  </div>
                  <div class="question-content" style="margin-bottom: 12px;">
                    <p style="font-size: 14px; color: #333;">{{ q.question }}</p>
                  </div>
                  
                  <!-- 单选题选项 -->
                  <a-radio-group 
                    v-if="q.type === 'single'" 
                    v-model:value="multiChoiceAnswers[qIndex]"
                    style="display: block;"
                    :disabled="evaluationState.submitted && evaluationState.status === 'pass'"
                  >
                    <a-radio
                      v-for="(option, optIndex) in q.options"
                      :key="optIndex"
                      :value="optIndex"
                      style="display: block; margin-bottom: 8px"
                      :class="getOptionClass(qIndex, optIndex, 'single')"
                    >
                      {{ String.fromCharCode(65 + optIndex) }}. {{ option }}
                      <!-- 正确答案标记 -->
                      <span v-if="showCorrectMark(qIndex, optIndex)" style="color: #52c41a; margin-left: 8px;">← 正确答案</span>
                    </a-radio>
                  </a-radio-group>
                  
                  <!-- 多选题选项 -->
                  <a-checkbox-group 
                    v-else 
                    v-model:value="multiChoiceAnswers[qIndex]"
                    style="display: block;"
                    :disabled="evaluationState.submitted && evaluationState.status === 'pass'"
                  >
                    <a-checkbox
                      v-for="(option, optIndex) in q.options"
                      :key="optIndex"
                      :value="optIndex"
                      style="display: block; margin-bottom: 8px"
                      :class="getOptionClass(qIndex, optIndex, 'multiple')"
                    >
                      {{ String.fromCharCode(65 + optIndex) }}. {{ option }}
                      <!-- 正确答案标记 -->
                      <span v-if="showCorrectMark(qIndex, optIndex)" style="color: #52c41a; margin-left: 8px;">← 正确答案</span>
                    </a-checkbox>
                  </a-checkbox-group>
                  
                  <!-- 错误时显示解析 -->
                  <div 
                    v-if="getQuestionResult(qIndex) && !getQuestionResult(qIndex)?.correct && getQuestionResult(qIndex)?.explanation"
                    style="margin-top: 12px; padding: 12px; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px;"
                  >
                    <strong style="color: #d48806;">💡 解析：</strong>
                    <span>{{ getQuestionResult(qIndex)?.explanation }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 单题目模式（兼容旧数据） -->
              <div v-else>
                <div class="question-content">
                  <p>{{ challengeInfo.question }}</p>
                </div>
                <a-radio-group v-model:value="choiceAnswer">
                  <a-radio
                    v-for="(option, index) in challengeInfo.options"
                    :key="index"
                    :value="index"
                    style="display: block; margin-bottom: 8px"
                  >
                    {{ String.fromCharCode(65 + index) }}. {{ option }}
                  </a-radio>
                </a-radio-group>
              </div>
              
              <!-- 评测结果面板 -->
              <div 
                v-if="evaluationState.submitted" 
                class="evaluation-result-panel"
                :style="{
                  marginTop: '20px',
                  padding: '16px',
                  borderRadius: '8px',
                  border: evaluationState.status === 'pass' ? '2px solid #52c41a' : '2px solid #ff4d4f',
                  background: evaluationState.status === 'pass' ? '#f6ffed' : '#fff2f0'
                }"
              >
                <div style="display: flex; align-items: center; margin-bottom: 12px;">
                  <span style="font-size: 20px; margin-right: 8px;">
                    {{ evaluationState.status === 'pass' ? '🎉' : '❌' }}
                  </span>
                  <span style="font-size: 16px; font-weight: bold;">
                    {{ evaluationState.status === 'pass' ? '恭喜通关！' : '评测未通过' }}
                  </span>
                  <a-tag 
                    :color="evaluationState.status === 'pass' ? 'success' : 'error'" 
                    style="margin-left: 12px;"
                  >
                    得分：{{ evaluationState.total_tests > 0 ? Math.round(evaluationState.passed_tests / evaluationState.total_tests * 100) : evaluationState.score }}/100
                  </a-tag>
                </div>
                
                <div style="display: flex; gap: 16px; margin-bottom: 12px; align-items: center;">
                  <span>正确题数：{{ evaluationState.passed_tests }}/{{ evaluationState.total_tests }}</span>
                  <span 
                    v-if="evaluationState.status === 'pass' && challengeInfo.coin" 
                    class="coin-reward"
                    style="display: inline-flex; align-items: center; padding: 4px 12px; background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%); border-radius: 16px; color: #5c4800; font-weight: bold; box-shadow: 0 2px 4px rgba(255,183,0,0.3);"
                  >
                    <span style="font-size: 18px; margin-right: 4px;">🪙</span>
                    +{{ challengeInfo.coin }} 金币
                  </span>
                </div>
                
                <div v-if="evaluationState.status !== 'pass'" style="color: #ff4d4f;">
                  {{ evaluationState.error_message }}
                </div>
                
                <!-- 重新作答按钮 -->
                <a-button 
                  v-if="evaluationState.status !== 'pass'"
                  type="primary" 
                  @click="resetChoiceEvaluation"
                  style="margin-top: 12px;"
                >
                  重新作答
                </a-button>
              </div>
              
              <!-- 提交按钮 -->
              <a-button
                v-if="!evaluationState.submitted || evaluationState.status !== 'pass'"
                type="primary"
                @click="submitChoice"
                style="margin-top: 16px;"
                :disabled="!isChoiceAnswerComplete"
              >
                {{ evaluationState.submitted ? '重新提交' : '提交答案' }}
              </a-button>
            </div>

            <!-- 代码编辑器区域 - 当环境类型不是shell和desktop时显示 -->
            <div class="editor-container" v-else-if="challengeInfo.envType !== 'shell' && challengeInfo.envType !== 'desktop'">
              <div class="editor-toolbar">
                <span class="file-name">{{ activeFile?.name }}</span>
                <div class="editor-actions">
                  <!-- 运行按钮，用于代码环境 -->
                  <a-button
                    v-if="challengeInfo.envType === 'code' || challengeInfo.envType === 'html'"
                    type="default"
                    size="small"
                    @click="toggleTestCases"
                  >
                    <template #icon><PlayCircleOutlined /></template>
                    查看测试用例
                  </a-button>
                  <!-- 提交评测按钮 [DT-03修复: 添加disabled防止重复点击] -->
                  <a-button 
                    v-if="challengeInfo.envType === 'code' || challengeInfo.envType === 'html'"
                    type="primary" 
                    size="small" 
                    :loading="evaluating"
                    :disabled="evaluating"
                    @click="evaluate"
                    style="margin-left: 8px;"
                  >
                    <template #icon><CheckCircleOutlined /></template>
                    {{ evaluating ? '评测中...' : '提交评测' }}
                  </a-button>
                  <!-- 只有需要外部环境时才显示启动按钮 -->
                  <a-button 
                    v-else-if="challengeInfo.envType !== 'shell' && challengeInfo.envType !== 'desktop'"
                    type="primary" 
                    size="small" 
                    :loading="environmentControl.isProcessing"
                    @click="startEnvironment"
                  >
                    {{ environmentControl.isProcessing ? '启动中...' : '启动环境' }}
                  </a-button>
                  <a-dropdown>
                    <a-button type="text" size="small">
                      <template #icon><FontSizeOutlined /></template>
                      字号选择
                    </a-button>
                    <template #overlay>
                      <a-menu @click="handleFontSizeChange">
                        <a-menu-item key="12">12px</a-menu-item>
                        <a-menu-item key="14">14px</a-menu-item>
                        <a-menu-item key="16">16px</a-menu-item>
                        <a-menu-item key="18">18px</a-menu-item>
                        <a-menu-item key="20">20px</a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                  <a-button v-if="canShowPreview" type="text" size="small" @click="togglePreview">
                    <template #icon><EyeOutlined /></template>
                    {{ showPreview ? '隐藏预览' : '页面预览' }}
                  </a-button>
                  <!-- 设备模拟选择 -->
                  <a-select 
                    v-if="showPreview" 
                    v-model:value="previewDevice" 
                    size="small"
                    style="width: 90px; margin-left: 8px;"
                  >
                    <a-select-option value="desktop">🖥️ 桌面</a-select-option>
                    <a-select-option value="tablet">📱 平板</a-select-option>
                    <a-select-option value="mobile">📲 手机</a-select-option>
                  </a-select>
                  <a-button type="text" size="small" @click="resetAllCode">
                    <template #icon><ReloadOutlined /></template>
                    重置全部代码
                  </a-button>
                  <a-button type="text" size="small" @click="resetCurrentFile">
                    <template #icon><UndoOutlined /></template>
                    重置本页代码
                  </a-button>
                  <a-button
                    v-if="isTaskCompleted"
                    type="text"
                    size="small"
                    @click="returnToPassedCode"
                  >
                    <template #icon><RollbackOutlined /></template>
                    返回通关时代码
                  </a-button>
                  <!-- 自动保存状态 -->
                  <span class="auto-save-status" :class="autoSaveStatus">
                    <template v-if="autoSaveStatus === 'saved'">
                      <CheckCircleOutlined style="color: #52c41a;" />
                      <span style="margin-left: 4px; color: #52c41a;">已保存 {{ lastSavedTime }}</span>
                    </template>
                    <template v-else-if="autoSaveStatus === 'saving'">
                      <LoadingOutlined style="color: #1890ff;" />
                      <span style="margin-left: 4px; color: #1890ff;">保存中...</span>
                    </template>
                    <template v-else>
                      <ExclamationCircleOutlined style="color: #faad14;" />
                      <span style="margin-left: 4px; color: #faad14;">未保存</span>
                    </template>
                  </span>
                  <a-button type="text" size="small" @click="autoSaveCode" title="立即保存 (Ctrl+S)">
                    <template #icon><SaveOutlined /></template>
                  </a-button>
                  <!-- 帮助按钮 -->
                  <a-tooltip placement="bottom">
                    <template #title>
                      <div style="font-size: 12px;">
                        <div><strong>快捷键</strong></div>
                        <div>Ctrl+Enter: 评测</div>
                        <div>Ctrl+S: 保存</div>
                        <div v-if="canShowPreview">Ctrl+P: 预览</div>
                      </div>
                    </template>
                    <a-button type="text" size="small" @click="showHelpDialog">
                      <template #icon><QuestionCircleOutlined /></template>
                    </a-button>
                  </a-tooltip>
                </div>
              </div>
              
              <div class="editor-main">
                <div class="file-explorer-section">
                  <file-explorer
                    :files="fileTreeData"
                    :default-selected-key="activeFileId"
                    @select="handleFileSelect"
                  />
                </div>
                <div class="monaco-editor-section">
                  <div class="monaco-editor-container">
                    <!-- 编辑器加载状态 -->
                    <div v-if="!editorReady && activeFile" class="editor-loading">
                      <a-spin tip="编辑器加载中..." size="large" />
                    </div>
                    <!-- 编辑器错误提示 -->
                    <div v-if="editorError" class="editor-error">
                      <a-alert
                        message="编辑器加载失败"
                        :description="editorError"
                        type="error"
                        show-icon
                        closable
                        @close="editorError = ''"
                      />
                    </div>
                    <!-- Monaco编辑器 -->
                    <monaco-editor
                      v-if="activeFile"
                      ref="monacoEditor"
                      v-model:value="activeFile.content"
                      :language="activeFile.language || 'python'"
                      :read-only="activeFile.readOnly || false"
                      :options="editorOptions"
                      @mounted="handleEditorMounted"
                      @error="handleEditorError"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- 命令行终端区域 - 当环境类型是shell时显示 -->
            <div class="terminal-container" v-if="challengeInfo.envType === 'shell'">
              <div class="editor-toolbar">
                <span class="file-name">命令行终端</span>
                <div class="editor-actions">
                  <a-button
                    type="primary"
                    size="small"
                    :loading="environmentControl.isLaunching.value || environmentControl.isStopping.value || environmentControl.isSwitching.value"
                    @click="startEnvironment"
                  >
                    {{ (environmentControl.isLaunching.value || environmentControl.isStopping.value || environmentControl.isSwitching.value) ? '启动中...' : '启动环境' }}
                  </a-button>
                  <a-button type="text" size="small" @click="resetTerminal">
                    <template #icon><ReloadOutlined /></template>
                    重置命令行
                  </a-button>
                </div>
              </div>
              
              <div class="terminal-area">
                <terminal-emulator
                  ref="terminalRef"
                  :initial-output="terminalInitOutput"
                  :prompt="terminalPrompt"
                  @execute="handleCommandExecution"
                  @reset="handleTerminalReset"
                />
              </div>
            </div>
            
            <!-- 云桌面环境区域 - 当环境类型是desktop时显示 -->
            <div class="cloud-desktop-container" v-if="challengeInfo.envType === 'desktop'">
              <div class="editor-toolbar">
                <span class="file-name">云桌面环境</span>
                <div class="editor-actions">
                  <a-button type="text" size="small" @click="extendDesktopTime" :disabled="!canExtendTime">
                    <template #icon><ClockCircleOutlined /></template>
                    延时 ({{ desktopRemainingTime }}分)
                  </a-button>
                  <a-button type="text" size="small" @click="openClipboard">
                    <template #icon><CopyOutlined /></template>
                    剪切板
                  </a-button>
                  <a-button type="text" size="small" @click="toggleFullscreen">
                    <template #icon>
                      <FullscreenOutlined v-if="!isFullscreen" />
                      <FullscreenExitOutlined v-else />
                    </template>
                    {{ isFullscreen ? '退出全屏' : '全屏' }}
                  </a-button>
                  <a-button type="text" size="small" @click="resetEnvironment">
                    <template #icon><ReloadOutlined /></template>
                    重置环境
                  </a-button>
                  <a-button type="text" size="small" @click="resetTask">
                    <template #icon><UndoOutlined /></template>
                    重置任务
                  </a-button>
                </div>
              </div>
              
              <div class="desktop-area">
                <!-- 未启动时显示占位符 -->
                <div class="desktop-placeholder" v-if="!desktopEnvironmentUrl">
                  <a-result
                    status="info"
                    title="云桌面环境"
                    sub-title="点击启动按钮开始您的实验环境"
                  >
                    <template #extra>
                      <a-button 
                        type="primary" 
                        size="large"
                        :loading="desktopLaunching"
                        @click="startDesktopEnvironment"
                      >
                        {{ desktopLaunching ? '正在启动...' : '启动环境' }}
                      </a-button>
                    </template>
                  </a-result>
                </div>
                <!-- 已启动时显示云桌面环境 (noVNC) -->
                <div v-else class="vdi-container">
                  <iframe 
                    ref="vdiIframeRef"
                    :src="desktopEnvironmentUrl"
                    class="vdi-iframe"
                    allow="clipboard-read; clipboard-write"
                    @load="handleVdiLoaded"
                  />
                </div>
              </div>
            </div>
            
            <!-- 评测区 -->
            <div class="evaluation-area" v-if="challengeInfo.envType !== 'shell' && challengeInfo.envType !== 'desktop'">
              <div class="evaluation-header">
                <div class="test-cases-toggle">
                  <a-button 
                    type="text" 
                    @click="toggleTestCases"
                    :class="{ 'expanded': showTestCases }"
                  >
                    <template #icon>
                      <DownOutlined v-if="!showTestCases" />
                      <UpOutlined v-else />
                    </template>
                    {{ showTestCases ? '收起测试集' : '展开测试集' }}
                  </a-button>
                  <a-button 
                    type="text" 
                    @click="showTestCaseExamples"
                    style="margin-left: 8px;"
                  >
                    <template #icon><EyeOutlined /></template>
                    查看示例
                  </a-button>
                </div>
                <div class="evaluation-actions">
                  <!-- [DT-03修复: 添加disabled防止重复点击] -->
                  <a-button 
                    type="primary" 
                    :loading="evaluating"
                    :disabled="evaluating"
                    @click="handleEvaluate"
                  >
                    {{ evaluating ? '评测中...' : '评 测' }}
                  </a-button>
                </div>
              </div>
              
              <div class="test-cases" v-if="showTestCases">
                <a-collapse v-model:activeKey="activeTestCases">
                  <a-collapse-panel 
                    v-for="testCase in visibleTestCases" 
                    :key="testCase.id" 
                    :header="testCase.title"
                  >
                    <div class="test-case-content">
                      <div class="test-input">
                        <div class="test-title">预期输入：</div>
                        <pre>{{ testCase.input }}</pre>
                      </div>
                      <div class="test-output">
                        <div class="test-title">预期输出：</div>
                        <pre>{{ testCase.expectedOutput }}</pre>
                      </div>
                    </div>
                  </a-collapse-panel>
                  <div class="hidden-test-cases" v-if="hiddenTestCases.length > 0">
                    <a-alert
                      type="info"
                      show-icon
                      message="隐藏测试集"
                      description="该题目包含隐藏测试集，评测时将同时验证这些测试集是否通过。"
                    />
                  </div>
                </a-collapse>
              </div>
              
              <div class="evaluation-results" v-if="evaluationResults.length > 0">
                <a-divider>评测结果</a-divider>
                <a-tabs>
                  <a-tab-pane key="overall" tab="总体结果">
                    <a-result
                      :status="evaluationAllPassed ? 'success' : 'error'"
                      :title="evaluationAllPassed ? '🎉 评测通过！' : '❌ 评测未通过'"
                      :sub-title="evaluationAllPassed 
                        ? '恭喜你通过了所有测试用例!' 
                        : `通过 ${evaluationState.passed_tests || evaluationResults.filter(r => r.passed).length}/${evaluationState.total_tests || evaluationResults.length} 个测试用例`"
                    >
                      <template #extra>
                        <a-space direction="vertical" align="center">
                          <!-- 统计信息 -->
                          <div class="evaluation-stats" style="margin-bottom: 16px;">
                            <a-row :gutter="16">
                              <a-col :span="8">
                                <a-statistic 
                                  title="通过用例" 
                                  :value="evaluationState.passed_tests || evaluationResults.filter(r => r.passed).length"
                                  :value-style="{ color: '#52c41a' }"
                                />
                              </a-col>
                              <a-col :span="8">
                                <a-statistic 
                                  title="失败用例" 
                                  :value="(evaluationState.total_tests || evaluationResults.length) - (evaluationState.passed_tests || evaluationResults.filter(r => r.passed).length)"
                                  :value-style="{ color: '#ff4d4f' }"
                                />
                              </a-col>
                              <a-col :span="8">
                                <a-statistic 
                                  title="得分" 
                                  :value="evaluationState.score || Math.round((evaluationResults.filter(r => r.passed).length / evaluationResults.length) * 100)"
                                  suffix="分"
                                />
                              </a-col>
                            </a-row>
                          </div>
                          <!-- [DT-03修复: 添加disabled防止重复点击] -->
                          <a-button type="primary" @click="evaluate" :loading="evaluating" :disabled="evaluating">
                            {{ evaluating ? '评测中...' : '重新评测' }}
                          </a-button>
                        </a-space>
                      </template>
                    </a-result>
                  </a-tab-pane>
                  <a-tab-pane key="detail" tab="详细结果">
                    <div class="result-details">
                      <a-list
                        :data-source="evaluationResults"
                        :bordered="false"
                        :split="true"
                      >
                        <template #renderItem="{ item, index }">
                          <a-list-item>
                            <a-card 
                              :bordered="true" 
                              :class="{ 
                                'result-card': true,
                                'passed': item.passed, 
                                'failed': !item.passed,
                                'hidden': item.hidden
                              }"
                              :style="{ 
                                width: '100%',
                                borderLeft: item.passed ? '4px solid #52c41a' : '4px solid #ff4d4f',
                                marginBottom: '12px'
                              }"
                            >
                              <template #title>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                  <span style="font-size: 18px;">{{ item.passed ? '✅' : '❌' }}</span>
                                  <span>{{ item.title || `测试用例 ${index + 1}` }}</span>
                                </div>
                              </template>
                              <template #extra>
                                <a-tag :color="item.passed ? 'success' : 'error'" style="font-size: 14px; padding: 4px 12px;">
                                  {{ item.passed ? '通过' : '未通过' }}
                                </a-tag>
                              </template>
                              
                              <!-- 错误原因（最重要的信息，优先显示） -->
                              <div v-if="item.error && !item.passed && !item.hidden" class="result-error" style="margin-bottom: 16px;">
                                <a-alert
                                  :message="'错误原因：' + item.error"
                                  type="error"
                                  show-icon
                                  style="font-weight: 500;"
                                />
                              </div>
                              
                              <!-- 输出对比 -->
                              <div class="result-comparison" v-if="!item.hidden && (item.actualOutput || item.expectedOutput)">
                                <a-row :gutter="16">
                                  <a-col :span="12" v-if="item.expectedOutput">
                                    <div class="result-section">
                                      <div class="result-title" style="color: #52c41a; font-weight: 600;">📥 预期输出：</div>
                                      <pre style="background: #f6ffed; border: 1px solid #b7eb8f; padding: 12px; border-radius: 4px; max-height: 200px; overflow: auto;">{{ item.expectedOutput || '(无)' }}</pre>
                                    </div>
                                  </a-col>
                                  <a-col :span="12" v-if="item.actualOutput && item.actualOutput !== '通过' && item.actualOutput !== '未通过'">
                                    <div class="result-section">
                                      <div class="result-title" style="color: #ff4d4f; font-weight: 600;">📤 实际输出：</div>
                                      <pre style="background: #fff2f0; border: 1px solid #ffa39e; padding: 12px; border-radius: 4px; max-height: 200px; overflow: auto;">{{ item.actualOutput || '(无输出)' }}</pre>
                                    </div>
                                  </a-col>
                                </a-row>
                              </div>
                              
                              <!-- 隐藏测试用例 -->
                              <div v-if="item.hidden" class="hidden-result">
                                <a-alert
                                  type="info"
                                  show-icon
                                  :message="item.passed ? '🔒 隐藏测试用例已通过' : '🔒 隐藏测试用例未通过'"
                                  description="该测试用例的详细内容对学生不可见"
                                />
                              </div>
                            </a-card>
                          </a-list-item>
                        </template>
                      </a-list>
                    </div>
                  </a-tab-pane>
                </a-tabs>
              </div>
            </div>
          </div>
        </div>
      </template>
      <template v-else-if="!loading">
        <a-result
          status="404"
          title="未找到任务"
          sub-title="您请求的挑战任务不存在或已被删除"
        >
          <template #extra>
            <a-button type="primary" @click="goBack">
              返回
            </a-button>
          </template>
        </a-result>
      </template>
    </a-spin>

    <!-- 页面预览窗口 -->
    <preview-window
      v-if="canShowPreview"
      :is-visible="showPreview"
      :html-content="previewHtmlContent"
      :css-content="previewCssContent"
      :js-content="previewJsContent"
      :task-id="taskId"
      :device-width="deviceSizes[previewDevice].width"
      :device-label="deviceSizes[previewDevice].label"
      @close="showPreview = false"
      @update:is-visible="(val) => showPreview = val"
    />

    <!-- 剪切板工具弹窗 -->
    <a-modal
      v-model:open="clipboardVisible"
      title="剪切板工具"
      width="600px"
      :footer="null"
      @cancel="clipboardVisible = false"
    >
      <div class="clipboard-content">
        <p class="clipboard-description">
          在下方输入框中输入或粘贴文本，可以在本地和云桌面环境之间复制粘贴内容。
        </p>
        <a-textarea
          v-model:value="clipboardText"
          placeholder="输入或粘贴文本内容..."
          :rows="8"
          class="clipboard-textarea"
        />
        <div class="clipboard-actions">
          <a-button @click="pasteFromClipboard" :disabled="!isClipboardSupported">
            <template #icon><ImportOutlined /></template>
            从剪切板粘贴
          </a-button>
          <a-button type="primary" @click="copyToClipboard" :disabled="!clipboardText.trim() || !isClipboardSupported">
            <template #icon><CopyOutlined /></template>
            复制到剪切板
          </a-button>
        </div>
        <div v-if="!isClipboardSupported" class="clipboard-warning">
          <a-alert
            message="浏览器不支持剪切板API"
            description="请手动复制粘贴文本内容"
            type="warning"
            show-icon
          />
        </div>
      </div>
    </a-modal>

    <!-- 环境冲突提示弹窗 -->
    <EnvironmentConflictDialog
      :open="environmentControl.showConflictDialog.value"
      :active-environment="environmentControl.activeEnvironment.value"
      @update:open="(val) => environmentControl.showConflictDialog.value = val"
      @go-back="environmentControl.handleGoBackToActiveEnvironment"
      @switch-environment="environmentControl.handleSwitchToNewEnvironment"
    />
    
    <!-- 确认切换环境弹窗 -->
    <SwitchEnvironmentDialog
      :open="environmentControl.showSwitchDialog.value"
      :current-environment="environmentControl.activeEnvironment.value"
      :target-practice-name="environmentControl.pendingLaunch.value?.practiceName || ''"
      :target-environment-type="environmentControl.pendingLaunch.value?.environmentType || ''"
      :processing="environmentControl.isSwitching.value"
      @update:open="(val) => environmentControl.showSwitchDialog.value = val"
      @confirm="environmentControl.confirmSwitchEnvironment"
      @cancel="environmentControl.cancelSwitchEnvironment"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, shallowRef, h } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Divider, Typography, Tabs, Alert, Spin, Layout, Tree, Modal, message } from 'ant-design-vue';
import MonacoEditor from '../../../components/editor/MonacoEditor.vue';
import FileExplorer from '../../../components/editor/FileExplorer.vue';
import HtmlPreview from '../../../components/editor/HtmlPreview.vue';
import PreviewWindow from '../../../components/editor/PreviewWindow.vue';
import TerminalEmulator from '../../../components/editor/TerminalEmulator.vue';
import JupyterLite from '../../../components/JupyterLite.vue';
import {
  ArrowLeftOutlined,
  ArrowRightOutlined,
  FontSizeOutlined,
  ReloadOutlined,
  UndoOutlined,
  RollbackOutlined,
  DownOutlined,
  UpOutlined,
  EyeOutlined,
  CodeOutlined,
  ClockCircleOutlined,
  CopyOutlined,
  ImportOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  LockOutlined,
  UnlockOutlined,
  BookOutlined,
  BulbOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  SaveOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue';
import { 
  getChallenge, 
  evaluateCodeWithAllTestCases, 
  validateHtmlChallenge,
  getTaskDetail,
  getTaskTests,
  getTaskAnswer,
  saveCodeSnapshot,
  evaluateTask,
  getPracticeTasks
} from '../../../api/challenge';
import type { CodingChallenge, TestCase, CodeFile } from '../../../api/challenge';
// @ts-ignore
import showdown from 'showdown';
import { useUserStore } from '../../../stores/user';
import { getToken } from '@/utils/auth';
import EnvironmentConflictDialog from '../../../components/common/EnvironmentConflictDialog.vue';
import SwitchEnvironmentDialog from '../../../components/common/SwitchEnvironmentDialog.vue';
import { useEnvironmentControl } from '../../../composables/useEnvironmentControl';
import { processTaskReward, getUserCoinBalance } from '../../../utils/coinSystem';
import { useGlobalDataSyncStore } from '../../../stores/globalDataSync';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore(); // 使用用户store
const dataSyncStore = useGlobalDataSyncStore(); // 数据同步store
let courseId = route.params.courseId as string;
let classroomId = route.params.classroomId as string;
let taskId = route.params.taskId as string;

const requireCurrentUserId = () => {
  const userId = userStore.userId;
  if (!userId) {
    message.warning('请先登录后再访问挑战页面');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};

// 环境控制
const environmentControl = useEnvironmentControl();

// 状态变量
const loading = ref(true);
const desktopLaunching = ref(false);  // VDI启动状态
const evaluating = ref(false);
const running = ref(false);
const runOutput = ref('');
const showExampleDialog = ref(false);
const challengeInfo = ref<CodingChallenge | null>(null);
const activeTaskTab = ref('task');
const showTestCases = ref(false);
const activeTestCases = ref<string[]>([]);
const monacoEditor = shallowRef();
const showHtmlPreview = ref(false);
const htmlPreviewContent = ref('');
const showPreview = ref(false);
const previewHtmlContent = ref('');
const previewCssContent = ref('');
const previewJsContent = ref('');

// 预览设备模拟
const previewDevice = ref<'desktop' | 'tablet' | 'mobile'>('desktop');
const deviceSizes = {
  desktop: { width: '100%', label: '桌面' },
  tablet: { width: '768px', label: '平板' },
  mobile: { width: '375px', label: '手机' }
};

// 文件树和编辑器相关状态
const fileTreeData = ref<any[]>([]);
const activeFileId = ref('');
const activeFile = ref<CodeFile | null>(null);
const editorOptions = ref({
  fontSize: 14
});
const editorReady = ref(false);
const editorError = ref('');

// 文件原始内容，用于重置功能
const originalFileContents = ref<Record<string, string>>({});

// 任务状态跟踪
const taskStatus = ref<string>('not_started');

// 评测结果
const evaluationResults = ref<any[]>([]);
const evaluationAllPassed = ref(false);

// 判断题和选择题相关状态
const judgmentAnswer = ref<boolean | null>(null);
const choiceAnswer = ref<number | null>(null);
// 多题目选择题答案（每个元素是该题的答案：单选为number，多选为number[]）
const multiChoiceAnswers = ref<(number | number[] | null)[]>([]);

// 评测结果状态
interface QuestionResult {
  question_id: string;
  question_index: number;
  question_type: string;
  question_content: string;
  options: string[];
  user_answer: number | number[] | null;
  correct_answer: number | number[];
  explanation: string;
  correct: boolean;
}

interface EvaluationResult {
  status: 'pass' | 'fail' | null;
  score: number;
  total_tests: number;
  passed_tests: number;
  error_message: string;
  question_results: QuestionResult[];
  submitted: boolean;  // 是否已提交过
}

const evaluationState = ref<EvaluationResult>({
  status: null,
  score: 0,
  total_tests: 0,
  passed_tests: 0,
  error_message: '',
  question_results: [],
  submitted: false
});

const resetEvaluationState = () => {
  evaluationState.value = {
    status: null,
    score: 0,
    total_tests: 0,
    passed_tests: 0,
    error_message: '',
    question_results: [],
    submitted: false
  };
};

const resetChallengeStateForRoute = () => {
  loading.value = true;
  evaluating.value = false;
  running.value = false;
  runOutput.value = '';
  challengeInfo.value = null;
  activeTaskTab.value = 'task';
  showTestCases.value = false;
  activeTestCases.value = [];
  fileTreeData.value = [];
  activeFileId.value = '';
  activeFile.value = null;
  editorReady.value = false;
  editorError.value = '';
  htmlPreviewContent.value = '';
  showPreview.value = false;
  previewHtmlContent.value = '';
  previewCssContent.value = '';
  previewJsContent.value = '';
  originalFileContents.value = {};
  taskStatus.value = 'not_started';
  evaluationResults.value = [];
  evaluationAllPassed.value = false;
  judgmentAnswer.value = null;
  choiceAnswer.value = null;
  multiChoiceAnswers.value = [];
  allTasks.value = [];
  currentTaskIndex.value = -1;
  resetEvaluationState();
};

// 获取某道题的评测结果
const getQuestionResult = (qIndex: number): QuestionResult | null => {
  if (!evaluationState.value.submitted || !evaluationState.value.question_results) return null;
  return evaluationState.value.question_results.find(r => r.question_index === qIndex) || null;
};

// 根据评测结果获取题目边框样式
const getQuestionBorderStyle = (qIndex: number): object => {
  const result = getQuestionResult(qIndex);
  if (!result) return { border: '1px solid #e8e8e8', background: '#fafafa' };
  return result.correct 
    ? { border: '2px solid #52c41a', background: '#f6ffed' }
    : { border: '2px solid #ff4d4f', background: '#fff2f0' };
};

// 获取选项的样式类
const getOptionClass = (qIndex: number, optIndex: number, type: 'single' | 'multiple'): string => {
  const result = getQuestionResult(qIndex);
  if (!result) return '';
  
  const correctAnswer = result.correct_answer;
  const userAnswer = result.user_answer;
  
  // 检查这个选项是否是正确答案
  const isCorrectOption = type === 'single' 
    ? correctAnswer === optIndex 
    : Array.isArray(correctAnswer) && correctAnswer.includes(optIndex);
  
  // 检查这个选项是否被用户选中
  const isUserSelected = type === 'single'
    ? userAnswer === optIndex
    : Array.isArray(userAnswer) && userAnswer.includes(optIndex);
  
  if (isCorrectOption && isUserSelected) return 'option-correct';
  if (isCorrectOption && !isUserSelected) return 'option-missed';  // 漏选
  if (!isCorrectOption && isUserSelected) return 'option-wrong';   // 错选
  return '';
};

// 是否显示正确答案标记
const showCorrectMark = (qIndex: number, optIndex: number): boolean => {
  const result = getQuestionResult(qIndex);
  if (!result || result.correct) return false;  // 答对了不显示
  
  const correctAnswer = result.correct_answer;
  // 检查这个选项是否是正确答案
  return Array.isArray(correctAnswer) 
    ? correctAnswer.includes(optIndex)
    : correctAnswer === optIndex;
};

// 重置选择题评测状态
const resetChoiceEvaluation = () => {
  resetEvaluationState();
  // 不清空用户答案，让用户可以修改后重新提交
};

// 计算属性：选择题答案是否完整
const isChoiceAnswerComplete = computed(() => {
  // 多题目模式
  if (challengeInfo.value?.questions && challengeInfo.value.questions.length > 0) {
    return challengeInfo.value.questions.every((q: any, index: number) => {
      const answer = multiChoiceAnswers.value[index];
      if (q.type === 'single') {
        return answer !== null && answer !== undefined;
      } else {
        return Array.isArray(answer) && answer.length > 0;
      }
    });
  }
  // 单题目模式
  return choiceAnswer.value !== null;
});

// 新增命令行终端相关变量
const terminalRef = shallowRef();
const terminalInitOutput = ref<string[]>(['欢迎使用命令行终端', '输入命令开始练习...']);
const terminalPrompt = ref('$ ');
const terminalHistory = ref<string[]>([]); // 记录终端历史命令
const terminalCommandResponses = ref<Record<string, string[]>>({}); // 命令响应映射

// 云桌面相关变量
const desktopRemainingTime = ref(30); // 剩余时间（分钟）

// 性能优化：防抖处理状态更新
let desktopTimeUpdateTimer: NodeJS.Timeout | null = null;
let countdownTimer: NodeJS.Timeout | null = null; // 倒计时器
const canExtendTime = computed(() => desktopRemainingTime.value < 20);
const isFullscreen = ref(false);
const clipboardVisible = ref(false);
const clipboardText = ref('');
const isClipboardSupported = ref(false);
const desktopEnvironmentUrl = ref(''); // VDI 环境 URL
const desktopEnvironmentId = ref(''); // VDI 环境 ID
const jupyterRef = ref(); // Jupyter 组件引用
const vdiIframeRef = ref<HTMLIFrameElement>(); // VDI iframe 引用

// 环境资源控制相关变量 - 使用新的环境控制系统
// 这些状态现在通过 environmentControl 管理

// 任务导航相关变量
const allTasks = ref<any[]>([]);
const currentTaskIndex = ref(-1);
const hasPrevTask = computed(() => currentTaskIndex.value > 0);
// 下一关按钮：必须有下一关，且当前关卡已通关
const hasNextTask = computed(() => {
  const hasNext = currentTaskIndex.value < allTasks.value.length - 1;
  const currentCompleted = taskStatus.value === 'completed' || evaluationState.value.status === 'pass';
  return hasNext && currentCompleted;
});

// 根据环境类型生成描述信息
const envTypeDescription = computed(() => {
  const envType = challengeInfo.value?.envType || 'code';

  switch (envType) {
    case 'code':
      return {
        title: '本题为编程题，你的代码需要：',
        requirements: [
          '完成指定功能的函数或程序',
          '处理输入数据并产生正确输出',
          '通过所有测试用例验证'
        ]
      };
    case 'html':
      return {
        title: '本题为HTML前端开发题，操作步骤：',
        requirements: [
          '在编辑器中编写HTML代码',
          '点击"页面预览"按钮实时查看效果',
          '确保DOM元素符合任务要求后点击"评测"'
        ]
      };
    case 'shell':
      return {
        title: '本题为命令行操作题，你需要：',
        requirements: [
          '使用Linux命令行工具',
          '完成文件操作和数据处理',
          '按要求输出结果'
        ]
      };
    case 'desktop':
      return {
        title: '本题为云桌面操作题，你需要：',
        requirements: [
          '在云桌面环境中完成操作',
          '使用预装的软件工具',
          '按照要求完成任务并提交结果'
        ]
      };
    default:
      return {
        title: '本题为编程练习，你的代码需要：',
        requirements: [
          '按照任务要求编写代码',
          '处理输入并产生输出',
          '确保代码正确性和效率'
        ]
      };
  }
});

// 计算属性
const renderedTaskContent = computed(() => {
  if (!challengeInfo.value?.taskContent) return '';
  
  const converter = new showdown.Converter({
    tables: true,
    tasklists: true,
    strikethrough: true
  });
  return converter.makeHtml(challengeInfo.value.taskContent);
});

const visibleTestCases = computed(() => {
  if (!challengeInfo.value?.testCases) return [];
  return challengeInfo.value.testCases.filter(tc => !tc.hidden);
});

const hiddenTestCases = computed(() => {
  if (!challengeInfo.value?.testCases) return [];
  return challengeInfo.value.testCases.filter(tc => tc.hidden);
});

// 计算HTML挑战类型
const isHtmlChallenge = computed(() => {
  return challengeInfo.value?.envType === 'html';
});

// 命令行环境相关计算属性
const isCommandChallenge = computed(() => {
  return challengeInfo.value?.envType === 'shell';
});

// 云桌面环境相关计算属性
const isCloudDesktopChallenge = computed(() => {
  return challengeInfo.value?.envType === 'desktop';
});

// 任务完成状态
const isTaskCompleted = computed(() => {
  return taskStatus.value === 'completed';
});

// 是否可以查看参考答案（教师/管理员始终可以，学生需要通关后）
const canViewAnswer = computed(() => {
  const role = userStore.userRole;
  console.log('[参考答案Tab] 计算权限 - 用户角色:', role, '任务完成:', isTaskCompleted.value, '评估状态:', evaluationState.value.status);
  // 教师和管理员始终可以查看
  if (role === 'teacher' || role === 'admin') {
    console.log('[参考答案Tab] 教师/管理员权限，允许查看');
    return true;
  }
  // 学生需要通关后才能查看
  const canView = isTaskCompleted.value || evaluationState.value.status === 'pass';
  console.log('[参考答案Tab] 学生权限检查结果:', canView);
  return canView;
});

// Tab切换处理
const handleTabChange = (activeKey: string) => {
  console.log('[参考答案Tab] Tab切换触发:', activeKey, '当前canViewAnswer:', canViewAnswer.value);
  if (activeKey === 'answer') {
    if (!canViewAnswer.value) {
      message.warning({
        content: '请先通过该任务才能查看参考答案',
        duration: 3,
      });
      // 切换回过关任务Tab
      activeTaskTab.value = 'task';
      return;
    }
    // 显式设置为answer Tab
    activeTaskTab.value = 'answer';
  }
};

// 复制参考答案
const copyReferenceAnswer = () => {
  if (!challengeInfo.value?.referenceAnswer) {
    message.warning({ content: '暂无参考答案', duration: 2 });
    return;
  }
  
  navigator.clipboard.writeText(challengeInfo.value.referenceAnswer).then(() => {
    message.success({ content: '✅ 代码已复制到剪贴板', duration: 2 });
  }).catch(() => {
    message.error({ content: '复制失败，请手动复制', duration: 2 });
  });
};

// 刷新参考答案（通关后调用）
const refreshReferenceAnswer = async () => {
  if (!challengeInfo.value) return;
  
  try {
    console.log('[参考答案] 通关后刷新参考答案...');
    const roleForAnswer = userStore.userRole === 'admin' ? 'teacher' : userStore.userRole;
    const answerResponse = await getTaskAnswer(taskId, requireCurrentUserId(), roleForAnswer || 'student');
    
    const content = answerResponse.content || answerResponse.data?.content;
    if (content) {
      challengeInfo.value.referenceAnswer = content;
      console.log('[参考答案] 已刷新，内容长度:', content.length);
    }
  } catch (err) {
    console.error('[参考答案] 刷新失败:', err);
  }
};

// 是否可以显示页面预览 - 仅对 HTML 类型任务启用
const canShowPreview = computed(() => {
  // 只有 HTML 类型的任务才显示页面预览
  // Python/其他代码类型任务不需要页面预览
  return challengeInfo.value?.envType === 'html' &&
         fileTreeData.value.length > 0;
});

// 方法

// 返回上一页
const goBack = () => {
  if (classroomId) {
    router.push(`/classroom/${classroomId}`);
  } else if (window.history.length > 1) {
    router.back();
  } else {
    router.push('/classroom');
  }
};

// 导航到上一关
const navigateToPrevTask = () => {
  if (!hasPrevTask.value) return;
  
  const prevTask = allTasks.value[currentTaskIndex.value - 1];
  if (prevTask) {
      // 保存当前代码快照
      if (activeFile.value) {
        const currentContent = getCurrentEditorContent();
        saveCodeSnapshot(taskId, requireCurrentUserId(), `hash_${Date.now()}`, {
          [activeFile.value.id]: currentContent
        }).catch(err => console.error('保存代码快照失败:', err));
      }
    
    router.push(`/course/challenge/${courseId}/${prevTask.id}`);
  }
};

// 导航到下一关
const navigateToNextTask = () => {
  if (!hasNextTask.value) return;
  
  const nextTask = allTasks.value[currentTaskIndex.value + 1];
  if (nextTask) {
      // 保存当前代码快照
      if (activeFile.value) {
        const currentContent = getCurrentEditorContent();
        saveCodeSnapshot(taskId, requireCurrentUserId(), `hash_${Date.now()}`, {
          [activeFile.value.id]: currentContent
        }).catch(err => console.error('保存代码快照失败:', err));
      }
    
    router.push(`/course/challenge/${courseId}/${nextTask.id}`);
  }
};

// 切换测试集显示状态
const toggleTestCases = () => {
  showTestCases.value = !showTestCases.value;
};

// 提交判断题答案
const submitJudgment = async () => {
  if (judgmentAnswer.value === null) {
    message.warning('请选择答案');
    return;
  }

  try {
    const currentUserId = requireCurrentUserId();
    console.log('[判断题评测] 开始提交，答案:', judgmentAnswer.value);
    
    // 将布尔值转换为字符串，因为后端期望 string 类型
    const result = await evaluateTask(taskId, currentUserId, {
      answer: String(judgmentAnswer.value),
      task_type: 'TRUE_FALSE'
    });

    console.log('[判断题评测] API返回结果:', result);

    if (result.code === '0000') {
      // 后端返回 status: "pass" 或 "fail"
      const isCorrect = result.data.status === 'pass';
      console.log('[判断题评测] 评测结果:', isCorrect ? '正确' : '错误');
      
      if (isCorrect) {
        // 更新任务状态
        taskStatus.value = 'completed';
        console.log('[判断题评测] 任务状态已更新为 completed');
        
        // 显示醒目的成功弹窗
        Modal.success({
          title: '🎉 回答正确！',
          content: h('div', { style: 'text-align: center; padding: 10px 0;' }, [
            h('p', { style: 'font-size: 16px; margin-bottom: 12px;' }, '恭喜通关！'),
            challengeInfo.value?.coin ? h('div', { 
              style: 'margin-top: 12px; padding: 8px 16px; background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%); border-radius: 16px; display: inline-flex; align-items: center; color: #5c4800; font-weight: bold;'
            }, [
              h('span', { style: 'font-size: 18px; margin-right: 4px;' }, '🪙'),
              `+${challengeInfo.value.coin} 金币`
            ]) : null
          ].filter(Boolean)),
          okText: '继续学习',
          centered: true,
        });
        
        // 触发任务完成事件
        dataSyncStore.emitTaskCompleted(challengeInfo.value, {
          taskId: taskId,
          courseId: courseId,
          classroomId: classroomId,
          userId: userStore.userId
        });
      } else {
        // 显示醒目的失败弹窗
        Modal.error({
          title: '❌ 回答错误',
          content: h('div', { style: 'padding: 10px 0;' }, [
            h('p', { style: 'font-size: 14px; color: #ff4d4f;' }, '答案不正确，请重新选择后再次提交。')
          ]),
          okText: '重新作答',
          centered: true,
        });
        console.log('[判断题评测] 显示错误消息');
      }
    } else {
      console.error('[判断题评测] API返回错误:', result);
      message.error(result.message || '评测失败');
    }
  } catch (error) {
    console.error('提交判断题失败:', error);
    message.error('提交失败，请重试');
  }
};
// 提交选择题答案
const submitChoice = async () => {
  // 多题目模式
  if (challengeInfo.value?.questions && challengeInfo.value.questions.length > 0) {
    if (!isChoiceAnswerComplete.value) {
      message.warning({
        content: '请完成所有题目',
        duration: 3,
      });
      return;
    }
    
    try {
      console.log('[选择题评测] 多题目模式，答案:', multiChoiceAnswers.value);
      const currentUserId = requireCurrentUserId();
      
      // 将答案格式化为字符串，方便后端解析
      const answersToSubmit = challengeInfo.value.questions.map((q: any, index: number) => {
        const answer = multiChoiceAnswers.value[index];
        if (q.type === 'single') {
          return { questionId: q.id, answer: answer };
        } else {
          return { questionId: q.id, answer: answer };
        }
      });
      
      const result = await evaluateTask(taskId, currentUserId, {
        answer: JSON.stringify(answersToSubmit),
        task_type: challengeInfo.value.taskType
      });

      console.log('[选择题评测] API返回:', result);

      if (result.code === '0000') {
        const isCorrect = result.data.status === 'pass';
        console.log('[选择题评测] 评测结果:', isCorrect ? '正确' : '错误');
        
        // 更新评测状态
        evaluationState.value = {
          status: result.data.status,
          score: result.data.score || 0,
          total_tests: result.data.total_tests || 0,
          passed_tests: result.data.passed_tests || 0,
          error_message: result.data.error_message || '',
          question_results: result.data.question_results || [],
          submitted: true
        };
        
        if (isCorrect) {
          console.log('[选择题评测] 准备显示成功消息...');
          taskStatus.value = 'completed';
          
          // 显示醒目的成功弹窗
          Modal.success({
            title: '🎉 恭喜通关！',
            content: h('div', { style: 'text-align: center; padding: 10px 0;' }, [
              h('p', { style: 'font-size: 16px; margin-bottom: 12px;' }, '全部回答正确！'),
              h('div', { style: 'display: flex; justify-content: center; gap: 20px;' }, [
                h('span', { style: 'color: #52c41a; font-weight: bold;' }, `得分: ${result.data.score || 100}分`),
                h('span', { style: 'color: #1890ff;' }, `正确: ${result.data.passed_tests}/${result.data.total_tests}题`)
              ]),
              challengeInfo.value?.coin ? h('div', { 
                style: 'margin-top: 12px; padding: 8px 16px; background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%); border-radius: 16px; display: inline-flex; align-items: center; color: #5c4800; font-weight: bold;'
              }, [
                h('span', { style: 'font-size: 18px; margin-right: 4px;' }, '🪙'),
                `+${challengeInfo.value.coin} 金币`
              ]) : null
            ].filter(Boolean)),
            okText: '继续学习',
            centered: true,
          });
          
          dataSyncStore.emitTaskCompleted({
            id: taskId,
            practiceId: courseId,
            coin: challengeInfo.value?.coin || 0,
            title: challengeInfo.value?.title || ''
          }, {
            status: 'pass',
            score: 100
          });
          
          // 通关后刷新参考答案权限（学生现在可以查看）
          await refreshReferenceAnswer();
        } else {
          const errorMsg = result.data.error_message || '部分题目回答错误';
          
          // 显示醒目的失败弹窗
          Modal.error({
            title: '❌ 评测未通过',
            content: h('div', { style: 'padding: 10px 0;' }, [
              h('p', { style: 'font-size: 14px; margin-bottom: 12px; color: #ff4d4f;' }, errorMsg),
              h('div', { style: 'display: flex; justify-content: center; gap: 20px;' }, [
                h('span', { style: 'color: #52c41a;' }, `正确: ${result.data.passed_tests}题`),
                h('span', { style: 'color: #ff4d4f;' }, `错误: ${result.data.total_tests - result.data.passed_tests}题`)
              ]),
              h('p', { style: 'margin-top: 12px; color: #666; font-size: 13px;' }, '请检查上方标红的题目，查看正确答案后重新作答。')
            ]),
            okText: '重新作答',
            centered: true,
          });
        }
      } else {
        message.error({
          content: result.message || '评测失败',
          duration: 5,
        });
      }
    } catch (error) {
      console.error('提交选择题失败:', error);
      message.error({
        content: '提交失败，请重试',
        duration: 5,
      });
    }
    return;
  }
  
  // 单题目模式（兼容旧数据）
  if (choiceAnswer.value === null) {
    message.warning('请选择答案');
    return;
  }

  try {
    const currentUserId = requireCurrentUserId();
    const result = await evaluateTask(taskId, currentUserId, {
      answer: String(choiceAnswer.value),
      task_type: 'SINGLE_CHOICE'
    });

    if (result.code === '0000') {
      const isCorrect = result.data.status === 'pass';
      if (isCorrect) {
        message.success('回答正确！');
        taskStatus.value = 'completed';
        dataSyncStore.emitTaskCompleted({
          id: taskId,
          practiceId: courseId,
          coin: challengeInfo.value?.coin || 0,
          title: challengeInfo.value?.title || ''
        }, {
          status: 'pass',
          score: 100
        });
      } else {
        message.error('回答错误，请重试');
      }
    }
  } catch (error) {
    message.error('提交失败，请重试');
  }
};

// 处理字体大小更改
const handleFontSizeChange = (e: any) => {
  const size = parseInt(e.key, 10);
  editorOptions.value = {
    ...editorOptions.value,
    fontSize: size
  };
  message.success(`字号已调整为 ${size}px`);
};

// 重置当前文件代码
const resetCurrentFile = () => {
  if (!activeFile.value) return;
  
  const originalContent = originalFileContents.value[activeFile.value.id];
  if (originalContent !== undefined) {
    activeFile.value.content = originalContent;
    if (monacoEditor.value) {
      monacoEditor.value.setValue(originalContent);
    }
    message.success('已重置当前文件代码');
  }
};

// 返回通关时代码
const returnToPassedCode = async () => {
  if (!challengeInfo.value) return;

  try {
    const { getPassedCodeSnapshot } = await import('../../../api/challenge');
    const response = await getPassedCodeSnapshot(taskId, userStore.userId);

    if ((response.code === 200 || response.code === "0000") && response.data) {
      console.log('返回通关时代码响应数据:', response.data);
      const passedSnapshot = response.data;

      // 恢复通关时代的代码文件
      const restoreFiles = (files: CodeFile[], snapshot: any) => {
        files.forEach(file => {
          if (!file.isDirectory && snapshot[file.name]) {
            file.content = snapshot[file.name];
          }

          if (file.children && file.children.length > 0) {
            restoreFiles(file.children, snapshot);
          }
        });
      };

      // 执行恢复
      restoreFiles(challengeInfo.value.codeFiles, passedSnapshot);

      // 如果当前文件是打开的，更新编辑器
      if (activeFile.value && monacoEditor.value) {
        const passedContent = passedSnapshot[activeFile.value.name];
        if (passedContent !== undefined) {
          monacoEditor.value.setValue(passedContent);
        }
      }

      message.success('已恢复到通关时代的代码');
    } else {
      message.error('获取通关时代码失败，请稍后重试');
    }
  } catch (error) {
    console.error('恢复通关时代码失败:', error);
    message.error('恢复通关时代码失败，请稍后重试');
  }
};

// 重置所有代码
const resetAllCode = async () => {
  if (!challengeInfo.value) return;

  // 显示确认对话框
  const { Modal } = await import('ant-design-vue');
  Modal.confirm({
    title: '确认重置全部代码',
    content: '确定要重置所有代码文件吗？这将清除所有文件的修改内容，恢复到初始状态。',
    okText: '确定',
    cancelText: '取消',
    onOk: () => {
      // 递归重置代码文件
      const resetFiles = (files: CodeFile[]) => {
        files.forEach(file => {
          if (!file.isDirectory && file.id in originalFileContents.value) {
            file.content = originalFileContents.value[file.id];
          }

          if (file.children && file.children.length > 0) {
            resetFiles(file.children);
          }
        });
      };

      // 执行重置
      resetFiles(challengeInfo.value.codeFiles);

      // 如果当前文件是打开的，更新编辑器
      if (activeFile.value && monacoEditor.value) {
        const originalContent = originalFileContents.value[activeFile.value.id];
        if (originalContent !== undefined) {
          monacoEditor.value.setValue(originalContent);
        }
      }

      message.success('已重置所有代码');
    }
  });
};

// 从代码文件列表构建文件树数据
const buildFileTreeData = (files: CodeFile[]) => {
  // 递归转换文件格式为树形结构
  const convertToTreeData = (files: CodeFile[]): any[] => {
    return files.map(file => {
      const node = {
        key: file.id,
        title: file.name,
        isLeaf: !file.isDirectory,
        children: file.children ? convertToTreeData(file.children) : undefined
      };
      
      // 保存原始内容，用于重置功能
      if (!file.isDirectory && file.content) {
        originalFileContents.value[file.id] = file.content;
      }
      
      return node;
    });
  };
  
  fileTreeData.value = convertToTreeData(files);
};

// 处理文件选择事件
const handleFileSelect = (key: string) => {
  // 递归查找文件
  const findFile = (files: CodeFile[]): CodeFile | null => {
    for (const file of files) {
      if (file.id === key) {
        return file;
      }
      
      if (file.children && file.children.length > 0) {
        const found = findFile(file.children);
        if (found) return found;
      }
    }
    
    return null;
  };
  
  if (!challengeInfo.value?.codeFiles) return;
  
  const file = findFile(challengeInfo.value.codeFiles);
  if (file && !file.isDirectory) {
    // 切换文件时重置编辑器状态
    editorReady.value = false;
    editorError.value = '';
    activeFileId.value = key;
    activeFile.value = file;
  }
};

// 处理编辑器加载成功
const handleEditorMounted = (editor: any) => {
  console.log('[编辑器] Monaco编辑器加载成功');
  editorReady.value = true;
  editorError.value = '';
};

// 处理编辑器加载错误
const handleEditorError = (error: any) => {
  console.error('[编辑器] Monaco编辑器加载失败:', error);
  editorError.value = typeof error === 'string' ? error : '编辑器初始化失败，请刷新页面重试';
  editorReady.value = false;
};

// 获取当前编辑器中的实际代码内容
// 优先从Monaco编辑器实例获取，确保获取的是编辑器中的实际内容
// 这样可以避免响应式变量更新延迟导致的问题
const getCurrentEditorContent = (): string => {
  if (monacoEditor.value && typeof monacoEditor.value.getValue === 'function') {
    return monacoEditor.value.getValue();
  }
  // 如果编辑器实例不存在，回退到activeFile.content
  return activeFile.value?.content || '';
};

// 本地运行代码（用于测试，不评分）
const runCode = async () => {
  if (!challengeInfo.value) return;
  
  running.value = true;
  runOutput.value = '';
  
  try {
    // 使用辅助函数获取编辑器中的实际代码内容
    const code = getCurrentEditorContent();
    
    if (!code.trim()) {
      message.warning('请先输入代码');
      return;
    }
    
    // 获取测试用例
    const testCases = challengeInfo.value.testCases;
    
    // 如果没有测试用例，尝试从API获取
    if (!testCases || testCases.length === 0) {
      // 尝试获取测试用例
      try {
        const testsResponse = await getTaskTests(taskId);
        console.log('[本地运行] 获取测试用例响应:', testsResponse);
        if (testsResponse.data?.tests) {
          // 转换测试用例格式
          const tests = testsResponse.data.tests.map((test: any) => ({
            id: test.caseId?.toString() || test.id?.toString(),
            title: `测试用例 ${test.caseId || test.id}`,
            input: test.input || test.input_data || '',
            expectedOutput: test.expected || test.expected_output || '',
            hidden: test.hidden || false
          }));
          challengeInfo.value.testCases = tests;
          console.log('[本地运行] 转换后的测试用例:', tests);
        }
      } catch (error) {
        console.error('获取测试用例失败:', error);
      }
    }
    
    // 显示运行结果
    if (challengeInfo.value.testCases && challengeInfo.value.testCases.length > 0) {
      const firstTestCase = challengeInfo.value.testCases[0];
      console.log('[本地运行] 使用的测试用例:', firstTestCase);
      
      // 解析输入输出（如果是JSON格式）
      let inputDisplay = firstTestCase.input || '无输入';
      let outputDisplay = firstTestCase.expectedOutput || '无预期输出';
      
      try {
        // 尝试格式化JSON
        if (inputDisplay && inputDisplay.trim().startsWith('{')) {
          inputDisplay = JSON.stringify(JSON.parse(inputDisplay), null, 2);
        }
        if (outputDisplay && outputDisplay.trim().startsWith('{')) {
          outputDisplay = JSON.stringify(JSON.parse(outputDisplay), null, 2);
        }
      } catch (e) {
        // 不是JSON，保持原样
      }
      
      // 创建运行结果显示
      const modalContent = `
<div style="font-family: monospace;">
  <h4>运行结果</h4>
  <div style="margin: 10px 0;">
    <strong>测试用例输入:</strong>
    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 200px;">${inputDisplay}</pre>
  </div>
  <div style="margin: 10px 0;">
    <strong>预期输出:</strong>
    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 200px;">${outputDisplay}</pre>
  </div>
  <div style="margin: 10px 0; padding: 10px; background: #fff7e6; border: 1px solid #ffd666; border-radius: 4px;">
    <strong>💡 提示:</strong>
    <p style="margin: 5px 0;">1. 你的代码需要从标准输入读取JSON数据</p>
    <p style="margin: 5px 0;">2. 处理数据并输出JSON格式的结果</p>
    <p style="margin: 5px 0;">3. 点击"提交评测"进行完整测试</p>
  </div>
</div>`;
      
      // 使用ant-design的Modal显示结果
      Modal.info({
        title: '📋 测试用例格式说明',
        content: h('div', { innerHTML: modalContent }),
        width: 700,
        maskClosable: true,
        okText: '我知道了'
      });
    } else {
      message.info('正在获取测试用例...');
    }
    
  } catch (error: any) {
    message.error('运行失败: ' + error.message);
  } finally {
    running.value = false;
  }
};

// 显示测试用例示例
const showTestCaseExamples = () => {
  if (!challengeInfo.value || !challengeInfo.value.testCases) {
    message.warning('暂无测试用例');
    return;
  }
  
  const examples = challengeInfo.value.testCases.filter(tc => !tc.hidden).slice(0, 2);
  
  if (examples.length === 0) {
    message.info('所有测试用例均为隐藏用例');
    return;
  }
  
  let content = '<div style="font-family: monospace;">';
  content += '<h3>测试用例示例</h3>';
  content += '<p style="color: #666;">以下是部分测试用例的输入输出格式：</p>';
  
  examples.forEach((tc, index) => {
    content += `
      <div style="margin: 20px 0; border: 1px solid #e8e8e8; padding: 15px; border-radius: 4px;">
        <h4>示例 ${index + 1}: ${tc.title}</h4>
        <div style="margin: 10px 0;">
          <strong>输入格式:</strong>
          <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">${tc.input || '无输入'}</pre>
        </div>
        <div style="margin: 10px 0;">
          <strong>预期输出:</strong>
          <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">${tc.expectedOutput || '无输出'}</pre>
        </div>
      </div>
    `;
  });
  
  content += '<p style="color: #ff4d4f; margin-top: 20px;">注意：你的代码需要能够处理JSON格式的输入，并输出JSON格式的结果。</p>';
  content += '</div>';
  
  Modal.info({
    title: '📋 输入输出格式说明',
    content: h('div', { innerHTML: content }),
    width: 700,
    maskClosable: true,
    okText: '我知道了'
  });
};

// 显示帮助对话框
const showHelpDialog = () => {
  const envType = challengeInfo.value?.envType || 'code';
  
  let helpContent = `
<div style="font-family: system-ui, -apple-system, sans-serif;">
  <h3 style="color: #1890ff; margin-bottom: 16px;">📖 使用帮助</h3>
  
  <div style="margin-bottom: 20px;">
    <h4 style="color: #333; margin-bottom: 8px;">⌨️ 快捷键</h4>
    <table style="width: 100%; border-collapse: collapse;">
      <tr style="background: #f5f5f5;">
        <td style="padding: 8px; border: 1px solid #e8e8e8;"><kbd style="background: #fafafa; padding: 2px 6px; border-radius: 3px; border: 1px solid #d9d9d9;">Ctrl + Enter</kbd></td>
        <td style="padding: 8px; border: 1px solid #e8e8e8;">提交评测</td>
      </tr>
      <tr>
        <td style="padding: 8px; border: 1px solid #e8e8e8;"><kbd style="background: #fafafa; padding: 2px 6px; border-radius: 3px; border: 1px solid #d9d9d9;">Ctrl + S</kbd></td>
        <td style="padding: 8px; border: 1px solid #e8e8e8;">保存代码</td>
      </tr>
      ${envType === 'html' ? `
      <tr style="background: #f5f5f5;">
        <td style="padding: 8px; border: 1px solid #e8e8e8;"><kbd style="background: #fafafa; padding: 2px 6px; border-radius: 3px; border: 1px solid #d9d9d9;">Ctrl + P</kbd></td>
        <td style="padding: 8px; border: 1px solid #e8e8e8;">预览页面</td>
      </tr>
      ` : ''}
    </table>
  </div>
  
  <div style="margin-bottom: 20px;">
    <h4 style="color: #333; margin-bottom: 8px;">🛠️ 工具栏功能</h4>
    <ul style="padding-left: 20px; line-height: 2;">
      <li><strong>查看测试用例</strong>：展开/收起下方测试用例面板</li>
      <li><strong>提交评测</strong>：运行代码并检测是否通过所有测试用例</li>
      <li><strong>字号选择</strong>：调整编辑器字体大小</li>
      <li><strong>重置全部代码</strong>：恢复所有文件到初始状态</li>
      <li><strong>重置本页代码</strong>：恢复当前文件到初始状态</li>
      <li><strong>返回通关时代码</strong>：恢复到通关时保存的代码版本</li>
    </ul>
  </div>
  
  <div style="margin-bottom: 20px;">
    <h4 style="color: #333; margin-bottom: 8px;">💡 提示</h4>
    <ul style="padding-left: 20px; line-height: 2;">
      <li>代码会自动保存，无需担心丢失</li>
      <li>通关后可以继续优化代码，重新提交</li>
      <li>点击"参考答案"标签可查看标准解法</li>
      <li>如遇问题，可尝试刷新页面</li>
    </ul>
  </div>
</div>`;

  Modal.info({
    title: '❓ 帮助中心',
    content: h('div', { innerHTML: helpContent }),
    width: 600,
    maskClosable: true,
    okText: '知道了'
  });
};

// 根据任务类型调用对应的评测函数
const handleEvaluate = async () => {
  // [DT-03修复] 防止重复提交
  if (evaluating.value) {
    console.log('[handleEvaluate] 正在评测中，请勿重复提交');
    message.warning('正在评测中，请等待评测完成');
    return;
  }

  const taskType = challengeInfo.value?.taskType;
  console.log('[handleEvaluate] 任务类型:', taskType);
  
  if (taskType === 'TRUE_FALSE') {
    // 判断题
    await submitJudgment();
  } else if (taskType === 'SINGLE_CHOICE' || taskType === 'MULTIPLE_CHOICE') {
    // 选择题
    await submitChoice();
  } else {
    // 编程题等其他类型
    await evaluate();
  }
};

// 执行代码评测
const evaluate = async () => {
  // [DT-03修复] 防止重复提交 - 检查是否正在评测中
  if (evaluating.value) {
    console.log('[评测] 正在评测中，请勿重复提交');
    message.warning('正在评测中，请等待评测完成');
    return;
  }

  // 检查登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再进行评测');
    return;
  }

  if (!challengeInfo.value) return;
  
  evaluating.value = true;
  
  try {
    // 准备评测数据
    const evaluationData: any = {
      codeRepoHash: `hash_${Date.now()}` // 生成临时hash
    };

    // 根据环境类型准备不同的评测数据
    // 注意：后端API期望使用answer字段，不是code字段
    if (challengeInfo.value.envType === 'code' || challengeInfo.value.envType === 'html') {
      // 使用辅助函数获取编辑器中的实际代码内容
      const codeContent = getCurrentEditorContent();
      evaluationData.answer = codeContent;
      // 添加所有文件的快照，用于保存代码状态
      const filesSnapshot: any = {};
      challengeInfo.value.codeFiles.forEach(file => {
        if (!file.isDirectory && file.content !== undefined) {
          filesSnapshot[file.id] = file.content;
        }
      });
      evaluationData.files = filesSnapshot;
      console.log('[评测] 代码内容长度:', evaluationData.answer.length);
      console.log('[评测] 代码内容预览:', evaluationData.answer.substring(0, 100));
    } else if (challengeInfo.value.envType === 'shell') {
      // 命令行环境，使用命令历史作为答案
      evaluationData.answer = terminalHistory.value.join('\n');
    }
    
    // 调用评测API
    console.log('[评测] 发送评测请求:', evaluationData);
    const currentUserId = requireCurrentUserId();
    const response = await evaluateTask(taskId, currentUserId, evaluationData);
    console.log('[评测] 收到响应:', response);
    const result = response.data || response;
    
    // 检查是否有错误
    if (result.logs && result.logs.includes('答案不能为空')) {
      message.error('代码不能为空，请输入代码后再评测');
      evaluationResults.value = [];
      return;
    }
    
    // 处理评测结果
    if (result.status === 'pass') {
      evaluationAllPassed.value = true;

      // 检查是否为重复提交（任务已完成，本次评测不给予金币奖励）
      const isDuplicate = result.score === 0 || 
                          result.message?.includes('不给予金币奖励') ||
                          result.logs?.includes('该任务已完成') ||
                          result.logs?.includes('不给予金币奖励');
      
      // 只有首次完成时才发放金币奖励
      if (!isDuplicate) {
      // 发放金币奖励
      try {
        const taskForReward = {
          id: taskId,
          title: challengeInfo.value.title,
          type: challengeInfo.value.type || 'practice',
          difficulty: challengeInfo.value.difficulty || 1,
          coins: challengeInfo.value.coins || 10
        };

        const rewardResult = await processTaskReward(
          String(currentUserId),
          taskForReward as any,
          100, // 假设满分
          courseId,
          classroomId
        );

        if (rewardResult.success) {
          message.success(`恭喜你通过了所有测试用例！获得 ${rewardResult.rewardResult.totalCoins} 金币奖励！`, 3);

          // 标记任务为已完成
          taskStatus.value = 'completed';

          // 发送数据同步事件
          dataSyncStore.emitCoinUpdated(rewardResult.rewardResult.totalCoins, '任务完成奖励');

          // 显示奖励详情
          setTimeout(() => {
            const breakdownHtml = rewardResult.rewardResult.breakdown
              .map(item => `<li>${item}</li>`)
              .join('');
            
            Modal.success({
              title: '🎉 任务完成奖励',
              content: h('div', [
                h('p', [
                  h('strong', '获得金币：'),
                  rewardResult.rewardResult.totalCoins.toString()
                ]),
                h('p', [
                  h('strong', '当前余额：'),
                  rewardResult.newBalance.toString()
                ]),
                h('div', { style: 'margin-top: 16px;' }, [
                  h('p', [h('strong', '奖励明细：')]),
                  h('ul', { innerHTML: breakdownHtml })
                ])
              ])
            });
          }, 1000);
        } else {
          // 显示醒目的成功弹窗
          Modal.success({
            title: '🎉 评测通过！',
            content: h('div', { style: 'text-align: center; padding: 10px 0;' }, [
              h('p', { style: 'font-size: 16px; margin-bottom: 12px;' }, '恭喜你通过了所有测试用例！'),
              challengeInfo.value?.coin ? h('div', { 
                style: 'margin-top: 12px; padding: 8px 16px; background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%); border-radius: 16px; display: inline-flex; align-items: center; color: #5c4800; font-weight: bold;'
              }, [
                h('span', { style: 'font-size: 18px; margin-right: 4px;' }, '🪙'),
                `+${challengeInfo.value.coin} 金币`
              ]) : null
            ].filter(Boolean)),
            okText: '继续学习',
            centered: true,
          });
          if (rewardResult.error) {
            message.warning(rewardResult.error);
          }
        }

        // 发送任务完成同步事件
        dataSyncStore.emitTaskCompleted(taskForReward as any, {
          id: `submission_${Date.now()}`,
          taskId: taskId,
          userId: String(currentUserId),
          classroomId,
          courseId,
          submittedAt: new Date().toISOString(),
          status: 'completed',
          score: taskForReward.points,
          maxScore: taskForReward.points,
          attempts: 1
        });
      } catch (error) {
        console.error('金币奖励处理失败:', error);
        Modal.success({
          title: '🎉 评测通过！',
          content: '恭喜你通过了所有测试用例！',
          okText: '继续学习',
          centered: true,
        });
      }
      } else {
        // 重复提交，不发放金币奖励
        Modal.success({
          title: '✅ 评测通过',
          content: '恭喜你通过了所有测试用例！（该任务已完成，本次评测不给予金币奖励）',
          okText: '确定',
          centered: true,
        });
        // 标记任务为已完成（即使已经完成过）
        taskStatus.value = 'completed';
      }

      // 构建通过的结果
      evaluationResults.value = challengeInfo.value.testCases.map(tc => ({
        id: tc.id,
        title: tc.title,
        passed: true,
        actualOutput: '通过',
        expectedOutput: tc.expectedOutput,
        error: '',
        hidden: tc.hidden
      }));
    } else {
      evaluationAllPassed.value = false;
      
      // 解析错误日志和测试结果
      const logs = result.logs || result.error_message || '';
      const passedTestsCount = result.passed_tests || 0;
      const totalTestsCount = result.total_tests || challengeInfo.value?.testCases?.length || 0;
      
      // 显示醒目的失败弹窗
      Modal.error({
        title: '❌ 评测未通过',
        content: h('div', { style: 'padding: 10px 0;' }, [
          h('p', { style: 'font-size: 14px; margin-bottom: 12px;' }, '请检查代码后重新评测'),
          h('div', { style: 'display: flex; justify-content: center; gap: 20px; margin-bottom: 12px;' }, [
            h('span', { style: 'color: #52c41a;' }, `通过: ${passedTestsCount}个`),
            h('span', { style: 'color: #ff4d4f;' }, `失败: ${totalTestsCount - passedTestsCount}个`)
          ]),
          h('p', { style: 'color: #666; font-size: 13px;' }, '查看下方"详细结果"了解具体错误信息。')
        ]),
        okText: '查看详情',
        centered: true,
      });
      
      const testResults = result.test_results || [];
      
      console.log('[评测] 错误日志:', logs);
      console.log('[评测] test_results:', testResults);
      console.log('[评测] 通过/总数:', passedTestsCount, '/', totalTestsCount);
      
      // 解析日志中的详细错误信息
      const logLines = logs.split('\n').filter((line: string) => line.trim());
      const caseErrors: Record<string, string> = {};
      
      // 解析 "Case1 FAIL: 输出格式" 这样的格式
      logLines.forEach((line: string) => {
        const match = line.match(/Case(\d+)\s*(FAIL|OK|PASS):\s*(.+)/i);
        if (match) {
          const caseId = match[1];
          const status = match[2].toUpperCase();
          const detail = match[3].trim();
          if (status === 'FAIL') {
            caseErrors[`case_${caseId}`] = detail;
          }
        }
      });
      
      // 优先使用后端返回的 test_results，否则根据日志构建
      if (testResults.length > 0) {
        evaluationResults.value = testResults.map((tr: any, index: number) => ({
          id: tr.case_id || `case_${index + 1}`,
          title: `测试用例 ${index + 1}`,
          passed: tr.passed || tr.status === 'pass',
          actualOutput: tr.actual_output || tr.output || (tr.passed ? '通过' : '未通过'),
          expectedOutput: tr.expected_output || tr.expected || '',
          error: tr.error_message || tr.error || caseErrors[`case_${index + 1}`] || '',
          hidden: tr.hidden || false
        }));
      } else if (challengeInfo.value.testCases && challengeInfo.value.testCases.length > 0) {
        // 使用本地测试用例配置
        evaluationResults.value = challengeInfo.value.testCases.map((tc, index) => {
          const caseLog = logLines.find((line: string) => line.includes(`Case${index + 1}`));
          const passed = caseLog && (caseLog.includes('OK') || caseLog.includes('PASS'));
          const errorDetail = caseErrors[`case_${index + 1}`] || '';
          
          return {
            id: tc.id,
            title: tc.title || `测试用例 ${index + 1}`,
            passed: passed || false,
            actualOutput: passed ? '通过' : '未通过',
            expectedOutput: tc.expectedOutput || '',
            error: errorDetail || (passed ? '' : '测试未通过'),
            hidden: tc.hidden || false
          };
        });
      } else {
        // 根据日志构建测试结果
        const caseMatches = logs.match(/Case\d+\s*(FAIL|OK|PASS)/gi) || [];
        if (caseMatches.length > 0) {
          evaluationResults.value = caseMatches.map((match: string, index: number) => {
            const passed = match.toUpperCase().includes('OK') || match.toUpperCase().includes('PASS');
            const errorDetail = caseErrors[`case_${index + 1}`] || '';
            return {
              id: `case_${index + 1}`,
              title: `测试用例 ${index + 1}`,
              passed,
              actualOutput: passed ? '通过' : '未通过',
              expectedOutput: '',
              error: errorDetail || (passed ? '' : '测试未通过'),
              hidden: false
            };
          });
        } else {
          // 通用错误显示
          evaluationResults.value = [{
            id: '1',
            title: '评测结果',
            passed: false,
            actualOutput: logs || '评测失败',
            expectedOutput: '预期输出',
            error: logs || '评测失败，请检查代码',
            hidden: false
          }];
        }
      }
      
      // 更新统计信息到 evaluationState
      evaluationState.value = {
        ...evaluationState.value,
        status: 'fail',
        score: result.score || 0,
        total_tests: totalTestsCount,
        passed_tests: passedTestsCount,
        error_message: result.error_message || logs,
        submitted: true
      };
    }
    
    // 自动展开评测结果
    showTestCases.value = true;
    
    // 保存代码快照
    if (activeFile.value) {
      try {
        // 使用辅助函数获取编辑器中的实际代码内容
        const currentContent = getCurrentEditorContent();
        await saveCodeSnapshot(taskId, currentUserId, evaluationData.codeRepoHash, {
          [activeFile.value.id]: currentContent
        });
      } catch (err) {
        console.error('保存代码快照失败:', err);
      }
    }
  } catch (err: any) {
    console.error('[评测] 发生错误:', err);
    message.error(err.message || '评测过程发生错误，请重试');
    evaluationResults.value = [];
  } finally {
    evaluating.value = false;
    console.log('[评测] 评测结束，状态已重置');
  }
};

// 生成HTML预览内容
const generateHtmlPreview = () => {
  if (!isHtmlChallenge.value || !activeFile.value) return;
  
  // 如果当前文件是HTML文件，直接使用其内容
  if (activeFile.value.language === 'html') {
    htmlPreviewContent.value = activeFile.value.content || '';
    return;
  }
  
  // 如果当前文件不是HTML，查找主HTML文件
  const htmlFile = findHtmlMainFile();
  if (htmlFile) {
    htmlPreviewContent.value = htmlFile.content || '';
  }
};

// 查找主HTML文件（通常是index.html）
const findHtmlMainFile = () => {
  if (!challengeInfo.value?.codeFiles[0]?.children) return null;
  
  const files = challengeInfo.value.codeFiles[0].children;
  
  // 首先查找index.html
  const indexHtml = files.find(file => 
    file.name.toLowerCase() === 'index.html' && !file.isDirectory
  );
  
  if (indexHtml) return indexHtml;
  
  // 如果没有index.html，查找任何.html文件
  return files.find(file => 
    file.name.toLowerCase().endsWith('.html') && !file.isDirectory
  );
};

// 切换HTML预览
const toggleHtmlPreview = () => {
  if (!isHtmlChallenge.value) return;

  if (!showHtmlPreview.value) {
    generateHtmlPreview();
  }

  showHtmlPreview.value = !showHtmlPreview.value;
};

// 切换页面预览
const togglePreview = () => {
  if (!canShowPreview.value) return;

  if (!showPreview.value) {
    generatePreviewContent();
  }

  showPreview.value = !showPreview.value;
};

// 生成页面预览内容
const generatePreviewContent = () => {
  if (!canShowPreview.value) return;

  // 查找不同类型的文件
  const htmlFile = findFileByExtension(['html', 'htm']);
  const cssFile = findFileByExtension(['css']);
  const jsFile = findFileByExtension(['js', 'javascript']);

  // 如果有专门的HTML文件，使用文件内容；否则使用当前激活文件的内容
  let htmlContent = htmlFile?.content;
  if (!htmlContent && activeFile.value?.content) {
    // 检查当前文件是否包含HTML标签
    const content = activeFile.value.content;
    if (content.includes('<html') || content.includes('<!DOCTYPE html') ||
        content.includes('<body') || content.includes('<head')) {
      htmlContent = content;
    }
  }

  // 设置预览内容
  previewHtmlContent.value = htmlContent || generateDefaultHtml();
  previewCssContent.value = cssFile?.content || '';
  previewJsContent.value = jsFile?.content || '';
};

// 根据文件扩展名查找文件
const findFileByExtension = (extensions: string[]) => {
  const findInFiles = (files: any[]): any => {
    for (const file of files) {
      if (!file.isDirectory && file.name && extensions.some(ext => file.name.toLowerCase().endsWith(`.${ext}`))) {
        return file;
      }
      if (file.children && file.children.length > 0) {
        const found = findInFiles(file.children);
        if (found) return found;
      }
    }
    return null;
  };

  return findInFiles(fileTreeData.value);
};

// 生成默认HTML模板
const generateDefaultHtml = () => {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>页面预览</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
        .preview-hint { max-width: 600px; margin: 0 auto; padding: 40px 20px; text-align: center; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #007bff; margin-bottom: 20px; }
        p { color: #6c757d; line-height: 1.6; margin-bottom: 15px; }
        .tip { background: #e7f3ff; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; text-align: left; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="preview-hint">
        <h1>📄 页面预览</h1>
        <p>请在编辑器中编写HTML代码</p>
        <p>您可以直接在当前文件中编写完整的HTML页面，或创建独立的HTML、CSS、JavaScript文件</p>
        <div class="tip">
            <strong>💡 提示：</strong><br>
            • 在编辑器中输入HTML代码后，预览窗口会自动更新<br>
            • 支持&lt;style&gt;标签内的CSS样式<br>
            • 支持&lt;script&gt;标签内的JavaScript代码
        </div>
    </div>
</body>
</html>`;
};

// 预览更新防抖定时器
let previewUpdateTimer: ReturnType<typeof setTimeout> | null = null;

// 自动保存相关
let autoSaveTimer: ReturnType<typeof setTimeout> | null = null;
const autoSaveStatus = ref<'saved' | 'saving' | 'unsaved'>('saved');
const lastSavedTime = ref<string>('');

// 自动保存到 localStorage
const autoSaveCode = () => {
  if (!activeFile.value?.content || !taskId) return;
  
  autoSaveStatus.value = 'saving';
  
  try {
    const saveKey = `code_${taskId}_${activeFile.value.id}`;
    localStorage.setItem(saveKey, activeFile.value.content);
    localStorage.setItem(`${saveKey}_timestamp`, new Date().toISOString());
    
    autoSaveStatus.value = 'saved';
    lastSavedTime.value = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    console.log('[自动保存] 代码已保存到本地存储');
  } catch (error) {
    console.error('[自动保存] 保存失败:', error);
    autoSaveStatus.value = 'unsaved';
  }
};

// 从 localStorage 恢复代码
const restoreSavedCode = () => {
  if (!activeFile.value || !taskId) return false;
  
  try {
    const saveKey = `code_${taskId}_${activeFile.value.id}`;
    const savedCode = localStorage.getItem(saveKey);
    const savedTimestamp = localStorage.getItem(`${saveKey}_timestamp`);
    
    if (savedCode && savedCode !== activeFile.value.content) {
      // 检查保存时间是否在24小时内
      if (savedTimestamp) {
        const savedDate = new Date(savedTimestamp);
        const now = new Date();
        const hoursDiff = (now.getTime() - savedDate.getTime()) / (1000 * 60 * 60);
        
        if (hoursDiff < 24) {
          console.log('[自动保存] 发现本地存储的代码，时间:', savedTimestamp);
          activeFile.value.content = savedCode;
          lastSavedTime.value = savedDate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
          message.info(`已恢复上次编辑的代码 (${lastSavedTime.value})`);
          return true;
        }
      }
    }
  } catch (error) {
    console.error('[自动保存] 恢复失败:', error);
  }
  return false;
};

// 清除自动保存的代码
const clearSavedCode = () => {
  if (!activeFile.value || !taskId) return;
  
  try {
    const saveKey = `code_${taskId}_${activeFile.value.id}`;
    localStorage.removeItem(saveKey);
    localStorage.removeItem(`${saveKey}_timestamp`);
    console.log('[自动保存] 本地存储已清除');
  } catch (error) {
    console.error('[自动保存] 清除失败:', error);
  }
};

// 监听HTML文件内容变化，更新预览
watch(() => activeFile.value?.content, (newContent) => {
  if (isHtmlChallenge.value && showHtmlPreview.value) {
    generateHtmlPreview();
  }

  // 实时更新页面预览 - 使用防抖优化
  if (canShowPreview.value && showPreview.value) {
    // 清除之前的定时器
    if (previewUpdateTimer) {
      clearTimeout(previewUpdateTimer);
    }
    
    // 使用较短的延迟（100ms）提高响应性
    previewUpdateTimer = setTimeout(() => {
      requestAnimationFrame(() => {
        generatePreviewContent();
      });
    }, 100);
  }
  
  // 自动保存 - 防抖30秒
  autoSaveStatus.value = 'unsaved';
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
  }
  autoSaveTimer = setTimeout(() => {
    autoSaveCode();
  }, 30000); // 30秒后自动保存
}, { deep: true });

// 监听参考答案变化，用于调试
watch(() => challengeInfo.value?.referenceAnswer, (newAnswer) => {
  if (newAnswer) {
    console.log('[参考答案] 数据变化，新值长度:', newAnswer.length);
  }
}, { immediate: true });

// 检查登录状态
const checkLoginStatus = () => {
  if (!userStore.isLoggedIn) {
    message.warning('此功能需要登录才能使用');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
  }
};

const syncRouteParams = () => {
  courseId = route.params.courseId as string;
  classroomId = route.params.classroomId as string;
  taskId = route.params.taskId as string;
};

// 获取挑战信息
const fetchChallengeInfo = async () => {
  try {
    loading.value = true;
    const currentCourseId = courseId;
    const currentTaskId = taskId;
    
    // 先检查用户是否已登录
    if (!userStore.isLoggedIn) {
      message.warning('请先登录后再访问挑战页面');
      router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
      return;
    }
    
    // 获取任务详情
    const currentUserId = requireCurrentUserId();
    const taskResponse = await getTaskDetail(currentTaskId, currentUserId);
    const taskData = taskResponse?.data?.data || taskResponse?.data || taskResponse;
    
    if (!taskData || !taskData.taskId) {
      console.log('API Response:', taskResponse);
      throw new Error('获取任务详情失败：数据为空');
    }

    // 根据任务状态设置taskStatus
    if (taskData.status === 'passed') {
      taskStatus.value = 'completed';
    }
    
    // 获取实践下的所有任务，用于导航
    try {
      const tasksResponse = await getPracticeTasks(currentCourseId);
      if (tasksResponse.data?.list) {
        allTasks.value = tasksResponse.data.list;
        // 找到当前任务的索引
        currentTaskIndex.value = allTasks.value.findIndex(
          task => task.id.toString() === currentTaskId
        );
      }
    } catch (err) {
      console.log('获取任务列表失败:', err);
    }
    
    // 获取测试集
    let testData = [];
    try {
      const testsResponse = await getTaskTests(currentTaskId, false, userStore.userRole || 'student');
      testData = testsResponse?.data?.tests || testsResponse?.data || [];
    } catch (err) {
      console.log('获取测试集失败:', err);
    }
    const testCases: TestCase[] = testData.map((test: any) => ({
      id: test.caseId.toString(),
      title: `测试用例 ${test.caseId}`,
      input: test.input || '',
      expectedOutput: test.expected || '',
      hidden: test.hidden || false
    }));
    
    // 解析技能数据
    let skills: string[] = [];
    try {
      if (taskData?.skills) {
        skills = typeof taskData.skills === 'string' 
          ? JSON.parse(taskData.skills) 
          : taskData.skills;
      }
    } catch (error) {
      console.warn('解析技能数据失败:', error);
      skills = [];
    }
    
    // 先获取参考答案（如果有权限）
    let referenceAnswer = '';
    console.log('[参考答案] 检查权限 - 用户角色:', userStore.userRole, '任务状态:', taskData.status);
    if (userStore.userRole === 'teacher' || userStore.userRole === 'admin' || taskData.status === 'passed') {
      console.log('[参考答案] 用户有权限查看，正在获取...');
      try {
        // 如果是admin，使用teacher角色来获取参考答案（后端限制）
        const roleForAnswer = userStore.userRole === 'admin' ? 'teacher' : userStore.userRole;
        const answerResponse = await getTaskAnswer(currentTaskId, currentUserId, roleForAnswer || 'student');
        console.log('[参考答案] API响应:', answerResponse);
        // 兼容两种响应格式：直接返回 {content: ...} 或 {data: {content: ...}}
        const content = answerResponse.content || answerResponse.data?.content;
        if (content) {
          referenceAnswer = content;
          console.log('[参考答案] 已获取，内容长度:', referenceAnswer.length);
          console.log('[参考答案] 前100字符:', referenceAnswer.substring(0, 100));
        } else {
          console.log('[参考答案] API返回内容为空');
          referenceAnswer = '// 参考答案暂未提供';
        }
      } catch (err) {
        console.error('[参考答案] 获取失败:', err);
        referenceAnswer = '// 获取参考答案失败，请重试';
      }
    } else {
      console.log('[参考答案] 用户无权限查看');
      referenceAnswer = '// 您需要先通过该任务才能查看参考答案';
    }
    
    // 构建挑战信息对象，使用参考答案作为初始代码
    const challenge: CodingChallenge = {
      id: taskData?.taskId?.toString() || '',
      title: taskData?.title || '',
      taskContent: taskData?.handbookMd || '',
      envType: taskData?.envType || 'code',
      difficulty: taskData.difficulty || 'intermediate',
      coin: taskData.coin || 0,
      coins: taskData.coin || 0, // 为了兼容Task接口
      type: 'practice',
      skills: skills,
      testCases: testCases,
      referenceAnswer: referenceAnswer,
      codeFiles: await buildCodeFiles(taskData.envType, referenceAnswer, taskData.title),
      // 添加题目相关字段
      taskType: taskData?.taskType,
      question: taskData?.question,
      options: taskData?.options,
      correctAnswer: taskData?.correctAnswer,
      explanation: taskData?.explanation,
      // 多题目支持
      questions: taskData?.questions
    };
    
    challengeInfo.value = challenge;
    
    // 处理文件树
    if (challenge.codeFiles && challenge.codeFiles.length > 0) {
      buildFileTreeData(challenge.codeFiles);
      
      // 找到第一个非目录文件作为默认打开文件
      const findFirstFile = (files: CodeFile[]): CodeFile | null => {
        for (const file of files) {
          if (!file.isDirectory) {
            return file;
          }
          
          if (file.children && file.children.length > 0) {
            const found = findFirstFile(file.children);
            if (found) return found;
          }
        }
        
        return null;
      };
      
      const firstFile = findFirstFile(challenge.codeFiles);
      if (firstFile) {
        activeFileId.value = firstFile.id;
        activeFile.value = firstFile;
        // 初始化编辑器状态
        editorReady.value = false;
        editorError.value = '';
      }
    }
  } catch (error) {
    console.error('获取挑战信息失败:', error);
    message.error('获取挑战信息失败');
  } finally {
    loading.value = false;
  }
};

// 根据环境类型构建默认代码文件
const buildCodeFiles = async (envType: string, referenceAnswer?: string, taskTitle?: string): Promise<CodeFile[]> => {
  switch (envType) {
    case 'code':
      // 根据任务标题生成不同的初始代码
      let initialContent = '';

      if (taskTitle?.includes('变量与数据类型')) {
        initialContent = `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
变量与数据类型操作
请完成process_student_info函数，实现数据类型转换和成绩计算
"""

def process_student_info(name, age_str, score_str, is_monitor_str):
    """
    处理学生信息
    参数:
        name: 学生姓名
        age_str: 年龄字符串
        score_str: 成绩字符串
        is_monitor_str: 是否班长字符串
    返回:
        处理后的学生信息字典
    """
    # 请在此处编写你的代码
    # 1. 将字符串转换为对应数据类型
    # 2. 根据成绩计算等级
    # 3. 返回包含所有信息的字典

    pass

# 测试代码（请勿修改）
if __name__ == "__main__":
    # 示例调用
    result = process_student_info("李华", "18", "85.5", "True")
    print(result)
`;
      } else if (taskTitle?.includes('输入输出')) {
        initialContent = `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
输入输出与字符串处理
请掌握基本的输入输出操作和字符串处理方法
"""

# 请在此处编写你的代码
# 练习基本的print()和input()函数
# 学习字符串的基本操作方法

print("请输入你的姓名：")
name = input()

print("请输入你的年龄：")
age = input()

print(f"你好，{name}！你的年龄是{age}岁。")
`;
      } else if (taskTitle?.includes('运算符')) {
        initialContent = `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运算符综合应用
请掌握各种运算符的使用方法
"""

# 请在此处编写你的代码
# 练习算术运算符、比较运算符、逻辑运算符等

# 示例：计算两个数的各种运算结果
a = 10
b = 3

print(f"a + b = {a + b}")
print(f"a - b = {a - b}")
print(f"a * b = {a * b}")
print(f"a / b = {a / b}")
print(f"a // b = {a // b}")  # 整除
print(f"a % b = {a % b}")    # 取余
print(f"a ** b = {a ** b}")  # 幂运算

# 比较运算
print(f"a > b: {a > b}")
print(f"a < b: {a < b}")
print(f"a == b: {a == b}")
`;
      } else {
        // 默认的Python代码模板
        initialContent = `#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
${taskTitle || 'Python编程任务'}
请在此处编写你的代码
"""

# 请在此处编写你的代码

print("Hello, World!")
`;
      }

      // 如果有参考答案且是教师/管理员，可以选择使用参考答案
      if (referenceAnswer && referenceAnswer.length > 100 &&
          (userStore.userRole === 'teacher' || userStore.userRole === 'admin')) {
        // 教师和管理员可以看到完整的参考答案作为初始代码
        initialContent = referenceAnswer;
      }
      
      return [{
        id: '1',
        name: 'solution.py',
        path: '/solution.py',
        content: initialContent,
        language: 'python',
        isDirectory: false,
        readOnly: false
      }];
    case 'html':
      return [{
        id: '1',
        name: 'index.html',
        path: '/index.html',
        content: '<!DOCTYPE html>\n<html>\n<head>\n    <title>My Page</title>\n</head>\n<body>\n    <!-- 在此处编写你的HTML代码 -->\n</body>\n</html>',
        language: 'html',
        isDirectory: false,
        readOnly: false
      }];
    case 'shell':
      // 命令行环境不需要代码文件
      return [];
    case 'desktop':
      // 云桌面环境不需要代码文件
      return [];
    default:
      return [{
        id: '1',
        name: 'main.py',
        path: '/main.py',
        content: '# 请在此处编写你的代码\n',
        language: 'python',
        isDirectory: false,
        readOnly: false
      }];
  }
};

// 处理命令执行
const handleCommandExecution = (command: string) => {
  // 检查登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再使用命令行');
    return;
  }

  if (!challengeInfo.value) return;
  
  // 记录命令历史
  terminalHistory.value.push(command);
  
  // 解析命令
  const cmd = command.trim().split(' ')[0].toLowerCase();
  const args = command.trim().split(' ').slice(1);
  
  // 简单模拟命令行响应
  setTimeout(() => {
    let response: string[] = [];
    
    // 检查是否有预设的响应
    if (terminalCommandResponses.value[command]) {
      response = terminalCommandResponses.value[command];
    } else {
      // 默认命令处理
      switch (cmd) {
        case 'help':
          response = [
            'Available commands:',
            '  help     - 显示帮助信息',
            '  ls       - 列出文件和目录',
            '  cd       - 切换目录',
            '  pwd      - 显示当前路径',
            '  cat      - 查看文件内容',
            '  clear    - 清除屏幕',
            '  history  - 显示历史命令'
          ];
          break;
        case 'ls':
          response = ['file1.txt', 'file2.txt', 'dir1/', 'dir2/'];
          break;
        case 'cd':
          response = args.length > 0 ? [`Changed directory to ${args[0]}`] : ['Missing directory argument'];
          break;
        case 'pwd':
          response = ['/home/user/practice'];
          break;
        case 'cat':
          response = args.length > 0 
            ? [`File content of ${args[0]}: This is a sample file content.`]
            : ['Missing filename argument'];
          break;
        case 'clear':
          // 清除终端内容
          if (terminalRef.value) {
            terminalRef.value.resetTerminal();
          }
          return; // 不添加输出
        case 'history':
          response = terminalHistory.value.slice(0, -1); // 不包括当前命令
          break;
        default:
          response = [`Command not found: ${cmd}. Type 'help' for available commands.`];
      }
    }
    
    // 添加响应到终端
    if (terminalRef.value && response.length > 0) {
      terminalRef.value.addOutputLines(response);
    }
  }, 300);
};

// 重置终端
const resetTerminal = () => {
  if (terminalRef.value) {
    terminalRef.value.resetTerminal();
  }
};

// 处理终端重置
const handleTerminalReset = async () => {
  try {
    // 显示确认对话框
    await new Promise((resolve, reject) => {
      Modal.confirm({
        title: '确认重置',
        content: '点击可将命令行重置为初始状态，是否确认？',
        okText: '确定',
        cancelText: '取消',
        onOk: () => resolve(true),
        onCancel: () => reject(new Error('用户取消'))
      });
    });

    // 调用后端API重置环境
    const { resetTerminalEnvironment } = await import('../../../api/challenge');
    const response = await resetTerminalEnvironment(taskId, requireCurrentUserId());

    if (response.code === '0000' || response.code === "0000") {
      // 重置前端状态
      terminalHistory.value = [];
      if (terminalRef.value) {
        terminalRef.value.resetTerminal();
      }
      // 显示成功消息
      message.success('命令行环境已重置');
    } else {
      throw new Error(response.message || '重置失败');
    }
  } catch (error: any) {
    if (error.message !== '用户取消') {
      console.error('重置终端环境失败:', error);
      message.error(error.message || '重置命令行环境失败');
    }
  }
};

// 云桌面相关方法
const extendDesktopTime = async () => {
  if (!canExtendTime.value) {
    message.warning('当前剩余时间充足，无需延时');
    return;
  }
  
  try {
    const { extendEnvironmentTime } = await import('../../../api/training');
    const response = await extendEnvironmentTime(desktopEnvironmentId.value || taskId, 30); // 延时 30 分钟
    if (response && response.code === "0000") {
      desktopRemainingTime.value += 30;
      message.success('云桌面已延时30分钟');
    } else {
      const errorMsg = response?.message || '延时失败，请稍后重试';
      message.error(errorMsg);
    }
  } catch (error) {
    console.error('延时操作失败:', error);
    const errorMsg = error?.response?.data?.message || error?.message || '延时失败，请稍后重试';
    message.error(errorMsg);
  }
};

const openClipboard = () => {
  // 打开剪切板弹窗
  clipboardVisible.value = true;
};

const copyToClipboard = async () => {
  if (!isClipboardSupported.value) {
    message.error('浏览器不支持剪切板API，请手动复制');
    return;
  }

  try {
    await navigator.clipboard.writeText(clipboardText.value);
    message.success('已复制到剪切板');
  } catch (error) {
    console.error('复制失败:', error);
    message.error('复制失败，请手动复制');
  }
};

const pasteFromClipboard = async () => {
  if (!isClipboardSupported.value) {
    message.error('浏览器不支持剪切板API，请手动粘贴');
    return;
  }

  try {
    const text = await navigator.clipboard.readText();
    clipboardText.value = text;
    message.success('已从剪切板粘贴');
  } catch (error) {
    console.error('粘贴失败:', error);
    message.error('粘贴失败，请手动粘贴');
  }
};

// 启动倒计时器
const startCountdownTimer = () => {
  // 清除现有定时器
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }

  // 每分钟减少1分钟
  countdownTimer = setInterval(() => {
    if (desktopRemainingTime.value > 0) {
      desktopRemainingTime.value--;

      // 当剩余时间少于5分钟时显示警告
      if (desktopRemainingTime.value === 5) {
        message.warning('实验环境剩余时间不足5分钟，请及时保存工作');
      }

      // 时间到时自动断开
      if (desktopRemainingTime.value === 0) {
        message.error('实验环境已超时关闭');
        stopCountdownTimer();
        // 可以在这里添加自动断开环境的逻辑
      }
    }
  }, 60000); // 60秒 = 1分钟
};

// 停止倒计时器
const stopCountdownTimer = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
};

const toggleFullscreen = async () => {
  try {
    if (!document.fullscreenElement) {
      const element = document.querySelector('.cloud-desktop-container');
      if (element) {
        await element.requestFullscreen();
        isFullscreen.value = true;
        message.success('已进入全屏模式');
      }
    } else {
      await document.exitFullscreen();
      isFullscreen.value = false;
      message.success('已退出全屏模式');
    }
  } catch (error) {
    console.error('全屏切换失败:', error);
    message.error('全屏切换失败');
  }
};

const resetEnvironment = async () => {
  // 重置云桌面环境
  const { Modal } = await import('ant-design-vue');
  Modal.confirm({
    title: '确认重置环境',
    content: '确定要重置云桌面环境吗？这将清除除持久化路径外的所有内容。',
    okText: '确认',
    cancelText: '取消',
    onOk: async () => {
      try {
        const { resetEnvironment: resetEnv } = await import('../../../api/training');
        const response = await resetEnv(desktopEnvironmentId.value || taskId);
        if (response && (response.code === "0000" || response.env_id)) {
          message.success('云桌面环境已重置');
          // 可能需要重新加载 Jupyter 环境
          if (jupyterRef.value) {
            jupyterRef.value.reload();
          }
        } else {
          const errorMsg = response?.message || '重置失败，请稍后重试';
          message.error(errorMsg);
        }
      } catch (error) {
        console.error('重置环境失败:', error);
        const errorMsg = error?.response?.data?.message || error?.message || '重置失败，请稍后重试';
        message.error(errorMsg);
      }
    }
  });
};

const resetTask = () => {
  // 重置任务代码
  message.success('任务代码已重置为初始状态');
};

// VDI环境启动 - 独立的启动函数
const startDesktopEnvironment = async () => {
  console.log('[VDI] 点击启动环境');
  desktopLaunching.value = true;
  await startEnvironment();
  desktopLaunching.value = false;
};

// 环境资源控制相关方法 - 使用新的环境控制系统
const startEnvironment = async () => {
  if (!challengeInfo.value) return;
  
  // 对于代码编辑环境，不需要启动外部环境
  if (challengeInfo.value.envType === 'code' || challengeInfo.value.envType === 'html') {
    message.info('代码编辑器已就绪，可以直接编写代码');
    return;
  }
  
  // 对于需要外部环境的类型，先检查冲突再启动
  try {
    environmentControl.isLaunching.value = true;
    
    // ========== 冲突检测 ==========
    console.log('[环境冲突检测] 开始检查活跃环境...');
    try {
      const activeCheckResponse = await fetch('/api/v1/environments/active', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${getToken() || ''}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (activeCheckResponse.ok) {
        const activeResult = await activeCheckResponse.json();
        console.log('[环境冲突检测] 检查结果:', activeResult);
        
        // 支持两种命名风格：camelCase (API返回) 和 snake_case
        const activePracticeId = activeResult.data?.practiceId || activeResult.data?.practice_id;
        
        if (activeResult.data && activePracticeId && 
            String(activePracticeId) !== String(courseId)) {
          // 检测到不同实践的活跃环境，显示冲突弹窗
          console.log('[环境冲突检测] 发现冲突! 当前实践:', courseId, ', 活跃实践:', activePracticeId);
          
          environmentControl.activeEnvironment.value = {
            id: activeResult.data.id,
            practiceId: String(activePracticeId),
            practiceName: activeResult.data.practiceName || activeResult.data.practice_name || `实践 ${activePracticeId}`,
            environmentType: activeResult.data.environmentType || activeResult.data.environment_type,
            startTime: activeResult.data.startTime || activeResult.data.created_at
          };
          environmentControl.pendingLaunch.value = {
            practiceId: String(courseId),
            practiceName: challengeInfo.value.title || `实践 ${courseId}`,
            environmentType: challengeInfo.value.envType
          };
          environmentControl.showConflictDialog.value = true;
          environmentControl.isLaunching.value = false;
          return; // 不继续启动，等待用户选择
        }
      }
    } catch (e) {
      console.log('[环境冲突检测] 检查失败或无活跃环境，继续启动:', e);
    }
    // ========== 冲突检测结束 ==========
    
    if (challengeInfo.value.envType === 'desktop') {
      // 云桌面环境（Jupyter/VDI）- 使用通用环境启动API
      try {
        // courseId 实际上是 practice_id
        const practiceIdValue = courseId;
        console.log('[Desktop环境] 准备启动, practiceId:', practiceIdValue, 'taskId:', taskId);
        
        // 先创建环境会话记录
        const sessionResponse = await fetch('/api/v1/environments/launch', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken() || ''}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            practiceId: practiceIdValue,
            environmentType: 'desktop'
          })
        });
        
        if (sessionResponse.ok) {
          const sessionResult = await sessionResponse.json();
          console.log('[Desktop环境] 会话创建结果:', sessionResult);
          console.log('[Desktop环境] data内容:', sessionResult.data);
          console.log('[Desktop环境] access_url:', sessionResult.data?.access_url);
          
          // 会话创建成功，显示准备中信息
          message.info('云桌面环境会话已创建，正在准备环境...');
          
          // 设置环境ID
          desktopEnvironmentId.value = sessionResult.data?.id || taskId;
          
          // 如果有真实的VDI URL配置，使用它
          const vdiUrl = sessionResult.data?.access_url || sessionResult.data?.url;
          console.log('[Desktop环境] vdiUrl:', vdiUrl);
          if (vdiUrl) {
            desktopEnvironmentUrl.value = vdiUrl;
            message.success('云桌面环境启动成功');
            console.log('[Desktop环境] 设置desktopEnvironmentUrl:', vdiUrl);
          } else {
            // 没有VDI URL
            console.log('[Desktop环境] 无VDI URL，环境准备中');
            message.warning('云桌面环境正在配置中，请稍后刷新');
          }
          return;
        }
        
        // 会话创建失败
        throw new Error('环境会话创建失败');
      } catch (error) {
        console.error('启动Jupyter环境失败:', error);
        message.error('启动Jupyter环境失败，请重试');
      }
    } else if (challengeInfo.value.envType === 'shell') {
      // Shell环境 - 也需要调用环境启动API创建会话
      try {
        // courseId 实际上是 practice_id
        const practiceIdValue = courseId;
        console.log('[Shell环境] 准备创建会话, practiceId:', practiceIdValue, 'userId:', userStore.userId);
        
        const response = await fetch('/api/v1/environments/launch', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken() || ''}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            practiceId: practiceIdValue,
            environmentType: 'shell'
          })
        });

        console.log('[Shell环境] API响应状态:', response.status);
        
        if (response.ok) {
          const result = await response.json();
          console.log('[Shell环境] API响应:', result);
          if (result.code === '0000') {
            console.log('Shell环境会话创建成功', result.data);
          } else {
            console.warn('[Shell环境] 会话创建返回非成功码:', result);
          }
        } else {
          const errorText = await response.text();
          console.error('[Shell环境] API错误:', response.status, errorText);
        }
      } catch (e) {
        console.error('创建Shell环境会话失败:', e);
      }
      message.success('命令行环境已就绪');
    } else {
      // 其他环境类型
      message.warning('该环境类型暂不支持');
    }
  } finally {
    environmentControl.isLaunching.value = false;
  }
};

// 处理 Jupyter 加载成功
const handleJupyterLoaded = () => {
  console.log('Jupyter 环境加载成功');
  // 启动倒计时器
  startCountdownTimer();
};

// 处理 VDI 云桌面加载成功
const handleVdiLoaded = () => {
  console.log('[VDI] 云桌面环境加载成功');
  message.success('云桌面环境已就绪');
  // 启动倒计时器
  startCountdownTimer();
  // 重置启动状态
  desktopLaunching.value = false;
};

// 处理 Jupyter 加载错误
const handleJupyterError = (error: string) => {
  console.error('Jupyter 环境加载失败:', error);
  message.error('云桌面环境加载失败，请重试');
  // 可选：重置环境 URL，允许用户重新启动
  desktopEnvironmentUrl.value = '';
};

// 生命周期钩子
// 快捷键处理
const handleKeyboard = (event: KeyboardEvent) => {
  // Ctrl/Cmd + Enter: 评测
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault();
    if (!evaluating.value) {
      handleEvaluate();
      message.info('⌨️ 快捷键触发评测');
    }
  }
  
  // Ctrl/Cmd + S: 保存
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault();
    autoSaveCode();
    message.success('💾 代码已保存');
  }
  
  // Ctrl/Cmd + P: 切换预览 (仅HTML任务)
  if ((event.ctrlKey || event.metaKey) && event.key === 'p' && canShowPreview.value) {
    event.preventDefault();
    togglePreview();
    message.info(showPreview.value ? '👁️ 预览已开启' : '🙈 预览已关闭');
  }
};

const restoreSavedCodeLater = () => {
  setTimeout(() => {
    if (activeFile.value) {
      restoreSavedCode();
    }
  }, 500);
};

watch(
  () => [route.params.courseId, route.params.taskId],
  async ([newCourseId, newTaskId], [oldCourseId, oldTaskId]) => {
    if (newCourseId === oldCourseId && newTaskId === oldTaskId) return;
    syncRouteParams();
    resetChallengeStateForRoute();
    await fetchChallengeInfo();
    restoreSavedCodeLater();
  }
);

onMounted(async () => {
  syncRouteParams();
  checkLoginStatus(); // 检查用户是否已登录
  
  // 调试：检查环境控制初始状态
  console.log('[onMounted] 环境控制初始状态:', {
    isLaunching: environmentControl.isLaunching.value,
    isStopping: environmentControl.isStopping?.value,
    isSwitching: environmentControl.isSwitching?.value,
    isProcessing: environmentControl.isProcessing.value
  });
  
  // 重置环境控制状态
  environmentControl.isLaunching.value = false;
  console.log('[onMounted] 已重置 isLaunching 为 false');

  // 检查剪切板支持
  isClipboardSupported.value = typeof navigator !== 'undefined' && 'clipboard' in navigator;

  // 直接加载挑战信息，环境控制在需要时处理
  await fetchChallengeInfo();
  
  // 调试：加载完成后检查状态
  console.log('[onMounted] fetchChallengeInfo 完成后环境控制状态:', {
    isLaunching: environmentControl.isLaunching.value,
    isProcessing: environmentControl.isProcessing.value,
    envType: challengeInfo.value?.envType
  });
  
  // 尝试恢复自动保存的代码
  restoreSavedCodeLater();
  
  // 添加快捷键监听
  document.addEventListener('keydown', handleKeyboard);
});

// 组件卸载时清理资源
onUnmounted(() => {
  // 清理倒计时器
  stopCountdownTimer();

  // 清理其他定时器
  if (desktopTimeUpdateTimer) {
    clearTimeout(desktopTimeUpdateTimer);
    desktopTimeUpdateTimer = null;
  }
  
  // 清理自动保存定时器并执行最终保存
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
  
  // 组件卸载时保存当前代码
  if (activeFile.value?.content) {
    autoSaveCode();
  }
  
  // 清理预览更新定时器
  if (previewUpdateTimer) {
    clearTimeout(previewUpdateTimer);
    previewUpdateTimer = null;
  }
  
  // 清理快捷键监听
  document.removeEventListener('keydown', handleKeyboard);
});
</script>

<style scoped>
/* 选择题对错标记样式 */
.option-correct :deep(.ant-radio-wrapper),
.option-correct :deep(.ant-checkbox-wrapper) {
  color: #52c41a !important;
  font-weight: 500;
}

.option-wrong :deep(.ant-radio-wrapper),
.option-wrong :deep(.ant-checkbox-wrapper) {
  color: #ff4d4f !important;
  text-decoration: line-through;
}

.option-missed :deep(.ant-radio-wrapper),
.option-missed :deep(.ant-checkbox-wrapper) {
  color: #faad14 !important;
  font-weight: 500;
}

/* 评测结果面板动画 */
.evaluation-result-panel {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 金币奖励动画 */
@keyframes coinBounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

.coin-reward {
  animation: coinBounce 1s ease infinite;
}

.challenge-detail-page {
  min-height: 100vh;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  padding: 0 20px;
  height: auto;
  line-height: normal;
  z-index: 10;
}

.header-content {
  display: flex;
  align-items: center;
  height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  margin-right: 40px;
}

.logo img {
  height: 30px;
  margin-right: 10px;
}

.logo span {
  font-size: 18px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.nav {
  flex: 1;
}

.user-info {
  margin-left: auto;
}

.page-content {
  flex: 1;
  overflow: hidden;
  padding: 0;
  background-color: #f0f2f5;
}

.challenge-container {
  height: calc(100vh - 60px);
  display: flex;
}

/* 任务手册区样式 */
.task-manual-area {
  flex: 0 0 400px;
  max-width: 600px;
  min-width: 320px;
  height: 100%;
  border-right: 1px solid #e8e8e8;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: flex-basis 0.3s ease;
}

.task-manual-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.task-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  margin: 0 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.task-tabs {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

:deep(.ant-tabs-content) {
  height: 100%;
  overflow: auto;
  background-color: #fff;
  border-radius: 0 0 4px 4px;
}

:deep(.ant-tabs-nav) {
  margin-bottom: 0 !important;
}

:deep(.ant-tabs-nav::before) {
  border-bottom: none !important;
}

/* ============ 过关任务区域样式 ============ */
.task-content-wrapper {
  padding: 20px;
  overflow: auto;
  height: 100%;
  background: linear-gradient(135deg, #fafbfc 0%, #ffffff 100%);
}

.task-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-tips {
  margin-bottom: 20px;
}

.tips-alert {
  border-radius: 8px;
  border-left: 4px solid #1890ff;
  background: linear-gradient(135deg, #e6f4ff 0%, #ffffff 100%);
}

.tips-content {
  padding: 4px 0;
}

.tips-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 12px 0;
}

.tips-list li {
  padding: 4px 0;
  color: #595959;
  display: flex;
  align-items: center;
}

.view-example-btn {
  padding: 0;
  height: auto;
  font-size: 13px;
}

.task-description {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  line-height: 1.8;
}

/* ============ 参考答案区域样式 ============ */
.reference-answer-wrapper {
  padding: 20px;
  overflow: auto;
  height: 100%;
  background: linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%);
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #1890ff;
}

.answer-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.answer-actions {
  display: flex;
  gap: 8px;
}

.answer-code-container {
  position: relative;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.code-language-tag {
  position: absolute;
  top: 8px;
  right: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: #888;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  z-index: 10;
}

.answer-code {
  background: #fafafa;
  margin: 0;
  padding: 40px 20px 20px 20px;
  overflow-x: auto;
  font-size: 14px;
  line-height: 1.6;
}

.answer-code code {
  color: #d4d4d4;
  font-family: 'Fira Code', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', monospace;
  white-space: pre;
  display: block;
}

.answer-explanation {
  margin-top: 20px;
  background: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 8px;
  padding: 16px;
}

.explanation-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 8px;
}

.explanation-content {
  color: #8c6d1f;
  font-size: 14px;
  line-height: 1.6;
}

.explanation-content p {
  margin: 0;
}

/* Tab标题样式 */
.tab-title {
  display: flex;
  align-items: center;
  font-weight: 500;
}

:deep(.ant-tabs-tabpane) {
  padding: 0;
  border-top: none;
}

/* 实验环境区样式 */
.practice-environment-area {
  flex: 1;
  min-width: 600px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.editor-toolbar {
  padding: 8px 16px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fafafa;
}

.file-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.editor-actions {
  display: flex;
  gap: 10px;
}

.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.file-explorer-section {
  width: 220px;
  border-right: 1px solid #e8e8e8;
  overflow: auto;
}

.monaco-editor-section {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.editor-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
  background: rgba(255, 255, 255, 0.9);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.editor-error {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  max-width: 80%;
}

/* 评测区样式 */
.evaluation-area {
  height: 250px;
  background-color: #fff;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.evaluation-header {
  padding: 8px 16px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fafafa;
}

.test-cases {
  padding: 16px;
  overflow: auto;
  max-height: 200px;
}

.test-case-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.test-input, .test-output {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 10px;
}

.test-title {
  font-weight: 500;
  margin-bottom: 5px;
}

.hidden-test-cases {
  margin-top: 10px;
}

.evaluation-results {
  flex: 1;
  overflow: auto;
  padding: 0 16px 16px;
}

.result-details {
  width: 100%;
}

.result-card {
  margin-bottom: 10px;
}

.passed {
  border-color: #52c41a;
}

.failed {
  border-color: #f5222d;
}

.hidden {
  border-color: #faad14;
}

.result-comparison {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-actual, .result-expected {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 10px;
}

.result-error {
  margin-top: 10px;
}

/* Markdown样式 */
:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  padding: 0;
  margin: 0;
  background-color: transparent;
}

:deep(.markdown-body h1) {
  font-size: 24px;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

:deep(.markdown-body h2) {
  font-size: 20px;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

:deep(.markdown-body h3) {
  font-size: 18px;
}

:deep(.markdown-body p) {
  margin-top: 0;
  margin-bottom: 16px;
}

:deep(.markdown-body code) {
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-family: SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace;
  font-size: 85%;
  margin: 0;
  padding: 0.2em 0.4em;
}

:deep(.markdown-body pre) {
  background-color: #f6f8fa;
  border-radius: 3px;
  overflow: auto;
  padding: 16px;
}

:deep(.markdown-body pre code) {
  background-color: transparent;
  padding: 0;
}

.no-gap {
  margin: 0;
  padding: 0;
}

.no-gap :deep(.ant-typography) {
  margin-bottom: 0;
}

.monaco-editor-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

/* 命令行终端样式 */
.terminal-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #000000;
  border-bottom: none;
}

.terminal-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 500px;
  max-height: 100%;
  background-color: #000000;
}

/* 云桌面样式 */
.cloud-desktop-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.desktop-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 600px;
  background-color: #f0f0f0;
  position: relative;
}

.desktop-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fafafa;
}

/* VDI 云桌面容器 */
.vdi-container {
  flex: 1;
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.vdi-iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
  background-color: #f5f5f5;
}

/* Jupyter 环境容器 */
.desktop-area :deep(.jupyter-container) {
  width: 100%;
  height: 100%;
}

/* 全屏模式样式 */
.cloud-desktop-container:fullscreen {
  background-color: #fff;
}

.cloud-desktop-container:fullscreen .desktop-area {
  height: 100vh;
}

.cloud-desktop-container:fullscreen .editor-toolbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background-color: rgba(250, 250, 250, 0.95);
  backdrop-filter: blur(10px);
}

/* 环境冲突弹窗样式 */
.env-conflict-content {
  padding: 20px 0;
}

.conflict-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .task-manual-area {
    flex: 0 0 350px;
  }
  
  .practice-environment-area {
    min-width: 500px;
  }
}

@media (max-width: 1024px) {
  .challenge-container {
    flex-direction: column;
    height: auto;
    min-height: calc(100vh - 60px);
  }
  
  .task-manual-area {
    flex: none;
    width: 100%;
    max-width: 100%;
    height: 40vh;
    min-height: 300px;
    border-right: none;
    border-bottom: 1px solid #e8e8e8;
  }
  
  .practice-environment-area {
    flex: none;
    width: 100%;
    min-width: 100%;
    min-height: 60vh;
  }
  
  .editor-container,
  .terminal-container,
  .cloud-desktop-container {
    min-height: 400px;
  }
}

@media (max-width: 768px) {
  .task-manual-area {
    height: 35vh;
    min-height: 250px;
  }
  
  .monaco-editor-container {
    min-height: 350px;
  }
  
  .editor-actions {
    flex-wrap: wrap;
  }
  
  .task-navigation {
    flex-direction: column;
    gap: 10px;
  }
  
  .task-title {
    order: -1;
    margin: 0 0 10px 0;
  }
}

/* 剪切板工具样式 */
.clipboard-content {
  padding: 16px 0;
}

.clipboard-description {
  color: #666;
  margin-bottom: 16px;
  line-height: 1.5;
}

.clipboard-textarea {
  margin-bottom: 16px;
}

.clipboard-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.clipboard-warning {
  margin-top: 16px;
}
</style> 
