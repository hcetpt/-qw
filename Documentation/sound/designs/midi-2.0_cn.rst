MIDI 2.0在Linux上的应用
=================

概述
=======

MIDI 2.0是一种扩展协议，用于提供比传统MIDI 1.0更高的分辨率和更精细的控制。为了支持MIDI 2.0而引入的基本变化包括：

- 支持通用MIDI数据包（UMP）
- 支持MIDI 2.0协议消息
- 在UMP和传统MIDI 1.0字节流之间进行透明转换
- 通过MIDI-CI进行属性和配置文件的配置

UMP是一种新的容器格式，可以容纳所有MIDI 1.0和MIDI 2.0协议消息。与之前的字节流不同，UMP是32位对齐的，并且每个消息都可以放在一个单独的数据包中。UMP可以发送事件到最多16个“UMP组”，每个UMP组包含最多16个MIDI通道。
MIDI 2.0协议是一种扩展协议，以实现比旧版MIDI 1.0协议更高的分辨率和更多的控制。
MIDI-CI是一种高级协议，可以与MIDI设备通信以灵活地配置文件和设置。它以特殊的SysEx形式表示。
对于Linux的实现，内核支持UMP传输以及UMP上的MIDI协议编码/解码，而MIDI-CI则在用户空间通过标准SysEx来支持。
截至本文撰写时，只有USB MIDI设备原生支持UMP和Linux 2.0。UMP支持本身非常通用，因此也可以被其他传输层使用，尽管其实现方式可能不同（例如作为ALSA序列器客户端）。
UMP设备的访问提供了两种方式：通过rawmidi设备访问和通过ALSA序列器API访问。
ALSA序列器API进行了扩展，允许UMP数据包的有效载荷。可以在MIDI 1.0和MIDI 2.0序列器客户端之间自由连接，并且事件会透明地进行转换。

内核配置
====================

为支持MIDI 2.0添加了以下新配置项：`CONFIG_SND_UMP`、`CONFIG_SND_UMP_LEGACY_RAWMIDI`、`CONFIG_SND_SEQ_UMP`、`CONFIG_SND_SEQ_UMP_CLIENT`和`CONFIG_SND_USB_AUDIO_MIDI_V2`。第一个可见的配置项是`CONFIG_SND_USB_AUDIO_MIDI_V2`，当选择此项（设置`=y`）时，UMP的核心支持（`CONFIG_SND_UMP`）和序列器绑定（`CONFIG_SND_SEQ_UMP_CLIENT`）将自动选择。
另外，如果设置`CONFIG_SND_UMP_LEGACY_RAWMIDI=y`，则会启用对UMP端点的传统raw MIDI设备的支持。
RawMIDI 设备与 USB MIDI 2.0
================================

当设备支持 MIDI 2.0 时，默认情况下，USB 音频驱动程序会探测并使用位于交替设置 1 的 MIDI 2.0 接口，而不是位于交替设置 0 的 MIDI 1.0 接口。您可以通过向 snd-usb-audio 驱动模块传递 `midi2_enable=0` 参数来切换回旧的 MIDI 1.0 接口绑定。USB 音频驱动程序尝试查询自 UMP v1.1 提供的 UMP 端点和 UMP 功能块信息，并基于这些信息构建拓扑结构。如果设备较旧且不响应新的 UMP 查询，则驱动程序会退回到基于 USB 描述符中的组终端块（GTB）信息构建拓扑结构。某些设备可能会因意外的 UMP 命令而出现问题；在这种情况下，请向 snd-usb-audio 驱动传递 `midi2_ump_probe=0` 参数以跳过 UMP v1.1 查询。

当探测到 MIDI 2.0 设备时，内核会为该设备的每个 UMP 端点创建一个 rawmidi 设备。其设备名称为 `/dev/snd/umpC*D*`，不同于标准的 MIDI 1.0 rawmidi 设备名称 `/dev/snd/midiC*D*`，以避免遗留应用程序错误访问 UMP 设备。

您可以直接从此 UMP rawmidi 设备读取或写入 UMP 数据包。例如，通过以下 `hexdump` 命令可以显示卡 0 设备 0 的传入 UMP 数据包的十六进制格式：

