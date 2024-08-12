SPDX 许可证标识符: GPL-2.0

===============================
Linux 内核的 DPLL 子系统
===============================

DPLL
====

PLL（Phase Locked Loop，锁相环）是一种电子电路，它使设备的时钟信号与外部时钟信号同步。这样可以有效地使设备运行在与 PLL 输入提供的相同的时钟信号频率上。
DPLL（Digital Phase Locked Loop，数字锁相环）是一种集成电路，在普通 PLL 行为的基础上，还包括了数字相位检测器，并且可能在环路中具有数字分频器。因此，DPLL 的输入和输出频率可能是可配置的。
子系统
=========

DPLL 子系统的首要目的是提供一个通用接口来配置使用任何类型的数字 PLL 的设备，这些设备可以使用不同的输入信号源进行同步，以及支持不同类型的输出。
主要接口基于 NETLINK_GENERIC 协议，并定义了一个事件监控多播组。
设备对象
=============

单个 DPLL 设备对象表示单一的数字 PLL 电路及其连接的一系列引脚。
它会响应 netlink 命令中的 `do` 请求（命令 `DPLL_CMD_DEVICE_GET`），报告支持的操作模式及当前状态；通过同一命令的 `dump` netlink 请求列出已注册在子系统中的所有 DPLL。
更改 DPLL 设备的配置是通过 netlink 命令 `DPLL_CMD_DEVICE_SET` 的 `do` 请求完成的。
设备句柄为 `DPLL_A_ID`，需要提供这个句柄来获取或设置系统中特定设备的配置。可以通过 `DPLL_CMD_DEVICE_GET` 的 `dump` 请求或 `DPLL_CMD_DEVICE_ID_GET` 的 `do` 请求获得该句柄，其中必须提供能够唯一匹配到一个设备的属性。
引脚对象
==========

引脚是一个形态不固定的对象，它可以代表输入也可以代表输出，既可以是设备内部组件，也可以是外部连接的。
每个 DPLL 的引脚数量不同，但通常一个 DPLL 设备会有多个引脚。
针脚的属性、功能和状态通过 netlink 的 `do` 请求与 ``DPLL_CMD_PIN_GET`` 命令响应提供给用户。
也可以通过 ``DPLL_CMD_PIN_GET`` 命令的 `dump` 请求列出系统中注册的所有针脚。
可以通过 netlink 的 ``DPLL_CMD_PIN_SET`` 命令的 `do` 请求来改变针脚的配置。
针脚句柄是一个 ``DPLL_A_PIN_ID``，应当提供它以获取或设置系统中特定针脚的配置。这个句柄可以通过 ``DPLL_CMD_PIN_GET`` 命令的 `dump` 请求或 ``DPLL_CMD_PIN_ID_GET`` 命令的 `do` 请求获得，在后一种情况下，用户提供的属性将导致匹配一个针脚。

### 针脚选择

通常，选定的针脚（其信号驱动 dpll 设备）可以从 ``DPLL_A_PIN_STATE`` 属性中获取，并且对于任何 dpll 设备来说，只有一个针脚应该处于 ``DPLL_PIN_STATE_CONNECTED`` 状态。
针脚的选择可以手动完成或自动完成，这取决于硬件能力和活动的 dpll 设备工作模式（``DPLL_A_MODE`` 属性）。结果是，每种模式在可用的针脚状态以及用户可以为 dpll 设备请求的状态方面都存在差异。
在手动模式（``DPLL_MODE_MANUAL``）下，用户可以请求或接收以下针脚状态之一：

- ``DPLL_PIN_STATE_CONNECTED`` — 使用该针脚驱动 dpll 设备
- ``DPLL_PIN_STATE_DISCONNECTED`` — 该针脚不用于驱动 dpll 设备

在自动模式（``DPLL_MODE_AUTOMATIC``）下，用户可以请求或接收以下针脚状态之一：

- ``DPLL_PIN_STATE_SELECTABLE`` — 应将该针脚视为自动选择算法的有效输入
- ``DPLL_PIN_STATE_DISCONNECTED`` — 不应将该针脚视为自动选择算法的有效输入

在自动模式（``DPLL_MODE_AUTOMATIC``）下，一旦自动选择算法锁定 dpll 设备的一个输入，用户只能接收到针脚状态 ``DPLL_PIN_STATE_CONNECTED``。

