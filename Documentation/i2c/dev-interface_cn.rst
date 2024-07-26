在用户空间实现I2C设备驱动程序
============================================

通常，I2C设备由内核驱动程序控制。但也可以通过`/dev`接口从用户空间访问适配器上的所有设备。为此，您需要加载`i2c-dev`模块。
每个注册的I2C适配器都会分配一个编号，从0开始计数。您可以通过检查`/sys/class/i2c-dev/`来查看哪些编号对应哪个适配器。
或者，您可以运行`i2cdetect -l`以获取当前系统中存在的所有I2C适配器的格式化列表。`i2cdetect`是`i2c-tools`包的一部分。
I2C设备文件是主设备号为89的字符设备文件，并且次设备号对应于上述分配的编号。它们应该被称为“i2c-%d”（如i2c-0、i2c-1等）。所有256个次设备号都保留给I2C使用。

C语言示例
=========

假设您想要从C程序访问一个I2C适配器。
首先，您需要包含这两个头文件：

```c
#include <linux/i2c-dev.h>
#include <i2c/smbus.h>
```

接下来，您需要确定要访问哪个适配器。您应该检查`/sys/class/i2c-dev/`或运行`i2cdetect -l`来做决定。
适配器编号是以动态方式分配的，因此您不能对其做出太多假设。这些编号甚至可能从一次启动到下一次启动发生变化。
接下来，打开设备文件，如下所示：

```c
int file;
int adapter_nr = 2; /* 可能是动态确定的 */
char filename[20];

snprintf(filename, 19, "/dev/i2c-%d", adapter_nr);
file = open(filename, O_RDWR);
if (file < 0) {
  /* 错误处理；您可以检查errno以了解出了什么问题 */
  exit(1);
}
```

当您打开了设备后，必须指定与之通信的设备地址：

```c
int addr = 0x40; /* I2C地址 */

if (ioctl(file, I2C_SLAVE, addr) < 0) {
  /* 错误处理；您可以检查errno以了解出了什么问题 */
  exit(1);
}
```

现在，您已经设置好了。您可以使用SMBus命令或简单的I2C与您的设备进行通信。如果设备支持的话，建议优先使用SMBus命令。下面分别展示了这两种方法：

```c
__u8 reg = 0x10; /* 要访问的设备寄存器 */
__s32 res;
char buf[10];

/* 使用SMBus命令 */
res = i2c_smbus_read_word_data(file, reg);
if (res < 0) {
  /* 错误处理：I2C事务失败 */
} else {
  /* res 包含读取的数据 */
}

/*
 * 使用I2C写入，相当于
 * i2c_smbus_write_word_data(file, reg, 0x6543)
 */
buf[0] = reg;
buf[1] = 0x43;
buf[2] = 0x65;
if (write(file, buf, 3) != 3) {
  /* 错误处理：I2C事务失败 */
}

/* 使用I2C读取，相当于i2c_smbus_read_byte(file) */
if (read(file, buf, 1) != 1) {
  /* 错误处理：I2C事务失败 */
} else {
  /* buf[0] 包含读取的字节 */
}
```

请注意，仅有一部分I2C和SMBus协议可以通过read()和write()调用来实现。特别是所谓的组合事务（在同一事务中混合读取和写入消息）不受支持。出于这个原因，此接口几乎从未被用户空间程序使用。

**重要提示**：由于使用了内联函数，编译您的程序时**必须**使用`-O`或其变体！

完整的接口描述
==========================

定义了以下IOCTL请求：

``ioctl(file, I2C_SLAVE, long addr)``
  更改从机地址。地址通过参数的最低7位传递（对于10位地址，则通过参数的最低10位传递）

``ioctl(file, I2C_TENBIT, long select)``
  如果select不等于0则选择10位地址，如果select等于0则选择正常的7位地址。默认值为0。此请求仅在适配器具有I2C_FUNC_10BIT_ADDR功能时有效。
