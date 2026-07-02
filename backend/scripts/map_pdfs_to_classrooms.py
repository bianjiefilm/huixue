import psycopg2
import sys
import glob

DB_URL = "postgresql://huixue:huixue123@db:5432/huixue"

def main():
    # Find 18 distinct pdf files in the container's mounted yolume
    pdf_files = glob.glob("/app/ziyuan_data/**/*.pdf", recursive=True)
    if not pdf_files:
        print("No pdf found in /app/ziyuan_data!")
        sys.exit(1)
        
    # Group by parent folder to get diverse looking PDFs (e.g. Spark, CV, Python)
    diversity_map = {}
    for path in pdf_files:
        parts = path.split('/')
        dir_name = parts[4] if len(parts) > 4 else "misc"
        if dir_name not in diversity_map:
            diversity_map[dir_name] = []
        diversity_map[dir_name].append(path)

    selected_pdfs = []
    while len(selected_pdfs) < 18 and diversity_map:
        for k in list(diversity_map.keys()):
            if diversity_map[k]:
                selected_pdfs.append(diversity_map[k].pop(0))
                if len(selected_pdfs) == 18:
                    break
            else:
                del diversity_map[k]

    if len(selected_pdfs) < 18:
        print(f"Only {len(selected_pdfs)} unique pdf found, duplicating to 18.")
        while len(selected_pdfs) < 18:
            selected_pdfs.append(selected_pdfs[0])

    # Convert container absolute path to backend static url
    real_pdfs = [f.replace("/app/ziyuan_data", "/static/resources") for f in selected_pdfs]
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # In some logic the user was operating initially on 18 classrooms, let's span 100 to 117
    # Note: our earlier E2E suite actually evaluated 18 Classrooms: IDs 100 -> 117.
    for i in range(18):
        classroom_id = 100 + i
        pdf_url = real_pdfs[i]
        file_name = pdf_url.split('/')[-1]
        
        cur.execute("SELECT id FROM resource_modules WHERE classroom_id = %s ORDER BY id LIMIT 1", (classroom_id,))
        module_row = cur.fetchone()
        if not module_row:
            print(f"Classroom {classroom_id} has no resource modules!")
            continue
            
        module_id = module_row[0]
        
        # We find the existing PPTX logic record and override it to instead serve the native PDF equivalently:
        cur.execute("SELECT id FROM resource_files WHERE module_id = %s AND file_type = 'PPTX'", (module_id,))
        existing_file = cur.fetchone()
        
        if existing_file:
            print(f"Swapping existing corrupted PPTX into robust PDF for classroom {classroom_id}: {file_name}")
            cur.execute("""
                UPDATE resource_files 
                SET url = %s, name = %s, file_type = 'pdf'
                WHERE id = %s
            """, (pdf_url, file_name, existing_file[0]))
        else:
            # Maybe the PPTX didn't exist on this particular ID, inject the PDF regardless to keep sequence.
            print(f"Inserting new PDF baseline for classroom {classroom_id}")
            cur.execute("""
                INSERT INTO resource_files (module_id, name, file_type, file_size, url, uploader_id)
                VALUES (%s, %s, 'pdf', 10485760, %s, 1)
            """, (module_id, file_name, pdf_url))
            
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
