SPDX 许可证标识符: GPL-2.0 或更高版本

CTU CAN FD 驱动程序
==================

作者: Martin Jerabek <martin.jerabek01@gmail.com>

关于 CTU CAN FD IP 核心
------------------------

`CTU CAN FD <https://gitlab.fel.cvut.cz/canbus/ctucanfd_ip_core>`_ 是一个用 VHDL 编写的开源软核。
它起源于 2015 年 Ondrej Ille 在 `CTU <https://www.cvut.cz/en>`_ 的 `FEE <http://www.fel.cvut.cz/en/>`_ 中的 `Department of Measurement <https://meas.fel.cvut.cz/>`_ 的项目。
该软核还支持基于 Xilinx Zynq SoC 的 MicroZed 板卡的 `Vivado 集成 <https://gitlab.fel.cvut.cz/canbus/zynq/zynq-can-sja1000-top>`_ 和基于 Intel Cyclone V 5CSEMA4U23C6 的 DE0-Nano-SoC Terasic 板卡的 `QSys 集成 <https://gitlab.fel.cvut.cz/canbus/intel-soc-ctucanfd>`_，以及 `PCIe 集成 <https://gitlab.fel.cvut.cz/canbus/pcie-ctucanfd>`_。
在 Zynq 情况下，该核心通过 APB 系统总线连接，而该总线不支持枚举，因此设备必须在设备树中指定。这种类型的设备在内核中称为平台设备，并由平台设备驱动程序处理。
CTU CAN FD 外设的基本功能模型已经被接受到 QEMU 主线。有关 CAN FD 总线、主机连接和 CTU CAN FD 核心仿真，请参见 QEMU 的 `CAN 仿真支持 <https://www.qemu.org/docs/master/system/devices/can.html>`_。仿真支持的开发版本可以从 QEMU 本地开发的 `仓库 <https://gitlab.fel.cvut.cz/canbus/qemu-canbus>`_ 的 ctu-canfd 分支克隆。

关于 SocketCAN
--------------

SocketCAN 是 Linux 内核中 CAN 设备的标准通用接口。顾名思义，该总线是通过套接字访问的，类似于常见的网络设备。关于这一点的详细描述可以在 `Linux SocketCAN <https://www.kernel.org/doc/html/latest/networking/can.html>`_ 中找到。简而言之，它提供了一种自然的方式来实现和使用 CAN 上的高层协议，就像以太网上的 UDP/IP 一样。

设备探测
~~~~~~~~~~~

在详细介绍 CAN 总线设备驱动程序的结构之前，让我们先回顾一下内核是如何识别设备的。
一些总线（如 PCI 或 PCIe）支持设备枚举。也就是说，在系统启动时，它会发现总线上的所有设备并读取它们的配置。内核通过其供应商 ID 和设备 ID 识别设备，如果注册了针对此标识符组合的驱动程序，则会调用其探测方法来填充给定硬件的驱动实例。USB 类似于此，只是它允许设备热插拔。
情况对于直接嵌入SoC并连接到内部系统总线（如AXI、APB、Avalon等）的外设是不同的。这些总线不支持枚举，因此内核必须从其他地方了解这些设备。这正是设备树的用武之地。

### 设备树
~~~~~~

设备树中的一个条目表明了一个设备存在于系统中，它如何可达（位于哪个总线上）以及其配置——寄存器地址、中断等。下面是一个这样的设备树示例：
::

           / {
               /* ... */
               amba: amba {
                   #address-cells = <1>;
                   #size-cells = <1>;
                   compatible = "simple-bus";

                   CTU_CAN_FD_0: CTU_CAN_FD@43c30000 {
                       compatible = "ctu,ctucanfd";
                       interrupt-parent = <&intc>;
                       interrupts = <0 30 4>;
                       clocks = <&clkc 15>;
                       reg = <0x43c30000 0x10000>;
                   };
               };
           };

### 驱动结构
~~~~~~~~~~

驱动可以分为两部分：平台相关的设备发现和设置，以及平台无关的CAN网络设备实现。