```
% hexdump -C /dev/snd/umpC0D0
00000000  01 07 b0 20 00 07 b0 20  64 3c 90 20 64 3c 80 20  |... ... d<. d<. |
```

与 MIDI 1.0 字节流不同，UMP 是一个 32 位数据包，读取或写入设备的大小也对齐到 32 位（即 4 字节）。UMP 数据包的有效载荷中的 32 位字始终采用 CPU 本机字节序。传输驱动程序负责将 UMP 字从/转换为系统字节序所需的传输字节序/字节顺序。

当设置了 `CONFIG_SND_UMP_LEGACY_RAWMIDI` 时，驱动程序还会另外创建一个标准的 raw MIDI 设备作为 `/dev/snd/midiC*D*`。此设备包含 16 个子流，每个子流对应一个（从 0 开始编号的）UMP 组。遗留应用程序可以通过每个子流以 MIDI 1.0 字节流格式访问指定的组。使用 ALSA rawmidi API，您可以打开任意子流，而仅打开 `/dev/snd/midiC*D*` 将最终打开第一个子流。

每个 UMP 端点可以提供附加信息，这些信息是通过 UMP 1.1 流消息或 USB MIDI 2.0 描述符查询构造的。UMP 端点可能包含一个或多个 UMP 块，其中 UMP 块是在 ALSA UMP 实现中引入的抽象，用于表示 UMP 组之间的关联。UMP 块对应于 UMP 1.1 规范中的功能块。当没有 UMP 1.1 功能块信息时，可以从 USB MIDI 2.0 规范中定义的组终端块（GTB）部分填充。

UMP 端点和 UMP 块的信息可以在 `/proc/asound/card*/midi*` 文件中找到。例如：

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

请注意，上述 `/proc` 文件中显示的 `Groups` 字段表示的是从 1 开始编号的 UMP 组（从-到）。
那些额外的 UMP Endpoint 和 UMP Block 信息可以通过新的 ioctl 命令 `SNDRV_UMP_IOCTL_ENDPOINT_INFO` 和 `SNDRV_UMP_IOCTL_BLOCK_INFO` 分别获取。
RawMIDI 名称和 UMP Endpoint 名称通常是相同的，对于 USB MIDI 设备来说，名称取自相应的 USB MIDI 接口描述符中的 `iInterface`。如果未提供，则作为备选方案从 USB 设备描述符中的 `iProduct` 复制。
Endpoint 的产品 ID 是一个字符串字段，应该具有唯一性。对于 USB MIDI 设备，它从设备的 `iSerialNumber` 复制。
协议能力以及实际的协议位定义在 `asound.h` 中。

### ALSA 序列器与 USB MIDI 2.0

除了 RawMIDI 接口之外，ALSA 序列器接口还支持新的 UMP MIDI 2.0 设备。现在，每个 ALSA 序列器客户端可以设置其 MIDI 版本（0、1 或 2），以声明自己是传统的设备、UMP MIDI 1.0 设备或 UMP MIDI 2.0 设备。
第一个传统客户端发送/接收旧的序列事件。与此同时，UMP MIDI 1.0 和 2.0 客户端则通过扩展事件记录来发送和接收 UMP 数据。MIDI 版本可以在 `snd_seq_client_info` 结构体的新字段 `midi_version` 中看到。
一个 UMP 包可以通过指定新的事件标志位 `SNDRV_SEQ_EVENT_UMP` 在序列事件中发送/接收。当设置此标志时，事件有 16 字节（128 位）的数据负载用于保存 UMP 包。如果没有设置 `SNDRV_SEQ_EVENT_UMP` 标志位，则事件被视为传统的事件（最大 12 字节数据负载）处理。
当设置了 `SNDRV_SEQ_EVENT_UMP` 标志位时，UMP 序列事件的类型字段将被忽略（但默认应设置为 0）。
每个客户端的类型可以在 `/proc/asound/seq/clients` 中查看。
例如：

  % cat /proc/asound/seq/clients
  客户端信息
    当前客户端数：3
  ...
  客户端 14： "Midi Through" [内核遗留]
    端口 0： "Midi Through Port-0" (RWe-)
  客户端 20： "ProtoZOA" [内核UMP MIDI1]
    UMP端点：ProtoZOA
    UMP块 0：ProtoZOA 主 [活动]
      组：1-1
    UMP块 1：ProtoZOA Ext IN [活动]
      组：2-2
    UMP块 2：ProtoZOA Ext OUT [活动]
      组：3-3
    端口 0： "MIDI 2.0" (RWeX) [输入/输出]
    端口 1： "ProtoZOA Main" (RWeX) [输入/输出]
    端口 2： "ProtoZOA Ext IN" (-We-) [输出]
    端口 3： "ProtoZOA Ext OUT" (R-e-) [输入]

