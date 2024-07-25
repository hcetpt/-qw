import sys
from openai import OpenAI
import os
import re
import json

def get_response(question):
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"), # 如果您没有配置环境变量，请在此处用您的API Key进行替换
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填写DashScope SDK的base_url
    )
    completion = client.chat.completions.create(
        model="qwen-long",
        messages=[{'role': 'system', 'content': 'You are a helpful assistant.'},
                  {'role': 'user', 'content': question}]
        )
    print(completion.model_dump_json())

def segment_document(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        segments = re.split(r'\.\n', content)
        
        counter = 0
        output_segments = []
        current_segment = ""
        
        for segment in segments:
            current_segment += segment.strip() + "\n"
            counter += 1
            
            if counter == 10:
                output_segments.append(current_segment.rstrip())
                current_segment = ""
                counter = 0
        
        if current_segment:
            output_segments.append(current_segment.rstrip())
        
        for i, segment in enumerate(output_segments):
            get_response("翻译成中文:"+segment)
            #print(segment)
            #if i < len(output_segments) - 1:
            #    print('%%%' * 40)
            
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python script.py <文件路径>")
    else:
        file_path = sys.argv[1]
        segment_document(file_path)
