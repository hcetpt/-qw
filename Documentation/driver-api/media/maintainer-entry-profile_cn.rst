媒体子系统配置文件
=======================

概述
--------

媒体子系统涵盖了对多种设备的支持：流捕获、模拟和数字电视流、摄像头、遥控器、HDMI CEC 和媒体管道控制。它主要涉及以下目录的内容：

  - drivers/media
  - drivers/staging/media
  - Documentation/admin-guide/media
  - Documentation/driver-api/media
  - Documentation/userspace-api/media
  - Documentation/devicetree/bindings/media/\ [1]_
  - include/media

.. [1] 设备树绑定由 OPEN FIRMWARE AND FLATTENED DEVICE TREE BINDINGS 的维护者们负责（参见 MAINTAINERS 文件）。因此，任何针对这些绑定的更改必须先经过他们的审查，然后才能通过媒体子系统的开发树合并。
媒体用户空间和内核API都有相应的文档，并且这些文档必须与API的变化保持同步。这意味着所有向子系统添加新特性的补丁都必须同时对相应的API文件进行更新。
由于媒体子系统的规模庞大且范围广泛，其维护模式是拥有专门的子维护者，他们具备子系统特定方面的广泛知识。子维护者的任务是审查补丁，为用户提供反馈以确保补丁遵循子系统的规则并正确使用了媒体内核和用户空间API。
媒体子系统的补丁必须作为纯文本电子邮件发送到 media 邮件列表 linux-media@vger.kernel.org。带有HTML格式的邮件将被邮件服务器自动拒绝。同时抄送相关子维护者也是明智的选择。
媒体的工作流程很大程度上依赖于Patchwork，这意味着一旦提交了补丁，邮件首先会被邮件列表服务器接受，之后应该可以在以下位置找到：

   - https://patchwork.linuxtv.org/project/linux-media/list/

如果在几分钟后没有自动出现，请检查邮件是否为纯文本\ [2]_ 格式，并确认你的邮件客户端没有破坏空白字符，然后再抱怨或重新提交。
你也可以通过以下链接查看邮件列表服务器是否已接收你的补丁：

   - https://lore.kernel.org/linux-media/

.. [2] 如果你的邮件包含HTML内容，邮件列表服务器将会直接丢弃它，没有任何进一步的通知。
媒体维护者
+++++++++++++++++

在媒体子系统中，我们有一组资深开发者负责代码审查（通常被称为子维护者），以及另一位资深开发者负责整个子系统的管理。对于核心变更，尽可能多地由多个媒体维护者进行审查。
专注于子系统特定领域的媒体维护者包括：

- 遥控器（红外线）:
    Sean Young <sean@mess.org>

- HDMI CEC:
    Hans Verkuil <hverkuil@xs4all.nl>

- 媒体控制器驱动程序:
    Laurent Pinchart <laurent.pinchart@ideasonboard.com>

- ISP、v4l2-async、v4l2-fwnode、v4l2-flash-led-class 和传感器驱动程序:
    Sakari Ailus <sakari.ailus@linux.intel.com>

- V4L2 驱动程序和核心V4L2框架:
    Hans Verkuil <hverkuil@xs4all.nl>

子系统的维护者是：
  Mauro Carvalho Chehab <mchehab@kernel.org>

媒体维护者可以根据需要将补丁委托给其他维护者。
在这种情况下，checkpatch 的“delegate”字段指明当前谁负责审查该补丁。
提交检查清单附录
-------------------------

更改 Open Firmware/设备树绑定的补丁必须经过 设备树维护者的审查。因此，当通过 devicetree@vger.kernel.org 邮件列表提交这些补丁时，应将设备树维护者添加为抄送人。
在 https://git.linuxtv.org/v4l-utils.git/ 有一套合规工具，用于检查驱动程序是否正确实现了媒体 API：

====================	=======================================================
类型			工具
====================	=======================================================
V4L2 驱动\[3\]		``v4l2-compliance``
V4L2 虚拟驱动		``contrib/test/test-media``
CEC 驱动		``cec-compliance``
====================	=======================================================

.. [3] ``v4l2-compliance`` 还涵盖了 V4L2 驱动中的媒体控制器使用情况
其他合规工具正在开发中，以检查子系统的其他部分
在补丁向上游提交之前，这些测试需要通过
此外，请注意我们构建内核的方式如下：

```bash
make CF=-D__CHECK_ENDIAN__ CONFIG_DEBUG_SECTION_MISMATCH=y C=1 W=1 CHECK=check_script
```

其中检查脚本是：

```bash
#!/bin/bash
/devel/smatch/smatch -p=kernel $@ >&2
/devel/sparse/sparse $@ >&2
```

除非有充分的理由，否则请确保不要在你的补丁中引入新的警告。
样式清理补丁
+++++++++++++++++++++

当样式更改与其他文件更改一起出现时，欢迎进行样式清理。
我们可以接受纯样式清理补丁，但理想情况下，应该是一个针对整个子系统的补丁（如果清理量较小），或者至少按目录分组。例如，如果你正在对 drivers/media 下的驱动进行大规模的清理，请为 drivers/media/pci 下的所有驱动发送一个补丁，另一个为 drivers/media/usb 等等。
编码风格附录
+++++++++++++++++++++

媒体开发使用 `checkpatch.pl` 的严格模式来验证代码风格，例如：

```bash
$ ./scripts/checkpatch.pl --strict --max-line-length=80
```

原则上，补丁应遵循编码风格规则，但如果存在合理的理由，则允许例外。在这种情况下，维护者和评审者可能会询问未处理 `checkpatch.pl` 建议的原因。
请注意，目标是提高代码可读性。在某些情况下，`checkpatch.pl` 可能会指出实际上看起来更差的问题。因此，你应该运用良好的判断力。
需要注意的是，解决一个 `checkpatch.pl` 问题（任何类型的）可能单独导致每行超过80个字符。虽然这不是严格禁止的，但仍应努力保持每行不超过80个字符。这可能包括重构代码以减少缩进、使用更短的变量或函数名称以及最重要的，简单地折行。
特别地，我们接受超过80列的行：

    - 在字符串上，因为不应该由于行长度限制而将其打断；
    - 当函数或变量名需要有较长的标识符时，这时很难遵守80列的限制；
    - 在算术表达式上，如果分行会使它们更难阅读；
    - 当这样做可以避免一行以一个未闭合的括号或方括号结尾时。
关键周期日期
------------

新提交可以在任何时候发送，但如果希望赶上下一个合并窗口，则应该在-rc5之前发送，并且理想情况下应在-rc6时在linux-media分支中稳定下来。

审查频率
------------

只要你的补丁位于 https://patchwork.linuxtv.org 上，它迟早会被处理，因此你无需重新提交补丁。
除了错误修复外，我们通常不会在-rc6到下一个-rc1之间将新的补丁添加到开发树中。
请注意，媒体子系统是一个高流量的领域，所以我们可能需要一段时间来审查你的补丁。如果你在几周内没有收到反馈，请随时联系我们，或者请其他开发者公开添加“Reviewed-by”和更为重要的“Tested-by:”标签。
请注意，我们期望“Tested-by:”有一个详细的描述，明确指出测试所使用的硬件平台以及测试的具体内容。
