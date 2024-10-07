```python
#!/usr/bin/env python
# 版权 2009 Simon Arlott

# 本程序是自由软件；您可以根据自由软件基金会发布的GNU通用公共许可证的条款重新分发和/或修改它；
# 可以选择使用许可证的第2版，也可以选择使用任何更新的版本。
#
# 本程序以希望对您有所帮助，但没有任何形式的保证；甚至不保证适销性或适合于某一特定目的。
# 更多细节请参见GNU通用公共许可证。
#
# 您应该已经随同本程序收到了一份GNU通用公共许可证的副本；如果没有，请写信给自由软件基金会，
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#
# 使用方法: cxacru-cf.py < cxacru-cf.bin
# 输出: 适用于sysfs adsl_config属性的值字符串
#
# 警告: MD5哈希值为cdbac2689969d5ed5d4850f117702110的cxacru-cf.bin文件包含未对齐的值，
# 这将阻止调制解调器建立连接。如果去掉前两个字节和最后两个字节，则这些值会变为有效值，
# 但是调制方式将被强制为仅支持ANSI T1.413标准，这可能不适合所有情况。
#
# 原始二进制格式是一个le32值的打包列表
import sys
import struct

i = 0
while True:
    buf = sys.stdin.read(4)

    if len(buf) == 0:
        break
    elif len(buf) != 4:
        sys.stdout.write("\n")
        sys.stderr.write("错误: 读取了{0}字节而非4字节\n".format(len(buf)))
        sys.exit(1)

    if i > 0:
        sys.stdout.write(" ")
    sys.stdout.write("{0:x}={1}".format(i, struct.unpack("<I", buf)[0]))
    i += 1

sys.stdout.write("\n")
```
