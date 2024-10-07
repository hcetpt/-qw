MSR 跟踪事件
=============

x86 内核支持跟踪大多数 MSR（模型特定寄存器）访问。
要查看 Intel 系统上 MSR 的定义，请参阅 SDM（软件开发手册），链接如下：https://www.intel.com/sdm （第三卷）

可用的跟踪点：

/sys/kernel/tracing/events/msr/

跟踪 MSR 读取：

read_msr

  - msr: MSR 编号
  - val: 读取的值
  - failed: 访问失败则为 1，否则为 0

跟踪 MSR 写入：

write_msr

  - msr: MSR 编号
  - val: 写入的值
  - failed: 访问失败则为 1，否则为 0

在内核中跟踪 RDPMC：

rdpmc

跟踪数据可以使用 postprocess/decode_msr.py 脚本进行后处理：

```
cat /sys/kernel/tracing/trace | decode_msr.py /usr/src/linux/include/asm/msr-index.h
```

以添加符号化的 MSR 名称
