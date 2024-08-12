### Linux IPMI 驱动程序

#### 作者：Corey Minyard <minyard@mvista.com> / <minyard@acm.org>

智能平台管理接口（IPMI）是一种用于控制监控系统的智能设备的标准。它提供了系统中传感器的动态发现功能，并能够监控这些传感器，在传感器值发生变化或超出特定范围时进行通知。此外，它还为现场可更换单元（FRU）提供标准化数据库以及一个看门狗定时器。
要使用此标准，您需要在系统中具备与 IPMI 控制器（称为底板管理控制器或 BMC）的接口，以及可以利用 IPMI 系统的管理软件。
本文档描述了如何使用 Linux 的 IPMI 驱动程序。如果您对 IPMI 本身不熟悉，请参阅 https://www.intel.com/design/servers/ipmi/index.htm。IPMI 是一个很大的主题，我无法在此全部涵盖！

### 配置

Linux 的 IPMI 驱动程序是模块化的，这意味着您需要根据硬件选择几个不同的选项来确保其正确工作。大多数选项可以在“字符设备”菜单下的 IPMI 菜单中找到。
无论如何，您必须选择“IPMI 顶层消息处理器”以使用 IPMI。除此之外的选择取决于您的需求和硬件情况。
消息处理器本身并不提供任何用户级接口。内核代码（如看门狗）仍然可以使用它。如果您需要从用户空间访问，则需要选择“IPMI 设备接口”，如果希望通过设备驱动程序访问的话。
驱动程序接口依赖于您的硬件。如果您的系统正确地提供了 IPMI 的 SMBIOS 信息，驱动程序将检测到它并自动工作。如果您有一块具有标准接口的主板（这些通常会是“KCS”、“SMIC” 或 “BT”，请参阅硬件手册），请选择“IPMI SI 处理器”选项。也存在一个可以直接通过 I2C 访问 IPMI 管理控制器的驱动程序。某些主板支持这种方式，但不能保证适用于所有主板。对于这种情况，请选择“IPMI SMBus 处理器”，但如果 SMBIOS/APCI 信息错误或不存在，可能需要做一些额外配置才能确定是否能在您的系统上工作。同时启用这两种方式通常是安全的，并让驱动程序自动检测存在的组件。
您通常应该在系统上启用 ACPI，因为具备 IPMI 的系统可能会有描述它们的 ACPI 表格。
如果您有一个标准接口且主板制造商正确完成了他们的工作，IPMI 控制器应能自动检测（通过 ACPI 或 SMBIOS 表格），并且可以正常工作。遗憾的是，许多主板并没有这些信息。驱动程序尝试采用标准默认设置，但这些设置可能不起作用。如果您处于这种情况下，需要阅读下面名为“SI 驱动程序”或“SMBus 驱动程序”的部分，了解如何手动配置您的系统。
IPMI 定义了一个标准的看门狗定时器。您可以通过 'IPMI Watchdog Timer' 配置选项来启用它。如果您将驱动程序编译到内核中，那么通过内核命令行选项，可以在初始化时立即启动看门狗定时器。它还有许多其他选项，请参阅下面的 'Watchdog' 部分以获取更多详细信息。

请注意，您还可以让看门狗在关闭后继续运行（默认情况下，在关闭时禁用）。进入 'Watchdog Cards' 菜单，启用 'Watchdog Timer Support'，并启用 'Disable watchdog shutdown on close' 选项。

IPMI 系统通常可以使用 IPMI 命令进行关机。选择 'IPMI Poweroff' 来执行此操作。驱动程序会自动检测系统是否可以通过 IPMI 关机。即使您的系统不支持此选项，启用它也是安全的。这适用于 ATCA 系统、Radisys CPI1 卡以及任何支持标准机箱管理命令的 IPMI 系统。

如果希望驱动程序在发生恐慌时向事件日志记录一个事件，则启用 'Generate a panic event to all BMCs on a panic' 选项。如果希望使用 OEM 事件将整个恐慌字符串写入事件日志，请启用 'Generate OEM events containing the panic string' 选项。您也可以通过设置 ipmi_msghandler 模块中的名为 "panic_op" 的模块参数为 "event" 或 "string" 动态启用这些功能。将该参数设置为 "none" 将禁用此功能。

### 基本设计

