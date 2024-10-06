用户空间 LED
=============

uleds 驱动支持用户空间的 LED。这对于测试触发器非常有用，也可以用于实现虚拟 LED。
用法
=====

当驱动加载时，会在 /dev/uleds 创建一个字符设备。要创建一个新的 LED 类设备，请打开 /dev/uleds 并向其中写入一个 uleds_user_dev 结构体（在内核公共头文件 linux/uleds.h 中定义）：

```c
#define LED_MAX_NAME_SIZE 64

struct uleds_user_dev {
    char name[LED_MAX_NAME_SIZE];
};
```

将根据提供的名称创建一个新的 LED 类设备。名称可以是任何有效的 sysfs 设备节点名称，但建议使用 LED 类命名约定 "devicename:color:function"。
当前的亮度可以通过从字符设备读取一个字节来获取。值为无符号整数：0 到 255。读取操作会阻塞直到亮度发生变化。也可以轮询设备节点以通知亮度值的变化。
当关闭 /dev/uleds 的打开文件句柄时，LED 类设备将被移除。
通过打开更多的 /dev/uleds 文件句柄可以创建多个 LED 类设备。
请参阅 tools/leds/uledmon.c 获取一个示例用户空间程序。
