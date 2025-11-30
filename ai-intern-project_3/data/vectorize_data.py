import pandas as pd
import requests
import json
import re

def load_data(file_path):
    data = pd.read_csv(file_path)
    print("Loaded data columns:", data.columns)
    return data

def segment_text(text, max_length=300):
    """将长文本分段，每段不超过max_length个字符"""
    # 尝试按自然段落分割（换行符）
    segments = [seg.strip() for seg in text.split('\n') if seg.strip()]
    
    # 如果分段后仍然过长，按标点符号分割
    final_segments = []
    for seg in segments:
        if len(seg) <= max_length:
            final_segments.append(seg)
        else:
            # 按句号、问号、感叹号分割
            sub_segs = re.split(r'(?<=[。？！])', seg)
            current_seg = ""
            for sub in sub_segs:
                if len(current_seg) + len(sub) <= max_length:
                    current_seg += sub
                else:
                    if current_seg:
                        final_segments.append(current_seg)
                    current_seg = sub
            if current_seg:
                final_segments.append(current_seg)
    return final_segments

def get_embeddings(texts, model="Xorbits/bge-m3", api_url="http://170.18.10.21:6002/v1/embeddings"):
    payload = {
        "model": model,
        "input": texts
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(api_url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def vectorize_dataset(data):
    """处理全文分段并获取向量"""
    all_segments = []
    
    for _, row in data.iterrows():
        # 获取项目序号
        project_id = row['序号']
        # 分段处理全文
        segments = segment_text(row['全文'])
        
        # 为每个分段创建记录
        for seg_idx, segment in enumerate(segments):
            all_segments.append({
                "project_id": project_id,
                "segment_index": seg_idx,
                "segment_text": segment
            })
    
    # 提取纯文本列表用于向量化
    segment_texts = [seg["segment_text"] for seg in all_segments]
    
    # 批量获取向量
    embeddings_resp = get_embeddings(segment_texts)
    embeddings = [item["embedding"] for item in embeddings_resp["data"]]
    
    # 将向量添加到分段记录
    for i, seg in enumerate(all_segments):
        seg["embedding"] = embeddings[i]
    
    return all_segments

def save_embeddings(embeddings, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 读取数据集
    data = load_data('/Users/shinerong/Desktop/ai-intern-project/data/projects.csv')
    
    # 获取分段向量化结果
    segmented_embeddings = vectorize_dataset(data)
    
    # 保存结果
    save_embeddings(segmented_embeddings, 'project_segmented_embeddings.json')
    print(f"Saved {len(segmented_embeddings)} segmented embeddings to project_segmented_embeddings.json")