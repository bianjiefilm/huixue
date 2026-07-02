"""
Add database indexes for performance optimization
"""
from sqlalchemy import create_engine, text, Index
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_indexes():
    """Create database indexes for performance optimization"""
    engine = create_engine(settings.DATABASE_URL)
    
    indexes = [
        # User indexes
        "CREATE INDEX IF NOT EXISTS idx_user_username ON api_users(username);",
        "CREATE INDEX IF NOT EXISTS idx_user_email ON api_users(email);",
        "CREATE INDEX IF NOT EXISTS idx_user_active ON api_users(is_active);",
        
        # Course indexes
        "CREATE INDEX IF NOT EXISTS idx_course_type ON courses(course_type);",
        "CREATE INDEX IF NOT EXISTS idx_course_difficulty ON courses(difficulty);",
        "CREATE INDEX IF NOT EXISTS idx_course_direction ON courses(direction);",
        "CREATE INDEX IF NOT EXISTS idx_course_visibility ON courses(visibility);",
        "CREATE INDEX IF NOT EXISTS idx_course_created ON courses(created_at);",
        
        # Classroom indexes
        "CREATE INDEX IF NOT EXISTS idx_classroom_teacher ON classrooms(teacher_id);",
        "CREATE INDEX IF NOT EXISTS idx_classroom_status ON classrooms(status);",
        "CREATE INDEX IF NOT EXISTS idx_classroom_start_date ON classrooms(start_date);",
        "CREATE INDEX IF NOT EXISTS idx_classroom_end_date ON classrooms(end_date);",
        "CREATE INDEX IF NOT EXISTS idx_classroom_teacher_status ON classrooms(teacher_id, status);",
        
        # Practice indexes
        "CREATE INDEX IF NOT EXISTS idx_practice_course ON practices(course_id);",
        "CREATE INDEX IF NOT EXISTS idx_practice_difficulty ON practices(difficulty);",
        "CREATE INDEX IF NOT EXISTS idx_practice_status ON practices(publish_status);",
        
        # Task indexes
        "CREATE INDEX IF NOT EXISTS idx_task_practice ON tasks(practice_id);",
        "CREATE INDEX IF NOT EXISTS idx_task_type ON tasks(task_type);",
        "CREATE INDEX IF NOT EXISTS idx_task_order ON tasks(practice_id, task_order);",
        
        # Stage indexes
        "CREATE INDEX IF NOT EXISTS idx_stage_task ON stages(task_id);",
        "CREATE INDEX IF NOT EXISTS idx_stage_order ON stages(task_id, stage_order);",
        
        # Student indexes
        "CREATE INDEX IF NOT EXISTS idx_student_classroom ON students(classroom_id);",
        "CREATE INDEX IF NOT EXISTS idx_student_user ON students(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_student_classroom_user ON students(classroom_id, user_id);",
        
        # Grade indexes
        "CREATE INDEX IF NOT EXISTS idx_grade_student ON grades(student_id);",
        "CREATE INDEX IF NOT EXISTS idx_grade_course ON grades(course_id);",
        "CREATE INDEX IF NOT EXISTS idx_grade_classroom ON grades(classroom_id);",
        "CREATE INDEX IF NOT EXISTS idx_grade_status ON grades(status);",
        "CREATE INDEX IF NOT EXISTS idx_grade_student_course ON grades(student_id, course_id);",
        
        # Exam indexes
        "CREATE INDEX IF NOT EXISTS idx_exam_classroom ON exams(classroom_id);",
        "CREATE INDEX IF NOT EXISTS idx_exam_creator ON exams(created_by);",
        "CREATE INDEX IF NOT EXISTS idx_exam_status ON exams(status);",
        "CREATE INDEX IF NOT EXISTS idx_exam_start_time ON exams(start_time);",
        "CREATE INDEX IF NOT EXISTS idx_exam_classroom_status ON exams(classroom_id, status);",
        
        # Question indexes
        "CREATE INDEX IF NOT EXISTS idx_question_exam ON questions(exam_id);",
        "CREATE INDEX IF NOT EXISTS idx_question_type ON questions(question_type);",
        "CREATE INDEX IF NOT EXISTS idx_question_order ON questions(exam_id, question_order);",
        
        # Resource indexes
        "CREATE INDEX IF NOT EXISTS idx_resource_type ON resources(resource_type);",
        "CREATE INDEX IF NOT EXISTS idx_resource_created ON resources(created_at);",
        
        # Session indexes (for analytics)
        "CREATE INDEX IF NOT EXISTS idx_session_user ON sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_session_classroom ON sessions(classroom_id);",
        "CREATE INDEX IF NOT EXISTS idx_session_start ON sessions(start_time);",
        "CREATE INDEX IF NOT EXISTS idx_session_user_date ON sessions(user_id, DATE(start_time));",
        
        # Training indexes
        "CREATE INDEX IF NOT EXISTS idx_training_difficulty ON trainings(difficulty);",
        "CREATE INDEX IF NOT EXISTS idx_training_visibility ON trainings(visibility);",
        "CREATE INDEX IF NOT EXISTS idx_training_created ON trainings(created_at);",
        
        # Composite indexes for common queries
        "CREATE INDEX IF NOT EXISTS idx_course_type_difficulty ON courses(course_type, difficulty);",
        "CREATE INDEX IF NOT EXISTS idx_classroom_teacher_dates ON classrooms(teacher_id, start_date, end_date);",
        "CREATE INDEX IF NOT EXISTS idx_grade_classroom_student_course ON grades(classroom_id, student_id, course_id);",
    ]
    
    with engine.connect() as conn:
        for index_sql in indexes:
            try:
                conn.execute(text(index_sql))
                conn.commit()
                logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
                logger.error(f"SQL: {index_sql}")
    
    logger.info("Index creation completed")

if __name__ == "__main__":
    create_indexes()