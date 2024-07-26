SPDX 许可证标识符: GPL-2.0 或更高版本

CTU CAN FD 驱动程序
==================

作者: Martin Jerabek <martin.jerabek01@gmail.com>

关于 CTU CAN FD IP 核心
-----------------------

`CTU CAN FD <https://gitlab.fel.cvut.cz/canbus/ctucanfd_ip_core>`_ 是用 VHDL 编写的开源软核。
它起源于 2015 年作为 Ondrej Ille 在 `捷克工业大学 (CTU) <https://www.cvut.cz/en>`_ 电子工程学院 (`FEE <http://www.fel.cvut.cz/en/>`_) 的测量系 (`Department of Measurement <https://meas.fel.cvut.cz/>`_) 的项目。
为基于 Xilinx Zynq 系统芯片 (SoC) 的 MicroZed 板卡开发了 `Vivado 集成 <https://gitlab.fel.cvut.cz/canbus/zynq/zynq-can-sja1000-top>`_ 的 SocketCAN 驱动程序，以及为基于 Intel Cyclone V 5CSEMA4U23C6 的 Terasic DE0-Nano-SoC 板卡开发了 `QSys 集成 <https://gitlab.fel.cvut.cz/canbus/intel-soc-ctucanfd>`_。
此外还支持 `PCIe 集成 <https://gitlab.fel.cvut.cz/canbus/pcie-ctucanfd>`_。在 Zynq 的情况下，核心通过 APB 系统总线连接，该总线不支持枚举，因此必须在设备树中指定设备。
这种类型的设备在内核中称为平台设备，并由平台设备驱动程序处理。
CTU CAN FD 外设的基本功能模型已被接受进入 QEMU 主线。参见 QEMU 的 `CAN 模拟支持 <https://www.qemu.org/docs/master/system/devices/can.html>`_ 了解关于 CAN FD 总线、主机连接和 CTU CAN FD 核心模拟的信息。模拟支持的开发版本可以从 QEMU 本地开发的 `仓库 <https://gitlab.fel.cvut.cz/canbus/qemu-canbus>`_ 中 ctu-canfd 分支克隆。

关于 SocketCAN
---------------

SocketCAN 是 Linux 内核中 CAN 设备的标准通用接口。如其名称所示，该总线是通过套接字访问的，类似于常见的网络设备。其背后的原因在 `Linux SocketCAN <https://www.kernel.org/doc/html/latest/networking/can.html>`_ 中进行了深入描述。
简而言之，它提供了一种自然的方式来实现和使用 CAN 上的高层协议，就像以太网上的 UDP/IP 一样。

设备探测
~~~~~~~~~~

在详细介绍 CAN 总线设备驱动程序的结构之前，让我们先回顾一下内核是如何了解设备的。
某些总线（如 PCI 或 PCIe）支持设备枚举。也就是说，在系统启动时，它会发现总线上的所有设备并读取它们的配置。内核通过其供应商 ID 和设备 ID 来识别设备，如果有一个针对此 ID 组合注册的驱动程序，则会调用其探测方法来填充给定硬件的驱动程序实例。USB 类似于此情况，只是它允许热插拔设备。
情况对于直接嵌入在片上系统（SoC）中并连接到内部系统总线（如 AXI、APB、Avalon 等）的外设是不同的。这些总线不支持枚举功能，因此内核必须从其他地方了解这些设备的信息。这正是设备树发挥作用的地方。

### 设备树

设备树中的一个条目说明了系统中存在的某个设备，以及如何访问该设备（它位于哪个总线上），还包括其配置信息——寄存器地址、中断等。下面是一个这样的设备树示例：
```plaintext
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
```

### 驱动结构

驱动可以分为两部分：与平台相关的设备发现和设置，以及与平台无关的 CAN 网络设备实现。

#### 平台设备驱动

以 Zynq 为例，核心通过 AXI 系统总线连接，而这个总线不支持枚举功能，因此需要在设备树中指定设备。这种类型的设备在内核中被称为“平台设备”，由“平台设备驱动”来处理。

