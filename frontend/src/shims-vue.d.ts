declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 为缺失类型声明的模块添加声明
declare module '../views/excellent-works/index.vue'
declare module '../views/excellent-works/excellent-results.vue'
declare module '../views/excellent-works/collected-works.vue'
declare module '../views/exam/index.vue'
declare module '../views/exam/paper-bank.vue'
declare module '../views/exam/my-exams.vue'
declare module '../views/exam/question-bank.vue'
declare module '../views/exam/create-question.vue'
declare module '../views/exam/edit-question.vue'
declare module '../views/exam/edit-paper.vue'
declare module '../views/exam/template-paper.vue'
declare module '../views/admin/user/Student.vue'
declare module '../views/admin/user/Role.vue'
declare module '../views/Redirect.vue' 