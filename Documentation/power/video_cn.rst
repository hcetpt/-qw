===========================
S3 恢复时的视频问题
===========================

2003-2006，Pavel Machek

在 S3 恢复过程中，硬件需要重新初始化。对于大多数设备来说，这是很容易做到的，并且内核驱动程序知道如何进行初始化。不幸的是，有一个例外：显卡。这些显卡通常由 BIOS 初始化，而内核没有足够的信息来启动显卡。（内核通常甚至不包含显卡驱动——vesafb 和 vgacon 被广泛使用）
这对于 swsusp 并不是问题，因为在 swsusp 恢复期间，BIOS 会正常运行，因此显卡也会正常初始化。对于 S1 待机模式来说也不应该是个问题，因为硬件状态应该在该模式下保持不变。
我们可以在早期恢复阶段运行显卡 BIOS，或者稍后使用 vbetool 解释它，或者也许在特定系统上什么都不需要做，因为显卡状态得以保留。不幸的是，不同的方法适用于不同的系统，没有已知的方法能够适应所有系统。
已经开发了一个用户空间应用程序 s2ram；它包含了一个很长的系统白名单，并自动为给定的系统选择有效的方法。可以从 www.sf.net/projects/suspend 的 CVS 下载。如果您遇到一个不在白名单上的系统，请尝试找到一种有效的方法，并提交白名单条目，以避免重复工作。
目前，VBE_SAVE 方法（见下文第 6 点）在大多数系统上有效。不幸的是，vbetool 只能在用户空间恢复后运行，这使得早期恢复问题的调试变得困难/不可能。不依赖用户空间的方法更可取。

详细信息
~~~~~~~~

有几种类型的系统在 S3 恢复后视频可以正常工作：

(1) 显卡状态在 S3 过程中得以保留的系统
(2) 在 S3 恢复期间可以调用显卡 BIOS 的系统。不幸的是，在那个阶段调用显卡 BIOS 是不正确的，但某些机器上却能工作。使用 acpi_sleep=s3_bios
(3) 将显卡初始化为 VGA 文本模式并且 BIOS 能够很好地设置视频模式的系统。使用 acpi_sleep=s3_mode
(4) 在一些系统上，s3_bios 会使显卡进入文本模式，因此需要使用 acpi_sleep=s3_bios,s3_mode
(5) Radeon 系统，其中 X 可以软启动您的显卡。您需要足够新的 X，并且需要纯文本控制台（没有 vesafb 或 radeonfb）。更多信息请参阅 http://www.doesi.gmxhome.de/linux/tm800s3/s3.html
或者，你应该使用 `vbetool`（6），对于某些其他 Radeon 系统来说，仅使用 `vbetool` 就足以使系统恢复。这需要文本控制台正常工作。执行以下命令：`vbetool vbestate save > /tmp/delme; echo 3 > /proc/acpi/sleep; vbetool post; vbetool vbestate restore < /tmp/delme; setfont <whatever>`，这样你的视频应该就能正常工作。

在某些系统上，可以启动大部分内核，然后进行 BIOS 的 POST 操作。Ole Rohne 在此链接提供了相关补丁：http://dev.gentoo.org/~marineam/patch-radeonfb-2.6.11-rc2-mm2

在某些系统上，你可以使用 `video_post` 工具或执行 `echo 3 > /sys/power/state && /usr/sbin/video_post`，这将初始化控制台模式下的显示。如果你在 X 环境中，可以通过按下 `CTRL+ALT+F1` 切换到虚拟终端，再通过 `CTRL+ALT+F7` 返回 X 环境，从而使图形模式下的显示恢复正常。

如果传递了 `acpi_sleep=something` 参数，并且与你的 BIOS 不兼容，那么在恢复时可能会导致硬崩溃。请小心操作。另外，在进行实验时最好使用普通的 VGA 控制台。`vesafb` 和 `radeonfb`（等）驱动程序在恢复时有导致机器崩溃的倾向。

如果你的系统上述方法都不适用，那么你可能需要发明另一个丑陋但有效的解决方案，或者为你的显卡编写一个正确的驱动程序（祝你好运获取文档）。也许从 X 环境中挂起（真正的 X 环境，了解你的硬件，而不是 XF68_FBcon）可能会有更好的效果。

已知能正常工作的笔记本列表：

