### SPDX 许可证标识符：GPL-2.0

#### Linux I2C Sysfs

##### 概览

由于 I2C 多路复用器（I2C MUX）的存在，I2C 拓扑结构可能非常复杂。Linux 内核将多路复用器通道抽象为逻辑 I2C 总线编号。然而，在物理 I2C 总线编号、MUX 拓扑结构与逻辑 I2C 总线编号之间存在知识空白。本文档旨在填补这一空白，以便读者（例如硬件工程师和新软件开发者）通过了解物理 I2C 拓扑结构并导航 Linux 壳中的 I2C sysfs 来理解内核中逻辑 I2C 总线的概念。这些知识对于使用 `i2c-tools` 进行开发和调试非常重要。

##### 目标受众

需要在运行 Linux 的系统上使用 Linux 壳与 I2C 子系统交互的人员。

##### 先决条件

1. 熟悉基本的 Linux 壳文件系统命令和操作。
2. 对 I2C、I2C 多路复用器和 I2C 拓扑结构有基本了解。

##### I2C Sysfs 的位置

通常，Linux 的 Sysfs 文件系统挂载在 `/sys` 目录下，因此您可以在 `/sys/bus/i2c/devices` 下找到 I2C Sysfs，并直接 `cd` 到该目录。在这个目录下有一系列符号链接。以 `i2c-` 开头的链接是 I2C 总线，它们可能是物理总线也可能是逻辑总线；其他以数字开头并以数字结尾的链接是 I2C 设备，其中第一个数字代表 I2C 总线编号，第二个数字代表 I2C 地址。

例如 Google Pixel 3 手机：

```
blueline:/sys/bus/i2c/devices $ ls
0-0008  0-0061  1-0028  3-0043  4-0036  4-0041  i2c-1  i2c-3
0-000c  0-0066  2-0049  4-000b  4-0040  i2c-0   i2c-2  i2c-4
```

`i2c-2` 是编号为 2 的 I2C 总线，而 `2-0049` 是总线 2 上地址为 0x49 的 I2C 设备，并且该设备已绑定到内核驱动程序。

##### 术语定义

首先，为了避免后文出现混淆，我们先定义一些术语。

- **（物理）I2C 总线控制器**

  运行 Linux 内核的硬件系统可能具有多个物理 I2C 总线控制器。这些控制器是硬件且物理存在的，系统可能在内存空间中定义了多个寄存器来控制这些控制器。Linux 内核在源代码目录 `drivers/i2c/busses` 中包含了用于不同系统的 I2C 总线驱动程序，这些驱动程序可以将内核 I2C API 转换为寄存器操作。这个术语不仅仅局限于 Linux 内核。

- **I2C 总线物理编号**

  对于每个物理 I2C 总线控制器，系统供应商可能会给每个控制器分配一个物理编号。例如，具有最低寄存器地址的第一个 I2C 总线控制器可能被称为 `I2C-0`。
### 逻辑I2C总线
--------------

在Linux I2C Sysfs中看到的每一个I2C总线编号都是一个带有指定编号的逻辑I2C总线。这类似于软件代码通常基于虚拟内存空间编写，而不是物理内存空间。每个逻辑I2C总线可能是对物理I2C总线控制器的抽象，或者是I2C多路复用器（MUX）通道的抽象。如果是MUX通道的抽象，那么当我们通过这样的逻辑总线访问I2C设备时，内核会为你切换I2C MUX到正确的通道，这是抽象的一部分。

### 物理I2C总线
----------------

如果逻辑I2C总线是物理I2C总线控制器的直接抽象，我们称之为物理I2C总线。

### 注意事项
--------------

对于只了解板级物理I2C设计的人来说，这部分可能会令人困惑。实际上，在设备树源文件（DTS）的`aliases`部分中，可以将I2C总线的物理编号重命名为不同的逻辑I2C总线编号。例如，可以查看`arch/arm/boot/dts/nuvoton-npcm730-gsj.dts`这个DTS文件作为示例。

