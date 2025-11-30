import psycopg2
import json
import os

# 连接数据库
conn = psycopg2.connect(
    dbname="embeddings_db",
    user="shinerong",
    password="",
    host="localhost"
)
cur = conn.cursor()

# 删除旧表并重建（含 project_id）
cur.execute("""
    DROP TABLE IF EXISTS embeddings;
    CREATE TABLE embeddings (
        id SERIAL PRIMARY KEY,
        project_id INT NOT NULL REFERENCES exchange_projects(id),
        segment_text TEXT NOT NULL,
        embedding VECTOR(1024) NOT NULL
    );
""")

# 读取 JSON 文件
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, '../project_segmented_embeddings.json')

with open(file_path, 'r') as f:
    embeddings_data = json.load(f)

# 插入数据
for item in embeddings_data:
    cur.execute(
        "INSERT INTO embeddings (project_id, segment_text, embedding) VALUES (%s, %s, %s)",
        (item["project_id"], item["segment_text"], item["embedding"])
    )

# 提交事务
conn.commit()
cur.close()
conn.close()

print("✅ 向量数据已成功导入 embeddings_db")
print(f"共导入 {len(embeddings_data)} 条分段向量记录")