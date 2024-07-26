MIDI 2.0 在 Linux 上的应用
=================

概述
=====

MIDI 2.0 是一种扩展协议，旨在提供比传统 MIDI 1.0 更高的分辨率和更精细的控制。为了支持 MIDI 2.0 而进行的基础性改变包括：

- 支持通用 MIDI 数据包（UMP）
- 支持 MIDI 2.0 协议消息
- 在 UMP 和传统 MIDI 1.0 字节流之间进行透明转换
- 使用 MIDI 配置交互 (MIDI-CI) 进行属性和配置文件设置

UMP 是一种新的容器格式，用于容纳所有的 MIDI 协议 1.0 和 MIDI 2.0 协议消息。与之前的字节流不同，UMP 是以 32 位对齐的，并且每条消息都可以放入一个单独的数据包中。UMP 可以发送事件到最多 16 个“UMP 组”，每个 UMP 组可以包含最多 16 个 MIDI 通道。
MIDI 2.0 协议是一种扩展协议，可实现比旧版 MIDI 1.0 协议更高的分辨率和更多的控制功能。
MIDI-CI 是一种高级协议，可以与 MIDI 设备通信以实现灵活的配置文件和配置设置。它以特殊 SysEx 的形式表示。
在 Linux 实现中，内核支持 UMP 传输层以及 UMP 上 MIDI 协议的编码/解码，而 MIDI-CI 则通过标准 SysEx 在用户空间中得到支持。
截至本文撰写时，只有 USB MIDI 设备原生支持 UMP 和 Linux 2.0。UMP 支持本身非常通用，因此也可被其他传输层使用，尽管其实施方式可能有所不同（例如，作为 ALSA 序列器客户端）。
UMP 设备的访问提供了两种方式：通过 rawmidi 设备访问和通过 ALSA 序列器 API 访问。
ALSA 序列器 API 已经进行了扩展，以允许 UMP 数据包的有效载荷。
允许 MIDI 1.0 和 MIDI 2.0 序列器客户端之间的自由连接，事件会在这些连接间进行透明转换。

内核配置
==========

为了支持 MIDI 2.0，添加了以下新的配置项：`CONFIG_SND_UMP`、`CONFIG_SND_UMP_LEGACY_RAWMIDI`、`CONFIG_SND_SEQ_UMP`、`CONFIG_SND_SEQ_UMP_CLIENT` 和 `CONFIG_SND_USB_AUDIO_MIDI_V2`。首先出现的是 `CONFIG_SND_USB_AUDIO_MIDI_V2`，当你选择它（设置为 `=y`）时，UMP 的核心支持 (`CONFIG_SND_UMP`) 和序列器绑定 (`CONFIG_SND_SEQ_UMP_CLIENT`) 将自动被选中。
此外，如果将 `CONFIG_SND_UMP_LEGACY_RAWMIDI=y` 设置为启用，则会支持 UMP 端点的传统 raw MIDI 设备。
当设备支持MIDI 2.0时，USB音频驱动程序会探测并默认使用MIDI 2.0接口（该接口始终位于altset 1），而不是MIDI 1.0接口（位于altset 0）。您也可以通过向snd-usb-audio驱动模块传递`midi2_enable=0`选项来切换回使用旧的MIDI 1.0接口。USB音频驱动程序尝试查询自UMP v1.1起提供的UMP端点和UMP功能块信息，并基于这些信息构建拓扑结构。如果设备较旧且不响应新的UMP查询，则驱动程序会退回到根据USB描述符中的组终端块（GTB）信息构建拓扑结构。某些设备可能会因意外的UMP命令而出现问题；在这种情况下，可以通过向snd-usb-audio驱动传递`midi2_ump_probe=0`选项来跳过UMP v1.1的查询。

当探测到MIDI 2.0设备时，内核会为设备的每个UMP端点创建一个rawmidi设备。其设备名称为`/dev/snd/umpC*D*`，与MIDI 1.0的标准rawmidi设备名`/dev/snd/midiC*D*`不同，这样做是为了避免遗留应用程序错误地访问UMP设备。

您可以直接从这个UMP rawmidi设备读取和写入UMP数据包。例如，以下命令将显示卡0设备0的传入UMP数据包的十六进制格式：

