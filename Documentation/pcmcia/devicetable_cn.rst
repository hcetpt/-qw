============= 
设备表 
============= 

PCMCIA 设备与驱动程序之间的匹配使用以下一个或多个标准进行：

- 制造商ID
- 卡ID
- 产品ID字符串及其哈希值
- 功能ID
- 设备功能（实际和伪功能）

你应该使用 `include/pcmcia/device_id.h` 中的辅助函数来生成将设备与驱动程序匹配的 `struct pcmcia_device_id[]` 元素。
如果你想匹配产品ID字符串，还需要将字符串的crc32哈希值传递给宏，例如，如果你想匹配产品ID字符串 "1"，你需要使用

```c
PCMCIA_DEVICE_PROD_ID1("some_string", 0x(hash_of_some_string)),
```

如果哈希值不正确，内核会在模块初始化时通过 "dmesg" 告知你，并告诉你正确的哈希值。
你可以通过查看PCMCIA设备的sysfs目录下的 "modalias" 文件来确定产品ID字符串的哈希值。它会生成如下形式的字符串：
```
pcmcia:m0149cC1ABf06pfn00fn00pa725B842DpbF1EFEE84pc0877B627pd00000000
```

在 "pa" 后面的十六进制值是产品ID字符串1的哈希值，在 "pb" 后面的是字符串2的哈希值，依此类推。
或者，你可以使用 `crc32hash`（参见 `tools/pcmcia/crc32hash.c`）来确定crc32哈希值。只需将你想评估的字符串作为参数传递给这个程序，例如：
```
$ tools/pcmcia/crc32hash "Dual Speed"
```
