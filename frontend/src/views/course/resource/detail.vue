<template>
  <div class="detail-page copilot-theme">
    <!-- 课程顶部信息 Banner -->
    <div class="course-banner" :style="{ background: course?.cover || 'linear-gradient(135deg, #1890ff, #36cfc9)' }">
      <div class="responsive-container banner-wrapper">
        <div class="course-img">
          <img :src="courseDetail?.cover_url || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22200%22 height=%22200%22 viewBox=%220 0 200 200%22%3E%3Crect fill=%22%231890ff%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 font-size=%2240%22 fill=%22white%22 text-anchor=%22middle%22 dy=%22.3em%22%3E📚%3C/text%3E%3C/svg%3E'" alt="课程教材" />
        </div>
        <div class="course-info">
          <h1 class="course-title">{{ courseDetail?.title }}</h1>
          <div class="course-meta">
            <div class="meta-item">
              <span class="label">章节数</span>
              <span class="value">{{ courseDetail?.chapters?.length || 0 }}</span>
            </div>
            <div class="meta-item">
              <span class="label">实践数</span>
              <span class="value">{{ courseDetail?.practices?.length || 0 }}</span>
            </div>
            <div class="meta-item">
              <span class="label">课程方向</span>
              <span class="value">{{ courseDetail?.direction || '未知' }}</span>
            </div>
          </div>
          <div class="course-actions">
            <a-button type="primary" class="create-btn" @click="openCreateModal">创建课堂</a-button>
            <a-button class="add-btn" @click="openAddToClassroomModal">添加到课堂</a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 课程详情区域 -->
    <a-layout has-sider class="course-detail-layout">
      <!-- 左侧导航栏 -->
      <a-layout-sider
        :width="200"
        class="course-sider-left"
      >
        <div class="left-sidebar">
          <a-menu
            mode="inline"
            v-model:selectedKeys="activeSection"
            class="section-menu"
          >
            <a-menu-item key="experiments" @click="changeSection('experiments')">
              <template #icon><ExperimentOutlined /></template>
              课程实验
            </a-menu-item>
            <a-menu-item key="syllabus" @click="changeSection('syllabus')">
              <template #icon><ProfileOutlined /></template>
              教学大纲
            </a-menu-item>
            <a-menu-item key="resources" @click="changeSection('resources')">
              <template #icon><FolderOutlined /></template>
              教学资源
            </a-menu-item>
            <a-menu-item key="exams" @click="changeSection('exams')">
              <template #icon><FormOutlined /></template>
              课程考核
            </a-menu-item>
          </a-menu>
        </div>
      </a-layout-sider>
      
      <!-- 主内容区 -->
      <a-layout class="course-main-layout">
        <a-layout-content class="course-content-area">
          <!-- 加载状态 -->
          <div v-if="loading" style="text-align: center; padding: 100px 0;">
            <a-spin size="large" tip="正在加载课程详情..."/>
          </div>
          
          <!-- 错误状态 -->
          <div v-else-if="loadError" style="text-align: center; padding: 100px 0;">
            <a-result
              status="error"
              title="加载失败"
              :sub-title="loadError"
            >
              <template #extra>
                <a-button type="primary" @click="retryLoad">
                  重新加载
                </a-button>
              </template>
            </a-result>
          </div>
          
          <!-- 正常内容 -->
          <template v-else>

          <!-- 课程实验内容（默认视图）-->
          <div v-if="activeSection.includes('experiments')" class="content-section">
            <h2>课程实验</h2>

            <!-- 课程概述 -->
            <a-card class="intro-card" title="课程概述">
              <div class="course-description markdown-body" v-html="renderedDescription"></div>
            </a-card>

            <!-- 课程特色 -->
            <a-card class="intro-card" title="课程特色" style="margin-top: 16px;">
              <a-row :gutter="[16, 16]">
                <a-col :span="12">
                  <div class="feature-item">
                    <CheckCircleOutlined class="feature-icon" />
                    <div class="feature-content">
                      <h4>实战导向</h4>
                      <p>基于真实行业案例，培养实际应用能力</p>
                    </div>
                  </div>
                </a-col>
                <a-col :span="12">
                  <div class="feature-item">
                    <TrophyOutlined class="feature-icon" />
                    <div class="feature-content">
                      <h4>闯关式学习</h4>
                      <p>游戏化学习体验，完成任务获得金币奖励</p>
                    </div>
                  </div>
                </a-col>
                <a-col :span="12">
                  <div class="feature-item">
                    <RocketOutlined class="feature-icon" />
                    <div class="feature-content">
                      <h4>循序渐进</h4>
                      <p>从基础到进阶，系统化的知识体系</p>
                    </div>
                  </div>
                </a-col>
                <a-col :span="12">
                  <div class="feature-item">
                    <TeamOutlined class="feature-icon" />
                    <div class="feature-content">
                      <h4>名师团队</h4>
                      <p>知名高校教师授课，专业有保障</p>
                    </div>
                  </div>
                </a-col>
              </a-row>
            </a-card>

            <!-- 先修要求 -->
            <a-card class="intro-card" title="先修要求" style="margin-top: 16px;">
              <a-alert
                message="建议学习本课程前具备以下知识基础"
                type="info"
                show-icon
                style="margin-bottom: 12px;"
              />
              <ul class="prerequisites-list">
                <li>基本的计算机操作能力</li>
                <li>具备一定的逻辑思维能力</li>
                <li v-if="courseDetail?.direction === '编程语言'">了解基本的编程概念（可选）</li>
                <li v-if="courseDetail?.direction === '大数据'">掌握至少一门编程语言基础</li>
                <li v-if="courseDetail?.direction === '人工智能'">具备Python编程基础和数学基础</li>
              </ul>
            </a-card>

            <!-- 课程结构统计 -->
            <a-card class="intro-card" title="课程结构" style="margin-top: 16px;">
              <a-descriptions bordered :column="2">
                <a-descriptions-item label="课程章节">
                  {{ (Array.isArray(courseDetail?.chapters) ? courseDetail.chapters.length : (courseDetail?.chapters || 0)) }} 章
                </a-descriptions-item>
                <a-descriptions-item label="实践模块">
                  {{ courseDetail?.practices?.length || 0 }} 个
                </a-descriptions-item>
                <a-descriptions-item label="总关卡数">
                  {{ (courseDetail?.practices || []).reduce((sum, p) => sum + (p.task_count || 0), 0) }} 个
                </a-descriptions-item>
                <a-descriptions-item label="总金币数">
                  {{ (courseDetail?.practices || []).reduce((sum, p) => sum + (p.coin || 0), 0) }}
                </a-descriptions-item>
                <a-descriptions-item label="教学资源">
                  {{ courseDetail?.resources?.length || courseDetail?.material_resources_count || 0 }} 个文件
                </a-descriptions-item>
                <a-descriptions-item label="考核试卷">
                  {{ courseDetail?.assessments?.length || courseDetail?.material_assessments_count || 0 }} 份
                </a-descriptions-item>
                <a-descriptions-item label="课程方向">
                  {{ courseDetail?.direction || '未分类' }}
                </a-descriptions-item>
                <a-descriptions-item label="难度级别">
                  <a-tag :color="getDifficultyColor(courseDetail?.difficulty)">
                    {{ getDifficultyText(courseDetail?.difficulty) }}
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
            
            <!-- 课程章节 -->
            <a-card class="intro-card" title="课程章节" style="margin-bottom: 16px;">
              <a-list 
                v-if="courseDetail?.chapters && courseDetail.chapters.length > 0"
                :data-source="courseDetail.chapters" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item, index }">
                  <a-list-item 
                    class="chapter-item"
                    :class="{ 'selected': selectedChapterId === item.id }"
                    @click="handleChapterClick(item.id)"
                    style="cursor: pointer;"
                  >
                    <a-list-item-meta>
                      <template #avatar>
                        <a-avatar 
                          :style="{ 
                            backgroundColor: selectedChapterId === item.id ? '#52c41a' : '#1890ff' 
                          }"
                        >
                          {{ index + 1 }}
                        </a-avatar>
                      </template>
                      <template #title>
                        <span :style="{ fontWeight: selectedChapterId === item.id ? 'bold' : 'normal' }">
                          {{ item.title }}
                        </span>
                      </template>
                      <template #description>
                        实验数量：{{ item.experiment_count || 0 }} 个
                        <span v-if="selectedChapterId === item.id" style="color: #52c41a; margin-left: 8px;">
                          ✓ 已选中
                        </span>
                      </template>
                    </a-list-item-meta>
                  </a-list-item>
                </template>
              </a-list>
              <a-empty v-else description="暂无章节信息" />
            </a-card>

            <!-- 课程实验列表 -->
            <a-card class="intro-card">
              <template #title>
                <span>微型实验</span>
                <span v-if="selectedChapterId" style="color: #52c41a; font-size: 14px; margin-left: 8px;">
                  (已筛选)
                </span>
                <a-button 
                  v-if="selectedChapterId" 
                  type="link" 
                  size="small" 
                  @click="selectedChapterId = null"
                  style="margin-left: 8px;"
                >
                  显示全部
                </a-button>
              </template>
              <div v-if="filteredPractices && filteredPractices.length > 0" class="course-experiments">
                <a-collapse v-model:activeKey="expandedPractices" ghost>
                  <a-collapse-panel
                    v-for="practice in filteredPractices"
                    :key="practice.id"
                    :header="`${practice.title} (${practice.task_count}个关卡)`"
                  >
                    <template #extra>
                      <div>
                        <a-button type="link" size="small" @click="goToPracticeDetail(practice.id)">查看详情</a-button>
                        <a-tag :color="getDifficultyColor(practice.difficulty)" style="margin-left: 8px;">{{ getDifficultyText(practice.difficulty) }}</a-tag>
                      </div>
                    </template>

                    <div class="practice-description" style="margin-bottom: 16px;">
                      <p>{{ practice.summary }}</p>
                      <p style="color: #666; font-size: 12px;">总计 {{ practice.coin }} 金币</p>
                    </div>

                    <!-- 关卡列表 -->
                    <div class="challenge-list">
                      <div
                        v-for="task in practice.tasks"
                        :key="task.id"
                        class="challenge-item"
                      >
                        <div class="challenge-info">
                          <span class="challenge-number">{{ task.title }}</span>
                          <span class="challenge-reward">{{ task.coin }} 金币</span>
                          <a-tag :color="getDifficultyColor(task.difficulty)" size="small" style="margin-left: 8px;">
                            {{ getDifficultyText(task.difficulty) }}
                          </a-tag>
                        </div>
                        <a-button type="primary" size="small" @click="viewChallenge(practice.id, task.id)">
                          开启挑战
                        </a-button>
                      </div>
                    </div>
                  </a-collapse-panel>
                </a-collapse>
                
                <!-- 实践统计 -->
                <a-divider />
                <div class="practice-stats">
                  <a-row :gutter="16">
                    <a-col :span="6">
                      <a-statistic title="实践模块" :value="courseDetail?.practices?.length || 0" suffix="个" />
                    </a-col>
                    <a-col :span="6">
                      <a-statistic title="总关卡数" :value="(courseDetail?.practices || []).reduce((sum, p) => sum + (p.task_count || 0), 0)" suffix="个" />
                    </a-col>
                    <a-col :span="6">
                      <a-statistic title="总金币数" :value="(courseDetail?.practices || []).reduce((sum, p) => sum + (p.coin || 0), 0)" />
                    </a-col>
                    <a-col :span="6">
                      <a-statistic title="难度级别" :value="getDifficultyText(courseDetail.difficulty)" />
                    </a-col>
                  </a-row>
                </div>
              </div>
              <a-empty v-else description="暂无实践课程" />
            </a-card>
          </div>

          <!-- 教学大纲内容 -->
          <div v-if="activeSection.includes('syllabus')" class="content-section">
            <h2>教学大纲</h2>
            <a-card>
              <div class="syllabus-content">
                <div v-if="syllabusSummary" class="syllabus-summary">
                  <a-typography-title :level="4">智能摘要</a-typography-title>
                  <a-typography-paragraph>
                    {{ syllabusSummary.brief }}
                  </a-typography-paragraph>
                  <a-divider />
                  <div class="summary-highlights" v-if="syllabusSummary.highlights?.length">
                    <a-typography-title :level="5">学习亮点</a-typography-title>
                    <a-list :data-source="syllabusSummary.highlights">
                      <template #renderItem="{ item }">
                        <a-list-item>
                          <a-list-item-meta
                            :title="item.title"
                            :description="item.description"
                          />
                          <template #extra>
                            <a-tag color="cyan">{{ item.tag || '亮点' }}</a-tag>
                          </template>
                        </a-list-item>
                      </template>
                    </a-list>
                  </div>
                </div>
                <div class="markdown-body" v-html="renderedSyllabus"></div>
              </div>
            </a-card>
          </div>

          <!-- 教学资源内容 -->
          <div v-if="activeSection.includes('resources')" class="content-section">
            <h2>教学资源</h2>
            <a-card>
              <a-alert 
                message="在线预览" 
                description="点击资源标题即可在线预览文件内容，支持 PDF、PPT、Word、Excel、视频等多种格式" 
                type="info" 
                show-icon 
                style="margin-bottom: 16px;"
              />
              
              <a-list 
                :data-source="courseDetail?.resources || []" 
                item-layout="horizontal"
                :locale="{ emptyText: '暂无教学资源' }"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta>
                      <template #title>
                        <a @click="previewResource(item)" class="resource-link">
                          <FileOutlined style="margin-right: 8px;" />
                          {{ item.title }}
                        </a>
                      </template>
                      <template #description>
                        <span>{{ getResourceTypeText(item.resource_type) }} · 教学材料</span>
                      </template>
                    </a-list-item-meta>
                    <template #extra>
                      <a-space>
                        <a-tag :color="getResourceTypeColor(item.resource_type)">
                          {{ getResourceTypeText(item.resource_type) }}
                        </a-tag>
                        <a-button 
                          type="link" 
                          size="small"
                          @click="previewResource(item)"
                        >
                          <EyeOutlined /> 预览
                        </a-button>
                      </a-space>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
              
              <!-- 资源统计信息 -->
              <a-divider />
              <div class="resource-stats">
                <a-row :gutter="16">
                  <a-col :span="6">
                    <a-statistic 
                      title="资源总数" 
                      :value="courseDetail?.resources?.length || 0" 
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic 
                      title="PDF文档" 
                      :value="courseDetail?.resources?.filter(r => r.resource_type?.toLowerCase().includes('pdf')).length || 0" 
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic 
                      title="PPT课件" 
                      :value="courseDetail?.resources?.filter(r => r.resource_type?.toLowerCase().includes('ppt')).length || 0" 
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic 
                      title="视频教学" 
                      :value="courseDetail?.resources?.filter(r => r.resource_type?.toLowerCase().includes('video') || r.resource_type?.toLowerCase().includes('mp4')).length || 0" 
                    />
                  </a-col>
                </a-row>
              </div>
            </a-card>
          </div>

          <!-- 课程考核内容 -->
          <div v-if="activeSection.includes('exams')" class="content-section">
            <h2>课程考核</h2>
            <a-card>
              <a-alert 
                v-if="userStore.userInfo.role === 'teacher' || userStore.userInfo.role === 'admin'"
                message="教师权限" 
                description="您可以预览试卷内容。学生只有在正式考试时才能查看试题。" 
                type="success" 
                show-icon 
                style="margin-bottom: 16px;"
              />
              <a-alert 
                v-else
                message="权限提示" 
                description="试卷内容仅在正式考试时向学生开放，此处仅展示试卷列表。" 
                type="warning" 
                show-icon 
                style="margin-bottom: 16px;"
              />
              
              <a-list 
                :data-source="courseDetail?.assessments || []" 
                item-layout="horizontal"
                :locale="{ emptyText: '暂无考核试卷' }"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta>
                      <template #title>
                        <a 
                          v-if="userStore.userInfo.role === 'teacher' || userStore.userInfo.role === 'admin'"
                          @click="previewExam(item)" 
                          class="exam-link"
                        >
                          <FormOutlined style="margin-right: 8px;" />
                          {{ item.title }}
                        </a>
                        <span v-else class="exam-title-disabled">
                          <FormOutlined style="margin-right: 8px;" />
                          {{ item.title }}
                          <a-tag color="orange" size="small" style="margin-left: 8px;">考试时开放</a-tag>
                        </span>
                      </template>
                      <template #description>
                        <span>{{ item.assessment_type }} · 考核试卷</span>
                      </template>
                    </a-list-item-meta>
                    <template #extra>
                      <a-space>
                        <a-tag color="blue">{{ item.assessment_type }}</a-tag>
                        <a-button 
                          v-if="userStore.userInfo.role === 'teacher' || userStore.userInfo.role === 'admin'"
                          type="link" 
                          size="small"
                          @click="previewExam(item)"
                        >
                          <EyeOutlined /> 预览试卷
                        </a-button>
                        <a-tooltip v-else title="学生无权预览">
                          <a-button type="link" size="small" disabled>
                            <EyeOutlined /> 预览试卷
                          </a-button>
                        </a-tooltip>
                      </a-space>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
              
              <!-- 考核统计信息 -->
              <a-divider />
              <div class="exam-stats">
                <a-row :gutter="16">
                  <a-col :span="8">
                    <a-statistic 
                      title="试卷总数" 
                      :value="courseDetail?.assessments?.length || 0" 
                    />
                  </a-col>
                  <a-col :span="8">
                    <a-statistic 
                      title="期中考试" 
                      :value="courseDetail?.assessments?.filter(e => e.assessment_type?.includes('期中')).length || 0" 
                    />
                  </a-col>
                  <a-col :span="8">
                    <a-statistic 
                      title="期末考试" 
                      :value="courseDetail?.assessments?.filter(e => e.assessment_type?.includes('期末')).length || 0" 
                    />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic title="考试配置" value="完整" />
                  </a-col>
                  <a-col :span="6">
                    <a-statistic title="自动组卷" value="支持" />
                  </a-col>
                </a-row>
              </div>
            </a-card>
          </div>
          
          <!-- 资源调试面板（仅在debug模式下显示） -->
          <ResourceDebugPanel v-if="courseId" :courseId="parseInt(courseId)" />
          </template>
        </a-layout-content>
        
        <!-- 右侧边栏 -->
        <a-layout-sider
          :width="260"
          class="course-sider-right"
        >
          <div class="right-sidebar">
            <!-- 团队信息 -->
            <a-card v-if="courseDetail?.teaching_team_name" title="开课团队" class="info-card">
              <div class="team-list">
                <div class="team-item">
                  <a-avatar :size="56" style="background-color: #f56a00">
                    <template #icon>{{ courseDetail.teaching_team_name?.charAt(0) }}<UserOutlined /></template>
                  </a-avatar>
                  <div class="team-name">{{ courseDetail.teaching_team_name }}</div>
                </div>
              </div>
            </a-card>

            <!-- 推荐教师 -->
            <a-card v-if="courseDetail?.lead_teacher_name" title="推荐教师" class="info-card">
              <div class="teacher-info">
                <a-avatar v-if="courseDetail.lead_teacher_avatar" :size="64" :src="courseDetail.lead_teacher_avatar" />
                <a-avatar v-else :size="64" style="background-color: #1890ff">
                  <EyeOutlined />
                  <span style="font-size: 18px;">Preview</span>
                </a-avatar>
                <div class="teacher-meta">
                  <div class="teacher-name">{{ courseDetail.lead_teacher_name }}</div>
                  <div class="teacher-title">{{ courseDetail.lead_teacher_university }}</div>
                </div>
              </div>
            </a-card>
          </div>
        </a-layout-sider>
      </a-layout>
    </a-layout>
    
    <!-- 创建课堂弹窗 -->
    <a-modal
      v-model:open="createModalVisible"
      title="创建课堂"
      @ok="handleCreateConfirm"
      :confirm-loading="confirmLoading"
      :maskClosable="modalMaskClosable"
    >
      <a-form :model="formState" layout="vertical" ref="roomformRef">
        <a-form-item label="课堂名称" name="name" required :rules="[{ required: true, message: '请输入课堂名称' }]">
          <a-input v-model:value="formState.name" placeholder="课堂名称" />
        </a-form-item>
		<a-form-item label="学年" name="academic_year">
		  <a-input v-model:value="formState.academic_year" placeholder="例如: 2024-2025" />
		</a-form-item>
		<a-form-item label="学期" name="semester" required :rules="[{ required: true, message: '请输入学期' }]">
		  <a-input v-model:value="formState.semester" placeholder="学期" />
		</a-form-item>
        <a-form-item label="学分" name="credit" required :rules="[{ required: true, message: '请输入学分' }]">
          <a-input-number v-model:value="formState.credit" placeholder="例如: 4" :min="1" :max="10" style="width: 100%" />
        </a-form-item>
        <a-form-item label="开始时间" name="start_date" required :rules="[{ required: true, message: '请选择开始时间' }]">
          <a-date-picker 
            format="YYYY-MM-DD" 
            v-model:value="formState.start_date" 
            style="width: 100%" 
            value-format="YYYY-MM-DD"
          />
        </a-form-item>
        <a-form-item label="结束时间" name="end_date" required :rules="[{ required: true, message: '请选择结束时间' }]">
          <a-date-picker 
            format="YYYY-MM-DD" 
            v-model:value="formState.end_date" 
            style="width: 100%" 
            value-format="YYYY-MM-DD"
          />
        </a-form-item>
        <a-form-item label="同步设置">
          <a-checkbox v-model:checked="formState.sync_resources_from_source" style="display: block; margin-bottom: 8px;">
            同步教学资源
          </a-checkbox>
          <a-checkbox v-model:checked="formState.sync_assessments_from_source">
            同步课程考核
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 添加到课堂模态框 -->
    <a-modal
      v-model:open="addToClassroomModalVisible"
      title="添加到课堂"
      @ok="handleAddToClassroom"
      :confirm-loading="addToClassroomLoading"
      :maskClosable="modalMaskClosable"
    >
      <div style="margin-bottom: 16px;">
        <p>选择要添加课程的课堂：</p>
      </div>
      <a-select
        v-model:value="selectedClassroomId"
        placeholder="请选择课堂"
        style="width: 100%"
        :loading="classroomListLoading"
      >
        <a-select-option
          v-for="classroom in classroomList"
          :key="classroom.id"
          :value="classroom.id"
        >
          {{ classroom.name }}
        </a-select-option>
      </a-select>
    </a-modal>

    <!-- 资源预览组件 -->
    <ResourcePreview
      v-model:visible="previewModalVisible"
      :resource="currentPreviewResource"
      :key="currentPreviewResource?.id"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watchEffect, watch, nextTick } from 'vue';
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import 'github-markdown-css/github-markdown.css'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import { materialDetail } from '@/api/cmaterial';
import { addClassRoomByCourse, techerClassRooms, addClassRoomPractice } from '@/api/classrooms';
import { useUserStore } from '@/stores/user';
import { 
  AppstoreOutlined,
  ProfileOutlined,
  FolderOutlined,
  FormOutlined,
  FileOutlined,
  DownloadOutlined,
  UserOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  RocketOutlined,
  TeamOutlined,
  EyeOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue';
// 使用 materialDetail 替代 getCourseDetail
// import { getCourseDetail } from '@/api/course';
import type { CourseResource } from '@/types/course';
import type { ValidateErrorEntity } from 'ant-design-vue/es/form';
import TeachingResourceLibrary from './teaching-resource-library.vue';
import ResourceDebugPanel from '@/components/debug/ResourceDebugPanel.vue';
import ResourcePreview from '@/components/common/ResourcePreview.vue';

// 路由参数
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const courseId = route.params.id as string;

// 课程数据
const course = ref<CourseResource | null>(null);
const courseDetail = ref<CourseDetail | null>(null);
const activeSection = ref<string[]>(['experiments']); // 默认显示课程实验
const roomformRef = ref();
const syllabusSummary = ref<any>(null)
const syllabusContent = ref<string>('') // 教学大纲内容
const loading = ref(false) // 加载状态
const loadError = ref<string | null>(null) // 错误信息
const selectedChapterId = ref<number | null>(null) // 选中的章节ID

const markdownRenderer = new MarkdownIt({
  html: false,
  linkify: true, // 启用linkify来处理Markdown链接
  typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
    }
    return `<pre class="hljs"><code>${MarkdownIt().utils.escapeHtml(str)}</code></pre>`
  }
})