```
% hexdump -C /dev/snd/umpC0D0
00000000  01 07 b0 20 00 07 b0 20  64 3c 90 20 64 3c 80 20  |... ... d<. d<. |
```

与MIDI 1.0字节流不同，UMP是一个32位数据包，因此从设备读取或写入的数据大小也按32位对齐（即4字节）。

UMP数据包的有效载荷中的32位单词总是采用CPU本机字节序。传输驱动程序负责将UMP单词从/到系统字节序转换为所需的传输字节序/字节顺序。

当设置了`CONFIG_SND_UMP_LEGACY_RAWMIDI`配置项时，驱动程序还会额外创建一个标准的raw MIDI设备，路径为`/dev/snd/midiC*D*`。
该设备包含16个子流，每个子流对应一个（从0开始计数的）UMP组。遗留应用程序可以以MIDI 1.0字节流格式通过每个子流访问指定的组。利用ALSA rawmidi API，您可以打开任意子流，而仅打开`/dev/snd/midiC*D*`将最终打开第一个子流。

每个UMP端点可以提供附加信息，这些信息是从UMP 1.1流消息或USB MIDI 2.0描述符中获取的信息构造而成。UMP端点可能包含一个或多个UMP块，其中UMP块是ALSA UMP实现中引入的一个抽象概念，用于表示UMP组之间的关联关系。UMP块对应于UMP 1.1规范中的功能块。当UMP 1.1功能块信息不可用时，可以从USB MIDI 2.0规范定义的组终端块（GTB）部分填充。

UMP端点和UMP块的信息可以在`/proc/asound/card*/midi*`文件中找到。例如：

```
% cat /proc/asound/card1/midi0
ProtoZOA MIDI
  
Type: UMP
EP Name: ProtoZOA
EP Product ID: ABCD12345678
UMP Version: 0x0000
Protocol Caps: 0x00000100
Protocol: 0x00000100
Num Blocks: 3
  
Block 0 (ProtoZOA Main)
  Direction: bidirectional
  Active: Yes
  Groups: 1-1
  Is MIDI1: No

Block 1 (ProtoZOA Ext IN)
  Direction: output
  Active: Yes
  Groups: 2-2
  Is MIDI1: Yes (Low Speed)
...
```

请注意，上述`proc`文件中显示的`Groups`字段表示的是基于1的UMP组编号（从-到）。
这些额外的 UMP Endpoint 和 UMP Block 信息可以通过新的 ioctl 命令 `SNDRV_UMP_IOCTL_ENDPOINT_INFO` 和 `SNDRV_UMP_IOCTL_BLOCK_INFO` 分别获取。
Rawmidi 名称和 UMP Endpoint 名称通常相同，对于 USB MIDI 设备来说，它取自相应的 USB MIDI 接口描述符中的 `iInterface`。如果没有提供，则作为备选方案从 USB 设备描述符中的 `iProduct` 复制。
Endpoint 的产品 ID 是一个字符串字段，应当是唯一的。对于 USB MIDI 设备，它从设备的 `iSerialNumber` 复制而来。
协议能力及实际的协议位定义在 `asound.h` 中。

### ALSA 序列器与 USB MIDI 2.0

除了 rawmidi 接口外，ALSA 序列器接口还支持新的 UMP MIDI 2.0 设备。现在，每个 ALSA 序列器客户端可以设置其 MIDI 版本（0、1 或 2），以此声明自己为传统的设备、UMP MIDI 1.0 设备或 UMP MIDI 2.0 设备。
第一个传统客户端是指发送/接收旧序列事件的客户端。同时，UMP MIDI 1.0 和 2.0 客户端通过扩展的事件记录来发送和接收 UMP 数据。MIDI 版本可以在 `snd_seq_client_info` 结构体的新字段 `midi_version` 中看到。
一个 UMP 包可通过设置新的事件标志位 `SNDRV_SEQ_EVENT_UMP` 在序列器事件中发送/接收。当设置了这个标志位时，事件有 16 字节（128 位）的数据负载来存放 UMP 包。如果没有设置 `SNDRV_SEQ_EVENT_UMP` 标志位，事件则被视为传统事件处理（最大 12 字节数据负载）。
当设置了 `SNDRV_SEQ_EVENT_UMP` 标志位时，UMP 序列器事件的类型字段被忽略（但默认应设为 0）。
每个客户端的类型可以在 `/proc/asound/seq/clients` 中查看。
例如：

  % cat /proc/asound/seq/clients
  客户端信息
    当前客户端数：3
  ...
  客户端 14： "Midi Through" [内核Legacy]
    端口 0： "Midi Through Port-0" (RWe-)
  客户端 20： "ProtoZOA" [内核UMP MIDI1]
    UMP终端点：ProtoZOA
    UMP块0：ProtoZOA 主 [活动]
      组：1-1
    UMP块1：ProtoZOA Ext IN [活动]
      组：2-2
    UMP块2：ProtoZOA Ext OUT [活动]
      组：3-3
    端口 0： "MIDI 2.0" (RWeX) [输入/输出]
    端口 1： "ProtoZOA 主" (RWeX) [输入/输出]
    端口 2： "ProtoZOA Ext IN" (-We-) [输出]
    端口 3： "ProtoZOA Ext OUT" (R-e-) [输入]

