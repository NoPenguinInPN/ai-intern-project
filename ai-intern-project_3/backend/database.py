import requests
import psycopg2
import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_embeddings(text, model="Xorbits/bge-m3", api_url="http://170.18.10.21:6002/v1/embeddings"):
    """获取文本的向量表示"""
    payload = {"model": model, "input": [text]}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        # 返回原始向量数组而非JSON字符串
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        logger.error(f"向量化失败: {str(e)}")
        raise

# 新增：执行SQL查询函数
def execute_sql_query(sql_query):
    """执行SQL查询并返回结果"""
    try:
        # 连接数据库
        conn = psycopg2.connect(
            dbname="embeddings_db",
            user="shinerong",
            password="",
            host="localhost"
        )
        cur = conn.cursor()
        
        # 执行查询
        cur.execute(sql_query)
        results = cur.fetchall()
        
        # 格式化为字符串
        output = []
        for row in results:
            output.append("\t".join(str(item) for item in row))
        
        return "\n".join(output)
        
    except Exception as e:
        logger.error(f"SQL查询失败: {str(e)}")
        return f"查询失败: {str(e)}"
    finally:
        if conn:
            conn.close()

def query_database(user_message):
    """查询数据库并返回相关上下文"""
    try:
        # 获取文本向量
        embedding = get_embeddings(user_message)
        
        # 连接数据库
        conn = psycopg2.connect(
            dbname="embeddings_db",
            user="shinerong",
            password="",
            host="localhost"
        )
        cur = conn.cursor()
        
        # 1. 查询最接近的5个向量片段
        # 修改点：使用数组参数自动转换 + 显式类型转换
        cur.execute("""
            SELECT project_id, segment_text 
            FROM embeddings 
            ORDER BY embedding <=> %s::vector
            LIMIT 5
        """, (embedding,))
        top_segments = cur.fetchall()
        
        # 提取去重的project_id
        project_ids = list({segment[0] for segment in top_segments})
        
        # 2. 根据project_id查询项目详情
        if project_ids:
            cur.execute(f"""
                SELECT project_name, full_text 
                FROM exchange_projects 
                WHERE id IN ({','.join(map(str, project_ids))})
            """)
            project_details = cur.fetchall()
        else:
            project_details = []
        
        # 构造上下文字符串
        context = "\n".join([
            f"项目名称: {name}\n项目详情: {text}" 
            for name, text in project_details
        ])
        
        return context
        
    except Exception as e:
        logger.error(f"数据库查询失败: {str(e)}")
        return ""
    finally:
        if conn:
            conn.close()