Linux IPMI 驱动程序被设计得非常模块化和灵活，您只需要采用所需的部分，并且可以用多种不同的方式使用它。正因为如此，它被划分为多个代码段。这些代码段（按模块名称划分）包括：

- ipmi_msghandler：这是 IPMI 系统的核心软件部分。它处理所有消息、消息计时和响应。IPMI 用户与此绑定，IPMI 物理接口（称为系统管理接口或 SMIs）也与此绑定。这提供了内核空间中的 IPMI 接口，但不提供应用程序进程可用的接口。
- ipmi_devintf：这为 IPMI 驱动程序提供用户空间 IOCTL 接口，该设备的每个打开文件都作为 IPMI 用户与消息处理器绑定。
- ipmi_si：这是一个用于各种系统接口的驱动程序。它支持 KCS、SMIC 和 BT 接口。除非您拥有 SMBus 接口或自己的自定义接口，否则您可能需要使用此驱动程序。
- ipmi_ssif：这是一个用于访问 SMBus 上 BMC 的驱动程序。它使用 I2C 内核驱动程序的 SMBus 接口来发送和接收 SMBus 上的 IPMI 消息。
- ipmi_powernv：这是一个用于访问 POWERNV 系统上 BMC 的驱动程序。
- ipmi_watchdog：IPMI 要求系统具备强大的看门狗定时器。此驱动程序实现了基于 IPMI 消息处理器的标准 Linux 看门狗定时器接口。
翻译为中文：

`ipmi_poweroff` - 某些系统支持通过 IPMI 命令进行关机的功能。
`bt-bmc` - 这不是主驱动程序的一部分，而是一个用于访问 BT 接口的 BMC 端接口的驱动程序。在运行 Linux 的 BMC 上使用它来为主机提供一个接口。

这些都可以通过配置选项单独选择。关于此接口的大量文档可以在头文件中找到。IPMI 头文件包括：

`linux/ipmi.h` - 包含 IPMI 的用户界面和 IOCTL 接口。
`linux/ipmi_smi.h` - 包含系统管理接口（与 IPMI 控制器交互的事物）使用的接口。
`linux/ipmi_msgdefs.h` - 定义基本的 IPMI 消息传递。

### 地址机制

IPMI 地址的工作方式类似于 IP 地址，需要一个覆盖层来处理不同的地址类型。覆盖层如下所示：

```c
struct ipmi_addr
{
    int   addr_type;
    short channel;
    char  data[IPMI_MAX_ADDR_SIZE];
};
```

`addr_type` 决定了地址的实际含义。目前驱动程序理解两种不同类型的地址：

- “系统接口”地址定义为：

```c
struct ipmi_system_interface_addr
{
    int   addr_type;
    short channel;
};
```

类型为 `IPMI_SYSTEM_INTERFACE_ADDR_TYPE`。这种地址用于直接与当前卡上的 BMC 通信。`channel` 必须为 `IPMI_BMC_CHANNEL`。

- 目的地为通过 BMC 经 IPMB 总线发送的消息使用 `IPMI_IPMB_ADDR_TYPE` 地址类型。其格式为：

```c
struct ipmi_ipmb_addr
{
    int           addr_type;
    short         channel;
    unsigned char slave_addr;
    unsigned char lun;
};
```

这里的“channel”通常是零，但某些设备支持多个通道，它对应于 IPMI 规范中定义的通道。

还有一种 IPMB 直接地址，适用于发送方直接位于 IPMB 总线上且无需经过 BMC 的情况。
您可以使用 `IPMI_IPMB_DIRECT_ADDR_TYPE` 向 IPMB 上的特定管理控制器（MC）发送消息，其格式如下：

  ```c
  struct ipmi_ipmb_direct_addr
  {
    int           addr_type;
    short         channel;
    unsigned char slave_addr;
    unsigned char rq_lun;
    unsigned char rs_lun;
  };
  ```

通道值始终为零。您还可以接收来自其他已注册以处理和响应的 MC 的命令，因此可以利用此功能在总线上实现一个管理控制器。
消息
------

消息定义如下：

  ```c
  struct ipmi_msg
  {
    unsigned char netfn;
    unsigned char lun;
    unsigned char cmd;
    unsigned char *data;
    int           data_len;
  };
  ```

