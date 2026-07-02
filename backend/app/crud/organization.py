from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from ..models.organization import School, College, Major, Grade, Class, Teacher, Student
from ..schemas.organization import (
    SchoolCreate, SchoolUpdate, CollegeCreate, CollegeUpdate,
    MajorCreate, MajorUpdate, GradeCreate, GradeUpdate,
    ClassCreate, ClassUpdate, TeacherCreate, TeacherUpdate,
    StudentCreate, StudentUpdate, OrganizationTreeNode
)

# School CRUD
class SchoolCRUD:
    def get_school(self, db: Session, school_id: int) -> Optional[School]:
        return db.query(School).filter(School.id == school_id).first()

    def get_schools(self, db: Session, skip: int = 0, limit: int = 100) -> List[School]:
        return db.query(School).offset(skip).limit(limit).all()

    def create_school(self, db: Session, school: SchoolCreate) -> School:
        db_school = School(**school.dict())
        db.add(db_school)
        db.commit()
        db.refresh(db_school)
        return db_school

    def update_school(self, db: Session, school_id: int, school: SchoolUpdate) -> Optional[School]:
        db_school = self.get_school(db, school_id)
        if db_school:
            update_data = school.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_school, key, value)
            db.commit()
            db.refresh(db_school)
        return db_school

    def update_school_logo(self, db: Session, school_id: int, logo_url: str, logo_data: bytes = None) -> Optional[School]:
        db_school = self.get_school(db, school_id)
        if db_school:
            db_school.logo_url = logo_url
            if logo_data:
                db_school.logo_data = logo_data
            db.commit()
            db.refresh(db_school)
        return db_school

# College CRUD
class CollegeCRUD:
    def get_college(self, db: Session, college_id: int) -> Optional[College]:
        return db.query(College).filter(College.id == college_id).first()

    def get_colleges_by_school(self, db: Session, school_id: int, skip: int = 0, limit: int = 100) -> List[College]:
        return db.query(College).filter(College.school_id == school_id).offset(skip).limit(limit).all()

    def create_college(self, db: Session, college: CollegeCreate) -> College:
        db_college = College(**college.dict())
        db.add(db_college)
        db.commit()
        db.refresh(db_college)
        return db_college

    def update_college(self, db: Session, college_id: int, college: CollegeUpdate) -> Optional[College]:
        db_college = self.get_college(db, college_id)
        if db_college:
            update_data = college.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_college, key, value)
            db.commit()
            db.refresh(db_college)
        return db_college

    def delete_college(self, db: Session, college_id: int) -> bool:
        db_college = self.get_college(db, college_id)
        if db_college:
            # 检查是否有子组织或人员
            has_majors = db.query(Major).filter(Major.college_id == college_id).first()
            has_teachers = db.query(Teacher).filter(Teacher.college_id == college_id).first()
            if has_majors or has_teachers:
                return False
            db.delete(db_college)
            db.commit()
            return True
        return False

    def batch_update_status(self, db: Session, college_ids: List[int], is_active: bool) -> int:
        updated = db.query(College).filter(College.id.in_(college_ids)).update(
            {College.is_active: is_active}, synchronize_session=False
        )
        db.commit()
        return updated

# Major CRUD
class MajorCRUD:
    def get_major(self, db: Session, major_id: int) -> Optional[Major]:
        return db.query(Major).filter(Major.id == major_id).first()

    def get_majors_by_college(self, db: Session, college_id: int, skip: int = 0, limit: int = 100) -> List[Major]:
        return db.query(Major).filter(Major.college_id == college_id).offset(skip).limit(limit).all()

    def create_major(self, db: Session, major: MajorCreate) -> Major:
        db_major = Major(**major.dict())
        db.add(db_major)
        db.commit()
        db.refresh(db_major)
        return db_major

    def update_major(self, db: Session, major_id: int, major: MajorUpdate) -> Optional[Major]:
        db_major = self.get_major(db, major_id)
        if db_major:
            update_data = major.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_major, key, value)
            db.commit()
            db.refresh(db_major)
        return db_major

    def delete_major(self, db: Session, major_id: int) -> bool:
        db_major = self.get_major(db, major_id)
        if db_major:
            # 检查是否有子组织或人员
            has_grades = db.query(Grade).filter(Grade.major_id == major_id).first()
            has_students = db.query(Student).filter(Student.major_id == major_id).first()
            if has_grades or has_students:
                return False
            db.delete(db_major)
            db.commit()
            return True
        return False

