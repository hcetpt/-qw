.. _todo:

=========
待办事项列表
=========

本节包含内核 DRM 图形子系统中一些较小的维护任务，适合新手项目或下雨天的闲暇时间。
难度
----------

为了使任务更易于分类，我们将它们分为不同的级别：

入门级：适合开始了解 DRM 子系统的任务
中级：需要一些在 DRM 子系统工作的经验，或者一些特定 GPU/显示图形知识的任务。对于调试问题来说，最好有相关硬件（或虚拟驱动）来进行测试
高级：需要对 DRM 子系统和图形主题有相当好的理解的任务。通常需要相关硬件进行开发和测试
专家级：只有在你已经成功完成了一些复杂的重构，并且是该领域的专家时，才尝试这些任务

子系统的重构
===========================

移除自定义的 dumb_map_offset 实现
---------------------------------------------

所有基于 GEM 的驱动程序都应该使用 drm_gem_create_mmap_offset() 而不是自定义实现
审核每个单独的驱动程序，确保它可以与通用实现一起工作（各种实现中有许多过时的锁定残余），然后移除它
联系人：Daniel Vetter，相应的驱动程序维护者

难度：中级

将现有的 KMS 驱动程序转换为原子模式设置
--------------------------------------------------

3.19 版本引入了原子模式设置接口和辅助函数，因此现在可以将驱动程序转换为原子模式设置。现代合成器如 Wayland 或 Android 上的 Surfaceflinger 非常需要一个原子模式设置接口，所以这是关于未来的光明前景
有一个关于原子模式设置的转换指南 [1]_，并且你需要一个尚未转换的驱动程序对应的 GPU。LWN.net 上的“Atomic mode setting design overview”系列文章 [2]_ [3]_ 也可以有所帮助
作为这一部分，驱动程序还需要转换为通用平面（这意味着将主平面和光标作为适当的平面对象暴露出来）。但是通过直接使用新的原子辅助驱动回调，这更容易做到
.. [1] https://blog.ffwll.ch/2014/11/atomic-modeset-support-for-kms-drivers.html
  .. [2] https://lwn.net/Articles/653071/
  .. [3] https://lwn.net/Articles/653466/

联系人：Daniel Vetter，相应的驱动程序维护者

难度：高级

清理平面周围裁剪协调的混乱
---------------------------------------------------------

我们有一个帮助函数 drm_plane_helper_check_update() 来正确处理这个问题，但它并未被一致使用。应该予以修复，最好是在原子辅助函数中（并将驱动程序转换为裁剪坐标）。可能还需要将该帮助函数从 drm_plane_helper.c 移到原子辅助函数中，以避免混淆——该文件中的其他帮助函数都是过时的遗留函数
联系人：Ville Syrjälä，Daniel Vetter，驱动程序维护者

级别：高级

改进平面原子检查辅助函数
------------------------------

除了上面提到的裁剪坐标外，当前辅助函数还存在一些次优之处：

- `drm_plane_helper_funcs->atomic_check` 会为启用或禁用的平面调用。这至少会让驱动程序感到困惑，最坏的情况是当没有 CRTC 的平面被禁用时，驱动程序会崩溃。唯一的特殊处理是在平面状态结构中重置值，这些应该移到 `drm_plane_funcs->atomic_duplicate_state` 函数中。
- 完成这一工作后，辅助函数可以停止对禁用平面调用 `->atomic_check`。
- 然后我们可以遍历所有驱动程序，并移除那些或多或少令人困惑的对 `plane_state->fb` 和 `plane_state->crtc` 的检查。

联系人：Daniel Vetter

级别：高级

将早期原子模式集驱动程序转换为异步提交辅助函数
----------------------------------------------------

在原子模式集辅助函数出现的第一年里，并不支持异步/非阻塞提交，每个驱动程序都需要手动实现。这个问题现在已经修复，但仍然有一部分现有驱动程序可以轻松地转换到新的基础设施上。
辅助函数的一个问题是它们要求驱动程序正确处理原子提交的完成事件。但修复这些问题本身是有益的。
与此相关的是 legacy_cursor_update 黑客技术，这应该被替换为新的原子异步检查/提交功能，对于那些仍在查看该标志的驱动程序来说尤其如此。

联系人：Daniel Vetter，各自的驱动程序维护者

级别：高级

重命名 drm_atomic_state
------------------------