驱动程序负责添加或移除头部信息。数据部分仅包含要发送的数据（请勿在此处放置地址信息）或响应。请注意，响应的完成代码是“data”中的第一个项，不被移除，因为这是规范中所有消息的定义方式（从而使计算偏移量变得更简单）。
当从用户空间使用 IOCTL 接口时，您必须提供一块数据用于“data”，填充它，并将 data_len 设置为数据块的长度，即使是在接收消息时也是如此。否则，驱动程序将没有地方存放消息。
从内核空间的消息处理器接收到的消息将以以下形式出现：

  ```c
  struct ipmi_recv_msg
  {
    struct list_head link;

    /* 按照上述 "Receive Types" 定义的消息类型。 */
    int         recv_type;

    ipmi_user_t      *user;
    struct ipmi_addr addr;
    long             msgid;
    struct ipmi_msg  msg;

    /* 处理完消息后调用此函数。它将释放消息并执行任何必要的清理工作。 */
    void (*done)(struct ipmi_recv_msg *msg);

    /* 数据的占位符，不要对它的大小或存在性做出任何假设，因为它可能会改变。 */
    unsigned char   msg_data[IPMI_MAX_MSG_LENGTH];
  };
  ```

您应该查看接收类型，并根据需要处理消息。
上层接口（消息处理器）
-------------------------------

该接口的上层为用户提供了一个一致的 IPMI 接口视图。它允许访问多个 SMI 接口（因为某些板卡实际上具有多个 BMC），并且用户无需关心下面的 SMI 类型。
监视接口
^^^^^^^^^^^^^^^^^^^^^^^

当您的代码启动时，IPMI 驱动可能已经检测到 IPMI 设备是否存在，也可能尚未检测到。因此，您可能需要延迟设置直到设备被检测到，或者可以直接立即进行设置。
为了处理这种情况，并允许发现，您可以使用 `ipmi_smi_watcher_register()` 注册一个 SMI 监视器来遍历接口，并告诉您它们何时出现或消失。
创建用户
^^^^^^^^^^^^^^^^^

要使用消息处理器，您必须首先使用 `ipmi_create_user` 创建一个用户。接口编号指定了您想要连接的 SMI，并且您必须提供回调函数以便在数据到达时调用。这些回调函数可以在中断级别运行，所以在使用回调时要小心。这还允许您传递一段数据（handler_data），该数据将在所有调用中返回给您。
完成后，请调用 `ipmi_destroy_user()` 来销毁用户。
从用户空间打开设备会自动创建一个用户，关闭设备则会自动销毁用户。
### 消息传送

要从内核空间发送消息，`ipmi_request_settime()` 函数几乎处理了所有消息。大多数参数都是自解释的。但是，它需要一个“msgid”参数。这不是消息序列号。它只是一个长整型值，在消息响应返回时会传递回来。你可以根据需要使用它。

响应通过在调用 `ipmi_create_user()` 时传入的 “handler” 结构体中的 `ipmi_recv_hndl` 字段指向的函数返回。再次提醒，这些可能在中断级别运行。记得检查接收类型。

从用户空间，你需要填充一个 `ipmi_req_t` 结构体并使用 `IPMICTL_SEND_COMMAND` 输入输出控制命令。对于接收到的数据，你可以使用 `select()` 或 `poll()` 来等待消息到来。然而，你不能使用 `read()` 来获取它们，必须调用 `IPMICTL_RECEIVE_MSG` 并使用 `ipmi_recv_t` 结构体来实际获取消息。记得你必须在 `msg.data` 字段中提供数据块的指针，并且必须在 `msg.data_len` 字段中填写数据大小。这为接收者提供了实际放置消息的地方。

如果消息无法放入你提供的数据中，你会得到 `EMSGSIZE` 错误，驱动程序会将数据保留在接收队列中。如果你想获取它并且截断消息，请使用 `IPMICTL_RECEIVE_MSG_TRUNC` 输入输出控制命令。

当你在 IPMB 总线上发送一个命令（根据 IPMI 规范，该命令由 netfn 的最低位定义）时，驱动程序会自动为命令分配序列号并保存命令。如果响应在 IPMI 规定的 5 秒内没有收到，它将自动生成一个超时响应。如果接收到未请求的响应（例如，在 5 秒后），该响应将被忽略。

在内核空间中，当你接收到消息并处理完毕后，**必须** 调用 `ipmi_free_recv_msg()` 来释放它，否则会导致消息泄露。请注意，你不应该对消息的 “done” 字段进行任何操作，因为这是正确清理消息所必需的。

