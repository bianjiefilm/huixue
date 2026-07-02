import { request } from '@/utils/request';
import { get } from '@/utils/request';
import type { Classroom } from '@/types/course';
import { handleApiError } from '@/utils/errorHandler';
import { useUserStore } from '@/stores/user';

/**
 * 教师课堂列表
 */
export function	techerClassRooms(params?: { teacher_id?: number }) {
	const userStore = useUserStore();
	return request<{
		ongoing: Classroom[];
		upcoming: Classroom[];
		ended: Classroom[];
		total_count: number;
		ongoing_count: number;
		upcoming_count: number;
		ended_count: number;
	}>({
		url: '/api/v1/my-classrooms',
		method: 'get',
		params: {
			teacher_id: params?.teacher_id || userStore.userId,
			...params
		},
	})
}
/**
 * 教师课堂详情
 */
export function	techerClRoomsDetail(params: { id: string }) {
	return request<Classroom>({
		url: `/api/v1/classrooms/${params.id}`,
		method: 'get',
		params: {
			enhanced: true
		}
	})
}
/**
 * 创建课堂（废弃，使用addClassRoomByCourse）
 */
export function	addClassRoom(data: {
	name: string;
	description?: string;
	semester: string;
	credits: number;
	startDate: string;
	endDate: string;
}) {
	const userStore = useUserStore();
	return request<Classroom>({
		url: '/api/v1/classrooms',
		method: 'post',
		data: data,
		params: {
			teacher_id: userStore.userId
		}
	})
}
/**
 * 创建课堂
 */
export function	addClassRoomByCourse(data: {
	name: string;
	credit: number;
	start_date: string;
	end_date: string;
	semester: string;
	academic_year: string;
	source_course_id?: number;
	sync_resources_from_source?: boolean;
	sync_assessments_from_source?: boolean;
    cover_url?: string | null;
}, teacherId?: number) {
	const userStore = useUserStore();
    const actualTeacherId = teacherId || userStore.userId;
	return request({
		url: '/api/v1/classrooms',
		method: 'post',
		data: {
            ...data,
            teacher_id: actualTeacherId
        },
		params: {
			teacher_id: actualTeacherId
		}
	})
}
/**
 * 添加章节
 */
export function	addClassRoomChapter(classroomId: number, title: string, teacherId?: number) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${classroomId}/chapters`,
		method: 'post',
		params: {
			title: title,
			teacher_id: teacherId || userStore.userId
		}
	})
}
/**
 * 章节列表
 */
export function	getClassRoomChapter(classroomId: number, teacherId?: number) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${classroomId}/chapters`,
		method: 'get',
		params: {
			teacher_id: teacherId || userStore.userId
		}
	})
}
/**
 * 单章节列表
 */
export function	getChapterList(data: { classroom_id: number }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/chapters`,
		method: 'get',
		params: {
			teacher_id: userStore.userId
		},
	})
}
/**
 * 修改章节
 */
export function	editClassRoomChapter(data: { id: number | string; name: string }, teacherId?: number) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/chapters/${data.id}`,
		method: 'patch',
		params: {
			title: data.name,
			teacher_id: teacherId || userStore.userId
		}
	})
}
/**
 * 删除章节
 */
export function	delClassRoomChapter(data: { id: number | string }, teacherId?: number) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/chapters/${data.id}`,
		method: 'delete',
		params: {
			teacher_id: teacherId || userStore.userId
		}
	})
}
/**
 * 添加实训项目
 */
export async function addClassRoomTraining(data: { classroom_id: number; course_ids: number[] }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/courses/add-training`,
		method: 'post',
		data: {
			course_ids: data.course_ids
		},
		params: {
			teacher_id: userStore.userId
		}
	});
}

/**
 * 保存实训设置
 */