#### 平台设备驱动
^^^^^^^^^^^^^^^^^^^^^^

在Zynq的情况下，核心通过AXI系统总线连接，该总线不支持枚举，因此设备必须在设备树中指定。这种类型的设备在内核中被称为“平台设备”，由“平台设备驱动”处理 [1]。
平台设备驱动提供了以下功能：

- 一个`probe`函数
- 一个`remove`函数
- 一张兼容设备表，列出驱动可以处理的设备

`probe`函数在设备出现（或驱动加载，以较晚发生的为准）时恰好被调用一次。如果同一个驱动处理多个设备，则为每个设备调用一次`probe`函数。其作用是分配和初始化处理设备所需的资源，并为平台无关层设置低级函数，例如`read_reg`和`write_reg`。之后，驱动将设备注册到更高层，在我们的案例中是作为“网络设备”。
`remove`函数在设备消失或驱动即将卸载时被调用。它的作用是释放`probe`中分配的资源，并从更高层注销设备。
最后，兼容设备表指定了驱动可以处理哪些设备。设备树条目`compatible`会与所有平台驱动的表格进行匹配。
```c
           /* OF平台绑定的匹配表 */
           static const struct of_device_id ctucan_of_match[] = {
               { .compatible = "ctu,canfd-2", },
               { .compatible = "ctu,ctucanfd", },
               { /* 列表结束 */ },
           };
           MODULE_DEVICE_TABLE(of, ctucan_of_match);

           static int ctucan_probe(struct platform_device *pdev);
           static int ctucan_remove(struct platform_device *pdev);

           static struct platform_driver ctucanfd_driver = {
               .probe  = ctucan_probe,
               .remove = ctucan_remove,
               .driver = {
                   .name = DRIVER_NAME,
                   .of_match_table = ctucan_of_match,
               },
           };
           module_platform_driver(ctucanfd_driver);
```

#### 网络设备驱动
^^^^^^^^^^^^^^^^^^^^^

每个网络设备至少必须支持以下操作：

- 启用设备：`ndo_open`
- 停用设备：`ndo_close`
- 将TX帧提交给设备：`ndo_start_xmit`
- 向网络子系统报告TX完成和错误：ISR
- 将RX帧提交给网络子系统：ISR和NAPI

有两个可能的事件源：设备和网络子系统。设备事件通常通过中断信号处理，由中断服务例程（ISR）处理。来自网络子系统的事件的处理函数则在`struct net_device_ops`中指定。
当设备被启用时，例如通过调用`ip link set can0 up`，驱动的函数`ndo_open`会被调用。它应该验证接口配置并配置并启用设备。相反的操作是`ndo_close`，在设备被停用时调用，无论是显式还是隐式地。
当系统需要发送一个帧时，它通过调用 `ndo_start_xmit` 来实现，该函数将帧入队到设备中。如果设备的硬件队列（FIFO、邮箱或其他实现方式）变得满时，`ndo_start_xmit` 的实现在通过 `netif_stop_queue` 停止发送队列时会通知网络子系统。当设备再次有可用空间并且能够入队另一个帧时，会在中断服务例程（ISR）中重新启用。

所有设备事件都在 ISR 中处理，具体如下：

1. **发送完成**。当设备成功完成一个帧的传输后，该帧会被本地回显。在发生错误时，会向网络子系统发送一个具有信息性的错误帧 [2]_。在这两种情况下，都会恢复软件发送队列以便可以发送更多帧。
2. **错误条件**。如果出现问题（例如，设备进入总线关闭状态或接收缓冲区溢出），则更新错误计数器，并将具有信息性的错误帧入队到软件接收队列。
3. **接收缓冲区非空**。在这种情况下，读取接收帧并将它们入队到软件接收队列。通常使用 NAPI 作为中间层（见下文）。

### NAPI

