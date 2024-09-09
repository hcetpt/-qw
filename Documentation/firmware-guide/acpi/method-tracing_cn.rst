.. SPDX-License-Identifier: GPL-2.0
.. include:: <isonum.txt>

=====================
ACPICA 跟踪设施
=====================

:版权: |copy| 2015, Intel Corporation
:作者: Lv Zheng <lv.zheng@intel.com>

摘要
========
本文档描述了方法跟踪设施的功能和接口。

功能与使用示例
==================

ACPICA 提供了方法跟踪功能。目前实现了以下两个功能：
日志缩减
------------

当启用 CONFIG_ACPI_DEBUG 时，ACPICA 子系统提供了调试输出。通过 ACPI_DEBUG_PRINT() 宏部署的调试消息可以在两个级别上进行缩减 —— 每个组件级别（称为调试层，通过 /sys/module/acpi/parameters/debug_layer 配置）和每个类型级别（称为调试级别，通过 /sys/module/acpi/parameters/debug_level 配置）。然而，当特定的层/级别应用于控制方法评估时，调试输出的数量可能仍然太大，无法放入内核日志缓冲区。因此，提出了一个想法：仅在开始控制方法评估时启用详细的调试层/级别日志，并在停止控制方法评估时禁用详细日志记录。
以下命令示例说明了“日志缩减”功能的使用方法：

a. 在控制方法被评估时过滤出匹配的调试层/级别日志：

```
# cd /sys/module/acpi/parameters
# echo "0xXXXXXXXX" > trace_debug_layer
# echo "0xYYYYYYYY" > trace_debug_level
# echo "enable" > trace_state
```

b. 在指定的控制方法被评估时过滤出匹配的调试层/级别日志：

```
# cd /sys/module/acpi/parameters
# echo "0xXXXXXXXX" > trace_debug_layer
# echo "0xYYYYYYYY" > trace_debug_level
# echo "\PPPP.AAAA.TTTT.HHHH" > trace_method_name
# echo "method" > /sys/module/acpi/parameters/trace_state
```

c. 在指定的控制方法首次被评估时过滤出匹配的调试层/级别日志：

```
# cd /sys/module/acpi/parameters
# echo "0xXXXXXXXX" > trace_debug_layer
# echo "0xYYYYYYYY" > trace_debug_level
# echo "\PPPP.AAAA.TTTT.HHHH" > trace_method_name
# echo "method-once" > /sys/module/acpi/parameters/trace_state
```

其中：
`0xXXXXXXXX/0xYYYYYYYY`
   参见 Documentation/firmware-guide/acpi/debug.rst 获取可能的调试层/级别掩码值。

`\PPPP.AAAA.TTTT.HHHH`
   控制方法在 ACPI 命名空间中的完整路径。它不必是控制方法评估的入口。

AML 跟踪器
------------

在 AML 解释器开始或停止执行控制方法或 AML 操作码时，方法跟踪设施会在“跟踪点”添加特殊的日志条目。请注意，这些日志条目的格式可能会发生变化：

