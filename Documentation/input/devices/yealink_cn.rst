Yealink USB-P1K 电话的驱动文档
===============================================

状态
======

P1K 是一款相对便宜的 USB 1.1 电话，具有以下功能：

- 键盘：完全支持，yealink.ko / 输入事件 API
- 液晶屏：完全支持，yealink.ko / sysfs API
- LED：完全支持，yealink.ko / sysfs API
- 拨号音：完全支持，yealink.ko / sysfs API
- 铃声：完全支持，yealink.ko / sysfs API
- 音频播放：完全支持，snd_usb_audio.ko / ALSA API
- 音频录音：完全支持，snd_usb_audio.ko / ALSA API

如需查看厂商文档，请访问 http://www.yealink.com

键盘功能
=================

当前内核中的映射由 map_p1k_to_key 函数提供如下所示：

```
物理 USB-P1K 按键布局  输入事件

       上                  上
  接入   断开     左        右
       下                  下

接听   C   挂断   回车      删除    退出
  1     2     3          1, 2, 3
  4     5     6          4, 5, 6
  7     8     9          7, 8, 9
  *     0     #          *, 0, #
```

“上”和“下”键用按钮上的箭头表示。
“接听”和“挂断”键用按钮上的绿色和红色电话图标表示。

液晶屏功能
============

液晶屏被划分为一个三行显示：

```
|[]   [][]   [][]   [][]   in   |[][]
|[] M [][] D [][] : [][]   out  |[][]
                              store

NEW REP         SU MO TU WE TH FR SA

[] [] [] [] [] [] [] [] [] [] [] []
[] [] [] [] [] [] [] [] [] [] [] []
```

格式描述：
从用户空间的角度来看，世界被分为“数字”和“图标”。
一个数字可以有一个字符集，而一个图标只能是“打开”或“关闭”。

格式说明符：

- `'8'`：通用七段数码管，每个段落可单独寻址
- `'1'`：只有两个段落的数字，仅能显示 1
- `'e'`：月份中最重要的日期数字，至少能显示 1、2、3
- `'M'`：最重要的分钟数字，至少能显示 0、1、2、3、4、5
- 图标或图示：
  - `'.'`：例如 AM、PM、SU 等单个段落元素或点。
驱动程序使用说明
============

对于用户空间，可以通过 sysfs 接口使用以下接口：

  /sys/.../
           line1 读/写，LCD 第一行
           line2 读/写，LCD 第二行
           line3 读/写，LCD 第三行

	   get_icons 读取，返回可用图标集
	   hide_icon 写入，通过写入图标名称来隐藏元素
	   show_icon 写入，通过写入图标名称来显示元素
	   map_seg7 读/写，7 段字符集，适用于所有 Yealink 电话。（参见 map_to_7segment.h）

	   ringtone 写入，上传铃声的二进制表示，参见 yealink.c。状态为 实验性，因为可能存在异步和同步 USB 调用之间的竞态条件

lineX
~~~~~

读取 /sys/../lineX 将返回当前值的格式字符串。
示例：
```
    cat ./line3
    888888888888
    Linux Rocks!
```

向 /sys/../lineX 写入将设置对应的 LCD 行。
- 多余的字符会被忽略
- 如果写入的字符少于允许的数量，则剩余的字符保持不变
- 制表符 '\t' 和换行符 '\n' 不会覆盖原有内容
- 向图标写入空格将始终隐藏其内容
示例：

    date +"%m.%e.%k:%M"  | sed 's/^0/ /' > ./line1

这将更新LCD上的当前日期和时间。
获取图标
~~~~~~~~~

读取此文件将返回所有可用的图标名称及其当前设置：

    cat ./get_icons
    on M
    on D
    on :
       IN
       OUT
       STORE
       NEW
       REP
       SU
       MO
       TU
       WE
       TH
       FR
       SA
       LED
       DIALTONE
       RINGTONE

显示/隐藏图标
~~~~~~~~~~~~~~~

写入这些文件将更新图标的显示状态
每次只能更新一个图标
如果图标也在某个./lineX上，相应的值将用图标的首字母进行更新
示例 - 点亮商店图标：

    echo -n "STORE" > ./show_icon

    cat ./line1
    18.e8.M8.88...188
		  S

示例 - 发出铃声10秒：

    echo -n RINGTONE > /sys/..../show_icon
    sleep 10
    echo -n RINGTONE > /sys/..../hide_icon

声音功能
==============

声音由ALSA驱动（snd_usb_audio）支持：

设备的实际限制是一个16位通道，采样和播放速率为8000 Hz。
示例 - 录音测试：

    arecord -v -d 10 -r 8000 -f S16_LE -t wav  foobar.wav

示例 - 播放测试：

    aplay foobar.wav

故障排除
==============

问：模块yealink编译和安装没有问题，但电话未初始化且对任何操作无反应
答：如果你看到类似以下信息：
    hiddev0: USB HID v1.00 Device [Yealink Network Technology Ltd. VOIP USB Phone]
在dmesg中，这意味着hid驱动程序首先捕获了该设备。尝试在其他USB hid驱动程序之前加载yealink模块。请参阅你的发行版提供的有关模块配置的说明。
问：电话现在可以工作了（显示版本并接受键盘输入），但我找不到sysfs文件
答：sysfs文件位于特定的USB端点上。在大多数发行版中，你可以执行："find /sys/ -name get_icons"来获取提示。

致谢与鸣谢
=========================

  - Olivier Vandorpe，启动usbb2k-api项目并进行了大量的逆向工程。
- Martin Diehl，指出了如何处理USB内存分配
- Dmitry Torokhov，进行了大量的代码审查并提出了建议
