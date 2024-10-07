```sh
#! /bin/sh
#
#  Turtle Beach MultiSound 驱动说明
#  -- Andrew Veliath <andrewtv@usa.net>
#
#  最后更新：                       1998年9月10日
#  对应的 msnd 驱动版本：          0.8.3
#
# ** 此文件包含一个 README（顶部部分）和一个 shell 归档文件（底部部分）
#    可以通过运行 `sh MultiSound` 来解压对应的实用程序源代码（仅适用于 Pinnacle 和 Fiji 卡）。**
#
#
#  -=-=- 获取固件 -=-=-
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#  请参阅此文档中的“获取和创建固件文件”部分，了解获取必要的固件文件的说明。
#
#
#  支持的功能
#  ~~~~~~~~~~~~~~~~~~
#
#  目前支持全双工数字音频（仅限 /dev/dsp，/dev/audio 目前不可用）和混音器功能（/dev/mixer）（尚不支持内存映射数字音频）
#  如果您有数字子板，还可以进行数字传输和监控（有关使用 S/PDIF 端口的更多信息，请参阅相关章节）
#
#  对于 Turtle Beach MultiSound Hurricane 架构的支持由以下模块组成（这些模块也可以编译到内核中）：
#
#  snd-msnd-lib           - MultiSound 基础（需要 snd）
#
#  snd-msnd-classic       - 为 Classic、Monterey 和 Tahiti 卡提供基础音频/混音器支持
#
#  snd-msnd-pinnacle      - 为 Pinnacle 和 Fiji 卡提供基础音频/混音器支持
#
#
#  重要说明 - 使用前请阅读
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#  固件文件不包括在内（将来可能会改变）。您必须从 Turtle Beach 获取这些图像（它们包含在 MultiSound 开发工具包中），并将它们放置在 /etc/sound 中，并在 Linux 配置中指定完整的路径。如果您将 MultiSound 驱动编译到内核中而不是作为模块使用，则这些固件文件必须在内核编译期间可访问。
#
#  请注意，这些文件必须是二进制文件，而不是汇编文件。请参阅本文档后面的章节获取这些文件的说明。
#
#
#  配置卡资源
#  ~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#  ** 本节非常重要，如果配置不当，您的卡可能无法工作或导致系统崩溃。**
#
#  * Classic/Monterey/Tahiti
#
#  这些卡通过 snd-msnd-classic 驱动进行配置。您必须知道 IO 端口，然后驱动会自动选择卡上的中断和内存资源。您需要确保这些位置是否空闲，否则冲突会导致系统锁定。
#
#  * Pinnacle/Fiji
#
#  Pinnacle 和 Fiji 卡有一个额外的配置端口，可能是 0x250、0x260 或 0x270。这个端口可以禁用以便通过即插即用（PnP）进行严格配置，但在使用 PnP 时您会失去访问该卡上的 IDE 控制器和游戏杆设备的能力。此 shell 归档中包含的 pinnaclecfg 程序可用于在非 PnP 模式下配置卡，在 PnP 模式下您可以使用 isapnptools。这里简要描述如下：
#
#  pinnaclecfg 并不是必需的；您也可以使用 snd-msnd-pinnacle 模块来完全配置卡。但是，pinnaclecfg 可用于在加载 snd-msnd-pinnacle 模块后更改特定设备的资源值。如果您将驱动编译到内核中，必须在编译时设置这些值，但在加载内核后可以通过 pinnaclecfg 程序更改其他外围设备的资源值。
#
#
#  *** PnP 模式
#
#  如果可以，请使用 pnpdump 获得一个示例配置；我能够通过命令 `pnpdump 1 0x203` 获得一个配置——这可能会因人而异（单独运行 pnpdump 对我来说不起作用）。然后，编辑此文件并使用 isapnp 取消注释并设置卡的值。
```
# 在插入 snd-msnd-pinnacle 模块时使用这些值。使用这种方法，您可以为 DSP 和 Kurzweil 合成器（Pinnacle）设置资源。由于 Linux 不直接支持即插即用（PnP）设备，因此当驱动程序编译到内核中时，在 PnP 模式下使用该卡可能会遇到困难。在这种情况下，使用非 PnP 模式是更好的选择。