平台设备驱动提供了以下内容：

- 一个**探查**函数
- 一个**移除**函数
- 可处理的**兼容**设备列表

**探查**函数会在设备出现时（或驱动加载时，以较晚发生者为准）被调用一次。如果有多个设备由同一个驱动处理，则会对每个设备调用一次**探查**函数。其作用是分配和初始化处理设备所需的资源，并为与平台无关的层设置低级函数，例如 `read_reg` 和 `write_reg`。之后，驱动将设备注册给更高层，在本例中作为“网络设备”。

**移除**函数会在设备消失或驱动即将卸载时被调用。它的作用是释放**探查**函数中分配的资源，并从更高层注销设备。

最后，**兼容**设备列表指明了驱动可以处理哪些设备。设备树条目 `compatible` 将与所有“平台驱动”的表进行匹配。
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

每个网络设备至少需要支持以下操作：

- 使设备上线：`ndo_open`
- 使设备下线：`ndo_close`
- 向设备提交发送帧：`ndo_start_xmit`
- 向网络子系统报告发送完成及错误：中断服务例程（ISR）
- 向网络子系统提交接收帧：中断服务例程（ISR）和 NAPI

存在两种可能的事件源：设备和网络子系统。设备事件通常通过中断信号，由中断服务例程（ISR）处理。网络子系统产生的事件则在 `struct net_device_ops` 中定义处理函数。

当设备上线时（例如，通过调用 `ip link set can0 up`），会调用驱动的 `ndo_open` 函数。该函数应验证接口配置，并配置和启用设备。与此相对的是 `ndo_close`，在设备下线时调用，无论是显式还是隐式地。
当系统需要发送一个帧时，它通过调用`ndo_start_xmit`来实现，该函数将帧加入到设备队列中。如果设备的硬件队列（无论是FIFO、邮箱还是其他实现方式）变得满了，`ndo_start_xmit`的实现会通知网络子系统停止TX队列（通过`netif_stop_queue`）。当设备再次有可用空间并且能够加入另一个帧时，TX队列会在中断服务例程(ISR)中重新启用。
所有的设备事件都在ISR中处理，具体包括：

1. **TX完成**。当设备成功完成一个帧的传输后，该帧会被本地回显。若发生错误，则向网络子系统发送一个信息性的错误帧[2]。无论哪种情况，都会恢复软件TX队列，以便可以发送更多的帧。
2. **错误条件**。如果出现异常情况（例如，设备进入总线关闭状态或发生RX溢出），则更新错误计数器，并将信息性的错误帧加入到SW RX队列。
3. **RX缓冲区非空**。在这种情况下，读取RX帧并将其加入到SW RX队列。通常使用NAPI作为中间层（参见下文）。

### NAPI

传入帧的频率可能非常高，为每个帧调用中断服务例程所带来的开销可能导致显著的系统负载。Linux内核中有多种机制来应对这种情况。这些机制随着Linux内核多年的发展和改进而不断演进。对于网络设备而言，当前的标准是NAPI——即“新API”。它与经典的上半部/下半部中断处理类似，仅在ISR中确认中断，并发出信号表明其余的处理应在softirq上下文中进行。此外，它还提供了一段时间内*轮询*新帧的可能性。这有可能避免开启中断、在ISR中处理传入IRQ、重新启用softirq以及切换回softirq上下文的成本。
更多关于NAPI的信息，请参考：:ref:`Documentation/networking/napi.rst <napi>`

### 将核心集成至Xilinx Zynq

