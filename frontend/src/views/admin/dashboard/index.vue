<template>
  <!-- Nested under admin layout (layout owns padding); no PageShell -->
  <div class="admin-page dashboard-page">
    <PageHeaderBar title="系统仪表盘" subtitle="数据概览与统计" />

    <Stack :gap="5">
      <!-- 数据统计卡片 -->
      <a-row :gutter="16" class="stat-cards">
        <a-col :span="6">
          <a-card :bordered="false">
            <template #title>
              <div class="card-title">
                <team-outlined class="card-icon" />
                <span>总用户数</span>
              </div>
            </template>
            <div class="card-content">
              <div class="card-value">{{ dashboardData.totalUsers }}</div>
              <div class="card-footer">
                <span>较昨日</span>
                <span :class="dashboardData.userIncrease > 0 ? 'increase' : 'decrease'">
                  {{ dashboardData.userIncrease > 0 ? '+' : '' }}{{ dashboardData.userIncrease }}
                  <rise-outlined v-if="dashboardData.userIncrease > 0" />
                  <fall-outlined v-else />
                </span>
              </div>
            </div>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card :bordered="false">
            <template #title>
              <div class="card-title">
                <book-outlined class="card-icon" />
                <span>课程总数</span>
              </div>
            </template>
            <div class="card-content">
              <div class="card-value">{{ dashboardData.totalCourses }}</div>
              <div class="card-footer">
                <span>较昨日</span>
                <span :class="dashboardData.courseIncrease > 0 ? 'increase' : 'decrease'">
                  {{ dashboardData.courseIncrease > 0 ? '+' : '' }}{{ dashboardData.courseIncrease }}
                  <rise-outlined v-if="dashboardData.courseIncrease > 0" />
                  <fall-outlined v-else />
                </span>
              </div>
            </div>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card :bordered="false">
            <template #title>
              <div class="card-title">
                <trophy-outlined class="card-icon" />
                <span>项目总数</span>
              </div>
            </template>
            <div class="card-content">
              <div class="card-value">{{ dashboardData.totalProjects }}</div>
              <div class="card-footer">
                <span>较昨日</span>
                <span :class="dashboardData.projectIncrease > 0 ? 'increase' : 'decrease'">
                  {{ dashboardData.projectIncrease > 0 ? '+' : '' }}{{ dashboardData.projectIncrease }}
                  <rise-outlined v-if="dashboardData.projectIncrease > 0" />
                  <fall-outlined v-else />
                </span>
              </div>
            </div>
          </a-card>
        </a-col>

        <a-col :span="6">
          <a-card :bordered="false">
            <template #title>
              <div class="card-title">
                <solution-outlined class="card-icon" />
                <span>考试总数</span>
              </div>
            </template>
            <div class="card-content">
              <div class="card-value">{{ dashboardData.totalExams }}</div>
              <div class="card-footer">
                <span>较昨日</span>
                <span :class="dashboardData.examIncrease > 0 ? 'increase' : 'decrease'">
                  {{ dashboardData.examIncrease > 0 ? '+' : '' }}{{ dashboardData.examIncrease }}
                  <rise-outlined v-if="dashboardData.examIncrease > 0" />
                  <fall-outlined v-else />
                </span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 系统使用情况图表 -->
      <a-row :gutter="16" class="charts-row">
        <a-col :span="16">
          <a-card title="系统访问趋势" :bordered="false">
            <div ref="visitsTrendChart" class="chart-box"></div>
          </a-card>
        </a-col>

        <a-col :span="8">
          <a-card title="用户分布" :bordered="false">
            <div ref="userDistributionChart" class="chart-box"></div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 近期活动 -->
      <a-row :gutter="16" class="activity-row">
        <a-col :span="12">
          <a-card title="近期活动" :bordered="false">
            <a-list
              :data-source="dashboardData.recentActivities"
              :pagination="{ pageSize: 5 }"
              class="activity-list"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #avatar>
                      <a-avatar :style="{ backgroundColor: item.iconColor }">
                        <template #icon>
                          <user-outlined v-if="item.type === 'user'" />
                          <book-outlined v-if="item.type === 'course'" />
                          <trophy-outlined v-if="item.type === 'project'" />
                          <solution-outlined v-if="item.type === 'exam'" />
                        </template>
                      </a-avatar>
                    </template>
                    <template #title>{{ item.title }}</template>
                    <template #description>
                      <span>{{ item.description }}</span>
                      <br />
                      <span class="activity-time">{{ item.time }}</span>
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>

        <a-col :span="12">
          <a-card title="系统公告" :bordered="false">
            <a-list
              :data-source="dashboardData.announcements"
              :pagination="{ pageSize: 5 }"
              class="announcement-list"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #title>{{ item.title }}</template>
                    <template #description>
                      <span>{{ item.content }}</span>
                      <br />
                      <span class="announcement-time">{{ item.time }}</span>
                    </template>
                  </a-list-item-meta>
                  <template #extra>
                    <a-tag :color="item.important ? 'red' : 'blue'">
                      {{ item.important ? '重要' : '普通' }}
                    </a-tag>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>
    </Stack>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import {
  TeamOutlined,
  BookOutlined,
  TrophyOutlined,
  SolutionOutlined,
  RiseOutlined,
  FallOutlined,
  UserOutlined
} from '@ant-design/icons-vue';
import * as echarts from 'echarts/core';
import {
  LineChart,
  PieChart,
  BarChart
} from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { useDashboardStore } from '../../../stores/dashboard';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import Stack from '@/components/common/Stack.vue';

