===========================
S3 恢复时的视频问题
===========================

2003-2006，Pavel Machek

在 S3 恢复过程中，硬件需要重新初始化。对于大多数设备而言，这很容易做到，并且内核驱动程序知道如何进行。不幸的是，存在一个例外：显卡。这些通常由 BIOS 初始化，而内核没有足够的信息来启动显卡。（内核通常甚至不包含显卡驱动程序——vesafb 和 vgacon 被广泛使用）
这对 swsusp 并不是问题，因为在 swsusp 恢复期间，BIOS 正常运行，因此显卡正常初始化。它也不应该成为 S1 待机的问题，因为硬件应该在此过程中保持其状态。
我们要么在早期恢复阶段运行显卡的 BIOS，要么稍后使用 vbetool 解释它，或者可能在特定系统上根本不需要任何操作，因为显卡的状态被保留了。不幸的是，不同的方法适用于不同的系统，没有任何已知的方法可以适用于所有系统。
已经开发了一个名为 s2ram 的用户空间应用程序；它包含了一个很长的系统白名单，并能自动为给定的系统选择有效的方法。可以从 www.sf.net/projects/suspend 的 CVS 下载。如果你遇到一个不在白名单中的系统，请尝试找到可行的解决方案，并提交白名单条目，以避免重复工作。
目前，VBE_SAVE 方法（下面的第 6 种方法）在大多数系统上都能工作。不幸的是，vbetool 只能在用户空间恢复之后运行，这就使得调试早期恢复问题变得困难/不可能。不依赖于用户空间的方法更可取。
详情
~~~~~~~

有几种类型的系统在 S3 恢复后视频仍然能正常工作：

(1) 显卡状态在 S3 过程中得到保留的系统
(2) 可以在 S3 恢复期间调用显卡 BIOS 的系统。不幸的是，在这一点上调用显卡 BIOS 是不正确的，但事实证明它在某些机器上能工作。使用 acpi_sleep=s3_bios
(3) 将显卡初始化到 VGA 文本模式并且 BIOS 足够好能够设置视频模式的系统。在这种情况下使用 acpi_sleep=s3_mode
(4) 在一些系统上，s3_bios 会将显卡切换到文本模式，因此需要使用 acpi_sleep=s3_bios,s3_mode
(5) Radeon 系统，其中 X 可以软启动你的显卡。你需要一个足够新的 X，以及一个纯文本控制台（无 vesafb 或 radeonfb）。更多信息请参见 http://www.doesi.gmxhome.de/linux/tm800s3/s3.html
或者，你应该使用 vbetool（注6）代替。

(6) 对于其他 Radeon 系统，vbetool 就足以让系统恢复生机。它需要文本控制台能够工作。执行 `vbetool vbestate save > /tmp/delme`；然后 `echo 3 > /proc/acpi/sleep`；接着 `vbetool post`；再运行 `vbetool vbestate restore < /tmp/delme`；最后 `setfont <whatever>`，这样你的视频应该就能正常工作了。
(7) 在一些系统上，可以先启动大部分内核，然后执行 BIOS 的 POST 过程。Ole Rohne 提供了一个补丁以实现这一功能，地址为：`http://dev.gentoo.org/~marineam/patch-radeonfb-2.6.11-rc2-mm2`
(8) 在一些系统上，你可以使用 `video_post` 工具或者执行 `echo 3 > /sys/power/state  && /usr/sbin/video_post` 来在控制台模式下初始化显示。如果你正在使用 X 环境，你可以通过 `CTRL+ALT+F1` 切换到虚拟终端然后再通过 `CTRL+ALT+F7` 返回到 X 环境，从而让图形模式下的显示恢复正常。

现在，如果你传递了 `acpi_sleep=something` 参数，并且它与你的 BIOS 不兼容，那么在恢复过程中可能会导致系统崩溃。请小心操作。另外，在进行实验时使用纯 VGA 控制台是最安全的。vesafb 和 radeonfb （等等）驱动程序在恢复过程中有导致机器崩溃的倾向。

