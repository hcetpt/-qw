Linux I2C 从设备接口描述
=====================================

由 Wolfram Sang <wsa@sang-engineering.com> 在 2014-15 年编写

如果所使用的 I2C 控制器具备从设备功能，Linux 也可以作为 I2C 从设备。要实现这一功能，需要在总线驱动程序中支持从设备，并且还需要一个硬件无关的软件后端来提供实际的功能。一个这样的后端示例是 slave-eeprom 驱动程序，它充当双存储驱动程序。当总线上的另一个 I2C 主控器可以像常规 EEPROM 一样访问它时，Linux I2C 从设备可以通过 sysfs 访问内容并按需处理数据。后端驱动程序和 I2C 总线驱动程序通过事件进行通信。下面是一个小图，用于可视化数据流和数据传输的方式。虚线仅表示一个例子。后端也可以使用字符设备、仅限内核或完全不同的东西：

```
              例如 sysfs       I2C 从设备事件      I/O 寄存器
  +-----------+   v    +---------+     v     +--------+  v  +------------+
  | 用户空间  +........+ 后端    +-----------+ 驱动程序 +-----+ 控制器    |
  +-----------+        +---------+           +--------+     +------------+
                                                                | |
  ----------------------------------------------------------------+-- I2C
  --------------------------------------------------------------+---- 总线
```

注意：技术上，在后端和驱动程序之间还有 I2C 核心层。但是，在撰写本文时，该层是透明的。

用户手册
========

I2C 从设备后端的行为就像标准的 I2C 客户端。因此，您可以按照文档 instantiating-devices.rst 中所述实例化它们。唯一的区别是 I2C 从设备后端有自己的地址空间。所以，您必须将 0x1000 加到您原本请求的地址上。例如，在总线 1 上的 7 位地址 0x64 处从用户空间实例化 slave-eeprom 驱动程序：

  ```
  # echo slave-24c02 0x1064 > /sys/bus/i2c/devices/i2c-1/new_device
  ```

每个后端都应该附带单独的文档以描述其特定行为和设置。

开发者手册
==========

首先，将详细描述总线驱动程序和后端使用的事件。之后，将给出一些扩展总线驱动程序和编写后端的实现提示。

I2C 从设备事件
---------------

总线驱动程序使用以下函数向后端发送事件：

```
ret = i2c_slave_event(client, event, &val)
```

'client' 描述 I2C 从设备。'event' 是以下特殊事件类型之一。'val' 包含一个 u8 值，用于读/写的数据字节，因此它是双向的。无论 'val' 是否用于某个事件，都必须始终提供指向 'val' 的指针，即不要在这里使用 NULL。'ret' 是来自后端的返回值。必须提供的事件必须由总线驱动程序提供，并且必须由后端驱动程序检查。

事件类型：

* I2C_SLAVE_WRITE_REQUESTED（必需）

  'val': 未使用

  'ret': 如果后端准备就绪则为 0，否则为某些 errno

另一个 I2C 主控器想要写入数据给我们。一旦检测到我们自己的地址和写入位，就应该发送此事件。数据尚未到达，因此没有什么可处理或返回的。返回后，总线驱动程序必须始终确认地址阶段。如果 'ret' 为零，则已完成后端初始化或唤醒，可以接收更多数据。如果 'ret' 为 errno，则总线驱动程序应该拒绝所有传入的字节，直到下一个停止条件，以强制重新传输。

* I2C_SLAVE_READ_REQUESTED（必需）

  'val': 后端返回要发送的第一个字节

  'ret': 始终为 0

另一个 I2C 主控器想要从我们这里读取数据。一旦检测到我们自己的地址和读取位，就应该发送此事件。返回后，总线驱动程序应该传输第一个字节。

* I2C_SLAVE_WRITE_RECEIVED（必需）

  'val': 总线驱动程序传递接收到的字节

  'ret': 如果应确认字节则为 0，如果应拒绝字节则为某些 errno

