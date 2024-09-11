.. _vkms:

==========================================
drm/vkms 虚拟内核模式设置
==========================================

.. kernel-doc:: drivers/gpu/drm/vkms/vkms_drv.c
   :doc: vkms (虚拟内核模式设置)

设置
=====

可以通过以下步骤设置 VKMS 驱动：

要检查 VKMS 是否已加载，请运行以下命令：

```
lsmod | grep vkms
```

这应该会列出 VKMS 驱动。如果没有输出，那么你需要启用并加载 VKMS 驱动。
确保在你的内核配置文件中将 VKMS 驱动设置为可加载模块。执行以下命令：

```
make nconfig
```

进入 `设备驱动程序 > 图形支持`

启用 `虚拟 KMS（实验性）`

编译并构建内核以使更改生效。
现在，为了加载驱动程序，使用以下命令：

```
sudo modprobe vkms
```

现在运行 `lsmod` 命令，VKMS 驱动将会被列出。
你也可以在 `dmesg` 日志中观察到驱动程序的加载情况。
VKMS 驱动具有模拟不同硬件种类的可选功能，这些功能作为模块选项暴露出来。你可以使用 `modinfo` 命令查看 vkms 的模块选项：

```
modinfo vkms
```

模块选项在测试时非常有用，并且可以在加载 vkms 时启用模块。
例如，要加载带有光标功能的 vkms，可以使用以下命令：

```
sudo modprobe vkms enable_cursor=1
```

要卸载驱动程序，使用以下命令：

```
sudo modprobe -r vkms
```

使用 IGT 进行测试
================

IGT GPU 工具是一个专门用于调试和开发 DRM 驱动程序的测试套件。
可以从这里安装 IGT 工具：`<https://gitlab.freedesktop.org/drm/igt-gpu-tools>`_
测试需要在没有合成器的情况下运行，因此你需要切换到文本模式。你可以通过以下命令实现这一点：

```
sudo systemctl isolate multi-user.target
```

要返回图形模式，执行以下命令：

```
sudo systemctl isolate graphical.target
```

一旦你处于文本模式下，你可以使用 `--device` 开关或 IGT_DEVICE 变量来指定要测试的驱动程序的设备过滤器。IGT_DEVICE 也可以与 run-test.sh 脚本一起使用，以运行特定驱动程序的测试：

```
sudo ./build/tests/<测试名称> --device "sys:/sys/devices/platform/vkms"
sudo IGT_DEVICE="sys:/sys/devices/platform/vkms" ./build/tests/<测试名称>
sudo IGT_DEVICE="sys:/sys/devices/platform/vkms" ./scripts/run-tests.sh -t <测试名称>
```

例如，要测试写回库的功能，我们可以运行 kms_writeback 测试：

```
sudo ./build/tests/kms_writeback --device "sys:/sys/devices/platform/vkms"
sudo IGT_DEVICE="sys:/sys/devices/platform/vkms" ./build/tests/kms_writeback
sudo IGT_DEVICE="sys:/sys/devices/platform/vkms" ./scripts/run-tests.sh -t kms_writeback
```

如果你不想运行整个测试，还可以运行子测试：

```
sudo ./build/tests/kms_flip --run-subtest basic-plain-flip --device "sys:/sys/devices/platform/vkms"
sudo IGT_DEVICE="sys:/sys/devices/platform/vkms" ./build/tests/kms_flip --run-subtest basic-plain-flip
```

待办事项
====

如果你有兴趣完成下面列出的任何一项任务，请与 VKMS 维护者分享你的兴趣。

IGT 更好的支持
------------------

调试：

- kms_plane：某些测试用例由于捕获 CRC 时超时而失败；

虚拟硬件（无垂直同步）模式：
- VKMS 已经支持通过 hrtimers 模拟垂直同步，这可以通过 kms_flip 测试进行验证。在某种程度上，我们可以说 VKMS 已经模仿了真实硬件的垂直同步。然而，我们也有一些不支持垂直同步中断并且立即完成页面翻转事件的虚拟硬件。在这种情况下，合成器开发者可能会在虚拟硬件上创建忙循环。支持虚拟硬件行为对 VKMS 来说是有用的，因为这可以帮助合成器开发者在多种场景下测试他们的特性。

添加平面功能
------------------

有很多平面功能我们可以增加支持：

- 添加背景颜色 KMS 属性 [适合入门]
- 缩放
### 额外的缓冲区格式，特别是视频用的YUV格式如NV12
低/高bpp的RGB格式也很有趣。
- 异步更新（目前仅通过使用传统光标API在光标平面上实现）
对于所有这些功能，我们还需要审查igt测试覆盖情况，并确保所有相关的igt测试用例都能在vkms上运行。它们是实习项目的不错选择。

### 运行时配置

我们希望能够在不重新加载模块的情况下重新配置vkms实例。使用/测试案例包括：
- 热插拔/热移除连接器（以便测试组合器处理DP MST的能力）
- 配置平面/控制器/连接器（首先需要一些代码支持多个此类对象）
- 更改输出配置：插入/拔出屏幕、更改EDID、允许更改刷新率
目前提出的解决方案是通过configfs暴露vkms配置。所有现有的模块选项也应该通过configfs支持。

### 回写支持

- 写回和CRC捕获操作共享composer_enabled布尔值以确保垂直同步。当这些操作一起工作时，可能需要对composer状态进行引用计数才能正确工作。
[适合入门]

- 添加支持克隆的写回输出及相关测试用例，在IGT kms_writeback中使用克隆输出。
作为 V4L 设备。这对于在特殊的 VKMS 配置上调试合成器非常有用，以便开发者能够看到实际发生的情况。

输出特性
--------------

- 支持可变刷新率/FreeSync。这可能需要 Prime 缓冲共享支持，以便我们可以通过 VGem 围栏来模拟测试中的渲染。同时还需要支持指定 EDID。
- 添加链路状态支持，以便当例如 DisplayPort 链路故障时，合成器可以验证其运行时回退机制。

CRC API 改进
--------------------

- 优化 CRC 计算 `compute_crc()` 和平面混合 `blend()`。

使用 eBPF 的原子检查
-------------------------------

原子驱动有许多限制，并没有通过例如可能的属性值以显式的形式暴露给用户空间。用户空间只能通过原子 IOCTL 来查询这些限制，可能使用 TEST_ONLY 标志。尝试为所有这些限制添加可配置代码以允许合成器进行测试将是徒劳的。相反，我们可以添加对 eBPF 的支持来验证任何类型的原子状态，并实现一个包含不同限制的库。这需要许多特性（平面合成、多个输出等）已经启用才能有意义。
