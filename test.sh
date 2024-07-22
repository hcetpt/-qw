#!/bin/bash

segment_text_file() {
    # 检查是否提供了文件路径参数
    if [ "$#" -ne 1 ]; then
        echo "使用方法: segment_text_file <文件路径>"
        return 1
    fi

    local file_path="$1"
    local counter=0
    local segment=""
    
    # 读取文件每一行
    while IFS= read -r line; do
        segment+="$line\n"
        # 搜索行中包含的".\n"次数，这里简化处理，直接计数换行符作为分段依据
        # 注意：实际按".\n"分段需复杂匹配，这里仅示意
        counter=$((counter + $(grep -o "\.\n" <<< "$line" | wc -l)))
        
        # 每达到10个换行符（近似代表10个段落结束），打印当前段并重置
        if [ "$counter" -ge 10 ]; then
            echo -e "$segment"
            segment=""
            counter=0
        fi
    done < "$file_path"

    # 打印最后一个未完成的段（如果有的话）
    if [ -n "$segment" ]; then
        echo -e "$segment"
    fi
}

segment_text_file "/home/orangepi/share/qw/Documentation/arch/arm64/features.rst"
# 示例使用
# segment_text_file "/path/to/your/document.rst"