这里你可以找到两种类型的内核客户端，"Legacy" 对应客户端 14，
而 "UMP MIDI1" 对应客户端 20，这是一个USB MIDI 2.0 设备。
一个USB MIDI 2.0 客户端总是将端口 0 标记为 "MIDI 2.0"，其余的端口从 1 开始对应每个 UMP 组（例如，端口 1 对应组 1）。
在这个例子中，设备有三个活动组（主、Ext IN 和 Ext OUT），它们作为序列器端口从 1 到 3 显示出来。
"MIDI 2.0" 端口是为 UMP 终端点准备的，它与其它 UMP 组端口的区别在于 UMP 终端点端口会发送设备上所有端口的事件（“全接收”），而每个 UMP 组端口只发送给定 UMP 组的事件。
另外，没有分配到特定组的 UMP 消息（例如 UMP 消息类型 0x0f）仅被发送到 UMP 终端点端口。
需要注意的是，尽管每个 UMP 序列器客户端通常创建 16 个端口，但那些不属于任何 UMP 块（或属于不活动的 UMP 块）的端口会被标记为不活动，并且不会出现在 /proc 输出中。在上面的例子中，序列器端口从 4 到 16 都存在，但并未在那里显示。
上述 /proc 文件还显示了 UMP 块的信息。同样的条目（但包含更详细的信息）可以在 rawmidi 的 /proc 输出中找到。
当不同 MIDI 版本之间的客户端相互连接时，事件会根据客户端的版本自动转换，不仅包括 Legacy 和 UMP MIDI 1.0/2.0 类型之间，还包括 UMP MIDI 1.0 和 2.0 类型之间。例如，在 Legacy 模式下通过 `aseqdump` 程序监听 ProtoZOA 主端口时，你将得到如下输出：

  % aseqdump -p 20:1
  等待数据。按 Ctrl+C 结束
源  事件                      通道  数据
   20:1   音符按下                 0, 音符 60, 速度 100
   20:1   音符抬起                0, 音符 60, 速度 100
   20:1   控制变化          0, 控制器 11, 值 4

当你以 MIDI 2.0 模式运行 `aseqdump` 时，它将接收到高精度的数据，例如：

  % aseqdump -u 2 -p 20:1
  等待数据。按 Ctrl+C 结束
### 源 事件                  通道  数据
   20:1   音符按下                 0, 音符 60, 强度 0xc924, 属性类型 = 0, 数据 = 0x0
   20:1   音符释放                0, 音符 60, 强度 0xc924, 属性类型 = 0, 数据 = 0x0
   20:1   控制改变              0, 控制器 11, 值 0x2000000

这些数据由ALSA序列器核心自动转换。

#### Rawmidi API 扩展
* 可以通过新的ioctl命令`SNDRV_UMP_IOCTL_ENDPOINT_INFO`获取额外的UMP终端信息。它包含了关联的声卡和设备编号、位标志、协议、UMP块的数量、终端名称字符串等。
  * 协议在两个字段中指定：协议能力与当前协议。两者都用位标志指定了MIDI协议版本（`SNDRV_UMP_EP_INFO_PROTO_MIDI1`或`SNDRV_UMP_EP_INFO_PROTO_MIDI2`）在高位字节，以及抖动减少的时间戳（`SNDRV_UMP_EP_INFO_PROTO_JRTS_TX`和`SNDRV_UMP_EP_INFO_PROTO_JRTS_RX`）在低位字节。
  * 一个UMP终端最多可以包含32个UMP块，并且当前分配的块数会在终端信息中显示出来。
