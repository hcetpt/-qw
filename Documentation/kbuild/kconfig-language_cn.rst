Kconfig 语言
============

简介
------------

配置数据库是一组以树形结构组织的配置选项：

	+- 代码成熟度级别选项
	|  +- 提示开发中和/或不完整的代码/驱动程序
	+- 通用设置
	|  +- 网络支持
	|  +- System V IPC
	|  +- BSD 进程会计
	|  +- Sysctl 支持
	+- 可加载模块支持
	|  +- 启用可加载模块支持
	|     +- 在所有模块符号上设置版本信息
	|     +- 内核模块加载器
	+- ..

每个条目都有自己的依赖关系。这些依赖关系用于确定条目的可见性。任何子条目仅在其父条目可见时才可见。
菜单条目
------------

大多数条目定义一个配置选项；其他条目则帮助组织它们。单个配置选项的定义如下：

  config MODVERSIONS
	bool "在所有模块符号上设置版本信息"
	depends on MODULES
	help
	  通常，每当您切换到新内核时，模块都需要重新编译。..
每行都以关键字开头，并可以跟随多个参数。“config”开始一个新的配置条目。随后的行定义了此配置选项的属性。属性可以是配置选项的类型、输入提示、依赖关系、帮助文本和默认值。可以用相同名称多次定义一个配置选项，但每次定义只能有一个输入提示，且类型不能冲突。
菜单属性
--------------

一个菜单条目可以有多个属性。并非所有属性都适用于所有地方（参见语法）。

- 类型定义：“bool”/“tristate”/“string”/“hex”/“int”

  每个配置选项必须有一个类型。只有两种基本类型：tristate 和 string；其他类型基于这两种类型。类型定义可选地接受一个输入提示，因此这两个示例等效：

	bool "网络支持"

  和：

	bool
	prompt "网络支持"

- 输入提示：“prompt”<prompt> ["if" <expr>]

  每个菜单条目最多可以有一个提示，用于显示给用户。可选地，可以使用“if”添加仅针对此提示的依赖关系
- 默认值：“default”<expr> ["if" <expr>]

  一个配置选项可以有任意数量的默认值。如果多个默认值可见，则只激活第一个定义的默认值
默认值不限于其定义所在的菜单条目。这意味着默认值可以在其他地方定义或被更早的定义覆盖
只有当用户未通过输入提示设置其他值时，默认值才会分配给配置符号。如果输入提示可见，默认值将呈现给用户并可以由他覆盖
可选地，可以使用“if”添加仅针对此默认值的依赖关系
默认值故意设置为'n'，以避免增加构建的负担。除少数例外情况外，新的配置选项不应更改此默认值。目的是让“make oldconfig”在每次发布时尽可能少地向配置中添加内容。

注释：
需要设置“默认y/m”的情况包括：

a) 对于以前总是被构建的内容，新增的Kconfig选项应设置为“默认y”。

b) 新增的用于隐藏/显示其他Kconfig选项（但不生成任何代码）的门控Kconfig选项，应设置为“默认y”，以便用户能够看到这些其他选项。

c) 对于设置为“默认n”的驱动程序中的子驱动行为或类似选项。这允许提供合理的默认值。

d) 大家普遍期望的硬件或基础设施，如CONFIG_NET或CONFIG_BLOCK。这种情况很少见。
- 类型定义 + 默认值示例：

	"def_bool"/"def_tristate" <expr> ["if" <expr>]

  这是一种类型定义加上值的简写表示法。
可选地，可以通过"if"添加此默认值的依赖项。
- 依赖项： "depends on" <expr>

  这定义了此菜单项的依赖项。如果定义了多个依赖项，则它们通过'&&'连接。这些依赖项应用于此菜单项内的所有其他选项（这些选项也接受"if"表达式），因此以下两个示例等效：

	bool "foo" if BAR
	default y if BAR

  和：

	depends on BAR
	bool "foo"
	default y

- 反向依赖项： "select" <symbol> ["if" <expr>]

  正常依赖项会减少符号的上限（参见下面），而反向依赖项可用于强制另一个符号的下限。当前菜单符号的值用作<symbol>可以设置的最小值。如果<symbol>被多次选择，则下限设置为最大的选择值。
