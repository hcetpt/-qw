SPDX 许可证标识符: GPL-2.0

============================================
AMD HSMP 接口
============================================

AMD 的较新型号 Fam19h EPYC 服务器处理器支持通过 HSMP（主机系统管理端口）实现系统管理功能。主机系统管理端口 (HSMP) 是一种接口，它为操作系统级别的软件提供了通过一组邮箱寄存器访问系统管理功能的途径。
更多关于此接口的信息可以在家族/型号 PPR 的 "7 主机系统管理端口 (HSMP)" 章节中找到，例如：https://www.amd.com/content/dam/amd/en/documents/epyc-technical-docs/programmer-references/55898_B1_pub_0_50.zip


HSMP 接口仅在 EPYC 服务器 CPU 型号上得到支持。
HSMP 设备
============================================

位于 `drivers/platforms/x86/` 下的 amd_hsmp 驱动创建了一个杂项设备 `/dev/hsmp` ，以允许用户空间程序运行 HSMP 邮箱命令。
```
$ ls -al /dev/hsmp
crw-r--r-- 1 root root 10, 123 Jan 21 21:41 /dev/hsmp
```

设备节点的特点：
* 写模式用于运行设置/配置命令。
* 读模式用于运行获取/状态监控命令。

访问限制：
* 只有 root 用户被允许以写模式打开文件。
* 文件可以被所有用户以读模式打开。

内核集成：
* 内核中的其他子系统可以使用导出的传输函数 `hsmp_send_message()`。
* 调用者之间的锁定由驱动程序处理。
HSMP sysfs 接口
====================

1. 指标表二进制 sysfs

AMD MI300A MCM 提供了 GET_METRICS_TABLE 消息，用于一次性从 SMU 中检索大部分系统管理信息。
指标表作为一个十六进制的 sysfs 二进制文件提供，在每个插槽的 sysfs 目录下创建，路径为 `/sys/devices/platform/amd_hsmp/socket%d/metrics_bin`。

注意：不支持 lseek()，因为整个指标表将被读取。
### 公共PPR文档中的指标表定义
公共PPR文档中将记录指标表的定义。
同样的定义也在`amd_hsmp.h`头文件中给出。
#### 示例

##### 从C程序访问hsmp设备
首先，你需要包含以下头文件：

```c
#include <linux/amd_hsmp.h>
```

该头文件定义了支持的消息/消息ID。
接下来，打开设备文件，如下所示：

```c
int file;

file = open("/dev/hsmp", O_RDWR);
if (file < 0) {
    /* 错误处理；你可以检查errno来了解发生了什么错误 */
    exit(1);
}
```

定义了以下的IO控制命令：

```c
ioctl(file, HSMP_IOCTL_CMD, struct hsmp_message *msg)
```

其中参数是一个指向以下结构体的指针：

```c
struct hsmp_message {
    __u32   msg_id;               /* 消息ID */
    __u16   num_args;             /* 消息中输入参数的数量 */
    __u16   response_sz;          /* 预期输出/响应的数量 */
    __u32   args[HSMP_MAX_MSG_LEN]; /* 参数/响应缓冲区 */
    __u16   sock_ind;             /* 套接字编号 */
};
```

如果失败，ioctl会返回非零值；你可以通过读取errno来了解发生了什么。成功时，交易返回0。
更多关于接口和消息定义的详细信息可以在相应家族/型号PPR的第“7章 主机系统管理端口(HSMP)”中找到，例如：https://www.amd.com/content/dam/amd/en/documents/epyc-technical-docs/programmer-references/55898_B1_pub_0_50.zip

用户空间的C-APIs可以通过链接esmi库获得，该库由E-SMS项目提供：https://www.amd.com/en/developer/e-sms.html
详情参见：https://github.com/amd/esmi_ib_library