* 每个UMP块的信息可以通过另一个新的ioctl命令`SNDRV_UMP_IOCTL_BLOCK_INFO`获取。需要为要查询的块传递块ID号（从0开始）。接收到的数据包含了块的方向、第一个关联组ID（从0开始）及组的数量、块的名称字符串等。
  * 方向可以是`SNDRV_UMP_DIR_INPUT`、`SNDRV_UMP_DIR_OUTPUT`或`SNDRV_UMP_DIR_BIDIRECTION`。
* 对于支持UMP v1.1的设备，UMP MIDI协议可以通过“流配置请求”消息（UMP类型0x0f，状态0x05）进行切换。当UMP核心接收到这样的消息时，它会更新UMP EP信息以及相应的序列器客户端。

### 控制API扩展
* 新增了ioctl命令`SNDRV_CTL_IOCTL_UMP_NEXT_DEVICE`来查询下一个UMP rawmidi设备，而现有的ioctl命令`SNDRV_CTL_IOCTL_RAWMIDI_NEXT_DEVICE`只查询传统的rawmidi设备。
  * 若要设置要打开的子设备（子流编号），可以使用ioctl命令`SNDRV_CTL_IOCTL_RAWMIDI_PREFER_SUBDEVICE`，就像处理普通的rawmidi一样。
* 两个新的ioctl命令`SNDRV_CTL_IOCTL_UMP_ENDPOINT_INFO`和`SNDRV_CTL_IOCTL_UMP_BLOCK_INFO`通过ALSA控制API提供了指定UMP设备的UMP终端和UMP块的信息，无需实际打开（UMP）rawmidi设备。
`card`字段在查询时被忽略，始终与控制界面的卡片绑定。

Sequencer API 扩展
==================

* 在`snd_seq_client_info`中添加了`midi_version`字段来指示每个客户端当前的MIDI版本（0、1 或 2）。
当`midi_version`为1或2时，从UMP序器客户端读取的对齐也从之前的28字节更改为32字节以适应扩展的有效负载。写入的对齐大小没有改变，但每个事件的大小可能因下面的新位标志而有所不同。
* 为每个序器事件标志添加了`SNDRV_SEQ_EVENT_UMP`位标志。当设置了此位标志时，序器事件将扩展到具有更大的16字节有效负载而非传统的12字节，并且事件包含有效负载中的UMP数据包。
* 新的序器端口类型位`SNDRV_SEQ_PORT_TYPE_MIDI_UMP`表示端口支持UMP功能。
* 序器端口新增了能力位以指示非活动端口(`SNDRV_SEQ_PORT_CAP_INACTIVE`)和UMP终结点端口(`SNDRV_SEQ_PORT_CAP_UMP_ENDPOINT`)。
* ALSA序器客户端的事件转换可以通过在客户端信息中设置新的过滤位`SNDRV_SEQ_FILTER_NO_CONVERT`来抑制。
例如，内核直通客户端(`snd-seq-dummy`)内部设置了此标志。
* 端口信息中新增了一个字段`direction`，用于指示端口的方向（输入`SNDRV_SEQ_PORT_DIR_INPUT`、输出`SNDRV_SEQ_PORT_DIR_OUTPUT`或双向`SNDRV_SEQ_PORT_DIR_BIDIRECTION`）。
* 端口信息中另一个额外字段是`ump_group`，它指定了关联的UMP组编号（基于1的编号）。
当该值非零时，UMP数据包中针对指定组更新的UMP组字段（修正为以0为基础）。
每个序列器端口如果特定于某个UMP组，则应设置此字段。
* 每个客户端可以在`group_filter`位图中设置额外的事件过滤器用于UMP组。过滤器由从1开始的组号位图组成。例如，如果设置了第1位，则来自第1组（即第一个组）的消息将被过滤掉，并不会被传递。第0位用于过滤无UMP组的消息。
* 添加了两种新的ioctl供支持UMP的客户端使用：`SNDRV_SEQ_IOCTL_GET_CLIENT_UMP_INFO`和`SNDRV_SEQ_IOCTL_SET_CLIENT_UMP_INFO`。它们用于获取或设置与序列器客户端关联的`snd_ump_endpoint_info`或`snd_ump_block_info`数据。USB MIDI驱动程序从底层UMP原始MIDI提供这些信息，而用户空间客户端可以通过`*_SET` ioctl提供其自定义数据。
对于Endpoint数据，`type`字段传递0；而对于Block数据，传递块号+1到`type`字段。
对于内核客户端设置数据将导致错误。
* 在UMP 1.1版本中，功能块信息可以动态更改。当从设备接收到功能块更新时，ALSA序列器核心会相应地更改对应的序列器端口名称和属性，并通过向ALSA序列器系统端口发布公告来通知这些更改，类似于正常的端口更改通知。
MIDI2 USB小工具功能驱动
=======================