传入帧的频率可能很高，为每个帧调用中断服务例程所带来的开销可能导致显著的系统负载。Linux 内核中有多种机制来处理这种情况。这些机制在多年的 Linux 内核开发和改进过程中不断演变。对于网络设备，当前的标准是 NAPI（新 API）。它类似于经典的上半部/下半部中断处理方法，即仅在 ISR 中确认中断并发出信号，指示其余处理应在软中断上下文中进行。此外，它还提供了在一段时间内轮询新帧的可能性。这有可能避免启用中断、在 ISR 中处理传入 IRQ、重新启用软中断并切换回软中断上下文所带来的昂贵开销。更多信息请参阅 :ref:`Documentation/networking/napi.rst <napi>`。

### 将核心集成到 Xilinx Zynq

该核心接口是一个简单的 Avalon （搜索 Intel **Avalon 接口规范**）总线子集，最初用于 Altera FPGA 芯片。然而，Xilinx 本机接口使用的是 AXI（搜索 ARM **AMBA AXI 和 ACE 协议规范 AXI3, AXI4 和 AXI4-Lite, ACE 和 ACE-Lite**）。

最明显的解决方案是使用 Avalon/AXI 桥接器或实现一些简单的转换实体。然而，该核心的接口是半双工且没有握手信号，而 AXI 是全双工且具有双向信号。此外，即使是 AXI-Lite 从接口也相当耗费资源，而且 CAN 核心并不需要 AXI 的灵活性和速度。
因此，选择了一个更简单的总线——APB（高级外设总线）
（搜索ARM **AMBA APB 协议规范**）
APB-AXI 桥接器在 Xilinx Vivado 中可以直接使用，接口适配器实体仅需几个简单的组合赋值。

最后，为了能够将该核心作为一个自定义 IP 包含在块图中，该核心连同 APB 接口一起被打包为一个 Vivado 组件。
CTU CAN FD 驱动设计
------------------------

CAN 设备驱动的一般结构已经在前面进行了探讨。接下来的段落将提供对 CTU CAN FD 核心驱动更详细的描述。
低级驱动
~~~~~~~~~

该核心并非仅用于 SocketCAN，因此需要有一个与操作系统无关的低级驱动。这种低级驱动可以用于操作系统的驱动实现或直接用于裸机系统或用户空间应用程序。另一个优点是，如果硬件略有变动，只需修改低级驱动即可。

代码 [3]_ 部分是自动生成的，部分是由核心作者手动编写的，并有论文作者的贡献。低级驱动支持以下操作：设置位定时、设置控制器模式、启用/禁用、读取接收帧、写入发送帧等。
配置位定时
~~~~~~~~~~~

在 CAN 总线上，每个比特被分为四个段：SYNC（同步）、PROP（传播）、PHASE1 和 PHASE2。它们的持续时间以时间量子的倍数表示（详情见 `CAN 规范 2.0 版本 <http://esd.cs.ucr.edu/webres/can20.pdf>`_ 第八章）。

在配置比特率时，必须根据比特率和采样点计算所有段（以及时间量子）的持续时间。对于 CAN FD 的名义比特率和数据比特率，这些计算是独立进行的。

SocketCAN 相当灵活，既可以通过手动设置所有段的持续时间来实现高度定制化的配置，也可以通过仅设置比特率和采样点来实现方便的配置（如果不指定，则根据博世推荐自动选择）。然而，每个 CAN 控制器可能有不同的基频和不同的段持续时间寄存器宽度。因此，算法需要知道持续时间和时钟预分频器的最小值和最大值，并尝试优化数值以满足约束条件和请求参数。
```c
struct can_bittiming_const {
    char name[16];      /* CAN控制器硬件的名称 */
    __u32 tseg1_min;    /* 时间段1 = prop_seg + phase_seg1 */
    __u32 tseg1_max;
    __u32 tseg2_min;    /* 时间段2 = phase_seg2 */
    __u32 tseg2_max;
    __u32 sjw_max;      /* 同步跳跃宽度 */
    __u32 brp_min;      /* 位率预分频器 */
    __u32 brp_max;
    __u32 brp_inc;
};
```

[lst:can_bittiming_const]

