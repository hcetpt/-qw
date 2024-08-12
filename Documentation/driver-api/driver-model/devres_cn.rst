下面是给定文档的中文翻译：

---

**Devres - 管理设备资源**

**Tejun Heo** <teheo@suse.de>

**初稿** 2007年1月10日

.. contents

   1. 引言			: 嗯？Devres 是什么？
   2. Devres			: Devres 的简要介绍
   3. Devres 组			: 将多个 Devres 分组并一起释放
   4. 细节			: 生命周期规则、调用上下文等
   5. 开销			: 我们需要为此付出多少代价？
   6. 管理接口列表：当前实现的管理接口

**1. 引言**
-------------

在尝试将 libata 转换为使用 iomap 的过程中，产生了 devres。每个 iomap 地址都应该在驱动程序卸载时被保留并在适当时候解除映射。例如，一个普通的 SFF ATA 控制器（即，传统的 PCI IDE）在本机模式下会使用 5 个 PCI BAR，并且所有这些 BAR 都应该得到维护。
与许多其他设备驱动程序一样，libata 的低级驱动程序在其 `->remove` 和 `->probe` 失败路径中存在足够的 bug。嗯，是的，这可能是因为 libata 的低级驱动程序开发者们有点懒惰，但所有低级驱动程序开发者不都是这样吗？经过一天的时间摆弄没有文档或文档有误的脑残硬件后，如果最终能工作起来，那么它就是工作了。
由于种种原因，低级驱动程序没有得到核心代码那样多的关注或测试，而驱动程序卸载或初始化失败的 bug 并不足以引起注意。初始化失败路径的情况更糟，因为这种情况发生的概率较低，但又需要处理多个入口点。
因此，许多低级驱动程序在驱动程序卸载时会泄露资源，并且在 `->probe()` 中具有半残缺的失败路径实现，当发生失败时可能会泄露资源甚至导致系统崩溃。iomap 的加入使这个问题更加复杂。msi 和 msix 也是如此。
**2. Devres**
--------------

基本上，devres 是一个与 `struct device` 关联的任意大小内存区域的链表。每个 devres 条目都关联有一个释放函数。可以通过几种方式来释放 devres。无论如何，在驱动程序卸载时所有 devres 条目都会被释放。在释放时，会调用与之关联的释放函数，然后释放 devres 条目。
对于使用 devres 的设备驱动程序中常用的资源，创建了管理接口。例如，使用 `dma_alloc_coherent()` 获取一致性 DMA 内存。其管理版本称为 `dmam_alloc_coherent()`。它与 `dma_alloc_coherent()` 完全相同，只是通过它分配的 DMA 内存在驱动程序卸载时会被自动释放。其实现如下所示：

```c
  struct dma_devres {
    size_t      size;
    void        *vaddr;
    dma_addr_t  dma_handle;
  };

  static void dmam_coherent_release(struct device *dev, void *res)
  {
    struct dma_devres *this = res;

    dma_free_coherent(dev, this->size, this->vaddr, this->dma_handle);
  }

  dmam_alloc_coherent(dev, size, dma_handle, gfp)
  {
    struct dma_devres *dr;
    void *vaddr;

    dr = devres_alloc(dmam_coherent_release, sizeof(*dr), gfp);
    ..
    /* 以通常的方式分配 DMA 内存 */
    vaddr = dma_alloc_coherent(...);
    ..
    /* 在 dr 中记录 size、vaddr、dma_handle */
    dr->vaddr = vaddr;
    ..
```
### Code Translation:

```c
void devres_add(struct device *dev, struct devres_resource *dr);

return (void *)vaddr;
}

if a driver uses dmam_alloc_coherent(), the allocated region is guaranteed to be
freed whether initialization fails halfway or the device gets
detached. If most resources are acquired using the managed interface, a
driver can have much simpler initialization and cleanup code. The initialization path basically
looks like the following:

my_init_one()
{
    struct mydev *d;

    d = devm_kzalloc(dev, sizeof(*d), GFP_KERNEL);
    if (!d)
        return -ENOMEM;

    d->ring = dmam_alloc_coherent(...);
    if (!d->ring)
        return -ENOMEM;

    if (check something)
        return -EINVAL;
    ...
    return register_to_upper_layer(d);
}

And the cleanup path:

my_remove_one()
{
    unregister_from_upper_layer(d);
    shutdown_my_hardware();
}
```

