FPGA 管理器
============

概述
--------

FPGA 管理器核心导出了一组用于使用图像编程 FPGA 的函数。此 API 不依赖于制造商。所有与制造商相关的细节都隐藏在一个低级别的驱动程序中，该驱动程序向核心注册了一系列操作。FPGA 图像数据本身非常依赖于制造商，但就我们的目的而言，它只是二进制数据。FPGA 管理器核心不会解析它。要编程的 FPGA 图像可以存在于分散/聚集列表、单个连续缓冲区或固件文件中。因为应避免为缓冲区分配连续内核内存，因此鼓励用户在可能的情况下使用分散/聚集列表。编程图像的具体细节体现在一个结构体（`struct fpga_image_info`）中。这个结构体包含了指向 FPGA 图像的指针以及特定于图像的详细信息，如图像是否为全配置或部分重新配置构建。

如何支持新的 FPGA 设备
--------------------------------

为了添加另一个 FPGA 管理器，需要编写一个实现了操作集的驱动程序。探测函数调用 `fpga_mgr_register()` 或 `fpga_mgr_register_full()`，例如：

```c
static const struct fpga_manager_ops socfpga_fpga_ops = {
	.write_init = socfpga_fpga_ops_configure_init,
	.write = socfpga_fpga_ops_configure_write,
	.write_complete = socfpga_fpga_ops_configure_complete,
	.state = socfpga_fpga_ops_state,
};

static int socfpga_fpga_probe(struct platform_device *pdev)
{
	struct device *dev = &pdev->dev;
	struct socfpga_fpga_priv *priv;
	struct fpga_manager *mgr;
	int ret;

	priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
	if (!priv)
		return -ENOMEM;

	/* 
	 * 执行 ioremap 操作，获取中断等，并将它们保存到 priv 中
	 */

	mgr = fpga_mgr_register(dev, "Altera SOCFPGA FPGA Manager",
					&socfpga_fpga_ops, priv);
	if (IS_ERR(mgr))
		return PTR_ERR(mgr);

	platform_set_drvdata(pdev, mgr);

	return 0;
}

static int socfpga_fpga_remove(struct platform_device *pdev)
{
	struct fpga_manager *mgr = platform_get_drvdata(pdev);

	fpga_mgr_unregister(mgr);

	return 0;
}
```

或者，探测函数也可以调用其中一个资源管理注册函数 `devm_fpga_mgr_register()` 或 `devm_fpga_mgr_register_full()`。当使用这些函数时，参数语法是相同的，但是对 `fpga_mgr_unregister()` 的调用应该被移除。在上述示例中，`socfpga_fpga_remove()` 函数将不需要。

这些操作将实现所需的设备特定寄存器写入以完成特定 FPGA 的编程序列。这些操作返回 0 表示成功，否则返回负错误码。

编程序列如下：
1. `.parse_header`（可选，可能被调用一次或多次）
2. `.write_init`
3. `.write` 或 `.write_sg`（可能被调用一次或多次）
4. `.write_complete`

`.parse_header` 函数会将 `header_size` 和 `data_size` 设置到 `struct fpga_image_info` 中。在调用 `.parse_header` 之前，`header_size` 初始化为 `initial_header_size`。如果 `fpga_manager_ops` 的 `skip_header` 标志为真，则 `.write` 函数将从图像缓冲区的开头偏移 `header_size` 处获取图像缓冲区。如果设置了 `data_size`，`.write` 函数将获取 `data_size` 字节的图像缓冲区，否则 `.write` 将获取直到图像缓冲区结束的数据。
这不会影响 `.write_sg`，`.write_sg` 仍然以散列表形式获取整个图像。如果 FPGA 图像已经被映射为单个连续缓冲区，则整个缓冲区将传递给 `.parse_header`。如果图像是以分散/聚集形式存在的，核心代码将在第一次调用 `.parse_header` 之前至少缓冲 `initial_header_size` 大小的数据；如果这还不够，`.parse_header` 应该将所需大小设置到 `info->header_size` 并返回 `-EAGAIN`，然后它将再次被调用，输入更多的图像缓冲区数据。
`.write_init` 函数将准备 FPGA 接收图像数据。传递给 `.write_init` 的缓冲区长度至少为 `info->header_size` 字节；如果整个位流不是立即可用的，那么核心代码将在开始前至少缓冲这么多数据。
`.write` 函数将一个缓冲区写入 FPGA。该缓冲区可能包含整个 FPGA 图像，也可能只包含 FPGA 图像的一个较小部分。在这种情况下，此函数会被多次调用以处理连续的块。这个接口适用于使用 PIO 的驱动程序。
`.write_sg` 版本的行为与 `.write` 相同，只是输入是一个 `sg_table` 散列列表。这个接口适用于使用 DMA 的驱动程序。
在所有图像数据写入后会调用 `.write_complete` 函数，使 FPGA 进入运行模式。
操作包括一个 `.state` 函数，该函数将确定 FPGA 的状态，并返回一个 `enum fpga_mgr_states` 类型的代码。这不会导致状态改变。

实现新的 FPGA 管理器驱动程序的 API
----------------------------------------------

* `fpga_mgr_states` - :c:expr:`fpga_manager->state` 的值
* struct fpga_manager - FPGA 管理器结构体
* struct fpga_manager_ops - 低级 FPGA 管理器驱动程序操作
* struct fpga_manager_info - 用于 `fpga_mgr_register_full()` 的参数结构体
* `__fpga_mgr_register_full()` - 使用 `fpga_mgr_info` 结构体创建并注册一个 FPGA 管理器，提供最大灵活性的选项
* `__fpga_mgr_register()` - 使用标准参数创建并注册一个 FPGA 管理器
* `__devm_fpga_mgr_register_full()` - `__fpga_mgr_register_full()` 的资源管理版本
* `__devm_fpga_mgr_register()` - `__fpga_mgr_register()` 的资源管理版本
* `fpga_mgr_unregister()` - 注销一个 FPGA 管理器

提供了辅助宏 `fpga_mgr_register_full()`、`fpga_mgr_register()`、`devm_fpga_mgr_register_full()` 和 `devm_fpga_mgr_register()` 来简化注册过程。

.. kernel-doc:: include/linux/fpga/fpga-mgr.h
   :functions: fpga_mgr_states

.. kernel-doc:: include/linux/fpga/fpga-mgr.h
   :functions: fpga_manager

.. kernel-doc:: include/linux/fpga/fpga-mgr.h
   :functions: fpga_manager_ops

.. kernel-doc:: include/linux/fpga/fpga-mgr.h
   :functions: fpga_manager_info

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: __fpga_mgr_register_full

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: __fpga_mgr_register

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: __devm_fpga_mgr_register_full

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: __devm_fpga_mgr_register

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: fpga_mgr_unregister