// 自定义链接渲染，确保API链接能正确打开
markdownRenderer.renderer.rules.link_open = function(tokens, idx, options, env, self) {
  const token = tokens[idx]
  const href = token.attrGet('href')

  // 如果是API链接，添加target="_blank"和rel="noopener noreferrer"
  if (href && (href.startsWith('/api/v1/') || href.includes('api/v1/'))) {
    token.attrSet('target', '_blank')
    token.attrSet('rel', 'noopener noreferrer')
  }

  return self.renderToken(tokens, idx, options)
}

const renderedSyllabus = computed(() => {
  if (!syllabusContent.value) {
    return ''
  }

  let html = markdownRenderer.render(syllabusContent.value)

  // 处理API链接，添加target="_blank"和rel属性
  html = html.replace(
    /<a href="([^"]*(?:api\/v1\/[^"]*))"[^>]*>/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">'
  )

  return DOMPurify.sanitize(html)
})

// 渲染课程描述（Markdown转HTML）
const renderedDescription = computed(() => {
  if (!courseDetail.value?.description) {
    return '<p style="color: #999;">暂无课程描述</p>'
  }
  return DOMPurify.sanitize(markdownRenderer.render(courseDetail.value.description))
})

// 筛选后的实践列表
const filteredPractices = computed(() => {
  if (!courseDetail.value?.practices) {
    return []
  }

  // 如果没有选中章节，显示所有实践
  if (!selectedChapterId.value) {
    return courseDetail.value.practices
  }

  // TODO: 根据章节ID筛选实践（需要后端提供chapter_id字段）
  // 目前先返回所有实践
  return courseDetail.value.practices
})

// 点击章节处理
const handleChapterClick = (chapterId: number) => {
  if (selectedChapterId.value === chapterId) {
    // 再次点击同一章节，取消筛选
    selectedChapterId.value = null
  } else {
    selectedChapterId.value = chapterId
  }
}

// 创建课堂表单数据
const createModalVisible = ref(false);
const confirmLoading = ref(false);

// 添加到课堂相关
const addToClassroomModalVisible = ref(false);
const addToClassroomLoading = ref(false);
const selectedClassroomId = ref(null);
const classroomList = ref([]);
const classroomListLoading = ref(false);
const formState = reactive({
  name: '',
  source_course_id: parseInt(courseId),
  credit: 4,
  start_date: null as any,
  end_date: null as any,
  semester: '',
  academic_year: '2024-2025',
  sync_resources_from_source: true,
  sync_assessments_from_source: true
});

// 预览相关
const previewModalVisible = ref(false);
const currentPreviewResource = ref(null);

// 实践展开状态
const expandedPractices = ref([]);

// 计算属性，处理maskClosable属性
const modalMaskClosable = computed(() => false);

// 切换内容区域
const changeSection = async (section: string) => {
  console.log('切换到section:', section);

  // 确保section是有效的
  const validSections = ['experiments', 'syllabus', 'resources', 'exams'];
  if (!validSections.includes(section)) {
    console.error('无效的section:', section);
    return;
  }

  // 更新activeSection
  activeSection.value = [section];
  console.log('activeSection设置为:', activeSection.value);

  // 如果切换到教学大纲Tab，获取内容
  if (section === 'syllabus') {
    await fetchSyllabusContent();
  }

  // 强制触发组件更新
  nextTick(() => {
    console.log('nextTick执行，activeSection:', activeSection.value);

    // 手动更新menu的选中状态
    const menuItems = document.querySelectorAll('.section-menu .ant-menu-item');
    menuItems.forEach((item, index) => {
      const key = item.getAttribute('data-menu-id') || item.getAttribute('key') || item.getAttribute('data-key');

      if (key === section) {
        item.classList.add('ant-menu-item-selected');
        console.log(`✅ 手动选中菜单项: ${key}`);
      } else {
        item.classList.remove('ant-menu-item-selected');
      }
    });
  });
};

// 打开创建课堂弹窗
const openCreateModal = () => {
  // 自动填充课程信息
  formState.name = courseDetail.value?.title || '';
  formState.credit = courseDetail.value?.credits || 4;
  createModalVisible.value = true;
};

// 打开添加到课堂弹窗
const openAddToClassroomModal = async () => {
  addToClassroomModalVisible.value = true;
  selectedClassroomId.value = null;

  // 加载教师的课堂列表
  try {
    classroomListLoading.value = true;
    const response = await techerClassRooms();
    // 过滤出进行中和未开始的课堂
    classroomList.value = [
      ...(response.data.ongoing || []),
      ...(response.data.upcoming || [])
    ];
  } catch (error) {
    console.error('加载课堂列表失败:', error);
    message.error('加载课堂列表失败');
  } finally {
    classroomListLoading.value = false;
  }
};

// 处理添加到课堂
const handleAddToClassroom = async () => {
  if (!selectedClassroomId.value) {
    message.error('请选择要添加的课堂');
    return;
  }

  try {
    addToClassroomLoading.value = true;

    // 调用API添加课程到课堂
    await addClassRoomPractice({
      classroom_id: selectedClassroomId.value,
      chapter_id: '', // 使用空字符串，后端会转换为null
      course_type: 'practice',
      course_ids: courseId
    });

    // 关闭弹窗
    addToClassroomModalVisible.value = false;

    // 显示成功消息
    message.success('课程添加成功');

    // 重置状态
    selectedClassroomId.value = null;

  } catch (error: any) {
    console.error('添加课程到课堂失败:', error);
    const errorMessage = error?.response?.data?.detail || error?.message || '添加课程失败，请重试';
    message.error(errorMessage);
  } finally {
    addToClassroomLoading.value = false;
  }
};

// 查看关卡挑战
const viewChallenge = (practiceId: number, taskId: number) => {
  // 在新标签页中打开关卡详情页
  // 构造URL，指向关卡详情页
  const challengeUrl = `/#/course/challenge/${practiceId}/${taskId}`;
  window.open(challengeUrl, '_blank');
};
//const syllabusContent = computed(() =>courseDetail?.teaching_syllabus);
// 确认创建课堂
const handleCreateConfirm = () => {
	roomformRef.value.validate()
	.then(() => {
		confirmLoading.value = true;
		addClassRoom();
		
	})
	.catch((error: ValidateErrorEntity<formState>) => {
		//console.log('error', error);
	});
};
const addClassRoom = async () => {
	try {
		// 验证必填字段
		if (!formState.name?.trim()) {
			message.error('请输入课堂名称');
			return;
		}

		if (!formState.start_date) {
			message.error('请选择开始时间');
			return;
		}

		if (!formState.end_date) {
			message.error('请选择结束时间');
			return;
		}

		// 检查结束时间是否晚于开始时间
		const startDate = dayjs(formState.start_date);
		const endDate = dayjs(formState.end_date);
		if (endDate.isBefore(startDate)) {
			message.error('结束时间不能早于开始时间');
			return;
		}

	  // 构建发送给后端的数据
	  const classroomData = {
	    name: formState.name.trim(),
	    description: `课程：${course.value?.title || 'Python程序设计'}，学分：${formState.credit}`,
	    start_date: startDate.toISOString(),
	    end_date: endDate.toISOString(),
	    max_students: 50,
	    is_public: true
	  };

	  // 调用API创建课堂
	  const res = await addClassRoomByCourse(classroomData, userStore.userId);

	  // 关闭弹窗
	  createModalVisible.value = false;

	  // 显示成功消息
	  message.success('课堂创建成功');

	  // 重置表单
	  formState.name = '';
	  formState.credit = 4;
	  formState.semester = '';
	  formState.academic_year = '2024-2025';
	  formState.start_date = null;
	  formState.end_date = null;
	  formState.sync_resources_from_source = false;
	  formState.sync_assessments_from_source = false;

	  confirmLoading.value = false;

	  // 根据文档要求，页面应该刷新并显示我的课堂默认页面
	  // 跳转到我的课堂页面
	  router.push('/classroom');

	} catch (err: any) {
	  console.error('创建课堂失败:', err);
	  // 提供更具体的错误信息
	  const errorMessage = err?.response?.data?.detail || err?.message || '创建课堂失败，请重试';
	  message.error(errorMessage);
	  confirmLoading.value = false;
	}
}
// 预览资源
const previewResource = (resource: any) => {
  // 从资源类型或URL推断文件类型
  let fileType = resource.resource_type || 'unknown';

  // 如果fileType是数据库中的类型，需要转换为组件期望的类型
  // pdf/ppt/word/excel/video/image/markdown/json/exam
  const ext = resource.url?.split('.').pop()?.toLowerCase();
  if (ext) {
    if (ext === 'pdf') fileType = 'pdf';
    else if (['ppt', 'pptx'].includes(ext)) fileType = 'office';
    else if (['doc', 'docx'].includes(ext)) fileType = 'word';  // Word文档使用专用预览
    else if (['xls', 'xlsx'].includes(ext)) fileType = 'office';
    else if (['mp4', 'avi', 'mov', 'wmv'].includes(ext)) fileType = 'video';
    else if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) fileType = 'image';
    else if (['md', 'markdown'].includes(ext)) fileType = 'markdown';
    else if (ext === 'json') fileType = 'json';
  }
  
  currentPreviewResource.value = {
    id: resource.id,
    title: resource.title,
    url: resource.url,
    fileType: fileType,
    content: resource.content,
    examType: resource.examType,
    questionCount: resource.questionCount,
    totalScore: resource.totalScore
  };
  previewModalVisible.value = true;
};

