用户空间 LED
==============

uleds 驱动支持用户空间 LED。这可用于测试触发器，也可以用于实现虚拟 LED。
使用方法
=====

当驱动加载时，会在 `/dev/uleds` 创建一个字符设备。要创建一个新的 LED 类设备，请打开 `/dev/uleds` 并向其中写入 `uleds_user_dev` 结构体（可在内核公共头文件 `linux/uleds.h` 中找到）：

```c
#define LED_MAX_NAME_SIZE 64

struct uleds_user_dev {
    char name[LED_MAX_NAME_SIZE];
};
```

将根据给定的名字创建一个新的 LED 类设备。名字可以是任何有效的 sysfs 设备节点名称，但建议使用 LED 类的命名约定 “devicename:color:function”。
当前的亮度可通过从该字符设备读取一个字节来获取。值为无符号数：0 到 255。读取操作会阻塞直到亮度发生变化。当亮度值变化时，也可以对该设备节点进行轮询以接收通知。
当关闭对 `/dev/uleds` 的打开文件句柄时，LED 类设备将被移除。
通过向 `/dev/uleds` 打开额外的文件句柄，可以创建多个 LED 类设备。
请参阅 `tools/leds/uledmon.c` 了解用户空间程序示例。
