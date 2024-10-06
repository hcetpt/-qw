配置目标和编辑器
=================

此文件包含了一些使用 ``make *config`` 的帮助信息。
使用 ``make help`` 列出所有可能的配置目标。
xconfig ('qconf')、menuconfig ('mconf') 和 nconfig ('nconf') 程序中也有嵌入的帮助文本。确保查看这些程序以获取导航、搜索和其他一般帮助信息。
gconfig ('gconf') 程序提供的帮助文本有限。

总览
=======

新的内核版本通常会引入新的配置符号。更重要的是，新的内核版本可能会重命名配置符号。在这种情况下，使用以前有效的 .config 文件并运行 "make oldconfig" 不一定会为你生成一个可用的新内核，因此你可能需要查看新引入的内核符号。
要查看新配置符号的列表，请使用：

    cp user/some/old.config .config
    make listnewconfig

配置程序将逐行列出所有新的符号。
或者，你可以使用暴力方法：

    make oldconfig
    scripts/diffconfig .config.old .config | less

环境变量
=====================

``*config`` 的环境变量：

``KCONFIG_CONFIG``
    此环境变量可以用来指定一个默认的内核配置文件名，以覆盖默认的 ".config" 名称。

``KCONFIG_DEFCONFIG_LIST``
    此环境变量指定了一个配置文件列表，可以在 .config 尚不存在的情况下作为基础配置使用。
列表中的条目之间用空格分隔，并且会使用第一个存在的文件。

``KCONFIG_OVERWRITECONFIG``
    如果你在环境中设置了 KCONFIG_OVERWRITECONFIG，当 .config 是指向其他位置的符号链接时，Kconfig 不会破坏这些符号链接。
``KCONFIG_WARN_UNKNOWN_SYMBOLS``
    此环境变量使 Kconfig 在配置输入中对所有未识别的符号发出警告。

``KCONFIG_WERROR``
    如果设置此变量，Kconfig 将把警告视为错误处理。

``CONFIG_``
    如果在环境中设置了 ``CONFIG_``，Kconfig 在保存配置时会使用其值作为所有符号的前缀，而不是使用默认的 ``CONFIG_``。

用于 ``{allyes/allmod/allno/rand}config`` 的环境变量：

``KCONFIG_ALLCONFIG``
    ``allyesconfig``、``allmodconfig``、``allnoconfig`` 和 ``randconfig`` 变体也可以使用环境变量 ``KCONFIG_ALLCONFIG`` 作为标志或包含用户需要设置为特定值的配置符号的文件名。如果 ``KCONFIG_ALLCONFIG`` 在没有文件名的情况下使用（即 ``KCONFIG_ALLCONFIG == ""`` 或 ``KCONFIG_ALLCONFIG == "1"``），则 ``make *config`` 会检查一个名为 "all{yes/mod/no/def/random}.config" 的文件（对应于使用的 ``*config`` 命令）以获取要强制设置的符号值。如果没有找到该文件，则会检查名为 "all.config" 的文件以包含强制设置的值。
这使您可以创建“微型”配置（miniconfig）或自定义配置文件，其中只包含您感兴趣的配置符号。然后内核配置系统将生成完整的 .config 文件，包括您的 miniconfig 文件中的符号。

``KCONFIG_ALLCONFIG`` 文件是一个配置文件，其中包含（通常是所有符号的一个子集）预设的配置符号。这些变量设置仍然受常规依赖性检查的约束。

示例：

        KCONFIG_ALLCONFIG=custom-notebook.config make allnoconfig

    或者：

        KCONFIG_ALLCONFIG=mini.config make allnoconfig

    或者：

        make KCONFIG_ALLCONFIG=mini.config allnoconfig

    这些示例将禁用大多数选项（allnoconfig），但启用或禁用指定的微型配置文件中明确列出的选项。

用于 ``randconfig`` 的环境变量：

``KCONFIG_SEED``
    您可以将其设置为整数值以初始化随机数生成器（RNG），如果您想以某种方式调试 kconfig 解析器/前端的行为。如果不设置，则使用当前时间。

``KCONFIG_PROBABILITY``
    此变量可用于调整概率。此变量可以不设置或为空，或者设置为三种不同的格式：

    =======================     ==================  =====================
    KCONFIG_PROBABILITY         y:n 分割            y:m:n 分割
    =======================     ==================  =====================
    不设置或空                 50  : 50            33  : 33  : 34
    N                            N  : 100-N         N/2 : N/2 : 100-N
    [1] N:M                     N+M : 100-(N+M)      N  :  M  : 100-(N+M)
    [2] N:M:L                    N  : 100-N          M  :  L  : 100-(M+L)
    =======================     ==================  =====================

其中 N、M 和 L 是范围 [0,100] 内的十进制整数，并且满足以下条件：

    [1] N+M 在范围 [0,100] 内

    [2] M+L 在范围 [0,100] 内