这里可以看到两种类型的内核客户端，客户端14为“遗留”类型，
而客户端20为“UMP MIDI1”，这是一个USB MIDI 2.0设备。
一个USB MIDI 2.0客户端总是将端口0命名为"MIDI 2.0"，
其余的端口从1开始对应每个UMP组（例如端口1对应组1）。
在这个例子中，设备有三个活动组（主、扩展输入和扩展输出），
这些组被暴露为序列器端口1到3。
"MIDI 2.0"端口用于UMP端点，它与其他UMP组端口的区别在于，
UMP端点端口发送设备上所有端口的事件（“全捕捉”），
而每个UMP组端口只发送特定UMP组的事件。
此外，无UMP组的消息（如UMP消息类型0x0f）仅发送到UMP端点端口。
请注意，尽管每个UMP序列器客户端通常创建16个端口，
但那些不属于任何UMP块（或属于非活动UMP块）的端口会被标记为不活动，并且不会出现在proc输出中。
在上面的例子中，从端口4到端口16是存在的，但没有显示出来。
上面的proc文件还显示了UMP块的信息。同样的条目（但包含更详细的信息）可以在rawmidi的proc输出中找到。
当不同MIDI版本的客户端连接时，事件会根据客户端的版本自动转换，
不仅在遗留与UMP MIDI 1.0/2.0之间，还在UMP MIDI 1.0与2.0之间进行转换。
例如，在legacy模式下运行`aseqdump`程序以监听ProtoZOA Main端口，输出如下：

  % aseqdump -p 20:1
  等待数据。按Ctrl+C结束
源  事件                        音道  数据
   20:1   音符开                    0, 音符 60, 速度 100
   20:1   音符关                    0, 音符 60, 速度 100
   20:1   控制改变                  0, 控制器 11, 值 4

当你在MIDI 2.0模式下运行`aseqdump`时，它会接收到高精度数据，如下所示：

  % aseqdump -u 2 -p 20:1
  等待数据。按Ctrl+C结束
来源 事件              通道 数据
20:1   音符触键               0, 音符 60, 速度 0xc924, 属性类型 = 0, 数据 = 0x0
20:1   音符释放               0, 音符 60, 速度 0xc924, 属性类型 = 0, 数据 = 0x0
20:1   控制改变               0, 控制器 11, 值 0x2000000

当数据由ALSA 序列器核心自动转换时
Rawmidi API 扩展
======================