KMS 框架对“状态”概念有两种略有不同的定义。对于给定的对象（平面、CRTC、编码器等，即 `drm_$OBJECT_state`），状态是指该对象的整个状态。然而，在设备级别，`drm_atomic_state` 指的是一组有限对象的状态更新。
这个状态并不是整个设备的状态，而是该设备中某些对象的完整状态。这对新手来说很困惑，`drm_atomic_state` 应该重命名为更清晰的名字，如 `drm_atomic_commit`。
除了重命名结构本身之外，这也意味着需要重命名一些相关的函数（`drm_atomic_state_alloc`、`drm_atomic_state_get`、`drm_atomic_state_put`、`drm_atomic_state_init`、`__drm_atomic_state_free` 等）。

联系人：Maxime Ripard <mripard@kernel.org>

级别：高级

原子 KMS 的后续影响
-----------------------

`drm_atomic_helper.c` 提供了一组函数，实现了基于新原子驱动接口的旧 IOCTLs。这对于逐步转换驱动程序非常有用，但不幸的是，语义上的不匹配问题比较严重。因此有一些后续工作来调整函数接口以解决这些问题：

* 原子需要锁获取上下文。目前这是通过一些糟糕的黑客技术隐式传递的，并且也是在后台使用 `GFP_NOFAIL` 分配的。所有旧路径都需要开始显式分配获取上下文并在栈上明确传递给驱动程序，以便旧的基于原子的函数能够使用它们。
除了某些驱动代码外，其余部分已经完成。此任务应在 `drm_modeset_lock_all()` 中添加 `WARN_ON(!drm_drv_uses_atomic_modeset)` 来完成。

* 许多虚函数钩子现在位于错误的位置：DRM 有一个核心虚函数表（命名为 `drm_foo_funcs`），用于实现用户空间的 ABI。然后还有一些可选的钩子用于辅助库（命名为 `drm_foo_helper_funcs`），这些是仅用于内部使用的。一些这样的钩子应该从 `_funcs` 移动到 `_helper_funcs`，因为它们不是核心 ABI 的一部分。在 `drm_crtc.h` 中每个此类情况的内核文档中都有一个 `FIXME` 注释。
联系人：Daniel Vetter

难度等级：中级

移除 GEM 驱动中的 `dev->struct_mutex`
---------------------------------------------

`dev->struct_mutex` 是来自旧时代的 DRM 大锁，并且已经渗透到了所有地方。如今，在现代驱动中，唯一需要它的部分是在序列化 GEM 缓冲对象销毁时。不幸的是，这意味着驱动程序必须跟踪这个锁，并根据上下文调用 `unreference` 或 `unreference_locked`。
自内核 4.8 版本以来，核心 GEM 已经不再需要 `struct_mutex` 了，并且有一个针对完全摆脱 `struct_mutex` 的驱动程序的 GEM 对象 `free` 回调。
对于需要 `struct_mutex` 的驱动程序，应将其替换为驱动程序私有的锁。棘手的部分在于 BO（缓冲对象）释放函数，因为这些函数不能再可靠地获取该锁。相反，状态需要用适当的次级锁保护，或者将一些清理工作推送到工作线程中。对于性能关键型驱动程序，可能更好地采用更细粒度的每缓冲对象和每上下文锁定方案。目前只有 `msm` 和 `i915` 驱动程序使用 `struct_mutex`。
联系人：Daniel Vetter，相关驱动程序维护者

难度等级：高级

将缓冲对象锁定移动到 `dma_resv_lock()`
---------------------------------------------

许多驱动程序有自己每对象的锁定方案，通常使用 `mutex_lock()`。这导致各种各样的问题，因为在共享缓冲区时，根据哪个驱动程序是导出者和导入者，锁定层次会颠倒。
为了解决这个问题，我们需要一种标准的每对象锁定机制，即 `dma_resv_lock()`。这个锁需要作为最外层的锁来调用，并移除所有其他特定于驱动程序的每对象锁。问题是实际更改锁定协议是一个重要的步骤，因为涉及 `struct dma_buf` 缓冲区共享。
难度等级：专家

将日志转换为带有 `drm_device` 参数的 `drm_*` 函数
------------------------------------------------------------

