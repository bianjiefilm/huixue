from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class School(Base):
    """学校信息表"""
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="学校名称")
    short_name = Column(String(100), comment="学校简称")
    motto = Column(Text, comment="校训")
    logo_url = Column(String(500), comment="Logo URL")
    logo_data = Column(LargeBinary, comment="Logo二进制数据")
    code = Column(String(50), unique=True, comment="学校编码")
    description = Column(Text, comment="学校描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    colleges = relationship("College", back_populates="school", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="school")
    students = relationship("Student", back_populates="school")

class College(Base):
    """学院表"""
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="学院名称")
    code = Column(String(50), nullable=False, comment="学院编码")
    description = Column(Text, comment="学院描述")
    principal = Column(String(100), comment="负责人")
    contact_phone = Column(String(50), comment="联系电话")
    contact_email = Column(String(200), comment="联系邮箱")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 外键
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    school = relationship("School", back_populates="colleges")
    majors = relationship("Major", back_populates="college", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="college")

class Major(Base):
    """专业表"""
    __tablename__ = "majors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="专业名称")
    code = Column(String(50), nullable=False, comment="专业编码")
    description = Column(Text, comment="专业描述")
    principal = Column(String(100), comment="负责人")
    degree_type = Column(String(50), comment="学位类型(本科/专科/研究生)")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 外键
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    college = relationship("College", back_populates="majors")
    grades = relationship("Grade", back_populates="major", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="major")

class Grade(Base):
    """年级表"""
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, comment="入学年份")
    name = Column(String(100), comment="年级名称")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 外键
    major_id = Column(Integer, ForeignKey("majors.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    major = relationship("Major", back_populates="grades")
    classes = relationship("Class", back_populates="grade", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="grade")

class Class(Base):
    """班级表"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="班级名称")
    code = Column(String(50), nullable=False, comment="班级编码")
    class_teacher = Column(String(100), comment="班主任")
    student_count = Column(Integer, default=0, comment="学生人数")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 外键
    grade_id = Column(Integer, ForeignKey("grades.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    grade = relationship("Grade", back_populates="classes")
    students = relationship("Student", back_populates="class_")

class Teacher(Base):
    """教师表"""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    job_number = Column(String(50), unique=True, nullable=False, comment="工号")
    name = Column(String(100), nullable=False, comment="姓名")
    gender = Column(String(10), comment="性别")
    birth_date = Column(DateTime, comment="出生日期")
    phone = Column(String(50), comment="联系电话")
    email = Column(String(200), comment="邮箱")
    id_card = Column(String(50), comment="身份证号")
    title = Column(String(100), comment="职称")
    department = Column(String(200), comment="部门")
    hire_date = Column(DateTime, comment="入职日期")
    is_admin = Column(Boolean, default=False, comment="是否管理员")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 外键
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    school = relationship("School", back_populates="teachers")
    college = relationship("College", back_populates="teachers")

class Student(Base):
    """学生表"""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_number = Column(String(50), unique=True, nullable=False, comment="学号")
    name = Column(String(100), nullable=False, comment="姓名")
    gender = Column(String(10), comment="性别")
    birth_date = Column(DateTime, comment="出生日期")
    phone = Column(String(50), comment="联系电话")
    email = Column(String(200), comment="邮箱")
    id_card = Column(String(50), comment="身份证号")
    entrance_year = Column(Integer, comment="入学年份")
    graduation_year = Column(Integer, comment="毕业年份")
    student_status = Column(String(50), default="在校", comment="学籍状态")
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 外键
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"))
    major_id = Column(Integer, ForeignKey("majors.id"))
    grade_id = Column(Integer, ForeignKey("grades.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    school = relationship("School", back_populates="students")
    major = relationship("Major", back_populates="students")
    grade = relationship("Grade", back_populates="students")
    class_ = relationship("Class", back_populates="students") 