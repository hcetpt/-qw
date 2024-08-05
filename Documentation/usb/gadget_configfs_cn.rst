============================================
通过 configfs 配置的 Linux USB Gadget
============================================

2013 年 4 月 25 日


概述
========

一个 USB Linux Gadget 是一种具有 UDC（USB 设备控制器）的设备，可以连接到 USB 主机以扩展其功能，如串行端口或大容量存储能力。从主机的角度来看，Gadget 是一系列配置的集合，每个配置包含多个接口，在 Gadget 的视角下，这些接口被称为功能，每个功能代表例如一个串行连接或 SCSI 磁盘。Linux 提供了许多 Gadget 可以使用的功能。

创建一个 Gadget 意味着决定将有哪些配置，以及每个配置将提供哪些功能。Configfs（请参见 `Documentation/filesystems/configfs.rst`）非常适合用于向内核告知上述决策。本文档将介绍如何实现这一过程，同时也会描述 configfs 如何集成到 Gadget 中的设计。

要求
============

为了使这一切生效，configfs 必须可用，因此 `.config` 文件中的 `CONFIGFS_FS` 必须是 `'y'` 或 `'m'`。截至本文档编写之时，`USB_LIBCOMPOSITE` 已选择 `CONFIGFS_FS`。

使用
=====

（最初描述通过 configfs 提供的第一个功能的帖子可在此处查看：http://www.spinics.net/lists/linux-usb/msg76388.html）

```
$ modprobe libcomposite
$ mount none $CONFIGFS_HOME -t configfs
```

其中 `$CONFIGFS_HOME` 是 configfs 的挂载点。

1. 创建 Gadget
-----------------------

对于要创建的每个 Gadget，都需要创建相应的目录：

```
$ mkdir $CONFIGFS_HOME/usb_gadget/<gadget 名称>
```

例如：

```
$ mkdir $CONFIGFS_HOME/usb_gadget/g1
```
翻译成中文：

$ cd $CONFIGFS_HOME/usb_gadget/g1

每个设备都需要指定其供应商ID (<VID>) 和产品ID (<PID>) ：

	$ echo <VID> > idVendor
	$ echo <PID> > idProduct

一个设备还需要其序列号、制造商和产品字符串。为了有一个地方来存储它们，必须为每种语言创建一个字符串子目录，例如：

	$ mkdir strings/0x409

然后可以指定这些字符串：

	$ echo <序列号> > strings/0x409/serialnumber
	$ echo <制造商> > strings/0x409/manufacturer
	$ echo <产品> > strings/0x409/product

可以在语言目录内创建更多的自定义字符串描述符作为目录，并将字符串文本写入该字符串目录内的 "s" 属性中：

	$ mkdir strings/0x409/xu.0
	$ echo <字符串文本> > strings/0x409/xu.0/s

如果功能驱动程序支持，可以通过这些自定义字符串描述符的符号链接将这些字符串与类描述符关联起来。

2. 创建配置
--------------

每个设备将包含多个配置，需要为其对应的目录创建这些配置：

$ mkdir configs/<名称>.<编号>

其中 <名称> 可以是文件系统中合法的任何字符串，而 <编号> 是配置的编号，例如：

	$ mkdir configs/c.1

每个配置也需要其字符串，因此必须为每种语言创建一个子目录，例如：

	$ mkdir configs/c.1/strings/0x409

然后可以指定配置字符串：

	$ echo <配置> > configs/c.1/strings/0x409/configuration

还可以为配置设置一些属性，例如：

	$ echo 120 > configs/c.1/MaxPower

3. 创建功能
--------------

设备将提供一些功能，对于每个功能，需要创建其相应的目录：

	$ mkdir functions/<名称>.<实例名称>

其中 <名称> 对应于允许的功能名称之一，而实例名称是在文件系统中允许的任意字符串，例如：

  $ mkdir functions/ncm.usb0 # 加载 usb_f_ncm.ko 模块

每个功能提供一组特定的属性，具有只读或可读写访问权限。在适用的情况下，需要相应地写入这些属性。
请参阅 `Documentation/ABI/testing/configfs-usb-gadget` 获取更多信息。
4. 将功能与配置关联
----------------------

此时已经创建了多个设备（gadgets），每个设备都有指定的配置和可用的功能。剩下的就是指定哪些功能在哪些配置中可用（同一个功能可以在多个配置中使用）。这是通过创建符号链接来实现的：

```
$ ln -s functions/<name>.<instance name> configs/<name>.<number>
```

例如：

```
$ ln -s functions/ncm.usb0 configs/c.1
```

...
...
...
5. 启用设备
------------

以上所有步骤都是为了组合配置和功能以构成设备。
一个示例目录结构可能如下所示：
```
./strings
  ./strings/0x409
  ./strings/0x409/serialnumber
  ./strings/0x409/product
  ./strings/0x409/manufacturer
  ./configs
  ./configs/c.1
  ./configs/c.1/ncm.usb0 -> ../../../../usb_gadget/g1/functions/ncm.usb0
  ./configs/c.1/strings
  ./configs/c.1/strings/0x409
  ./configs/c.1/strings/0x409/configuration
  ./configs/c.1/bmAttributes
  ./configs/c.1/MaxPower
  ./functions
  ./functions/ncm.usb0
  ./functions/ncm.usb0/ifname
  ./functions/ncm.usb0/qmult
  ./functions/ncm.usb0/host_addr
  ./functions/ncm.usb0/dev_addr
  ./UDC
  ./bcdUSB
  ./bcdDevice
  ./idProduct
  ./idVendor
  ./bMaxPacketSize0
  ./bDeviceProtocol
  ./bDeviceSubClass
  ./bDeviceClass
```