需要注意的是，在发送过程中有一个 `ipmi_request_supply_msgs()` 调用，允许你提供 smi 和接收消息。这对于那些即使系统缺少缓冲区也要工作的代码片段非常有用（例如，看门狗定时器就使用了这个功能）。你需要提供自己的缓冲区和自己的释放例程。虽然不建议常规使用这种方式，因为它很难管理自己的缓冲区。

### 事件与接收到的命令

驱动程序负责轮询 IPMI 事件和接收命令（命令是那些不是响应的消息，而是 IPMB 总线上的其他设备发送给你的命令）。为了接收这些命令，你必须注册，它们不会自动发送给你。
为了接收事件，您必须调用 `ipmi_set_gets_events()` 并将 "val" 设置为非零值。自启动以来驱动程序接收到的任何事件会立即传递给第一个注册接收事件的用户。之后，如果有多个用户注册了接收事件，他们将会收到所有传入的事件。

对于接收命令，您需要单独注册想要接收的命令。调用 `ipmi_register_for_cmd()` 并为每个要接收的命令提供对应的 netfn 和命令名称。您还可以指定一个通道掩码来确定从哪些通道接收该命令（或使用 IPMI_CHAN_ALL 来接收所有通道上的命令，如果您不关心具体通道的话）。每个 netfn/cmd/通道组合只能有一个用户注册，但不同的用户可以注册不同的命令，或者同一命令的不同通道掩码组合。

为了响应接收到的命令，设置返回的 netfn 中的响应位，使用接收到的消息中的地址，并使用与接收到的消息相同的 msgid。

在用户空间中，提供了等效的 IOCTL 来执行这些功能。

### 下层接口（SMI）

如前所述，可以向消息处理器注册多个 SMI 接口，每个接口在注册时都会被分配一个接口编号。它们通常按照注册顺序进行分配，但如果某个 SMI 注销后又注册了一个新的 SMI，则原来的顺序可能不再适用。

`ipmi_smi.h` 定义了管理接口的标准，请参阅该文件获取更多详细信息。

### SI 驱动

SI 驱动允许配置 KCS、BT 和 SMIC 接口。它通过多种方法发现接口，这取决于具体的系统。

您可以在模块加载行上指定最多四个接口，并控制一些模块参数：

```sh
modprobe ipmi_si.o type=<type1>,<type2>... ports=<port1>,<port2>... addrs=<addr1>,<addr2>... irqs=<irq1>,<irq2>...
```

这里 `<type1>` 等代表不同类型的接口，`<port1>` 表示端口号，`<addr1>` 表示地址，`<irq1>` 表示中断请求号。
除了try...项之外，每一项都是一个列表，其中第一项对应第一个接口，第二项对应第二个接口，以此类推。
si_type 可以是 "kcs"、"smic" 或 "bt"。如果你留空，它默认为 "kcs"。
如果你为某个接口指定了非零的 addrs，驱动程序将会使用给定的内存地址作为设备地址。这将覆盖 si_ports。
如果你为某个接口指定了非零的 ports，驱动程序将会使用给定的 I/O 端口作为设备地址。
如果你为某个接口指定了非零的 irqs，驱动程序将会尝试使用给定的中断作为设备的中断。

具体参数如下：

- `regspacings=<sp1>,<sp2>,...`：表示每个接口的寄存器间距。
- `regsizes=<size1>,<size2>,..`：表示每个接口的寄存器大小。
- `regshifts=<shift1>,<shift2>,..`：表示每个接口的寄存器偏移量。
- `slave_addrs=<addr1>,<addr2>,..`：表示每个接口的从设备地址。
- `force_kipmid=<enable1>,<enable2>,..`：表示是否强制启用 KIPMID 模式。
- `kipmid_max_busy_us=<ustime1>,<ustime2>,..`：表示在 KIPMID 模式下，允许的最大忙时等待时间（微秒）。
- `unload_when_empty=[0|1]`：表示当没有数据传输时是否卸载设备。
- `trydmi=[0|1]`、`tryacpi=[0|1]`、`tryplatform=[0|1]` 和 `trypci=[0|1]`：这些选项分别表示是否尝试通过 DMI、ACPI、平台方法和 PCI 方法来检测设备。
其他尝试...项目通过它们对应的名字禁用发现功能。这些项目默认都是启用的，设置为零以禁用它们。`tryplatform`禁用开放固件（OpenFirmware）。

