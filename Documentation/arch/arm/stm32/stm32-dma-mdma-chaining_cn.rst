### SPDX 许可证标识符：GPL-2.0

=======================
STM32 DMA-MDMA 链接
=======================

#### 引言

  本文档描述了 STM32 DMA-MDMA 链接功能。但在进一步介绍之前，我们先来了解一下所涉及的外设。
为了将数据传输任务从 CPU 上卸载下来，STM32 微处理器（MPU）集成了直接内存访问控制器（DMA）。
STM32MP1 系统芯片（SoC）同时集成了 STM32 DMA 和 STM32 MDMA 控制器。STM32 DMA 请求路由功能通过 DMA 请求多路复用器（STM32 DMAMUX）得到了增强。

**STM32 DMAMUX**

  STM32 DMAMUX 可以将任何来自特定外设的 DMA 请求路由到任意一个 STM32 DMA 控制器（STM32MP1 包含两个 STM32 DMA 控制器）的通道上。
**STM32 DMA**

  STM32 DMA 主要用于为不同的外设实现中心数据缓冲存储（通常位于系统 SRAM 中）。它可以访问外部 RAM，但不具备生成方便的突发传输的能力，因此无法确保最佳的 AXI 性能。
**STM32 MDMA**

  STM32 MDMA（主 DMA）主要用于管理无需 CPU 干预的 RAM 数据缓冲之间的直接数据传输。它也可以在分层结构中使用，其中 STM32 DMA 作为第一级数据缓冲接口供 AHB 外设使用，而 STM32 MDMA 则作为第二级 DMA 提供更好的性能。作为 AXI/AHB 主控器，STM32 MDMA 可以控制 AXI/AHB 总线。

#### 原理

  STM32 DMA-MDMA 链接功能基于 STM32 DMA 和 STM32 MDMA 控制器的优势。
STM32 DMA 具有循环双缓冲模式（DBM）。在每次事务结束时（当 DMA 数据计数器 - DMA_SxNDTR - 达到 0 时），内存指针（通过 DMA_SxSM0AR 和 DMA_SxM1AR 配置）会进行交换，并且 DMA 数据计数器会自动重装。这使得软件或 STM32 MDMA 可以处理一个内存区域，而另一个内存区域则正在被 STM32 DMA 传输所填充/使用。
利用 STM32 MDMA 的链表模式，单个请求可以启动一系列节点的数据数组转移，直到该通道的链表指针为空。最后一个节点的通道传输完成即为整个传输的结束，除非首尾节点互相链接，在这种情况下，链表将循环形成一个循环 MDMA 转移。
STM32 MDMA 与 STM32 DMA 之间有直接连接。这使外设之间的自主通信和同步成为可能，从而节省了 CPU 资源并减轻了总线拥堵。STM32 DMA 通道的传输完成信号可以触发 STM32 MDMA 的传输。STM32 MDMA 可以通过写入其中断清除寄存器（其地址存储在 MDMA_CxMAR 中，位掩码在 MDMA_CxMDR 中）来清除由 STM32 DMA 产生的请求。
下面是提供的英文内容翻译成中文：

