编写 MUSB 黏合层
=========================

:作者: Apelete Seketeli

简介
============

Linux MUSB 子系统是更大的 Linux USB 子系统的一部分。它为那些不使用通用主机控制器接口（UHCI）或开放式主机控制器接口（OHCI）的嵌入式 USB 设备控制器（UDC）提供支持。
相反，这些嵌入式 UDC 依赖于它们至少部分实现的 USB On-the-Go (OTG) 规范。大多数情况下使用的硅参考设计是 Mentor Graphics Inventra™ 设计中发现的多点 USB 高速双角色控制器 (MUSB HDRC)。
作为自学练习，我为 Ingenic JZ4740 SoC 编写了一个 MUSB 黏合层，该层借鉴了内核源代码树中的许多 MUSB 黏合层。这个层可以在 ``drivers/usb/musb/jz4740.c`` 中找到。在本文档中，我将介绍 ``jz4740.c`` 黏合层的基础知识，解释不同的组成部分以及编写自己的设备黏合层需要做些什么。
.. _musb-basics:

Linux MUSB 基础
=================

为了开始这个话题，请阅读 USB On-the-Go 基础（参见资源），这提供了在硬件级别上 USB OTG 操作的介绍。德克萨斯仪器公司和模拟设备公司的几个维基页面也概述了 Linux 内核 MUSB 配置，尽管重点在于这些公司提供的某些特定设备。
最后，熟悉 USB 规范可能也会有所帮助，可以通过 USB 主页获取，通过编写 USB 设备驱动程序文档（再次参见资源）提供实用示例。
Linux USB 栈是一个分层架构，其中 MUSB 控制器硬件位于最低层。MUSB 控制器驱动程序对 MUSB 控制器硬件进行抽象以供 Linux USB 栈使用::

	  ------------------------
	  |                      | <------- drivers/usb/gadget
	  | Linux USB 核心栈     | <------- drivers/usb/host
	  |                      | <------- drivers/usb/core
	  ------------------------
		     ⬍
	 --------------------------
	 |                        | <------ drivers/usb/musb/musb_gadget.c
	 | MUSB 控制器驱动程序   | <------ drivers/usb/musb/musb_host.c
	 |                        | <------ drivers/usb/musb/musb_core.c
	 --------------------------
		     ⬍
      ---------------------------------
      | MUSB 平台特定驱动程序          |
      |                               | <-- drivers/usb/musb/jz4740.c
      |       即 “黏合层”              |
      ---------------------------------
		     ⬍
      ---------------------------------
      |   MUSB 控制器硬件             |
      ---------------------------------

如上所述，黏合层实际上是位于控制器驱动程序和控制器硬件之间的平台特定代码
就像 Linux USB 驱动程序需要向 Linux USB 子系统注册自己一样，MUSB 黏合层首先需要向 MUSB 控制器驱动程序注册自己。这将使控制器驱动程序了解黏合层支持哪些设备，以及在检测到或释放支持的设备时应调用哪些函数；记住我们这里讨论的是一个嵌入式的控制器芯片，因此没有运行时的插入或移除。
所有这些信息都通过在黏合层定义的 :c:type:`platform_driver` 结构传递给 MUSB 控制器驱动程序，如下所示::

    static struct platform_driver jz4740_driver = {
	.probe      = jz4740_probe,
	.remove     = jz4740_remove,
	.driver     = {
	    .name   = "musb-jz4740",
	},
    };

probe 和 remove 函数指针在匹配的设备被检测到时分别被调用。name 字符串描述了此黏合层支持的设备。在当前情况下，它与在 ``arch/mips/jz4740/platform.c`` 中声明的一个 platform_device 结构相匹配。请注意，我们在这里没有使用设备树绑定。
为了向控制器驱动程序注册自己，黏合层会经历几个步骤，基本上分配控制器硬件资源并初始化一些电路。为此，它需要跟踪在整个过程中使用的信息。这是通过定义一个私有的 ``jz4740_glue`` 结构来完成的::

    struct jz4740_glue {
	struct device           *dev;
	struct platform_device  *musb;
	struct clk      *clk;
    };

dev 和 musb 成员都是设备结构变量。第一个持有关于设备的一般信息，因为它是最基本的设备结构，而后一个持有与设备注册到的子系统更密切相关的信息。clk 变量保持与设备时钟操作相关的信息。
让我们来看看探查函数中的步骤，这些步骤使黏合层向控制器驱动程序注册自身。
为了提高可读性，每个函数将被拆分成逻辑部分，每一部分都像与其他部分独立一样展示。