export async function saveTrainingSettings(data: {
	classroom_id: number;
	training_id: number;
	settings: {
		require_design_files: boolean;
		require_experiment_report: boolean;
		total_score: number;
		late_submission_penalty: number;
		assignment_nodes: Array<{ name: string; score: number }>;
	};
}) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/trainings/${data.training_id}/settings`,
		method: 'put',
		data: data.settings,
		params: {
			teacher_id: userStore.userId
		}
	});
}

/**
 * 添加课程
 */
export async function	addClassRoomPractice(data: { classroom_id: number; chapter_id: string; course_type: string; course_ids: string }, teacherId?: number) {
	const userStore = useUserStore();
	try {
		const response = await request({
			url: `/api/v1/classrooms/${data.classroom_id}/courses/add-practice`,
			method: 'post',
			data: {
				course_ids: data.course_ids.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id)),
                chapter_id: data.chapter_id && data.chapter_id !== '' ? parseInt(data.chapter_id) : null
			},
			params: {
				teacher_id: teacherId || userStore.userId
			}
		});
		return response;
	} catch (error) {
		handleApiError(error, '添加实践课程失败');
		throw error;
	}
}
/**
 * 发布课程
 */
export async function	pushClassRoomPractice(data: { classroom_id: number; course_ids: number[]; deadline_at?: string; is_mandatory?: boolean }) {
	const userStore = useUserStore();
	try {
		const response = await request({
			url: `/api/v1/classrooms/${data.classroom_id}/courses/publish`,
			method: 'post',
			data: {
				course_ids: data.course_ids,
				deadline_at: data.deadline_at,
				is_mandatory: data.is_mandatory
			},
			params: {
				teacher_id: userStore.userId
			}
		});
		return response;
	} catch (error) {
		handleApiError(error, '发布课程失败');
		throw error;
	}
}
/**
 * 修改课程
 */
export function	editClassRoomPractice(data: { classroom_course_id: number; name?: string }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classroom-courses/${data.classroom_course_id}`,
		method: 'put',
		data: {
			name: data.name
		},
		params: {
			teacher_id: userStore.userId
		}
	})
}
/**
 * 重命名课程
 */
export function	renameClassroomCourse(courseId: number, name: string, teacherId?: number) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classroom-courses/${courseId}/rename`,
		method: 'patch',
		params: {
			name: name,
			teacher_id: teacherId || userStore.userId
		}
	})
}
/**
 * 删除课程
 */
export function	delClassRoomPractice(data: { classroom_course_id: number }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classroom-courses/${data.classroom_course_id}`,
		method: 'delete',
		params: {
			teacher_id: userStore.userId
		}
	})
}
/**
 * 课程设置
 */
export function	getPracticeStting(data: { classroom_course_id: number }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classroom-courses/${data.classroom_course_id}/settings`,
		method: 'get',
		params: {
			teacher_id: userStore.userId
		},
	})
}
/**
 * 保存课程设置
 */
export function	savePracticeStting(data: { classroom_course_id: number; settings: any }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classroom-courses/${data.classroom_course_id}/settings`,
		method: 'patch',
		data: data.settings,
		params: {
			teacher_id: userStore.userId
		}
	})
}
/**
 * 课堂学生列表
 */
export function	getRoomStuList(data: { classroom_id: number, keyword?: string }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/students`,
		method: 'get',
		params: {
			teacher_id: userStore.userId,
			keyword: data.keyword
		}
	})
}
/**
 * 添加课堂学生
 */
export function	addRoomStudents(data: { classroom_id: number; student_ids: number[] }) {
	// 从localStorage获取当前用户信息（应用使用userInfo键）
	const userStr = localStorage.getItem('userInfo');
	const user = userStr ? JSON.parse(userStr) : null;
	const teacherId = user?.id;

	// 后端需要teacher_id和uids作为查询参数
	// uids需要作为多个查询参数传递，如 uids=1&uids=2&uids=3
	const uidsParams = data.student_ids.map(id => `uids=${id}`).join('&');
	let url = `/api/v1/classrooms/${data.classroom_id}/students`;
	if (teacherId) {
		url += `?teacher_id=${teacherId}&${uidsParams}`;
	} else if (uidsParams) {
		url += `?${uidsParams}`;
	}

	return request({
		url,
		method: 'post',
	})
}
/**
 * 移除课堂学生
 */
export function	delRoomStudents(data: { classroom_id: number; student_ids: number[] }) {
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/students`,
		method: 'delete',
		data: {
			student_ids: data.student_ids
		},
	})
}
/**
 * 课堂资源
 */
export function	getRoomResourcesList(data: { classroom_id: number }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/resources`,
		method: 'get',
		params: {
			teacher_id: userStore.userId
		}
	})
}
/**
 * 课堂实训
 */
export function	getRoomProjectList(data: { classroom_id: number }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/trainings`,
		method: 'get',
		params: {
			teacher_id: userStore.userId
		}
	})
}
/**
 * 添加课堂实训
 */
export function	addRoomProjects(data: { classroom_id: number; course_ids: number[] }) {
	const userStore = useUserStore();
	return request({
		url: `/api/v1/classrooms/${data.classroom_id}/courses/add-training`,
		method: 'post',
		params: {
			teacher_id: userStore.userId
		},
		data: {
			course_ids: data.course_ids
		},
	})
}

/**
 * 获取用户课堂列表
 */
export async function getUserClassrooms(userId?: number) {
  try {
    const params: any = {};
    if (userId) {
      params.student_id = userId;
    }
    const response = await get('/api/v1/user/classrooms', { params });
    return response;
  } catch (error) {
    console.error('获取用户课堂列表失败:', error);
    return { data: [] };
  }
}

/**
 * 获取带统计信息的课堂课程列表
 */