### 共享针脚

单个针脚对象可以连接到多个 dpll 设备上。
那么有两种类型的配置选项：

1) 设置在针脚上 — 配置影响所有针脚所注册的 dpll 设备（例如，``DPLL_A_PIN_FREQUENCY``），
2) 设置在针脚-dpll 组合上 — 配置仅影响选定的 dpll 设备（例如，``DPLL_A_PIN_PRIO``，``DPLL_A_PIN_STATE``，``DPLL_A_PIN_DIRECTION``）

### 多路复用型针脚

针脚可以是多路复用型的，它汇聚子针脚并作为针脚多路复用器。一个或多个针脚与多路复用型针脚注册，而不是直接与 dpll 设备注册。
与MUX型引脚注册的引脚为用户提供了额外的嵌套属性`DPLL_A_PIN_PARENT_PIN`，对应于它们注册时的每个父级引脚。
如果一个引脚与多个父级引脚注册，则其行为类似于多输出复用器。在这种情况下，`DPLL_CMD_PIN_GET`的输出将包含多个与每个父级相关的引脚-父级嵌套属性及其当前状态，例如：

        'pin': [{{
          'clock-id': 282574471561216,
          'module-name': 'ice',
          'capabilities': 4,
          'id': 13,
          'parent-pin': [
          {'parent-id': 2, 'state': 'connected'},
          {'parent-id': 3, 'state': 'disconnected'}
          ],
          'type': 'synce-eth-port'
          }}]

一次只能有一个子引脚向父级MUX型引脚提供信号，选择是通过使用`DPLL_A_PIN_PARENT`嵌套属性来请求改变希望的父级上的子引脚状态实现的。Netlink `设置父级引脚状态`消息格式示例：

  ========================== =============================================
  ``DPLL_A_PIN_ID``          子引脚ID
  ``DPLL_A_PIN_PARENT_PIN``  请求与父级引脚相关配置的嵌套属性
    ``DPLL_A_PIN_PARENT_ID`` 父级引脚ID
    ``DPLL_A_PIN_STATE``     在父级上请求的引脚状态
  ========================== =============================================

### 引脚优先级

某些设备可能提供自动引脚选择模式的能力（`DPLL_A_MODE`属性的枚举值`DPLL_MODE_AUTOMATIC`）。
通常，自动选择是在硬件级别执行的，这意味着只有直接连接到DPLL的引脚才能用于自动输入引脚选择。
在自动选择模式下，用户不能手动选择设备的输入引脚，相反，用户应为所有直接连接的引脚提供一个优先级`DPLL_A_PIN_PRIO`，设备会挑选最高优先级的有效信号并用它来控制DPLL设备。Netlink `设置父级DPLL上的优先级`消息格式示例：

  ============================ =============================================
  ``DPLL_A_PIN_ID``            配置的引脚ID
  ``DPLL_A_PIN_PARENT_DEVICE`` 请求与父级DPLL设备相关配置的嵌套属性
    ``DPLL_A_PIN_PARENT_ID``   父级DPLL设备ID
    ``DPLL_A_PIN_PRIO``        在父级DPLL上请求的引脚优先级
  ============================ =============================================

MUX型引脚的子引脚不具备自动输入引脚选择功能，为了配置MUX型引脚的活动输入，用户需要在父级引脚上请求子引脚的期望状态，如“MUX型引脚”章节所述。

### 相位偏移测量和调整

设备可能具备测量引脚与其父级DPLL设备之间的信号相位差的能力。如果支持引脚-DPLL相位偏移测量，那么应当为每个父级DPLL设备提供`DPLL_A_PIN_PHASE_OFFSET`属性。
设备也可能具备调整引脚上信号相位的能力。如果支持引脚相位调整，引脚句柄应通过`DPLL_CMD_PIN_GET`响应提供最小和最大值给用户，这些值通过`DPLL_A_PIN_PHASE_ADJUST_MIN`和`DPLL_A_PIN_PHASE_ADJUST_MAX`属性提供。配置的相位调整值由引脚的`DPLL_A_PIN_PHASE_ADJUST`属性提供，并且可以通过带有`DPLL_CMD_PIN_SET`命令的同一属性请求值的更改。
=============================== ======================================
  ``DPLL_A_PIN_ID``               配置的引脚ID
  ``DPLL_A_PIN_PHASE_ADJUST_MIN`` 相位调整属性的最小值
  ``DPLL_A_PIN_PHASE_ADJUST_MAX`` 相位调整属性的最大值
  ``DPLL_A_PIN_PHASE_ADJUST``     在父级DPLL设备上配置的相位调整值
  ``DPLL_A_PIN_PARENT_DEVICE``    请求特定父级DPLL设备配置的嵌套属性
    ``DPLL_A_PIN_PARENT_ID``      父级DPLL设备ID
    ``DPLL_A_PIN_PHASE_OFFSET``   测量的引脚与父级DPLL设备之间的相位差
  =============================== ======================================

