### SPDX 许可证标识符：GPL-2.0

#### Linux I2C Sysfs

##### 概览

由于 I2C 多路复用器（I2C MUX）的存在，I2C 拓扑结构可能非常复杂。Linux 内核将多路复用器通道抽象为逻辑 I2C 总线编号。然而，在物理 I2C 总线编号、MUX 拓扑结构与逻辑 I2C 总线编号之间存在知识空白。本文档旨在填补这一空白，以便读者（例如硬件工程师和新软件开发者）通过了解物理 I2C 拓扑结构并导航 Linux 壳中的 I2C sysfs 来理解内核中逻辑 I2C 总线的概念。这些知识对于使用 `i2c-tools` 进行开发和调试非常重要。

##### 目标受众

需要在运行 Linux 的系统上使用 Linux 壳与 I2C 子系统交互的人士。

##### 先决条件

1. 熟悉基本的 Linux 壳文件系统命令和操作。
2. 对 I2C、I2C 多路复用器和 I2C 拓扑结构有基本了解。

##### I2C Sysfs 的位置

通常，Linux Sysfs 文件系统挂载在 `/sys` 目录下，因此您可以在 `/sys/bus/i2c/devices` 下找到 I2C Sysfs，并直接进入该目录。
在此目录下有一系列符号链接。以 `i2c-` 开头的链接代表 I2C 总线，可能是物理总线也可能是逻辑总线。其他以数字开头并以数字结尾的链接代表 I2C 设备，其中第一个数字是 I2C 总线编号，第二个数字是 I2C 地址。
例如 Google Pixel 3 手机：

```
blueline:/sys/bus/i2c/devices $ ls
0-0008  0-0061  1-0028  3-0043  4-0036  4-0041  i2c-1  i2c-3
0-000c  0-0066  2-0049  4-000b  4-0040  i2c-0   i2c-2  i2c-4
```

`i2c-2` 是编号为 2 的 I2C 总线，而 `2-0049` 是位于总线 2 上地址 0x49 的 I2C 设备，并与一个内核驱动程序绑定。

##### 术语

首先，为了避免后续章节中的混淆，我们定义一些术语。

- **（物理）I2C 总线控制器**

  运行 Linux 内核的硬件系统可能包含多个物理 I2C 总线控制器。这些控制器是硬件且物理存在的，并且系统可能在内存空间中定义了多个寄存器来控制它们。Linux 内核在源代码目录 `drivers/i2c/busses` 下提供了 I2C 总线驱动程序，用于将内核 I2C API 转换为不同系统的寄存器操作。这个术语不仅仅局限于 Linux 内核。

- **I2C 总线物理编号**

  对于每个物理 I2C 总线控制器，系统供应商可能会为每个控制器分配一个物理编号。例如，具有最低寄存器地址的第一个 I2C 总线控制器可以被命名为 `I2C-0`。
### 逻辑I2C总线
--------------

在Linux I2C Sysfs中看到的每一个I2C总线编号都是一个带有指定编号的逻辑I2C总线。这类似于软件代码通常基于虚拟内存空间编写，而不是物理内存空间。每个逻辑I2C总线可能是对物理I2C总线控制器的抽象，或者是I2C多路复用器（MUX）通道的抽象。如果是MUX通道的抽象，那么当我们通过这样的逻辑总线访问I2C设备时，内核会为你切换I2C MUX到正确的通道，这是抽象的一部分。

### 物理I2C总线
----------------

如果逻辑I2C总线是物理I2C总线控制器的直接抽象，我们称之为物理I2C总线。

### 注意事项
--------------

对于只了解板级物理I2C设计的人来说，这部分可能会令人困惑。实际上，在设备树源文件（DTS）的`aliases`部分中，可以将I2C总线的物理编号重命名为不同的逻辑I2C总线编号。例如，可以查看`arch/arm/boot/dts/nuvoton-npcm730-gsj.dts`这个DTS文件作为示例。

**最佳实践：**（面向内核软件开发者）最好保持I2C总线的物理编号与其对应的逻辑I2C总线编号相同，而不是重命名或映射它们，这样对其他用户来说会更少产生混淆。这些物理I2C总线可以作为从I2C MUX扇出的良好起点。以下示例中，我们将假设物理I2C总线的编号与它们的物理I2C总线编号相同。

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

另一个可以检查的符号链接是`mux_device`。这个链接仅存在于由另一个I2C总线扇出的逻辑I2C总线目录中。读取这个链接也会告诉你哪个I2C MUX设备创建了这个逻辑I2C总线。