反向依赖项只能与布尔或三态符号一起使用。
注释：
select 应谨慎使用。select 会强制一个符号的值而不检查其依赖项。
通过滥用 `select`，你甚至可以在 `FOO` 依赖于未设置的 `BAR` 的情况下选择符号 `FOO`。
通常，只将 `select` 用于不可见的符号（没有任何提示）以及没有依赖关系的符号。
这将限制其用途，但另一方面可以避免非法配置的出现。
如果 `select` <symbol> 后跟 `if` <expr>，<symbol> 将由当前菜单符号值和 <expr> 的逻辑与来选择。这意味着，由于存在 `if` <expr>，下限可能会降低。这种行为可能看起来很奇怪，但我们依赖于它。（这种行为的未来尚未决定。）

- 弱逆向依赖：`imply` <symbol> ["if" <expr>]

  这类似于 `select`，因为它对另一个符号施加了一个下限，不同之处在于“暗示”的符号值仍可从直接依赖或可见提示中设置为 `n`。
以以下示例为例：

    config FOO
	tristate "foo"
	imply BAZ

    config BAZ
	tristate "baz"
	depends on BAR

  以下值是可能的：

	===		===		=============	==============
	FOO		BAR		BAZ 的默认值	BAZ 的选择
	===		===		=============	==============
	n		y		n		N/m/y
	m		y		m		M/y/n
	y		y		y		Y/m/n
	n		m		n		N/m
	m		m		m		M/n
	y		m		m		M/n
	y		n		*		N
	===		===		=============	==============

  这在多个驱动程序想要表明它们能够接入一个次级子系统时很有用，同时允许用户在不取消这些驱动程序的情况下配置该子系统。
注意：如果 FOO=y 和 BAZ=m 的组合导致链接错误，你可以使用 IS_REACHABLE() 来保护函数调用：

	foo_init()
	{
		if (IS_REACHABLE(CONFIG_BAZ))
			baz_register(&foo);
		..
	}

  注意：如果 BAZ 提供的功能对于 FOO 来说非常重要，FOO 应该不仅暗示 BAZ，还应该暗示其依赖项 BAR：

    config FOO
	tristate "foo"
	imply BAR
	imply BAZ

  注意：如果 `imply` <symbol> 后跟 `if` <expr>，<symbol> 的默认值将是当前菜单符号值和 <expr> 的逻辑与。（这种行为的未来尚未决定。）

- 限制菜单显示：`visible if` <expr>

  此属性仅适用于菜单块，如果条件为假，则不会向用户显示该菜单块（其中包含的符号仍然可以通过其他符号选择）。它类似于单个菜单条目的条件性 “prompt” 属性。`visible` 的默认值为真。
- 数值范围：`range` <symbol> <symbol> ["if" <expr>]

  这允许限制 int 和 hex 符号可能输入值的范围。用户只能输入一个大于或等于第一个符号且小于或等于第二个符号的值。
- 帮助文本：`help`

  这定义了一个帮助文本。帮助文本的结束由缩进级别确定，这意味着它在第一行比帮助文本第一行缩进更少的地方结束。
### 模块属性： "modules"
这声明了要作为MODULES符号使用的符号，该符号启用了所有配置符号的第三种模块状态。
最多只能有一个符号设置 "modules" 选项。

### 菜单依赖
-----------------

依赖定义了一个菜单项的可见性，并且还可以减少三态符号的输入范围。表达式中使用的三态逻辑比普通的布尔逻辑多一个状态来表示模块状态。依赖表达式的语法如下：

```
<expr> ::= <symbol>                           (1)
         <symbol> '=' <symbol>                (2)
         <symbol> '!=' <symbol>               (3)
         <symbol1> '<' <symbol2>              (4)
         <symbol1> '>' <symbol2>              (4)
         <symbol1> '<=' <symbol2>             (4)
         <symbol1> '>=' <symbol2>             (4)
         '(' <expr> ')'                       (5)
         '!' <expr>                           (6)
         <expr> '&&' <expr>                   (7)
         <expr> '||' <expr>                   (8)
```

表达式的优先级从高到低列出。