``` 
`ioctl(file, I2C_PEC, long select)`
选择SMBus PEC（包错误检查）生成和验证。
如果 `select` 不等于 0，则启用；如果 `select` 等于 0，则禁用。默认为 0。
仅用于SMBus事务。此请求仅在适配器具有I2C_FUNC_SMBUS_PEC功能时生效；如果没有该功能，它仍然是安全的，只是不会产生任何效果。

`ioctl(file, I2C_FUNCS, unsigned long *funcs)`
获取适配器的功能并将其存入 `*funcs` 中。

`ioctl(file, I2C_RDWR, struct i2c_rdwr_ioctl_data *msgset)`
执行组合读写操作而无需在中间停止。
只有当适配器具有I2C_FUNC_I2C功能时才有效。参数是指向以下结构体的指针：

    struct i2c_rdwr_ioctl_data {
      struct i2c_msg *msgs;  /* 指向简单消息数组的指针 */
      int nmsgs;             /* 需要交换的消息数量 */
    }

`msgs[]` 包含指向数据缓冲区的进一步指针。
函数将根据特定消息中是否设置了I2C_M_RD标志来从或向这些缓冲区写入或读取数据。
每个消息中必须设置从设备地址以及是否使用十位地址模式，这会覆盖上述ioctl命令中设置的值。

`ioctl(file, I2C_SMBUS, struct i2c_smbus_ioctl_data *args)`
如果可能的话，请使用下面描述的 `i2c_smbus_*` 方法代替直接发出ioctl命令。
你可以通过使用read(2)和write(2)调用来进行纯I2C事务。
你不需要传递地址字节；相反，在尝试访问设备之前，通过ioctl I2C_SLAVE设置它。
```
您可以使用以下函数进行SMBus级别的事务（详细信息请参阅文档文件 `smbus-protocol.rst`）：

```plaintext
__s32 i2c_smbus_write_quick(int file, __u8 value);
__s32 i2c_smbus_read_byte(int file);
__s32 i2c_smbus_write_byte(int file, __u8 value);
__s32 i2c_smbus_read_byte_data(int file, __u8 command);
__s32 i2c_smbus_write_byte_data(int file, __u8 command, __u8 value);
__s32 i2c_smbus_read_word_data(int file, __u8 command);
__s32 i2c_smbus_write_word_data(int file, __u8 command, __u16 value);
__s32 i2c_smbus_process_call(int file, __u8 command, __u16 value);
__s32 i2c_smbus_block_process_call(int file, __u8 command, __u8 length,
                                   __u8 *values);
__s32 i2c_smbus_read_block_data(int file, __u8 command, __u8 *values);
__s32 i2c_smbus_write_block_data(int file, __u8 command, __u8 length,
                                 __u8 *values);
```

所有这些事务在失败时返回-1；您可以读取 `errno` 来查看发生了什么。写操作成功时返回0；读操作返回读取的值，除了 `read_block`，它返回读取的值的数量。块缓冲区不需要超过32字节。

上述函数通过链接到由i2c-tools项目提供的libi2c库来提供。详情请参见：[https://git.kernel.org/pub/scm/utils/i2c-tools/i2c-tools.git/](https://git.kernel.org/pub/scm/utils/i2c-tools/i2c-tools.git/)

### 实现细节

对于感兴趣的人，以下是当您使用 `/dev` 接口访问I2C时内核中的代码流程：

1. 您的应用程序打开 `/dev/i2c-N` 并在其上调用 `ioctl()`，如上文“C示例”部分所述。
2. 这些 `open()` 和 `ioctl()` 调用由 i2c-dev 内核驱动处理：参见 `i2c-dev.c:i2cdev_open()` 和 `i2c-dev.c:i2cdev_ioctl()`。您可以将 i2c-dev 视为一个通用的 I2C 芯片驱动，可以从用户空间对其进行编程。
3. 一些 `ioctl()` 调用是用于管理任务，并直接由 i2c-dev 处理。例如 I2C_SLAVE（设置要访问的设备地址）和 I2C_PEC（启用或禁用未来事务的SMBus错误检查）。
4. 其他 `ioctl()` 调用被 i2c-dev 转换为内核中的函数调用。例如 I2C_FUNCS 查询 I2C 适配器的功能，使用 `i2c.h:i2c_get_functionality()`，而 I2C_SMBUS 使用 `i2c-core-smbus.c:i2c_smbus_xfer()` 执行 SMBus 事务。
i2c-dev 驱动负责验证来自用户空间的所有参数的有效性。在这之后，这些从用户空间通过 i2c-dev 的调用与 I2C 芯片驱动直接执行的调用之间没有区别。这意味着 I2C 总线驱动无需实现任何特殊功能以支持来自用户空间的访问。
5. 这些 `i2c.h` 函数是您的 I2C 总线驱动实际实现的包装器。每个适配器必须声明回调函数来实现这些标准调用。`i2c.h:i2c_get_functionality()` 调用 `i2c_adapter.algo->functionality()`，而 `i2c-core-smbus.c:i2c_smbus_xfer()` 调用 `adapter.algo->smbus_xfer()`（如果已实现），否则调用 `i2c-core-smbus.c:i2c_smbus_xfer_emulated()`，后者又调用 `i2c_adapter.algo->master_xfer()`。

在您的 I2C 总线驱动处理完这些请求后，执行流程沿调用链向上运行，几乎不做任何处理，除了由 i2c-dev 对返回的数据（如果有）进行适当格式封装以适应 ioctl 的需求。