// 下载资源
const downloadResource = (resource: any) => {
  if (!resource?.url) {
    message.error('资源链接不存在');
    return;
  }
  const link = document.createElement('a');
  link.href = resource.url;
  link.download = resource.title || 'resource';
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  message.success(`开始下载：${resource.title}`);
};

// 获取资源类型文本
const getResourceTypeText = (type: string) => {
  if (!type) return '未知';
  const lowerType = type.toLowerCase();
  if (lowerType.includes('pdf')) return 'PDF文档';
  if (lowerType.includes('ppt')) return 'PPT课件';
  if (lowerType.includes('doc')) return 'Word文档';
  if (lowerType.includes('xls') || lowerType.includes('excel')) return 'Excel表格';
  if (lowerType.includes('video') || lowerType.includes('mp4')) return '视频';
  return type;
};

// 获取资源类型颜色
const getResourceTypeColor = (type: string) => {
  if (!type) return 'default';
  const lowerType = type.toLowerCase();
  if (lowerType.includes('pdf')) return 'red';
  if (lowerType.includes('ppt')) return 'orange';
  if (lowerType.includes('doc')) return 'blue';
  if (lowerType.includes('xls') || lowerType.includes('excel')) return 'green';
  if (lowerType.includes('video') || lowerType.includes('mp4')) return 'purple';
  return 'default';
};

