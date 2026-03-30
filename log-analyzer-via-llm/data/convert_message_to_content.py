import json

# ===================== 【只需修改这2个路径】 =====================
INPUT_JSONL = "chatml_finetune_dataset.jsonl"    # 旧的数据集路径
OUTPUT_JSONL = "final_dataset.jsonl"  # 生成的新正确数据集
# =================================================================

def convert_file(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as in_f, \
         open(output_path, "w", encoding="utf-8") as out_f:
        
        line_count = 0
        for line in in_f:
            line = line.strip()
            if not line:
                continue
            
            # 读取每一条数据
            sample = json.loads(line)
            
            # 核心：把 message 替换为 content
            if "messages" in sample:
                for msg in sample["messages"]:
                    if "message" in msg:
                        msg["content"] = msg.pop("message")
            
            # 写入新文件
            out_f.write(json.dumps(sample, ensure_ascii=False) + "\n")
            line_count += 1

    print(f"✅ 转换完成！共处理 {line_count} 条数据")
    print(f"✅ 新文件已保存到：{output_path}")

if __name__ == "__main__":
    # 重要提醒：备份原文件
    print(f"⚠️  正在转换：{INPUT_JSONL}")
    convert_file(INPUT_JSONL, OUTPUT_JSONL)