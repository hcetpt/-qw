===========================
S3 恢复时的视频问题
===========================

2003-2006，Pavel Machek

在 S3 恢复过程中，硬件需要重新初始化。对于大多数设备而言，这很容易做到，并且内核驱动程序知道如何进行。不幸的是，存在一个例外：显卡。这些通常由 BIOS 初始化，而内核没有足够的信息来启动显卡。（内核通常甚至不包含显卡驱动程序——vesafb 和 vgacon 被广泛使用）
这对 swsusp 并不是问题，因为在 swsusp 恢复期间，BIOS 正常运行，因此显卡正常初始化。它也不应该成为 S1 待机的问题，因为硬件应该在此过程中保持其状态。
我们要么在早期恢复阶段运行显卡的 BIOS，要么稍后使用 vbetool 解释它，或者可能在特定系统上根本不需要任何操作，因为显卡的状态被保留了。不幸的是，不同的方法适用于不同的系统，而且目前没有一种已知的方法适用于所有系统。
已经开发了一个名为 s2ram 的用户空间应用程序；它包含了一个很长的系统白名单，并能自动为给定系统选择有效的方法。可以从 www.sf.net/projects/suspend 的 CVS 中下载。如果你有一个不在白名单中的系统，请尝试找到可行的解决方案，并提交白名单条目，以避免重复工作。
目前，VBE_SAVE 方法（下面的第 6 种方法）在大多数系统上都能工作。不幸的是，vbetool 只能在用户空间恢复之后运行，这就使得调试早期恢复问题变得困难/不可能。不依赖于用户空间的方法更可取。
详情
~~~~~~~

存在几种类型的系统，在 S3 恢复后视频可以正常工作：

(1) 显卡状态在 S3 过程中得以保留的系统
(2) 在 S3 恢复期间可以调用显卡 BIOS 的系统。不幸的是，在这一点上调用显卡 BIOS 是不正确的，但在某些机器上却能够工作。使用 `acpi_sleep=s3_bios`
(3) 将显卡初始化为 VGA 文本模式的系统，并且 BIOS 工作得足够好以至于能够设置视频模式。在这些系统上使用 `acpi_sleep=s3_mode`
(4) 在某些系统上，`s3_bios` 会将显卡踢入文本模式，因此需要 `acpi_sleep=s3_bios,s3_mode`
(5) Radeon 系统，其中 X 可以软启动你的显卡。你需要一个足够新的 X，以及一个纯文本控制台（没有 vesafb 或 radeonfb）。更多信息请参见 http://www.doesi.gmxhome.de/linux/tm800s3/s3.html
或者，你应该使用vbetool（注释6）代替。
（6）对于其他Radeon系统，vbetool足以使系统恢复生机。它需要文本控制台工作。执行vbetool vbestate save > /tmp/delme；echo 3 > /proc/acpi/sleep；vbetool post；vbetool vbestate restore < /tmp/delme；setfont <whatever>，你的视频应该能正常工作。
（7）在某些系统上，可能先启动大部分内核，然后POSTing BIOS有效。Ole Rohne有专门的补丁位于http://dev.gentoo.org/~marineam/patch-radeonfb-2.6.11-rc2-mm2
（8）在一些系统上，你可以使用video_post工具和或执行echo 3 > /sys/power/state && /usr/sbin/video_post，这将在控制台模式下初始化显示。如果你在X中，可以通过CTRL+ALT+F1 - CTRL+ALT+F7切换到虚拟终端再回到X，以图形模式重新激活显示器。

现在，如果你传递了acpi_sleep=something，并且与你的BIOS不兼容，你将在恢复时遇到硬崩溃。请小心。同时最安全的是使用普通的旧VGA控制台进行实验。vesafb和radeonfb（等）驱动程序有在恢复期间导致机器崩溃的倾向。

你可能有一个上述方法都不适用的系统。在这种情况下，你要么发明另一个丑陋但有效的解决方案，要么为你的显卡编写正确的驱动程序（祝你好运获取文档:-()。也许从X中挂起（正确的X，了解你的硬件，不是XF68_FBcon）可能会有更好的工作机会。

已知可工作的笔记本列表：

