============= 驱动变更 =============

此文件详细记录了2.6版本中影响PCMCIA卡驱动作者的变更：

* pcmcia_loop_config() 和自动配置（自2.6.36起）
   如果 `struct pcmcia_device *p_dev->config_flags` 被正确设置，
   pcmcia_loop_config() 现在会自动设置某些配置值，尽管驱动仍然可以在回调函数中覆盖这些设置。目前提供的自动配置选项包括：

	- CONF_AUTO_CHECK_VCC : 检查匹配的Vcc
	- CONF_AUTO_SET_VPP   : 设置Vpp
	- CONF_AUTO_AUDIO     : 如需要，自动启用音频线路
	- CONF_AUTO_SET_IO    : 设置ioport资源（->resource[0,1]）
	- CONF_AUTO_SET_IOMEM : 设置第一个iomem资源（->resource[2]）

* pcmcia_request_configuration -> pcmcia_enable_device（自2.6.36起）
   pcmcia_request_configuration() 已重命名为 pcmcia_enable_device()，因为它与 pcmcia_disable_device() 相对应。配置设置现在存储在 struct pcmcia_device 中，例如在字段 config_flags、config_index、config_base 和 vpp 中。
* pcmcia_request_window 的变更（自2.6.36起）
   驱动程序现在被要求填写 `struct pcmcia_device *p_dev->resource[2,3,4,5]` 来为最多四个 ioport 范围。调用 pcmcia_request_window() 后，找到的区域将被保留并可立即使用 —— 直到调用 pcmcia_release_window()。
* pcmcia_request_io 的变更（自2.6.36起）
   驱动程序现在被要求填写 `struct pcmcia_device *p_dev->resource[0,1]` 来为最多两个 ioport 范围。调用 pcmcia_request_io() 后，找到的端口将被保留；调用 pcmcia_request_configuration() 后，它们可以被使用。
* 不再有 dev_info_t 和 cs_types.h（自2.6.36起）
   删除了 dev_info_t 和其他一些类型定义。请不要再在 PCMCIA 设备驱动程序中使用它们。此外，请不要包含 pcmcia/cs_types.h，因为该文件已不存在。
* 不再有 dev_node_t（自2.6.35起）
   不再需要填充“dev_node_t”结构体。
* 新的IRQ请求规则（自2.6.35起）
   驱动程序现在可以选择以下方法代替旧的 pcmcia_request_irq() 接口：

   - 直接调用 request_irq/free_irq。使用 `*p_dev->irq` 中的 IRQ
- 使用 pcmcia_request_irq(p_dev, handler_t); PCMCIA 核心会在调用 pcmcia_disable_device() 或设备弹出时自动清理
* 不再有 cs_error / CS_CHECK / CONFIG_PCMCIA_DEBUG（自2.6.33起）
   请改用 Linux 风格的返回值检查，以及必要时使用 "dev_dbg()" 或 "pr_debug()" 的调试信息，代替 cs_error() 回调或 CS_CHECK() 宏。
* 新的CIS元组访问方式（自2.6.33起）
   驱动应当使用 "pcmcia_get_tuple()" 如果只对一个（原始）元组感兴趣，或者使用 "pcmcia_loop_tuple()" 如果对某种类型的全部元组感兴趣。为了从 CISTPL_FUNCE 解码MAC地址，添加了一个新的辅助函数 "pcmcia_get_mac_from_cis()"。
* 新的配置循环辅助函数（自2.6.28起）
   通过调用 pcmcia_loop_config()，驱动可以遍历所有可用的配置选项。在驱动的 probe() 阶段，在大多数情况下不需要直接使用 pcmcia_get_{first,next}_tuple、pcmcia_get_tuple_data 和 pcmcia_parse_tuple。
* 新版本辅助功能（自 2.6.17 版本起）
   现在，无需调用 pcmcia_release_{configuration,io,irq,win}，只需调用 pcmcia_disable_device 即可。由于没有合理的理由再调用 pcmcia_release_io 和 pcmcia_release_irq，因此它们的导出已被移除。

