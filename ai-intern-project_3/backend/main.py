from flask import Flask, request, jsonify
from flask_cors import CORS  # 解决跨域问题
import os
import json
import logging
from src.api_client import APIClient
from database import query_database, execute_sql_query  # 新增导入execute_sql_query

# 初始化Flask应用并启用CORS
app = Flask(__name__)
CORS(app)  # 允许所有跨域请求，生产环境应配置具体域名

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载配置
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return {}

# 实例化API客户端
cfg = load_config()
client = APIClient(
    chat_url=cfg.get("CHAT_API_URL"),
    embed_url=cfg.get("EMBED_API_URL"),
    api_key=cfg.get("MODEL_API_KEY")
)

# 聊天接口
@app.route("/chat", methods=["POST"])
def chat_endpoint():
    try:
        data = request.json
        user_message = data.get("message")
        
        if not user_message:
            return jsonify({"error": "缺少消息内容"}), 400
        
        # 新增：问题分类prompt（包含表结构信息）
        validity_check_prompt = (
            "请判断用户输入是否是有效问题。有效问题应满足以下条件：\n"
            "1. 与项目相关（不要求有具体且详细的说明）\n"
            "2. 不是乱码或无意义内容\n\n"
            "如果无效，请回复<invalid>并友善的回复，然后指出其未明确提出问题，引导其正确询问有关留学交流项目的内容\n"
            "如果有效，请判断问题意图。如果是可直接查询类，回复<valid_projects>，并且根据以下提示提供sql语句；"
            "如果为现有projects表不方便直接查询，或者倾向于询问某具体project，请回复<valid_embaddings>\n\n"
            "以下是数据库表结构信息（请严格使用这些表结构和字段名）：\n"
            "--- exchange_projects 表结构 ---\n"
            "CREATE TABLE exchange_projects (\n"
            "    id SERIAL PRIMARY KEY, -- 序号: 1\n"
            "    project_name TEXT, -- 项目名称: 2025年秋季学期奥斯陆交换项目通知（挪威-本科生、硕士生）\n"
            "    project_type TEXT, -- 项目性质: 长期项目\n"
            "    publish_date DATE, -- 发布时间: 2025-04-22\n"
            "    source TEXT, -- 来源: 国际合作与交流处学生交流科\n"
            "    official_website TEXT, -- 项目官网: https://www.uio.no/english/studies/admission/exchange/bilateral/\n"
            "    exchange_time TEXT, -- 交流时间: 2025年秋季起一学期\n"
            "    quota TEXT, -- 名额: 1名本科生（大二、大三）、1名硕士生（非毕业年级）\n"
            "    cost TEXT, -- 费用: 免学费，其余自费\n"
            "    major_requirements TEXT, -- 专业要求: 无\n"
            "    language_requirements TEXT, -- 语言要求: 本科生IELTS 5、TOEFL 60 /硕士生IELTS 6.5、TOEFL 90\n"
            "    gpa_requirements TEXT, -- 成绩要求: 无\n"
            "    initial_selection TEXT, -- 学校初选: 有意申请此项目的同学需向我校本科生院和研究生院报名，经选拔获得推荐资格。\n"
            "    application_materials TEXT, -- 申请材料: 获得校荐资格的同学，请根据附件及外方网站的要求，于5月1日前完成网申。\n"
            "    acceptance TEXT, -- 录取: 最终是否录取，由外方学校决定。\n"
            "    deadlines TEXT, -- 时间截点: 4月27日本科生院、研究生院向国际处提供推荐名单；4月27日国际处完成提名事宜；5月1日学生完成网申。\n"
            "    application_procedure TEXT, -- 报名方式: 本科生登录“交换生管理系统”申请，研究生登录南京大学网上办事大厅申请。\n"
            "    notes TEXT, -- 注意事项: 包含9条具体要求（见原始数据）\n"
            "    full_text TEXT -- 全文字段：此字段很长，非指定查找某条数据避免SELECT\n"
            ");\n\n"
            "--- embeddings 表结构 ---\n"
            "CREATE TABLE embeddings (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    index INT,\n"
            "    embedding VECTOR(1024)\n"
            ");\n\n"
            "所有的回复不展示思考过程，只展示回复内容。"
        )
        
        # 新增：调用模型进行问题分类
        classification_response = client.call_chat(
            messages=[
                {"role": "system", "content": validity_check_prompt},
                {"role": "user", "content": user_message}
            ],
            model="tclf90/qwen3-32b-gptq-int8",
            temperature=0.1,
            stream=False
        )
        
        classification_reply = classification_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(classification_reply)

        # 新增：根据分类结果采取不同处理流程
        if "<invalid>" in classification_reply:
            # 直接返回分类阶段的回复（已包含错误提示）
            return jsonify({"reply": classification_reply.replace("<invalid>", "").strip()})
        
        elif "<valid_projects>" in classification_reply:
            # 提取SQL语句并执行查询
            sql_query = extract_sql_from_response(classification_reply)
            if not sql_query:
                return jsonify({"error": "未能提取有效的SQL查询语句"}), 400
                
            query_result = execute_sql_query(sql_query)
            print(query_result)
            
            # 统一使用valid_embaddings的提示格式
            system_prompt = "你是一个专业的AI助手，请根据且仅根据以下上下文，用自然语言清晰的回答"
            augmented_message = f"{user_message}\n\n请根据且仅根据以下上下文进行回答：\n{query_result}"
            
            response = client.call_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": augmented_message}
                ],
                model="tclf90/qwen3-32b-gptq-int8",
                temperature=0.1,
                stream=False
            )
            
            reply = response.get("choices", [{}])[0].get("message", {}).get("content", "（无回复内容）")
            return jsonify({"reply": reply})
        
        elif "<valid_embaddings>" in classification_reply:
            # 原有向量匹配流程
            context = query_database(user_message)
            system_prompt = "你是一个专业的AI助手，请根据且仅根据以下上下文，用自然语言清晰的回答"
            augmented_message = f"{user_message}\n\n请根据且仅根据以下上下文进行回答：\n{context}"
            
            response = client.call_chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": augmented_message}
                ],
                model="tclf90/qwen3-32b-gptq-int8",
                temperature=0.1,
                stream=False
            )
            
            reply = response.get("choices", [{}])[0].get("message", {}).get("content", "（无回复内容）")
            return jsonify({"reply": reply})
        
        else:
            return jsonify({"error": "问题分类失败", "details": classification_reply}), 500
    
    except Exception as e:
        logger.error(f"聊天接口错误: {str(e)}", exc_info=True)
        return jsonify({"error": "处理请求时发生错误", "details": str(e)}), 500

# 新增辅助函数：从模型回复中提取SQL语句
def extract_sql_from_response(response_text):
    """从模型回复中提取SQL查询语句"""
    # 分割响应内容，取最后一个<valid_projects>后的内容
    parts = response_text.split("<valid_projects>")
    if len(parts) > 1:
        response_text = parts[-1]

    # 尝试查找SQL代码块
    if "```sql" in response_text:
        start_idx = response_text.find("```sql") + 6
        end_idx = response_text.find("```", start_idx)
        if end_idx != -1:
            sql = response_text[start_idx:end_idx].strip()
            return sql.rstrip('。')  # 删除末尾中文句号

    # 尝试查找SELECT语句
    select_idx = response_text.find("SELECT")
    if select_idx != -1:
        semicolon_idx = response_text.find(";", select_idx)
        if semicolon_idx != -1:
            sql = response_text[select_idx:semicolon_idx + 1]
        else:
            sql = response_text[select_idx:]
        return sql.rstrip('。')  # 删除末尾中文句号

    return None

# 启动服务
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)