```c
static int jz4740_probe(struct platform_device *pdev)
{
    struct platform_device      *musb;
    struct jz4740_glue      *glue;
    struct clk                      *clk;
    int             ret;

    glue = devm_kzalloc(&pdev->dev, sizeof(*glue), GFP_KERNEL);
    if (!glue)
        return -ENOMEM;

    musb = platform_device_alloc("musb-hdrc", PLATFORM_DEVID_AUTO);
    if (!musb) {
        dev_err(&pdev->dev, "分配musb设备失败\n");
        return -ENOMEM;
    }

    clk = devm_clk_get(&pdev->dev, "udc");
    if (IS_ERR(clk)) {
        dev_err(&pdev->dev, "获取时钟失败\n");
        ret = PTR_ERR(clk);
        goto err_platform_device_put;
    }

    ret = clk_prepare_enable(clk);
    if (ret) {
        dev_err(&pdev->dev, "启用时钟失败\n");
        goto err_platform_device_put;
    }

    musb->dev.parent        = &pdev->dev;

    glue->dev           = &pdev->dev;
    glue->musb          = musb;
    glue->clk           = clk;

    return 0;

err_platform_device_put:
    platform_device_put(musb);
    return ret;
}
```

`probe`函数的前几行用于分配和赋值`glue`、`musb`和`clk`变量。`GFP_KERNEL`标志（第8行）允许分配过程在等待内存时休眠，因此可以在锁定情况下使用。`PLATFORM_DEVID_AUTO`标志（第12行）允许自动分配和管理设备ID以避免与显式ID发生命名空间冲突。通过`devm_clk_get`（第18行），粘合层分配了时钟——`devm_`前缀表示`clk_get`是受管理的：当设备被释放时，它会自动释放已分配的时钟资源数据，并启用它。
接下来是注册步骤：

```c
static int jz4740_probe(struct platform_device *pdev)
{
    struct musb_hdrc_platform_data  *pdata = &jz4740_musb_platform_data;

    pdata->platform_ops     = &jz4740_musb_ops;

    platform_set_drvdata(pdev, glue);

    ret = platform_device_add_resources(musb, pdev->resource,
            pdev->num_resources);
    if (ret) {
        dev_err(&pdev->dev, "添加资源失败\n");
        goto err_clk_disable;
    }

    ret = platform_device_add_data(musb, pdata, sizeof(*pdata));
    if (ret) {
        dev_err(&pdev->dev, "添加平台数据失败\n");
        goto err_clk_disable;
    }

    return 0;

err_clk_disable:
    clk_disable_unprepare(clk);
err_platform_device_put:
    platform_device_put(musb);
    return ret;
}
```

第一步是通过`platform_set_drvdata`（第7行）将粘合层私有持有的设备数据传递给控制器驱动程序。接下来是通过`platform_device_add_resources`（第9行）传递该点上私有持有的设备资源信息。最后是将特定于平台的数据传递给控制器驱动程序（第16行）。平台数据将在:musb-dev-platform-data:中讨论，但在这里我们关注的是`musb_hdrc_platform_data`结构中的`platform_ops`函数指针（第5行）。此函数指针使MUSB控制器驱动程序知道调用哪个函数来执行设备操作：

```c
static const struct musb_platform_ops jz4740_musb_ops = {
    .init       = jz4740_musb_init,
    .exit       = jz4740_musb_exit,
};
```

这里是最小的情况，其中只调用init和exit函数，当需要时由控制器驱动程序调用。事实上，JZ4740 MUSB控制器是一个基本控制器，缺少其他控制器中的一些功能，否则我们还可以有指向其他几个函数的指针，例如电源管理函数或用于切换OTG和非OTG模式的函数。
在注册过程中，控制器驱动程序实际上调用了init函数：

```c
static int jz4740_musb_init(struct musb *musb)
{
    musb->xceiv = usb_get_phy(USB_PHY_TYPE_USB2);
    if (!musb->xceiv) {
        pr_err("HS UDC: 没有配置收发器\n");
        return -ENODEV;
    }

    /* 硅片未实现ConfigData寄存器
     * 设置dyn_fifo以避免从硬件读取EP配置
     */
    musb->dyn_fifo = true;

    musb->isr = jz4740_musb_interrupt;

    return 0;
}
```