你可能拥有的是一个以上方法都无法工作的系统。在这种情况下，要么发明一个新的丑陋但有效的解决方案，要么为你的显卡编写一个合适的驱动程序（祝你好运获得文档）。也许从 X 环境中挂起（正确的 X 环境，了解你的硬件，而不是 XF68_FBcon）可能有更好的机会工作。

已知可工作的笔记本列表：

| Model | 解决方案（或“如何做”） |
| --- | --- |
| Acer Aspire 1406LC | Ole 的后期 BIOS 初始化（7），关闭 DRI |
| Acer TM 230 | s3_bios（2） |
| Acer TM 242FX | vbetool（6） |
| Acer TM C110 | video_post（8） |
| Acer TM C300 | vga=normal（仅限控制台挂起，而非在 X 环境中），vbetool（6） 或 video_post（8） |
| Acer TM 4052LCi | s3_bios（2） |
| Acer TM 636Lci | s3_bios,s3_mode（4） |
| Acer TM 650 (Radeon M7) | vga=normal 加上 boot-radeon（5）可以获得文本控制台 |
| Acer TM 660 | 未知 |
| Acer TM 800 | vga=normal，X 补丁，参见网页（5） 或 vbetool（6） |
| Acer TM 803 | vga=normal，X 补丁，参见网页（5） 或 vbetool（6） |
| Acer TM 803LCi | vga=normal，vbetool（6） |
| Arima W730a | 需要 vbetool（6） |
| Asus L2400D | s3_mode（3）（注2）（S1 也正常工作） |
| Asus L3350M (SiS 740) | （6） |
| Asus L3800C (Radeon M7) | s3_bios（2）（S1 也正常工作） |
| Asus M6887Ne | vga=normal，s3_bios（2），在 x.org 中使用 radeon 驱动程序而非 fglrx |
| Athlon64 桌面原型机 | s3_bios（2） |
| Compal CL-50 | 未知 |
| Compaq Armada E500 - P3-700 | 无（1）（S1 也正常工作） |
| Compaq Evo N620c | vga=normal，s3_bios（2） |
| Dell 600m, ATI R250 Lf | 无（1），但需要 xorg-x11-6.8.1.902-1 |
| Dell D600, ATI RV250 | vga=normal 和 X，或尝试 vbestate（6） |
| Dell D610 | vga=normal 和 X（可能也可以使用 vbestate（6），但未经过测试） |
| Dell Inspiron 4000 | 未知 |
| Dell Inspiron 500m | 未知 |
| Dell Inspiron 510m | 未知 |
| Dell Inspiron 5150 | 需要 vbetool（6） |
| Dell Inspiron 600m | 未知 |
| Dell Inspiron 8200 | 未知 |
| Dell Inspiron 8500 | 未知 |
| Dell Inspiron 8600 | 未知 |
| eMachines Athlon64 机器 | 需要 vbetool（6）（请有人提供型号） |
| HP NC6000 | s3_bios，可能不能使用 radeonfb（2）；或 vbetool（6） |
| HP NX7000 | 未知 |
| HP Pavilion ZD7000 | 需要 vbetool post，需要开源的 nv 驱动程序用于 X |
| HP Omnibook XE3 (Athlon 版本) | 无（1） |
| HP Omnibook XE3GC | 无（1），视频是 S3 Savage/IX-MV |
| HP Omnibook XE3L-GF | vbetool（6） |
| HP Omnibook 5150 | 无（1）（S1 也正常工作） |
| IBM TP T20, model 2647-44G | 无（1），视频是 S3 Inc. 86C270-294 Savage/IX-MV，vesafb 能得到“有趣”的效果但 X 正常工作 |
| IBM TP A31 / Type 2652-M5G | s3_mode（3）[与 BIOS 1.04 2002-08-23 兼容，但与 BIOS 1.11 2004-11-05 完全不兼容] |
| IBM TP R32 / Type 2658-MMG | 无（1） |
| IBM TP R40 2722B3G | 未知 |
| IBM TP R50p / Type 1832-22U | s3_bios（2） |
| IBM TP R51 | 无（1） |
| IBM TP T30 236681A | 未知 |
| IBM TP T40 / Type 2373-MU4 | 无（1） |
| IBM TP T40p | 无（1） |
| IBM TP R40p | s3_bios（2） |
| IBM TP T41p | s3_bios（2），恢复后切换到 X |
| IBM TP T42 | s3_bios（2） |
| IBM ThinkPad T42p (2373-GTG) | s3_bios（2） |
| IBM TP X20 | 未知 |
| IBM TP X30 | s3_bios，s3_mode（4） |
| IBM TP X31 / Type 2672-XXH | 无（1），使用 radeontool（`http://fdd.com/software/radeon/`）来关闭背光 |
| IBM TP X32 | 无（1），但长时间挂起后背光会开启而视频被破坏。s3_bios、s3_mode（4）也能工作。也许这样能得到更好的结果？ |
| IBM Thinkpad X40 Type 2371-7JG | s3_bios,s3_mode（4） |
| IBM TP 600e | 无（1），但需要从控制台切换回 X |
| Medion MD4220 | 未知 |
| Samsung P35 | 需要 vbetool（6） |
| Sharp PC-AR10 (ATI rage) | 无（1），背光不会关闭 |
| Sony Vaio PCG-C1VRX/K | s3_bios（2） |
| Sony Vaio PCG-F403 | 未知 |
| Sony Vaio PCG-GRT995MP | 无（1），与 ‘nv’ X 驱动程序一起工作 |
| Sony Vaio PCG-GR7/K | 无（1），但需要 radeonfb，使用 radeontool（`http://fdd.com/software/radeon/`）来关闭背光 |
| Sony Vaio PCG-N505SN | 未知 |
| Sony Vaio vgn-s260 | X 或 boot-radeon 可以初始化 |
| Sony Vaio vgn-S580BH | vga=normal，但从 X 挂起。除非返回到 X，否则控制台将为空白 |