所有与相位相关的值均以皮秒表示，代表信号相位之间的时间差。负值意味着引脚上的信号相位比DPLL的信号更早；正值则意味着引脚上的信号相位比DPLL的信号更晚。
相位调整值（包括最小值和最大值）是整数，而测量的相位偏移值是具有三位小数点精度的分数，应该除以`DPLL_PIN_PHASE_OFFSET_DIVIDER`获取整数部分，模除获取小数部分。

### 配置命令组

配置命令用于获取已注册DPLL设备（及其引脚）的信息以及设置设备或引脚的配置。
由于DPLL设备必须被抽象并反映真实的硬件，因此无法从用户空间通过netlink添加新的DPLL设备，并且每个设备都应由其驱动程序进行注册。
所有的netlink命令都需要`GENL_ADMIN_PERM`权限。这是为了防止来自未经授权的用户空间应用程序的垃圾信息发送或拒绝服务攻击。
Netlink命令列表及其可能的属性
================================

用于标识DPLL设备使用的命令类型的常量使用`DPLL_CMD_`前缀和后缀，并根据命令的目的来命名。
与DPLL设备相关的属性使用`DPLL_A_`前缀和后缀，并根据属性的目的来命名。

| 命令 | 描述 |
| --- | --- |
| `DPLL_CMD_DEVICE_ID_GET` | 获取设备ID的命令 |
|   `DPLL_A_MODULE_NAME` | 注册者的模块名称属性 |
|   `DPLL_A_CLOCK_ID` | 根据IEEE 1588标准定义的独特时钟标识符（EUI-64）属性 |
|   `DPLL_A_TYPE` | DPLL设备类型属性 |

| 命令 | 描述 |
| --- | --- |
| `DPLL_CMD_DEVICE_GET` | 获取设备信息或列出系统中可用设备的命令 |
|   `DPLL_A_ID` | 独特的DPLL设备ID属性 |
|   `DPLL_A_MODULE_NAME` | 注册者的模块名称属性 |
|   `DPLL_A_CLOCK_ID` | 根据IEEE 1588标准定义的独特时钟标识符（EUI-64）属性 |
|   `DPLL_A_MODE` | 选择模式属性 |
|   `DPLL_A_MODE_SUPPORTED` | 可用的选择模式属性 |
|   `DPLL_A_LOCK_STATUS` | DPLL设备锁定状态属性 |
|   `DPLL_A_TEMP` | 设备温度信息属性 |
|   `DPLL_A_TYPE` | DPLL设备类型属性 |

| 命令 | 描述 |
| --- | --- |
| `DPLL_CMD_DEVICE_SET` | 设置DPLL设备配置的命令 |
|   `DPLL_A_ID` | DPLL设备内部索引属性 |
|   `DPLL_A_MODE` | 要配置的选择模式属性 |

用于标识针脚使用的命令类型的常量使用`DPLL_CMD_PIN_`前缀和后缀，并根据命令的目的来命名。
与针脚相关的属性使用`DPLL_A_PIN_`前缀和后缀，并根据属性的目的来命名。

| 命令 | 描述 |
| --- | --- |
| `DPLL_CMD_PIN_ID_GET` | 获取针脚ID的命令 |
|   `DPLL_A_PIN_MODULE_NAME` | 注册者的模块名称属性 |
|   `DPLL_A_PIN_CLOCK_ID` | 根据IEEE 1588标准定义的独特时钟标识符（EUI-64）属性 |
|   `DPLL_A_PIN_BOARD_LABEL` | 注册者提供的针脚板标签属性 |
|   `DPLL_A_PIN_PANEL_LABEL` | 注册者提供的针脚面板标签属性 |
|   `DPLL_A_PIN_PACKAGE_LABEL` | 注册者提供的针脚封装标签属性 |
|   `DPLL_A_PIN_TYPE` | 针脚类型属性 |

