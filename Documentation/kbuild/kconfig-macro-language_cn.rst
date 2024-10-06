======================
Kconfig 宏语言
======================

概念
---

基本思想受到了 Make 的启发。当我们查看 Make 时，会注意到它实际上包含两种语言。一种语言描述了由目标和先决条件组成的依赖图。另一种是用于执行文本替换的宏语言。
这两种语言阶段有明显的区分。例如，你可以像下面这样编写一个 Makefile：

    APP := foo
    SRC := foo.c
    CC := gcc

    $(APP): $(SRC)
            $(CC) -o $(APP) $(SRC)

宏语言将变量引用替换为其展开形式，并处理得好像源文件输入如下所示：

    foo: foo.c
            gcc -o foo foo.c

然后，Make 分析依赖图并确定需要更新的目标。

Kconfig 中的想法与此非常相似——可以像这样描述一个 Kconfig 文件：

    CC := gcc

    config CC_HAS_FOO
            def_bool $(shell, $(srctree)/scripts/gcc-check-foo.sh $(CC))

Kconfig 中的宏语言将源文件处理成以下中间形式：

    config CC_HAS_FOO
            def_bool y

然后，Kconfig 进入评估阶段来解决符号间的依赖关系，具体解释见 kconfig-language.rst。

变量
----

与 Make 类似，Kconfig 中的变量作为宏变量工作。宏变量在原地展开以生成文本字符串，该字符串可能进一步展开。要获取变量的值，需要在变量名周围加上 $( )。即使对于单字母变量名，括号也是必需的；$X 是语法错误。${CC} 形式的花括号形式也不支持。

有两种类型的变量：简单展开变量和递归展开变量。
简单展开变量使用 := 赋值操作符定义。其右侧在从 Kconfig 文件读取行时立即展开。
递归展开变量使用 = 赋值操作符定义。其右侧只是作为变量的值存储，不进行任何展开。相反，在使用变量时才进行展开。
还有一种赋值操作符：+= 用于向变量追加文本。如果左侧最初被定义为简单变量，则 += 的右侧立即展开。否则，其评估被推迟。
变量引用可以带参数，形式如下：

  $(name,arg1,arg2,arg3)

可以将带参数的引用视为函数。（更准确地说，是“用户定义的函数”，与下面列出的“内置函数”相对）

希望这个翻译对你有帮助！如果有任何问题或需要进一步的修改，请告诉我。
有用的函数在使用时必须进行展开，因为相同的函数在传递不同的参数时会展开为不同的结果。因此，用户定义的函数是通过 `=` 赋值运算符来定义的。函数体定义中引用的参数使用 `$`(1)，`$`(2) 等表示。

实际上，递归展开的变量和用户定义的函数在内部是一样的。（换句话说，“变量”就是“零参数的函数”。）当我们广义地说“变量”时，它包括“用户定义的函数”。

内置函数
---------

与 Make 类似，Kconfig 提供了多个内置函数。每个函数需要特定数量的参数。

在 Make 中，每个内置函数至少需要一个参数。而在 Kconfig 中，允许内置函数没有参数，例如 `$(filename)` 和 `$(lineno)`。你可以将这些看作是“内置变量”，但归根结底这只是命名的问题。在这里我们称之为“内置函数”，以指代原生支持的功能。

目前 Kconfig 支持以下内置函数：

- `$(shell, command)`

  “shell” 函数接受一个参数，该参数会被展开并传递给子 shell 进行执行。命令的标准输出随后被读取并作为函数的返回值。输出中的每个换行符会被替换为空格，并且任何末尾的换行符都会被删除。标准错误不会返回，也不会返回任何程序退出状态。

- `$(info, text)`

  “info” 函数接受一个参数并将其打印到标准输出。该函数评估后返回一个空字符串。

- `$(warning-if, condition, text)`

  “warning-if” 函数接受两个参数。如果条件部分为 “y”，则文本部分会被发送到标准错误输出。文本前会加上当前 Kconfig 文件的名称和当前行号。

