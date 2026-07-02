"""
调试资源匹配性的API端点
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Any

from app.core.dependencies import get_db
from app.models.models import Course, ResourceModule, ResourceFile
from app.utils.logger import logger

router = APIRouter()

@router.get("/debug/course-resources/{course_id}")
async def debug_course_resources(
    course_id: int,
    db: Session = Depends(get_db)
):
    """调试课程资源匹配情况"""
    try:
        # 获取课程信息
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        # 获取该课程的所有资源模块
        modules = db.query(ResourceModule).filter(
            ResourceModule.classroom_id == course_id
        ).all()
        
        # 统计资源情况
        resource_stats = {
            "course_id": course_id,
            "course_title": course.title,
            "course_type": course.course_type.value if course.course_type else None,
            "total_modules": len(modules),
            "total_files": 0,
            "file_types": {},
            "modules": []
        }
        
        # 详细分析每个模块
        for module in modules:
            files = db.query(ResourceFile).filter(
                ResourceFile.module_id == module.id
            ).all()
            
            module_info = {
                "module_id": module.id,
                "module_name": module.name,
                "file_count": len(files),
                "files": []
            }
            
            for file in files:
                resource_stats["total_files"] += 1
                file_type = file.file_type.lower()
                resource_stats["file_types"][file_type] = resource_stats["file_types"].get(file_type, 0) + 1
                
                module_info["files"].append({
                    "id": file.id,
                    "name": file.name,
                    "url": file.url,
                    "type": file.file_type,
                    "size": file.file_size
                })
            
            resource_stats["modules"].append(module_info)
        
        # 检查资源路径匹配性
        mismatch_info = check_resource_path_mismatch(course, modules, db)
        resource_stats["path_analysis"] = mismatch_info
        
        return resource_stats
        
    except Exception as e:
        logger.error(f"调试课程资源时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"调试失败: {str(e)}")

def check_resource_path_mismatch(course: Course, modules: List[ResourceModule], db: Session) -> Dict:
    """检查资源路径是否匹配"""
    analysis = {
        "expected_path": f"课程资源/{course.title}",
        "mismatched_files": [],
        "correct_files": [],
        "suggestions": []
    }
    
    for module in modules:
        files = db.query(ResourceFile).filter(
            ResourceFile.module_id == module.id
        ).all()
        
        for file in files:
            # 检查文件路径是否包含正确的课程名
            if course.title in file.url:
                analysis["correct_files"].append({
                    "file": file.name,
                    "path": file.url
                })
            else:
                # 尝试从路径中提取实际的课程名
                path_parts = file.url.split('/')
                if len(path_parts) >= 2:
                    actual_course = path_parts[1]  # 假设格式是 "课程资源/课程名/文件名"
                    analysis["mismatched_files"].append({
                        "file": file.name,
                        "current_path": file.url,
                        "expected_course": course.title,
                        "actual_course": actual_course
                    })
    
    # 生成修复建议
    if analysis["mismatched_files"]:
        analysis["suggestions"].append("发现资源路径不匹配，可能的原因：")
        analysis["suggestions"].append("1. 课程名称与资源文件夹名称不一致")
        analysis["suggestions"].append("2. 资源被错误地分配给了其他课程")
        analysis["suggestions"].append("3. 需要重新运行资源导入脚本")
    
    return analysis

@router.get("/debug/all-courses-resources")
async def debug_all_courses_resources(db: Session = Depends(get_db)):
    """调试所有课程的资源匹配情况"""
    try:
        # 获取所有有资源的课程
        courses_with_resources = db.query(Course).join(
            ResourceModule, Course.id == ResourceModule.classroom_id
        ).distinct().all()
        
        results = []
        for course in courses_with_resources:
            modules = db.query(ResourceModule).filter(
                ResourceModule.classroom_id == course.id
            ).all()
            
            total_files = 0
            mismatched_files = 0
            
            for module in modules:
                files = db.query(ResourceFile).filter(
                    ResourceFile.module_id == module.id
                ).all()
                
                for file in files:
                    total_files += 1
                    if course.title not in file.url:
                        mismatched_files += 1
            
            results.append({
                "course_id": course.id,
                "course_title": course.title,
                "total_modules": len(modules),
                "total_files": total_files,
                "mismatched_files": mismatched_files,
                "match_rate": f"{((total_files - mismatched_files) / total_files * 100):.1f}%" if total_files > 0 else "N/A"
            })
        
        return {
            "total_courses": len(results),
            "courses": results,
            "summary": {
                "courses_with_perfect_match": sum(1 for r in results if r["mismatched_files"] == 0),
                "courses_with_issues": sum(1 for r in results if r["mismatched_files"] > 0)
            }
        }
        
    except Exception as e:
        logger.error(f"调试所有课程资源时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"调试失败: {str(e)}")

@router.post("/debug/fix-resource-paths/{course_id}")
async def fix_resource_paths(
    course_id: int,
    dry_run: bool = True,
    db: Session = Depends(get_db)
):
    """修复课程资源路径（可选择试运行模式）"""
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        modules = db.query(ResourceModule).filter(
            ResourceModule.classroom_id == course_id
        ).all()
        
        fixes = []
        
        for module in modules:
            files = db.query(ResourceFile).filter(
                ResourceFile.module_id == module.id
            ).all()
            
            for file in files:
                if course.title not in file.url:
                    # 构建正确的路径
                    path_parts = file.url.split('/')
                    if len(path_parts) >= 3:
                        # 替换课程名部分
                        path_parts[1] = course.title
                        new_url = '/'.join(path_parts)
                        
                        fixes.append({
                            "file_id": file.id,
                            "file_name": file.name,
                            "old_url": file.url,
                            "new_url": new_url
                        })
                        
                        if not dry_run:
                            file.url = new_url
        
        if not dry_run and fixes:
            db.commit()
        
        return {
            "course_id": course_id,
            "course_title": course.title,
            "dry_run": dry_run,
            "fixes_count": len(fixes),
            "fixes": fixes[:10],  # 只显示前10个修复
            "message": "修复完成" if not dry_run else "试运行完成，未实际修改"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"修复资源路径时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"修复失败: {str(e)}")