细心的读者会注意到，PROP_SEG 和 PHASE_SEG1 的持续时间不是单独确定的，而是合并后，默认情况下将得到的 TSEG1 均匀分配给 PROP_SEG 和 PHASE_SEG1。实际上，这几乎没有后果，因为采样点位于 PHASE_SEG1 和 PHASE_SEG2 之间。然而，在 CTU CAN FD 中，持续时间寄存器 `PROP` 和 `PH1` 的位宽不同（分别为 6 位和 7 位），因此自动生成的值可能会超出较短的寄存器，必须重新分配 [4]_

处理接收
~~~~~~~~~~

帧接收由 NAPI 队列处理，当 RXNE（接收 FIFO 非空）位被设置时，NAPI 队列在中断服务程序中启用。帧逐个读取，直到接收 FIFO 中没有剩余帧或 NAPI 轮询运行达到最大工作配额（参见）。每个帧随后传递到网络接口接收队列。
一个接收到的帧可能是 CAN 2.0 帧或 CAN FD 帧。在内核中区分这两种帧的方法是分配 `struct can_frame` 或 `struct canfd_frame`，两者具有不同的大小。在控制器中，关于帧类型的信息存储在接收 FIFO 的第一个字中。
这带来了鸡与蛋的问题：我们希望为帧分配 `skb`，只有在成功分配后才从 FIFO 中获取帧；否则将其保留在那里以备后用。但为了能够正确分配 `skb`，我们必须先读取 FIFO 的第一个字。有几种可能的解决方案：

1. 读取字，然后分配。如果分配失败，则丢弃其余部分的帧。当系统内存不足时，情况已经很糟糕了。
2. 总是预先分配足够大的 `skb` 以容纳 FD 帧。然后调整 `skb` 的内部结构，使其看起来像是为较小的 CAN 2.0 帧分配的。
3. 添加选项来查看 FIFO 而不是消耗该字。
4. 如果分配失败，将读取的字存储在驱动程序的数据中。下次尝试时，使用已存储的字而不是再次读取。

选项 1 简单，但如果可以做得更好就不令人满意。选项 2 不可接受，因为它需要修改内核结构的私有状态。稍高的内存消耗只是“蛋糕”上的虚拟樱桃。选项 3 需要非平凡的硬件更改，并且从硬件角度来看并不理想。
选项 4 看起来是一个不错的折衷方案，其缺点是部分帧可能会在 FIFO 中停留较长时间。然而，可能只有一个所有者拥有接收 FIFO，因此没有人会看到部分帧（忽略一些奇特的调试场景）。此外，驱动程序在初始化时重置核心，因此部分帧也无法被“收养”。最终选择了选项 4 [5]_
### 接收帧的时间戳
^^^^^^^^^^^^^^^^^^^^^^

CTU CAN FD 核报告了接收帧的确切时间戳。默认情况下，时间戳是在帧结束标志（EOF）的最后一个比特位的采样点捕获的，但也可以配置为在起始标志（SOF）位捕获。时间戳源位于核心外部，宽度可达 64 位。截至本文撰写时，从内核传递时间戳到用户空间的功能尚未实现，但计划在未来实现。

### 处理发送
~~~~~~~~~~~

CTU CAN FD 核有 4 个独立的发送缓冲区，每个缓冲区有自己的状态和优先级。当核需要发送时，会选择一个处于 Ready 状态且优先级最高的发送缓冲区。优先级是一个 3 位数，在寄存器 `TX_PRIORITY` 中表示（字节对齐）。这应该足够灵活以适应大多数应用场景。然而，SocketCAN 只支持一个 FIFO 队列用于传出帧 [6]_。可以通过为每个缓冲区分配不同的优先级并在帧传输完成后 *旋转* 优先级来模拟 FIFO 行为。除了优先级旋转外，软件还必须维护 FIFO 队列中发送缓冲区的头指针和尾指针，以便能够确定下一个应使用的缓冲区 (`txb_head`) 和第一个完成的缓冲区 (`txb_tail`)。实际缓冲区索引显然是模 4 的（发送缓冲区的数量），但指针必须至少宽一位，以便能够区分 FIFO 满和 FIFO 空的情况——在这种情况下，`txb_head ≡ txb_tail (mod 4)`。FIFO 的维护示例如下：