### Explanation:

如上所示，使用`devres`可以大大简化底层驱动。复杂性从维护较少的底层驱动转移到了维护较好的高层。同时，由于初始化失败路径与清理路径是共享的，两者都能得到更多的测试。

然而，在将当前调用或赋值转换为受管理的`devm_*`版本时，你需要检查内部操作（例如内存分配）是否失败。管理资源仅关注这些资源的释放——所有其他必要的检查仍然由你负责。在某些情况下，这可能意味着需要引入以前在迁移到受管理的`devm_*`调用之前不需要的检查。

### 资源组 (Devres Group)

资源条目可以使用资源组进行分组。当一个组被释放时，所有包含的普通资源条目和适当嵌套的组都会被释放。一个用途是在失败时回滚一系列已获取的资源。例如：

```c
if (!devres_open_group(dev, NULL, GFP_KERNEL))
    return -ENOMEM;

acquire A;
if (failed)
    goto err;

acquire B;
if (failed)
    goto err;
...
devres_remove_group(dev, NULL);
return 0;

err:
devres_release_group(dev, NULL);
return err_code;
```

由于资源获取失败通常意味着探测失败，上述结构通常在中间层驱动中很有用（例如，libata核心层），其中接口函数在失败时不应有副作用。
对于LLD（低层驱动），大多数情况下仅仅返回错误码就足够了。

每个组通过`void *id`来标识。它可以通过作为`devres_open_group()`的`@id`参数显式指定，或者通过传递NULL作为`@id`自动创建，如上面的例子所示。在这两种情况下，`devres_open_group()`返回该组的id。返回的id可以传递给其他`devres`函数以选择目标组。
如果给这些函数传递NULL，则选择最新打开的组。

例如，你可以像下面这样做：

```c
int my_midlayer_create_something()
{
    if (!devres_open_group(dev, my_midlayer_create_something, GFP_KERNEL))
        return -ENOMEM;

    ...
    devres_close_group(dev, my_midlayer_create_something);
    return 0;
}

void my_midlayer_destroy_something()
{
    devres_release_group(dev, my_midlayer_create_something);
}
```

### 细节

一个`devres`条目的生命周期从分配开始，并在其被释放或销毁（移除并释放）时结束——没有引用计数。
### 原文翻译

#### Devres Core 保证原子性对所有基本的 devres 操作，并且
支持单实例 devres 类型（原子查找并添加若不存在）。除此之外，同步并发访问已分配的 devres 数据是调用者的责任。这通常不是问题，因为总线操作和资源分配已经完成了这项工作。
例如，单实例 devres 类型的一个例子，请参阅 `lib/devres.c` 中的 `pcim_iomap_table()` 函数。
所有的 devres 接口函数可以在没有上下文的情况下被调用，如果给出了正确的 gfp 标志。

5. 开销
--------

每个 devres 会计信息与请求的数据区域一起分配。在关闭调试选项的情况下，会计信息在 32 位机器上占用 16 字节，在 64 位机器上占用 24 字节（三个指针向上取整到 ull 对齐）。如果使用单链表，它可以减少到两个指针（32 位 8 字节，64 位 16 字节）。
每个 devres 组占用 8 个指针。如果使用单链表可以减少到 6 个。
在带有两个端口的 ahci 控制器上，经过简单的转换后，内存空间开销在 32 位机器上介于 300 到 400 字节之间（我们当然可以投入更多努力到 libata 核心层）。

6. 管理接口列表
------------------

**时钟 (CLOCK)**
  - `devm_clk_get()`
  - `devm_clk_get_optional()`
  - `devm_clk_put()`
  - `devm_clk_bulk_get()`
  - `devm_clk_bulk_get_all()`
  - `devm_clk_bulk_get_optional()`
  - `devm_get_clk_from_child()`
  - `devm_clk_hw_register()`
  - `devm_of_clk_add_hw_provider()`
  - `devm_clk_hw_register_clkdev()`

**直接内存访问 (DMA)**
  - `dmaenginem_async_device_register()`
  - `dmam_alloc_coherent()`
  - `dmam_alloc_attrs()`
  - `dmam_free_coherent()`
  - `dmam_pool_create()`
  - `dmam_pool_destroy()`