`jz4740_musb_init()`的目标是获取MUSB控制器硬件的收发器驱动程序数据并将其传递给MUSB控制器驱动程序，这是常规做法。收发器是控制器硬件内部负责发送/接收USB数据的电路。
由于它是OSI模型物理层的实现，收发器也称为PHY。
通过`usb_get_phy()`获取`MUSB PHY`驱动程序数据，它返回包含驱动程序实例数据的结构指针。接下来的几条指令（第12行和第14行）作为特例处理和设置IRQ处理使用。特例处理和IRQ处理将在:musb-dev-quirks:和:musb-handling-irqs:中讨论。

```c
static int jz4740_musb_exit(struct musb *musb)
{
    usb_put_phy(musb->xceiv);

    return 0;
}
```

作为init的对应部分，exit函数在控制器硬件本身即将被释放时释放MUSB PHY驱动程序。
再次注意，在这种情况下init和exit相对简单，因为JZ4740控制器硬件的功能集较为基础。在为更复杂的控制器硬件编写musb粘合层时，您可能需要在这两个函数中处理更多的加工任务。
从初始化函数返回后，MUSB控制器驱动程序会跳回到探测函数：

    static int jz4740_probe(struct platform_device *pdev)
    {
	ret = platform_device_add(musb);
	if (ret) {
	    dev_err(&pdev->dev, "failed to register musb device\n");
	    goto err_clk_disable;
	}

	return 0;

    err_clk_disable:
	clk_disable_unprepare(clk);
    err_platform_device_put:
	platform_device_put(musb);
	return ret;
    }

这是设备注册过程的最后一步，在这里胶合层将控制器硬件设备添加到Linux内核设备层次结构中：在这个阶段，所有已知的关于该设备的信息都会传递给Linux USB核心堆栈：

   .. code-block:: c
    :emphasize-lines: 5,6

    static int jz4740_remove(struct platform_device *pdev)
    {
	struct jz4740_glue  *glue = platform_get_drvdata(pdev);

	platform_device_unregister(glue->musb);
	clk_disable_unprepare(glue->clk);

	return 0;
    }

作为探测函数的对应部分，移除函数注销了MUSB控制器硬件（第5行）并禁用了时钟（第6行），允许它被屏蔽。

.. _musb-handling-irqs:

处理IRQs
==========

除了MUSB控制器硬件的基本设置和注册之外，胶合层还负责处理IRQs：

   .. code-block:: c
    :emphasize-lines: 7,9-11,14,24

    static irqreturn_t jz4740_musb_interrupt(int irq, void *__hci)
    {
	unsigned long   flags;
	irqreturn_t     retval = IRQ_NONE;
	struct musb     *musb = __hci;

	spin_lock_irqsave(&musb->lock, flags);

	musb->int_usb = musb_readb(musb->mregs, MUSB_INTRUSB);
	musb->int_tx = musb_readw(musb->mregs, MUSB_INTRTX);
	musb->int_rx = musb_readw(musb->mregs, MUSB_INTRRX);

	/*
	 * 控制器仅用于外设模式，主机模式IRQ位的状态未定义。屏蔽这些位以确保musb驱动核心永远不会看到它们被设置
	 */
	musb->int_usb &= MUSB_INTR_SUSPEND | MUSB_INTR_RESUME |
	    MUSB_INTR_RESET | MUSB_INTR_SOF;

	if (musb->int_usb || musb->int_tx || musb->int_rx)
	    retval = musb_interrupt(musb);

	spin_unlock_irqrestore(&musb->lock, flags);

	return retval;
    }

在这里，胶合层主要需要读取相关的硬件寄存器，并将它们的值传递给控制器驱动程序，后者将处理实际触发IRQ的事件。
中断处理程序的关键部分由 :c:func:`spin_lock_irqsave` 和其对应的 :c:func:`spin_unlock_irqrestore` 函数保护（分别在第7行和第24行），这可以防止中断处理程序代码同时被两个不同的线程执行。
然后读取相关的中断寄存器（第9到11行）：

-  ``MUSB_INTRUSB``: 指示当前哪些USB中断处于活动状态，

-  ``MUSB_INTRTX``: 指示当前哪些TX端点的中断处于活动状态，