```
+------+---+---+---+---+
| TXB# | 0 | 1 | 2 | 3 |
+======+===+===+===+===+
| Seq  | A | B | C |   |
+------+---+---+---+---+
| Prio | 7 | 6 | 5 | 4 |
+------+---+---+---+---+
|      |   | T |   | H |
+------+---+---+---+---+
```

```
+------+---+---+---+---+
| TXB# | 0 | 1 | 2 | 3 |
+======+===+===+===+===+
| Seq  |   | B | C |   |
+------+---+---+---+---+
| Prio | 4 | 7 | 6 | 5 |
+------+---+---+---+---+
|      |   | T |   | H |
+------+---+---+---+---+
```

```
+------+---+---+---+---+----+
| TXB# | 0 | 1 | 2 | 3 | 0’ |
+======+===+===+===+===+====+
| Seq  | E | B | C | D |    |
+------+---+---+---+---+----+
| Prio | 4 | 7 | 6 | 5 |    |
+------+---+---+---+----+----+
|      |   | T |   |   | H  |
+------+---+---+---+---+----+
```

```
.. kernel-figure:: fsm_txt_buffer_user.svg
   发送缓冲区状态及其可能的转换
```

### 发送帧的时间戳
^^^^^^^^^^^^^^^^^^^^^^

提交帧到发送缓冲区时，可以指定该帧应在哪个时间戳进行发送。帧的实际发送可能会晚于指定的时间戳，但不会早于它。注意，时间戳不参与缓冲区优先级排序——这是由上述机制决定的。基于时间的包发送功能最近被合并到了 Linux v4.19 `基于时间的包发送 <https://lwn.net/Articles/748879/>`_，但还需要研究这一功能是否适用于 CAN。类似地，核心支持获取发送帧的时间戳，即帧成功传输的时间。具体细节与接收帧的时间戳非常相似，详情见上文。

### 处理接收缓冲区溢出
~~~~~~~~~~~~~~~~~~~~~~~~~~

当接收到的帧无法完全放入硬件接收 FIFO 缓冲区时，会设置接收 FIFO 溢出标志（STATUS[DOR]）并触发数据溢出中断（DOI）。处理中断时，首先必须清除 DOR 标志（通过 COMMAND[CDO]），然后清除 DOI 中断标志。否则，中断会立即重新触发。
**注**：开发过程中曾讨论过内部硬件流水线是否会破坏这个清除序列，是否需要在清除标志和中断之间插入一个虚拟周期。在 Avalon 接口中确实证明了这种情况，但 APB 是安全的，因为它使用两周期事务。基本上，DOR 标志会被清除，但在 DOI 清除请求应用的同时，DOI 寄存器的 Preset 输入仍然为高电平。由于 Set 优先级高于 Reset，因此 DOI 标志不会被复位。这个问题已经通过交换 Set/Reset 优先级解决了（参见问题 #187）。
报告错误被动和总线关闭状态

可能需要报告节点达到*错误被动*、*错误警告*和*总线关闭*状态的情况。驱动程序通过中断（EPI，EWLI）得知错误状态的变化，然后通过读取其错误计数器来确定内核的错误状态。然而，在这里存在一个轻微的竞争条件——状态转换发生（并触发中断）与读取错误计数器之间存在延迟。当接收到EPI时，节点可能是*错误被动*或*总线关闭*。如果节点进入*总线关闭*状态，则显然会保持该状态直到复位；否则，节点是*或曾是* *错误被动*。然而，可能会出现读取的状态为*错误警告*甚至*错误活动*。在这种情况下，是否以及如何报告可能不清楚，但个人认为仍然应该报告过去的错误状态。类似地，当接收到EWLI但后来检测到状态为*错误被动*时，应报告*错误被动*。

CTU CAN FD 驱动源代码参考
--------------------------

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd.h
   :internal:

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd_base.c
   :internal:

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd_pci.c
   :internal:

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd_platform.c
   :internal:

CTU CAN FD IP 核心和驱动开发致谢
-------------------------------

* Odrej Ille <ondrej.ille@gmail.com>

  * 作为捷克技术大学电气工程学院测量系的学生开始了这个项目
  * 多年来投入了大量的个人时间和热情
  * 完成了多个资助任务

* `测量系 <https://meas.fel.cvut.cz/>`_，
  `电气工程学院 <http://www.fel.cvut.cz/en/>`_，
  `捷克技术大学 <https://www.cvut.cz/en>`_

  * 多年来一直是该项目的主要投资者
  * 在其CAN/CAN FD诊断框架中使用该项目为斯柯达汽车提供支持

* `Digiteq Automotive <https://www.digiteqautomotive.com/en>`_

  * 资助了CAN FD开放内核支持Linux内核系统项目
  * 协商并支付了捷克技术大学以允许公众访问该项目
  * 提供了额外的资金支持

* `控制工程系 <https://control.fel.cvut.cz/en>`_，
  `电气工程学院 <http://www.fel.cvut.cz/en/>`_，
  `捷克技术大学 <https://www.cvut.cz/en>`_

  * 解决了CAN FD开放内核支持Linux内核系统项目
  * 提供GitLab管理
  * 提供虚拟服务器和计算能力用于持续集成
  * 提供硬件用于HIL持续集成测试

* `PiKRON Ltd. <http://pikron.com/>`

  * 提供少量资金启动项目的开源工作

* Petr Porazil <porazil@pikron.com>

  * 设计PCIe收发器附加板及组装板
  * 设计和组装基于MicroZed/Zynq系统的MZ_APO基板

* Martin Jerabek <martin.jerabek01@gmail.com>

  * 开发Linux驱动
  * 持续集成平台架构师和GHDL更新
  * 论文《开源和开放硬件CAN FD协议支持》

* Jiri Novak <jnovak@fel.cvut.cz>

  * 在捷克技术大学电气工程学院测量系启动、管理和使用项目

* Pavel Pisa <pisa@cmp.felk.cvut.cz>

  * 发起开源，协调和管理捷克技术大学电气工程学院控制工程系的项目

* Jaroslav Beran<jara.beran@gmail.com>

  * 为Intel SoC进行系统集成，核心和驱动测试及更新

* Carsten Emde (`OSADL <https://www.osadl.org/>`_)

  * 提供了OSADL专业知识讨论IP核心许可问题
  * 指出LGPL和CAN总线可能的专利问题导致重新授权IP核心设计为BSD类许可证

* Reiner Zitzmann 和 Holger Zeltwanger (`CAN in Automation <https://www.can-cia.org/>`_)

  * 提供建议和帮助以通知社区关于该项目，并邀请我们参加专注于CAN总线未来发展方向的活动

* Jan Charvat

  * 实现了CTU CAN FD功能模型并将其集成到QEMU主线(`docs/system/devices/can.rst <https://www.qemu.org/docs/master/system/devices/can.html>`_)
  * 学士论文《QEMU仿真器的CAN FD通信控制器模型》

注释
-----

.. [1]
   其他总线有它们自己特定的驱动接口来设置设备。
.. [2]
   不要与CAN错误帧混淆。这是一个设置了`CAN_ERR_FLAG`标志的`can_frame`，并在其`data`字段中包含一些错误信息。
.. [3]
   可在CTU CAN FD仓库中找到
   `<https://gitlab.fel.cvut.cz/canbus/ctucanfd_ip_core>`_

.. [4]
   低级驱动函数`ctucan_hw_set_nom_bittiming`和`ctucan_hw_set_data_bittiming`中所做的那样。
.. [5]
   在撰写本论文时，选项1仍在使用中，并且修改已在gitlab问题#222中排队。
.. [6]
   严格来说，自v4.19起支持多个CAN TX队列
   `can: enable multi-queue for SocketCAN devices <https://lore.kernel.org/patchwork/patch/913526/>`_，但尚未有主线驱动使用它们。
.. [7]
   或者更准确地说，在下一个时钟周期。