对于可能有多个实例的驱动程序来说，在日志中区分各个实例是必要的。由于 `DRM_INFO/WARN/ERROR` 不支持这一点，驱动程序使用 `dev_info/warn/err` 来进行区分。我们现在有了 `drm_*` 变体的 DRM 打印函数，因此可以开始将这些驱动程序转换回使用 DRM 格式的特定日志消息。
在开始此转换之前，请联系相关维护者以确保您的工作会被合并——并非所有人都同意 DRM dmesg 宏更好。
联系人：Sean Paul，您计划转换的驱动程序的维护者

难度等级：入门

将驱动程序转换为使用简单的模式设置挂起/恢复
----------------------------------------------------

大多数驱动程序（除了 `i915` 和 `nouveau`）使用 `drm_atomic_helper_suspend/resume()` 的可以被转换为使用 `drm_mode_config_helper_suspend/resume()`。此外，在较旧的原子模式设置驱动程序中还有硬编码版本的原子挂起/恢复代码。
联系人：你计划转换的驱动程序维护者

级别：中级

在不使用 fbdev 的情况下重新实现 drm_fbdev_fb_ops 中的函数
-------------------------------------------------------

drm_fbdev_fb_ops 中的一些回调函数可以从不依赖 fbdev 模块的角度进行重写。一些辅助函数可以进一步利用 `struct iosys_map` 而不是原始指针。

联系人：Thomas Zimmermann <tzimmermann@suse.de>，Daniel Vetter

级别：高级

基准测试和优化位块传输（blitting）及格式转换函数
--------------------------------------------------------------

快速绘制到显示内存对于许多应用程序的性能至关重要。至少在 x86-64 架构上，`sys_imageblit()` 显著慢于 `cfb_imageblit()`，尽管两者都使用相同的位块传输算法且后者是为 I/O 内存编写的。事实证明，`cfb_imageblit()` 使用了 `movl` 指令，而 `sys_imageblit()` 显然没有。这似乎是 gcc 优化器的问题。DRM 的格式转换辅助函数可能也存在类似问题。

对 fbdev 的 `sys_()` 辅助函数和 DRM 的格式转换辅助函数进行基准测试和优化。在可以进一步优化的情况下，也许可以实现不同的算法。对于微优化，明确使用 `movl/movq` 指令。这可能需要特定架构的辅助函数（例如 `storel()` 和 `storeq()`）。

联系人：Thomas Zimmermann <tzimmermann@suse.de>

级别：中级

清理 drm_framebuffer_funcs 和 drm_mode_config_funcs.fb_create
-----------------------------------------------------------------

更多的驱动程序可以切换到 drm_gem_framebuffer 辅助函数。
各种阻碍因素：

- 需要首先切换到通用的脏页跟踪代码，使用 `drm_atomic_helper_dirtyfb`（例如 qxl）
- 需要切换到 `drm_fbdev_generic_setup()`，否则大量的自定义帧缓冲区设置代码无法删除
- 需要切换到 `drm_gem_fb_create()`，因为现在 `drm_gem_fb_create()` 对原子驱动程序的有效格式进行了检查
- 许多驱动程序继承了 `drm_framebuffer`，我们需要一个与嵌入兼容的版本的 `drm_gem_fb_create` 函数。也许可以命名为 `drm_gem_fb_create/_with_dirty/_with_funcs`，按需使用
联系人：Daniel Vetter

级别：中级

通用 fbdev defio 支持
----------------------

fbdev 核心中的 defio 支持代码有一些非常特定的要求，这意味着驱动程序需要为 fbdev 准备一个特殊的帧缓冲区。主要问题是它使用了 struct page 中的一些字段，这会破坏 shmem gem 对象（以及其他一些东西）。为了支持 defio，受影响的驱动程序需要使用影子缓冲区，这可能会增加 CPU 和内存开销。可能的解决方案是在 drm fbdev 模拟中编写我们自己的 defio mmap 代码。它需要完全包装现有的 mmap 操作，在执行写保护/mkwrite 技巧之后转发所有内容：

- 在 drm_fbdev_fb_mmap 辅助函数中，如果我们需要 defio，则将默认页面保护设置为写保护，如下所示：

      vma->vm_page_prot = pgprot_wrprotect(vma->vm_page_prot);

- 设置 mkwrite 和 fsync 回调，实现方式类似于核心 fbdev defio 的实现。这些都应该在普通的 pte 上工作，实际上不需要 struct page。
- 使用单独的数据结构（每个页面一位的位字段应该可以工作）来跟踪脏页，以避免覆盖 struct page。