// 跳转到实践详情页
const goToPracticeDetail = (practiceId: number) => {
  console.log('跳转到实践详情页:', practiceId);
  // 在新标签页打开实践详情页
  const practiceUrl = `/course/micro/${practiceId}`;
  window.open(practiceUrl, '_blank');
};

// 获取难度颜色
const getDifficultyColor = (difficulty: string) => {
  if (!difficulty) return 'blue';
  const upperDiff = difficulty.toUpperCase();
  const colorMap = {
    'BEGINNER': 'green',
    'INTERMEDIATE': 'orange', 
    'ADVANCED': 'red'
  };
  return colorMap[upperDiff] || 'blue';
};

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  if (!difficulty) return '未知';
  const upperDiff = difficulty.toUpperCase();
  const textMap = {
    'BEGINNER': '初级',
    'INTERMEDIATE': '中级',
    'ADVANCED': '高级'
  };
  return textMap[upperDiff] || '未知';
};

// 预览考试
const previewExam = (exam: any) => {
  console.log('预览考试:', exam);

  // 设置预览内容
  currentPreviewResource.value = {
    id: exam.id,
    title: exam.title,
    url: exam.url,
    fileType: 'exam',
    examType: exam.assessment_type,
    questionCount: exam.question_count || 0,
    totalScore: exam.total_score || 0
  };

  // 打开预览模态框
  previewModalVisible.value = true;
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case '已发布':
      return 'green';
    case '未开始':
      return 'orange';
    case '已结束':
      return 'red';
    default:
      return 'blue';
  }
};