// 注册必须的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  LineChart,
  PieChart,
  BarChart,
  CanvasRenderer
]);

// 图表实例引用
const visitsTrendChart = ref<HTMLElement | null>(null);
const userDistributionChart = ref<HTMLElement | null>(null);
let visitsChartInstance: echarts.ECharts | null = null;
let userDistChartInstance: echarts.ECharts | null = null;

// 初始化仪表盘数据
const dashboardStore = useDashboardStore();
const dashboardData = dashboardStore.dashboardData;

// Token colors for charts (avoid hard-coded #1890ff)
const PRIMARY = '#1677ff';
const SUCCESS = '#52c41a';

// 初始化图表
onMounted(async () => {
  // 加载仪表盘数据
  await dashboardStore.fetchDashboardData();

  // 初始化访问趋势图表
  if (visitsTrendChart.value) {
    visitsChartInstance = echarts.init(visitsTrendChart.value);
    const visitsTrendOption = {
      title: {
        text: '最近7天系统访问量'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['访问人数', '活跃用户']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: dashboardData.visitsTrend.dates
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '访问人数',
          type: 'line',
          data: dashboardData.visitsTrend.visits,
          smooth: true,
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(0,0,0,0.3)',
            shadowBlur: 10,
            shadowOffsetY: 8
          },
          itemStyle: {
            color: PRIMARY
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(22,119,255,0.5)' },
                { offset: 1, color: 'rgba(22,119,255,0.1)' }
              ]
            }
          }
        },
        {
          name: '活跃用户',
          type: 'line',
          data: dashboardData.visitsTrend.activeUsers,
          smooth: true,
          lineStyle: {
            width: 3,
            shadowColor: 'rgba(0,0,0,0.3)',
            shadowBlur: 10,
            shadowOffsetY: 8
          },
          itemStyle: {
            color: SUCCESS
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(82,196,26,0.5)' },
                { offset: 1, color: 'rgba(82,196,26,0.1)' }
              ]
            }
          }
        }
      ]
    };
    visitsChartInstance.setOption(visitsTrendOption);
  }

  // 初始化用户分布图表
  if (userDistributionChart.value) {
    userDistChartInstance = echarts.init(userDistributionChart.value);
    const userDistOption = {
      title: {
        text: '用户角色分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 10,
        data: ['学生', '教师', '管理员']
      },
      series: [
        {
          name: '用户分布',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: '20',
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: dashboardData.userDistribution.students, name: '学生' },
            { value: dashboardData.userDistribution.teachers, name: '教师' },
            { value: dashboardData.userDistribution.admins, name: '管理员' }
          ]
        }
      ]
    };
    userDistChartInstance.setOption(userDistOption);
  }

  // 窗口大小变化时重新调整图表大小
  const handleResize = () => {
    visitsChartInstance?.resize();
    userDistChartInstance?.resize();
  };
  window.addEventListener('resize', handleResize);

  // 组件卸载时清理
  onUnmounted(() => {
    visitsChartInstance?.dispose();
    userDistChartInstance?.dispose();
    window.removeEventListener('resize', handleResize);
  });
});
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.card-title {
  display: flex;
  align-items: center;
}

.card-icon {
  font-size: 16px;
  margin-right: var(--hx-space-2);
  color: var(--hx-color-primary);
}

.card-content {
  display: flex;
  flex-direction: column;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: var(--hx-space-2);
  color: var(--hx-color-text-primary);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  color: var(--hx-color-text-tertiary);
}

.increase {
  color: var(--hx-color-success);
}

.decrease {
  color: var(--hx-color-error);
}

.chart-box {
  width: 100%;
  height: 350px;
}

.activity-time,
.announcement-time {
  color: var(--hx-color-text-tertiary);
  font-size: 12px;
}
</style>
