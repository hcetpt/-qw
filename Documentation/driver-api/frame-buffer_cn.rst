帧缓冲库
====================

帧缓冲驱动程序严重依赖于四个数据结构。这些
结构在 include/linux/fb.h 中声明。它们是 fb_info，
fb_var_screeninfo，fb_fix_screeninfo 和 fb_monospecs。最后
三个可以供用户空间使用。
fb_info 定义了特定视频卡的当前状态。在
fb_info 内部，存在一个 fb_ops 结构，它是使 fbdev 和 fbcon 工作所需的函数集合。fb_info 只对内核可见。
fb_var_screeninfo 用于描述用户定义的视频卡特性。通过 fb_var_screeninfo，可以定义诸如深度和分辨率等属性。
下一个结构是 fb_fix_screeninfo。这定义了当设置模式时创建且不能以其他方式更改的卡属性。一个很好的例子就是帧缓冲内存的起始位置。这“锁定”了帧缓冲内存的地址，使其无法被更改或移动。
最后一个结构是 fb_monospecs。在旧 API 中，fb_monospecs 的重要性不大。这允许做一些禁止的事情，比如在固定频率监视器上设置 800x600 的模式。在新 API 中，fb_monospecs 防止此类情况的发生，并且如果正确使用，可以防止烧毁显示器。直到内核版本 2.5.x，fb_monospecs 才会变得有用。
帧缓冲内存
-------------------

.. kernel-doc:: drivers/video/fbdev/core/fbmem.c
   :export:

帧缓冲颜色映射
---------------------

.. kernel-doc:: drivers/video/fbdev/core/fbcmap.c
   :export:

帧缓冲视频模式数据库
--------------------------------

.. kernel-doc:: drivers/video/fbdev/core/modedb.c
   :internal:

.. kernel-doc:: drivers/video/fbdev/core/modedb.c
   :export:

Macintosh 帧缓冲视频模式数据库
------------------------------------------

.. kernel-doc:: drivers/video/fbdev/macmodes.c
   :export:

帧缓冲字体
------------------

更多信息请参阅文件 lib/fonts/fonts.c