| 命令 | 描述 |
| --- | --- |
| `DPLL_CMD_PIN_GET` | 获取针脚信息或列出系统中可用针脚的命令 |
|   `DPLL_A_PIN_ID` | 独特的针脚ID属性 |
|   `DPLL_A_PIN_MODULE_NAME` | 注册者的模块名称属性 |
|   `DPLL_A_PIN_CLOCK_ID` | 根据IEEE 1588标准定义的独特时钟标识符（EUI-64）属性 |
|   `DPLL_A_PIN_BOARD_LABEL` | 注册者提供的针脚板标签属性 |
|   `DPLL_A_PIN_PANEL_LABEL` | 注册者提供的针脚面板标签属性 |
|   `DPLL_A_PIN_PACKAGE_LABEL` | 注册者提供的针脚封装标签属性 |
|   `DPLL_A_PIN_TYPE` | 针脚类型属性 |
|   `DPLL_A_PIN_FREQUENCY` | 针脚当前频率属性 |
|   `DPLL_A_PIN_FREQUENCY_SUPPORTED` | 支持的频率嵌套属性 |
|     `DPLL_A_PIN_ANY_FREQUENCY_MIN` | 频率最小值属性 |
|     `DPLL_A_PIN_ANY_FREQUENCY_MAX` | 频率最大值属性 |
|   `DPLL_A_PIN_PHASE_ADJUST_MIN` | 相位调整最小值属性 |
|   `DPLL_A_PIN_PHASE_ADJUST_MAX` | 相位调整最大值属性 |
|   `DPLL_A_PIN_PHASE_ADJUST` | 在父设备上配置的相位调整值属性 |
|   `DPLL_A_PIN_PARENT_DEVICE` | 对于针脚连接的每个父设备的嵌套属性 |
|     `DPLL_A_PIN_PARENT_ID` | 父DPLL设备ID属性 |
|     `DPLL_A_PIN_PRIO` | 在DPLL设备上的针脚优先级属性 |
|     `DPLL_A_PIN_STATE` | 在父DPLL设备上的针脚状态属性 |
|     `DPLL_A_PIN_DIRECTION` | 在父DPLL设备上的针脚方向属性 |
|     `DPLL_A_PIN_PHASE_OFFSET` | 针脚与父DPLL之间的测量相位差属性 |
|   `DPLL_A_PIN_PARENT_PIN` | 对于针脚连接的每个父针脚的嵌套属性 |
|     `DPLL_A_PIN_PARENT_ID` | 父针脚ID属性 |
|     `DPLL_A_PIN_STATE` | 在父针脚上的针脚状态属性 |
|   `DPLL_A_PIN_CAPABILITIES` | 针脚能力掩码属性 |

| 命令 | 描述 |
| --- | --- |
| `DPLL_CMD_PIN_SET` | 设置针脚配置的命令 |
|   `DPLL_A_PIN_ID` | 独特的针脚ID属性 |
|   `DPLL_A_PIN_FREQUENCY` | 请求的针脚频率属性 |
|   `DPLL_A_PIN_PHASE_ADJUST` | 在父设备上请求的相位调整值属性 |
|   `DPLL_A_PIN_PARENT_DEVICE` | 对于每个父DPLL设备配置请求的嵌套属性 |
|     `DPLL_A_PIN_PARENT_ID` | 父DPLL设备ID属性 |
|     `DPLL_A_PIN_DIRECTION` | 请求的针脚方向属性 |
|     `DPLL_A_PIN_PRIO` | 请求的在DPLL设备上的针脚优先级属性 |
|     `DPLL_A_PIN_STATE` | 请求的在DPLL设备上的针脚状态属性 |
|   `DPLL_A_PIN_PARENT_PIN` | 对于每个父针脚配置请求的嵌套属性 |
|     `DPLL_A_PIN_PARENT_ID` | 父针脚ID属性 |
|     `DPLL_A_PIN_STATE` | 请求的在父针脚上的针脚状态属性 |