最好为此编写一些 igt 测试用例。
联系人：Daniel Vetter, Noralf Tronnes

级别：高级

连接器注册/注销修复
-------------------

- 对于大多数连接器而言，直接从驱动程序代码调用 drm_connector_register/unregister 是没有实际作用的，drm_dev_register/unregister 已经处理了这些。我们可以移除所有这些调用。
- 对于 DP 驱动程序来说情况更复杂一些，因为我们需要在调用 drm_dp_aux_register 时已经注册了连接器。通过调用 drm_dp_aux_init 并按照内核文档推荐的方式将实际注册操作放入 late_register 回调来解决这个问题。

级别：中级

移除加载/卸载回调
-------------------

struct &drm_driver 中的加载/卸载回调非常中间层化，并且由于历史原因，它们的顺序是错误的（并且我们无法修正这一点），即在设置 &drm_driver 结构体和调用 drm_dev_register() 之间。
- 重构驱动程序，不再使用加载/卸载回调，而是直接在驱动程序的探测函数中编码加载/卸载序列。
- 一旦所有驱动程序都转换完毕，移除加载/卸载回调。
联系人：Daniel Vetter

级别：中级

替换 drm_detect_hdmi_monitor() 为 drm_display_info.is_hdmi
--------------------------------------------------------------

一旦解析了 EDID，显示器的 HDMI 支持信息就可以通过 drm_display_info.is_hdmi 获取。许多驱动程序仍然调用 drm_detect_hdmi_monitor() 来获取相同的信息，这效率较低。
审核每个调用 `drm_detect_hdmi_monitor()` 的单独驱动程序，并在适用的情况下切换到 `drm_display_info.is_hdmi`
联系人：Laurent Pinchart，各自驱动程序维护者

难度级别：中级

整合自定义驱动模式设置属性
--------------------------------------------

在原子模式设置（atomic modeset）出现之前，许多驱动程序都会创建自己的属性。原子模式设置带来了这样一个要求：不应使用自定义的、特定于驱动程序的属性。
对于此任务，我们的目标是引入核心辅助函数或重用现有的辅助函数：

一个快速且未经确认的例子列表：
引入核心辅助函数：
- 音频（amdgpu、intel、gma500、radeon）
- 亮度、对比度等（armada、nouveau）——仅限覆盖层（overlay）？
- 广播RGB（gma500、intel）
- 色键（armada、nouveau、rcar）——仅限覆盖层？
- 杂色（dither）（amdgpu、nouveau、radeon）——在不同驱动程序中有所不同
- 下扫描（underscan）系列（amdgpu、radeon、nouveau）

已经存在于核心中的：
- 色彩空间（colorspace）（sti）
- 电视格式名称、增强功能（gma500、intel）
- 电视过扫描、边缘等（gma500、intel）
- 图层顺序（zorder）（omapdrm）——与zpos相同？

联系人：Emil Velikov，各自驱动程序维护者

难度级别：中级

在整个代码库中使用 `struct iosys_map`
----------------------------------------

共享设备内存的指针存储在 `struct iosys_map` 中。每个实例都知道它是指向系统内存还是I/O内存。大部分DRM范围内的接口已经被转换为使用 `struct iosys_map`，但实现通常仍然使用原始指针。
任务是在适当的地方使用 `struct iosys_map`：
- 内存管理器应为dma-buf导入的缓冲区使用 `struct iosys_map`
- TTM可能从内部使用 `struct iosys_map` 中受益
- 帧缓冲区复制和位图（blitting）辅助函数应操作 `struct iosys_map`

联系人：Thomas Zimmermann <tzimmermann@suse.de>，Christian König，Daniel Vetter

难度级别：中级

审查所有驱动程序是否正确设置 `struct drm_mode_config.{max_width,max_height}`
--------------------------------------------------------------------------------------

`struct drm_mode_config.{max_width,max_height}` 中的值描述了支持的最大帧缓冲区大小。这是虚拟屏幕尺寸，但许多驱动程序将其视为物理分辨率的限制。
最大宽度取决于硬件的最大扫描线间距。最大高度取决于可寻址视频内存的数量。审查所有驱动程序以将这些字段初始化为正确的值。
联系人：Thomas Zimmermann <tzimmermann@suse.de>

难度：中级