该核心接口了一个简单的Avalon（搜索Intel **Avalon Interface Specifications**）总线子集，最初用于Altera FPGA芯片。然而，Xilinx原生支持的是AXI（搜索ARM **AMBA AXI and ACE Protocol Specification AXI3, AXI4, and AXI4-Lite, ACE and ACE-Lite**）。
最直接的解决方案可能是使用Avalon/AXI桥接器或者实现一些简单的转换实体。但是，该核心的接口是半双工且无握手信号，而AXI是全双工且具有双向信号。此外，即使是AXI-Lite从属接口也相当资源密集，而对于CAN核心而言，AXI的灵活性和速度并非必需。
因此选择了一个更简单的总线——APB（高级外设总线）
（搜索 **ARM AMBA APB 协议规范**）
APB-AXI 桥接器在 Xilinx Vivado 中可以直接使用，而接口适配器实体只是几个简单的组合赋值。
最终，为了能够将该核心作为一个自定义 IP 包含在方块图中，核心及其 APB 接口被封装为一个 Vivado 组件。
CTU CAN FD 驱动设计
------------------------

CAN 设备驱动的一般结构已经在前文中探讨过。接下来的几段将提供对 CTU CAN FD 核心驱动的更详细描述。

低层驱动
~~~~~~~~~

该核心并非仅用于 SocketCAN，因此希望有一个与操作系统无关的低层驱动。这种低层驱动可以用于实现操作系统驱动或直接在裸机上使用，或者在用户空间的应用程序中使用。另一个优点是如果硬件稍有变动，只需修改低层驱动即可。

代码 [3]_ 部分是自动生成的，部分是由核心作者手动编写的，并且有论文作者的贡献。
低层驱动支持的操作包括：设置位定时、设置控制器模式、启用/禁用、读取接收帧、写入发送帧等。

配置位定时
~~~~~~~~~~

在 CAN 总线上，每个比特位被分为四个阶段：同步段（SYNC）、传播段（PROP）、相位缓冲段 1（PHASE1）和相位缓冲段 2（PHASE2）。这些阶段的持续时间以时间量子的倍数表示（详情见 `CAN 规范，版本 2.0 <http://esd.cs.ucr.edu/webres/can20.pdf>`_，第 8 章）。

配置比特率时，需要根据比特率和采样点计算所有阶段（及时间量子）的持续时间。对于 CAN FD 的名义比特率和数据比特率，这都是独立完成的。

SocketCAN 具有很高的灵活性，既可以手动设置所有阶段的持续时间来实现高度定制化的配置，也可以通过只设置比特率和采样点来方便地进行配置（如果没有指定，则根据博世推荐自动选择）。然而，每个 CAN 控制器可能具有不同的基频时钟和不同的阶段持续时间寄存器宽度。因此，算法需要知道持续时间和时钟预分频器的最小值和最大值，并试图优化数值以满足约束条件和请求的参数。
以下是提供的C语言结构体及其描述的中文翻译：

```c
struct can_bittiming_const { 
    char name[16];      /* CAN控制器硬件的名称 */
    __u32 tseg1_min;    /* 时间段1 = PROP_SEG + PHASE_SEG1 */
    __u32 tseg1_max;
    __u32 tseg2_min;    /* 时间段2 = PHASE_SEG2 */
    __u32 tseg2_max;
    __u32 sjw_max;      /* 同步跳跃宽度 */
    __u32 brp_min;      /* 位率预分频器 */
    __u32 brp_max;
    __u32 brp_inc;
};
```

[List: can_bittiming_const]

细心的读者会注意到，PROP_SEG 和 PHASE_SEG1 的持续时间并非单独确定，而是合并后默认将得到的 TSEG1 均等分割给这两个阶段。实际上，这几乎不会产生影响，因为采样点位于 PHASE_SEG1 和 PHASE_SEG2 之间。然而，在 CTU CAN FD 中，“PROP”和“PH1”两个持续时间寄存器的位宽不同（分别为6位和7位），因此自动生成的值可能会超出较短寄存器的范围，必须在这两个寄存器间重新分配 [4]_

### 处理接收

帧接收在NAPI队列中处理，当 RXNE（接收FIFO非空）标志被设置时，从中断服务例程（ISR）启用该队列。帧逐一读取，直到接收FIFO中没有剩余帧或NAPI轮询运行达到最大工作配额（参见 ）。每个帧随后传递到网络接口的接收队列。