1. 将符号转换为表达式。布尔和三态符号直接转换为相应的表达式值。其他所有类型的符号结果为 'n'。
2. 如果两个符号的值相等，则返回 'y'，否则返回 'n'。
3. 如果两个符号的值相等，则返回 'n'，否则返回 'y'。
4. 如果 <symbol1> 的值分别小于、大于、小于等于或大于等于 <symbol2> 的值，则返回 'y'，否则返回 'n'。
5. 返回表达式的值。用于覆盖优先级。
6. 返回 (2-/expr/) 的结果。
7. 返回 min(/expr/, /expr/) 的结果。
(8) 返回 `max(/expr/, /expr/)` 的结果
表达式的值可以是 'n'、'm' 或 'y'（或分别为 0、1、2 用于计算）。当一个菜单项的表达式计算结果为 'm' 或 'y' 时，该菜单项可见。
符号有两种类型：常量符号和非常量符号。
非常量符号是最常见的一种，并通过 'config' 语句定义。非常量符号完全由字母数字字符或下划线组成。
常量符号仅作为表达式的一部分。常量符号始终被单引号或双引号包围。在引号内，允许任何其他字符，并且可以使用反斜杠 '\' 转义引号。

### 菜单结构

菜单项在树中的位置可以通过两种方式确定。首先，可以显式指定：

```
menu "网络设备支持"
   depends on NET

  config NETDEVICES
   ...
endmenu
```

在 "menu" ... "endmenu" 块内的所有条目将成为 "网络设备支持" 的子菜单。所有子项将继承来自菜单项的依赖关系，例如这意味着依赖关系 "NET" 将添加到配置选项 NETDEVICES 的依赖列表中。

另一种生成菜单结构的方法是通过分析依赖关系。如果一个菜单项以某种方式依赖于前一个条目，则可以将其作为其子菜单。首先，前一个（父级）符号必须是依赖列表的一部分，然后必须满足以下两个条件之一：

- 如果父项设置为 'n'，则子项必须变为不可见；
- 子项只有在父项可见的情况下才可见。

```
config MODULES
bool "启用模块支持"

config MODVERSIONS
bool "为所有模块符号设置版本信息"
depends on MODULES

comment "模块支持已禁用"
depends on !MODULES
```

MODVERSIONS 直接依赖于 MODULES，这意味着它只有在 MODULES 不等于 'n' 时才可见。另一方面，注释仅在 MODULES 设置为 'n' 时才可见。

### Kconfig 语法

配置文件描述了一系列菜单项，其中每一行都以关键字开头（除了帮助文本）。以下是结束菜单项的关键字：

- config
- menuconfig
- choice/endchoice
- comment
- menu/endmenu
- if/endif
- source

前五个也开始了菜单项的定义。

`config`：
```
"config" <symbol>
<config options>
```

这定义了一个配置符号 `<symbol>` 并接受上述任何属性作为选项。
### `menuconfig`:

```
"menuconfig" <symbol>
<config options>
```

这与简单的配置项类似，但它还为前端提供了一个提示，即所有子选项应作为一个单独的选项列表显示。为了确保所有子选项确实会出现在 `menuconfig` 入口下而不是外部，`<config options>` 列表中的每一项都必须依赖于 `menuconfig` 符号。实际上，这可以通过以下两种结构之一来实现：

1.
```
menuconfig M
if M
    config C1
    config C2
endif
```

2.
```
menuconfig M
config C1
    depends on M
config C2
    depends on M
```

在下面的例子 (3) 和 (4) 中，C1 和 C2 仍然具有 M 依赖项，但由于 C0 不依赖于 M，它们将不再出现在 `menuconfig M` 下：

3.
```
menuconfig M
    config C0
if M
    config C1
    config C2
endif
```

4.
```
menuconfig M
config C0
config C1
    depends on M
config C2
    depends on M
```

### 选择（choices）：

```
"choice"
<choice options>
<choice block>
"endchoice"
```

这定义了一个选择组，并接受上述任何属性作为选项。选择只能是布尔类型或三态类型。如果未指定选择类型，则其类型将由该组中的第一个选择元素的类型决定，或者如果没有选择元素指定类型，则保持未知状态。
虽然布尔选择只允许选择一个配置项，但三态选择还允许设置任意数量的配置项为 'm'。这可以用于存在多个硬件驱动程序的情况，其中只有一个驱动程序可以编译/加载到内核中，但所有驱动程序都可以作为模块编译。

### 注释（comment）：

```
"comment" <prompt>
<comment options>
```

这定义了一个注释，在配置过程中向用户显示，并且也输出到文件中。唯一的可能选项是依赖项。

### 菜单（menu）：

```
"menu" <prompt>
<menu options>
<menu block>
"endmenu"
```

这定义了一个菜单块，有关更多信息，请参阅上面的“菜单结构”。唯一的可能选项是依赖项和 "visible" 属性。

### 条件（if）：

```
"if" <expr>
<if block>
"endif"
```