接下来的三个参数与寄存器布局有关。接口使用的寄存器可能不会连续出现，也可能不在8位寄存器中。这些参数允许更精确地指定寄存器中的数据布局。

`regspacings`参数给出连续寄存器起始地址之间的字节数。例如，如果`regspacing`设置为4且起始地址是0xca2，则第二个寄存器的地址将是0xca6。此值默认为1。

`regsizes`参数给出寄存器的大小（以字节计）。IPMI使用的数据宽度为8位，但它可能位于一个更大的寄存器内。此参数允许指定读写类型。
它可以是1、2、4或8。默认值为1。

由于寄存器大小可能大于32位，因此IPMI数据可能不在最低8位中。`regshifts`参数给出将数据移位到实际IPMI数据所需的位数。

`slave_addrs`指定本地BMC的IPMI地址。这通常是0x20，并且驱动程序默认为此值，但如果不是这个值，可以在启动驱动程序时进行指定。

`force_ipmid`参数强制启用（如果设置为1）或禁用（如果设置为0）内核IPMI守护进程。通常这是由驱动程序自动检测的，但中断存在问题的系统可能需要启用该守护进程，或者用户如果不希望使用该守护进程（不需要其性能，不想消耗CPU资源）可以禁用它。

如果`unload_when_empty`设置为1，则如果没有找到任何接口或所有接口都无法工作，驱动程序将被卸载。默认值为1。设置为0对于热插拔有用，但显然仅对模块有效。

当编译到内核中时，这些参数可以通过内核命令行指定，例如：

```
ipmi_si.type=<type1>,<type2>...
```
这些配置选项的作用与同名的模块参数相同：
- `ipmi_si.ports=<port1>,<port2>,...`：指定 IPMI 接口所使用的端口。
- `ipmi_si.addrs=<addr1>,<addr2>,...`：指定 IPMI 接口的地址。
- `ipmi_si.irqs=<irq1>,<irq2>,...`：指定 IPMI 接口所使用的中断请求（IRQ）。
- `ipmi_si.regspacings=<sp1>,<sp2>,...`：指定寄存器间隔。
- `ipmi_si.regsizes=<size1>,<size2>,...`：指定寄存器大小。
- `ipmi_si.regshifts=<shift1>,<shift2>,...`：指定寄存器位移。
- `ipmi_si.slave_addrs=<addr1>,<addr2>,...`：指定从设备地址。
- `ipmi_si.force_kipmid=<enable1>,<enable2>,...`：允许用户强制开启或关闭内核线程。如果设置为“开启”，即使接口不支持中断，也会启动内核线程以提高性能；如果设置为“关闭”，且接口不支持中断，则驱动程序运行会非常慢。
- `ipmi_si.kipmid_max_busy_us=<ustime1>,<ustime2>,...`：设置内核线程在两次轮询之间等待的最大微秒数。

如果您的 IPMI 接口不支持中断，并且是 KCS 或 SMIC 接口，IPMI 驱动程序将为该接口启动一个内核线程，以加快操作速度。这是一个低优先级的内核线程，在进行 IPMI 操作时不断轮询 IPMI 驱动程序。`force_kipmid` 模块参数允许用户强制启用或禁用此线程。如果您禁用它且接口不支持中断，那么驱动程序将会运行得非常慢。请不要责怪我，这些接口本身就存在局限性。
不幸的是，这个线程可能会根据接口性能消耗大量CPU资源。这不仅浪费了大量的CPU资源，还可能导致各种问题，比如无法正确检测空闲CPU状态以及增加额外的功耗。为了避免这种情况，`kipmid_max_busy_us` 设置了一个最大时间值（以微秒为单位），表示 `kipmid` 在休眠一周期之前可以连续运行的最大时间。这个值需要在性能和CPU资源浪费之间找到平衡，并且需要根据您的需求进行调整。也许将来会加入自动调节功能，但这并不简单，即便是自动调节也需要根据用户的期望性能进行调节。

驱动程序支持热插拔接口。这意味着，在内核启动并运行后，可以添加或移除接口。这是通过 `/sys/modules/ipmi_si/parameters/hotmod` 来完成的，这是一个只写参数。您需要向此接口写入一个字符串，其格式如下：