一个接收到的帧可能是CAN 2.0帧或CAN FD帧。在内核中区分这两种帧的方式是为它们分配`struct can_frame`或`struct canfd_frame`，这两者具有不同的大小。在控制器中，帧类型的信息存储在接收FIFO的第一字中。

这带来了一个先有鸡还是先有蛋的问题：我们想要为帧分配`skb`，只有在成功分配后才从FIFO中获取帧；否则将其保留在那里以供后续使用。但为了能够正确地分配`skb`，我们必须先从FIFO中获取第一个字。存在几种可能的解决方案：

1. 读取字，然后尝试分配。如果分配失败，则丢弃帧的其余部分。当系统内存不足时，情况本来就很糟糕。
2. 总是预先分配足够大的`skb`来容纳FD帧。然后根据实际情况调整`skb`的内部数据以看起来像是为较小的CAN 2.0帧分配的。
3. 添加选项允许查看FIFO而不消耗字。
4. 如果分配失败，将读取的字存储在驱动程序的数据中。下次尝试时使用已存储的字而不是再次读取。

选项1虽然简单，但如果能有更好的方法则不太令人满意。选项2不可接受，因为它需要修改核心内核结构的私有状态。稍高的内存消耗只是“蛋糕”上的虚拟樱桃。选项3需要不简单的硬件更改，并且从硬件角度来看并不理想。

选项4似乎是一个不错的折衷方案，其缺点是部分帧可能长时间停留在FIFO中。不过，可能只有一个所有者拥有接收FIFO，因此没有人能看到这个部分帧（忽略一些稀奇古怪的调试场景）。此外，驱动程序在其初始化时重置核心，因此不可能“收养”这部分帧。最终选择了选项4 [5]_
接收帧的时间戳记录
^^^^^^^^^^^^^^^^^^^^^^

CTU CAN FD 核报告接收帧的确切时间戳。默认情况下，时间戳在帧结束（EOF）的最后一个比特的采样点捕获，但也可以配置为在帧起始（SOF）比特处捕获。时间戳源位于核外部，宽度可达 64 位。截至本文档编写时，从内核传递时间戳到用户空间的功能尚未实现，但计划在未来添加。
处理发送
~~~~~~~~~~~

CTU CAN FD 核有 4 个独立的发送缓冲区，每个缓冲区有自己的状态和优先级。当核准备发送时，将选择处于就绪状态且具有最高优先级的发送缓冲区进行传输。
优先级是寄存器 `TX_PRIORITY` 中的 3 位数字（按字节对齐）。这应该足够灵活以适应大多数应用场景。然而，SocketCAN 只支持一个 FIFO 队列用于传出帧 [6]_。可以通过为每个缓冲区分配不同的优先级并在完成帧传输后“旋转”这些优先级来模拟 FIFO 行为。
除了优先级旋转之外，软件还必须维护 FIFO 队列中发送缓冲区的头部和尾部指针，以便确定哪个缓冲区应用于下一个帧 (`txb_head`) 以及哪一个应是第一个完成的 (`txb_tail`)。实际缓冲区索引显然是模 4（发送缓冲区的数量），但是指针必须至少宽一位才能区分 FIFO 已满和 FIFO 空的情况 — 在这种情况下，`txb_head ≡ txb_tail (mod 4)`。FIFO 的维护方式以及优先级旋转的一个示例如下：

|

+------+---+---+---+---+
| TXB# | 0 | 1 | 2 | 3 |
+======+===+===+===+===+
| 序号 | A | B | C |   |
+------+---+---+---+---+
| 优先级 | 7 | 6 | 5 | 4 |
+------+---+---+---+---+
|       |   | T |   | H |
+------+---+---+---+---+

|