这定义了一个条件块。依赖表达式 `<expr>` 将附加到所有封闭的菜单项上。

### 引入（source）：

```
"source" <prompt>
```

这读取指定的配置文件。此文件始终被解析。

### 主菜单（mainmenu）：

```
"mainmenu" <prompt>
```

这设置了配置程序的标题栏（如果配置程序选择使用的话）。它应该放置在配置文件的顶部，在其他任何语句之前。

### `#` Kconfig 源文件注释：

源文件中的未引用 `#` 字符表示源文件注释的开始。该行的其余部分是注释。

### Kconfig 提示：

这是一个 Kconfig 提示集合，其中大部分提示在初次接触时并不明显，并且在许多 Kconfig 文件中已成为惯用法。
添加通用特性并使使用方式可配置

这是一种常见的做法，即实现某些架构相关但并非所有架构都需要的功能/特性。
推荐的做法是使用一个名为 `HAVE_*` 的配置变量，该变量定义在一个通用的 Kconfig 文件中，并由相关的架构选择。
一个例子是通用 IOMAP 功能。
我们会在 `lib/Kconfig` 中看到如下内容：

  # 通用 IOMAP 用于 ...
  config HAVE_GENERIC_IOMAP

  config GENERIC_IOMAP
    depends on HAVE_GENERIC_IOMAP && FOO

在 `lib/Makefile` 中我们会看到：

  obj-$(CONFIG_GENERIC_IOMAP) += iomap.o

对于使用通用 IOMAP 功能的每个架构，我们会看到：

  config X86
    select ..
    select HAVE_GENERIC_IOMAP
    select ..

注意：我们使用现有的配置选项，并避免创建新的配置变量来选择 `HAVE_GENERIC_IOMAP`。
注意：内部配置变量 `HAVE_GENERIC_IOMAP` 的使用是为了克服 `select` 命令的一个限制，即无论依赖关系如何都会将配置选项强制为 'y'。
我们将依赖关系移到了符号 `GENERIC_IOMAP` 上，从而避免了 `select` 强制符号等于 'y' 的情况。

添加需要编译器支持的特性

有许多特性需要编译器的支持。描述对编译器功能依赖关系的推荐方法是使用 "depends on" 后跟一个测试宏：

  config STACKPROTECTOR
    bool "堆栈保护缓冲区溢出检测"
    depends on $(cc-option,-fstack-protector)
    ..
如果你需要将编译器功能暴露给 Makefile 和/或 C 源文件，推荐使用 `CC_HAS_` 作为配置选项的前缀：

  config CC_HAS_FOO
	def_bool $(success,$(srctree)/scripts/cc-check-foo.sh $(CC))

仅构建为模块
~~~~~~~~~~~~~~
为了将组件的构建限制为仅模块，可以在其配置符号上添加 "depends on m"。例如：

  config FOO
	depends on BAR && m

这将 FOO 限制为模块（=m）或禁用（=n）

编译测试
~~~~~~~~~~~~~~
如果一个配置符号有依赖项，但即使该依赖项未满足，受该配置符号控制的代码仍然可以编译，建议通过在依赖项中增加 "|| COMPILE_TEST" 子句来提高构建覆盖率。这对更奇特硬件的驱动程序特别有用，因为它允许持续集成系统在更常见的系统上进行编译测试，并由此检测错误。
需要注意的是，编译测试的代码在依赖项未满足的系统上运行时不应崩溃。

架构和平台依赖
~~~~~~~~~~~~~~~~~~~~~~~~
由于存在存根（stubs），大多数驱动程序现在可以在大多数架构上编译。然而，这并不意味着所有驱动程序都有必要在所有地方可用，因为实际硬件可能只存在于特定架构和平台上。对于片上系统（SoC）中的知识产权核心（IP cores）来说尤其如此，它们可能仅限于特定供应商或 SoC 系列。
为了避免向用户询问无法在其目标系统上使用的驱动程序，并且如果合理的话，控制驱动程序编译的配置符号应包含适当的依赖项，以将符号的可见性限制在（包含）驱动程序可以使用的平台之上。这种依赖项可以是架构（如 ARM）或平台（如 ARCH_OMAP4）的依赖项。这不仅简化了发行版配置所有者的工作，也简化了每个配置内核的开发人员或用户的工作。
可以通过结合上述编译测试规则来放宽此类依赖项，如下所示：

  config FOO
	bool "对 foo 硬件的支持"
	depends on ARCH_FOO_VENDOR || COMPILE_TEST