```
<op1>[:op2[:op3...]]
```

其中“op”可以是：

```
add|remove,kcs|bt|smic,mem|i/o,<address>[,<opt1>[,<opt2>[,...]]]
```

您可以在一行中指定多个接口。“opt”参数包括：

```
rsp=<regspacing>
rsi=<regsize>
rsh=<regshift>
irq=<irq>
ipmb=<ipmb slave addr>
```

这些选项与上面讨论的意义相同。需要注意的是，您也可以在内核命令行中使用这种方式来更紧凑地指定接口。在移除接口时，仅使用前三个参数（SI类型、地址类型和地址）进行比较，其他选项将被忽略。

### SMBus 驱动（SSIF）

SMBus 驱动允许系统中最多配置4个SMBus设备。默认情况下，该驱动仅会在DMI或ACPI表中发现设备时注册。您可以在加载模块时（对于模块）更改这一行为，例如：

```shell
modprobe ipmi_ssif.o 
	addr=<i2caddr1>[,<i2caddr2>[,...]]
	adapter=<adapter1>[,<adapter2>[...]]
	dbg=<flags1>,<flags2>..
slave_addrs=<addr1>,<addr2>,..
tryacpi=[0|1] trydmi=[0|1]
	[dbg_probe=1]
	alerts_broken
```

地址是标准的I2C地址。适配器是指适配器的名称，如 `/sys/class/i2c-adapter/i2c-<n>/name` 中所示的字符串名。它不是 `i2c-<n>` 本身。此外，名称比较时会忽略空格，因此如果名称是 "This is an I2C chip"，您可以输入 `adapter_name=ThisisanI2cchip`。这是因为很难在内核参数中传递空格。

调试标志是对每个BMC找到的信息设置的位标志，它们分别表示：
- IPMI 消息：1
- 驱动状态：2
- 定时信息：4
- I2C 探测：8

`tryxxx` 参数可用于禁用从不同来源检测接口的功能。
将 `dbg_probe` 设置为1将启用对SMBus上的BMC探测和检测过程的调试。
`slave_addrs` 指定了本地BMC的IPMI地址。这通常是0x20，驱动程序默认也是这个值，但如果地址不是0x20，则可以在驱动程序启动时指定。
alerts_broken 不会为 SSIF 启用 SMBus 警报。否则，如果硬件支持的话，SMBus 警报将会被启用。
通过 SMBus 发现符合 IPMI 标准的 BMC 可能会导致 I2C 总线上的设备失败。SMBus 驱动程序会向 I2C 总线写入一个“获取设备ID”的 IPMI 消息，并等待响应。这一操作可能对某些 I2C 设备造成不利影响。强烈建议在 smb_addr 参数中给出已知的 I2C 地址，除非您有 DMI 或 ACPI 数据来告知驱动程序应该使用什么地址。
当编译到内核时，可以通过内核命令行指定地址：

  ipmb_ssif.addr=<i2caddr1>[,<i2caddr2>[...]]
  ipmi_ssif.adapter=<adapter1>[,<adapter2>[...]]
  ipmi_ssif.dbg=<flags1>[,<flags2>[...]]
  ipmi_ssif.dbg_probe=1
  ipmi_ssif.slave_addrs=<addr1>[,<addr2>[...]]
  ipmi_ssif.tryacpi=[0|1] ipmi_ssif.trydmi=[0|1]

这些选项与模块命令行中的选项相同。
I2C 驱动程序不支持非阻塞访问或轮询，因此没有特殊的内核补丁和驱动修改的情况下，此驱动无法处理 IPMI 恐慌事件、在恐慌时扩展看门狗，或其他与恐慌相关的 IPMI 功能。您可以在 openipmi 网页上获得这些功能。
该驱动程序支持通过 I2C 的 sysfs 接口进行热插拔接口。
IPMI IPMB 驱动程序
--------------------
此驱动程序用于支持位于 IPMB 总线上的系统；它使接口看起来像一个标准的 IPMI 接口。向其发送系统接口寻址消息将导致消息发送到系统上注册的 BMC（默认 IPMI 地址为 0x20）。
此外，您还可以直接使用 IPMB 直接寻址来访问总线上的其他 MC。您可以接收来自总线上其他 MC 的命令，并通过上述正常的接收命令机制进行处理。
参数如下：

  ipmi_ipmb.bmcaddr=<用于系统接口地址消息的地址>
  ipmi_ipmb.retry_time_ms=<IPMB 上重试之间的间隔时间>
  ipmi_ipmb.max_retries=<重试消息的次数>