| 型号 | 解决方案（或“如何操作”） |
| --- | --- |
| Acer Aspire 1406LC | Ole 的延迟 BIOS 初始化（7），关闭 DRI |
| Acer TM 230 | s3_bios（2） |
| Acer TM 242FX | vbetool（6） |
| Acer TM C110 | video_post（8） |
| Acer TM C300 | vga=normal（仅在控制台下挂起，不在 X 环境下），vbetool（6）或 video_post（8） |
| Acer TM 4052LCi | s3_bios（2） |
| Acer TM 636Lci | s3_bios, s3_mode（4） |
| Acer TM 650（Radeon M7） | vga=normal 加上 boot-radeon（5）可恢复文本控制台 |
| Acer TM 660 | ??? |
| Acer TM 800 | vga=normal，X 补丁，参见网页（5），或 vbetool（6） |
| Acer TM 803 | vga=normal，X 补丁，参见网页（5），或 vbetool（6） |
| Acer TM 803LCi | vga=normal，vbetool（6） |
| Arima W730a | 需要 vbetool（6） |
| Asus L2400D | s3_mode（3）（S1 也正常工作） |
| Asus L3350M（SiS 740） | （6） |
| Asus L3800C（Radeon M7） | s3_bios（2）（S1 也正常工作） |
| Asus M6887Ne | vga=normal，s3_bios（2），使用 radeon 驱动程序代替 x.org 中的 fglrx |
| Athlon64 桌面原型机 | s3_bios（2） |
| Compal CL-50 | ??? |
| Compaq Armada E500 - P3-700 | 无（1）（S1 也正常工作） |
| Compaq Evo N620c | vga=normal，s3_bios（2） |
| Dell 600m, ATI R250 Lf | 无（1），但需要 xorg-x11-6.8.1.902-1 |
| Dell D600, ATI RV250 | vga=normal 和 X，或尝试 vbestate（6） |
| Dell D610 | vga=normal 和 X（可能也需要 vbestate（6），但未经过测试） |
| Dell Inspiron 4000 | ??? |
| Dell Inspiron 500m | ??? |
| Dell Inspiron 510m | ??? |
| Dell Inspiron 5150 | 需要 vbetool（6） |
| Dell Inspiron 600m | ??? |
| Dell Inspiron 8200 | ??? |
| Dell Inspiron 8500 | ??? |
| Dell Inspiron 8600 | ??? |
| eMachines Athlon64 机器 | 需要 vbetool（6）（请提供型号） |
| HP NC6000 | s3_bios，可能不能使用 radeonfb（2），或 vbetool（6） |
| HP NX7000 | ??? |
| HP Pavilion ZD7000 | 需要 vbetool post，需要开源的 nv 驱动程序用于 X |
| HP Omnibook XE3 Athlon 版本 | 无（1） |
| HP Omnibook XE3GC | 无（1），视频是 S3 Savage/IX-MV |
| HP Omnibook XE3L-GF | vbetool（6） |
| HP Omnibook 5150 | 无（1）（S1 也正常工作） |
| IBM TP T20, model 2647-44G | 无（1），视频是 S3 Inc. 86C270-294 Savage/IX-MV，vesafb 得到“有趣”的结果，但 X 正常工作 |
| IBM TP A31 / Type 2652-M5G | s3_mode（3）[使用 BIOS 1.04 2002-08-23 正常工作，但使用 BIOS 1.11 2004-11-05 完全不工作] |
| IBM TP R32 / Type 2658-MMG | 无（1） |
| IBM TP R40 2722B3G | ??? |
| IBM TP R50p / Type 1832-22U | s3_bios（2） |
| IBM TP R51 | 无（1） |
| IBM TP T30 236681A | ??? |
| IBM TP T40 / Type 2373-MU4 | 无（1） |
| IBM TP T40p | 无（1） |
| IBM TP R40p | s3_bios（2） |
| IBM TP T41p | s3_bios（2），恢复后切换到 X |
| IBM TP T42 | s3_bios（2） |
| IBM ThinkPad T42p (2373-GTG) | s3_bios（2） |
| IBM TP X20 | ??? |
| IBM TP X30 | s3_bios, s3_mode（4） |
| IBM TP X31 / Type 2672-XXH | 无（1），使用 radeontool（http://fdd.com/software/radeon/）关闭背光 |
| IBM TP X32 | 无（1），但在长时间挂起后背光亮起且视频损坏。s3_bios，s3_mode（4）也可行。也许能得到更好的结果？ |
| IBM Thinkpad X40 Type 2371-7JG | s3_bios,s3_mode（4） |
| IBM TP 600e | 无（1），但需要切换到控制台并返回 X |
| Medion MD4220 | ??? |
| Samsung P35 | 需要 vbetool（6） |
| Sharp PC-AR10 (ATI rage) | 无（1），背光不会关闭 |
| Sony Vaio PCG-C1VRX/K | s3_bios（2） |
| Sony Vaio PCG-F403 | ??? |
| Sony Vaio PCG-GRT995MP | 无（1），使用 ‘nv’ X 驱动程序正常工作 |
| Sony Vaio PCG-GR7/K | 无（1），但需要 radeonfb，使用 radeontool（http://fdd.com/software/radeon/）关闭背光 |
| Sony Vaio PCG-N505SN | ??? |
| Sony Vaio vgn-s260 | X 或 boot-radeon 可以初始化 |
| Sony Vaio vgn-S580BH | vga=normal，但需从 X 挂起。除非返回 X，否则控制台将是空白的 |

请注意，表中的“无（1）”表示该系统无需特殊处理即可正常工作。
### 已知可用的笔记本系统
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

================== ================== =======================
型号                    方法                       备注
================== ================== =======================
Sony Vaio vgn-FS115B   s3_bios (2)，s3_mode (4)  
Toshiba Libretto L5    none (1)                  
Toshiba Libretto 100CT/110CT  vbetool (6)            
Toshiba Portege 3020CT  s3_mode (3)               
Toshiba Satellite 4030CDT  s3_mode (3)（S1 也有效）
Toshiba Satellite 4080XCDT  s3_mode (3)（S1 也有效）
Toshiba Satellite 4090XCDT  ??? [#f1]_                
Toshiba Satellite P10-554  s3_bios，s3_mode (4) [#f3]_
Toshiba M30             (2) xor X 使用内部 AGP 的 NVIDIA 驱动
Uniwill 244IIO         ??? [#f1]_                 
================== ================== =======================

### 已知可用的台式机系统
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=================== ============================= ========================
主板                    显卡                           方法（或“如何操作”）
=================== ============================= ========================
Asus A7V8X            nVidia RIVA TNT2 model 64     s3_bios，s3_mode (4)
=================== ============================= ========================

.. [#f1] 来自 https://wiki.ubuntu.com/HoaryPMResults，不确定使用哪些选项。如果你知道，请告诉我。
.. [#f3] 不适用于 SMP 内核，仅适用于 UP 内核。