可选依赖
~~~~~~~~~~~~~~
一些驱动程序可以选择性地使用来自其他模块的功能，或者在禁用该模块的情况下干净地构建，但在尝试从内置驱动程序使用该可加载模块时会导致链接失败。
在 Kconfig 逻辑中表达这种可选依赖关系最常见的方式是使用稍微反直觉的方法：

  config FOO
	tristate "对 foo 硬件的支持"
	depends on BAR || !BAR

这意味着要么有依赖项 BAR，禁止 FOO=y 与 BAR=m 的组合，要么完全禁用 BAR。
如果有多个具有相同依赖项的驱动程序，则可以使用辅助符号，例如：

  config FOO
	tristate "对 foo 硬件的支持"
	depends on BAR_OPTIONAL

  config BAR_OPTIONAL
	def_tristate BAR || !BAR

Kconfig 递归依赖限制
~~~~~~~~~~~~~~~~~~~~~~~~
如果你遇到了 Kconfig 错误：“检测到递归依赖”，那么你遇到了 Kconfig 中的递归依赖问题。递归依赖可以总结为循环依赖。Kconfig 工具需要确保 Kconfig 文件符合指定的配置要求。为此，Kconfig 必须确定所有 Kconfig 符号的所有可能值，目前如果两个或更多 Kconfig 符号之间存在循环关系则无法实现这一点。更多详细信息请参阅下面的“简单 Kconfig 递归问题”小节。Kconfig 不解决递归依赖；这给 Kconfig 文件编写者带来了一些影响。
我们首先解释为什么会出现此问题，然后提供一个技术限制示例，这给 Kconfig 开发者带来了挑战。热衷于尝试解决此限制的开发者应该阅读下面的小节。
简单的 Kconfig 递归问题
~~~~~~~~~~~~~~~~~~~~~~~~
阅读：Documentation/kbuild/Kconfig.recursion-issue-01

测试：
```
make KBUILD_KCONFIG=Documentation/kbuild/Kconfig.recursion-issue-01 allnoconfig
```

累积的 Kconfig 递归问题
~~~~~~~~~~~~~~~~~~~~~~~~
阅读：Documentation/kbuild/Kconfig.recursion-issue-02

测试：
```
make KBUILD_KCONFIG=Documentation/kbuild/Kconfig.recursion-issue-02 allnoconfig
```

解决 Kconfig 递归问题的实际方案
~~~~~~~~~~~~~~~~~~~~~~~~
遇到递归 Kconfig 问题的开发者有两种选择。我们在下面记录这些选择，并提供通过不同解决方案解决的历史问题列表。
a) 删除任何多余的 "select FOO" 或 "depends on FOO"。
b) 匹配依赖语义：

   b1) 将所有 "select FOO" 替换为 "depends on FOO"，或者，
   
   b2) 将所有 "depends on FOO" 替换为 "select FOO"。

对 a) 的解决方案可以通过示例 Kconfig 文件 `Documentation/kbuild/Kconfig.recursion-issue-01` 进行测试。通过移除 `CORE_BELL_A_ADVANCED` 中的 "select CORE"（因为该依赖关系是隐含的，因为 `CORE_BELL_A` 已经依赖于 `CORE`）。有时可能无法删除某些依赖条件，在这种情况下可以使用 b) 的方法。
对于 b) 的两种不同解决方案可以在示例 Kconfig 文件 `Documentation/kbuild/Kconfig.recursion-issue-02` 中进行测试。
以下是此前解决这类递归问题的一些示例；所有错误似乎都涉及一个或多个 "select" 语句和一个或多个 "depends on" 语句：
============    ===================================
提交记录         解决方案
============    ===================================
06b718c01208    select A -> depends on A
c22eacfe82f9    depends on A -> depends on B
6a91e854442c    select A -> depends on A
118c565a8f2e    select A -> select B
f004e5594705    select A -> depends on A
c7861f37b4c6    depends on A -> (null)
80c69915e5fb    select A -> (null)              (1)
c2218e26c0d0    select A -> depends on A        (1)
d6ae99d04e1c    select A -> depends on A
95ca19cf8cbf    select A -> depends on A
8f057d7bca54    depends on A -> (null)
8f057d7bca54    depends on A -> select A
a0701f04846e    select A -> depends on A
0c8b92f7f259    depends on A -> (null)
e4e9e0540928    select A -> depends on A        (2)
7453ea886e87    depends on A -> (null)          (1)
7b1fff7e4fdf    select A -> depends on A
86c747d2a4f0    select A -> depends on A
d9f9ab51e55e    select A -> depends on A
0c51a4d8abd6    depends on A -> select A        (3)
e98062ed6dc4    select A -> depends on A        (3)
91e5d284a7f1    select A -> (null)
============    ===================================