* 可通过新的 ioctl `SNDRV_UMP_IOCTL_ENDPOINT_INFO` 获取附加的 UMP 端点信息。它包含关联的声卡和设备编号、位标志、协议、UMP 块的数量、端点名称字符串等。
协议在两个字段中指定，分别是协议能力（protocol capabilities）和当前协议（current protocol）。这两个字段都包含位标志来指定 MIDI 协议版本（`SNDRV_UMP_EP_INFO_PROTO_MIDI1` 或 `SNDRV_UMP_EP_INFO_PROTO_MIDI2`）的高字节以及抖动减少时间戳（`SNDRV_UMP_EP_INFO_PROTO_JRTS_TX` 和 `SNDRV_UMP_EP_INFO_PROTO_JRTS_RX`）的低字节。
一个 UMP 端点最多可包含 32 个 UMP 块，并且当前分配的块数会在端点信息中显示。
* 每个 UMP 块的信息可以通过另一个新的 ioctl `SNDRV_UMP_IOCTL_BLOCK_INFO` 获取。需要传递要查询的块的 ID 编号（从 0 开始）。接收到的数据包含块的方向、第一个相关组的 ID（从 0 开始）及其数量、块的名称字符串等。
方向可以是 `SNDRV_UMP_DIR_INPUT`、`SNDRV_UMP_DIR_OUTPUT` 或 `SNDRV_UMP_DIR_BIDIRECTION`。
* 对于支持 UMP v1.1 的设备，可以通过“流配置请求”消息（UMP 类型 0x0f，状态 0x05）切换 UMP MIDI 协议。当 UMP 核心接收到此类消息时，会更新 UMP 端点信息以及相应的序列器客户端。
控制 API 扩展
======================

* 引入了新的 ioctl `SNDRV_CTL_IOCTL_UMP_NEXT_DEVICE` 来查询下一个 UMP rawmidi 设备，而现有的 ioctl `SNDRV_CTL_IOCTL_RAWMIDI_NEXT_DEVICE` 只查询传统的 rawmidi 设备。
为了设置要打开的子设备（子流编号），可以使用 ioctl `SNDRV_CTL_IOCTL_RAWMIDI_PREFER_SUBDEVICE`，就像处理普通 rawmidi 一样。
* 新增的两个 ioctl `SNDRV_CTL_IOCTL_UMP_ENDPOINT_INFO` 和 `SNDRV_CTL_IOCTL_UMP_BLOCK_INFO` 通过 ALSA 控制 API 提供指定 UMP 设备的 UMP 端点和 UMP 块信息，而无需实际打开（UMP）rawmidi 设备。
`card`字段在查询时会被忽略，始终与控制界面的卡片绑定。

Sequencer API 扩展
==================

* 在`snd_seq_client_info`中添加了`midi_version`字段，以指示每个客户端当前的MIDI版本（0、1或2）。
当`midi_version`为1或2时，从UMP序器客户端读取的数据对齐方式也从之前的28字节更改为32字节，以适应扩展的有效载荷。写入的对齐大小未改变，但每个事件的大小可能根据以下新的位标志有所不同。
* 添加了`SNDRV_SEQ_EVENT_UMP`位标志，用于每个序器事件标志。当设置了这个位标志时，序器事件会扩展到具有更大的16字节有效载荷，而不是传统的12字节，并且事件包含有效载荷中的UMP数据包。
* 新的序器端口类型位`SNDRV_SEQ_PORT_TYPE_MIDI_UMP`表示端口支持UMP。
* 序器端口具有新的能力位，用于指示非活动端口（`SNDRV_SEQ_PORT_CAP_INACTIVE`）和UMP Endpoint端口（`SNDRV_SEQ_PORT_CAP_UMP_ENDPOINT`）。
* 可以通过将新的过滤位`SNDRV_SEQ_FILTER_NO_CONVERT`设置到客户端信息中来抑制ALSA序器客户端的事件转换。
例如，内核直通客户端（`snd-seq-dummy`）内部设置了此标志。
* 端口信息中新增了一个字段`direction`，用于指示端口的方向（`SNDRV_SEQ_PORT_DIR_INPUT`、`SNDRV_SEQ_PORT_DIR_OUTPUT`或`SNDRV_SEQ_PORT_DIR_BIDIRECTION`）。
* 端口信息中另一个新增的字段是`ump_group`，它指定了关联的UMP组号（基于1的编号）。
当非零时，UMP 数据包在传递给指定组时会更新 UMP 组字段（修正为基于 0 的索引）
每个排序器端口如果属于特定的 UMP 组，则应设置此字段
* 每个客户端可以在 `group_filter` 位图中设置用于 UMP 组的附加事件过滤器。该过滤器由基于 1 的组号位图组成。例如，当第 1 位被设置时，来自第 1 组（即第一个组）的消息将被过滤且不进行传递。
第 0 位用于过滤没有 UMP 组的消息
* 新增了两个 ioctl 命令供具备 UMP 功能的客户端使用：`SNDRV_SEQ_IOCTL_GET_CLIENT_UMP_INFO` 和 `SNDRV_SEQ_IOCTL_SET_CLIENT_UMP_INFO`。这些命令用于获取和设置与排序器客户端关联的 `snd_ump_endpoint_info` 或 `snd_ump_block_info` 数据。USB MIDI 驱动程序从底层 UMP rawmidi 提供这些信息，而用户空间客户端可以通过 `*_SET` ioctl 设置自己的数据
对于 Endpoint 数据，将 `type` 字段设为 0；而对于 Block 数据，则将块号加 1 后赋值给 `type` 字段
设置内核客户端的数据将会导致错误
* 在 UMP 1.1 中，功能块信息可以动态更改。当接收到设备的功能块更新时，ALSA 排序器核心会相应地更改相应的排序器端口名称和属性，并通过通告通知 ALSA 排序器系统端口，类似于普通端口更改通知。