最新内核包含了对USB MIDI 2.0小工具功能驱动的支持，可用于原型设计和调试MIDI 2.0特性。
需要启用`CONFIG_USB_GADGET`、`CONFIG_USB_CONFIGFS`和`CONFIG_USB_CONFIGFS_F_MIDI2`配置项以便使用MIDI2小工具驱动。
此外，使用小工具驱动程序时，你需要一个可用的UDC（通用设备控制器）驱动程序。
在下面的例子中，我们使用`dummy_hcd`驱动程序（通过`CONFIG_USB_DUMMY_HCD`启用），它在个人电脑和虚拟机上可用于调试目的。根据平台的不同，还有其他的UDC驱动程序，这些也可以用于真正的设备。

首先，在要运行该小工具的系统上加载`libcomposite`模块：

  % modprobe libcomposite

然后你会在configfs空间下找到一个名为`usb_gadget`的子目录（通常在现代操作系统中的路径为`/sys/kernel/config`）。接着创建一个小工具实例并在那里添加配置，例如：

  % cd /sys/kernel/config
  % mkdir usb_gadget/g1

  % cd usb_gadget/g1
  % mkdir configs/c.1
  % mkdir functions/midi2.usb0

  % echo 0x0004 > idProduct
  % echo 0x17b3 > idVendor
  % mkdir strings/0x409
  % echo "ACME Enterprises" > strings/0x409/manufacturer
  % echo "ACMESynth" > strings/0x409/product
  % echo "ABCD12345" > strings/0x409/serialnumber

  % mkdir configs/c.1/strings/0x409
  % echo "Monosynth" > configs/c.1/strings/0x409/configuration
  % echo 120 > configs/c.1/MaxPower

此时，应该会有一个名为`ep.0`的子目录，这是UMP端点的配置。你可以像这样填写端点信息：

  % echo "ACMESynth" > functions/midi2.usb0/iface_name
  % echo "ACMESynth" > functions/midi2.usb0/ep.0/ep_name
  % echo "ABCD12345" > functions/midi2.usb0/ep.0/product_id
  % echo 0x0123 > functions/midi2.usb0/ep.0/family
  % echo 0x4567 > functions/midi2.usb0/ep.0/model
  % echo 0x123456 > functions/midi2.usb0/ep.0/manufacturer
  % echo 0x12345678 > functions/midi2.usb0/ep.0/sw_revision

默认的MIDI协议可以设置为1或2：

  % echo 2 > functions/midi2.usb0/ep.0/protocol

你可以在这个端点子目录下找到一个名为`block.0`的子目录。这定义了功能块的信息：

  % echo "Monosynth" > functions/midi2.usb0/ep.0/block.0/name
  % echo 0 > functions/midi2.usb0/ep.0/block.0/first_group
  % echo 1 > functions/midi2.usb0/ep.0/block.0/num_groups

最后，链接配置并启用它：

  % ln -s functions/midi2.usb0 configs/c.1
  % echo dummy_udc.0 > UDC

其中`dummy_udc.0`是一个示例情况，它取决于系统。你可以在`/sys/class/udc`中找到UDC实例，并将找到的名称传递：

  % ls /sys/class/udc
  dummy_udc.0

现在，MIDI 2.0小工具设备已被启用，小工具主机通过`f_midi2`驱动程序创建了一个包含UMP rawmidi设备的新声卡实例：

  % cat /proc/asound/cards
  ...
