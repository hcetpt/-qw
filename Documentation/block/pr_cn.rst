持续预留的块层支持
===============================================

Linux 内核支持用户空间接口，以简化与支持此类功能（如 SCSI）的块设备对应的持续预留。持续预留允许在共享存储设置中将对块设备的访问限制给特定的发起者。
本文档提供了一般性的支持ioctl命令概述。对于更详细的参考，请参阅SCSI主要命令标准，特别是关于预留的部分以及“PERSISTENT RESERVE IN”和“PERSISTENT RESERVE OUT”命令。
所有实现都应确保在电源丢失后，预留仍然有效，并且覆盖多路径环境中的所有连接。这些行为在SPC中是可选的，但在Linux中会自动应用。
以下类型的预留被支持：
--------------------------------------------------

 - PR_WRITE_EXCLUSIVE
	只有拥有该预留的发起者可以写入设备。任何发起者都可以从设备读取数据。
- PR_EXCLUSIVE_ACCESS
	只有拥有该预留的发起者可以访问设备。
- PR_WRITE_EXCLUSIVE_REG_ONLY
	只有注册了密钥的发起者可以写入设备，任何发起者都可以从设备读取数据。
- PR_EXCLUSIVE_ACCESS_REG_ONLY
	只有注册了密钥的发起者可以访问设备。
- PR_WRITE_EXCLUSIVE_ALL_REGS

	只有注册了密钥的发起者可以写入设备，任何发起者都可以从设备读取数据。
所有已注册密钥的发起者都被视为保留持有者。

如果您想要使用这种类型，请参考SPC规范中关于保留持有者的定义。

- PR_EXCLUSIVE_ACCESS_ALL_REGS
仅已注册密钥的发起者可以访问该设备。
所有已注册密钥的发起者都被视为保留持有者。
如果您想要使用这种类型，请参考SPC规范中关于保留持有者的定义。

以下ioctl命令被支持：
------------------------------

1. IOC_PR_REGISTER
^^^^^^^^^^^^^^^^^^

此ioctl命令如果new_key参数非空，则注册一个新的保留。如果没有现有保留存在，old_key必须为零；如果要替换现有保留，old_key必须包含旧的保留密钥。
如果new_key参数为0，则取消注册由old_key传入的现有保留。
2. IOC_PR_RESERVE
^^^^^^^^^^^^^^^^^

此ioctl命令根据type参数保留设备，从而限制其他设备的访问。key参数必须是通过IOC_PR_REGISTER、IOC_PR_REGISTER_IGNORE、IOC_PR_PREEMPT或IOC_PR_PREEMPT_ABORT命令获取的现有设备保留密钥。
3. IOC_PR_RELEASE
^^^^^^^^^^^^^^^^^

此ioctl命令根据key和flags释放指定的保留，从而移除由此带来的任何访问限制。
4. IOC_PR_PREEMPT
^^^^^^^^^^^^^^^^^

此ioctl命令释放由old_key引用的现有保留，并用type类型的new_key新保留取代它。
### IOC_PR_PREEMPT_ABORT
^^^^^^^^^^^^^^^^^^^^^^^

此ioctl命令的工作方式与IOC_PR_PREEMPT相同，但还会终止通过由`old_key`标识的连接发送的任何未完成的命令。

### IOC_PR_CLEAR
^^^^^^^^^^^^^^^

此ioctl命令会取消注册`key`以及与设备注册的任何其他预留键，并且会取消任何现有的预留。

### 标志
-----

所有的ioctl命令都有一个标志字段。目前仅支持一个标志：

- `PR_FL_IGNORE_KEY`
    忽略现有的预留键。这通常被`IOC_PR_REGISTER`所支持，某些实现可能会在`IOC_PR_RESERVE`中也支持该标志。

对于所有未知的标志，内核将返回`-EOPNOTSUPP`。
