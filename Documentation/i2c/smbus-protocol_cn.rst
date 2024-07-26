### SMBus 协议

以下是对 SMBus 协议的概述。它适用于所有版本的协议（1.0、1.1 和 2.0）。
本文档末尾简要描述了该软件包不支持的某些协议特性。
某些适配器仅理解 SMBus（系统管理总线）协议，这是 I2C 协议的一个子集。幸运的是，许多设备也只使用这个子集，这使得将它们放置在 SMBus 上成为可能。
如果你为某个 I2C 设备编写驱动程序，请尽量使用 SMBus 命令（如果设备只使用 I2C 协议的这一子集的话）。这样就可以在 SMBus 适配器和 I2C 适配器上使用设备驱动程序（在 I2C 适配器上 SMBus 命令集会自动转换为 I2C，但在大多数纯 SMBus 适配器上无法处理纯粹的 I2C 命令）。

下面是 SMBus 协议操作列表及其执行函数。请注意，SMBus 协议规范中使用的名称通常与这些函数名称不符。对于某些传递单个数据字节的操作，使用 SMBus 协议操作名称的函数实际上执行的是不同的协议操作。
每种事务类型都对应一个功能标志。在调用事务函数之前，设备驱动程序应始终检查（仅一次）相应的功能标志，以确保底层 I2C 适配器支持所讨论的事务。详情请参阅 `Documentation/i2c/functionality.rst`。

#### 符号说明

- **S**：起始条件
- **Sr**：重复起始条件，用于从写模式切换到读模式
- **P**：停止条件
- **Rd/Wr (1 bit)**：读/写位。读取等于 1，写入等于 0
- **A, NA (1 bit)**：确认（ACK）和非确认（NACK）位
- **Addr (7 bits)**：I2C 7 位地址。请注意，这可以扩展以获取 10 位 I2C 地址
- **Comm (8 bits)**：命令字节，一个数据字节，通常用于选择设备上的寄存器
数据 (8 位)   一个普通的数据字节。DataLow 和 DataHigh 分别代表一个 16 位字的低位字节和高位字节。
计数 (8 位)   包含块操作长度的一个数据字节
[...]         由 I2C 设备发送的数据，而非由主机适配器发送的数据
=============== =============================================================

SMBus 快速命令
==============

这会向设备发送一位数据，替代读/写位：

  S 地址 Rd/Wr [A] P

功能标志：I2C_FUNC_SMBUS_QUICK

SMBus 接收字节
==============

通过 i2c_smbus_read_byte() 实现

这从设备读取一个字节，不指定设备寄存器。有些设备非常简单以至于这个接口就足够了；对于其他设备，如果你想要读取与前一个 SMBus 命令相同的寄存器，这是一个简写形式：

  S 地址 Rd [A] [数据] NA P

功能标志：I2C_FUNC_SMBUS_READ_BYTE

SMBus 发送字节
==============

通过 i2c_smbus_write_byte() 实现

此操作与接收字节相反：它向设备发送一个字节。更多详情请参考接收字节部分：

  S 地址 Wr [A] 数据 [A] P

功能标志：I2C_FUNC_SMBUS_WRITE_BYTE

SMBus 读取字节
==============

通过 i2c_smbus_read_byte_data() 实现

这从指定寄存器读取一个字节。寄存器是通过通信字指定的：

  S 地址 Wr [A] 通信 [A] Sr 地址 Rd [A] [数据] NA P

功能标志：I2C_FUNC_SMBUS_READ_BYTE_DATA

SMBus 读取字
=============

通过 i2c_smbus_read_word_data() 实现

此操作类似于读取字节；同样，数据是从指定寄存器读取的，该寄存器通过通信字指定。但这一次，数据是一个完整的字（16 位）：

  S 地址 Wr [A] 通信 [A] Sr 地址 Rd [A] [数据低位] A [数据高位] NA P

功能标志：I2C_FUNC_SMBUS_READ_WORD_DATA

注意有一个方便的函数 i2c_smbus_read_word_swapped() 可用于在两个数据字节顺序相反的情况下的读取操作（不符合 SMBus 规范，但非常流行）。

SMBus 写入字节
==============

通过 i2c_smbus_write_byte_data() 实现

这将一个字节写入到指定寄存器的设备中。寄存器是通过通信字指定的。这与读取字节操作相反：

  S 地址 Wr [A] 通信 [A] 数据 [A] P

功能标志：I2C_FUNC_SMBUS_WRITE_BYTE_DATA

SMBus 写入字
=============

通过 i2c_smbus_write_word_data() 实现

这是读取字操作的相反操作。16 位的数据被写入到指定寄存器的设备中，该寄存器通过通信字指定：

  S 地址 Wr [A] 通信 [A] 数据低位 [A] 数据高位 [A] P

功能标志：I2C_FUNC_SMBUS_WRITE_WORD_DATA

注意有一个方便的函数 i2c_smbus_write_word_swapped() 可用于在两个数据字节顺序相反的情况下的写入操作（不符合 SMBus 规范，但非常流行）。