这样的设备必须最终启用，以便USB主机可以枚举它。要启用设备，必须将其绑定到UDC（USB设备控制器）：

```
$ echo <udc name> > UDC
```

其中 `<udc name>` 是在 `/sys/class/udc/*` 中找到的一个名称，例如：

```
$ echo s3c-hsotg > UDC
```


6. 禁用设备
------------

```
$ echo "" > UDC
```

7. 清理
------------

从配置中移除功能：

```
$ rm configs/<config name>.<number>/<function>
```

其中 `<config name>.<number>` 指定配置，而 `<function>` 是指向要从配置中移除的功能的符号链接，例如：

```
$ rm configs/c.1/ncm.usb0
```
在配置中移除字符串目录：

    $ rmdir configs/<配置名称>.<编号>/strings/<语言>

例如：

    $ rmdir configs/c.1/strings/0x409

...

并移除配置：

    $ rmdir configs/<配置名称>.<编号>

例如：

    $ rmdir configs/c.1

...

移除功能（请注意，功能模块不会被卸载）：

    $ rmdir functions/<名称>.<实例名称>

例如：

    $ rmdir functions/ncm.usb0

...

在设备中移除字符串目录：

    $ rmdir strings/<语言>

例如：

    $ rmdir strings/0x409

最后，移除设备：

    $ cd .
翻译成中文:

```
rmdir <gadget 名称>

例如: 

    $ rmdir g1
```

### 实现设计

下面是关于 configfs 如何工作的基本思路。在 configfs 中，有项目（items）和组（groups），它们都被表示为目录。

项目（item）和组（group）之间的区别在于组可以包含其他组。下面的图示只展示了一个项目。
项目（items）和组（groups）都可以有属性，这些属性被表示为文件。用户可以创建和删除目录，但不能删除文件，这些文件可能是只读或可读写，具体取决于它们所代表的内容。
configfs 文件系统部分操作的对象是 config_items/groups 和 configfs 属性，这些都是通用的，并且对于所有配置元素来说类型都相同。然而，它们嵌入在特定用途的较大结构中。下图中有一个 "cs" 包含一个 config_item 和一个 "sa" 包含一个 configfs_attribute。
文件系统的视图将如下所示：

```
./
./cs         (目录)
     |
     +--sa   (文件)
     |
```

每当用户读取/写入 "sa" 文件时，会调用一个函数，该函数接受一个 struct config_item 和一个 struct configfs_attribute 作为参数。
在所述功能中，“cs”和“sa”使用众所周知的container_of技术进行检索，并调用适当的sa函数（显示或存储），并将“cs”和一个字符缓冲区传递给该函数。“显示”用于展示文件的内容（从cs复制数据到缓冲区），而“存储”则用于修改文件的内容（从缓冲区复制数据到cs），但具体执行什么操作则取决于这两个函数的实现者。

```plaintext
typedef struct configured_structure cs;
typedef struct specific_attribute sa;

                                             sa
                         +----------------------------------+
          cs              |  (*show)(cs *, buffer);          |
  +-----------------+     |  (*store)(cs *, buffer, length); |
  |                 |     |                                  |
  | +-------------+ |     |       +------------------+       |
  | | struct      |-|-----|-------|struct            |       |
  | | config_item | |     |       |configfs_attribute|       |
  | +-------------+ |     |       +------------------+       |
  |                 |     +----------------------------------+
  | data to be set  |
  |                 |
+-----------------+
```

文件名由配置项/组设计者决定，而目录名称通常可以随意指定。一个组可以有其默认子组自动创建。

关于configfs的更多信息，请参阅 `Documentation/filesystems/configfs.rst`

上述概念可以这样应用于USB小工具：

1. 小工具有其配置组，该组具有一些属性（如 idVendor、idProduct 等）以及默认子组（如 configs、functions 和 strings）。写入这些属性会导致信息被存储在适当的位置。在 configs、functions 和 strings 子组中，用户可以创建自己的子组来表示配置、功能和特定语言中的字符串组。
2. 用户创建配置和功能，在配置中创建指向功能的符号链接。当小工具的 UDC 属性被写入时，即绑定小工具到 UDC，会用到这些信息。在 drivers/usb/gadget/configfs.c 中的代码遍历所有配置，并在每个配置中遍历所有功能以将它们绑定起来。这样整个小工具就被绑定了。
3. 文件 drivers/usb/gadget/configfs.c 包含以下代码：

   - 小工具的 config_group
   - 小工具的默认组（configs、functions、strings）
   - 功能与配置之间的关联（符号链接）

4. 每个USB功能自然会有它自己想要配置的观点，因此特定功能的 config_groups 在功能实现文件 drivers/usb/gadget/f_*.c 中定义。
```
函数的代码是这样编写的，它使用了 `usb_get_function_instance()`，而后者又会调用 `request_module`。因此，只要 `modprobe` 能正常工作，特定函数所需的模块就会被自动加载。请注意，反之则不然：在设备功能被禁用并拆除后，这些模块仍然保持已加载的状态。