**最佳实践：**（面向内核软件开发者）最好保持I2C总线的物理编号与其对应的逻辑I2C总线编号相同，而不是重命名或映射它们，这样对其他用户来说会更少混淆。这些物理I2C总线可以作为从I2C MUX扇出的好起点。在以下示例中，我们将假设物理I2C总线的编号与它们的物理I2C总线编号相同。

### 遍历逻辑I2C总线
==================

接下来的内容中，我们将使用一个更为复杂的I2C拓扑结构作为示例。以下是该I2C拓扑结构的简要图示。如果你初看不明白这张图，请不要担心，继续阅读本文档，并在读完后回过头来查看它。
::

  i2c-7（物理I2C总线控制器7）
  `-- 7-0071（位于0x71的4通道I2C MUX）
      |-- i2c-60（通道0）
      |-- i2c-73（通道1）
      |   |-- 73-0040（具有hwmon目录的I2C传感器设备）
      |   |-- 73-0070（位于0x70的I2C MUX，存在于DTS中，但探测失败）
      |   `-- 73-0072（位于0x72的8通道I2C MUX）
      |       |-- i2c-78（通道0）
      |       |-- ...（通道1...6，i2c-79...i2c-84）
      |       `-- i2c-85（通道7）
      |-- i2c-86（通道2）
      `-- i2c-203（通道3）

### 区分物理和逻辑I2C总线
----------------------------------------

区分物理I2C总线和逻辑I2C总线的一个简单方法是使用命令`ls -l`或`readlink`读取I2C总线目录下的符号链接`device`。

另一个可以检查的替代符号链接是`mux_device`。这个链接仅存在于由另一个I2C总线扇出的逻辑I2C总线目录中。读取这个链接也会告诉你哪个I2C MUX设备创建了这个逻辑I2C总线。

如果符号链接指向以`.i2c`结尾的目录，则应该是一个物理I2C总线，直接抽象了一个物理I2C总线控制器。例如：
```
$ readlink /sys/bus/i2c/devices/i2c-7/device
../../f0087000.i2c
$ ls /sys/bus/i2c/devices/i2c-7/mux_device
ls: /sys/bus/i2c/devices/i2c-7/mux_device: No such file or directory
```

在这种情况下，`i2c-7`是一个物理I2C总线，因此在其目录下没有符号链接`mux_device`。如果内核软件开发者遵循常见的做法不对物理I2C总线进行重命名，这也意味着它是系统中的物理I2C总线控制器7。
另一方面，如果符号链接指向另一个I2C总线，则当前目录所表示的I2C总线必须是一个逻辑总线。链接指向的I2C总线是父级总线，它可以是物理I2C总线也可以是逻辑总线。在这种情况下，当前目录所表示的I2C总线抽象了一个在父级总线下方的I2C多路复用(MUX)通道。例如：

  * 使用`readlink`命令查看/sys/bus/i2c/devices/i2c-73/device
  * 使用`readlink`命令查看/sys/bus/i2c/devices/i2c-73/mux_device

``i2c-73``是由位于``i2c-7``上的I2C MUX分发出来的逻辑总线，该MUX的I2C地址为0x71。
每当访问带有编号73的I2C设备时，内核总是会自动切换到地址为0x71的I2C MUX的正确通道作为抽象的一部分。

### 查找逻辑I2C总线编号

在本节中，我们将描述如何根据对物理硬件I2C拓扑结构的理解来找出代表特定I2C MUX通道的逻辑I2C总线编号。
在这个例子中，我们有一个系统，它有一个未在DTS中重命名的物理I2C总线7。在这条总线上有一个地址为0x71的4通道MUX。还有一个8通道MUX位于0x71 MUX的第一通道后方，地址为0x72。让我们通过Sysfs导航并找出0x72 MUX的第3个通道的逻辑I2C总线编号。
首先，进入``i2c-7``目录:

  * 进入目录：`cd /sys/bus/i2c/devices/i2c-7`
  * 列出文件和目录：`ls`