MIDI2 USB Gadget 功能驱动
==========================

最新内核支持 USB MIDI 2.0 Gadget 功能驱动，可用于原型设计和调试 MIDI 2.0 特性
需要启用 `CONFIG_USB_GADGET`、`CONFIG_USB_CONFIGFS` 和 `CONFIG_USB_CONFIGFS_F_MIDI2` 以使用 MIDI2 Gadget 驱动
此外，使用小工具驱动程序时，您还需要一个正常工作的UDC驱动程序。
在下面的示例中，我们使用了`dummy_hcd`驱动程序（通过`CONFIG_USB_DUMMY_HCD`启用），该驱动程序在PC和VM上可用于调试目的。根据平台的不同，还有其他UDC驱动程序，这些也可以用于实际设备。

首先，在运行小工具的系统上加载`libcomposite`模块：

```sh
% modprobe libcomposite
```

然后，在configfs空间下会有一个`usb_gadget`子目录（通常在现代操作系统中的路径为`/sys/kernel/config`）。接着创建一个小工具实例并在其中添加配置，例如：

```sh
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
```

此时，必须存在一个名为`ep.0`的子目录，这是UMP端点的配置。您可以像这样填充端点信息：

```sh
% echo "ACMESynth" > functions/midi2.usb0/iface_name
% echo "ACMESynth" > functions/midi2.usb0/ep.0/ep_name
% echo "ABCD12345" > functions/midi2.usb0/ep.0/product_id
% echo 0x0123 > functions/midi2.usb0/ep.0/family
% echo 0x4567 > functions/midi2.usb0/ep.0/model
% echo 0x123456 > functions/midi2.usb0/ep.0/manufacturer
% echo 0x12345678 > functions/midi2.usb0/ep.0/sw_revision
```

默认的MIDI协议可以设置为1或2：

```sh
% echo 2 > functions/midi2.usb0/ep.0/protocol
```

而且，您可以在这个端点子目录下找到一个名为`block.0`的子目录。这定义了功能块的信息：

```sh
% echo "Monosynth" > functions/midi2.usb0/ep.0/block.0/name
% echo 0 > functions/midi2.usb0/ep.0/block.0/first_group
% echo 1 > functions/midi2.usb0/ep.0/block.0/num_groups
```

最后，链接配置并启用它：

```sh
% ln -s functions/midi2.usb0 configs/c.1
% echo dummy_udc.0 > UDC
```

其中`dummy_udc.0`是一个示例情况，并且会根据系统有所不同。您可以在`/sys/class/udc`中找到UDC实例，并传递找到的名称：

```sh
% ls /sys/class/udc
dummy_udc.0
```

现在，MIDI 2.0小工具设备已启用，并且通过`f_midi2`驱动程序创建了一个包含UMP rawmidi设备的新声卡实例：

```sh
% cat /proc/asound/cards
...
1 [Gadget         ]: f_midi2 - MIDI 2.0 Gadget
                       MIDI 2.0 Gadget
```

在连接的主机上，也会出现类似的声卡，但卡名和设备名与上述configfs中指定的一致：