如果符号链接指向以`.i2c`结尾的目录，则应该是一个物理I2C总线，直接抽象了一个物理I2C总线控制器。例如：

  ```
  $ readlink /sys/bus/i2c/devices/i2c-7/device
  ../../f0087000.i2c
  $ ls /sys/bus/i2c/devices/i2c-7/mux_device
  ls: /sys/bus/i2c/devices/i2c-7/mux_device: No such file or directory
  ```

在这种情况下，`i2c-7`是一个物理I2C总线，因此在其目录下没有符号链接`mux_device`。如果内核软件开发者遵循不重命名物理I2C总线的常见做法，这也意味着这是系统的物理I2C总线控制器7。
另一方面，如果符号链接指向另一个I2C总线，则当前目录所表示的I2C总线必须是一个逻辑总线。链接指向的I2C总线是父级总线，它可以是物理I2C总线也可以是逻辑总线。在这种情况下，当前目录所表示的I2C总线抽象出了父级总线下一个I2C多路复用器(MUX)的通道。例如：

  * 使用`readlink`命令查看`/sys/bus/i2c/devices/i2c-73/device`：
    ```
    $ readlink /sys/bus/i2c/devices/i2c-73/device
    ../../i2c-7
    ```
  * 使用`readlink`命令查看`/sys/bus/i2c/devices/i2c-73/mux_device`：
    ```
    $ readlink /sys/bus/i2c/devices/i2c-73/mux_device
    ../7-0071
    ```

`i2c-73` 是一个逻辑总线，由位于`i2c-7`上的I2C MUX分发，其I2C地址为0x71。
每当访问带有编号73的I2C设备时，内核总会自动切换到地址为0x71的I2C MUX的正确通道，这是抽象的一部分。

### 查找逻辑I2C总线编号

在本节中，我们将描述如何根据物理硬件I2C拓扑结构的知识来查找表示某些I2C MUX通道的逻辑I2C总线编号。
在这个例子中，我们有一个系统具有物理I2C总线7，并且在DTS中没有重命名。在此总线上有一个地址为0x71的4通道MUX。还有一个地址为0x72的8通道MUX位于0x71 MUX的第1通道后面。让我们通过Sysfs导航并找出0x72 MUX的第3通道的逻辑I2C总线编号。

首先，让我们进入`i2c-7`目录：

  ```
  ~$ cd /sys/bus/i2c/devices/i2c-7
  /sys/bus/i2c/devices/i2c-7$ ls
  7-0071         i2c-60         name           subsystem
  delete_device  i2c-73         new_device     uevent
  device         i2c-86         of_node
  i2c-203        i2c-dev        power
  ```

在那里，我们看到地址为0x71的MUX显示为`7-0071`。进入该目录：

  ```
  /sys/bus/i2c/devices/i2c-7$ cd 7-0071/
  /sys/bus/i2c/devices/i2c-7/7-0071$ ls -l
  channel-0   channel-3   modalias    power
  channel-1   driver      name        subsystem
  channel-2   idle_state  of_node     uevent
  ```

使用`readlink`或`ls -l`读取链接`channel-1`：

  ```
  /sys/bus/i2c/devices/i2c-7/7-0071$ readlink channel-1
  ../i2c-73
  ```

我们发现`i2c-7`上地址为0x71的MUX的第1通道被分配了一个逻辑I2C总线编号73。

让我们继续前往`i2c-73`目录，有几种方法：

  * 进入I2C Sysfs根目录下的`i2c-73`：
    ```
    /sys/bus/i2c/devices/i2c-7/7-0071$ cd /sys/bus/i2c/devices/i2c-73
    /sys/bus/i2c/devices/i2c-73$
    ```
  * 进入通道符号链接：
    ```
    /sys/bus/i2c/devices/i2c-7/7-0071$ cd channel-1
    /sys/bus/i2c/devices/i2c-7/7-0071/channel-1$
    ```
  * 进入链接的内容：
    ```
    /sys/bus/i2c/devices/i2c-7/7-0071$ cd ../i2c-73
    /sys/bus/i2c/devices/i2c-7/i2c-73$
    ```

无论哪种方式，你都会到达`i2c-73`目录。与上面类似，我们现在可以找到0x72 MUX及其各个通道被分配了哪些逻辑I2C总线编号：

  ```
  /sys/bus/i2c/devices/i2c-73$ ls
  73-0040        device         i2c-83         new_device
  73-004e        i2c-78         i2c-84         of_node
  73-0050        i2c-79         i2c-85         power
  73-0070        i2c-80         i2c-dev        subsystem
  73-0072        i2c-81         mux_device     uevent
  delete_device  i2c-82         name
  /sys/bus/i2c/devices/i2c-73$ cd 73-0072
  /sys/bus/i2c/devices/i2c-73/73-0072$ ls
  channel-0   channel-4   driver      of_node
  channel-1   channel-5   idle_state  power
  channel-2   channel-6   modalias    subsystem
  channel-3   channel-7   name        uevent
  /sys/bus/i2c/devices/i2c-73/73-0072$ readlink channel-3
  ../i2c-81
  ```

