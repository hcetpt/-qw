驱动程序变更
=============

此文件详细介绍了影响PCMCIA卡驱动程序作者的2.6版本中的变更：

* pcmcia_loop_config() 和自动配置（自2.6.36起）
   如果`struct pcmcia_device *p_dev->config_flags`相应设置，
   pcmcia_loop_config() 现在会自动设置某些配置值，
   尽管驱动程序仍可在回调函数中覆盖这些设置。
   当前提供的自动配置选项包括：
   
   - CONF_AUTO_CHECK_VCC：检查匹配的Vcc
   - CONF_AUTO_SET_VPP：设置Vpp
   - CONF_AUTO_AUDIO：如需，自动启用音频线路
   - CONF_AUTO_SET_IO：设置ioport资源（->resource[0,1]）
   - CONF_AUTO_SET_IOMEM：设置第一个iomem资源（->resource[2]）

* pcmcia_request_configuration -> pcmcia_enable_device（自2.6.36起）
   pcmcia_request_configuration() 已重命名为pcmcia_enable_device()，
   因为它与pcmcia_disable_device()相对应。配置设置现在存储在struct pcmcia_device中，
   例如在字段config_flags、config_index、config_base和vpp中。

* pcmcia_request_window变更（自2.6.36起）
   驱动程序现在被要求填充`struct pcmcia_device *p_dev->resource[2,3,4,5]`
   以支持最多四个ioport范围，而不是win_req_t。调用pcmcia_request_window()之后，
   在那里找到的区域将被预留并可立即使用——直到调用pcmcia_release_window()。

* pcmcia_request_io变更（自2.6.36起）
   驱动程序现在被要求填充`struct pcmcia_device *p_dev->resource[0,1]`
   以支持最多两个ioport范围，而不是io_req_t。调用pcmcia_request_io()之后，
   在那里找到的端口将被预留，在调用pcmcia_request_configuration()之后可使用。

* 不再有dev_info_t，不再有cs_types.h（自2.6.36起）
   dev_info_t和其他一些类型定义已被移除。PCMCIA设备驱动程序中不再使用它们。
   同时，请勿包含pcmcia/cs_types.h，因为该文件已不存在。

* 不再有dev_node_t（自2.6.35起）
   不再需要填充“dev_node_t”结构体。

* 新的IRQ请求规则（自2.6.35起）
   驱动程序现在可以选择：
   
   - 直接调用request_irq/free_irq。使用来自`*p_dev->irq`的IRQ。
   - 使用pcmcia_request_irq(p_dev, handler_t)，PCMCIA核心将在调用pcmcia_disable_device()或设备弹出时自动清理。

* 不再有cs_error / CS_CHECK / CONFIG_PCMCIA_DEBUG（自2.6.33起）
   请改用Linux风格的返回值检查，并在必要时使用“dev_dbg()”或“pr_debug()”调试信息，
   而不是cs_error()回调或CS_CHECK()宏。

* 新的CIS元组访问（自2.6.33起）
   驱动程序应当使用“pcmcia_get_tuple()”，如果它只对一个（原始）元组感兴趣；
   或者使用“pcmcia_loop_tuple()”，如果它对某一类型的全部元组感兴趣。
   为了从CISTPL_FUNCE解码MAC地址，添加了一个新的辅助函数“pcmcia_get_mac_from_cis()”。

* 新的配置循环帮助函数（自2.6.28起）
   通过调用pcmcia_loop_config()，驱动程序可以遍历所有可用的配置选项。
   在驱动程序的probe()阶段，大多数情况下不需要直接使用pcmcia_get_{first,next}_tuple、
   pcmcia_get_tuple_data和pcmcia_parse_tuple。
* 新版本辅助功能（自2.6.17起）
   现在不再需要调用 pcmcia_release_{configuration,io,irq,win}，只需调用 pcmcia_disable_device 即可。由于没有有效的理由继续调用 pcmcia_release_io 和 pcmcia_release_irq，因此它们的导出已被移除。

* 统一 detach 和 REMOVAL 事件代码，以及 attach 和 INSERTION 代码（自2.6.16起）:

       void (*remove)          (struct pcmcia_device *dev);
       int (*probe)            (struct pcmcia_device *dev);

* 将 suspend、resume 和 reset 从事件处理器中移出（自2.6.16起）:

       int (*suspend)          (struct pcmcia_device *dev);
       int (*resume)           (struct pcmcia_device *dev);

  应在 struct pcmcia_driver 中初始化，并处理 (SUSPEND == RESET_PHYSICAL) 和 (RESUME == CARD_RESET) 事件。

* 在 struct pcmcia_driver 中初始化事件处理器（自2.6.13起）
   事件处理器会收到所有事件的通知，并必须作为驱动程序中的 event() 回调进行初始化。

* 不再使用 pcmcia/version.h（自2.6.13起）
   此文件最终将被移除。

* 内核中的设备<->驱动匹配（自2.6.13起）
   PCMCIA 设备及其正确的驱动程序现在可以在内核空间中进行匹配。详情请参见 'devicetable.txt'。

* 设备模型集成（自2.6.11起）
   一个 struct pcmcia_device 会注册到设备模型核心中，并可以使用 handle_to_dev(client_handle_t * handle) 来使用（例如用于 SET_NETDEV_DEV）。

* 将内部 I/O 端口地址转换为 unsigned int（自2.6.11起）
   在 PCMCIA 卡驱动程序中，应将 ioaddr_t 替换为 unsigned int。

* 不再使用 irq_mask 和 irq_list 参数（自2.6.11起）
   PCMCIA 卡驱动程序不应再使用 irq_mask 和 irq_list 参数。相反，由 PCMCIA 核心来确定应该使用哪个 IRQ。因此，link->irq.IRQInfo2 被忽略。

* client->PendingEvents 已经移除（自2.6.11起）
   client->PendingEvents 不再可用。

* client->Attributes 已经移除（自2.6.11起）
   client->Attributes 未被使用，因此从所有 PCMCIA 卡驱动程序中移除。

* 不再提供核心函数（自2.6.11起）
   以下函数已从内核源码中移除，因为所有内核驱动程序都不使用它们，且没有外部驱动程序报告依赖于它们：

   pcmcia_get_first_region()
   pcmcia_get_next_region()
   pcmcia_modify_window()
   pcmcia_set_event_mask()
   pcmcia_get_first_window()
   pcmcia_get_next_window()

* 模块移除时遍历设备列表（自2.6.10起）
   在模块移除时，不再需要遍历驱动程序内部的客户端列表并调用 ->detach() 函数。

* 资源管理（自2.6.8起）
   尽管 PCMCIA 子系统会为卡片分配资源，但它不再标记这些资源为繁忙状态。这意味着驱动程序作者现在需要按照 Linux 中其他驱动程序的方式负责声明资源。你应该使用 request_region() 标记你的 IO 区域正在使用中，并使用 request_mem_region() 标记你的内存区域正在使用中。name 参数应指向你的驱动程序名称。例如，对于 pcnet_cs，name 应指向字符串 "pcnet_cs"。
* CardServices 已经移除
  在 2.4 中，CardServices() 是一个大的开关语句，用于调用各种服务。在 2.6 中，所有这些入口点都被导出并直接调用（除了 pcmcia_report_error()，可以改用 cs_error()）。
* 结构体 pcmcia_driver
  你需要使用结构体 pcmcia_driver 和 pcmcia_{un,}register_driver，而不是 {un,}register_pccard_driver。
