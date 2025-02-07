I2C/SMBUS 故障代码
=====================

这是在 I2C/SMBus 栈中使用故障代码最重要的约定的总结。
“故障”并不总是“错误”
----------------------------------
并非所有的故障报告都意味着错误；“页面故障”应该是一个熟悉的例子。软件经常在遇到短暂故障后重试幂等操作。在某些情况下，可能有更复杂的恢复方案是适当的，例如重新初始化（甚至可能重启）。在由故障报告触发这样的恢复之后，并没有错误发生。

以类似的方式，有时一个“故障”代码只是报告了一个操作定义的结果……它并不表示有任何问题，只是结果不在“理想路径”上。

简而言之，你的 I2C 驱动程序代码可能需要了解这些代码以便正确响应。其他代码可能依赖于你的代码报告正确的故障代码，这样它才能反过来正确运行。

I2C 和 SMBus 故障代码
-------------------------
这些通常作为负数返回，零或某个正数则表示非故障返回。这些符号所对应的特定数字在不同的架构之间有所不同，尽管大多数 Linux 系统使用 `<asm-generic/errno*.h>` 中的编号。

请注意，这里的描述并不详尽。还可能存在其他返回代码的情况，以及应返回这些代码的其他情况。但是，对于这些情况，驱动程序不应返回其他代码（除非硬件不提供唯一的故障报告）。

另外，适配器探测方法返回的代码遵循其主机总线（如 PCI 或平台总线）特有的规则。

EAFNOSUPPORT
	当 I2C 适配器不支持 10 位地址却请求使用此类地址时返回。

EAGAIN
	当 I2C 适配器在主传输模式下失去仲裁时返回：另一个主设备在同一时间发送了不同的数据。

同样地，在原子上下文中尝试调用 I2C 操作时返回，此时已经有任务正在使用该 I2C 总线执行其他操作。
EBADMSG  
当接收到无效的包错误码字节时，由SMBus逻辑返回。此代码是覆盖交易中所有字节的CRC校验，并在终止STOP之前发送。此故障仅在读取交易中报告；SMBus从设备可能有一种方式来报告主机写入时的PEC不匹配。请注意，即使使用了PEC，您也不应仅仅依赖它们作为检测数据传输错误的唯一方法。

EBUSY  
当总线忙的时间超过允许的时间时，由SMBus适配器返回。这通常表明某个设备（可能是SMBus适配器）需要一些故障恢复措施（例如重置），或者尝试重置但失败。

EINVAL  
此较为模糊的错误意味着在开始任何I/O操作之前检测到一个无效参数。尽可能使用更具体的错误代码。

EIO  
此较为模糊的错误意味着在执行I/O操作时出现问题。尽可能使用更具体的错误代码。

ENODEV  
由驱动程序probe()方法返回。与ENXIO相比，这个错误稍微具体一些，意味着问题不在于地址，而在于在该地址上找到的设备。驱动程序probe()可能会验证设备是否返回正确的响应，并根据情况返回此错误。（如果probe()返回除ENXIO和ENODEV之外的错误，驱动核心会发出警告。）

ENOMEM  
由任何无法在其需要时分配内存的组件返回。

ENXIO  
由I2C适配器返回，表示传输的地址阶段没有接收到ACK。虽然它可能仅仅意味着I2C设备暂时未响应，但通常意味着该地址没有任何监听者。
同样，由驱动程序probe()方法返回，以表示它们未找到要绑定的设备。（也可以使用ENODEV。）

EOPNOTSUPP  
当被要求执行其不支持或无法支持的操作时，由适配器返回。
例如，当一个不支持SMBus块传输的适配器被要求执行此类传输时，会返回此错误。在这种情况下，提出该块传输请求的驱动程序应在提出请求之前验证该功能是否受支持。
类似地，如果I2C适配器无法执行所有合法的I2C消息，则在被要求执行其无法完成的交易时应返回此错误。（这些限制不能从适配器的功能掩码中看出，因为假设如果适配器支持I2C，则支持所有的I2C特性。）

EPROTO  
当从设备不符合相关的I2C或SMBus（或芯片特定）协议规范时返回。一种情况是SMBus块数据响应（来自SMBus从设备）的长度超出1-32字节的范围。

ESHUTDOWN  
当使用已暂停的适配器请求传输时返回。
"ETIMEDOUT"
这是驱动程序在某个操作耗时过长并在完成之前被中止时返回的错误。
SMBus 适配器可能会在某个操作超出 SMBus 规范允许的时间时返回此错误；例如，当一个从设备过度拉伸时钟周期。I2C 没有这样的超时限制，但 I2C 适配器通常也会设定一些任意的限制（这些限制比 SMBus 长得多）。
