```python
#!/usr/bin/env python
# 为 trace 中的 read_msr 和 write_msr 添加符号名称
# 使用：decode_msr msr-index.h < trace

import sys
import re

msrs = dict()

# 打开 MSR 索引文件
with open(sys.argv[1] if len(sys.argv) > 1 else "msr-index.h", "r") as f:
    for line in f:
        match = re.match(r'#define (MSR_\w+)\s+(0x[0-9a-fA-F]+)', line)
        if match:
            msrs[int(match.group(2), 16)] = match.group(1)

# 额外的 MSR 范围
extra_ranges = (
    ("MSR_LASTBRANCH_%d_FROM_IP", 0x680, 0x69F),
    ("MSR_LASTBRANCH_%d_TO_IP", 0x6C0, 0x6DF),
    ("LBR_INFO_%d", 0xDC0, 0xDDF),
)

# 处理输入数据
for line in sys.stdin:
    match = re.search(r'(read|write)_msr:\s+([0-9a-f]+)', line)
    if match:
        result = None
        number = int(match.group(2), 16)
        if number in msrs:
            result = msrs[number]
        else:
            for er in extra_ranges:
                if er[1] <= number <= er[2]:
                    result = er[0] % (number - er[1])
                    break
        if result:
            line = line.replace(" " + match.group(2), " " + result + "(" + match.group(2) + ")")
    print(line, end='')
```

这段代码将为 `trace` 文件中的 `read_msr` 和 `write_msr` 操作添加符号名称。它从 `msr-index.h` 文件中读取 MSR 的定义，并在处理 `trace` 文件时替换相应的数值。