在所有驱动程序中请求内存区域
-------------------------------

遍历所有驱动程序并添加代码以请求驱动程序使用的内存区域。这需要添加对 `request_mem_region()`、`pci_request_region()` 或类似函数的调用。尽可能使用辅助函数进行管理清理。
驱动程序在这方面做得非常不好，过去在 DRM 和 fbdev 驱动程序之间存在冲突。不过，这样做仍然是正确的。
联系人：Thomas Zimmermann <tzimmermann@suse.de>

难度：入门级

移除对 FB_DEVICE 的依赖
-------------------------------

许多 fbdev 驱动程序通过 sysfs 提供属性，因此依赖于 CONFIG_FB_DEVICE 被选中。审查每个驱动程序，并尝试使任何对 CONFIG_FB_DEVICE 的依赖成为可选的。至少，可以在驱动程序中通过 `#ifdef CONFIG_FB_DEVICE` 条件化相关代码。并非所有驱动程序都能完全移除 CONFIG_FB_DEVICE。
联系人：Thomas Zimmermann <tzimmermann@suse.de>

难度：入门级

移除 panel-simple 和 panel-edp 中 remove/shutdown 时的 disable/unprepare
----------------------------------------------------------------------------------

自从提交 d2aacaf07395（“drm/panel: 在 drm_panel 中检查是否已准备/启用”）以来，我们在 drm_panel 核心中增加了一个检查，以确保没有人重复调用 prepare/enable/disable/unprepare。最终这可能会变成一个 WARN_ON() 或者某种更明显的警告，但目前我们实际上希望它被触发，所以我们不希望这个警告太明显。
具体来说，在关闭时，对于 panel-edp 和 panel-simple，由于这些面板在关闭和移除时硬编码了对 `drm_panel_disable()` 和 `drm_panel_unprepare()` 的调用，无论面板状态如何都会调用它们，因此这个警告会被触发。在具有正确编码的 DRM 模式设置驱动程序的系统上，如果该驱动程序调用了 `drm_atomic_helper_shutdown()`，几乎可以肯定会导致该警告被触发。
不幸的是，在我们确定所有与这些面板一起使用的 DRM 模式设置驱动程序都正确调用了 `drm_atomic_helper_shutdown()` 之前，我们不能安全地移除 panel-edp 和 panel-simple 中的这些调用。此待办事项是验证所有与 panel-edp 和 panel-simple 一起使用的 DRM 模式设置驱动程序是否正确调用了 `drm_atomic_helper_shutdown()`，然后从这些面板中移除 disable/unprepare 的调用。或者，可以说服利益相关者这些调用是没问题的，并将 `drm_panel_disable()` 和 `drm_panel_unprepare()` 中的错误消息降级为调试级别的消息。
联系人：Douglas Anderson <dianders@chromium.org>

难度：中级

过渡到不再使用 mipi_dsi_*_write_seq()
---------------------------------------------

宏 `mipi_dsi_generic_write_seq()` 和 `mipi_dsi_dcs_write_seq()` 不直观，因为如果有错误，它们会从 *调用者* 的函数中返回。我们应该将所有调用者迁移到使用 `mipi_dsi_generic_write_seq_multi()` 和 `mipi_dsi_dcs_write_seq_multi()` 宏。
一旦所有调用者都完成了迁移，这些宏以及它们调用的函数 `mipi_dsi_generic_write_chatty()` 和 `mipi_dsi_dcs_write_buffer_chatty()` 可能就可以被移除了。或者，如果人们认为 `_multi()` 版本在某些情况下过于繁琐，我们可以保留 `mipi_dsi_*_write_seq()` 版本，但更改它们使其不在调用者处返回。
联系人：Douglas Anderson <dianders@chromium.org>

难度：入门级

核心重构
==========

使 panic 处理工作
-------------------

这是一个包含许多小部分的多样化任务：

* 目前无法测试 panic 路径，导致不断出现故障。主要问题是 panic 可以从硬中断上下文触发，因此所有与 panic 相关的回调都可以在硬中断上下文中运行。如果我们可以通过 drm debugfs 文件触发调用来至少测试 fbdev 辅助代码和驱动程序代码，那将是很好的。硬中断上下文可以通过使用 IPI 到本地处理器来实现。
* 存在大量不同的 panic 处理器混淆。DRM fbdev 模拟助手有自己的（已被移除），此外 fbcon 代码本身也有一个。我们需要确保它们不再互相争斗。
### 绕过方法