.. table:: STM32 MDMA 互连表，与 STM32 DMA 相关

    +--------------+----------------+-----------+------------+
    | STM32 DMAMUX | STM32 DMA      | STM32 DMA | STM32 MDMA |
    | 通道         | 通道           | 转移完成  | 请求       |
    |              |                | 信号      |            |
    +==============+================+===========+============+
    | 通道 *0*     | DMA1 通道 0    | dma1_tcf0 | *0x00*     |
    +--------------+----------------+-----------+------------+
    | 通道 *1*     | DMA1 通道 1    | dma1_tcf1 | *0x01*     |
    +--------------+----------------+-----------+------------+
    | 通道 *2*     | DMA1 通道 2    | dma1_tcf2 | *0x02*     |
    +--------------+----------------+-----------+------------+
    | 通道 *3*     | DMA1 通道 3    | dma1_tcf3 | *0x03*     |
    +--------------+----------------+-----------+------------+
    | 通道 *4*     | DMA1 通道 4    | dma1_tcf4 | *0x04*     |
    +--------------+----------------+-----------+------------+
    | 通道 *5*     | DMA1 通道 5    | dma1_tcf5 | *0x05*     |
    +--------------+----------------+-----------+------------+
    | 通道 *6*     | DMA1 通道 6    | dma1_tcf6 | *0x06*     |
    +--------------+----------------+-----------+------------+
    | 通道 *7*     | DMA1 通道 7    | dma1_tcf7 | *0x07*     |
    +--------------+----------------+-----------+------------+
    | 通道 *8*     | DMA2 通道 0    | dma2_tcf0 | *0x08*     |
    +--------------+----------------+-----------+------------+
    | 通道 *9*     | DMA2 通道 1    | dma2_tcf1 | *0x09*     |
    +--------------+----------------+-----------+------------+
    | 通道 *10*    | DMA2 通道 2    | dma2_tcf2 | *0x0A*     |
    +--------------+----------------+-----------+------------+
    | 通道 *11*    | DMA2 通道 3    | dma2_tcf3 | *0x0B*     |
    +--------------+----------------+-----------+------------+
    | 通道 *12*    | DMA2 通道 4    | dma2_tcf4 | *0x0C*     |
    +--------------+----------------+-----------+------------+
    | 通道 *13*    | DMA2 通道 5    | dma2_tcf5 | *0x0D*     |
    +--------------+----------------+-----------+------------+
    | 通道 *14*    | DMA2 通道 6    | dma2_tcf6 | *0x0E*     |
    +--------------+----------------+-----------+------------+
    | 通道 *15*    | DMA2 通道 7    | dma2_tcf7 | *0x0F*     |
    +--------------+----------------+-----------+------------+

STM32 DMA-MDMA 链接特性使用 SRAM 缓冲区。STM32MP1 系统级芯片中嵌入了三种不同大小的快速访问静态内部 RAM，用于数据存储。
由于 STM32 DMA 的历史遗留问题（在微控制器中），STM32 DMA 在 DDR 上的表现较差，而在 SRAM 上则是最优的。因此，在 STM32 DMA 和 STM32 MDMA 之间使用 SRAM 缓冲区。该缓冲区被分为两个相等的部分，并且 STM32 DMA 使用其中一个部分，而 STM32 MDMA 同时使用另一个部分。
::

                    dma[1:2]-tcf[0:7]
                   .----------------
____________ '    _________     V____________
    | STM32 DMA  |    /  __|>_  \    | STM32 MDMA |
    |------------|   |  /     \  |   |------------|
    | DMA_SxM0AR |<=>| | SRAM  | |<=>| []-[]...[] |
    | DMA_SxM1AR |   |  \_____/  |   |            |
    |____________|    \___<|____/    |____________|

STM32 DMA-MDMA 链接使用 (struct dma_slave_config).peripheral_config 来交换配置 MDMA 所需的参数。这些参数被收集到一个包含三个值的 u32 数组中：

  * STM32 MDMA 请求（实际上是 DMAMUX 通道 ID），
  * 用于清除转移完成中断标志的 STM32 DMA 寄存器地址，
  * STM32 DMA 通道的转移完成中断标志掩码
设备树更新以支持 STM32 DMA-MDMA 链接
-------------------------------------------------------

  **1. 分配 SRAM 缓冲区**

    SRAM 设备树节点定义在 SoC 设备树中。你可以在你的板载设备树中引用它来定义你的 SRAM 池。
::

          &sram {
                  my_foo_device_dma_pool: dma-sram@0 {
                          reg = <0x0 0x1000>;
                  };
          };

    注意起始索引，如果有其他 SRAM 消费者的话
