```spdx
许可协议标识符: GPL-2.0 或 GFDL-1.1-no-invariants-or-later

.. _遥控器表格:

************************
遥控器表格
************************

遗憾的是，多年来并没有努力为不同设备创建统一的红外线（IR）按键代码。这导致了相同的红外线键名在不同的红外线设备上被完全不同的映射。因此，相同红外线键名在不同的红外线上被完全不同的映射。鉴于此，V4L2 API 现在规定了一种将媒体键映射到红外线的标准。
这个标准应该同时被 V4L/DVB 驱动程序和用户空间应用程序使用。

模块在 Linux 输入层中将遥控器注册为键盘。这意味着红外线按键将像普通键盘按键一样工作（如果启用了 CONFIG_INPUT_KEYBOARD）。通过事件设备（CONFIG_INPUT_EVDEV），应用程序可以访问 /dev/input/event 设备中的遥控器。
.. _rc_standard_keymap:

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 红外线默认键映射
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2


    -  .. 行 1

       -  键码

       -  含义

       -  红外线键示例

    -  .. 行 2

       -  **数字键**

    -  .. 行 3

       -  ``KEY_NUMERIC_0``

       -  键盘数字 0

       -  0

    -  .. 行 4

       -  ``KEY_NUMERIC_1``

       -  键盘数字 1

       -  1

    -  .. 行 5

       -  ``KEY_NUMERIC_2``

       -  键盘数字 2

       -  2

    -  .. 行 6

       -  ``KEY_NUMERIC_3``

       -  键盘数字 3

       -  3

    -  .. 行 7

       -  ``KEY_NUMERIC_4``

       -  键盘数字 4

       -  4

    -  .. 行 8

       -  ``KEY_NUMERIC_5``

       -  键盘数字 5

       -  5

    -  .. 行 9

       -  ``KEY_NUMERIC_6``

       -  键盘数字 6

       -  6

    -  .. 行 10

       -  ``KEY_NUMERIC_7``

       -  键盘数字 7

       -  7

    -  .. 行 11

       -  ``KEY_NUMERIC_8``

       -  键盘数字 8

       -  8

    -  .. 行 12

       -  ``KEY_NUMERIC_9``

       -  键盘数字 9

       -  9

    -  .. 行 13

       -  **影片播放控制**

    -  .. 行 14

       -  ``KEY_FORWARD``

       -  即时快进

       -  >> / FORWARD

    -  .. 行 15

       -  ``KEY_BACK``

       -  即时回放

       -  <<< / BACK

    -  .. 行 16

       -  ``KEY_FASTFORWARD``

       -  快速播放影片

       -  >>> / FORWARD

    -  .. 行 17

       -  ``KEY_REWIND``

       -  倒带播放影片

       -  REWIND / BACKWARD

    -  .. 行 18

       -  ``KEY_NEXT``

       -  选择下一章节 / 子章节 / 区间

       -  NEXT / SKIP

    -  .. 行 19

       -  ``KEY_PREVIOUS``

       -  选择前一章节 / 子章节 / 区间

       -  << / PREV / PREVIOUS

    -  .. 行 20

       -  ``KEY_AGAIN``

       -  重复视频或视频区间

       -  REPEAT / LOOP / RECALL

    -  .. 行 21

       -  ``KEY_PAUSE``

       -  暂停流

       -  PAUSE / FREEZE

    -  .. 行 22

       -  ``KEY_PLAY``

       -  正常播放速度播放影片

       -  NORMAL TIMESHIFT / LIVE / >

    -  .. 行 23

       -  ``KEY_PLAYPAUSE``

       -  在播放与暂停之间切换

       -  PLAY / PAUSE

    -  .. 行 24

       -  ``KEY_STOP``

       -  停止流

       -  STOP

    -  .. 行 25

       -  ``KEY_RECORD``

       -  开始/停止录制流

       -  CAPTURE / REC / RECORD/PAUSE

    -  .. 行 26

       -  ``KEY_CAMERA``

       -  拍摄图像的照片

       -  CAMERA ICON / CAPTURE / SNAPSHOT

    -  .. 行 27

       -  ``KEY_SHUFFLE``

       -  启用随机播放模式

       -  SHUFFLE

    -  .. 行 28

       -  ``KEY_TIME``

       -  激活时间移位模式

       -  TIME SHIFT

    -  .. 行 29

       -  ``KEY_TITLE``

       -  允许更改章节

       -  CHAPTER

    -  .. 行 30

       -  ``KEY_SUBTITLE``

       -  允许更改字幕

       -  SUBTITLE

    -  .. 行 31

       -  **图像控制**

    -  .. 行 32

       -  ``KEY_BRIGHTNESSDOWN``

       -  减少亮度

       -  BRIGHTNESS DECREASE

    -  .. 行 33

       -  ``KEY_BRIGHTNESSUP``

       -  增加亮度

       -  BRIGHTNESS INCREASE

    -  .. 行 34

       -  ``KEY_ANGLE``

       -  切换视频摄像机角度（对于包含多个角度存储的视频）

       -  ANGLE / SWAP

    -  .. 行 35

       -  ``KEY_EPG``

       -  打开电子节目指南（EPG）

       -  EPG / GUIDE

    -  .. 行 36

       -  ``KEY_TEXT``

       -  激活/更改隐藏字幕模式

       -  CLOSED CAPTION/TELETEXT / DVD TEXT / TELETEXT / TTX

    -  .. 行 37

       -  **音频控制**

    -  .. 行 38

       -  ``KEY_AUDIO``

       -  更改音频源

       -  AUDIO SOURCE / AUDIO / MUSIC

    -  .. 行 39

       -  ``KEY_MUTE``

       -  静音/取消静音音频

       -  MUTE / DEMUTE / UNMUTE

    -  .. 行 40

       -  ``KEY_VOLUMEDOWN``

       -  减小音量

       -  VOLUME- / VOLUME DOWN

    -  .. 行 41

       -  ``KEY_VOLUMEUP``

       -  增大音量

       -  VOLUME+ / VOLUME UP

    -  .. 行 42

       -  ``KEY_MODE``

       -  更改声音模式

       -  MONO/STEREO

    -  .. 行 43

       -  ``KEY_LANGUAGE``

       -  选择语言

       -  1ST / 2ND LANGUAGE / DVD LANG / MTS/SAP / MTS SEL

    -  .. 行 44

       -  **频道控制**

    -  .. 行 45

       -  ``KEY_CHANNEL``

       -  转到下一个喜爱的频道

       -  ALT / CHANNEL / CH SURFING / SURF / FAV

    -  .. 行 46

       -  ``KEY_CHANNELDOWN``

       -  顺序减小频道

       -  CHANNEL - / CHANNEL DOWN / DOWN

    -  .. 行 47

       -  ``KEY_CHANNELUP``

       -  顺序增加频道

       -  CHANNEL + / CHANNEL UP / UP

    -  .. 行 48

       -  ``KEY_DIGITS``

       -  使用多个数字设置频道

       -  PLUS / 100/ 1xx / xxx / -/-- / Single Double Triple Digit

    -  .. 行 49

       -  ``KEY_SEARCH``

       -  开始频道自动扫描

       -  SCAN / AUTOSCAN

    -  .. 行 50

       -  **彩色键**

    -  .. 行 51

       -  ``KEY_BLUE``

       -  红外线蓝色键

       -  BLUE

    -  .. 行 52

       -  ``KEY_GREEN``

       -  红外线绿色键

       -  GREEN

    -  .. 行 53

       -  ``KEY_RED``

       -  红外线红色键

       -  RED

    -  .. 行 54

       -  ``KEY_YELLOW``

       -  红外线黄色键

       -  YELLOW

    -  .. 行 55

       -  **媒体选择**

    -  .. 行 56

       -  ``KEY_CD``

       -  切换输入源至光盘

       -  CD

    -  .. 行 57

       -  ``KEY_DVD``

       -  切换输入至 DVD

       -  DVD / DVD MENU

    -  .. 行 58

       -  ``KEY_EJECTCLOSECD``

       -  打开/关闭 CD/DVD 播放器

       -  -> ) / CLOSE / OPEN

    -  .. 行 59

       -  ``KEY_MEDIA``

       -  开启/关闭媒体应用

       -  PC/TV / TURN ON/OFF APP

    -  .. 行 60

       -  ``KEY_PC``

       -  切换至 PC 模式

       -  PC

    -  .. 行 61

       -  ``KEY_RADIO``

       -  切换至 AM/FM 收音机模式

       -  RADIO / TV/FM / TV/RADIO / FM / FM/RADIO

    -  .. 行 62

       -  ``KEY_TV``

       -  选择电视模式

       -  TV / LIVE TV

    -  .. 行 63

       -  ``KEY_TV2``

       -  选择有线模式

       -  AIR/CBL

    -  .. 行 64

       -  ``KEY_VCR``

       -  选择录像机模式

       -  VCR MODE / DTR

    -  .. 行 65

       -  ``KEY_VIDEO``

       -  在输入模式之间切换

       -  SOURCE / SELECT / DISPLAY / SWITCH INPUTS / VIDEO

    -  .. 行 66

       -  **电源控制**

    -  .. 行 67

       -  ``KEY_POWER``

       -  开启/关闭计算机

       -  SYSTEM POWER / COMPUTER POWER

    -  .. 行 68

       -  ``KEY_POWER2``

       -  开启/关闭应用

       -  TV ON/OFF / POWER

    -  .. 行 69

       -  ``KEY_SLEEP``

       -  启用睡眠定时器

       -  SLEEP / SLEEP TIMER

    -  .. 行 70

       -  ``KEY_SUSPEND``

       -  将计算机置于待机模式

       -  STANDBY / SUSPEND

    -  .. 行 71

       -  **窗口控制**

    -  .. 行 72

       -  ``KEY_CLEAR``

       -  停止流并返回默认输入视频/音频

       -  CLEAR / RESET / BOSS KEY

    -  .. 行 73

       -  ``KEY_CYCLEWINDOWS``

       -  最小化窗口并切换到下一个

       -  ALT-TAB / MINIMIZE / DESKTOP

    -  .. 行 74

       -  ``KEY_FAVORITES``

       -  打开收藏流窗口

       -  TV WALL / Favorites

    -  .. 行 75

       -  ``KEY_MENU``

       -  调出应用菜单

       -  2ND CONTROLS (USA: MENU) / DVD/MENU / SHOW/HIDE CTRL

    -  .. 行 76

       -  ``KEY_NEW``

       -  打开/关闭画中画

       -  PIP

    -  .. 行 77

       -  ``KEY_OK``

       -  向应用发送确认码

       -  OK / ENTER / RETURN

    -  .. 行 78

       -  ``KEY_ASPECT_RATIO``

       -  选择屏幕宽高比

       -  4:3 16:9 SELECT

    -  .. 行 79

       -  ``KEY_FULL_SCREEN``

       -  进入缩放/全屏模式

       -  ZOOM / FULL SCREEN / ZOOM+ / HIDE PANEL / SWITCH

    -  .. 行 80

       -  **导航键**

    -  .. 行 81

       -  ``KEY_ESC``

       -  取消当前操作

       -  CANCEL / BACK

    -  .. 行 82

       -  ``KEY_HELP``

       -  打开帮助窗口

       -  HELP

    -  .. 行 83

       -  ``KEY_HOMEPAGE``

       -  导航至主页

       -  HOME

    -  .. 行 84

       -  ``KEY_INFO``

       -  打开屏幕显示

       -  DISPLAY INFORMATION / OSD

    -  .. 行 85

       -  ``KEY_WWW``

       -  打开默认浏览器

       -  WEB

    -  .. 行 86

       -  ``KEY_UP``

       -  上键

       -  UP

    -  .. 行 87

       -  ``KEY_DOWN``

       -  下键

       -  DOWN

    -  .. 行 88

       -  ``KEY_LEFT``

       -  左键

       -  LEFT

    -  .. 行 89

       -  ``KEY_RIGHT``

       -  右键

       -  RIGHT

    -  .. 行 90

       -  **其他键**

    -  .. 行 91

       -  ``KEY_DOT``

       -  返回一个点

       - 

    -  .. 行 92

       -  ``KEY_FN``

       -  选择功能

       -  FUNCTION

应注意，有时一些较便宜的红外线遥控器缺少一些基本按键。鉴于此，建议：

.. _rc_keymap_notes:

.. flat-table:: 注意事项
    :header-rows:  0
    :stub-columns: 0


    -  .. 行 1

       -  对于较简单的红外线遥控器，没有单独的频道键时，需要将 UP 映射为 ``KEY_CHANNELUP``

    -  .. 行 2

       -  对于较简单的红外线遥控器，没有单独的频道键时，需要将 DOWN 映射为 ``KEY_CHANNELDOWN``

    -  .. 行 3

       -  对于较简单的红外线遥控器，没有单独的音量键时，需要将 LEFT 映射为 ``KEY_VOLUMEDOWN``

    -  .. 行 4

       -  对于较简单的红外线遥控器，没有单独的音量键时，需要将 RIGHT 映射为 ``KEY_VOLUMEUP``
```