加载模块不会自动启动驱动程序，除非存在设备树信息对其进行设置。如果您想手动实例化其中一个，请执行以下操作：

  echo ipmi-ipmb <addr> > /sys/class/i2c-dev/i2c-<n>/device/new_device

请注意，这里提供的地址是 I2C 地址，而不是 IPMI 地址。因此，如果您希望您的 MC 地址为 0x60，则在这里输入 0x30。更多详细信息请参阅 I2C 驱动程序文档。
通过此接口向其他 IPMB 总线桥接命令的功能不可用。按设计未实现接收消息队列。BMC 上只有一个接收消息队列，这是为宿主机驱动程序准备的，而非 IPMB 总线上的某个实体。
### BMC 可能有多个 IPMB 总线，您的设备位于哪个总线上取决于系统的布线方式。您可以使用 "ipmitool channel info <n>" 获取通道信息，其中 <n> 是通道号，通道范围为 0-7，并尝试 IPMB 通道。

### 其他组件

#### 获取与 IPMI 设备相关的详细信息

一些用户需要更多关于设备的详细信息，比如地址来源或 IPMI 接口的原始基础设备。您可以使用 IPMI 的 smi_watcher 来捕捉 IPMI 接口的出现和消失，并通过函数 `ipmi_get_smi_info()` 获取信息，该函数返回以下结构体：

```c
struct ipmi_smi_info {
    enum ipmi_addr_src addr_src; // 地址来源枚举
    struct device *dev;          // 设备指针
    union {
        struct {
            void *acpi_handle; // 对于SI_ACPI地址源的ACPI句柄
        } acpi_info;
    } addr_info;
};
```

目前仅返回 SI_ACPI 地址源的特殊信息。其他类型的信息可能会根据需要添加。

请注意，在上述结构体中包含了 dev 指针，如果 `ipmi_smi_get_info` 返回成功，则必须对 dev 指针调用 `put_device` 函数。

### 看门狗

提供了一个看门狗定时器，它实现了 Linux 标准的看门狗定时器接口。它有三个模块参数可以用来控制它：

```bash
modprobe ipmi_watchdog timeout=<t> pretimeout=<t> action=<action type>
    preaction=<preaction type> preop=<preop type> start_now=x
    nowayout=x ifnum_to_use=n panic_wdt_timeout=<t>
```

`ifnum_to_use` 参数指定了看门狗定时器应使用的接口，默认值为 -1，表示选择第一个注册的接口。
`timeout` 参数是到采取行动所需的秒数，而 `pretimeout` 参数是在重置前发生预超时恐慌的秒数（如果 `pretimeout` 为零，则不会启用预超时）。需要注意的是，`pretimeout` 是在最终 `timeout` 之前的秒数。例如，如果 `timeout` 为 50 秒且 `pretimeout` 为 10 秒，则 `pretimeout` 将在 40 秒后（即 `timeout` 前 10 秒）发生。`panic_wdt_timeout` 是在内核恐慌时设置的 `timeout` 值，以便允许如 kdump 这样的操作在此期间执行。
`action` 可以是 "reset"、"power_cycle" 或 "power_off"，指定当计时器超时时要采取的动作，默认为 "reset"。
`preaction` 可以是 "pre_smi"（通过 SMI 接口指示）、"pre_int"（通过 SMI 接口并带有中断指示），以及 "pre_nmi"（预操作时的 NMI）。这是驱动程序如何被通知预超时的方式。
`preop` 可以设置为 "preop_none"（预超时时不执行任何操作）、"preop_panic"（将预操作设置为恐慌）或 "preop_give_data"（在预超时发生时提供数据供从看门狗设备读取）。"pre_nmi" 设置不能与 "preop_give_data" 结合使用，因为无法从 NMI 中执行数据操作。
当`preop`设置为"preop_give_data"时，预超时(pretimeout)发生时设备上会准备好一个字节以供读取。`select`和`fasync`也可以在该设备上使用。
如果`start_now`设置为1，则看门狗定时器会在驱动加载后立即开始运行。
如果`nowayout`设置为1，则关闭看门狗设备时看门狗定时器不会停止。`nowayout`的默认值取决于是否启用了`CONFIG_WATCHDOG_NOWAYOUT`选项：启用时默认值为true，未启用时为false。
编译到内核中时，可以通过内核命令行来配置看门狗：

  ipmi_watchdog.timeout=<t> ipmi_watchdog.pretimeout=<t>
  ipmi_watchdog.action=<action type>
  ipmi_watchdog.preaction=<preaction type>
  ipmi_watchdog.preop=<preop type>
  ipmi_watchdog.start_now=x
  ipmi_watchdog.nowayout=x
  ipmi_watchdog.panic_wdt_timeout=<t>