// 页面加载时获取课程数据
onMounted(() => {
  // 获取课程详情数据
  getMaterialDetail();
});

// 监听路由参数变化，当课程ID改变时重新加载数据
watch(() => route.params.id, async (newId, oldId) => {
  console.log('🔍 Watch triggered - newId:', newId, 'oldId:', oldId);
  if (newId && newId !== oldId) {
    console.log('✅ Course ID changed from', oldId, 'to', newId, ', reloading data');

    try {
      loading.value = true;
      loadError.value = null;

      // 直接使用newId调用API
      const response = await materialDetail(newId);
      if (response && (response.code === "0000" || response.code === 1)) {
        courseDetail.value = response.data;
        console.log('✅ Course detail loaded for ID', newId, ':', {
          title: response.data?.title,
          chapters: response.data?.chapters?.length,
          resources: response.data?.resources?.length,
          assessments: response.data?.assessments?.length
        });
        await fetchSyllabusSummary(response.data?.teaching_syllabus || '');
      } else {
        loadError.value = '获取课程详情失败';
        message.error('获取课程详情失败');
      }
    } catch (err) {
      console.error('Error fetching course detail:', err);
      loadError.value = '获取课程详情失败，请稍后重试';
      message.error('获取课程详情失败');
    } finally {
      loading.value = false;
    }
  } else {
    console.log('❌ Watch triggered but no change detected');
  }
}, { immediate: false });
const getMaterialDetail = async () => {
  try {
    loading.value = true
    loadError.value = null

    // 使用 materialDetail API获取课程详情
    const response = await materialDetail(courseId)
    if (response && (response.code === "0000" || response.code === 1)) {
      courseDetail.value = response.data
      console.log('Course detail loaded:', {
        title: response.data?.title,
        chapters: response.data?.chapters?.length,
        resources: response.data?.resources?.length,
        assessments: response.data?.assessments?.length,
        course_practices: response.data?.practices?.length,
        teaching_syllabus: response.data?.teaching_syllabus
      })

      // 如果当前激活的是教学大纲Tab，获取内容
      if (activeSection.value.includes('syllabus')) {
        await fetchSyllabusContent()
      }
    } else {
      loadError.value = '获取课程详情失败'
      message.error('获取课程详情失败')
    }
  } catch (err) {
    console.error('Error fetching course detail:', err)
    loadError.value = '获取课程详情失败，请稍后重试'
    message.error('获取课程详情失败')
  } finally {
    loading.value = false
  }
}