**图形设备管理 (DRM)**
  - `devm_drm_dev_alloc()`

**通用输入输出 (GPIO)**
  - `devm_gpiod_get()`
  - `devm_gpiod_get_array()`
  - `devm_gpiod_get_array_optional()`
  - `devm_gpiod_get_index()`
  - `devm_gpiod_get_index_optional()`
  - `devm_gpiod_get_optional()`
  - `devm_gpiod_put()`
  - `devm_gpiod_unhinge()`
  - `devm_gpiochip_add_data()`
  - `devm_gpio_request()`
  - `devm_gpio_request_one()`

**I2C**
  - `devm_i2c_add_adapter()`
  - `devm_i2c_new_dummy_device()`

**工业 I/O (IIO)**
  - `devm_iio_device_alloc()`
  - `devm_iio_device_register()`
  - `devm_iio_dmaengine_buffer_setup()`
  - `devm_iio_kfifo_buffer_setup()`
  - `devm_iio_kfifo_buffer_setup_ext()`
  - `devm_iio_map_array_register()`
  - `devm_iio_triggered_buffer_setup()`
  - `devm_iio_triggered_buffer_setup_ext()`
  - `devm_iio_trigger_alloc()`
  - `devm_iio_trigger_register()`
  - `devm_iio_channel_get()`
  - `devm_iio_channel_get_all()`
  - `devm_iio_hw_consumer_alloc()`
  - `devm_fwnode_iio_channel_get_by_name()`

**输入设备 (INPUT)**
  - `devm_input_allocate_device()`

**I/O 区域**
  - `devm_release_mem_region()`
  - `devm_release_region()`
  - `devm_release_resource()`
  - `devm_request_mem_region()`
  - `devm_request_free_mem_region()`
  - `devm_request_region()`
  - `devm_request_resource()`

**I/O 映射 (IOMAP)**
  - `devm_ioport_map()`
  - `devm_ioport_unmap()`
  - `devm_ioremap()`
  - `devm_ioremap_uc()`
  - `devm_ioremap_wc()`
  - `devm_ioremap_resource()`: 检查资源、请求内存区域、映射
  - `devm_ioremap_resource_wc()`
  - `devm_platform_ioremap_resource()`: 为平台设备调用 `devm_ioremap_resource()`
  - `devm_platform_ioremap_resource_byname()`
  - `devm_platform_get_and_ioremap_resource()`
  - `devm_iounmap()`

  **注：** 对于 PCI 设备，可以使用特定的 `pcim_*()` 函数，见下文
**中断请求 (IRQ)**
  - `devm_free_irq()`
  - `devm_request_any_context_irq()`
  - `devm_request_irq()`
  - `devm_request_threaded_irq()`
  - `devm_irq_alloc_descs()`
  - `devm_irq_alloc_desc()`
  - `devm_irq_alloc_desc_at()`
  - `devm_irq_alloc_desc_from()`
  - `devm_irq_alloc_descs_from()`
  - `devm_irq_alloc_generic_chip()`
  - `devm_irq_setup_generic_chip()`
  - `devm_irq_domain_create_sim()`

**LED**
  - `devm_led_classdev_register()`
  - `devm_led_classdev_register_ext()`
  - `devm_led_classdev_unregister()`
  - `devm_led_trigger_register()`
  - `devm_of_led_get()`

**媒体独立接口 (MDIO)**
  - `devm_mdiobus_alloc()`
  - `devm_mdiobus_alloc_size()`
  - `devm_mdiobus_register()`
  - `devm_of_mdiobus_register()`

**内存管理 (MEM)**
  - `devm_free_pages()`
  - `devm_get_free_pages()`
  - `devm_kasprintf()`
  - `devm_kcalloc()`
  - `devm_kfree()`
  - `devm_kmalloc()`
  - `devm_kmalloc_array()`
  - `devm_kmemdup()`
  - `devm_krealloc()`
  - `devm_krealloc_array()`
  - `devm_kstrdup()`
  - `devm_kstrdup_const()`
  - `devm_kvasprintf()`
  - `devm_kzalloc()`

**多功能设备 (MFD)**
  - `devm_mfd_add_devices()`