-  ``MUSB_INTRRX``: 指示当前哪些RX端点的中断处于活动状态
值得注意的是，:c:func:`musb_readb` 用于读取最多8位的寄存器，而 :c:func:`musb_readw` 允许我们读取最多16位的寄存器。根据你的设备寄存器大小，还有其他可用的函数。更多信息请参阅 ``musb_io.h``
第18行的指令是JZ4740 USB设备控制器特有的另一个特性，稍后将在 :ref:`musb-dev-quirks` 中讨论。
胶合层仍然需要注册IRQ处理程序。回想init函数中的第14行指令：

    static int jz4740_musb_init(struct musb *musb)
    {
	musb->isr = jz4740_musb_interrupt;

	return 0;
    }

这条指令设置了一个指向胶合层IRQ处理函数的指针，以便当控制器硬件发出IRQ时调用此处理函数。现在中断处理程序已经实现并注册。

.. _musb-dev-platform-data:

设备平台数据
==================

为了编写一个MUSB胶合层，你需要有一些描述你的控制器硬件能力的数据，这被称为平台数据。
平台数据特定于你的硬件，尽管它可以覆盖广泛的设备，并且通常可以在“arch/”目录下的某个地方找到，具体取决于你的设备架构。
例如，JZ4740 SoC的平台数据位于 ``arch/mips/jz4740/platform.c`` 中。在 ``platform.c`` 文件中，通过一系列结构来描述每个JZ4740 SoC设备。
下面是`arch/mips/jz4740/platform.c`中关于USB设备控制器(UDC)的部分：

   .. code-block:: c
    :emphasize-lines: 2,7,14-17,21,22,25,26,28,29

    /* USB 设备控制器 */
    struct platform_device jz4740_udc_xceiv_device = {
	.name = "usb_phy_gen_xceiv",
	.id   = 0,
    };

    static struct resource jz4740_udc_resources[] = {
	[0] = {
	    .start = JZ4740_UDC_BASE_ADDR,
	    .end   = JZ4740_UDC_BASE_ADDR + 0x10000 - 1,
	    .flags = IORESOURCE_MEM,
	},
	[1] = {
	    .start = JZ4740_IRQ_UDC,
	    .end   = JZ4740_IRQ_UDC,
	    .flags = IORESOURCE_IRQ,
	    .name  = "mc",
	},
    };

    struct platform_device jz4740_udc_device = {
	.name = "musb-jz4740",
	.id   = -1,
	.dev  = {
	    .dma_mask          = &jz4740_udc_device.dev.coherent_dma_mask,
	    .coherent_dma_mask = DMA_BIT_MASK(32),
	},
	.num_resources = ARRAY_SIZE(jz4740_udc_resources),
	.resource      = jz4740_udc_resources,
    };

`jz4740_udc_xceiv_device`平台设备结构（第2行）描述了UDC收发器，包括名称和ID号。
在撰写本文时，请注意`usb_phy_gen_xceiv`是所有与参考USB IP内置或独立的收发器所使用的特定名称，并且不需要任何PHY编程。要在内核配置中使用相应的收发器驱动程序，您需要设置`CONFIG_NOP_USB_XCEIV=y`。ID字段可以设置为-1（等同于`PLATFORM_DEVID_NONE`），-2（等同于`PLATFORM_DEVID_AUTO`），或者从0开始，如果您想要一个特定的ID号，则用于此类别的第一个设备。
`jz4740_udc_resources`资源结构（第7行）定义了UDC寄存器基地址。
第一个数组（第9至11行）定义了UDC寄存器基内存地址：`start`指向第一个寄存器内存地址，`end`指向最后一个寄存器内存地址，而`flags`成员定义了我们处理的资源类型。因此，使用`IORESOURCE_MEM`来定义寄存器内存地址。第二个数组（第14至17行）定义了UDC中断寄存器地址。由于JZ4740 UDC只有一个可用的中断寄存器，因此`start`和`end`指向同一个地址。`IORESOURCE_IRQ`标志表明我们在处理中断资源，而名称`mc`实际上硬编码在MUSB核心中，以便控制器驱动程序通过查询其名称来获取此中断资源。
最后，`jz4740_udc_device`平台设备结构（第21行）描述了UDC本身。
`musb-jz4740`名称（第22行）定义了用于此设备的MUSB驱动程序；请记住，这是我们在`musb-basics`中的`jz4740_driver`平台驱动程序结构中所使用的名称。
ID字段（第23行）被设置为-1（等同于`PLATFORM_DEVID_NONE`），因为我们不需要为此设备分配ID：MUSB控制器驱动程序已经在`musb-basics`中设置为自动分配ID。在`dev`字段中，我们关心的是DMA相关的信息。`dma_mask`字段（第25行）定义了将要使用的DMA掩码宽度，而`coherent_dma_mask`（第26行）具有相同的目的，但针对`alloc_coherent` DMA映射：在这两种情况下，我们都使用32位掩码。
然后`resource`字段（第29行）仅仅是之前定义的资源结构的指针，而`num_resources`字段（第28行）跟踪资源结构中定义的数组数量（在此例中有两个资源数组被定义）。
有了这个在`arch/`级别的UDC平台数据的快速概述后，让我们回到`drivers/usb/musb/jz4740.c`中的MUSB胶水层特有的平台数据：

   .. code-block:: c
    :emphasize-lines: 3,5,7-9,11

    static struct musb_hdrc_config jz4740_musb_config = {
	/* 硬件未实现USB OTG功能。 */
	.multipoint = 0,
	/* 扫描的最大EP数，驱动程序将决定哪些EP可以使用。 */
	.num_eps    = 4,
	/* 从表中配置EP所需的RAM位数 */
	.ram_bits   = 9,
	.fifo_cfg = jz4740_musb_fifo_cfg,
	.fifo_cfg_size = ARRAY_SIZE(jz4740_musb_fifo_cfg),
    };

    static struct musb_hdrc_platform_data jz4740_musb_platform_data = {
	.mode   = MUSB_PERIPHERAL,
	.config = &jz4740_musb_config,
    };