# 以下是一个适用于 isapnp 的 mypinnacle.conf 示例，将卡设置为 IO 基地址 0x210、IRQ 5 和内存 0xd8000，并将 Kurzweil 合成器设置为 0x330 和 IRQ 9（可能需要根据您的系统进行编辑）：

# (READPORT 0x0203)
# (CSN 2)
# (IDENTIFY *)

# # DSP
# (CONFIGURE BVJ0440/-1 (LD 0
#          (INT 0 (IRQ 5 (MODE +E))) (IO 0 (BASE 0x0210)) (MEM 0 (BASE 0x0d8000))
#          (ACT Y)))

# # Kurzweil 合成器（仅限 Pinnacle）
# (CONFIGURE BVJ0440/-1 (LD 1
#          (IO 0 (BASE 0x0330)) (INT 0 (IRQ 9 (MODE +E)))
#          (ACT Y)))

# (WAITFORKEY)

# *** 非 PnP 模式

# 第二种方法是在非 PnP 模式下运行该卡。实际上这有一些优势，因为您可以访问卡上的其他设备，例如游戏杆和 IDE 控制器。要配置该卡，请解压此 Shell 归档文件并构建 pinnaclecfg 程序。使用此程序，您可以为卡的设备分配资源值或禁用设备。作为使用 pinnaclecfg 的替代方案，您可以在加载 snd-msnd-pinnacle 模块时（或在编译驱动程序到内核时）指定许多配置值。

# 如果您为 snd-msnd-pinnacle 模块指定了 cfg=0x250，则会自动使用该配置端口配置卡的 IO、IRQ 和内存值（配置端口可通过跳线选择为 0x250、0x260 或 0x270）。

# 有关这些参数的更多信息，请参见下面的“snd-msnd-pinnacle 额外选项”部分（同样，如果您直接将驱动程序编译到内核中，这些额外参数在这里可能会有用）。

# ** 如果您选择了不正确的资源值，很容易导致机器出现问题。**

# 示例
# ~~~~~~~~

# * MultiSound Classic/Monterey/Tahiti：
# 
# modprobe snd
# insmod snd-msnd-lib
# insmod snd-msnd-classic io=0x290 irq=7 mem=0xd0000

# * MultiSound Pinnacle 在 PnP 模式下：
# 
# modprobe snd
# insmod snd-msnd-lib
# isapnp mypinnacle.conf
# insmod snd-msnd-pinnacle io=0x210 irq=5 mem=0xd8000 <-- 匹配 mypinnacle.conf 的值

# * MultiSound Pinnacle 在非 PnP 模式下（将 0x250 替换为您的配置端口，可以是 0x250、0x260 或 0x270）：
# 
# modprobe snd
# insmod snd-msnd-lib
# insmod snd-msnd-pinnacle cfg=0x250 io=0x290 irq=5 mem=0xd0000

# * 要在 PnP 模式下使用 Pinnacle 上的 MPU 兼容 Kurzweil 合成器（假设您已经执行了 `isapnp mypinnacle.conf`）：
# 
# insmod snd
# insmod mpu401 io=0x330 irq=9 <-- 匹配 mypinnacle.conf 的值

# * 要在非 PnP 模式下使用 Pinnacle 上的 MPU 兼容 Kurzweil 合成器，添加以下内容。注意我们首先配置外围设备的资源，然后安装一个 Linux 驱动程序：
# 
# insmod snd
# pinnaclecfg 0x250 mpu 0x330 9
# insmod mpu401 io=0x330 irq=9

