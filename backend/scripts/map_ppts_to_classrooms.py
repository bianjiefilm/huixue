import psycopg2
import sys
import glob

DB_URL = "postgresql://huixue:huixue123@db:5432/huixue"

def main():
    # 1. Find 18 pptx files in the container's mounted yolume
    pptx_files = glob.glob("/app/ziyuan_data/**/*.pptx", recursive=True)
    if not pptx_files:
        print("No pptx found in /app/ziyuan_data!")
        sys.exit(1)
        
    # Convert container absolute path to backend static url
    # /app/ziyuan_data/XXX -> /static/resources/XXX
    pptx_files = [f.replace("/app/ziyuan_data", "/static/resources") for f in pptx_files]
    pptx_files = list(set(pptx_files))
    if len(pptx_files) < 18:
        print(f"Only {len(pptx_files)} unique pptx found, duplicating to 18.")
        while len(pptx_files) < 18:
            pptx_files.append(pptx_files[0])
            
    real_ppts = pptx_files[:18]
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    for i in range(18):
        classroom_id = 100 + i
        ppt_url = real_ppts[i]
        file_name = ppt_url.split('/')[-1]
        
        # We need to insert a resource file for this classroom!
        # First find a module for this classroom
        cur.execute("SELECT id FROM resource_modules WHERE classroom_id = %s ORDER BY id LIMIT 1", (classroom_id,))
        module_row = cur.fetchone()
        if not module_row:
            print(f"Classroom {classroom_id} has no resource modules!")
            continue
            
        module_id = module_row[0]
        
        # Check if ppt already exists in this module to avoid duplicates
        cur.execute("SELECT id FROM resource_files WHERE module_id = %s AND file_type = 'PPTX'", (module_id,))
        existing_file = cur.fetchone()
        
        if existing_file:
            print(f"Updating existing PPTX for classroom {classroom_id}")
            cur.execute("""
                UPDATE resource_files 
                SET url = %s, name = %s 
                WHERE id = %s
            """, (ppt_url, file_name, existing_file[0]))
        else:
            print(f"Inserting new PPTX for classroom {classroom_id}")
            cur.execute("""
                INSERT INTO resource_files (module_id, name, file_type, file_size, url, uploader_id)
                VALUES (%s, %s, 'PPTX', 1048576, %s, 1)
            """, (module_id, file_name, ppt_url))
            
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
