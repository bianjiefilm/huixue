# 课堂管理功能对齐实现方案

## 1. 创建课堂功能增强

### 1.1 添加学生选项
```vue
// 在 /src/views/classroom/index.vue 的创建课堂表单中添加：
<a-form-item label="添加学生">
  <a-checkbox v-model:checked="newClassroom.addStudents">
    添加学生至本课堂
  </a-checkbox>
</a-form-item>
```

### 1.2 学期自动计算显示
```javascript
// 监听日期变化，自动计算学期
const calculatedSemester = computed(() => {
  if (!newClassroom.dateRange || newClassroom.dateRange.length === 0) {
    return '';
  }
  const startDate = dayjs(newClassroom.dateRange[0]);
  const year = startDate.year();
  const month = startDate.month() + 1;
  return month < 7 ? `${year}年春季` : `${year}年秋季`;
});
```

### 1.3 同学期课堂名称检查
```javascript
// 在创建前检查
const checkDuplicateName = async (name: string, semester: string) => {
  const classrooms = await getTeacherClassrooms();
  const duplicate = classrooms.find(c => 
    c.name === name && c.semester === semester
  );
  if (duplicate) {
    message.error(`${semester}已存在名为"${name}"的课堂`);
    return false;
  }
  return true;
};
```

## 2. 基于课程创建课堂增强

### 2.1 添加同步选项
```vue
// 在 /src/views/course/resource/detail.vue 的创建表单中添加：
<a-form-item>
  <a-checkbox v-model:checked="formState.syncResources">
    同步教学资源
  </a-checkbox>
</a-form-item>
<a-form-item>
  <a-checkbox v-model:checked="formState.syncAssessments">
    同步课程考核
  </a-checkbox>
</a-form-item>
```

### 2.2 自动填充课程信息
```javascript
// 打开创建弹窗时自动填充
const openCreateModal = () => {
  formState.name = courseDetail.value?.title || '';
  formState.credit = courseDetail.value?.credit || 4;
  // 其他自动填充逻辑
  createModalVisible.value = true;
};
```

## 3. 添加实训项目功能

### 3.1 创建添加实训对话框组件
```vue
// 新建 /src/components/classroom/AddTrainingCourseDialog.vue
<template>
  <a-modal
    v-model:open="visible"
    title="添加实训项目"
    width="800px"
    @ok="handleSubmit"
  >
    <!-- 实训项目列表选择 -->
  </a-modal>
</template>
```

### 3.2 后端API支持
```python
@router.post("/classrooms/{classroom_id}/courses/add-training")
def add_training_to_classroom(
    classroom_id: int,
    training_ids: List[int],
    db: Session = Depends(get_db)
):
    """添加实训项目到课堂"""
    # 实现逻辑
```

## 4. 调整排序功能

### 4.1 使用 vuedraggable 实现拖拽
```vue
<draggable
  v-model="localCourses"
  :group="{ name: 'courses' }"
  @end="handleDragEnd"
  item-key="id"
>
  <template #item="{ element }">
    <div class="course-item">
      {{ element.name }}
    </div>
  </template>
</draggable>
```

### 4.2 保存排序
```javascript
const handleDragEnd = async () => {
  const orderData = localCourses.value.map((course, index) => ({
    id: course.id,
    order_index: index
  }));
  await updateCourseOrder(classroomId, orderData);
};
```

## 5. 实训项目设置

### 5.1 创建实训设置模态框
```vue
// 新建 /src/components/classroom/TrainingSettingsModal.vue
<template>
  <a-modal title="实训项目设置">
    <a-form>
      <a-form-item label="需要提交设计文件">
        <a-switch v-model:checked="settings.requireDesignFiles" />
      </a-form-item>
      <a-form-item label="需要提交实验报告">
        <a-switch v-model:checked="settings.requireReport" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>
```

## 实施建议

1. **优先级排序**：
   - 高优先级：创建课堂的学期自动计算、添加实训项目功能
   - 中优先级：调整排序功能、实训项目设置
   - 低优先级：其他UI优化

2. **测试重点**：
   - 学期计算的准确性（春季/秋季分界）
   - 拖拽排序的用户体验
   - 权限控制的严格性（历史课堂不可编辑）

3. **数据迁移**：
   - 确保新增字段的默认值设置
   - 考虑历史数据的兼容性