+------+---+---+---+---+
| TXB# | 0 | 1 | 2 | 3 |
+======+===+===+===+===+
| 序号 |   | B | C |   |
+------+---+---+---+---+
| 优先级 | 4 | 7 | 6 | 5 |
+------+---+---+---+---+
|       |   | T |   | H |
+------+---+---+---+---+

|

+------+---+---+---+---+----+
| TXB# | 0 | 1 | 2 | 3 | 0’ |
+======+===+===+===+===+====+
| 序号 | E | B | C | D |    |
+------+---+---+---+---+----+
| 优先级 | 4 | 7 | 6 | 5 |    |
+------+---+---+---+---+----+
|       |   | T |   |   | H  |
+------+---+---+---+---+----+

|

.. kernel-figure:: fsm_txt_buffer_user.svg

   发送缓冲区的状态及其可能的转换

发送帧的时间戳记录
^^^^^^^^^^^^^^^^^^^^^^

向发送缓冲区提交帧时，可以指定帧应被发送的时间戳。帧的传输可能会晚于这个时间戳开始，但不会早于它。需要注意的是，时间戳不参与缓冲区优先级的决策 — 这完全由上述机制决定。
基于时间的包传输支持最近被合并到了 Linux v4.19 `基于时间的包传输 <https://lwn.net/Articles/748879/>`_，但还需进一步研究该功能是否适用于 CAN。
与获取接收帧的时间戳类似，核心也支持检索发送帧的时间戳 — 即帧成功发送的时间。具体细节与接收帧的时间戳记录非常相似，并在上文中描述过。

处理接收缓冲区溢出
~~~~~~~~~~~~~~~~~~~~~~~~~~

当接收到的帧无法完整地放入硬件接收 FIFO 中时，会设置 RX FIFO 溢出标志 (STATUS[DOR]) 并触发数据溢出中断 (DOI)。在处理此中断时，首先需要清除 DOR 标志（通过 COMMAND[CDO]），之后再清除 DOI 中断标志。否则，中断会立即重新触发 [7]_。
**注**：在开发过程中，曾讨论过内部硬件流水线是否会破坏这个清除序列，是否有必要在清除标志和中断之间增加一个空周期。在 Avalon 接口中确实证明了这一点，但 APB 是安全的因为它使用两周期事务。基本上，DOR 标志会被清除，但在 DOI 清除请求（即设置 DOI 寄存器的 Reset 输入为高电平）应用的周期里，DOI 寄存器的 Preset 输入仍然保持高电平。因为 Set 的优先级高于 Reset，所以 DOI 标志不会被重置。这个问题已经通过交换 Set/Reset 的优先级得以解决（参见问题 #187）。
报告错误被动和总线关闭状态
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在节点达到*错误被动*、*错误警告*和*总线关闭*状态时进行报告可能是有益的。驱动程序通过中断（EPI，EWLI）得知错误状态的变化，然后通过读取其错误计数器来确定内核的错误状态。然而，在这里存在轻微的竞争条件——状态转换发生（并触发中断）与读取错误计数器之间存在延迟。当接收到EPI时，节点可能处于*错误被动*或*总线关闭*状态。如果节点进入*总线关闭*状态，则显然会保持该状态直到被重置；否则，节点是*或曾经是* *错误被动*。然而，读取的状态可能是*错误警告*甚至*错误活动*。在这种情况下，是否以及确切地报告什么可能不明确，但我个人倾向于认为仍然应该报告过去的错误条件。类似地，当接收到EWLI但后来检测到的状态为*错误被动*时，应报告*错误被动*。

CTU CAN FD 驱动源码参考
-----------------------------------

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd.h
   :internal:

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd_base.c
   :internal:

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd_pci.c
   :internal:

.. kernel-doc:: drivers/net/can/ctucanfd/ctucanfd_platform.c
   :internal:

CTU CAN FD IP 核心及驱动开发致谢
---------------------------------------------------------