- `$(error-if, condition, text)`

  “error-if” 函数类似于 “warning-if”，但如果条件部分为 “y”，则会立即终止解析。
- $(filename)

  `filename` 不接受参数，而 $(filename) 展开为当前解析的文件名。
- $(lineno)

  `lineno` 不接受参数，而 $(lineno) 展开为当前解析的行号。

Make 与 Kconfig
--------------

Kconfig 采用了类似于 Make 的宏语言，但函数调用语法略有不同。在 Make 中，函数调用如下所示：

  $(func-name arg1,arg2,arg3)

函数名和第一个参数之间至少有一个空格。然后，第一个参数前导的空格将被修剪，而其他参数中的空格则保留。如果要在第一个参数中包含空格，需要使用某种技巧。例如，如果你想让 "info" 函数打印 "  hello"，可以这样写：

  empty :=
  space := $(empty) $(empty)
  $(info $(space)$(space)hello)

Kconfig 只使用逗号作为分隔符，并且在函数调用中保留所有空格。有些人喜欢在每个逗号分隔符后加一个空格：

  $(func-name, arg1, arg2, arg3)

在这种情况下，"func-name" 将接收到 " arg1"、" arg2" 和 " arg3"。根据函数的不同，前导空格的存在可能会产生影响。这一点在 Make 中同样适用——例如，$(subst .c, .o, $(sources)) 是一个典型的错误；它将 ".c" 替换成了 " .o"。

在 Make 中，用户定义的函数通过内置函数 `call` 来引用，如下所示：

    $(call my-func,arg1,arg2,arg3)

Kconfig 调用用户定义的函数和内置函数的方式相同。省略 `call` 使得语法更简洁。

在 Make 中，某些函数将逗号视为字面量而不是参数分隔符。例如，$(shell echo hello, world) 运行命令 "echo hello, world"。同样，$(info hello, world) 将 "hello, world" 打印到标准输出。可以说这是一种有用的不一致性。

在 Kconfig 中，为了简化实现并保持语法一致性，在 $( ) 上下文中出现的逗号总是分隔符。这意味着：

  $(shell, echo hello, world)

是一个错误，因为它传递了两个参数，而 `shell` 函数只接受一个参数。要传递包含逗号的参数，可以使用以下技巧：

  comma := ,
  $(shell, echo hello$(comma) world)

注意事项
-------

变量（或函数）不能跨令牌展开。因此，你不能将变量用作多令牌表达式的简写。
以下代码可以正常工作：

    RANGE_MIN := 1
    RANGE_MAX := 3

    config FOO
            int "foo"
            range $(RANGE_MIN) $(RANGE_MAX)

但是，以下代码无法正常工作：

    RANGES := 1 3

    config FOO
            int "foo"
            range $(RANGES)

在 Kconfig 中，变量不能扩展为任何关键字。以下代码也无法正常工作：

    MY_TYPE := tristate

    config FOO
            $(MY_TYPE) "foo"
            default y

显然从设计上来说，$(shell command) 在文本替换阶段进行展开。你不能将符号传递给 'shell' 函数。以下代码无法按预期工作：

    config ENDIAN_FLAG
            string
            default "-mbig-endian" if CPU_BIG_ENDIAN
            default "-mlittle-endian" if CPU_LITTLE_ENDIAN

    config CC_HAS_ENDIAN_FLAG
            def_bool $(shell $(srctree)/scripts/gcc-check-flag ENDIAN_FLAG)

相反，你可以按照以下方式处理，使得任何函数调用都能静态展开：

    config CC_HAS_ENDIAN_FLAG
            bool
            default $(shell $(srctree)/scripts/gcc-check-flag -mbig-endian) if CPU_BIG_ENDIAN
            default $(shell $(srctree)/scripts/gcc-check-flag -mlittle-endian) if CPU_LITTLE_ENDIAN