# -- 或者在非 PnP 模式下无需使用 pinnaclecfg 的以下序列：
# 
# modprobe snd
# insmod snd-msnd-lib
# insmod snd-msnd-pinnacle cfg=0x250 io=0x290 irq=5 mem=0xd0000 mpu_io=0x330 mpu_irq=9
# insmod snd
# insmod mpu401 io=0x330 irq=9

# * 要在非 PnP 模式下设置 Pinnacle 上的游戏杆端口（尽管您需要在其他地方找到实际的 Linux 游戏杆驱动程序），您可以使用 pinnaclecfg：
# 
# pinnaclecfg 0x250 joystick 0x200

# -- 或者可以使用以下内容通过 snd-msnd-pinnacle 进行配置：
# 
# modprobe snd
# insmod snd-msnd-lib
# insmod snd-msnd-pinnacle cfg=0x250 io=0x290 irq=5 mem=0xd0000 joystick_io=0x200

# snd-msnd-classic, snd-msnd-pinnacle 必需选项
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# 如果未给出以下选项，模块将不会加载。检查内核消息日志以获取有用的错误信息。
# 注意：探测不受支持，因此请确保您有正确的共享内存区域，否则可能会遇到问题。

# io                   DSP 的 I/O 基地址，例如 io=0x210
# irq                  中断请求号，例如 irq=5
# mem                  共享内存区域，例如 mem=0xd8000

# snd-msnd-classic, snd-msnd-pinnacle 额外选项
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# fifosize             数字音频 FIFO 大小（以千字节为单位）。如果不指定，默认值将被使用。增加这个值会减少 FIFO 欠流的机会，但会增加整体延迟。例如，fifosize=512 将分配 512kB 读写 FIFO（总共 1MB）。虽然这可以减少丢帧，但在繁重的系统负载下，FIFO 无疑会被数据饿死，最终还是会丢帧。一种解决方案是更改回放进程的调度优先级，使用 `nice` 或某种形式的 POSIX 软实时调度。

