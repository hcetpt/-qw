SPDX 许可证标识符: GPL-2.0

======================================
CoreSight 系统配置管理器
======================================

    :作者:   Mike Leach <mike.leach@linaro.org>
    :日期:   2020年10月

简介
============

CoreSight 系统配置管理器是一个API，允许使用预定义的配置对CoreSight系统进行编程，这些配置随后可以通过sysfs或perf轻松启用。
许多CoreSight组件可以以复杂的方式进行编程——特别是ETMs（嵌入式跟踪宏单元）。
此外，组件可以通过诸如CTI（交叉触发接口）和CTM（交叉触发矩阵）之类的跨触发组件在整个CoreSight系统中相互作用。这些系统设置可以作为命名配置被定义和启用。

基本概念
==============

本节介绍了CoreSight系统配置的基本概念。

特性
--------

一个特性是一组针对CoreSight设备的命名编程。编程是设备依赖的，并且可以用绝对寄存器值、资源使用情况和参数值来定义。
特性通过一个描述符来定义。这个描述符用于加载到匹配的设备上，无论是在特性加载到系统时，还是在CoreSight设备注册到配置管理器时。
加载过程涉及将描述符解释为驱动程序中的一系列寄存器访问——资源使用情况和参数描述转换为适当的寄存器访问。这种解释使得在需要时将特性编程到设备上变得简单而高效。
特性在设备上不会激活，直到该特性被启用，并且设备本身也被启用。当设备被启用时，已启用的特性将被编程到设备硬件中。
特性作为系统上的配置的一部分被启用。

参数值
~~~~~~~~~~~~~~~

参数值是一个可以在特性启用之前由用户设置的命名值，它可以调整由特性编程的操作行为。
例如，这可能是一个在编程操作中以给定频率重复的计数值。当启用该功能时，则使用该参数的当前值来对设备进行编程。
功能描述符定义了一个参数的默认值，在用户没有提供新值的情况下使用该默认值。
用户可以使用下面描述的 CoreSight 系统的 configfs API 更新参数值。
当在设备上启用该功能时，将加载参数的当前值到设备中。

配置
----

一个配置定义了一组要在选定配置的跟踪会话中使用的功能。对于任何跟踪会话，只能选择一个配置。
所定义的功能可以是任何注册以支持系统配置类型的设备上的功能。一个配置可以选择一类设备上的功能（例如所有 ETMv4 设备）或特定设备上的功能（例如系统上的某个特定 CTI）。
与功能类似，使用描述符来定义配置。
这将定义作为配置一部分必须启用的功能，以及可以用来覆盖默认参数值的预设值。

预设值
~~~~~~~~~~~~~

预设值是配置所使用功能的一组易于选择的参数值。单个预设集中的值的数量等于配置中使用功能的参数值之和。
例如，一个配置包含 3 个功能，其中一个有两个参数，另一个有一个参数，还有一个没有参数。因此，单个预设集将有 3 个值。
预设值可由配置文件定义，最多可以定义15个。如果没有选择预设值，则使用功能中定义的参数值作为默认值。

操作
~~~~

以下步骤描述了配置的操作过程：
1）在这个例子中，配置是“autofdo”，它关联了一个名为“strobing”的功能，该功能适用于ETMv4 CoreSight设备。
2）配置被启用。例如，“perf”可能会在其命令行中选择该配置：

    ```
    perf record -e cs_etm/autofdo/ myapp
    ```

    这将启用“autofdo”配置。
3）perf开始在系统上进行追踪。每当perf用于追踪的每个ETMv4被启用时，配置管理器会检查该ETMv4是否具有与当前活动配置相关的功能。在这种情况下，“strobing”被启用并编程到ETMv4中。
4）当ETMv4被禁用时，任何标记为需要保存的寄存器将被读回。
5）在perf会话结束时，配置将被禁用。

查看配置和功能
===============

当前加载到系统中的配置和功能集可以通过configfs API进行查看。
正常挂载配置文件系统后，`cs-syscfg` 子系统将会出现：

    $ ls /config
    cs-syscfg  stp-policy

该子系统有两个子目录：

    $ cd cs-syscfg/
    $ ls
    configurations  features