另一个 I2C 主控器已将一个字节发送给我们，需要将其设置在 'val' 中。如果 'ret' 为零，则总线驱动程序应该确认这个字节。如果 'ret' 为 errno，则应拒绝这个字节。

* I2C_SLAVE_READ_PROCESSED（必需）

  'val': 后端返回要发送的下一个字节

  'ret': 始终为 0

总线驱动程序请求在 'val' 中向另一个 I2C 主控器发送的下一个字节。重要的是：这并不意味着前一个字节已被确认，它只意味着前一个字节被移位到了总线上！为了确保无缝传输，大多数硬件会在前一个字节仍在移出时请求下一个字节。如果主控器发送 NACK 并在当前移出的字节后停止读取，则此处请求的字节将不会被使用。根据您的后端情况，它很可能需要在下一个 I2C_SLAVE_READ_REQUEST 时再次发送。

* I2C_SLAVE_STOP（必需）

  'val': 未使用

  'ret': 始终为 0

收到停止条件。这可能随时发生，后端应该重置其状态机以便能够接收新的请求。

软件后端
--------

如果您想编写一个软件后端：

* 使用标准的 i2c_driver 及其匹配机制。
* 编写处理上述从设备事件的 slave_callback（最好使用状态机）。
* 通过 i2c_slave_register() 注册此回调。

请参阅 i2c-slave-eeprom 驱动程序作为示例。
公交驱动支持
--------------

如果您希望为公交驱动添加从机支持：

* 实现注册/注销从机的调用，并将这些调用添加到 `struct i2c_algorithm` 中。在注册时，您可能需要设置 I2C 从机地址并启用特定于从机的中断。如果您使用运行时电源管理 (PM)，应使用 `pm_runtime_get_sync()`，因为您的设备通常需要始终通电以能够检测其从机地址。在注销时，执行与上述操作相反的操作。
* 捕获从机中断并向后端发送适当的 `i2c_slave_events`。请注意，大多数硬件支持在同一总线上作为主控器 _和_ 从机。因此，如果您扩展一个公交驱动，请确保该驱动也支持这一点。在几乎所有情况下，从机支持无需禁用主控器功能。可以参考 `i2c-rcar` 驱动作为一个示例。

关于 ACK/NACK
--------------

良好的做法是始终对地址阶段进行 ACK，以便主控器知道设备是否基本存在或是否神秘消失。使用 NACK 表示忙碌状态会带来麻烦。SMBus 要求始终对地址阶段进行 ACK，而 I2C 规范在这方面更为宽松。大多数 I2C 控制器也会在检测到其从机地址时自动进行 ACK，因此没有选择 NACK 的选项。基于这些原因，此 API 不支持地址阶段中的 NACK。

目前，没有从机事件报告主控器读取我们时是否 ACK 或 NACK 了字节。如果需要出现，我们可以将其作为一个可选事件。然而，这种情况应该极其罕见，因为预期主控器会在那之后发送 STOP，而我们对此有一个事件。此外，请记住，并非所有 I2C 控制器都有报告该事件的可能性。

关于缓冲区
-------------

在开发此 API 的过程中，提出了使用缓冲区而非仅使用字节的问题。此类扩展可能是可行的，但在此撰写之时其有用性尚不清楚。使用缓冲区时需要注意以下几点：

* 缓冲区应该是可选的，并且后端驱动程序始终必须支持基于字节的事务，因为这是大多数硬件的工作方式。
* 对于模拟硬件寄存器的后端，缓冲区基本上没有帮助，因为写入每个字节后应立即触发一个动作。
对于读取操作，如果后端由于内部处理更新了寄存器，则保留在缓冲区中的数据可能会过时。
* 主控器可以在任何时候发送 STOP。对于部分传输的缓冲区，这意味着需要额外的代码来处理这种异常情况。此类代码往往容易出错。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