Netlink转储请求
==================

`DPLL_CMD_DEVICE_GET`和`DPLL_CMD_PIN_GET`命令能够处理转储类型的netlink请求，在这种情况下，响应格式与它们的执行请求相同，但是返回系统中所有已注册的设备或针脚的信息。
设置命令格式
==================

`DPLL_CMD_DEVICE_SET` - 为了针对一个DPLL设备，用户需要提供`DPLL_A_ID`，即系统中DPLL设备的唯一标识符，以及要配置的参数（如`DPLL_A_MODE`）。
`DPLL_CMD_PIN_SET` - 为了针对一个针脚，用户必须提供`DPLL_A_PIN_ID`，即系统中针脚的唯一标识符。同时还需要添加要配置的针脚参数。
如果配置了`DPLL_A_PIN_FREQUENCY`，这将影响与该引脚相连的所有dpll设备，这就是为什么频率属性不应该被包含在`DPLL_A_PIN_PARENT_DEVICE`中的原因。
其他属性如`DPLL_A_PIN_PRIO`、`DPLL_A_PIN_STATE`或`DPLL_A_PIN_DIRECTION`必须被包含在`DPLL_A_PIN_PARENT_DEVICE`中，因为它们的配置仅针对由`DPLL_A_PIN_PARENT_ID`属性指定的一个父dpll，该属性也必须在这个嵌套结构内。
对于MUX类型的引脚，`DPLL_A_PIN_STATE`属性以类似的方式配置，即将所需状态包含在`DPLL_A_PIN_PARENT_PIN`嵌套属性中，并将目标父引脚ID包含在`DPLL_A_PIN_PARENT_ID`中。
一般来说，可以同时配置多个参数，但在内部每个参数更改都将单独触发，且配置顺序没有任何保证。
预定义的配置枚举值
===============================
.. kernel-doc:: include/uapi/linux/dpll.h

通知
=============

dpll设备可以提供关于设备状态变化的通知，例如锁定状态变化、输入/输出变化或其他报警。
有一个多播组用于通过netlink套接字向用户空间应用程序发送通知：`DPLL_MCGRP_MONITOR`。

通知消息：

  ============================== =====================================
  `DPLL_CMD_DEVICE_CREATE_NTF`   dpll设备创建
  `DPLL_CMD_DEVICE_DELETE_NTF`   dpll设备删除
  `DPLL_CMD_DEVICE_CHANGE_NTF`   dpll设备变更
  `DPLL_CMD_PIN_CREATE_NTF`      dpll引脚创建
  `DPLL_CMD_PIN_DELETE_NTF`      dpll引脚删除
  `DPLL_CMD_PIN_CHANGE_NTF`      dpll引脚变更
  ============================== =====================================

事件格式与相应的获取命令相同。
`DPLL_CMD_DEVICE_`事件的格式与`DPLL_CMD_DEVICE_GET`的响应相同。
`DPLL_CMD_PIN_`事件的格式与`DPLL_CMD_PIN_GET`的响应相同。
设备驱动实现
============================

设备通过调用dpll_device_get()分配。使用相同的参数进行第二次调用不会创建新对象，而是为给定参数提供的先前创建的设备提供指针，并增加该对象的引用计数。
通过调用dpll_device_put()来释放设备，它首先减少引用计数，一旦引用计数清零，对象就会被销毁。
设备应当实现一系列操作，并通过 `dpll_device_register()` 进行注册，此时它对用户变得可用。多个驱动实例可以通过 `dpll_device_get()` 获取对该设备的引用，同时也可以使用它们自己的 `ops` 和私有数据来注册 `dpll` 设备。

引脚是通过 `dpll_pin_get()` 单独分配的，其工作方式类似于 `dpll_device_get()`。函数首先创建一个对象，然后对于每次带有相同参数的调用，仅增加该对象的引用计数。同样地，`dpll_pin_put()` 的工作方式也类似于 `dpll_device_put()`。

一个引脚可以根据硬件需求与父 `dpll` 设备或父引脚进行注册。每个注册都需要注册者提供一组引脚回调函数以及用于调用这些回调函数的私有数据指针：

- `dpll_pin_register()` —— 使用 `dpll` 设备注册引脚，
- `dpll_pin_on_pin_register()` —— 将引脚注册到另一个MUX类型的引脚上