// 重试加载
const retryLoad = () => {
  getMaterialDetail()
}

// 获取教学大纲内容
// 注意：后端直接返回Markdown内容，不是URL
const fetchSyllabusContent = async () => {
  if (!courseDetail.value?.teaching_syllabus) {
    console.log('无教学大纲内容，跳过')
    syllabusContent.value = ''
    return
  }

  // teaching_syllabus 已经是Markdown内容，不需要再请求
  const content = courseDetail.value.teaching_syllabus
  console.log('教学大纲内容长度:', content.length)
  
  // 检查是否误返回了HTML（作为保护）
  if (content.trim().startsWith('<!DOCTYPE') || content.trim().startsWith('<html')) {
    console.warn('教学大纲内容疑似HTML，可能是API返回错误')
    syllabusContent.value = '教学大纲加载异常，请联系管理员。'
    return
  }
  
  syllabusContent.value = content
  
  // 获取摘要
  await fetchSyllabusSummary(content)
}

const fetchSyllabusSummary = async (syllabus: string) => {
  if (!syllabus) {
    syllabusSummary.value = null
    return
  }

  try {
    // 限制内容长度，避免AI处理过大数据
    const maxContentLength = 8000
    const truncatedContent = syllabus.length > maxContentLength
      ? syllabus.substring(0, maxContentLength) + '\n\n[内容已截断...]'
      : syllabus

    const response = await axios.post('/api/v1/ai/summary', {
      content: truncatedContent,
      course_title: courseDetail.value?.title || ''
    }, {
      timeout: 15000 // 15秒超时
    })

    // 检查响应状态
    if (response.status === 200 && response.data) {
      syllabusSummary.value = response.data
    } else {
      throw new Error(`API响应异常: ${response.status}`)
    }
  } catch (error) {
    console.warn('获取教学大纲摘要失败，使用原文展示', error)

    // 如果是内容过长导致的失败，尝试发送更短的版本
    if (error?.response?.status === 413 || syllabus.length > 8000) {
      try {
        const shortContent = syllabus.substring(0, 2000) + '\n\n[内容已大幅截断...]'
        const response = await axios.post('/api/v1/ai/summary', {
          content: shortContent,
          course_title: courseDetail.value?.title || ''
        }, {
          timeout: 10000
        })
        if (response.status === 200 && response.data) {
          syllabusSummary.value = response.data
          return
        }
      } catch (retryError) {
        console.warn('重试摘要失败', retryError)
      }
    }

    syllabusSummary.value = null
  }
}
</script>

<style scoped>
/* ==================== 深色主题样式 ==================== */