* Odrej Ille <ondrej.ille@gmail.com>

  * 作为捷克技术大学电气工程学院测量系的学生开始这个项目
  * 在多年里投入了大量的个人时间和热情到项目中
  * 完成了更多的资助任务

* `测量系 <https://meas.fel.cvut.cz/>`_，
  `电气工程学院 <http://www.fel.cvut.cz/en/>`_，
  `捷克技术大学 <https://www.cvut.cz/en>`_

  * 多年来一直是该项目的主要投资者
  * 在他们的CAN/CAN FD诊断框架中使用了该项目为斯柯达汽车服务

* `Digiteq Automotive <https://www.digiteqautomotive.com/en>`_

  * 资助了CAN FD开源核心支持Linux内核系统项目
  * 协商并支付给捷克技术大学以允许公众访问该项目
  * 提供额外的资金支持工作

* `控制工程系 <https://control.fel.cvut.cz/en>`_，
  `电气工程学院 <http://www.fel.cvut.cz/en/>`_，
  `捷克技术大学 <https://www.cvut.cz/en>`_

  * 解决了CAN FD开源核心支持Linux内核系统项目
  * 提供GitLab管理
  * 为持续集成提供虚拟服务器和计算能力
  * 为硬件在环持续集成测试提供硬件

* `PiKRON有限公司 <http://pikron.com/>`_

  * 为启动项目的开源准备提供少量资金

* Petr Porazil <porazil@pikron.com>

  * 设计PCIe收发器附加板和组装电路板
  * 设计和组装基于MicroZed/Zynq系统的MZ_APO基板

* Martin Jerabek <martin.jerabek01@gmail.com>

  * Linux驱动开发
  * 持续集成平台架构师和GHDL更新
  * 论文《开放源代码和开放硬件CAN FD协议支持》

* Jiri Novak <jnovak@fel.cvut.cz>

  * 在捷克技术大学电气工程学院测量系启动、管理和使用该项目

* Pavel Pisa <pisa@cmp.felk.cvut.cz>

  * 开始开源化，协调和管理捷克技术大学电气工程学院控制工程系的项目

* Jaroslav Beran <jara.beran@gmail.com>

  * 英特尔SoC系统集成，核心和驱动测试及更新

* Carsten Emde (`OSADL <https://www.osadl.org/>`_)

  * 提供OSADL专业知识讨论IP核心许可问题
  * 指出了LGPL可能导致的死锁和CAN总线可能的专利案例，这导致重新授权IP核心设计为类似BSD的许可

* Reiner Zitzmann 和 Holger Zeltwanger (`CAN in Automation <https://www.can-cia.org/>`_)

  * 提供建议和帮助通知社区关于该项目，并邀请我们参加专注于CAN总线未来发展方向的活动

* Jan Charvat

  * 实现了CTU CAN FD功能模型，该模型已集成到QEMU主线(`docs/system/devices/can.rst <https://www.qemu.org/docs/master/system/devices/can.html>`_)
  * 学士论文《QEMU模拟器中的CAN FD通信控制器模型》

注释
-----

.. [1]
   其他总线有自己的特定驱动接口来设置设备。
.. [2]
   不要与CAN错误帧混淆。这是一个带有`CAN_ERR_FLAG`标志的`can_frame`，其`data`字段包含一些错误信息。
.. [3]
   可用在CTU CAN FD仓库中
   `<https://gitlab.fel.cvut.cz/canbus/ctucanfd_ip_core>`_

.. [4]
   正如低级驱动函数`ctucan_hw_set_nom_bittiming`和`ctucan_hw_set_data_bittiming`所做的一样。
.. [5]
   在撰写本论文时，选项1仍在使用中，并且修改已在GitLab问题#222中排队。

.. [6]
   严格来说，自v4.19起已经支持多个CAN TX队列
   `can: enable multi-queue for SocketCAN devices <https://lore.kernel.org/patchwork/patch/913526/>`_ 但是尚未有主线驱动使用它们。
.. [7]
   或者更准确地说，在下一个时钟周期中。