关于添加或移除 `dpll` 设备的通知在子系统内部创建。
关于注册/注销引脚的通知也是由子系统触发的。
关于 `dpll` 设备或引脚状态变化的通知以两种方式被触发：

- 在成功请求 `dpll` 子系统的更改后，子系统会调用相应的通知函数，
- 由设备驱动通过 `dpll_device_change_ntf()` 或 `dpll_pin_change_ntf()` 请求，当驱动告知状态发生变化时

使用 `dpll` 接口的设备驱动不需要实现所有的回调操作。不过，有一些是必须实现的。
必需的 `dpll` 设备级别的回调操作包括：

- ``.mode_get``,
- ``.lock_status_get``

必需的引脚级别的回调操作包括：

- ``.state_on_dpll_get``（对于注册到 `dpll` 设备的引脚），
- ``.state_on_pin_get``（对于注册到父引脚的引脚），
- ``.direction_get``

其他所有操作处理器都会检查是否存在，如果特定处理器不存在，则返回 ``-EOPNOTSUPP``。
最简单的实现可以在OCP TimeCard驱动程序中找到。`ops`结构体定义如下：

.. code-block:: c

    static const struct dpll_device_ops dpll_ops = {
            .lock_status_get = ptp_ocp_dpll_lock_status_get,
            .mode_get = ptp_ocp_dpll_mode_get,
            .mode_supported = ptp_ocp_dpll_mode_supported,
    };

    static const struct dpll_pin_ops dpll_pins_ops = {
            .frequency_get = ptp_ocp_dpll_frequency_get,
            .frequency_set = ptp_ocp_dpll_frequency_set,
            .direction_get = ptp_ocp_dpll_direction_get,
            .direction_set = ptp_ocp_dpll_direction_set,
            .state_on_dpll_get = ptp_ocp_dpll_state_get,
    };

注册部分如下所示：

.. code-block:: c

    clkid = pci_get_dsn(pdev);
    bp->dpll = dpll_device_get(clkid, 0, THIS_MODULE);
    if (IS_ERR(bp->dpll)) {
            err = PTR_ERR(bp->dpll);
            dev_err(&pdev->dev, "dpll_device_alloc failed\n");
            goto out;
    }

    err = dpll_device_register(bp->dpll, DPLL_TYPE_PPS, &dpll_ops, bp);
    if (err)
            goto out;

    for (i = 0; i < OCP_SMA_NUM; i++) {
            bp->sma[i].dpll_pin = dpll_pin_get(clkid, i, THIS_MODULE, &bp->sma[i].dpll_prop);
            if (IS_ERR(bp->sma[i].dpll_pin)) {
                    err = PTR_ERR(bp->dpll);
                    goto out_dpll;
            }

            err = dpll_pin_register(bp->dpll, bp->sma[i].dpll_pin, &dpll_pins_ops,
                                    &bp->sma[i]);
            if (err) {
                    dpll_pin_put(bp->sma[i].dpll_pin);
                    goto out_dpll;
            }
    }

在错误处理路径中，需要按相反的顺序释放每一个分配：

.. code-block:: c

    while (i) {
            --i;
            dpll_pin_unregister(bp->dpll, bp->sma[i].dpll_pin, &dpll_pins_ops, &bp->sma[i]);
            dpll_pin_put(bp->sma[i].dpll_pin);
    }
    dpll_device_put(bp->dpll);

更复杂的例子可以在Intel的ICE驱动程序或nVidia的mlx5驱动程序中找到。

### SyncE 启用
为了启用SyncE功能，需要允许软件应用控制dpll设备，该应用会根据dpll设备及其输入信号的当前状态来监控和配置这些输入信号。
在这种情况下，dpll设备的输入信号也应该是可配置的，以便通过从PHY网络设备恢复的信号来驱动dpll。
这可以通过将一个引脚暴露给网络设备来实现——使用`dpll_netdev_pin_set(struct net_device *dev, struct dpll_pin *dpll_pin)`将引脚附加到网络设备本身。
暴露的引脚ID句柄`DPLL_A_PIN_ID`对用户是可识别的，因为它会作为嵌套属性`IFLA_DPLL_PIN`的一部分被包含在网络设备的`RTM_NEWLINK`命令响应中。