在那里我们可以看到0x71 MUX显示为``7-0071``。进入该目录:

  * 进入目录：`cd 7-0071/`
  * 列出文件和目录：`ls -l`

使用`readlink`或`ls -l`读取链接``channel-1``:

  * 使用`readlink`命令查看channel-1

我们发现0x71 MUX上``i2c-7``的第1个通道被分配了逻辑I2C总线编号73。
接下来继续旅程，可以以两种方式进入目录``i2c-73``:

  1. 从I2C Sysfs根目录进入``i2c-73``
  2. 进入channel符号链接
  3. 进入链接的内容

无论哪种方式，你都会到达``i2c-73``目录。与上面类似，我们现在可以找到0x72 MUX以及其通道被分配了哪些逻辑I2C总线编号:

  * 列出文件和目录：`ls`
  * 进入目录：`cd 73-0072`
  * 列出文件和目录：`ls`
  * 使用`readlink`命令查看channel-3

在那里我们发现0x72 MUX的第3个通道的逻辑I2C总线编号是81。稍后我们可以使用这个编号切换到其自己的I2C Sysfs目录或者发出``i2c-tools``命令。

**提示**：一旦理解了带有多路复用器的I2C拓扑结构，命令`i2cdetect -l`（如果系统中可用）可以在`I2C Tools`中轻松地给出I2C拓扑结构的概览。例如:

```
$ i2cdetect -l | grep -e '\-73' -e _7 | sort -V
i2c-7   i2c             npcm_i2c_7                              I2C adapter
i2c-73  i2c             i2c-7-mux (chan_id 1)                   I2C adapter
i2c-78  i2c             i2c-73-mux (chan_id 0)                  I2C adapter
i2c-79  i2c             i2c-73-mux (chan_id 1)                  I2C adapter
i2c-80  i2c             i2c-73-mux (chan_id 2)                  I2C adapter
i2c-81  i2c             i2c-73-mux (chan_id 3)                  I2C adapter
i2c-82  i2c             i2c-73-mux (chan_id 4)                  I2C adapter
i2c-83  i2c             i2c-73-mux (chan_id 5)                  I2C adapter
i2c-84  i2c             i2c-73-mux (chan_id 6)                  I2C adapter
i2c-85  i2c             i2c-73-mux (chan_id 7)                  I2C adapter
```

### 固定的逻辑I2C总线编号

如果没有在DTS中指定，当成功应用了I2C MUX驱动程序并且MUX设备成功探测后，内核将基于当前最大的逻辑总线编号递增地为MUX通道分配一个逻辑总线编号。例如，如果系统中``i2c-15``是最高的逻辑总线编号，并且一个4通道MUX成功应用，那么MUX通道0将被分配为``i2c-16``，一直到MUX通道3的``i2c-19``。
内核软件开发人员能够在DTS中固定分发MUX通道至静态的逻辑I2C总线编号。本文档不会详细介绍如何在DTS中实现这一点，但我们可以在``arch/arm/boot/dts/aspeed-bmc-facebook-wedge400.dts``中看到一个示例。

在上述示例中，在物理I2C总线2上有一个地址为0x70的8通道I2C MUX。MUX的第2个通道在DTS中定义为``imux18``，并在``aliases``部分使用行``i2c18 = &imux18;``固定到了逻辑I2C总线编号18。
进一步说，有可能设计一个逻辑I2C总线编号方案，这样人们可以容易记住或算术性计算。例如，我们可以把总线3上的MUX的分发通道固定从30开始。因此30将是总线3上的MUX通道0的逻辑总线编号，而37将是总线3上的MUX通道7的逻辑总线编号。
I2C 设备
==========