SMBus 进程调用
==============

此命令选择一个设备寄存器（通过通信字），向其发送 16 位数据，并返回 16 位数据：

  S 地址 Wr [A] 通信 [A] 数据低位 [A] 数据高位 [A]
                               Sr 地址 Rd [A] [数据低位] A [数据高位] NA P

功能标志：I2C_FUNC_SMBUS_PROC_CALL

SMBus 块读取
=============

通过 i2c_smbus_read_block_data() 实现

此命令从指定寄存器读取最多 32 字节的数据，该寄存器通过通信字指定。数据量由设备在计数字节中指定：

  S 地址 Wr [A] 通信 [A]
            Sr 地址 Rd [A] [计数] A [数据] A [数据] A ... A [数据] NA P

功能标志：I2C_FUNC_SMBUS_READ_BLOCK_DATA

SMBus 块写入
=============

通过 i2c_smbus_write_block_data() 实现

此操作与块读取命令相反，它将最多 32 字节的数据写入到指定寄存器的设备中，该寄存器通过通信字指定。数据量在计数字节中指定：

  S 地址 Wr [A] 通信 [A] 计数 [A] 数据 [A] 数据 [A] ... [A] 数据 [A] P

功能标志：I2C_FUNC_SMBUS_WRITE_BLOCK_DATA

SMBus 块写入 - 块读取进程调用
==================================

SMBus 块写入 - 块读取进程调用是在规范修订版 2.0 中引入的
此命令选择一个设备寄存器（通过通信字），向其发送 1 至 31 字节的数据，并返回 1 至 31 字节的数据：

  S 地址 Wr [A] 通信 [A] 计数 [A] 数据 [A] ...
Sr Addr Rd [A] [Count] A [Data] ... A P

功能标志：I2C_FUNC_SMBUS_BLOCK_PROC_CALL


SMBus 主机通知
==============

此命令由作为主设备的 SMBus 设备发送给作为从设备的 SMBus 主机。
其形式与“写入字”相同，只是将命令码替换为触发警报的设备地址：
```
[S] [HostAddr] [Wr] A [DevAddr] A [DataLow] A [DataHigh] A [P]
```

在 Linux 内核中是这样实现的：

* 支持 SMBus 主机通知的 I2C 总线驱动应报告 I2C_FUNC_SMBUS_HOST_NOTIFY；
* I2C 总线驱动通过调用 i2c_handle_smbus_host_notify() 触发 SMBus 主机通知；
* 如果没有其他指定，则支持触发 SMBus 主机通知的 I2C 设备驱动会将 client->irq 分配给主机通知中断。目前尚无办法从客户端获取数据参数。

包错误校验 (PEC)
==================

包错误校验是在规范的修订版 1.1 中引入的。
PEC 在使用它的传输的终止 STOP 前立即添加了一个 CRC-8 错误校验字节。

地址解析协议 (ARP)
====================

地址解析协议是在规范的修订版 2.0 中引入的。它是一个高层协议，利用了上述消息。
ARP 为协议添加了设备枚举和动态地址分配功能。所有 ARP 通信都使用从设备地址 0x61，并且需要 PEC 校验和。
SMBus 警报
==========

SMBus 警报在规范的第1.0版中被引入。
SMBus警报协议允许多个SMBus从设备共享SMBus主设备上的一个中断引脚，同时仍能让主设备知道是哪个从设备触发了中断。
在Linux内核中，这是通过以下方式实现的：

* 支持SMBus警报的I2C总线驱动应该调用i2c_new_smbus_alert_device()来安装SMBus警报支持。
* 触发SMBus警报的设备的I2C驱动应该实现可选的alert()回调函数。

I2C 块传输
==========

下面介绍的I2C块传输类似于SMBus块读和写操作，但这些操作不包含计数字节。它们由SMBus层支持，并在此处为了完整性进行描述，但它们**不是**由SMBus规范定义的。
I2C块传输不限制传输的字节数量，但SMBus层将限制设置为最多32个字节。

I2C 块读取
==========

通过i2c_smbus_read_i2c_block_data()实现。

此命令从指定寄存器读取一块字节数据，该寄存器通过通信字节（Comm）指定：
```
S Addr Wr [A] Comm [A]
            Sr Addr Rd [A] [Data] A [Data] A ... A [Data] NA P
```

功能标志：I2C_FUNC_SMBUS_READ_I2C_BLOCK

I2C 块写入
==========

通过i2c_smbus_write_i2c_block_data()实现。

与块读取命令相反，此操作向指定寄存器写入字节数据，该寄存器通过通信字节（Comm）指定。需要注意的是，长度为0、2或更多字节的命令是受支持的，因为它们与数据不可区分：
```
S Addr Wr [A] Comm [A] Data [A] Data [A] ... [A] Data [A] P
```

功能标志：I2C_FUNC_SMBUS_WRITE_I2C_BLOCK