```
[    0.186427]   exdebug-0398 ex_trace_point        : Method Begin [0xf58394d8:\_SB.PCI0.LPCB.ECOK] execution
[    0.186630]   exdebug-0398 ex_trace_point        : Opcode Begin [0xf5905c88:If] execution
[    0.186820]   exdebug-0398 ex_trace_point        : Opcode Begin [0xf5905cc0:LEqual] execution
```
```
[    0.187010]   exdebug-0398 ex_trace_point        : 操作码开始 [0xf5905a20:-NamePath-] 执行
[    0.187214]   exdebug-0398 ex_trace_point        : 操作码结束 [0xf5905a20:-NamePath-] 执行
[    0.187407]   exdebug-0398 ex_trace_point        : 操作码开始 [0xf5905f60:One] 执行
[    0.187594]   exdebug-0398 ex_trace_point        : 操作码结束 [0xf5905f60:One] 执行
[    0.187789]   exdebug-0398 ex_trace_point        : 操作码结束 [0xf5905cc0:LEqual] 执行
[    0.187980]   exdebug-0398 ex_trace_point        : 操作码开始 [0xf5905cc0:Return] 执行
[    0.188146]   exdebug-0398 ex_trace_point        : 操作码开始 [0xf5905f60:One] 执行
[    0.188334]   exdebug-0398 ex_trace_point        : 操作码结束 [0xf5905f60:One] 执行
[    0.188524]   exdebug-0398 ex_trace_point        : 操作码结束 [0xf5905cc0:Return] 执行
[    0.188712]   exdebug-0398 ex_trace_point        : 操作码结束 [0xf5905c88:If] 执行
```
```
[    0.188903]   exdebug-0398 ex_trace_point        : 方法结束 [0xf58394d8:_SB.PCI0.LPCB.ECOK] 执行
开发人员可以利用这些特殊的日志条目来跟踪 AML 的解释，从而有助于问题调试和性能调优。请注意，“AML 跟踪器”日志是通过 ACPI_DEBUG_PRINT() 宏实现的，因此需要启用 CONFIG_ACPI_DEBUG 来启用“AML 跟踪器”日志。
以下命令示例说明了“AML 跟踪器”功能的用法：

a. 在控制方法被评估时过滤掉方法开始/停止的“AML 跟踪器”日志：
   
      # cd /sys/module/acpi/parameters
      # echo "0x80" > trace_debug_layer
      # echo "0x10" > trace_debug_level
      # echo "enable" > trace_state

b. 在指定的控制方法被评估时过滤掉方法开始/停止的“AML 跟踪器”日志：

      # cd /sys/module/acpi/parameters
      # echo "0x80" > trace_debug_layer
      # echo "0x10" > trace_debug_level
      # echo "\PPPP.AAAA.TTTT.HHHH" > trace_method_name
      # echo "method" > trace_state

c. 在指定的控制方法首次被评估时过滤掉方法开始/停止的“AML 跟踪器”日志：

      # cd /sys/module/acpi/parameters
      # echo "0x80" > trace_debug_layer
      # echo "0x10" > trace_debug_level
      # echo "\PPPP.AAAA.TTTT.HHHH" > trace_method_name
      # echo "method-once" > trace_state

d. 在指定的控制方法被评估时过滤掉方法/操作码开始/停止的“AML 跟踪器”日志：

      # cd /sys/module/acpi/parameters
      # echo "0x80" > trace_debug_layer
      # echo "0x10" > trace_debug_level
      # echo "\PPPP.AAAA.TTTT.HHHH" > trace_method_name
      # echo "opcode" > trace_state

e. 在指定的控制方法首次被评估时过滤掉方法/操作码开始/停止的“AML 跟踪器”日志：

      # cd /sys/module/acpi/parameters
      # echo "0x80" > trace_debug_layer
      # echo "0x10" > trace_debug_level
      # echo "\PPPP.AAAA.TTTT.HHHH" > trace_method_name
      # echo "opcode-opcode" > trace_state

请注意，所有上述与方法跟踪设施相关的模块参数都可以作为引导参数使用，例如：

   acpi.trace_debug_layer=0x80 acpi.trace_debug_level=0x10 \
   acpi.trace_method_name=_SB.LID0._LID acpi.trace_state=opcode-once

接口描述
======================

所有方法跟踪功能都可以通过位于 /sys/module/acpi/parameters/ 的 ACPI 模块参数进行配置：

trace_method_name
  用户想要跟踪的 AML 方法的完整路径
请注意，完整路径不应在其名称段中包含尾部的 "_"，但可以包含 "\\" 来形成绝对路径
trace_debug_layer
  启用跟踪功能时使用的临时 debug_layer
默认使用 ACPI_EXECUTER (0x80)，这是用于匹配所有“AML 跟踪器”日志的 debug_layer
trace_debug_level
  启用跟踪功能时使用的临时 debug_level
默认使用 ACPI_LV_TRACE_POINT (0x10)，这是用于匹配所有“AML 跟踪器”日志的 debug_level
trace_state
  跟踪功能的状态
用户可以通过执行以下命令来启用或禁用此调试跟踪功能：

   # echo 字符串 > /sys/module/acpi/parameters/trace_state

其中“字符串”应该是以下内容之一：

"disable"
  禁用方法跟踪功能
```
"enable"
启用方法追踪功能
在任何方法执行期间，匹配 "trace_debug_layer/trace_debug_level" 的 ACPICA 调试消息将被记录

"method"
启用方法追踪功能
在 "trace_method_name" 方法执行期间，匹配 "trace_debug_layer/trace_debug_level" 的 ACPICA 调试消息将被记录

"method-once"
启用方法追踪功能
在 "trace_method_name" 方法执行期间，匹配 "trace_debug_layer/trace_debug_level" 的 ACPICA 调试消息仅记录一次

"opcode"
启用方法追踪功能
在 "trace_method_name" 方法/操作码执行期间，匹配 "trace_debug_layer/trace_debug_level" 的 ACPICA 调试消息将被记录

"opcode-once"
启用方法追踪功能
在 "trace_method_name" 方法/操作码执行期间，匹配 "trace_debug_layer/trace_debug_level" 的 ACPICA 调试消息仅记录一次
请注意，“enable”与其他特性启用选项之间的区别如下：

1. 当指定了“enable”时，由于“trace_debug_layer/trace_debug_level”应适用于所有控制方法的评估，在将“trace_state”配置为“enable”之后，“trace_method_name”将被重置为NULL。
2. 当指定了“method/opcode”时，如果在将“trace_state”配置为这些选项时“trace_method_name”为NULL，则“trace_debug_layer/trace_debug_level”将适用于所有控制方法的评估。