首先，胶水层配置了一些与控制器硬件特性的控制器驱动程序操作相关的方面。这是通过`jz4740_musb_config` :c:type:`musb_hdrc_config`结构完成的。
定义控制器硬件的OTG能力，`multipoint`成员（第3行）被设置为0（等同于false），因为JZ4740 UDC不支持OTG。然后`num_eps`（第5行）定义了控制器硬件的USB端点数量，包括端点0：这里我们有3个端点+端点0。接下来是`ram_bits`（第7行），它是MUSB控制器硬件的RAM地址总线宽度。当控制器驱动程序无法通过读取相关控制器硬件寄存器自动配置端点时，需要这些信息。这个问题将在我们讨论设备怪癖时进行讨论，在:musb-dev-quirks:。最后两个字段（第8和9行）也与设备怪癖有关：`fifo_cfg`指向USB端点配置表，而`fifo_cfg_size`跟踪该配置表中的条目数量。稍后在:musb-dev-quirks:中会有更多相关内容。
然后，此配置被嵌入到 `jz4740_musb_platform_data` 中的
:c:type:`musb_hdrc_platform_data` 结构体（第11行）：`config` 是指向配置结构本身的指针，而 `mode` 告诉控制器驱动程序
控制器硬件是否只能作为 `MUSB_HOST`、只能作为 `MUSB_PERIPHERAL` 或者是双模式的 `MUSB_OTG`
请记住，`jz4740_musb_platform_data` 然后被用来传递平台数据信息，如我们在
:ref:`musb-basics` 中看到的探测函数中那样。
.. _musb-dev-quirks:

设备特性
=============

除了完成特定于您设备的平台数据之外，您可能还需要在胶水层编写一些代码来解决某些特定于设备的限制。这些特性可能是由于一些硬件错误造成的，
或者仅仅是USB On-the-Go规范实现不完整的结果。
JZ4740 UDC就表现出这样的特性，下面我们将讨论其中的一些特性以增加理解，尽管您正在处理的控制器硬件上可能找不到这些特性。
首先让我们回到初始化函数：

   .. code-block:: c
    :emphasize-lines: 12

    static int jz4740_musb_init(struct musb *musb)
    {
	musb->xceiv = usb_get_phy(USB_PHY_TYPE_USB2);
	if (!musc->xceiv) {
	    pr_err("HS UDC: no transceiver configured\n");
	    return -ENODEV;
	}

	/* 硅片没有实现ConfigData寄存器
	 * 设置dyn_fifo以避免从硬件读取EP配置
	 */
	musb->dyn_fifo = true;

	musb->isr = jz4740_musb_interrupt;

	return 0;
    }

