#!/bin/bash

# 保存函数，翻译完成后，将临时存储的内容存到原文件名_cn.后缀
create_cn_version() {
    # 检查是否提供了文件路径参数
    if [ "$#" -ne 1 ]; then
        echo "使用方法: create_cn_version <文件路径>"
        return 1
    fi

    local original_file="$1"
    # 获取文件的基本名称
    local base_name=$(basename -- "$original_file")

    # 检查文件是否有扩展名
    if [[ "$base_name" == *.* ]]; then
        local extension="${base_name##*.}"
        local name_no_ext="${base_name%.*}"
        local new_file_name="${name_no_ext}_cn.${extension}"
    else
        local new_file_name="${base_name}_cn"
    fi

    # 构建新文件路径
    local new_file_path=$(dirname "$original_file")"/"${new_file_name}

    # 检查是否已经存在该文件并且不为空
    if [ -f "$new_file_path" ] && [ ! -z "$(cat "$new_file_path")" ]; then
        echo "文件已存在且非空: $new_file_path"
        return 0
    fi

    # 创建新文件
    touch "$new_file_path"
    if [ $? -eq 0 ]; then
        echo "新文件已创建: $new_file_path"
    else
        echo "创建文件时发生错误。"
        return 1
    fi
}

# 检查是否提供了一个路径参数
if [ "$#" -ne 1 ]; then
    echo "使用方法: $0 <路径>"
    exit 1
fi

# 存储输入的路径
path="$1"

# 使用find命令查找所有文件（包括子目录中的），排除隐藏文件，并将结果保存到数组中
mapfile -t files < <(find "$path" -type f ! -name '.*')

# 检查是否找到文件
if [ ${#files[@]} -eq 0 ]; then
    echo "没有找到文件。"
else
    # 遍历文件数组，并将每个文件路径作为参数传递给 create_cn_version 函数
    for file in "${files[@]}"; do
        create_cn_version "$file"
    done
fi