注释：
1. 无特定设置要求。
2. 使用 s3_bios 模式。
3. 使用 s3_mode 模式。
4. 使用 s3_mode 和 s3_bios 模式。
5. 使用 vga=normal 和 boot-radeon。
6. 使用 vbetool。
7. 使用 Ole 的后期 BIOS 初始化。
8. 使用 video_post。
索尼 VAIO VGN-FS115B			s3_bios (2)，s3_mode (4)
东芝 Libretto L5				无 (1)
东芝 Libretto 100CT/110CT		vbetool (6)
东芝 Portege 3020CT			s3_mode (3)
东芝 Satellite 4030CDT			s3_mode (3)（S1 同样可以正常工作）
东芝 Satellite 4080XCDT		s3_mode (3)（S1 同样可以正常工作）
东芝 Satellite 4090XCDT			??? [#f1]_
东芝 Satellite P10-554			s3_bios，s3_mode (4)[#f3]_
东芝 M30					(2) 或者 使用内部 AGP 的 Nvidia 驱动进行异或 X
Uniwill 244IIO				??? [#f1]_
================================== ===============================================

已知可工作的台式机系统
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=================== ============================= ========================
主板			显卡				方法（或“如何实现”）
=================== ============================= ========================
华硕 A7V8X			nVidia RIVA TNT2 模型 64		s3_bios，s3_mode (4)
=================== ============================= ========================


.. [#f1] 来自 https://wiki.ubuntu.com/HoaryPMResults，不确定使用哪些选项。如果您知道，请告知我。
.. [#f2] 需要使用较新内核进行测试。
.. [#f3] 不支持 SMP 内核，仅支持 UP。
