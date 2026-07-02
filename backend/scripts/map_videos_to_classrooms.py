import psycopg2
import sys

DB_URL = "postgresql://huixue:huixue123@db:5432/huixue"

real_videos = [
    "/static/resources/实训资源/01-某零售企业经营分析/export/files/fa61ab52e18c41b8bb10f055d6fc1c71.mp4",
    "/static/resources/实训资源/01-某零售企业经营分析/export/files/4061089527ce49239236204bc070dc8f.mp4",
    "/static/resources/E2E_CV_01.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第二章：科学计算与数据可视化.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第五章：回归问题与梯度下降法.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第三章：数据探索.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第六章：分类问题.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第九章：典型的卷积神经网络.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第四章：TensorFlow基础.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第七章：人工神经网络.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第十章：基于YOLO的目标检测实践.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第一章：人工智能的起源和发展.mp4",
    "/static/resources/课程资源/数据挖掘分析/视频和课件/第八章：卷积神经网络.mp4",
    "/static/resources/课程资源/大数据技术基础与应用实践/视频和课件/5.2 NoSQL与关系数据库的比较.mp4",
    "/static/resources/课程资源/大数据技术基础与应用实践/视频和课件/10.1.1 Spark简介.mp4",
    "/static/resources/课程资源/大数据技术基础与应用实践/视频和课件/13.2 Pregel简介.mp4",
    "/static/resources/实训资源/01-某零售企业经营分析/assets/files/fa61ab52e18c41b8bb10f055d6fc1c71.mp4",
    "/static/resources/实训资源/01-某零售企业经营分析/assets/files/4061089527ce49239236204bc070dc8f.mp4"
]

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Get 1 video file per classroom (100 to 117)
    cur.execute("""
        SELECT DISTINCT ON (c.id) c.id as classroom_id, f.id as file_id 
        FROM classrooms c 
        JOIN resource_modules m ON c.id = m.classroom_id 
        JOIN resource_files f ON m.id = f.module_id 
        WHERE c.id BETWEEN 100 AND 117 AND f.name LIKE '%视频%.mp4' 
        ORDER BY c.id, f.id;
    """)
    rows = cur.fetchall()
    
    if len(rows) != 18:
        print(f"Error: Expected 18 rows, found {len(rows)}")
        sys.exit(1)
        
    for i, (classroom_id, file_id) in enumerate(rows):
        video_url = real_videos[i]
        cur.execute("UPDATE resource_files SET url = %s WHERE id = %s", (video_url, file_id))
        print(f"Updated classroom {classroom_id} (file_id {file_id}) to {video_url}")
        
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
