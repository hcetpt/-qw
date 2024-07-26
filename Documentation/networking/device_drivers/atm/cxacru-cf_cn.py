```python
#!/usr/bin/env python
# 版权 2009 Simon Arlott

#
# 本程序为自由软件；你可以根据自由软件基金会发布的GNU通用公共许可证的条款重新发布和/或修改它，
# 许可证版本为第2版，或者（由您选择）任何更新的版本。
#
# 本程序是希望它有用而分发的，但不附带任何保证；甚至不默示保证其适销性或适合于某一特定目的。
# 有关详细信息，请参见GNU通用公共许可证。
#
# 您应该已随同本程序收到了一份GNU通用公共许可证的副本；如果没有，请写信给自由软件基金会,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA
#
# 使用方法: cxacru-cf.py < cxacru-cf.bin
# 输出: 适用于sysfs adsl_config属性的值字符串
#
# 警告: MD5哈希值为cdbac2689969d5ed5d4850f117702110的cxacru-cf.bin文件包含未对齐的值，这将阻止调制解调器建立连接。
# 如果删除第一个和最后一个两个字节，则这些值变为有效，但是会强制调制方式为ANSI T1.413，这可能不适合所有情况。
#
# 原始二进制格式是一个le32值的紧凑列表
import sys
import struct

i = 0
while True:
    buf = sys.stdin.read(4)

    if len(buf) == 0:
        break
    elif len(buf) != 4:
        sys.stdout.write("\n")
        sys.stderr.write("错误: 读取{0}字节而非4字节\n".format(len(buf)))
        sys.exit(1)

    if i > 0:
        sys.stdout.write(" ")
    sys.stdout.write("{0:x}={1}".format(i, struct.unpack("<I", buf)[0]))
    i += 1

sys.stdout.write("\n")
```

这是您提供的Python脚本的中文翻译。请注意，代码注释已尽可能地进行了准确翻译，以保持原文的意思。