第12行的指令帮助MUSB控制器驱动程序绕过控制器硬件缺少用于USB端点配置的寄存器的事实。
没有这些寄存器，控制器驱动程序无法从硬件读取端点配置，因此我们使用第12行的指令
来绕过从硅片读取配置，并依赖一个硬编码表来描述端点配置而不是从硬件读取配置：
    
    static struct musb_fifo_cfg jz4740_musb_fifo_cfg[] = {
	{ .hw_ep_num = 1, .style = FIFO_TX, .maxpacket = 512, },
	{ .hw_ep_num = 1, .style = FIFO_RX, .maxpacket = 512, },
	{ .hw_ep_num = 2, .style = FIFO_TX, .maxpacket = 64, },
    };

从上面的配置表可以看出，每个端点都由三个字段描述：`hw_ep_num` 是端点编号，`style` 是它的方向（`FIFO_TX` 对于控制器驱动程序发送数据包到控制器硬件，或 `FIFO_RX` 从硬件接收数据包），`maxpacket` 定义了可以通过该端点传输的每个数据包的最大尺寸。从表中可以知道，端点1可用于一次发送和接收512字节的USB数据包（实际上这是一个批量输入/输出端点），端点2可用于一次发送64字节的数据包（实际上是一个中断端点）。
请注意这里没有关于端点0的信息：这个端点在每种硅设计中都有默认实现，根据USB规范有预定义的配置。有关更多端点配置表的例子，请参见 `musb_core.c`。
现在我们回到中断处理函数：

   .. code-block:: c
    :emphasize-lines: 18-19

    static irqreturn_t jz4740_musb_interrupt(int irq, void *__hci)
    {
	unsigned long   flags;
	irqreturn_t     retval = IRQ_NONE;
	struct musb     *musb = __hci;

	spin_lock_irqsave(&musb->lock, flags);

	musb->int_usb = musb_readb(musb->mregs, MUSB_INTRUSB);
	musc->int_tx = musb_readw(musb->mregs, MUSB_INTRTX);
	musc->int_rx = musb_readw(musb->mregs, MUSB_INTRRX);

	/*
	 * 控制器仅支持gadget模式，主机模式中断位的状态未定义。
	 * 将其屏蔽以确保musb驱动核心永远不会看到这些位设置
	 */
	musc->int_usb &= MUSB_INTR_SUSPEND | MUSB_INTR_RESUME |
	    MUSB_INTR_RESET | MUSB_INTR_SOF;

	if (musc->int_usb || musc->int_tx || musc->int_rx)
	    retval = musb_interrupt(musc);

	spin_unlock_irqrestore(&musc->lock, flags);

	return retval;
    }

上面第18行的指令是控制器驱动程序绕过 `MUSB_INTRUSB` 寄存器中用于USB主机模式操作的一些中断位缺失的方式，因此它们处于未定义的硬件状态，因为此MUSB控制器硬件仅用于外设模式。因此，胶水层通过与 `MUSB_INTRUSB` 的值进行逻辑与操作来屏蔽这些缺失的位，以避免寄生中断。
这些只是JZ4740 USB设备控制器中发现的一些奇特特性。其他一些问题已在MUSB核心中直接解决，因为这些修复足够通用，可以为其他控制器硬件更好地处理这些问题。

结论
=====

编写Linux MUSB粘合层应该是一项更容易完成的任务，正如本文档试图展示的那样，解释了这项练习中的细节。鉴于JZ4740 USB设备控制器相对简单，我希望其粘合层能够为好奇的读者提供一个良好的示例。结合现有的MUSB粘合层使用本文档，应该能提供足够的指导来开始工作；如果遇到任何棘手的问题，linux-usb邮件列表存档是另一个有用的资源。

致谢
=====

非常感谢Lars-Peter Clausen和Maarten ter Huurne在我编写JZ4740粘合层期间回答我的问题，并帮助我使代码处于良好状态。
我也要感谢Qi-Hardware社区的全体成员，他们热情地提供了指导和支持。

资源
=====

USB主页: https://www.usb.org

linux-usb邮件列表归档: https://marc.info/?l=linux-usb

USB On-the-Go基础: https://www.maximintegrated.com/app-notes/index.mvp/id/1822

:ref:`编写USB设备驱动程序 <writing-usb-driver>`

德州仪器USB配置维基页面: https://web.archive.org/web/20201215135015/http://processors.wiki.ti.com/index.php/Usbgeneralpage