在之前的章节中，我们主要介绍了 I2C 总线。本节我们将探讨 I2C 设备目录中的信息，这些目录的链接名称格式为 ``${bus}-${addr}``。其中 ``${bus}`` 部分是逻辑 I2C 总线的十进制数字，而 ``${addr}`` 部分则是每个设备的 I2C 地址的十六进制数值。
I2C 设备目录内容
-------------------

在每个 I2C 设备目录内，都有一个名为 ``name`` 的文件。该文件指明了用于内核驱动程序探测此设备的设备名称。可以使用命令 `cat` 来读取其内容。例如：

```
/sys/bus/i2c/devices/i2c-73$ cat 73-0040/name
ina230
/sys/bus/i2c/devices/i2c-73$ cat 73-0070/name
pca9546
/sys/bus/i2c/devices/i2c-73$ cat 73-0072/name
pca9547
```

还有一个名为 ``driver`` 的符号链接，用以表明用于探测此设备的 Linux 内核驱动程序：

```
/sys/bus/i2c/devices/i2c-73$ readlink -f 73-0040/driver
/sys/bus/i2c/drivers/ina2xx
/sys/bus/i2c/devices/i2c-73$ readlink -f 73-0072/driver
/sys/bus/i2c/drivers/pca954x
```

但如果目录中不存在名为 ``driver`` 的链接，则可能意味着内核驱动程序由于某些错误未能成功探测到该设备。错误信息可以在 ``dmesg`` 中找到：

```
/sys/bus/i2c/devices/i2c-73$ ls 73-0070/driver
ls: 73-0070/driver: No such file or directory
/sys/bus/i2c/devices/i2c-73$ dmesg | grep 73-0070
pca954x 73-0070: probe failed
pca954x 73-0070: probe failed
```

根据 I2C 设备的具体类型以及用于探测设备的内核驱动程序的不同，设备目录中的内容也会有所不同。
I2C 多路复用器设备
------------------

如您在前一章节中已经了解到，I2C 多路复用器设备在其设备目录中会有名为 ``channel-*`` 的符号链接。这些链接指向它们对应的逻辑 I2C 总线目录：

```
/sys/bus/i2c/devices/i2c-73$ ls -l 73-0072/channel-*
lrwxrwxrwx ... 73-0072/channel-0 -> ../i2c-78
lrwxrwxrwx ... 73-0072/channel-1 -> ../i2c-79
lrwxrwxrwx ... 73-0072/channel-2 -> ../i2c-80
lrwxrwxrwx ... 73-0072/channel-3 -> ../i2c-81
lrwxrwxrwx ... 73-0072/channel-4 -> ../i2c-82
lrwxrwxrwx ... 73-0072/channel-5 -> ../i2c-83
lrwxrwxrwx ... 73-0072/channel-6 -> ../i2c-84
lrwxrwxrwx ... 73-0072/channel-7 -> ../i2c-85
```

I2C 传感器设备 / Hwmon
-----------------------

I2C 传感器设备也很常见。如果它们被内核的 hwmon（硬件监控）驱动程序成功绑定，那么您会在 I2C 设备目录中看到一个名为 ``hwmon`` 的目录。继续深入挖掘，您将发现 I2C 传感器设备的 Hwmon Sysfs：

```
/sys/bus/i2c/devices/i2c-73/73-0040/hwmon/hwmon17$ ls
curr1_input        in0_lcrit_alarm    name               subsystem
device             in1_crit           power              uevent
in0_crit           in1_crit_alarm     power1_crit        update_interval
in0_crit_alarm     in1_input          power1_crit_alarm
in0_input          in1_lcrit          power1_input
in0_lcrit          in1_lcrit_alarm    shunt_resistor
```

有关 Hwmon Sysfs 的更多信息，请参阅文档：

../hwmon/sysfs-interface.rst

在 I2C Sysfs 中实例化 I2C 设备
------------------------------------

请参阅 instantiating-devices.rst 中“方法 4：从用户空间实例化”部分。
