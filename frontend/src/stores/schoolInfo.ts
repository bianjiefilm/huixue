import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

export interface SchoolInfo {
  schoolName: string;
  shortName: string;
  motto: string;
  logo: string;
}

export const useSchoolInfoStore = defineStore('schoolInfo', () => {
  const schoolInfo = reactive<SchoolInfo>({
    schoolName: '西北大学',
    shortName: '西大',
    motto: '修德、笃学、求是、创新',
    logo: 'https://via.placeholder.com/150x150?text=校徽'
  });

  // 获取学校信息
  async function getSchoolInfo() {
    // 在实际项目中，这里应该调用API获取学校信息
    // 此处使用模拟数据
    return {
      schoolName: schoolInfo.schoolName,
      shortName: schoolInfo.shortName,
      motto: schoolInfo.motto,
      logo: schoolInfo.logo
    };
  }

  // 更新学校信息
  async function updateSchoolInfo(info: Partial<SchoolInfo>) {
    // 在实际项目中，这里应该调用API更新学校信息
    // 此处仅更新本地状态
    Object.assign(schoolInfo, info);
    return schoolInfo;
  }

  return {
    schoolInfo,
    getSchoolInfo,
    updateSchoolInfo
  }
}) 