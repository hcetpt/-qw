===========================
包含 uAPI 头文件
===========================

有时，为了描述用户空间 API 并在代码与文档之间生成交叉引用，包含头文件和 C 示例代码是有用的。为用户空间 API 文件添加交叉引用还有一个额外的优势：如果在文档中找不到某个符号，Sphinx 会生成警告。这有助于保持 uAPI 文档与内核更改同步。
:ref:`parse_headers.pl <parse_headers>` 提供了一种生成此类交叉引用的方法。它需要通过 Makefile 调用，在构建文档时使用。请参阅 ``Documentation/userspace-api/media/Makefile`` 了解如何在内核树中使用它的示例。
.. _parse_headers:

parse_headers.pl
^^^^^^^^^^^^^^^^

名称
****

parse_headers.pl - 解析 C 文件以识别函数、结构体、枚举和宏定义，并为 Sphinx 书籍创建交叉引用
概述
**********

\ **parse_headers.pl**\  [<选项>] <C_FILE> <OUT_FILE> [<EXCEPTIONS_FILE>]

其中 <选项> 可以是：--debug, --help 或 --usage
选项
*******

\ **--debug**\

使脚本处于详细输出模式，对于调试很有用
\ **--usage**\

打印简要的帮助信息并退出
\ **--help**\

打印更详细的帮助信息并退出
描述
***********

将 C 头文件或源文件 (C_FILE) 转换为带有交叉引用的 reStructuredText，这些交叉引用用于描述 API 的文档文件。它可以接受一个可选的 EXCEPTIONS_FILE，该文件描述了哪些元素将被忽略或指向非默认的引用。
输出写入到 (OUT_FILE)。
它能够识别宏定义、函数、结构体、类型定义、枚举及枚举成员，并为它们全部创建交叉引用。
它还能够识别用于指定 Linux 的 `#define` 中的 ioctl。

`EXCEPTIONS_FILE` 包含两种类型的声明：\ **忽略**\ 或 \ **替换**\ 。

忽略标签的语法为：

ignore \ **类型**\  \ **名称**\

\ **忽略**\ 意味着它不会为类型为 \ **类型**\ 的 \ **名称**\ 符号生成交叉引用。

替换标签的语法为：

replace \ **类型**\  \ **名称**\  \ **新值**\

\ **替换**\ 意味着它将为类型为 \ **类型**\ 的 \ **名称**\ 符号生成交叉引用，但是，它不使用默认的替换规则，而是使用 \ **新值**\ 。

对于这两种声明，\ **类型**\ 可以是以下之一：

\ **ioctl**\

忽略或替换声明适用于像这样的 ioctl 定义：

```c
#define	VIDIOC_DBG_S_REGISTER 	 _IOW('V', 79, struct v4l2_dbg_register)
```

\ **define**\

忽略或替换声明适用于在 C 文件中找到的任何其他 `#define`。

\ **typedef**\

忽略或替换声明适用于 C 文件中的 `typedef` 声明。

\ **struct**\

忽略或替换声明适用于 C 文件中的结构体声明的名称。

\ **enum**\

忽略或替换声明适用于 C 文件中的枚举声明的名称。

\ **symbol**\

忽略或替换声明适用于 C 文件中的枚举值的名称。

对于替换声明，\ **新值**\ 将自动为 \ **typedef**\ 、\ **enum**\ 和 \ **struct**\ 类型使用 :c:type: 引用。对于 \ **ioctl**\ 、\ **define**\ 和 \ **symbol**\ 类型则使用 :ref:。引用的类型也可以在替换声明中明确定义。
### 示例
**********

忽略定义 `_VIDEODEV2_H`

在 C 文件中忽略 `#define _VIDEODEV2_H`

忽略符号 `PRIVATE`

对于如下结构：

```c
enum foo { BAR1, BAR2, PRIVATE };
```

它不会为 `PRIVATE` 生成交叉引用。

替换符号 `BAR1` 为 `:c:type:``foo``  
替换符号 `BAR2` 为 `:c:type:``foo``  

对于如下结构：

```c
enum foo { BAR1, BAR2, PRIVATE };
```

它会使 `BAR1` 和 `BAR2` 枚举符号与 `foo` 符号在 C 领域中进行交叉引用。

### 问题
****

向 Mauro Carvalho Chehab <mchehab@kernel.org> 报告问题。

### 版权
*********

版权所有 © 2016 Mauro Carvalho Chehab <mchehab+samsung@kernel.org>

许可协议：GPLv2：GNU GPL 第2版 <https://gnu.org/licenses/gpl.html>

这是一款自由软件：您可以自由更改和重新分发它。

法律允许的范围内，不提供任何保证。