# Grade CRUD
class GradeCRUD:
    def get_grade(self, db: Session, grade_id: int) -> Optional[Grade]:
        return db.query(Grade).filter(Grade.id == grade_id).first()

    def get_grades_by_major(self, db: Session, major_id: int, skip: int = 0, limit: int = 100) -> List[Grade]:
        return db.query(Grade).filter(Grade.major_id == major_id).offset(skip).limit(limit).all()

    def create_grade(self, db: Session, grade: GradeCreate) -> Grade:
        db_grade = Grade(**grade.dict())
        if not db_grade.name:
            db_grade.name = f"{grade.year}级"
        db.add(db_grade)
        db.commit()
        db.refresh(db_grade)
        return db_grade

    def update_grade(self, db: Session, grade_id: int, grade: GradeUpdate) -> Optional[Grade]:
        db_grade = self.get_grade(db, grade_id)
        if db_grade:
            update_data = grade.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_grade, key, value)
            db.commit()
            db.refresh(db_grade)
        return db_grade

    def delete_grade(self, db: Session, grade_id: int) -> bool:
        db_grade = self.get_grade(db, grade_id)
        if db_grade:
            # 检查是否有子组织或人员
            has_classes = db.query(Class).filter(Class.grade_id == grade_id).first()
            has_students = db.query(Student).filter(Student.grade_id == grade_id).first()
            if has_classes or has_students:
                return False
            db.delete(db_grade)
            db.commit()
            return True
        return False

# Class CRUD
class ClassCRUD:
    def get_class(self, db: Session, class_id: int) -> Optional[Class]:
        return db.query(Class).filter(Class.id == class_id).first()

    def get_classes_by_grade(self, db: Session, grade_id: int, skip: int = 0, limit: int = 100) -> List[Class]:
        return db.query(Class).filter(Class.grade_id == grade_id).offset(skip).limit(limit).all()

    def create_class(self, db: Session, class_data: ClassCreate) -> Class:
        db_class = Class(**class_data.dict())
        db.add(db_class)
        db.commit()
        db.refresh(db_class)
        return db_class

    def update_class(self, db: Session, class_id: int, class_data: ClassUpdate) -> Optional[Class]:
        db_class = self.get_class(db, class_id)
        if db_class:
            update_data = class_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_class, key, value)
            db.commit()
            db.refresh(db_class)
        return db_class

    def delete_class(self, db: Session, class_id: int) -> bool:
        db_class = self.get_class(db, class_id)
        if db_class:
            # 检查是否有学生
            has_students = db.query(Student).filter(Student.class_id == class_id).first()
            if has_students:
                return False
            db.delete(db_class)
            db.commit()
            return True
        return False

    def update_student_count(self, db: Session, class_id: int):
        """更新班级学生数量"""
        count = db.query(Student).filter(Student.class_id == class_id, Student.is_active == True).count()
        db.query(Class).filter(Class.id == class_id).update({Class.student_count: count})
        db.commit()

# Teacher CRUD
class TeacherCRUD:
    def get_teacher(self, db: Session, teacher_id: int) -> Optional[Teacher]:
        return db.query(Teacher).filter(Teacher.id == teacher_id).first()

    def get_teacher_by_job_number(self, db: Session, job_number: str) -> Optional[Teacher]:
        return db.query(Teacher).filter(Teacher.job_number == job_number).first()

    def get_teachers(self, db: Session, school_id: int = None, college_id: int = None, 
                    search: str = None, skip: int = 0, limit: int = 100) -> List[Teacher]:
        query = db.query(Teacher)
        if school_id:
            query = query.filter(Teacher.school_id == school_id)
        if college_id:
            query = query.filter(Teacher.college_id == college_id)
        if search:
            query = query.filter(
                or_(
                    Teacher.name.contains(search),
                    Teacher.job_number.contains(search)
                )
            )
        return query.offset(skip).limit(limit).all()

    def create_teacher(self, db: Session, teacher: TeacherCreate) -> Teacher:
        db_teacher = Teacher(**teacher.dict())
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        return db_teacher

    def update_teacher(self, db: Session, teacher_id: int, teacher: TeacherUpdate) -> Optional[Teacher]:
        db_teacher = self.get_teacher(db, teacher_id)
        if db_teacher:
            update_data = teacher.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_teacher, key, value)
            db.commit()
            db.refresh(db_teacher)
        return db_teacher

    def delete_teacher(self, db: Session, teacher_id: int) -> bool:
        db_teacher = self.get_teacher(db, teacher_id)
        if db_teacher:
            db.delete(db_teacher)
            db.commit()
            return True
        return False

    def batch_update_status(self, db: Session, teacher_ids: List[int], is_active: bool) -> int:
        updated = db.query(Teacher).filter(Teacher.id.in_(teacher_ids)).update(
            {Teacher.is_active: is_active}, synchronize_session=False
        )
        db.commit()
        return updated

    def set_admin_status(self, db: Session, teacher_ids: List[int], is_admin: bool) -> int:
        updated = db.query(Teacher).filter(Teacher.id.in_(teacher_ids)).update(
            {Teacher.is_admin: is_admin}, synchronize_session=False
        )
        db.commit()
        return updated