```sh
% cat /proc/asound/cards
...
2 [ACMESynth      ]: USB-Audio - ACMESynth
                       ACME Enterprises ACMESynth at usb-dummy_hcd.0-1, high speed
```

您可以在小工具侧播放MIDI文件：

```sh
% aplaymidi -p 20:1 to_host.mid
```

这将作为输入从MIDI设备出现在连接的主机上：

```sh
% aseqdump -p 20:0 -u 2
```

反之亦然，连接的主机上的播放也会作为输入在小工具上工作。
每个功能块可能有不同的方向和UI提示，通过`direction`和`ui_hint`属性指定。传递`1`表示仅输入，`2`表示仅输出，`3`表示双向（默认值）。例如：

```sh
% echo 2 > functions/midi2.usb0/ep.0/block.0/direction
% echo 2 > functions/midi2.usb0/ep.0/block.0/ui_hint
```

如果您需要多个功能块，可以动态创建`block.1`、`block.2`等子目录，并在链接前按照上述配置步骤进行配置。例如，为了创建第二个键盘功能块：

```sh
% mkdir functions/midi2.usb0/ep.0/block.1
% echo "Keyboard" > functions/midi2.usb0/ep.0/block.1/name
% echo 1 > functions/midi2.usb0/ep.0/block.1/first_group
% echo 1 > functions/midi2.usb0/ep.0/block.1/num_groups
% echo 1 > functions/midi2.usb0/ep.0/block.1/direction
% echo 1 > functions/midi2.usb0/ep.0/block.1/ui_hint
```

`block.*`子目录也可以动态移除（除了持久存在的`block.0`）。
对于MIDI 1.0 I/O的功能块分配，通过`is_midi1`属性设置。`1`表示MIDI 1.0，而`2`表示低速连接下的MIDI 1.0：

```sh
% echo 2 > functions/midi2.usb0/ep.0/block.1/is_midi1
```

为了禁用小工具驱动程序处理UMP流消息，将`0`传递给顶级配置中的`process_ump`属性：

```sh
% echo 0 > functions/midi2.usb0/process_ump
```

小工具驱动程序还支持altset 0中的MIDI 1.0接口。当连接的主机选择MIDI 1.0接口时，小工具上的UMP I/O将相应地转换为/从USB MIDI 1.0数据包，同时小工具驱动程序继续通过UMP rawmidi与用户空间通信。
MIDI 1.0端口由每个功能块中的配置设置。
例如：

  % echo 0 > functions/midi2.usb0/ep.0/block.0/midi1_first_group
  % echo 1 > functions/midi2.usb0/ep.0/block.0/midi1_num_groups

上述配置将启用 MIDI 1.0 接口的第 1 组（索引为 0）。注意，这些组必须在功能块本身定义的组内。

Gadget 驱动程序也支持多个 UMP 端点。与功能块类似，你可以在卡顶层配置下创建一个新的子目录 `ep.1` 来启用一个新的端点：

  % mkdir functions/midi2.usb0/ep.1

然后在那里创建一个新的功能块。例如，要为这个新端点的功能块创建 4 个组：

  % mkdir functions/midi2.usb0/ep.1/block.0
  % echo 4 > functions/midi2.usb0/ep.1/block.0/num_groups

现在，你将总共有 4 个 rawmidi 设备：前两个是用于端点 0 和端点 1 的 UMP rawmidi 设备，另外两个是对应于端点 0 和端点 1 的传统 MIDI 1.0 rawmidi 设备。

当前设备上的备用设置可以通过带有 `RAWMIDI` 接口的控制元素 “操作模式” 来获取。例如，你可以通过运行在设备主机上的 `amixer` 程序来读取它：

  % amixer -c1 cget iface=RAWMIDI,name='Operation Mode'
  ; type=INTEGER,access=r--v----,values=1,min=0,max=2,step=0
  : values=2

返回的第二行中的值（以 `: values=` 开头）表示：1 代表 MIDI 1.0（备用设置 0），2 代表 MIDI 2.0（备用设置 1），0 代表未设置。

目前，在绑定之后无法更改配置。
