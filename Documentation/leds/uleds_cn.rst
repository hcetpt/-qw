用户空间LEDs
=============

uleds驱动支持用户空间的LEDs。这在测试触发器时非常有用，也可以用于实现虚拟LEDs。

使用方法
==========

当驱动加载后，会在/dev/uleds创建一个字符设备。要创建一个新的LED类设备，打开/dev/uleds并写入一个uleds_user_dev结构（在内核公共头文件linux/uleds.h中找到）：

```c
#define LED_MAX_NAME_SIZE 64

struct uleds_user_dev {
    char name[LED_MAX_NAME_SIZE];
};
```

将根据给定的名字创建一个新的LED类设备。这个名字可以是任何有效的sysfs设备节点名，但建议使用LED类命名规范："devicename:color:function"

当前亮度通过从字符设备读取单个字节获得。值为无符号：0到255。读取会阻塞直到亮度变化。当亮度值改变时，设备节点也可以被轮询以进行通知。

当关闭/dev/uleds的打开文件句柄时，LED类设备将被移除。

通过打开更多的/dev/uleds文件句柄可以创建多个LED类设备。

参见tools/leds/uledmon.c中的用户空间程序示例。