在那里，我们发现了0x72 MUX的第3通道的逻辑I2C总线编号是81。稍后我们可以使用这个编号切换到其自身的I2C Sysfs目录或者执行`i2c-tools`命令。

**提示：**一旦理解了带MUX的I2C拓扑结构，命令`i2cdetect -l`（如果在你的系统上可用）可以轻松给出I2C拓扑结构的概览。例如：

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

如果没有在DTS中指定，当应用了一个I2C MUX驱动并且MUX设备成功探测时，内核将基于当前最大的逻辑总线编号递增地为MUX通道分配逻辑总线编号。例如，如果系统中`i2c-15`是最高的逻辑总线编号，并且一个4通道MUX成功应用，那么MUX通道0将得到`i2c-16`，一直到MUX通道3得到`i2c-19`。

内核软件开发者能够在DTS中固定分发MUX通道到静态的逻辑I2C总线编号。本文档不会详细介绍如何在DTS中实现这一点，但我们可以看到一个例子：`arch/arm/boot/dts/aspeed-bmc-facebook-wedge400.dts`。

在上述示例中，物理I2C总线2上有一个地址为0x70的8通道I2C MUX。MUX的第2通道在DTS中定义为`imux18`，并用`i2c18 = &imux18;`这一行在`aliases`部分固定到了逻辑I2C总线编号18。

进一步说，有可能设计出一个逻辑I2C总线编号方案，人类容易记住或算术计算得出。例如，我们可以把总线3上的MUX分发通道固定从30开始。因此，总线3上MUX的第0通道的逻辑总线编号将是30，而总线3上MUX的第7通道的逻辑总线编号将是37。
I2C 设备
==========

在之前的章节中，我们主要介绍了 I2C 总线。本节我们将探讨从 I2C 设备目录中可以学到什么，这些目录的链接名称格式为 ``${bus}-${addr}``。其中 ``${bus}`` 部分是逻辑 I2C 总线的十进制数字，而 ``${addr}`` 部分则是每个设备的 I2C 地址的十六进制数。
I2C 设备目录内容
-------------------

在每个 I2C 设备目录内，有一个名为 ``name`` 的文件。
这个文件告诉了内核驱动程序用于探测该设备的设备名。使用命令 `cat` 来读取其内容。例如：

```
/sys/bus/i2c/devices/i2c-73$ cat 73-0040/name
ina230
/sys/bus/i2c/devices/i2c-73$ cat 73-0070/name
pca9546
/sys/bus/i2c/devices/i2c-73$ cat 73-0072/name
pca9547
```

还有一个名为 ``driver`` 的符号链接，它告诉了用于探测该设备的 Linux 内核驱动程序：

```
/sys/bus/i2c/devices/i2c-73$ readlink -f 73-0040/driver
/sys/bus/i2c/drivers/ina2xx
/sys/bus/i2c/devices/i2c-73$ readlink -f 73-0072/driver
/sys/bus/i2c/drivers/pca954x
```

但如果符号链接 ``driver`` 不存在，
可能意味着内核驱动程序由于某些错误未能成功探测到此设备。错误信息可以在 ``dmesg`` 中找到：

```
/sys/bus/i2c/devices/i2c-73$ ls 73-0070/driver
ls: 73-0070/driver: 没有该文件或目录
/sys/bus/i2c/devices/i2c-73$ dmesg | grep 73-0070
pca954x 73-0070: 探测失败
pca954x 73-0070: 探测失败
```

根据 I2C 设备的类型以及用于探测设备的内核驱动程序的不同，设备目录的内容也会有所不同。
I2C 多路复用器 (MUX) 设备
-----------------------

如您之前已经了解到的那样，I2C MUX 设备在其设备目录内会有符号链接 ``channel-*``。
这些符号链接指向它们对应的逻辑 I2C 总线目录：

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
------------------------

I2C 传感器设备也很常见。如果它们被内核 hwmon（硬件监控）驱动程序成功绑定，您会在 I2C 设备目录内看到一个 ``hwmon`` 目录。继续深入挖掘，您将找到 I2C 传感器设备的 Hwmon Sysfs：

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
```
../hwmon/sysfs-interface.rst
```

在 I2C Sysfs 中实例化 I2C 设备
------------------------------------

请参阅 `instantiating-devices.rst` 文件中的 "方法 4：从用户空间实例化" 部分。