# calibrate_signal     将其设置为 1 会根据信号校准 ADC，设置为 0 会根据卡校准（默认为 0）
```
snd-msnd-pinnacle 额外选项
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

digital              指定 digital=1 以启用 S/PDIF 输入（如果您有数字子板适配器）。这将使声卡在混音器中能够访问 DIGITAL1 输入。某些混音程序可能会在设置 DIGITAL1 源作为输入时遇到问题。如果遇到问题，可以尝试使用本文档底部的 setdigital.c 程序。

cfg                  Pinnacle 和 Fiji 的非即插即用配置端口（通常为 0x250、0x260 或 0x270，具体取决于跳线配置）。如果省略此选项，则假定该卡处于即插即用模式，并且指定的 DSP 资源值已经通过即插即用配置（即不会尝试进行任何配置）。

当 Pinnacle 处于非即插即用模式时，您可以使用以下选项来配置特定设备。如果未提供设备的完整规范，则不配置该设备。请注意，一旦这些设备的资源设置完成，您仍然需要使用 Linux 驱动程序（例如 Linux 摇杆驱动程序或用于 Kurzweil 合成器的 OSS 的 MPU401 驱动程序）。

mpu_io               MPU（板载 Kurzweil 合成器）的 I/O 端口
mpu_irq              MPU（板载 Kurzweil 合成器）的 IRQ
ide_io0              IDE 控制器的第一个 I/O 端口
ide_io1              IDE 控制器的第二个 I/O 端口
ide_irq              IDE 控制器的 IRQ
joystick_io          摇杆的 I/O 端口

获取和创建固件文件
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

对于 Classic/Tahiti/Monterey
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

从 Turtle Beach 下载并解压缩以下文件到 /tmp：

    ftp://ftp.voyetra.com/pub/tbs/msndcl/msndvkit.zip

解压后，再解压名为 MsndFiles.zip 的文件。然后将以下固件文件复制到 /etc/sound（注意文件重命名）：

    cp DSPCODE/MSNDINIT.BIN /etc/sound/msndinit.bin
    cp DSPCODE/MSNDPERM.REB /etc/sound/msndperm.bin

配置 Linux 内核时，指定 /etc/sound/msndinit.bin 和 /etc/sound/msndperm.bin 为两个固件文件（Linux 内核版本低于 2.2 不会询问固件路径，并且默认为 /etc/sound）。

如果将驱动程序编译到内核中，这些文件必须在编译期间可访问，但之后不再需要。然而，如果驱动程序作为模块使用，这些文件必须保留。

对于 Pinnacle/Fiji
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

从 Turtle Beach 下载并解压缩以下文件到 /tmp（确保使用完整的 URL；有些人无法导航到该 URL）：

    ftp://ftp.voyetra.com/pub/tbs/pinn/pnddk100.zip

解包此 shell 归档文件，并在创建的目录中运行 make（您需要一个 C 编译器和 flex 来构建工具）。这应该生成可执行文件 conv、pinnaclecfg 和 setdigital。conv 只在此处临时用于创建固件文件，而 pinnaclecfg 用于在非即插即用模式下配置 Pinnacle 或 Fiji 卡，setdigital 可用于在混音器上设置 S/PDIF 输入（pinnaclecfg 和 setdigital 应该被复制到方便的位置，可能在系统初始化时运行）。

要使用 `conv` 程序生成固件文件，我们通过以下转换创建二进制固件文件（假设归档文件解压到名为 PINNDDK 的目录）：

    ./conv < PINNDDK/dspcode/pndspini.asm > /etc/sound/pndspini.bin
    ./conv < PINNDDK/dspcode/pndsperm.asm > /etc/sound/pndsperm.bin

转换后，conv（和 conv.l）程序不再需要，可以安全删除。然后，在配置 Linux 内核时，指定 /etc/sound/pndspini.bin 和 /etc/sound/pndsperm.bin 为两个固件文件（Linux 内核版本低于 2.2 不会询问固件路径，并且默认为 /etc/sound）。
```
```
如果将驱动程序编译到内核中，这些文件在编译期间必须可访问，但之后不需要。但如果驱动程序作为模块使用，则这些文件必须保留。

使用 S/PDIF 端口的数字 I/O
~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果您有一个带有数字子板的 Pinnacle 或 Fiji，并且希望将其设置为输入源，如果您在尝试使用混音器程序时遇到问题，可以使用此程序（确保在加载模块时使用 digital=1 选项，或者在编译入内核操作时选择 Y）。选择 S/PDIF 端口后，您应该能够监控和录制该端口的内容。

使用 S/PDIF 端口需要注意的一点是，数字定时是从数字信号中获取的，因此如果端口没有连接信号并且选择了其作为录音输入，您会发现 PCM 播放速度失真。此外，尝试以非 DAT 速率进行录音可能会有问题（例如，在 DAT 信号为 44100Hz 时尝试以 8000Hz 录音）。如果您遇到此类问题，请将录音输入设置为模拟模式，以便您可以以非 DAT 速率录音。

-- 下面附有 Shell 归档文件，只需运行 `sh MultiSound` 即可解压。包含用于转换固件、配置非即插即用模式以及选择 MIXER 中 DIGITAL1 输入的 Pinnacle/Fiji 工具。

```
#!/bin/sh
# 这是一个 Shell 归档文件（由 GNU sharutils 4.2 生成）
# 要从这个归档文件中提取文件，请将其保存到某个 FILE 中，删除上面 `!/bin/sh' 行之前的所有内容，然后键入 `sh FILE'

# 由 <andrewtv@ztransform.velsoft.com> 于 1998-12-04 10:07 EST 制作
# 源目录为 `/home/andrewtv/programming/pinnacle/pinnacle`
```