=============================== ===============================================
型号                           解决方案（或“如何操作”）
=============================== ===============================================
Acer Aspire 1406LC		Ole的延迟BIOS初始化（7），关闭DRI
Acer TM 230			s3_bios（2）
Acer TM 242FX			vbetool（6）
Acer TM C110			video_post（8）
Acer TM C300                    vga=normal（仅在控制台上挂起，不在X中），vbetool（6）或video_post（8）
Acer TM 4052LCi			s3_bios（2）
Acer TM 636Lci			s3_bios,s3_mode（4）
Acer TM 650（Radeon M7）	vga=normal加上boot-radeon（5）可以恢复文本控制台
Acer TM 660			未知 [#f1]_
Acer TM 800			vga=normal，X补丁，参见网页（5），或vbetool（6）
Acer TM 803			vga=normal，X补丁，参见网页（5），或vbetool（6）
Acer TM 803LCi			vga=normal，vbetool（6）
Arima W730a			需要vbetool（6）
Asus L2400D                     s3_mode（3）[#f2]_（S1也工作正常）
Asus L3350M（SiS 740）           （6）
Asus L3800C（Radeon M7）		s3_bios（2）（S1也工作正常）
Asus M6887Ne			vga=normal，s3_bios（2），在x.org中使用radeon驱动程序而不是fglrx
Athlon64桌面原型机	s3_bios（2）
Compal CL-50			未知 [#f1]_
Compaq Armada E500 - P3-700     无（1）（S1也工作正常）
Compaq Evo N620c		vga=normal，s3_bios（2）
Dell 600m，ATI R250 Lf		无（1），但需要xorg-x11-6.8.1.902-1
Dell D600，ATI RV250            vga=normal和X，或尝试vbestate（6）
Dell D610			vga=normal和X（可能vbestate（6）也可以，但未经过测试）
Dell Inspiron 4000		未知 [#f1]_
Dell Inspiron 500m		未知 [#f1]_
Dell Inspiron 510m		未知
Dell Inspiron 5150		需要vbetool（6）
Dell Inspiron 600m		未知 [#f1]_
Dell Inspiron 8200		未知 [#f1]_
Dell Inspiron 8500		未知 [#f1]_
Dell Inspiron 8600		未知 [#f1]_
eMachines Athlon64机器	vbetool所需（6）（有人请给我模型号）
HP NC6000			s3_bios，可能不能使用radeonfb（2）；或vbetool（6）
HP NX7000			未知 [#f1]_
HP Pavilion ZD7000		需要vbetool post，需要开源nv驱动程序用于X
HP Omnibook XE3		athlon版本	无（1）
HP Omnibook XE3GC		无（1），视频是S3 Savage/IX-MV
HP Omnibook XE3L-GF		vbetool（6）
HP Omnibook 5150		无（1），（S1也工作正常）
IBM TP T20，型号2647-44G	无（1），视频是S3 Inc. 86C270-294 Savage/IX-MV，vesafb得到“有趣”的但X工作
IBM TP A31 / 类型2652-M5G      s3_mode（3）[与BIOS 1.04 2002-08-23工作正常，但与BIOS 1.11 2004-11-05完全不行：-（]
IBM TP R32 / 类型2658-MMG      无（1）
IBM TP R40 2722B3G		未知 [#f1]_
IBM TP R50p / 类型1832-22U     s3_bios（2）
IBM TP R51			无（1）
IBM TP T30	236681A		未知 [#f1]_
IBM TP T40 / 类型2373-MU4      无（1）
IBM TP T40p			无（1）
IBM TP R40p			s3_bios（2）
IBM TP T41p			s3_bios（2），恢复后切换到X
IBM TP T42			s3_bios（2）
IBM ThinkPad T42p（2373-GTG）	s3_bios（2）
IBM TP X20			未知 [#f1]_
IBM TP X30			s3_bios，s3_mode（4）
IBM TP X31 / 类型2672-XXH      无（1），使用radeontool（http://fdd.com/software/radeon/）关闭背光
IBM TP X32			无（1），但长时间挂起后背光亮着且视频被破坏。s3_bios，s3_mode（4）也有效。或许能得到更好的结果？
IBM Thinkpad X40 Type 2371-7JG  s3_bios,s3_mode（4）
IBM TP 600e			无（1），但需要切换到控制台再回到X
Medion MD4220			未知 [#f1]_
Samsung P35			需要vbetool（6）
Sharp PC-AR10（ATI rage）	无（1），背光不会关闭
Sony Vaio PCG-C1VRX/K		s3_bios（2）
Sony Vaio PCG-F403		未知 [#f1]_
Sony Vaio PCG-GRT995MP		无（1），与'nv' X驱动程序工作
Sony Vaio PCG-GR7/K		无（1），但需要radeonfb，使用radeontool（http://fdd.com/software/radeon/）关闭背光
Sony Vaio PCG-N505SN		未知 [#f1]_
Sony Vaio vgn-s260		X或boot-radeon可以初始化（5）
Sony Vaio vgn-S580BH		vga=normal，但从X挂起。除非返回到X，否则控制台将为空白
以下是给定文本的中文翻译：

Sony Vaio vgn-FS115B		s3_bios（2），s3_mode（4）
东芝Libretto L5		无（1）
东芝Libretto 100CT/110CT    vbetool（6）
东芝Portege 3020CT		s3_mode（3）
东芝Satellite 4030CDT	s3_mode（3）（S1也正常工作）
东芝Satellite 4080XCDT      s3_mode（3）（S1也正常工作）
东芝Satellite 4090XCDT      ??? [#f1]_
东芝Satellite P10-554       s3_bios，s3_mode（4）[#f3]_
东芝M30                     （2）或使用内部AGP的NVIDIA驱动程序与X进行异或运算
Uniwill 244IIO			??? [#f1]_
================================= ==============================================

已知可工作的台式机系统
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

===== ====== =============== ============
主板	    显卡                 解决方案（或“如何操作”）
===== ====== =============== ============
华硕A7V8X	    NVIDIA RIVA TNT2型号64	  s3_bios，s3_mode（4）
===== ====== =============== ============

.. [#f1] 来自https://wiki.ubuntu.com/HoaryPMResults，不确定使用哪些选项。如果您知道，请告诉我
.. [#f2] 需要用更新的内核测试
.. [#f3] 不适用于SMP内核，仅适用于UP
