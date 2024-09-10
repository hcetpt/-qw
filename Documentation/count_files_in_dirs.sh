#!/bin/bash

# 函数用于递归计算并打印目录下的文件数量
count_files() {
    local dir=$1
    local count=$(find "$dir" -type f | wc -l)
    echo "$dir: $count"
}

# 遍历当前目录下的所有子目录，并对每个子目录调用count_files函数
for dir in */; do
    if [ -d "$dir" ]; then
        count_files "$dir"
    fi
done

