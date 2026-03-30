# chat-template-analyzer.py
"""
用 Hugging Face 官方工具库（transformers），加载你本地的 Qwen2.5-3B 大模型的专属分词器，并打印出模型要求的对话格式模板。
"""
from transformers import AutoTokenizer      # 智能分词器，自动适配任何大模型

model_name = "../qwen25-3b"                 # 本地模型路径

# 自动读取本地模型文件夹，匹配并加载（from_pretrained）Qwen2.5-3b的专属分词器
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 输出分词器中存储的模型对话格式规则
print(tokenizer.chat_template)