(1) 部分（或没有）引用错误
(2) 这似乎是该修复的核心内容
(3) 相同的错误

未来的 Kconfig 工作
~~~~~~~~~~~~~~~~~~~

欢迎在两个方面对 Kconfig 进行改进：一是明确其语义，二是评估使用完整的 SAT 求解器。使用完整的 SAT 求解器可能是可取的，因为它可以实现更复杂的依赖映射和/或查询。例如，SAT 求解器的一个可能用途是处理当前已知的递归依赖问题。虽然尚不清楚这是否能解决这些问题，但这种评估是有必要的。如果支持完整的 SAT 求解器过于复杂或不能解决递归依赖问题，则 Kconfig 应至少具有清晰且明确定义的语义，并且记录递归依赖相关的限制或要求。
这两个方面的进一步工作都是受欢迎的。我们将在接下来的两个子节中详细讨论这两点。
Kconfig 的语义
~~~~~~~~~~~~~~~~~~~~

Kconfig 的使用范围很广，Linux 现在只是 Kconfig 的用户之一：一项研究已经完成了对 12 个项目中 Kconfig 使用情况的广泛分析 [0]_。
尽管其广泛应用，而且本文档在记录基本 Kconfig 语法方面做得不错，但更精确地定义 Kconfig 的语义是值得欢迎的。一个项目通过使用 xconfig 配置器推断了 Kconfig 的语义 [1]_。需要确认推断出的语义是否符合我们预期的 Kconfig 设计目标。
另一个项目正式定义了Kconfig语言核心子集的语义[10]。拥有明确定义的语义对于工具来说非常有用，例如用于实际依赖关系评估的情况。其中一个例子是将Kconfig推断出的语义以布尔抽象的形式表达，从而将Kconfig逻辑转换为布尔公式，并运行SAT求解器来查找死代码/特性（始终处于非激活状态）。使用这种方法在Linux中发现了114个死特性[1]（第8节：有效性威胁）。基于[10]中的语义，kismet工具能够发现反向依赖关系的滥用情况，并已导致数十次对Linux Kconfig文件的修复提交[11]。确认这一点可能会很有用，因为Kconfig作为领先的工业变体建模语言之一[1] [2]。对其研究有助于评估这类语言的实际用途，因为它们之前仅停留在理论层面，实际需求尚未被充分理解。然而，目前只有逆向工程技术被用来从诸如Kconfig这样的变体建模语言中推断语义[3]。

完整的Kconfig SAT求解器
~~~~~~~~~~~~~~~~~~~~~~~~

尽管如前所述，SAT求解器[4]尚未直接应用于Kconfig，但确实有工作已经完成，即将Kconfig推断出的语义以布尔抽象的形式表达，从而将Kconfig逻辑转换为布尔公式并运行SAT求解器[5]。另一个相关的项目是CADOS[6]（原名为VAMOS[7]），以及其中的主要工具undertaker[8]，最初由[9]引入。undertaker的基本概念是从Kconfig中提取变体模型，并将其与从CPP #ifdefs和构建规则中提取的命题公式一起输入到SAT求解器中，以便发现死代码、死文件和死符号。如果在Kconfig上使用SAT求解器是可行的，那么一种方法可能是重新利用这些努力。现有项目的导师们对此有足够的兴趣，不仅可以帮助指导如何将这项工作集成到上游，还可以长期维护它。感兴趣的开发者可以访问：

https://kernelnewbies.org/KernelProjects/kconfig-sat

.. [4] https://www.cs.cornell.edu/~sabhar/chapters/SATSolvers-KR-Handbook.pdf
.. [5] https://gsd.uwaterloo.ca/sites/default/files/vm-2013-berger.pdf
.. [6] https://cados.cs.fau.de
.. [7] https://vamos.cs.fau.de
.. [8] https://undertaker.cs.fau.de
.. [9] https://www4.cs.fau.de/Publications/2011/tartler_11_eurosys.pdf
.. [10] https://paulgazzillo.com/papers/esecfse21.pdf
.. [11] https://github.com/paulgazz/kmax
