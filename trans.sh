#!/bin/bash

# 检查是否提供了一个路径参数
if [ "$#" -ne 1 ]; then
    echo "使用方法: $0 <路径>"
    exit 1
fi

# 存储输入的路径
path="$1"

# 使用find命令查找所有文件（包括子目录中的），并将结果保存到数组中
mapfile -t files < <(find "$path" -type f)

# 检查是否找到文件
if [ ${#files[@]} -eq 0 ]; then
    echo "没有找到文件。"
else
    # 遍历文件数组，并将每个文件路径作为参数传递给qw脚本
    for file in "${files[@]}"; do
        ./qw "$file"
    done
fi


# 分段函数，将文件内容进行分段
greet() {
    # 函数体内部，$1 代表传递给函数的第一个参数
    echo "Hello, $1!"
}

# 调用函数greet，并传递参数"World"
:greet "World"

# 如果你想调用函数并传递其他变量作为参数也是可以的
username="Alice"
greet "$username"


# 翻译函数，获取要翻译的内容，通过qw进行翻译


# 保存函数，翻译完成后，将临时存储的内容存到原文件名_cn.后缀
create_cn_version() {
    # 检查是否提供了文件路径参数
    if [ "$#" -ne 1 ]; then
        echo "使用方法: create_cn_version <文件路径>"
        return 1
    fi

    local original_file="$1"
    # 获取文件的基本名称和扩展名
    local base_name=$(basename -- "$original_file")
    local extension="${base_name##*.}"
    local name_no_ext="${base_name%.*}"

    # 构建新文件名
    local new_file_name="${name_no_ext}_cn.${extension}"
    local new_file_path=$(dirname "$original_file")"/"${new_file_name}

    # 创建新文件（这里只是touch创建空文件，根据需要可以写入内容）
    touch "$new_file_path"
    if [ $? -eq 0 ]; then
        echo "新文件已创建: $new_file_path"
    else
        echo "创建文件时发生错误。"
        return 1
    fi
}

# 示例使用
# 假设你要基于一个示例文件创建中文版
# create_cn_version "/path/to/your/original_file.txt"