/* 页面基础 */
.detail-page.copilot-theme {
  background-color: var(--copilot-bg-primary, #f5f5f5);
  color: var(--copilot-text-primary, #e0e0e0);
  min-height: 100vh;
}

/* 三栏布局容器 */
.course-detail-layout {
  background: var(--copilot-bg-primary, #f5f5f5) !important;
}

/* 左侧导航栏 */
.course-sider-left {
  background-color: var(--copilot-bg-secondary, #ffffff) !important;
  position: sticky;
  top: 64px;
  overflow: auto;
  height: calc(100vh - 64px);
  border-right: 1px solid var(--copilot-border-default, #e8e8e8);
}

/* 主布局区域 */
.course-main-layout {
  padding: 0 24px 24px;
  background: var(--copilot-bg-primary, #f5f5f5) !important;
}

/* 内容区域 */
.course-content-area {
  background: var(--copilot-bg-secondary, #ffffff) !important;
  padding: 24px;
  min-height: 280px;
  border-radius: var(--copilot-radius-lg, 12px);
}

/* 右侧边栏 */
.course-sider-right {
  background-color: var(--copilot-bg-secondary, #ffffff) !important;
  padding-left: 24px;
  position: sticky;
  top: 64px;
  overflow: auto;
  height: calc(100vh - 64px);
  border-left: 1px solid var(--copilot-border-default, #e8e8e8);
}

/* ==================== Ant Design 组件覆盖 ==================== */

/* 左侧菜单 */
.detail-page.copilot-theme .left-sidebar {
  border-right: none;
}

.detail-page.copilot-theme :deep(.ant-menu) {
  background: transparent !important;
  color: var(--copilot-text-secondary, #a0a0a0);
  border-right: none;
}

.detail-page.copilot-theme :deep(.ant-menu-item) {
  color: var(--copilot-text-secondary, #a0a0a0);
  margin: 4px 8px;
  border-radius: var(--copilot-radius-md, 8px);
}

.detail-page.copilot-theme :deep(.ant-menu-item:hover) {
  background-color: var(--copilot-bg-hover, rgba(255, 255, 255, 0.05)) !important;
  color: var(--copilot-text-primary, #e0e0e0);
}

.detail-page.copilot-theme :deep(.ant-menu-item-selected) {
  background-color: var(--copilot-brand-primary-alpha-20, rgba(0, 198, 255, 0.15)) !important;
  color: var(--copilot-brand-primary, #00c6ff) !important;
}

.detail-page.copilot-theme :deep(.ant-menu-item-selected::after) {
  border-right-color: var(--copilot-brand-primary, #00c6ff) !important;
}

/* 卡片 */
.detail-page.copilot-theme :deep(.ant-card) {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  border-color: var(--copilot-border-default, #e8e8e8) !important;
  color: var(--copilot-text-primary, #e0e0e0);
  border-radius: var(--copilot-radius-lg, 12px);
}

.detail-page.copilot-theme :deep(.ant-card-head) {
  background: transparent;
  border-bottom-color: var(--copilot-border-default, #e8e8e8);
  color: var(--copilot-text-primary, #e0e0e0);
}

.detail-page.copilot-theme :deep(.ant-card-head-title) {
  color: var(--copilot-text-primary, #e0e0e0);
}

.detail-page.copilot-theme :deep(.ant-card-body) {
  color: var(--copilot-text-secondary, #a0a0a0);
}

/* 列表 */
.detail-page.copilot-theme :deep(.ant-list-item) {
  border-bottom-color: var(--copilot-border-default, #e8e8e8) !important;
  color: var(--copilot-text-primary, #e0e0e0);
}

.detail-page.copilot-theme :deep(.ant-list-item-meta-title) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-list-item-meta-title a) {
  color: var(--copilot-brand-primary, #00c6ff) !important;
}

.detail-page.copilot-theme :deep(.ant-list-item-meta-description) {
  color: var(--copilot-text-secondary, #a0a0a0) !important;
}

/* 折叠面板 */
.detail-page.copilot-theme :deep(.ant-collapse) {
  background: transparent;
  border-color: var(--copilot-border-default, #e8e8e8);
}

.detail-page.copilot-theme :deep(.ant-collapse-item) {
  border-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme :deep(.ant-collapse-header) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
  background: var(--copilot-bg-tertiary, #fafafa) !important;
}

.detail-page.copilot-theme :deep(.ant-collapse-content) {
  background: var(--copilot-bg-secondary, #ffffff) !important;
  border-top-color: var(--copilot-border-default, #e8e8e8) !important;
  color: var(--copilot-text-secondary, #a0a0a0);
}

/* 描述列表 */
.detail-page.copilot-theme :deep(.ant-descriptions) {
  background: transparent;
}

.detail-page.copilot-theme :deep(.ant-descriptions-bordered .ant-descriptions-item-label) {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  color: var(--copilot-text-secondary, #a0a0a0);
  border-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme :deep(.ant-descriptions-bordered .ant-descriptions-item-content) {
  background: var(--copilot-bg-secondary, #ffffff) !important;
  color: var(--copilot-text-primary, #e0e0e0);
  border-color: var(--copilot-border-default, #e8e8e8) !important;
}

/* 统计数字 */
.detail-page.copilot-theme :deep(.ant-statistic-title) {
  color: var(--copilot-text-secondary, #a0a0a0) !important;
}

.detail-page.copilot-theme :deep(.ant-statistic-content) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

/* 提示框 */
.detail-page.copilot-theme :deep(.ant-alert) {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  border-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme :deep(.ant-alert-info) {
  border-left: 3px solid var(--copilot-semantic-info, #60a5fa);
}

.detail-page.copilot-theme :deep(.ant-alert-warning) {
  border-left: 3px solid var(--copilot-semantic-warning, #facc15);
}

.detail-page.copilot-theme :deep(.ant-alert-success) {
  border-left: 3px solid var(--copilot-semantic-success, #22c55e);
}

.detail-page.copilot-theme :deep(.ant-alert-message) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-alert-description) {
  color: var(--copilot-text-secondary, #a0a0a0) !important;
}

/* 头像 */
.detail-page.copilot-theme :deep(.ant-avatar) {
  background: var(--copilot-brand-primary, #00c6ff);
}

/* 分割线 */
.detail-page.copilot-theme :deep(.ant-divider) {
  border-color: var(--copilot-border-default, #e8e8e8);
}

/* 空状态 */
.detail-page.copilot-theme :deep(.ant-empty-description) {
  color: var(--copilot-text-secondary, #a0a0a0);
}

/* 加载状态 */
.detail-page.copilot-theme :deep(.ant-spin-text) {
  color: var(--copilot-text-secondary, #a0a0a0);
}

/* 结果页 */
.detail-page.copilot-theme :deep(.ant-result-title) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-result-subtitle) {
  color: var(--copilot-text-secondary, #a0a0a0) !important;
}

/* 模态框 */
.detail-page.copilot-theme :deep(.ant-modal-content) {
  background: var(--copilot-bg-secondary, #ffffff) !important;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
}

.detail-page.copilot-theme :deep(.ant-modal-header) {
  background: transparent !important;
  border-bottom-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme :deep(.ant-modal-title) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-modal-close-x) {
  color: var(--copilot-text-secondary, #a0a0a0);
}

.detail-page.copilot-theme :deep(.ant-modal-body) {
  color: var(--copilot-text-primary, #e0e0e0);
}

.detail-page.copilot-theme :deep(.ant-modal-footer) {
  border-top-color: var(--copilot-border-default, #e8e8e8) !important;
}

/* 表单 */
.detail-page.copilot-theme :deep(.ant-form-item-label > label) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-input),
.detail-page.copilot-theme :deep(.ant-input-number),
.detail-page.copilot-theme :deep(.ant-picker) {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  border-color: var(--copilot-border-default, #e8e8e8) !important;
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-input:hover),
.detail-page.copilot-theme :deep(.ant-input-number:hover),
.detail-page.copilot-theme :deep(.ant-picker:hover) {
  border-color: var(--copilot-border-highlight, #3a4b6b) !important;
}

.detail-page.copilot-theme :deep(.ant-input:focus),
.detail-page.copilot-theme :deep(.ant-input-number:focus),
.detail-page.copilot-theme :deep(.ant-picker-focused) {
  border-color: var(--copilot-brand-primary, #00c6ff) !important;
  box-shadow: 0 0 0 2px rgba(0, 198, 255, 0.2) !important;
}

.detail-page.copilot-theme :deep(.ant-select-selector) {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  border-color: var(--copilot-border-default, #e8e8e8) !important;
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

.detail-page.copilot-theme :deep(.ant-checkbox-wrapper) {
  color: var(--copilot-text-primary, #e0e0e0);
}

/* ==================== 页面特定样式覆盖 ==================== */

/* 章节项 */
.chapter-item {
  transition: all 0.3s ease;
}

.detail-page.copilot-theme .chapter-item:hover {
  background-color: var(--copilot-bg-hover, rgba(255, 255, 255, 0.05));
}

.detail-page.copilot-theme .chapter-item.selected {
  background-color: var(--copilot-brand-primary-alpha-20, rgba(0, 198, 255, 0.15));
  border-left: 3px solid var(--copilot-brand-primary, #00c6ff);
}

.course-banner {
  padding: 40px 0;
  color: white;
}

.banner-wrapper {
  display: flex;
  align-items: center;
}

.responsive-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.course-img {
  flex: 0 0 160px;
  margin-right: 32px;
}

.course-img img {
  width: 100%;
  border-radius: 4px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.course-info {
  flex: 1;
}

.course-title {
  font-size: 24px;
  margin-bottom: 16px;
}

.course-meta {
  display: flex;
  margin-bottom: 24px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  margin-right: 32px;
}

.label {
  font-size: 14px;
  opacity: 0.8;
}

.value {
  font-size: 24px;
  font-weight: bold;
  margin-top: 4px;
}

.course-actions {
  margin-top: 16px;
}

.create-btn {
  padding: 0 24px;
  height: 36px;
}

.add-btn {
  margin-left: 12px;
  padding: 0 24px;
  height: 36px;
}

.challenge-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.challenge-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--copilot-bg-tertiary, #fafafa);
  border-radius: 6px;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
}

.challenge-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.challenge-number {
  font-weight: 500;
  color: var(--copilot-text-primary, #e0e0e0);
}

.challenge-reward {
  font-size: 12px;
  color: var(--copilot-semantic-warning, #facc15);
}

.left-sidebar {
  height: 100%;
  border-right: 1px solid var(--copilot-border-default, #e8e8e8);
}

.section-menu {
  border-right: none;
}

.content-section {
  margin-bottom: 32px;
}

.intro-card {
  margin-bottom: 24px;
}

.course-description {
  font-size: 15px;
  line-height: 1.8;
  color: var(--copilot-text-secondary, #a0a0a0);
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.feature-icon {
  font-size: 32px;
  color: var(--copilot-brand-primary, #00c6ff);
  flex-shrink: 0;
  margin-top: 4px;
}

.feature-content h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--copilot-text-primary, #e0e0e0);
}

.feature-content p {
  margin: 0;
  font-size: 14px;
  color: var(--copilot-text-secondary, #a0a0a0);
  line-height: 1.6;
}

.prerequisites-list {
  margin: 12px 0;
  padding-left: 24px;
}

.prerequisites-list li {
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--copilot-text-secondary, #a0a0a0);
  line-height: 1.6;
}

.chapter-item {
  margin-bottom: 16px;
}

.course-experiments {
  margin-bottom: 32px;
  padding: 16px;
  background: var(--copilot-bg-tertiary, #fafafa);
  border-radius: 8px;
  border-left: 4px solid var(--copilot-semantic-success, #22c55e);
}

.course-experiments h3 {
  color: var(--copilot-semantic-success, #22c55e);
  margin-bottom: 16px;
}

.practice-link {
  color: var(--copilot-brand-primary, #00c6ff);
  font-weight: 500;
}

.practice-link:hover {
  color: var(--copilot-brand-hover, #00e1ff);
}

.resource-link {
  color: var(--copilot-brand-primary, #00c6ff);
  font-weight: 500;
}

.resource-link:hover {
  color: var(--copilot-brand-hover, #00e1ff);
}

.exam-link {
  color: var(--copilot-brand-primary, #00c6ff);
  font-weight: 500;
}

.exam-link:hover {
  color: var(--copilot-brand-hover, #00e1ff);
}

.exam-title-disabled {
  color: var(--copilot-text-muted, #606060);
  cursor: not-allowed;
}

.resource-stats {
  background: var(--copilot-bg-tertiary, #fafafa);
  padding: 16px;
  border-radius: 6px;
  margin-top: 16px;
}

.exam-stats {
  background: var(--copilot-bg-tertiary, #fafafa);
  padding: 16px;
  border-radius: 6px;
  margin-top: 16px;
}

.practice-stats {
  background: var(--copilot-bg-tertiary, #fafafa);
  padding: 16px;
  border-radius: 6px;
  margin-top: 16px;
}

.info-card {
  margin-bottom: 24px;
}

.team-list {
  display: flex;
  flex-wrap: wrap;
}

.team-item {
  width: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 16px;
}

.team-name {
  margin-top: 8px;
  font-size: 14px;
  text-align: center;
}

.teacher-info {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.teacher-meta {
  margin-left: 16px;
}

.teacher-name {
  font-size: 16px;
  font-weight: bold;
}

.teacher-title {
  font-size: 14px;
  color: var(--copilot-text-secondary, #a0a0a0);
}

.syllabus-section {
  margin-bottom: 24px;
}

.preview-content {
  min-height: 800px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pdf-preview {
  width: 99%; /* 根据需要调整 */
  height: 750px; /* 根据需要调整 */
}

/* ==================== 内容区标题样式 ==================== */
.detail-page.copilot-theme .content-section h2 {
  color: var(--copilot-text-primary, #e0e0e0);
  font-size: 1.5rem;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--copilot-border-default, #e8e8e8);
}

/* Markdown 内容深色主题 */
.detail-page.copilot-theme .markdown-body {
  background: transparent !important;
  color: var(--copilot-text-secondary, #a0a0a0) !important;
}

.detail-page.copilot-theme .markdown-body h1,
.detail-page.copilot-theme .markdown-body h2,
.detail-page.copilot-theme .markdown-body h3,
.detail-page.copilot-theme .markdown-body h4,
.detail-page.copilot-theme .markdown-body h5,
.detail-page.copilot-theme .markdown-body h6 {
  color: var(--copilot-text-primary, #e0e0e0) !important;
  border-bottom-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme .markdown-body a {
  color: var(--copilot-brand-primary, #00c6ff) !important;
}

.detail-page.copilot-theme .markdown-body code {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  color: var(--copilot-semantic-warning, #facc15) !important;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 4px;
}

.detail-page.copilot-theme .markdown-body pre {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 8px;
}

.detail-page.copilot-theme .markdown-body pre code {
  background: transparent !important;
  border: none;
}

.detail-page.copilot-theme .markdown-body blockquote {
  border-left-color: var(--copilot-brand-primary, #00c6ff) !important;
  color: var(--copilot-text-secondary, #a0a0a0) !important;
  background: var(--copilot-bg-tertiary, #fafafa);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
}

.detail-page.copilot-theme .markdown-body table {
  border-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme .markdown-body table th,
.detail-page.copilot-theme .markdown-body table td {
  border-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme .markdown-body table th {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
}

.detail-page.copilot-theme .markdown-body table tr:nth-child(2n) {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
}

.detail-page.copilot-theme .markdown-body hr {
  background-color: var(--copilot-border-default, #e8e8e8) !important;
}

.detail-page.copilot-theme .markdown-body ul,
.detail-page.copilot-theme .markdown-body ol {
  color: var(--copilot-text-secondary, #a0a0a0);
}

/* 右侧信息卡片标题 */
.detail-page.copilot-theme .right-sidebar .info-card :deep(.ant-card-head-title) {
  color: var(--copilot-text-primary, #e0e0e0);
  font-weight: 600;
}

.detail-page.copilot-theme .team-name,
.detail-page.copilot-theme .teacher-name {
  color: var(--copilot-text-primary, #e0e0e0);
}

/* 教学大纲摘要样式 */
.detail-page.copilot-theme .syllabus-summary {
  background: var(--copilot-bg-tertiary, #fafafa);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.detail-page.copilot-theme .syllabus-summary :deep(.ant-typography) {
  color: var(--copilot-text-primary, #e0e0e0) !important;
}

/* 高亮代码块深色主题 */
.detail-page.copilot-theme .hljs {
  background: var(--copilot-bg-tertiary, #fafafa) !important;
  color: var(--copilot-text-primary, #e0e0e0) !important;
}
</style> 