通过在进入DRM fbdev仿真辅助函数的各个入口点检查 ``oops_in_progress`` 来解决此问题。一个更干净的方法是将fbcon切换到 `线程化的printk支持 <https://lwn.net/Articles/800946/>`_。

* ``drm_can_sleep()`` 函数非常混乱。它掩盖了正常操作中的真实bug，并且对于panic路径也不是一个完整的解决方案。我们需要确保只有在真正发生panic时才返回true，并修复所有相关的问题。
* panic处理程序永远不能休眠，这也意味着它不能调用 ``mutex_lock()``。同样，它也不能无条件获取任何其他锁，即使是自旋锁（因为NMI和硬中断也可能导致panic）。我们需要确保不调用这样的路径，或者尝试锁定一切。这非常棘手。
* 一个干净的解决方案是在KMS中提供一个完全独立的panic输出支持，绕过当前的fbcon支持。参见 `[PATCH v2 0/3] drm: 添加panic处理 <https://lore.kernel.org/dri-devel/20190311174218.51899-1-noralf@tronnes.org/>`_。
* 在QR码中编码实际的oops和之前的dmesg可能会帮助解决“重要信息被滚动走”的问题。参见 `[RFC][PATCH] 使用QR码传输oops消息 <https://lore.kernel.org/lkml/1446217392-11981-1-git-send-email-alexandru.murtaza@intel.com/>`_，其中有一些可以重用的示例代码。

联系人：Daniel Vetter

难度级别：高级

### 清理debugfs支持

存在许多问题：

- 将驱动程序转换为支持 ``drm_debugfs_add_files()`` 函数，而不是 ``drm_debugfs_create_files()`` 函数。
- 改进延迟注册的debugfs，推广同样的debugfs预注册基础设施到连接器和CRTC。这样，驱动程序不再需要将其设置代码分成init和register两部分。
- 我们可能希望在核心中直接支持CRTC/连接器以及其他一些KMS对象上的debugfs文件。这些对象的功能中有drm_print支持来转储KMS状态，因此所有内容都已经具备。然后，->show()函数显然应该指向正确的对象。
- 当前的 ``drm_driver->debugfs_init`` 钩子只是旧的加载序列的一个遗留产物。DRM debugfs应该更像sysfs，在那里你可以在任何时候为一个对象创建属性/文件，而核心负责在注册/注销时发布/取消发布所有文件。驱动程序不应该关心这些技术细节，修复这一点（加上将drm_minor->drm_device移动）将允许我们移除debugfs_init。

联系人：Daniel Vetter

难度级别：中级

### 对象生命周期修复

这里有两个相关的问题：

- 清理各种 ->destroy 回调，这些回调通常都是相同的简单代码。
许多驱动程序错误地使用 `devm_kzalloc` 分配 DRM 模式设置对象，这会导致在驱动程序卸载时出现使用后释放的问题。即使对于集成在 SoC 上的硬件驱动程序，这也可能是一个严重的问题，因为 EPROBE_DEFERRED 回退机制的存在。
这两个问题可以通过切换到 `drmm_kzalloc()` 及其提供的各种便利封装函数来解决，例如 `drmm_crtc_alloc_with_planes()`、`drmm_universal_plane_alloc()` 等等。
联系人：Daniel Vetter

难度级别：中级

从 dma-buf 导入中移除自动页面映射
------------------------------------

在导入 dma-buf 时，dma-buf 和 PRIME 框架会自动将导入的页面映射到导入者的 DMA 区域。`drm_gem_prime_fd_to_handle()` 和 `drm_gem_prime_handle_to_fd()` 要求导入者调用 `dma_buf_attach()`，即使他们从未执行实际的设备 DMA，而只是通过 `dma_buf_vmap()` 进行 CPU 访问。这对于不支持 DMA 操作的 USB 设备来说是个问题。
为了解决这个问题，应从缓冲区共享代码中移除自动页面映射。修复这个问题比较复杂，因为导入/导出缓存也与 `&drm_gem_object.import_attach` 相关联。目前我们通过查找 USB 主机控制器设备（只要它支持 DMA）来临时解决这个问题。否则导入可能会无谓地失败。
联系人：Thomas Zimmermann <tzimmermann@suse.de>，Daniel Vetter

难度级别：高级