# Student CRUD
class StudentCRUD:
    def get_student(self, db: Session, student_id: int) -> Optional[Student]:
        return db.query(Student).filter(Student.id == student_id).first()

    def get_student_by_number(self, db: Session, student_number: str) -> Optional[Student]:
        return db.query(Student).filter(Student.student_number == student_number).first()

    def get_students(self, db: Session, school_id: int = None, college_id: int = None,
                    major_id: int = None, grade_id: int = None, class_id: int = None,
                    search: str = None, skip: int = 0, limit: int = 100) -> List[Student]:
        query = db.query(Student)
        if school_id:
            query = query.filter(Student.school_id == school_id)
        if college_id:
            query = query.filter(Student.college_id == college_id)
        if major_id:
            query = query.filter(Student.major_id == major_id)
        if grade_id:
            query = query.filter(Student.grade_id == grade_id)
        if class_id:
            query = query.filter(Student.class_id == class_id)
        if search:
            query = query.filter(
                or_(
                    Student.name.contains(search),
                    Student.student_number.contains(search)
                )
            )
        return query.offset(skip).limit(limit).all()

    def create_student(self, db: Session, student: StudentCreate) -> Student:
        db_student = Student(**student.dict())
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        
        # 更新班级学生数量
        if db_student.class_id:
            class_crud.update_student_count(db, db_student.class_id)
        
        return db_student

    def update_student(self, db: Session, student_id: int, student: StudentUpdate) -> Optional[Student]:
        db_student = self.get_student(db, student_id)
        if db_student:
            old_class_id = db_student.class_id
            update_data = student.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_student, key, value)
            db.commit()
            db.refresh(db_student)
            
            # 更新相关班级学生数量
            if old_class_id:
                class_crud.update_student_count(db, old_class_id)
            if db_student.class_id and db_student.class_id != old_class_id:
                class_crud.update_student_count(db, db_student.class_id)
        
        return db_student

    def delete_student(self, db: Session, student_id: int) -> bool:
        db_student = self.get_student(db, student_id)
        if db_student:
            class_id = db_student.class_id
            db.delete(db_student)
            db.commit()
            
            # 更新班级学生数量
            if class_id:
                class_crud.update_student_count(db, class_id)
            
            return True
        return False

    def batch_update_status(self, db: Session, student_ids: List[int], is_active: bool) -> int:
        updated = db.query(Student).filter(Student.id.in_(student_ids)).update(
            {Student.is_active: is_active}, synchronize_session=False
        )
        db.commit()
        return updated

    def batch_transfer(self, db: Session, student_ids: List[int], 
                      college_id: int = None, major_id: int = None, 
                      grade_id: int = None, class_id: int = None) -> int:
        update_data = {}
        if college_id:
            update_data[Student.college_id] = college_id
        if major_id:
            update_data[Student.major_id] = major_id
        if grade_id:
            update_data[Student.grade_id] = grade_id
        if class_id:
            update_data[Student.class_id] = class_id
        
        updated = db.query(Student).filter(Student.id.in_(student_ids)).update(
            update_data, synchronize_session=False
        )
        db.commit()
        return updated

# Organization Tree
class OrganizationCRUD:
    def get_organization_tree(self, db: Session, school_id: int) -> OrganizationTreeNode:
        """获取完整的组织架构树"""
        school = db.query(School).filter(School.id == school_id).first()
        if not school:
            return None
        
        def build_tree_node(obj, node_type: str, parent_id: int = None) -> OrganizationTreeNode:
            children = []
            has_children = False
            
            if node_type == "school":
                colleges = db.query(College).filter(College.school_id == obj.id).all()
                children = [build_tree_node(college, "college", obj.id) for college in colleges]
                has_children = len(colleges) > 0
            elif node_type == "college":
                majors = db.query(Major).filter(Major.college_id == obj.id).all()
                children = [build_tree_node(major, "major", obj.id) for major in majors]
                has_children = len(majors) > 0
            elif node_type == "major":
                grades = db.query(Grade).filter(Grade.major_id == obj.id).all()
                children = [build_tree_node(grade, "grade", obj.id) for grade in grades]
                has_children = len(grades) > 0
            elif node_type == "grade":
                classes = db.query(Class).filter(Class.grade_id == obj.id).all()
                children = [build_tree_node(cls, "class", obj.id) for cls in classes]
                has_children = len(classes) > 0
            
            return OrganizationTreeNode(
                id=obj.id,
                name=obj.name,
                code=getattr(obj, 'code', None),
                type=node_type,
                parent_id=parent_id,
                is_active=obj.is_active,
                has_children=has_children,
                children=children
            )
        
        return build_tree_node(school, "school")

# 创建CRUD实例
school_crud = SchoolCRUD()
college_crud = CollegeCRUD()
major_crud = MajorCRUD()
grade_crud = GradeCRUD()
class_crud = ClassCRUD()
teacher_crud = TeacherCRUD()
student_crud = StudentCRUD()
organization_crud = OrganizationCRUD() 