export function getClassroomCoursesWithStats(params: {
  classroomId: number;
  status?: string;
  keyword?: string;
  page?: number;
  pageSize?: number;
  teacherId?: number;
}) {
  return request({
    url: `/api/v1/classrooms/${params.classroomId}/courses/enhanced`,
    method: 'get',
    params: {
      status: params.status,
      keyword: params.keyword,
      page: params.page || 1,
      page_size: params.pageSize || 20,
      teacher_id: params.teacherId
    }
  });
}

/**
 * 获取课堂课程状态统计
 */
export function getClassroomCoursesSummary(classroomId: number, teacherId?: number) {
  return request({
    url: `/api/v1/classrooms/${classroomId}/courses/summary`,
    method: 'get',
    params: {
      teacher_id: teacherId
    }
  });
}

/**
 * 批量发布课程
 */
export function publishClassroomCourses(data: {
  classroomId: number;
  courseIds: number[];
  teacherId: number;
}) {
  return request({
    url: `/api/v1/classrooms/${data.classroomId}/courses/publish`,
    method: 'post',
    data: {
      course_ids: data.courseIds
    },
    params: {
      teacher_id: data.teacherId
    }
  });
}

/**
 * 批量删除课程 (仅限未发布的课程)
 */
export function deleteClassroomCourses(data: {
  classroomId: number;
  courseIds: number[];
  teacherId: number;
}) {
  return request({
    url: `/api/v1/classrooms/${data.classroomId}/courses`,
    method: 'delete',
    data: {
      course_ids: data.courseIds
    },
    params: {
      teacher_id: data.teacherId
    }
  });
}

/**
 * 发布单个课程
 */
export function publishSingleCourse(data: {
  classroomId: number;
  courseId: number;
  teacherId: number;
}) {
  return request({
    url: `/api/v1/classrooms/${data.classroomId}/courses/publish`,
    method: 'post',
    data: {
      course_ids: [data.courseId]
    },
    params: {
      teacher_id: data.teacherId
    }
  });
}

/**
 * 删除单个课程
 */
export function deleteSingleCourse(data: {
  classroomCourseId: number;
  teacherId: number;
}) {
  return request({
    url: `/api/v1/classroom-courses/${data.classroomCourseId}`,
    method: 'delete',
    params: {
      teacher_id: data.teacherId
    }
  });
}

/**
 * 获取学生在课堂中的课程列表（学生端）
 */
export function getStudentCourses(params: {
  classroomId: number;
  studentId: number;
  status?: string;
  keyword?: string;
  page?: number;
  pageSize?: number;
}) {
  return request({
    url: `/api/v1/classrooms/${params.classroomId}/my-courses`,
    method: 'get',
    params: {
      student_id: params.studentId,
      status: params.status,
      keyword: params.keyword,
      page: params.page || 1,
      page_size: params.pageSize || 20
    }
  });
}

/**
 * 获取学生课程状态统计
 */
export function getStudentCoursesSummary(classroomId: number, studentId: number) {
  return request({
    url: `/api/v1/classrooms/${classroomId}/my-courses/summary`,
    method: 'get',
    params: {
      student_id: studentId
    }
  });
}

/**
 * 获取课堂课程列表
 */
export function getClassroomCourses(classroomId: number, teacherId?: number) {
  const userStore = useUserStore();
  return request({
    url: `/api/v1/classrooms/${classroomId}/courses`,
    method: 'get',
    params: {
      teacher_id: teacherId || userStore.userId
    }
  });
}

/**
 * 获取可添加到课堂的课程列表
 */
export function getAvailableCoursesForClassroom(params: {
  classroomId: number;
  courseType?: string;
  keyword?: string;
  direction?: string;
  category?: string;
  difficulty?: string;
  page?: number;
  pageSize?: number;
  teacherId?: number;
}) {
  const userStore = useUserStore();
  return request({
    url: `/api/v1/classrooms/${params.classroomId}/courses/available`,
    method: 'get',
    params: {
      course_type: params.courseType,
      keyword: params.keyword,
      direction: params.direction,
      category: params.category,
      difficulty: params.difficulty,
      page: params.page || 1,
      page_size: params.pageSize || 30,
      teacher_id: params.teacherId || userStore.userId
    }
  });
}
/**
 * 批量删除课程
 */
export async function deleteClassRoomPracticeBatch(data: { classroom_id: number; course_ids: number[] }) {
    const userStore = useUserStore();
    try {
        const response = await request({
            url: `/api/v1/classrooms/${data.classroom_id}/courses/batch_delete`,
            method: 'post',
            data: {
                course_ids: data.course_ids
            },
            params: {
                teacher_id: userStore.userId
            }
        });
        if (response.code === '0000') {
            return response;
        } else {
            throw new Error(response.message || '批量删除课程失败');
        }
    } catch (error) {
        throw error;
    }
}