系统内置了 `autofdo` 配置。可以通过以下方式查看：

    $ cd configurations/
    $ ls
    autofdo
    $ cd autofdo/
    $ ls
    description  feature_refs  preset1  preset3  preset5  preset7  preset9
    enable       preset        preset2  preset4  preset6  preset8
    $ cat description
    设置 ETM 以脉冲模式用于 autofdo
    $ cat feature_refs
    strobing

每个预设（preset）都有一个对应的 `preset<n>` 子目录。可以检查预设的值：

    $ cat preset1/values
    strobing.window = 0x1388 strobing.period = 0x2
    $ cat preset2/values
    strobing.window = 0x1388 strobing.period = 0x4

`enable` 和 `preset` 文件允许在使用 CoreSight 时通过 sysfs 控制配置。可以检查配置引用的功能（features）：

    $ cd ../../features/strobing/
    $ ls
    description  matches  nr_params  params
    $ cat description
    生成周期性的跟踪捕获窗口
参数 'window'：CPU 周期数 (W)
参数 'period'：每隔 x * W 周期使能 W 周期的跟踪
    $ cat matches
    SRC_ETMV4
    $ cat nr_params
    2

进入 `params` 目录来检查和调整参数：

    cd params
    $ ls
    period  window
    $ cd period
    $ ls
    value
    $ cat value
    0x2710
    # echo 15000 > value
    # cat value
    0x3a98

这样调整的参数会反映在所有已加载该功能的设备实例中。

在 perf 中使用配置
============================

加载到 CoreSight 配置管理中的配置也在 perf 的 `cs_etm` 事件基础设施中声明，以便在运行 perf 跟踪时可以选择这些配置：

    $ ls /sys/devices/cs_etm
    cpu0  cpu2  events  nr_addr_filters		power  subsystem  uevent
    cpu1  cpu3  format  perf_event_mux_interval_ms	sinks  type

这里的关键目录是 `events` —— 一个通用的 perf 目录，允许在 perf 命令行中选择。与 `sinks` 目录类似，这提供了配置名称的哈希值。

`events` 目录中的条目使用 perf 内置的语法生成器，在评估命令时替换语法为名称：

    $ ls events/
    autofdo
    $ cat events/autofdo
    configid=0xa7c3dddd

可以在 perf 命令行中选择 `autofdo` 配置：

    $ perf record -e cs_etm/autofdo/u --per-thread <application>

也可以选择一个预设（preset）来覆盖当前的参数值：

    $ perf record -e cs_etm/autofdo,preset=1/u --per-thread <application>

当这样选择配置时，将自动选择跟踪接收器（sink）。

在 sysfs 中使用配置
=============================

CoreSight 可以通过 sysfs 进行控制。当使用 sysfs 时，可以为 sysfs 会话中使用的设备激活一个配置。

在一个配置中有 `enable` 和 `preset` 文件。
要启用一个配置用于 sysfs：

    $ cd configurations/autofdo
    $ echo 1 > enable

这将使用功能中的默认参数值 —— 如上所述可以进行调整。
要使用一组预设参数值 `preset<n>`：

    $ echo 3 > preset

这将选择预设 `preset3` 用于配置。
预设的有效值为 0 —— 表示不选择预设，以及任何存在 `preset<n>` 子目录的值 `<n>`。
请注意，活动的 sysfs 配置是一个全局参数，因此在任何时候只能有一个配置对 sysfs 生效。
尝试启用第二个配置将导致错误。
此外，在使用过程中尝试禁用配置也会导致错误。
sysfs 使用活动配置与 perf 中使用的配置是独立的。

创建和加载自定义配置
==================

可以通过使用可加载模块动态地将自定义配置和/或功能加载到系统中。
一个自定义配置的例子可以在 ./samples/coresight 找到。这创建了一个新的配置，使用现有的内置闪烁功能，但提供了一组不同的预设值。
当模块被加载时，该配置会出现在 configfs 文件系统中，并且可以像选择内置配置那样进行选择。
配置可以使用之前加载的功能。系统会确保无法卸载当前正在使用的功能，通过强制卸载顺序严格为加载顺序的逆序来实现这一点。