战略地定义你的池大小：为了优化链接，STM32 DMA 和 STM32 MDMA 应当能同时在 SRAM 的每个缓冲区上工作
如果 SRAM 周期大于预期的 DMA 传输，则 STM32 DMA 和 STM32 MDMA 将会顺序而非同时工作。这不是功能性问题，但不是最优的选择
不要忘记在你的设备节点中引用你的 SRAM 池。你需要定义一个新的属性
::

          &my_foo_device {
                  ..
### 翻译成中文：

#### 1. 分配 SRAM 池

    在您的设备树节点中定义一个 SRAM 池，并将其与您的设备关联起来：
    ```
    my_dma_pool = &my_foo_device_dma_pool;
    };
    
    然后在您的 foo 驱动程序中获取这个 SRAM 池并分配您的 SRAM 缓冲区。

#### 2. 分配一个 STM32 DMA 通道和一个 STM32 MDMA 通道

    您需要在设备树节点中定义一个额外的通道，除了您已经为“经典”DMA 操作定义的一个之外。
    这个新通道必须从 STM32 MDMA 通道中取出，因此要使用的 DMA 控制器的 phandle 应该是 MDMA 控制器的 phandle。
    ```
          &my_foo_device {
                  [...]
                  my_dma_pool = &my_foo_device_dma_pool;
                  dmas = <&dmamux1 ...>,                // STM32 DMA 通道
                         <&mdma1 0 0x3 0x1200000a 0 0>; // + STM32 MDMA 通道
          };
    ```

    关于 STM32 MDMA 绑定：

    1. 请求行号：无论这里设置什么值，它都会被 MDMA 驱动程序覆盖，使用通过 (struct dma_slave_config).peripheral_config 传递的 STM32 DMAMUX 通道 ID。

    2. 优先级级别：选择非常高（0x3），这样您的通道将在请求仲裁时优先于其他通道。

    3. 一个 32 位掩码指定 DMA 通道配置：源地址和目标地址递增，块传输每次 128 字节。

    4. 一个 32 位值指定用于确认请求的寄存器：这将被 MDMA 驱动程序覆盖，使用通过 (struct dma_slave_config).peripheral_config 传递的 DMA 通道中断标志清除寄存器地址。

    5. 一个 32 位掩码指定用于确认请求的值：这将被 MDMA 驱动程序覆盖，使用通过 (struct dma_slave_config).peripheral_config 传递的 DMA 通道传输完成标志。

### STM32 DMA-MDMA 链接支持的驱动更新

#### 0. (可选) 如果使用 dmaengine_prep_slave_sg()，重构原始 sg_table

    如果使用 dmaengine_prep_slave_sg()，则不能直接使用原始 sg_table。需要从原始 sg_table 创建两个新的 sg_table。一个用于 STM32 DMA 传输（其中内存地址现在指向 SRAM 缓冲区而不是 DDR 缓冲区），另一个用于 STM32 MDMA 传输（其中内存地址指向 DDR 缓冲区）。
    新的 sg_list 项必须适合 SRAM 周期长度。以下是一个 DMA_DEV_TO_MEM 的示例：
    ```
      /*
        * 假设 sgl 和 nents 分别是初始的 scatterlist 和其长度
        * 假设 sram_dma_buf 和 sram_period 分别是从池中为 DMA 使用分配的内存和周期长度，
        * 其大小是 sram_buf 大小的一半
      */
      struct sg_table new_dma_sgt, new_mdma_sgt;
      struct scatterlist *s, *_sgl;
      dma_addr_t ddr_dma_buf;
      u32 new_nents = 0, len;
      int i;

      /* 计算所需的条目数 */
      for_each_sg(sgl, s, nents, i)
              if (sg_dma_len(s) > sram_period)
                      new_nents += DIV_ROUND_UP(sg_dma_len(s), sram_period);
              else
                      new_nents++;

      /* 为 STM32 DMA 通道创建 sg_table */
      ret = sg_alloc_table(&new_dma_sgt, new_nents, GFP_ATOMIC);
      if (ret)
              dev_err(dev, "DMA sg table alloc failed\n");

      for_each_sg(new_dma_sgt.sgl, s, new_dma_sgt.nents, i) {
              _sgl = sgl;
              sg_dma_len(s) = min(sg_dma_len(_sgl), sram_period);
              /* 目标是 sram_buf 的开始部分 */
              s->dma_address = sram_buf;
              /*
                * 对于 sg_list 中项的奇数索引，目标是 sram_buf 的第二部分
                */
              if (i & 1)
                      s->dma_address += sram_period;
      }

      /* 为 STM32 MDMA 通道创建 sg_table */
      ret = sg_alloc_table(&new_mdma_sgt, new_nents, GFP_ATOMIC);
      if (ret)
              dev_err(dev, "MDMA sg_table alloc failed\n");

      _sgl = sgl;
      len = sg_dma_len(sgl);
      ddr_dma_buf = sg_dma_address(sgl);
      for_each_sg(mdma_sgt.sgl, s, mdma_sgt.nents, i) {
              size_t bytes = min_t(size_t, len, sram_period);

              sg_dma_len(s) = bytes;
              sg_dma_address(s) = ddr_dma_buf;
              len -= bytes;

              if (!len && sg_next(_sgl)) {
                      _sgl = sg_next(_sgl);
                      len = sg_dma_len(_sgl);
                      ddr_dma_buf = sg_dma_address(_sgl);
              } else {
                      ddr_dma_buf += bytes;
              }
      }

    不要在使用 dmaengine_prep_slave_sg() 获取描述符之后忘记释放这些新的 sg_table。

#### 1. 设置控制器特定参数

    首先，使用 dmaengine_slave_config() 并提供一个 struct dma_slave_config 来配置 STM32 DMA 通道。您只需关注 DMA 地址，根据传输方向，内存地址应指向您的 SRAM 缓冲区，并设置 (struct dma_slave_config).peripheral_size != 0。
    STM32 DMA 驱动程序会检查 (struct dma_slave_config).peripheral_size 来确定是否使用了链路。如果使用了链路，那么 STM32 DMA 驱动程序会在 (struct dma_slave_config).peripheral_config 中填充一个包含三个 u32 的数组：第一个包含 STM32 DMAMUX 通道 ID，第二个包含通道中断标志清除寄存器地址，第三个包含通道传输完成标志掩码。
    然后，使用 dmaengine_slave_config 和另一个 struct dma_slave_config 来配置 STM32 MDMA 通道。注意 DMA 地址，根据传输方向，设备地址应指向您的 SRAM 缓冲区，而内存地址应指向原本用于“经典”DMA 操作的缓冲区。使用之前由 STM32 DMA 驱动程序更新的 (struct dma_slave_config).peripheral_size 和 .peripheral_config 来设置配置 STM32 MDMA 通道的 struct dma_slave_config 的 .peripheral_size 和 .peripheral_config。
下面是给定代码段的中文翻译：

### 1. 配置STM32 DMA和MDMA通道

```c
struct dma_slave_config dma_conf;
struct dma_slave_config mdma_conf;

memset(&dma_conf, 0, sizeof(dma_conf));
// [...]
dma_conf.direction = DMA_DEV_TO_MEM;
dma_conf.dst_addr = sram_dma_buf;        // SRAM 缓冲区
dma_conf.peripheral_size = 1;            // peripheral_size != 0 => 链接

dmaengine_slave_config(dma_chan, &dma_conf);

memset(&mdma_conf, 0, sizeof(mdma_conf));
mdma_conf.direction = DMA_DEV_TO_MEM;
mdma_conf.src_addr = sram_dma_buf;       // SRAM 缓冲区
mdma_conf.dst_addr = rx_dma_buf;         // 原始内存缓冲区
mdma_conf.peripheral_size = dma_conf.peripheral_size; // <- dma_conf
mdma_conf.peripheral_config = dma_conf.peripheral_config; // <- dma_conf

dmaengine_slave_config(mdma_chan, &mdma_conf);
```

### 2. 获取STM32 DMA通道事务描述符

    与获取“经典”DMA操作的描述符相同的方式，你只需要替换原始的sg_list（在使用`dmaengine_prep_slave_sg()`的情况下）为使用SRAM缓冲区的新sg_list，或者替换原始缓冲区地址、长度和周期（在使用`dmaengine_prep_dma_cyclic()`的情况下）为新的SRAM缓冲区。

### 3. 获取STM32 MDMA通道事务描述符

    如果你之前已经获取了STM32 DMA的描述符，则对于STM32 MDMA：
    * 如果使用的是`dmaengine_prep_slave_sg()`，则继续使用`dmaengine_prep_slave_sg()`；
    * 如果使用的是`dmaengine_prep_dma_cyclic()`，则继续使用`dmaengine_prep_dma_cyclic()`。
使用使用SRAM缓冲区的新的sg_list（在`dmaengine_prep_slave_sg()`的情况下），或者根据传输方向，使用原始DDR缓冲区（在`DMA_DEV_TO_MEM`的情况下）或SRAM缓冲区（在`DMA_MEM_TO_DEV`的情况下）。源地址应通过`dmaengine_slave_config()`预先设置。

### 4. 提交两个事务

    在提交事务前，你可能需要定义在哪个描述符上希望回调函数在传输结束时（`dmaengine_prep_slave_sg()`）或周期结束时（`dmaengine_prep_dma_cyclic()`）被调用。
根据方向，将回调函数设置在完成整个传输的描述符上：
    * `DMA_DEV_TO_MEM`: 将回调函数设置在“MDMA”描述符上
    * `DMA_MEM_TO_DEV`: 将回调函数设置在“DMA”描述符上
然后，无论顺序如何，使用`dmaengine_tx_submit()`提交描述符。

### 5. 发起挂起请求（并等待回调通知）

  由于STM32 MDMA通道的传输由STM32 DMA触发，因此必须先发起STM32 MDMA通道再发起STM32 DMA通道。
如果有回调函数，它将在整个传输结束或周期完成后被调用。
不要忘记终止两个通道。STM32 DMA通道配置为循环双缓冲模式，因此不会被硬件自动禁用，你需要终止它。STM32 MDMA通道在sg传输的情况下会被硬件停止，但在循环传输的情况下不会。你可以无论何种类型的传输都终止它。

### STM32 DMA-MDMA链接中的特殊案例：DMA_MEM_TO_DEV

  STM32 DMA-MDMA链接中的`DMA_MEM_TO_DEV`是一个特殊情况。确实，STM32 MDMA向SRAM缓冲区提供DDR数据，而STM32 DMA从SRAM缓冲区读取数据。因此，在STM32 DMA开始读取时，一些数据（第一个周期）需要复制到SRAM缓冲区中。
一种技巧是暂停STM32 DMA通道（这将引发一个传输完成信号，触发STM32 MDMA通道），但STM32 DMA读取的第一个数据可能是“错误”的。正确的方法是使用`dmaengine_prep_dma_memcpy()`准备第一个SRAM周期。然后应该从sg或循环传输中“移除”这个第一个周期。
由于这种复杂性，建议使用STM32的DMA-MDMA级联功能进行DMA_DEV_TO_MEM操作，并保留"经典"的DMA用法来进行DMA_MEM_TO_DEV操作，除非你不怕面对这些复杂性。

资源
------

应用笔记、数据手册和参考手册可以在ST官网（STM32MP1_）上找到。
特别关注三篇应用笔记（AN5224_、AN4031_和AN5001_），它们分别涉及STM32 DMAMUX、STM32 DMA和STM32 MDMA的内容。
.. _STM32MP1: https://www.st.com/en/microcontrollers-microprocessors/stm32mp1-series.html
.. _AN5224: https://www.st.com/resource/en/application_note/an5224-stm32-dmamux-the-dma-request-router-stmicroelectronics.pdf
.. _AN4031: https://www.st.com/resource/en/application_note/dm00046011-using-the-stm32f2-stm32f4-and-stm32f7-series-dma-controller-stmicroelectronics.pdf
.. _AN5001: https://www.st.com/resource/en/application_note/an5001-stm32cube-expansion-package-for-stm32h7-series-mdma-stmicroelectronics.pdf

作者:

- Amélie Delaunay <amelie.delaunay@foss.st.com>