示例：

    KCONFIG_PROBABILITY=10
        10% 的布尔值将设置为 'y'，90% 设置为 'n'
        5% 的三态值将设置为 'y'，5% 设置为 'm'，90% 设置为 'n'
    KCONFIG_PROBABILITY=15:25
        40% 的布尔值将设置为 'y'，60% 设置为 'n'
        15% 的三态值将设置为 'y'，25% 设置为 'm'，60% 设置为 'n'
    KCONFIG_PROBABILITY=10:15:15
        10% 的布尔值将设置为 'y'，90% 设置为 'n'
        15% 的三态值将设置为 'y'，15% 设置为 'm'，70% 设置为 'n'

用于 ``syncconfig`` 的环境变量：

``KCONFIG_NOSILENTUPDATE``
    如果此变量具有非空白值，则防止静默内核配置更新（需要显式更新）。
``KCONFIG_AUTOCONFIG``
此环境变量可以设置来指定“auto.conf”文件的路径和名称。其默认值为“include/config/auto.conf”。

``KCONFIG_AUTOHEADER``
此环境变量可以设置来指定“autoconf.h”（头文件）的路径和名称。
其默认值为“include/generated/autoconf.h”。

menuconfig
==========

在menuconfig中搜索：

搜索功能用于查找内核配置符号名称，因此你需要知道你要找的内容。
示例::

        /hotplug
        这将列出所有包含“hotplug”的配置符号，例如HOTPLUG_CPU、MEMORY_HOTPLUG。
对于搜索帮助，输入/后按两次TAB（以高亮显示<Help>），然后按Enter。这会告诉你可以在搜索字符串中使用正则表达式（regex）。因此，如果你对MEMORY_HOTPLUG不感兴趣，你可以尝试如下命令::

        /^hotplug

在搜索时，符号按照以下顺序排序：

- 首先，完全匹配项按字母顺序排序（完全匹配是指搜索匹配整个符号名称）；
- 然后，其他匹配项按字母顺序排序。

例如，^ATH.K 匹配如下内容：

        ATH5K ATH9K ATH5K_AHB ATH5K_DEBUG [...] ATH6KL ATH6KL_DEBUG
        [...] ATH9K_AHB ATH9K_BTCOEX_SUPPORT ATH9K_COMMON [...]

其中只有ATH5K和ATH9K是完全匹配项，因此它们排在最前面（并按字母顺序排列），然后是其他符号，按字母顺序排列。

在此菜单中，按带有(#)前缀的键可以直接跳转到该位置。退出新菜单后，你会返回当前的搜索结果。

menuconfig的用户界面选项：

``MENUCONFIG_COLOR``
可以使用MENUCONFIG_COLOR变量选择不同的颜色主题。要选择一个主题，请使用如下命令::

        make MENUCONFIG_COLOR=<theme> menuconfig

可用的主题包括::

      - mono       => 适用于单色显示器的颜色方案
      - blackbg    => 带有黑色背景的颜色方案
      - classic    => 蓝色背景的经典主题。经典外观
      - bluetitle  => 经典主题的LCD友好版本。（默认）

``MENUCONFIG_MODE``
此模式在一个大的树形结构中显示所有子菜单。
示例::

        make MENUCONFIG_MODE=single_menu menuconfig

nconfig
=======

nconfig是一个替代的基于文本的配置工具。它在终端（窗口）底部列出执行命令的功能键。
你也可以直接使用相应的数字键来执行命令，除非你在数据输入窗口中。例如，你可以直接按6键而不是F6来保存。
使用F1获取全局帮助或F3获取简短帮助菜单。

在nconfig中搜索：

你可以搜索菜单项的“提示”字符串或配置符号。
使用/开始在菜单项中搜索。这不支持正则表达式。使用<Down>或<Up>分别查找下一个匹配项和上一个匹配项。使用<Esc>终止搜索模式。
F8（SymSearch）根据给定的字符串或正则表达式（regex）搜索配置符号。
在SymSearch中，按下带有(#)前缀的键将直接跳转到该位置。退出这个新菜单后，你会返回当前的搜索结果。

环境变量：

``NCONFIG_MODE``
此模式在一个大的树形结构中显示所有子菜单。
示例：

```
make NCONFIG_MODE=single_menu nconfig
```

xconfig
=======

在xconfig中搜索：

搜索功能会搜索内核配置符号名称，因此你需要知道你要找的内容。
示例：

```
Ctrl-F hotplug
```

或者：

```
菜单：文件，搜索，hotplug
```

列出所有包含“hotplug”的符号名称的配置条目。在此搜索对话框中，你可以更改任何未被灰显的条目的配置设置。
你也可以在不返回主菜单的情况下输入不同的搜索字符串。
gconfig
=======

在 gconfig 中搜索：

    gconfig 没有专门的搜索命令。但是，gconfig 提供了多种不同的查看选项、模式和设置。