1 [Gadget         ]: f_midi2 - MIDI 2.0 Gadget
                       MIDI 2.0 Gadget

在连接的主机上，也会出现类似的声卡，但其名称和设备名称与上面configfs中指定的一致：

  % cat /proc/asound/cards
  ...
2 [ACMESynth      ]: USB-Audio - ACMESynth
                       ACME Enterprises ACMESynth at usb-dummy_hcd.0-1, high speed

你可以在小工具侧播放MIDI文件：

  % aplaymidi -p 20:1 to_host.mid

这会在连接的主机上显示为来自MIDI设备的输入：

  % aseqdump -p 20:0 -u 2

反之，在连接的主机上的播放也将在小工具上作为输入工作。
每个功能块可能有不同的方向和UI提示，这些可以通过`direction`和`ui_hint`属性来指定。
传递`1`表示仅输入，`2`表示仅输出，`3`表示双向（默认值）。例如：

  % echo 2 > functions/midi2.usb0/ep.0/block.0/direction
  % echo 2 > functions/midi2.usb0/ep.0/block.0/ui_hint

如果你需要多个功能块，你可以动态创建`block.1`、`block.2`等子目录，并在链接前按照上述配置过程进行配置。
例如，为了创建第二个键盘功能块：

  % mkdir functions/midi2.usb0/ep.0/block.1
  % echo "Keyboard" > functions/midi2.usb0/ep.0/block.1/name
  % echo 1 > functions/midi2.usb0/ep.0/block.1/first_group
  % echo 1 > functions/midi2.usb0/ep.0/block.1/num_groups
  % echo 1 > functions/midi2.usb0/ep.0/block.1/direction
  % echo 1 > functions/midi2.usb0/ep.0/block.1/ui_hint

`block.*`子目录也可以动态删除（除了持久存在的`block.0`）。
为了分配MIDI 1.0 I/O的功能块，请在`is_midi1`属性中设置。`1`表示MIDI 1.0，`2`表示低速连接下的MIDI 1.0：

  % echo 2 > functions/midi2.usb0/ep.0/block.1/is_midi1

为了禁用小工具驱动程序中的UMP流消息处理，可以在顶级配置中将`0`传递给`process_ump`属性：

  % echo 0 > functions/midi2.usb0/process_ump

小工具驱动程序还支持altset 0下的MIDI 1.0接口。当连接的主机选择了MIDI 1.0接口时，小工具上的UMP I/O会相应地转换为/从USB MIDI 1.0数据包，而小工具驱动程序继续通过UMP rawmidi与用户空间通信。
MIDI 1.0端口可以从每个功能块的配置中设置。
例如：

  % echo 0 > functions/midi2.usb0/ep.0/block.0/midi1_first_group
  % echo 1 > functions/midi2.usb0/ep.0/block.0/midi1_num_groups

上述配置将启用MIDI 1.0接口的第1组（索引为0）。请注意，这些组必须在功能块本身定义的组内。
设备驱动程序也支持多个UMP端点。与功能块类似，您可以在卡片顶层配置下创建一个名为`ep.1`的新子目录以启用一个新的端点：

  % mkdir functions/midi2.usb0/ep.1

然后在那里创建一个新的功能块。例如，要为此新端点的功能块创建4个组：

  % mkdir functions/midi2.usb0/ep.1/block.0
  % echo 4 > functions/midi2.usb0/ep.1/block.0/num_groups

现在，您总共有4个rawmidi设备：前两个是针对端点0和端点1的UMP rawmidi设备，另外两个则是对应于端点0和端点1的传统MIDI 1.0 rawmidi设备。
当前设备上的备用设置可以通过带有`RAWMIDI`接口的“操作模式”控制元素来告知。例如，您可以通过在设备主机上运行`amixer`程序来读取它：

  % amixer -c1 cget iface=RAWMIDI,name='Operation Mode'
  ; 类型=整数,访问权限=r--v----,值数=1,最小值=0,最大值=2,步长=0
  : 值=2

返回的第二行中的值（以`: 值=`显示）表示：1代表MIDI 1.0（备用设置0），2代表MIDI 2.0（备用设置1），而0则表示未设置。
截至目前，绑定后无法更改配置。