**多路复用器 (MUX)**
  - `devm_mux_chip_alloc()`
  - `devm_mux_chip_register()`
  - `devm_mux_control_get()`
  - `devm_mux_state_get()`

**网络 (NET)**
  - `devm_alloc_etherdev()`
  - `devm_alloc_etherdev_mqs()`
  - `devm_register_netdev()`

**每 CPU 内存 (PER-CPU MEM)**
  - `devm_alloc_percpu()`
  - `devm_free_percpu()`

**PCI**
  - `devm_pci_alloc_host_bridge()` : 管理的 PCI 主桥接器分配
  - `devm_pci_remap_cfgspace()` : 映射 PCI 配置空间
  - `devm_pci_remap_cfg_resource()` : 映射 PCI 配置空间资源

  - `pcim_enable_device()` : 成功后，所有 PCI 操作变为受管理
  - `pcim_iomap()` : 在单一 BAR 上执行 `iomap()`
  - `pcim_iomap_regions()` : 在多个 BAR 上执行 `request_region()` 和 `iomap()`
  - `pcim_iomap_regions_request_all()` : 在所有 BAR 上执行 `request_region()` 并在多个 BAR 上执行 `iomap()`
  - `pcim_iomap_table()` : 通过 BAR 索引的映射地址数组
  - `pcim_iounmap()` : 在单一 BAR 上执行 `iounmap()`
  - `pcim_iounmap_regions()` : 在多个 BAR 上执行 `iounmap()` 和 `release_region()`
  - `pcim_pin_device()` : 在释放后保持 PCI 设备启用
  - `pcim_set_mwi()` : 启用 Memory-Write-Invalidate PCI 事务

**物理层 (PHY)**
  - `devm_usb_get_phy()`
  - `devm_usb_get_phy_by_node()`
  - `devm_usb_get_phy_by_phandle()`
  - `devm_usb_put_phy()`

**管脚控制 (PINCTRL)**
  - `devm_pinctrl_get()`
  - `devm_pinctrl_put()`
  - `devm_pinctrl_get_select()`
  - `devm_pinctrl_register()`
  - `devm_pinctrl_register_and_init()`
  - `devm_pinctrl_unregister()`

**电源管理 (POWER)**
  - `devm_reboot_mode_register()`
  - `devm_reboot_mode_unregister()`

**脉宽调制 (PWM)**
  - `devm_pwmchip_alloc()`
  - `devm_pwmchip_add()`
  - `devm_pwm_get()`
  - `devm_fwnode_pwm_get()`

**调节器 (REGULATOR)**
  - `devm_regulator_bulk_register_supply_alias()`
  - `devm_regulator_bulk_get()`
  - `devm_regulator_bulk_get_const()`
  - `devm_regulator_bulk_get_enable()`
  - `devm_regulator_bulk_put()`
  - `devm_regulator_get()`
  - `devm_regulator_get_enable()`
  - `devm_regulator_get_enable_read_voltage()`
  - `devm_regulator_get_enable_optional()`
  - `devm_regulator_get_exclusive()`
  - `devm_regulator_get_optional()`
  - `devm_regulator_irq_helper()`
  - `devm_regulator_put()`
  - `devm_regulator_register()`
  - `devm_regulator_register_notifier()`
  - `devm_regulator_register_supply_alias()`
  - `devm_regulator_unregister_notifier()`

**复位 (RESET)**
  - `devm_reset_control_get()`
  - `devm_reset_controller_register()`

**实时时钟 (RTC)**
  - `devm_rtc_device_register()`
  - `devm_rtc_allocate_device()`
  - `devm_rtc_register_device()`
  - `devm_rtc_nvmem_register()`

**串行设备 (SERDEV)**
  - `devm_serdev_device_open()`

**从属 DMA 引擎 (SLAVE DMA ENGINE)**
  - `devm_acpi_dma_controller_register()`
  - `devm_acpi_dma_controller_free()`

**串行外设接口 (SPI)**
  - `devm_spi_alloc_master()`
  - `devm_spi_alloc_slave()`
  - `devm_spi_optimize_message()`
  - `devm_spi_register_controller()`
  - `devm_spi_register_host()`
  - `devm_spi_register_target()`

**看门狗 (WATCHDOG)**
  - `devm_watchdog_register_device()`