更好的测试
===========

使用 Kernel Unit Testing (KUnit) 框架添加单元测试
----------------------------------------------------

`KUnit <https://www.kernel.org/doc/html/latest/dev-tools/kunit/index.html>`_ 提供了一个用于 Linux 内核中的单元测试通用框架。拥有一个测试套件可以更早地识别回归。
一个很好的候选对象是 `drm_format_helper.c` 中的格式转换辅助函数。
联系人：Javier Martinez Canillas <javierm@redhat.com>

难度级别：中级

清理并记录前自测套件
---------------------

一些 KUnit 测试套件（drm_buddy、drm_cmdline_parser、drm_damage_helper、drm_format、drm_framebuffer、drm_dp_mst_helper、drm_mm、drm_plane_helper 和 drm_rect）是在引入 KUnit 时从之前的自测套件转换过来的。
这些套件之前几乎没有文档，并且目标与单元测试有所不同。尝试确定每个测试套件中的测试实际上在测试什么，以及是否适合单元测试，如果不适合则删除，如果适合则进行文档化，这将非常有帮助。
联系人：Maxime Ripard <mripard@kernel.org>

难度级别：中级

为 DRM 启用 Trinity
--------------------

并修复由此产生的问题。这将是非常有趣的。
难度级别：高级

使 i-g-t 中的 KMS 测试具有通用性
---------------------------------

i915 驱动程序团队维护了一套针对 i915 DRM 驱动程序的广泛测试套件，包括大量针对模式设置 API 的边缘情况测试用例。如果这些测试（至少那些不依赖于特定于 Intel 的 GEM 特性的测试）能够适用于任何 KMS 驱动程序，那将非常棒。
### 运行非i915上的i-g-t测试的基础工作已完成，目前缺少的是大规模转换。对于模式设置测试，我们首先需要一些基础设施来使用哑缓冲区（dumb buffers）处理非平铺缓冲区，以便能够运行所有与非i915相关的模式设置测试。
级别：高级

#### 扩展虚拟测试驱动（VKMS）
---------------------------------

详见 :ref:`VKMS <vkms>` 的文档。这是一个理想的实习任务，因为它只需要一个虚拟机，并且可以根据可用时间调整任务规模。
级别：详见详情

#### 背光重构
---------------------

背光驱动具有三重启用/禁用状态，这有些过度设计。计划修复如下：

1. 在所有地方推广使用 `backlight_enable()` 和 `backlight_disable()` 辅助函数。这已经开始进行了。
2. 只查看上述辅助函数设置的三个状态位中的一个。
3. 移除其他两个状态位。
联系人：Daniel Vetter
级别：中级

### 驱动特定任务
===============

#### AMD DC 显示驱动
---------------------

AMD DC 是从Vega开始的AMD设备的显示驱动。已经做了很多清理工作，但仍有很多工作要做。详见 `drivers/gpu/drm/amd/display/TODO` 中的任务。
联系人：Harry Wentland, Alex Deucher

#### 启动画面
==========

现在已经有支持内部DRM客户端的机制，使得可以继续进行因基于fbdev编写而被拒绝的启动画面工作。
- [v6,8/8] drm/client: Hack: 添加启动画面示例
  https://patchwork.freedesktop.org/patch/306579/

- [RFC PATCH v2 00/13] 基于内核的启动画面
  https://lore.kernel.org/r/20171213194755.3409-1-mstaudt@suse.de

联系人：Sam Ravnborg
级别：高级

#### 多个内部面板设备的亮度处理
============================================================

在x86/ACPI设备上，可能存在多个背光固件接口：（ACPI）视频、厂商特定以及其他接口。此外，KMS驱动还可以直接/本地（PWM）寄存器编程。
为了解决这个问题，x86/ACPI 上使用的背光驱动程序会调用 `acpi_video_get_backlight_type()` 函数，该函数具有选择使用哪个背光接口的启发式算法（+ 特殊处理）。不匹配返回类型的背光驱动程序不会注册自己，这样就只有一个背光设备被注册（在单 GPU 配置中，请参见下文）。

目前，这基本上假定系统上只有一个（内部）面板。

在具有两个面板的系统上，这可能会成为一个问题，具体取决于 `acpi_video_get_backlight_type()` 选择的接口：