* 统一 detach 和 REMOVAL 事件代码，以及 attach 和 INSERTION 代码（自 2.6.16 版本起）：

       void (*remove)          (struct pcmcia_device *dev);
       int (*probe)            (struct pcmcia_device *dev);

* 将 suspend、resume 和 reset 移出事件处理器（自 2.6.16 版本起）：

       int (*suspend)          (struct pcmcia_device *dev);
       int (*resume)           (struct pcmcia_device *dev);

   应该在 struct pcmcia_driver 中初始化，并处理 (SUSPEND == RESET_PHYSICAL) 和 (RESUME == CARD_RESET) 事件。

* 事件处理器初始化在 struct pcmcia_driver 中（自 2.6.13 版本起）
   事件处理器会接收到所有事件通知，必须作为驱动程序 struct pcmcia_driver 中的 event() 回调函数进行初始化。

* 不再使用 pcmcia/version.h（自 2.6.13 版本起）
   此文件最终会被移除。

* 内核内的设备<->驱动匹配（自 2.6.13 版本起）
   PCMCIA 设备及其正确的驱动现在可以在内核空间中进行匹配。详情请参阅 'devicetable.txt'。

* 设备模型集成（自 2.6.11 版本起）
   一个 struct pcmcia_device 被注册到设备模型核心，并且可以通过使用 handle_to_dev(client_handle_t * handle) 来使用（例如，用于 SET_NETDEV_DEV）。

* 将内部 I/O 端口地址转换为 unsigned int（自 2.6.11 版本起）
   在 PCMCIA 卡驱动程序中，ioaddr_t 应该被 unsigned int 替换。

* irq_mask 和 irq_list 参数（自 2.6.11 版本起）
   PCMCIA 卡驱动程序中不应再使用 irq_mask 和 irq_list 参数。相反，确定使用哪个 IRQ 的工作应由 PCMCIA 核心完成。因此，link->irq.IRQInfo2 被忽略。

* client->PendingEvents 已被移除（自 2.6.11 版本起）
   client->PendingEvents 已不再可用。

* client->Attributes 已被移除（自 2.6.11 版本起）
   client->Attributes 未被使用，因此从所有 PCMCIA 卡驱动程序中移除。

* 不再可用的核心函数（自 2.6.11 版本起）
   以下函数已从内核源码中移除，因为它们未被所有内核驱动使用，也没有外部驱动报告依赖于它们：

   - pcmcia_get_first_region()
   - pcmcia_get_next_region()
   - pcmcia_modify_window()
   - pcmcia_set_event_mask()
   - pcmcia_get_first_window()
   - pcmcia_get_next_window()

* 模块移除时对设备列表的迭代（自 2.6.10 版本起）
   模块移除时，不再需要在驱动程序的内部 client 列表上进行迭代并调用 ->detach() 函数。

* 资源管理（自 2.6.8 版本起）
   尽管 PCMCIA 子系统会为卡片分配资源，但它不再标记这些资源为繁忙状态。这意味着驱动作者现在负责像其他 Linux 驱动一样声明自己的资源。您应该使用 request_region() 来标记您的 I/O 区域正在使用中，并使用 request_mem_region() 来标记您的内存区域正在使用中。name 参数应该是指向您的驱动名称的指针。例如，对于 pcnet_cs，name 应指向字符串 "pcnet_cs"。
* CardServices 已经移除
  在 2.4 中的 CardServices() 实际上是一个大型的开关语句，用于调用各种服务。在 2.6 中，所有这些入口点都被导出并直接调用（除了 pcmcia_report_error()，你可以改用 cs_error()）
* 结构体 pcmcia_driver
  你需要使用结构体 pcmcia_driver 和函数 pcmcia_{un,}register_driver，而不是使用 {un,}register_pccard_driver