这些选项与模块参数选项相同。
如果看门狗接收到预动作(pre-action)，它将触发系统恐慌并启动120秒的重置超时。在系统恐慌或重启期间，如果看门狗正在运行，它将启动120秒计时器以确保重启的发生。
需要注意的是，如果你为看门狗设置了NMI预动作，则**不能**使用NMI看门狗。因为无法合理判断NMI是否来自IPMI控制器，所以一旦接收到未处理的NMI，它会假设该NMI来自IPMI，并立即触发系统恐慌。
打开看门狗定时器后，必须向设备写入字符'V'来关闭它，否则定时器不会停止。这是驱动的新语义，但使得其与其他Linux看门狗驱动保持一致。
### 系统恐慌超时

OpenIPMI驱动支持在系统发生恐慌时在系统事件日志中记录半自定义或自定义事件的功能。如果你启用了“在系统恐慌时向所有BMC生成恐慌事件”的选项，你将在标准IPMI事件格式下获得一个事件。如果你还启用了“生成包含恐慌字符串的OEM事件”的选项，你还会获得一系列保存了恐慌字符串的OEM事件。
这些事件的字段设置如下：

* 生成器ID: 0x21（内核）
* 事件管理器版本(EvM Rev): 0x03（此事件按照IPMI 1.0格式进行格式化）
* 传感器类型: 0x20（操作系统关键停止传感器）
* 传感器编号: 恐慌字符串的第一个字节（若无恐慌字符串则为0）
* 事件方向|事件类型: 0x6f（断言，特定于传感器的事件信息）
* 事件数据1: 0xa1（在OEM字节2和3中的运行时停止）
* 事件数据2: 恐慌字符串的第二个字节
* 事件数据3: 恐慌字符串的第三个字节

有关事件布局的详细信息，请参阅IPMI规范。此事件总是发送给本地管理控制器，它会负责将消息路由到正确的位置。

其他OEM事件具有以下格式：

* 记录ID（字节0-1）: 由SEL设置
* 记录类型（字节2）: 0xf0（OEM非时间戳）
* 字节3: 保存恐慌的卡的从属地址
* 字节4: 序列号（从零开始）
  剩余的字节（共11个字节）是恐慌字符串。如果恐慌字符串超过11个字节，将通过递增序列号发送多个消息。
因为您无法使用标准接口发送OEM事件，所以此功能会尝试找到一个系统事件日志（SEL）并在那里添加这些事件。它首先会查询本地管理控制器的能力。如果它有一个SEL，那么事件将被存储在本地管理控制器的SEL中。如果没有，并且本地管理控制器是一个事件生成器，则会查询来自本地管理控制器的事件接收器，并将事件发送到该设备上的SEL。否则，由于没有地方可以发送这些事件，所以事件将无处可去。

关机
------

如果选择了关机能力，IPMI驱动程序将在标准关机函数指针中安装一个关机函数。这在`ipmi_poweroff`模块中实现。当系统请求关机时，它将发送适当的IPMI命令来完成这个操作。这种支持在多个平台上可用。
有一个名为“poweroff_powercycle”的模块参数，它可以是零（执行关机）或非零（执行电源循环，即先关闭系统电源，然后几秒钟后重新开启）。设置`ipmi_poweroff.poweroff_control=x`可以在内核命令行上实现相同的功能。该参数也可以通过/proc文件系统在`/proc/sys/dev/ipmi/poweroff_powercycle`路径下访问。请注意，如果系统不支持电源循环，则始终只会执行关机操作。
参数“ifnum_to_use”指定了关机代码应使用的接口。默认值为-1，这意味着选择第一个注册的接口。
请注意，如果您启用了ACPI，系统将优先使用ACPI来进行关机操作。