1. 本机（native）：在这种情况下，KMS 驱动程序需要知道哪个背光设备属于哪个输出，因此一切都应该正常工作。
2. 视频（video）：这种方法确实支持控制多个背光设备，但需要做一些工作来获取输出与背光设备之间的映射关系。

上述假设两个面板都需要相同的背光接口类型。
如果系统中有多个面板且这两个面板需要不同类型的控制，则会出现问题。例如，一个面板需要 ACPI 视频背光控制，而另一个面板则使用本机背光控制。在这种情况下，目前只会根据 `acpi_video_get_backlight_type()` 的返回值注册所需的两个背光设备中的一个。

如果这种（理论上的）情况真的出现，那么支持这种情况将需要做一些工作。一种可能的解决方案是将设备和连接器名称传递给 `acpi_video_get_backlight_type()`，以便它可以处理这种情况。

需要注意的是，在双 GPU 笔记本电脑设置中有mux的情况下，用户空间已经看到了两个面板。在这些系统上，我们可能会看到两个本机背光设备；或者两个本机背光设备。用户空间已经有代码来通过检测相关面板是否处于活动状态（即mux指向的方向）来处理这种情况，然后使用那个背光设备。然而，用户空间假定只有一个面板。它只选择两个背光设备中的一个，并且只使用那个。

需要注意的是，所有我知道的用户空间代码都硬编码假定只有一个面板。

在最近更改之前，对于单个面板（单 GPU 笔记本电脑）不注册多个（例如视频 + 本机） `/sys/class/backlight` 设备时，用户空间会看到控制相同背光的所有背光设备。
为了解决这个问题，用户空间必须始终在`/sys/class/backlight`下选择一个首选设备，并忽略其他设备。因此，为了支持多个面板的亮度控制，用户空间也需要进行更新。计划通过在drm_connector对象中添加“显示亮度”属性来通过KMS API实现亮度控制。这解决了与`/sys/class/backlight` API相关的一些问题，包括无法将sysfs背光设备映射到特定连接器的问题。任何需要为具有多个面板的设备增加亮度控制支持的用户空间更改都应基于这个新的KMS属性。

联系人：Hans de Goede

级别：高级

缓冲区老化或其他损坏累积算法
=================================

对于每个缓冲区上传的驱动程序，需要处理缓冲区损坏（而不是像每个平面或每个CRTC上传的驱动程序那样处理帧损坏），但目前没有获取缓冲区年龄或其他损坏累积算法的支持。因此，损坏助手在页面翻转后发现与平面关联的帧缓冲区发生变化时，会回退到完整的平面更新。驱动程序通过设置`&drm_plane_state.ignore_damage_clips`为true来指示`drm_atomic_helper_damage_iter_init()`和`drm_atomic_helper_damage_iter_next()`帮助函数忽略损坏剪辑。这应该改进以使每个缓冲区上传的驱动程序能够正确地跟踪损坏。
关于损坏跟踪的更多信息和学习资料可以在 :ref:`damage_tracking_properties` 中找到。

联系人：Javier Martinez Canillas <javierm@redhat.com>

级别：高级

非DRM领域
==========

将fbdev驱动程序转换为DRM
----------------------------

有许多旧硬件的fbdev驱动程序。一些硬件已经过时，但有些仍然提供了足够好的帧缓冲区。那些仍然有用的驱动程序应当被转换为DRM并从fbdev中移除。
非常简单的fbdev驱动程序最好从一个新的DRM驱动程序开始转换。简单的KMS辅助工具和SHMEM应该能够处理现有的硬件。新驱动程序的回调函数可以从现有的fbdev代码中填充。
更复杂的fbdev驱动程序可以借助DRM fbconv助手逐步重构为DRM驱动程序。这些助手提供了DRM核心基础设施与fbdev驱动程序接口之间的过渡层。在fbconv助手之上创建一个新的DRM驱动程序，复制fbdev驱动程序，并将其与DRM代码挂钩。Thomas Zimmermann的fbconv树中有几个fbdev驱动程序的例子，以及该过程的教程。结果是一个原始的DRM驱动程序，能够运行X11和Weston。

.. [4] https://gitlab.freedesktop.org/tzimmermann/linux/tree/fbconv  
.. [5] https://gitlab.freedesktop.org/tzimmermann/linux/blob/fbconv/drivers/gpu/drm/drm_fbconv_helper.c

联系人：Thomas Zimmermann <tzimmermann@suse.de>

级别：高级
