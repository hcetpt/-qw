Linux 内核编程风格
=========================

这是一个简短的文档，描述了 Linux 内核首选的编程风格。编程风格是非常个人化的，我不会**强迫**我的观点给任何人，但对于任何我需要维护的代码，我都遵循这种风格，并且我也更希望大多数其他代码也采用这种风格。请至少考虑这里提出的各点。

首先，我建议打印一份 GNU 编程标准，然后**不要读它**。把它烧掉，这会是一个很好的象征性举动。
无论如何，我们开始吧：

1) 缩进
--------------

Tab 键代表 8 个字符，因此缩进也是 8 个字符。
有些异端运动试图将缩进设置为 4（甚至 2！）个字符深，这就像尝试定义圆周率的值为 3。
理由：缩进背后的理念是清楚地定义控制块的起始和结束位置。特别是当你连续盯着屏幕工作 20 小时后，你会发现如果使用较大的缩进，更容易理解缩进的工作方式。
现在，有些人会声称 8 字符的缩进会使代码向右移动得太远，使得在 80 字符的终端屏幕上难以阅读。对于这个问题的回答是，如果你需要超过 3 层的缩进，那么你的程序很可能已经设计得不够好了，应该重新调整。
简而言之，8 字符的缩进使代码更易于阅读，并且还有一个额外的好处，即当你嵌套函数过深时会给你一个警告。
请注意这个警告。
在 switch 语句中处理多层缩进的一种优选方法是在同一列对齐 `switch` 和其下属的 `case` 标签，而不是“双重缩进”这些 `case` 标签。例如：

```c
switch (suffix) {
case 'G':
case 'g':
    mem <<= 30;
    break;
case 'M':
case 'm':
    mem <<= 20;
    break;
case 'K':
case 'k':
    mem <<= 10;
    // fallthrough
default:
    break;
}
```

除非你有东西要隐藏，否则不要在一个单行上放置多个语句：

```c
if (condition) do_this();
  do_something_everytime;
```

不要使用逗号来避免使用花括号：

```c
if (condition)
    do_this(), do_that();
```

对于多个语句，始终使用花括号：

```c
if (condition) {
    do_this();
    do_that();
}
```

也不要将多个赋值放在一行内。内核编程风格非常简单，避免使用复杂的表达式。
除了注释、文档以及 Kconfig 中之外，从不使用空格进行缩进，上述示例是故意违反规则的例子。
1) 使用合适的编辑器并且不要在线尾留有空白。
2) 拆分长行和字符串
----------------------------------

编码风格关乎可读性和可维护性，并利用常见的工具。
单行的首选长度限制是80个字符。
超过80个字符的语句应该被合理地拆分成较短的部分，
除非超过80个字符显著提高了可读性且没有隐藏信息。
子级总是比父级明显更短，并且明显向右缩进。一个非常常用的做法
是将子级对齐到函数的左括号位置。
这些相同的规则也适用于具有长参数列表的函数头部。
但是，永远不要拆分用户可见的字符串，比如`printk`消息，因为那样会破坏
通过它们进行`grep`搜索的能力。
3) 大括号与空格的放置
----------------------------

在C语言风格中总会遇到的一个问题是大括号的放置。与缩进大小不同的是，选择一种放置策略而非另一种在技术上很少有原因，但由先知克尼汉(Kernighan)和里奇(Ritchie)展示给我们的首选方式是将开括号放在行末，闭括号放在行首，如下所示：

.. code-block:: c

	if (x is true) {
		我们执行y
	}

这适用于所有非函数的语句块（如if、switch、for、while、do）。例如：

.. code-block:: c

	switch (action) {
	case KOBJ_ADD:
		return "add";
	case KOBJ_REMOVE:
		return "remove";
	case KOBJ_CHANGE:
		return "change";
	default:
		return NULL;
	}

然而，有一个特殊情况，即函数：它们的开括号位于下一行的开头，如下所示：

.. code-block:: c

	int function(int x)
	{
		函数体
	}

世界各地的异教徒声称这种不一致性是……嗯……不一致的，但是所有正统的人都知道
(a) 克尼汉和里奇是**正确的**，(b) 克尼汉和里奇是正确的。此外，函数本身就是特殊的（在C语言中你不能嵌套函数）。
请注意，闭括号单独占一行且为空，**除了**在它后面紧跟同一语句的其他部分的情况下，例如do语句中的`while`或if语句中的`else`，如下所示：

.. code-block:: c

	do {
		do循环体
	} while (条件);

以及

.. code-block:: c

	if (x == y) {
		.
} else if (x > y) {
		..
### 否则 {
    ...
}

**理由：** K&R
此外，请注意这种花括号放置方式也最大限度地减少了空行（或几乎空的行）的数量，而不会影响可读性。因此，考虑到屏幕上的新行并非可再生资源（想象一下只有25行的终端屏幕），你将有更多的空行可以用来添加注释。
对于只包含一个语句的情况不要无谓地使用花括号
.. code-block:: c

    如果 (条件)
        操作();

和

.. code-block:: c

    如果 (条件)
        执行此操作();
    否则
        执行其他操作();

如果条件语句的一个分支只包含一个语句，则不适用上述规则；在这种情况下，应在两个分支中都使用花括号：

.. code-block:: c

    如果 (条件) {
        执行此操作();
        执行其他操作();
    } 否则 {
        否则执行此操作();
    }

另外，当循环包含多于一个简单语句时，应使用花括号：

.. code-block:: c

    当 (条件) {
        如果 (测试)
            执行某些操作();
    }

### 3.1 空格
***********

Linux内核风格中空格的使用主要取决于函数与关键字的用法。大多数关键字后面要加空格。值得注意的例外是sizeof、typeof、alignof 和 __attribute__，它们看起来有点像函数（在Linux中通常与圆括号一起使用，尽管语言本身不需要这样，例如：在声明 `struct fileinfo info;` 后面可以写 `sizeof info`）
所以这些关键字后面不加空格：

如果、switch、case、for、do、while

但sizeof、typeof、alignof 或 __attribute__后面不加空格。例如，

.. code-block:: c


    s = sizeof(结构体文件);

不要在圆括号表达式内部（周围）添加空格。以下示例是**错误**的：

.. code-block:: c


    s = sizeof( 结构体文件 );

声明指针数据或返回指针类型的函数时，推荐的做法是将 `*` 放在数据名称或函数名称旁边，而不是类型名称旁边。示例：

.. code-block:: c


    char *linux_banner;
    unsigned long long memparse(char *ptr, char **retptr);
    char *match_strdup(substring_t *s);

对于大多数二元和三元运算符（如等号、加号、减号、小于号、大于号、乘号、除号、模数、按位或、按位与、按位异或、小于等于、大于等于、等于、不等于、问号、冒号），两边都要留一个空格，

但是一元运算符后面不留空格：

& * + - ~ ! sizeof typeof alignof __attribute__ defined

后缀递增和递减一元运算符之前不留空格：

++
--

前缀递增和递减一元运算符之后不留空格：

++
--

结构成员运算符`.`和`->`周围不留空格。

不要在线末尾留下空白。一些具有“智能”缩进功能的编辑器会在新行开头适当插入空白，以便你可以立即开始输入下一行代码。
然而，如果你最终没有在该处放置代码行（比如留下一个空行），某些这样的编辑器不会删除这些空白，结果就是你会得到含有尾部空白的行。
Git会警告你提交的补丁中引入了尾部空白，并可选地为你删除尾部空白；但是，如果一系列补丁中应用了此操作，这可能会导致系列中的后续补丁因上下文行发生变化而失败。

### 4) 命名
---------

C语言是一种简练的语言，你的命名约定也应遵循这一风格。
与 Modula-2 和 Pascal 程序员不同，C 程序员不会使用诸如 `ThisVariableIsATemporaryCounter` 这样的可爱变量名。一个 C 程序员会将这个变量命名为 `tmp`，这更容易书写，并且一点也不更难理解。
然而，虽然混合大小写的变量名不被推荐，但对于全局变量来说，描述性的名称是必须的。将全局函数命名为 `foo` 是一种严重的错误。
全局变量（只有在你**真的**需要它们时才使用）和全局函数都需要有描述性的名称。如果你有一个统计活动用户数量的函数，你应该将其命名为 `count_active_users()` 或类似的名称，你不应该将其命名为 `cntusr()`。
将函数类型编码到名称中（所谓的匈牙利命名法）是愚蠢的 —— 编译器本身就了解这些类型，并可以检查它们，这样做只会让程序员感到困惑。
局部变量的名称应该简短、切题。如果你有一个随机的整数循环计数器，它可能应该被称为 `i`。如果没有任何误解的可能性，将其命名为 `loop_counter` 是没有必要的。类似地，`tmp` 可以是任何用于存储临时值的变量类型。
如果你担心混淆局部变量的名称，那么你还有另一个问题，这个问题被称为“函数生长激素失衡综合症”。
请参阅第 6 章（函数）。
对于符号名称和文档，请避免引入新的 “主从”（或仅“从属”）以及“黑名单/白名单”的使用。
推荐的 “主从” 替代方案包括：
    '{主,主要} / {次,副本,从属}'
    '{发起者,请求者} / {目标,响应者}'
    '{控制器,主机} / {设备,工作者,代理}'
    '领导者 / 跟随者'
    '指挥 / 表演者'

推荐的 “黑名单/白名单” 替代方案包括：
    '拒绝列表 / 允许列表'
    '阻止列表 / 通过列表'

引入新使用的例外情况是为了维护用户空间 ABI/API，或者在更新现有（截至 2020 年）硬件或协议规范要求使用这些术语的情况下。对于新规范，在可能的情况下，应将规范中的术语转换为内核编码标准。
5) 类型定义（Typedefs）
-----------
请不要使用诸如`vps_t`这样的类型定义。
对于结构体和指针使用类型定义是一个**错误**。当你在源代码中看到

.. code-block:: c

	vps_t a;

这代表了什么？相反，如果它写为

.. code-block:: c

	struct virtual_container *a;

那么你就能清楚地知道`a`是什么。
很多人认为类型定义可以**提高可读性**。其实不然。它们只适用于以下几种情况：

(a) 完全不透明的对象（其中类型定义被积极用于**隐藏**对象的真实类型）
示例：`pte_t`等不透明对象，你只能通过正确的访问函数来操作它们。
.. note::
	不透明性和“访问函数”本身并不是好的特性。
我们之所以对像`pte_t`这样的对象使用类型定义，是因为那里确实没有任何**可移植的**可访问信息。
(b) 明确的整数类型，其中抽象有助于避免混淆它是`int`还是`long`
`u8`/`u16`/`u32`都是很好的类型定义，尽管它们更适合放在(d)类别中。
.. note::
	再次强调，这里需要有一个**理由**。如果某事物是`unsigned long`，就没有理由进行如下定义：
	
	`typedef unsigned long myflags_t;`

但是如果在某些情况下它可能是`unsigned int`，而在其他配置下可能是`unsigned long`，那么当然可以使用类型定义。
(c) 当你使用`sparse`来实际创建一个**新的**类型以进行类型检查时。

以上内容翻译自原始英文文档，并进行了适当的调整以适应中文语境。
(d) 在某些特殊情况下，与标准C99类型完全相同的新类型
尽管人们的眼睛和大脑很快就能适应像 `uint32_t` 这样的标准类型，但有些人无论如何都反对使用这些类型。
因此，在某些情况下允许使用Linux特有的 `u8/u16/u32/u64` 类型及其有符号等价类型，尽管它们与标准类型相同，但在你自己的新代码中并非强制使用。
在编辑已使用上述某种类型集的现有代码时，你应该遵循该代码中已有的选择。

(e) 可以安全地在用户空间使用的类型
在某些对用户空间可见的结构中，我们不能要求使用C99类型，也不能使用上述的 `u32` 形式。因此，在所有与用户空间共享的结构中，我们使用 `__u32` 和类似的类型。
也许还有其他情况，但基本原则应该是除非你能清楚地符合上述规则之一，否则绝不要使用类型定义。
一般来说，一个指针或包含可以合理直接访问元素的结构**绝不应该**被定义为类型定义。

6) 函数
------------

函数应该简短且精炼，只做一件事情。它们应该能在一到两个屏幕的文本中展示（众所周知，ISO/ANSI的标准屏幕大小是80x24），并且只做好那一件事情。
函数的最大长度与其复杂性和缩进级别成反比。也就是说，如果你有一个概念上简单的函数，它只是一个长（但简单）的 `case` 语句，在其中你需要为许多不同的情况做很多小事情，那么拥有一个较长的函数是可以接受的。
然而，如果你有一个复杂的函数，并且你怀疑一个
能力不足的高中一年级学生可能都无法理解这个函数是做什么的，那么你应该更加严格地遵守
这些最大限制。使用具有描述性名称的帮助函数（如果你认为性能至关重要，可以要求编译器内联它们，
并且它可能会比你做得更好）
另一个衡量函数的标准是局部变量的数量。它们不应该超过5-10个，否则说明你做错了什么。重新考虑
该函数，并将其拆分成更小的部分。人类的大脑通常能轻松记住大约7件不同的事情，超过这个数量就会
感到困惑。你知道自己很聪明，但也许你希望两周后还能理解自己的所作所为。
在源文件中，用一个空白行分隔函数。如果函数被导出，其对应的 **EXPORT** 宏应该紧跟在闭合函数大括号之后。例如：

.. code-block:: c

	int system_is_up(void)
	{
		return system_state == SYSTEM_RUNNING;
	}
	EXPORT_SYMBOL(system_is_up);

6.1) 函数原型
************************

在函数原型中，包括参数名及其数据类型
虽然这并不是C语言的要求，但在Linux中这是首选的做法，因为它是一种简单的方式，可以为读者提供有价值的信息
不要在函数声明中使用 ``extern`` 关键字，因为这样会使行变得更长，并且这不是严格必要的
编写函数原型时，请保持元素的顺序一致
例如，使用以下函数声明示例：

.. code-block:: c

	__init void * __must_check action(enum magic value, size_t size, u8 count,
				       char *fmt, ...) __printf(4, 5) __malloc;

对于函数原型，推荐的元素顺序是：

- 存储类别（下面的例子是 ``static __always_inline``，需要注意的是 ``__always_inline``
  从技术上讲是一个属性，但它被视为与 ``inline`` 类似）
- 存储类别属性（这里为 ``__init`` ——即节区声明，但也包括像 ``__cold`` 这样的属性）
- 返回类型（这里为 ``void *``）
- 返回类型属性（这里为 ``__must_check``）
- 函数名（这里为 ``action``）
- 函数参数（这里为 ``(enum magic value, size_t size, u8 count, char *fmt, ...)``
  ，注意应始终包含参数名）
- 函数参数属性（这里为 ``__printf(4, 5)``）
- 函数行为属性（这里为 ``__malloc``）

请注意，在函数 **定义**（即实际的函数体）中，编译器不允许在函数参数之后有函数参数属性。
在这种情况下，它们应该放在存储类别属性之后（例如，注意与上面的 **声明** 示例相比，
``__printf(4, 5)`` 的位置发生了变化）：

.. code-block:: c

	static __always_inline __init __printf(4, 5) void * __must_check action(enum magic value,
		size_t size, u8 count, char *fmt, ...) __malloc
	{
		..
	}

7) 函数退出的集中处理
-----------------------------------

尽管有些人认为它已经过时，但相当于 `goto` 语句的无条件跳转指令被编译器频繁使用
当函数需要从多个位置退出，并且需要执行一些通用的工作，如清理时，`goto` 语句就非常有用。如果没有
需要清理的工作，则直接返回即可
选择能够说明 `goto` 所做的工作或为什么存在 `goto` 的标签名。一个好的名字示例可能是
`out_free_buffer:` 如果 `goto` 释放了 `buffer`。
避免使用像 `GW-BASIC` 中的名称如 ``err1:`` 和 ``err2:`` 这样的标签，因为如果你需要添加或删除退出路径时必须重新编号这些标签，并且这会使得验证正确性变得非常困难。

使用 `goto` 的理由是：

- 无条件语句更容易理解和跟踪。
- 减少了嵌套。
- 避免了在修改代码时不更新各个退出点所导致的错误。
- 节省编译器优化冗余代码的工作 ;)

```c
int fun(int a)
{
    int result = 0;
    char *buffer;

    buffer = kmalloc(SIZE, GFP_KERNEL);
    if (!buffer)
        return -ENOMEM;

    if (condition1) {
        while (loop1) {
            ..
        }
        result = 1;
        goto out_free_buffer;
    }
    ..
out_free_buffer:
    kfree(buffer);
    return result;
}
```

一种常见的错误类型是“单一错误”（one err bugs），它们看起来像这样：

```c
err:
    kfree(foo->bar);
    kfree(foo);
    return ret;
```

这段代码中的问题是，在某些退出路径中 `foo` 是 `NULL`。通常修复这类问题的方法是将其拆分为两个错误标签 `err_free_bar:` 和 `err_free_foo:`：

```c
err_free_bar:
    kfree(foo->bar);
err_free_foo:
    kfree(foo);
    return ret;
```

理想情况下，你应该模拟错误来测试所有的退出路径。

### 8) 注释

注释是有益的，但也要注意不要过度注释。永远不要试图通过注释来解释你的代码是如何工作的：最好是编写易于理解的代码，而解释糟糕的代码是浪费时间。
一般来说，你希望你的注释告诉人们你的代码做了什么，而不是如何做的。
同时，尽量避免在函数体内放置注释：如果一个函数复杂到你需要单独注释其中的部分，则可能需要回到第 6 章重新考虑一下。你可以写一些小注释来指出或者警告某些特别聪明（或丑陋）的地方，但要避免过多的注释。相反，把注释放在函数头部，告诉人们这个函数做什么，以及为什么这样做。

当注释内核API函数时，请使用 kernel-doc 格式。
详情请参考位于 :ref:`Documentation/doc-guide/ <doc_guide>` 和 `scripts/kernel-doc` 中的文件。

对于长（多行）注释，推荐的风格如下：

```c
/*
 * 这是 Linux 内核源代码中多行注释的首选风格
 * ...
 */
```
>* 请始终如一地使用它
>* 描述：左侧由星号构成的一列，开头和结尾几乎为空的行

对于 `net/` 和 `drivers/net/` 目录下的文件，较长（多行）注释的首选风格略有不同：
```c
/* 对于位于 net/ 和 drivers/net 目录下的文件，
 * 其推荐的注释风格看起来像这样
 *
 * 它与普遍推荐的注释风格几乎相同，
 * 但是没有最初的几乎空白的行
 */
```

注释数据同样非常重要，无论是基本类型还是派生类型。为此，请每行只声明一个数据项（不要用逗号分隔多个数据声明）。这样就为你留出了空间，在每一项旁边添加一个小注释，解释其用途。

9) 你把事情搞砸了
---------------------------

没关系，我们都会犯这样的错误。可能你的长期 Unix 使用者助手已经告诉你 `GNU emacs` 可以自动帮你格式化 C 源代码，并且你也注意到了确实如此，但它的默认设置却不够理想（实际上，它们比随机打字还要糟糕——无数只猴子在 `GNU emacs` 上打字也无法写出一个好的程序）。
因此，你可以选择放弃 `GNU emacs`，或者更改设置使其更合理。为了实现后者，你可以在 `.emacs` 文件中加入以下内容：

```elisp
(defun c-lineup-arglist-tabs-only (ignored)
  "通过制表符而不是空格对齐参数列表"
  (let* ((anchor (c-langelem-pos c-syntactic-element))
         (column (c-langelem-2nd-pos c-syntactic-element))
         (offset (- (1+ column) anchor))
         (steps (floor offset c-basic-offset)))
    (* (max steps 1)
       c-basic-offset)))

(dir-locals-set-class-variables
 'linux-kernel
 '((c-mode . (
          (c-basic-offset . 8)
          (c-label-minimum-indentation . 0)
          (c-offsets-alist . (
                  (arglist-close         . c-lineup-arglist-tabs-only)
                  (arglist-cont-nonempty
(c-lineup-gcc-asm-reg c-lineup-arglist-tabs-only))
                  (arglist-intro         . +)
                  (brace-list-intro      . +)
                  (c                     . c-lineup-C-comments)
                  (case-label            . 0)
                  (comment-intro         . c-lineup-comment)
                  (cpp-define-intro      . +)
                  (cpp-macro             . -1000)
                  (cpp-macro-cont        . +)
                  (defun-block-intro     . +)
                  (else-clause           . 0)
                  (func-decl-cont        . +)
                  (inclass               . +)
                  (inher-cont            . c-lineup-multi-inher)
                  (knr-argdecl-intro     . 0)
                  (label                 . -1000)
                  (statement             . 0)
                  (statement-block-intro . +)
                  (statement-case-intro  . +)
                  (statement-cont        . +)
                  (substatement          . +)
                  ))
          (indent-tabs-mode . t)
          (show-trailing-whitespace . t)
          ))))

(dir-locals-set-directory-class
 (expand-file-name "~/src/linux-trees")
 'linux-kernel)
```

这将使 `emacs` 在处理 `~/src/linux-trees` 下的 C 文件时更好地适应内核的编码风格。
即便你无法成功让 `emacs` 实现合理的格式化，也并非全无补救：可以使用 `indent` 工具。
现在，同样地，GNU indent 也有与 GNU emacs 相同的那种脑残设置，
这就是为什么你需要给它一些命令行选项。
不过这还不算太糟糕，因为即便是 GNU indent 的开发者们
也承认 K&R 的权威（GNU 开发者们并不是邪恶的，他们只是在这个问题上严重误入歧途），
所以你只需给 indent 加上选项 `-kr -i8`（代表“K&R 风格，8个字符的缩进”），
或者使用 `scripts/Lindent`，它可以按照最新风格进行缩进。
`indent` 有很多选项，特别是当你需要重新格式化注释时，你可能想查阅一下它的手册页。
但是请记住：`indent` 并不能修复糟糕的编程。

请注意，你还可以使用 `clang-format` 工具来帮助你遵守这些规则，
快速自动地重新格式化代码的一部分，并审查整个文件以发现编码风格错误、拼写错误和可能的改进。
它也非常适合用于排序 `#include` 指令、对齐变量/宏、重排文本等类似任务。
详情请参阅文件 :ref:`Documentation/dev-tools/clang-format.rst <clangformat>`。

10) Kconfig 配置文件
------------------------

对于源码树中的所有 Kconfig* 配置文件，其缩进方式略有不同。
`config` 定义下的行使用一个制表符进行缩进，而帮助文本则额外增加两个空格的缩进。例如：

```plaintext
config AUDIT
	bool "Auditing support"
	depends on NET
	help
	  启用可与其他内核子系统（如 SELinux）一起使用的审计基础架构（SELinux 日志记录 avc 消息输出需要此功能）。
	  如果没有配置 CONFIG_AUDITSYSCALL，则不会进行系统调用审计。
```

特别危险的功能（比如某些文件系统的写支持）应该在提示字符串中明确标注出来：

```plaintext
config ADFS_FS_RW
	bool "ADFS 写支持 (DANGEROUS)"
	depends on ADFS_FS
	..
```

关于配置文件的完整文档，请参阅文件 Documentation/kbuild/kconfig-language.rst。

11) 数据结构
--------------

在创建和销毁数据结构的单线程环境中可见的数据结构应该始终具有引用计数。
在内核中，垃圾回收是不存在的（而在内核之外，垃圾回收又慢又低效），这意味着你绝对 **必须** 对所有使用的数据结构进行引用计数。

引用计数意味着你可以避免加锁，并允许多个用户并行访问数据结构——而不用担心数据结构会突然消失，仅仅是因为它们休眠或暂时执行了其他操作。
请注意，锁定（locking）**并非**引用计数（reference counting）的替代品。锁定用于保持数据结构的一致性，而引用计数是一种内存管理技术。通常两者都需要，并且不应将它们混淆。

许多数据结构确实可以有两层引用计数，当存在不同“类别”的用户时。子类计数统计子类用户的数量，并且仅在子类计数降为零时递减全局计数一次。

这种“多级引用计数”可以在内存管理（如 `struct mm_struct`：mm_users 和 mm_count）和文件系统代码（如 `struct super_block`：s_count 和 s_active）中找到实例。

记住：如果另一个线程能够访问到你的数据结构，而你没有在它上面设置引用计数，那么你几乎肯定存在一个错误。
12) 宏、枚举和RTL
------------------------

定义常量和枚举中的标签的宏名称应使用大写字母

```c
#define CONSTANT 0x12345
```

当需要定义多个相关常量时，建议使用枚举。

使用大写宏名称是可取的，但看起来像函数的宏可以使用小写字母命名。

通常情况下，内联函数比看起来像函数的宏更优。

具有多个语句的宏应该用 do-while 块包围：

```c
#define macrofun(a, b, c)			\
	do {					\
		if (a == 5)			\
			do_this(b, c);		\
	} while (0)
```

带有未使用的参数的函数式宏应替换为静态内联函数以避免未使用的变量问题：

```c
static inline void fun(struct foo *foo)
{
}
```

由于历史原因，许多文件仍然采用“转换为(void)”的方法来评估参数。然而，这种方法并不推荐。
这段文本主要讨论了C语言中宏（macros）的不当用法以及内联函数（inline functions）的优势，并且提到了编写内核消息时应注意的一些事项。下面是该段落的中文翻译：

内联函数解决了“带有副作用的表达式被多次计算”的问题，避免了未使用的变量问题，并且通常来说比宏有更好的文档说明，原因不明。
```c
/*
 * 尽可能避免这样做，而应选择静态内联函数
 */
#define macrofun(foo) do { (void) (foo); } while (0)
```

使用宏时要避免的问题：

1) 影响控制流程的宏：
```c
#define FOO(x)					\
    do {					\
        if (blah(x) < 0)		\
            return -EBUGGERED;	\
    } while (0)
```
这是一个非常糟糕的做法。它看起来像一个函数调用，但实际上退出了“调用”函数；不要破坏那些阅读代码的人的内部解析器。

2) 依赖于具有魔术名称的局部变量的宏：
```c
#define FOO(val) bar(index, val)
```
这看起来不错，但当人们阅读代码时会感到困惑，并且很容易因为看似无害的变化而破坏代码。

3) 参数作为左值使用的宏：FOO(x) = y; 如果某人将 FOO 转换为内联函数，则会出现问题。

4) 忽略运算符优先级：使用表达式定义常量的宏必须将表达式括在圆括号中。注意类似参数使用的宏中的类似问题。
```c
#define CONSTANT 0x4000
#define CONSTEXP (CONSTANT | 3)
```

5) 在类似于函数的宏中定义局部变量时出现的命名冲突：
```c
#define FOO(x)				\
    ({					\
        typeof(x) ret;			\
        ret = calc_ret(x);		\
        (ret);				\
    })
```
ret 是一个常见的局部变量名——__foo_ret 不太可能与已有的变量发生冲突。

cpp 手册详尽地介绍了宏。gcc 内部手册还涵盖了 RTL，这是在内核中频繁使用汇编语言时所采用的。

13) 打印内核消息
-------------------

内核开发者希望被视为有学识的人。请注意内核消息的拼写以留下好印象。不要使用错误的缩写如 “dont”；应该使用 “do not” 或者 “don’t”。使消息简洁、清晰、明确。
内核消息不必以句点结尾。
打印带括号的数字（%d）没有增加任何价值，应当避免。
在 `<linux/dev_printk.h>` 中有一系列驱动模型诊断宏，你应该使用这些宏来确保消息与正确的设备和驱动相匹配，并且标记了正确的级别：`dev_err()`、`dev_warn()`、`dev_info()` 等等。对于那些不与特定设备关联的消息，`<linux/printk.h>` 定义了 `pr_notice()`、`pr_info()`、`pr_warn()`、`pr_err()` 等。当驱动正常工作时，它们应该是静默的，因此除非出现问题，否则最好使用 `dev_dbg/pr_debug`。

编写好的调试信息可能是一项挑战；一旦你有了这些信息，它们对于远程故障排查将非常有帮助。然而，调试信息的打印方式与其他非调试信息不同。其他 `pr_XXX()` 函数无条件地打印，而 `pr_debug()` 并不如此；默认情况下它被编译器排除，除非定义了 `DEBUG` 或设置了 `CONFIG_DYNAMIC_DEBUG`。`dev_dbg()` 也是如此，一个相关的约定使用 `VERBOSE_DEBUG` 来添加 `dev_vdbg()` 消息到已经被 `DEBUG` 启用的消息中。

许多子系统有 Kconfig 调试选项来在相应的 Makefile 中开启 `-DDEBUG`；在其他情况下，特定文件通过 `#define DEBUG` 来启用。当需要无条件打印调试信息时，例如已经在调试相关的 `#ifdef` 部分内，可以使用 `printk(KERN_DEBUG ...)`。

### 14) 分配内存

内核提供了以下通用内存分配器：`kmalloc()`、`kzalloc()`、`kmalloc_array()`、`kcalloc()`、`vmalloc()` 和 `vzalloc()`。关于它们的更多信息，请参阅 API 文档：:ref:`Documentation/core-api/memory-allocation.rst <memory_allocation>`。

传递结构体大小的首选形式如下：

```c
p = kmalloc(sizeof(*p), ...);
```

显式写出结构体名称的形式会损害可读性，并且在更改指针变量类型时，如果不相应地更新传递给内存分配器的 `sizeof`，可能会引入错误。

对返回值（即一个空指针）进行类型转换是多余的。从空指针转换为任何其他指针类型是由 C 语言保证的。

分配数组的首选形式如下：

```c
p = kmalloc_array(n, sizeof(...), ...);
```

分配零初始化数组的首选形式如下：

```c
p = kcalloc(n, sizeof(...), ...);
```

这两种形式都会检查分配大小 `n * sizeof(...)` 是否溢出，并在发生溢出时返回 NULL。

这些通用分配函数在没有使用 `__GFP_NOWARN` 时失败时都会输出堆栈跟踪，因此当返回 NULL 时不需要额外输出失败消息。

### 15) 内联函数的过度使用

似乎存在一种普遍的误解，认为 gcc 有一个名为 “inline” 的神奇加速选项。虽然在某些情况下使用内联是合适的（例如，作为替换宏的一种手段，见第 12 章），但很多时候并不适合。大量使用 `inline` 关键字会导致内核变得更大，从而整体上减慢系统的速度，因为 CPU 的 icache 占用空间变大，而且仅仅是因为可用的内存更少了。只需考虑一下：页面缓存缺失会导致磁盘寻道，这很容易耗时 5 毫秒。在这 5 毫秒内可以执行大量的 CPU 周期。

一个合理的经验法则是不要在超过 3 行代码的函数中使用 `inline`。例外情况是当已知某个参数是一个编译时常量，并且由于这个常量性，你知道编译器能够在编译时优化掉你的大部分函数。一个好的例子是 `kmalloc()` 内联函数。

人们经常争论说，在函数是静态的并且只被使用一次的情况下，总是添加 `inline` 是有益的，因为不存在空间权衡。虽然从技术上讲这是正确的，但 gcc 能够自动内联这些函数，而当出现第二个用户时去除 `inline` 的维护问题超过了提示 gcc 执行它本来就会做的事情的潜在价值。
16) 函数返回值与名称
----------------------------

函数可以返回多种类型的值，其中最常见的一种是指示函数是否成功或失败的值。这种值可以用错误代码整数表示（-Exxx=失败，0=成功），或者用一个“成功”布尔值表示（0=失败，非零=成功）。
混淆这两种表示方式是导致难以发现的bug的一个丰富来源。如果C语言对整数和布尔值有明确的区别，编译器就能帮我们找到这些错误……但它没有这样做。为了防止这类bug的发生，应当始终遵循以下约定：

    如果函数的名字是一个动作或命令，则该函数应返回错误代码整数。如果名字是一个判断语句，则函数应返回一个“成功”布尔值。
例如，“add work”是一个命令，因此add_work()函数在成功时返回0，在失败时返回-EBUSY。同样地，“PCI设备存在”是一个判断语句，因此pci_dev_present()函数在找到匹配的设备时返回1，未找到时返回0。

所有EXPORTed函数必须遵守此约定，所有公共函数也应如此。对于私有（静态）函数虽然不必遵守，但建议遵守。
如果函数的返回值是计算的实际结果，而不是计算是否成功的标志，则不受此规则约束。通常，它们通过返回某个超出正常范围的结果来表示失败。典型的例子是返回指针的函数；它们使用NULL或ERR_PTR机制来报告失败。

17) 使用bool
-------------------

Linux内核中的bool类型是C99标准中_Boolean类型的别名。bool值只能评估为0或1，并且隐式或显式地转换为bool会自动将值转化为真或假。当使用bool类型时，不需要使用!!构造，这样就消除了一个类别的bug。
当处理bool值时，应该使用true和false定义，而不是1和0。
在适当的情况下，可以自由地使用bool作为函数返回类型或栈变量。鼓励使用bool以提高可读性，对于存储布尔值而言，这通常是比'int'更好的选择。
如果缓存行布局或值的大小很重要，则不要使用bool，因为其大小和对齐方式根据编译架构的不同而变化。对于优化了对齐和大小的结构体，不应使用bool。
如果一个结构体包含许多真假值，可以考虑将它们整合到位字段中，成员为1位，或者使用适当的固定宽度类型，如u8。
### 同样对于函数参数，许多真/假值可以整合到一个单一的位操作‘标志’参数中，并且如果调用位置有裸露的真/假常量，“标志”通常是一个更易读的选择。
否则，在结构体和参数中有限地使用布尔类型可以提高可读性。

18) 不要重新发明内核宏
----------------------

头文件`include/linux/kernel.h`包含了一些你应该使用的宏，而不是明确地自己编写它们的一些变体。
例如，如果你需要计算数组的长度，利用以下宏：

```c
#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
```

同样地，如果你需要计算某个结构体成员的大小，使用：

```c
#define sizeof_field(t, f) (sizeof(((t*)0)->f))
```

还有一些min()和max()宏，如果你需要它们的话，它们会进行严格的类型检查。随意浏览该头文件，看看还有什么其他已经定义的内容你不应该在你的代码中重复实现。

19) 编辑器模行和其他杂项
-----------------------------

一些编辑器能够解释嵌入在源文件中的配置信息，这些信息通过特殊标记指示。例如，Emacs解释这样的标记行：

```c
-*- mode: c -*-
```

或者像这样：

```c
/*
Local Variables:
compile-command: "gcc -DMAGIC_DEBUG_FLAG foo.c"
End:
*/
```

Vim解释如下标记：

```c
/* vim:set sw=8 noet */
```

不要在源文件中包含任何这些内容。人们有自己的个人编辑器配置，而你的源文件不应该覆盖它们。这包括缩进和模式配置的标记。人们可能使用自己的自定义模式，或者可能有其他魔法方法使缩进正确工作。

20) 内联汇编
-------------------

在架构特定的代码中，你可能需要用内联汇编来与CPU或平台功能接口。当有必要时，不要犹豫这样做。
然而，当C语言能完成任务时，不要随意使用内联汇编。尽可能地从C语言中操作硬件。

考虑编写简单的辅助函数来封装常见的内联汇编部分，而不是反复地以微小变化的方式编写它们。记住内联汇编可以使用C语言的参数。

大型、非平凡的汇编函数应该放在`.S`文件中，并在对应的C头文件中定义C原型。对于汇编函数的C原型应该使用`asmlinkage`。

你可能需要将你的asm语句标记为volatile，以防止GCC删除它（如果GCC没有注意到任何副作用）。不过，你并不总是需要这样做，而且不必要地这样做可能会限制优化。
### 多条指令的内联汇编
当编写包含多条指令的单个内联汇编语句时，应将每条指令放在单独的引号字符串中，并在除最后一个字符串外的所有字符串末尾添加`\n\t`以适当地缩进汇编输出中的下一条指令：

```c
asm ("magic %reg1, #42\n\t"
     "more_magic %reg2, %reg3"
     : /* outputs */ : /* inputs */ : /* clobbers */);
```

### 21) 条件编译
---------------------------

尽可能不要在`.c`文件中使用预处理条件（如`#if`, `#ifdef`）；这样做会使代码更难阅读、逻辑更难理解。相反，在用于`.c`文件的头文件中使用此类条件，为`#else`情况提供无操作（no-op）存根版本，然后从`.c`文件中无条件地调用这些函数。编译器会避免生成存根调用的任何代码，从而产生相同的结果，但逻辑仍然易于理解。
优先选择整个函数而不是部分函数或表达式的一部分进行条件编译。与其在表达式中放置`#ifdef`，不如将表达式的部分或全部提取到一个独立的帮助函数中，并对该函数应用条件。

如果有一个函数或变量可能在某种配置下未被使用，并且编译器会警告其定义未被使用，请标记该定义为`__maybe_unused`，而不是将其包裹在预处理条件中。（然而，如果一个函数或变量总是未被使用，则应删除它。）

在代码中，尽可能使用`IS_ENABLED`宏将Kconfig符号转换为C布尔表达式，并在正常的C条件中使用它：

```c
if (IS_ENABLED(CONFIG_SOMETHING)) {
    ..
}
```
编译器会将条件常量化（constant-fold），并像使用`#ifdef`一样包含或排除代码块，因此这不会增加任何运行时开销。然而，这种方法仍然允许C编译器看到代码块内的内容，并检查其正确性（语法、类型、符号引用等）。因此，如果代码块内部引用了在条件不满足时不存在的符号，则仍然需要使用`#ifdef`。

对于任何非平凡的`#if`或`#ifdef`块（超过几行），在`#endif`后面在同一行上放置注释，注明使用的条件表达式。例如：

```c
#ifdef CONFIG_SOMETHING
    ..
#endif /* CONFIG_SOMETHING */
```

### 22) 不要使内核崩溃
---------------------------

通常情况下，决定是否使内核崩溃属于用户而非内核开发者的职责。
避免使用`panic()`函数
*************

`panic()`函数应当谨慎使用，主要是在系统启动期间使用。
例如，在启动过程中内存不足无法继续时可以接受使用`panic()`函数。
使用`WARN()`而不是`BUG()`
****************************

不要添加新的使用任何`BUG()`变体（如`BUG()`, `BUG_ON()`, 或 `VM_BUG_ON()`）的代码。相反，应使用`WARN*()`变体，最好使用`WARN_ON_ONCE()`，并且可能带有恢复代码。如果没有合理的方法至少部分恢复，则不需要恢复代码。“我太懒惰而不想处理错误”不是使用`BUG()`的理由。重大的内部损坏且没有继续的方式仍可使用`BUG()`，但需要充分的理由。
使用 `WARN_ON_ONCE()` 而不是 `WARN()` 或 `WARN_ON()`
**************************************************

通常更倾向于使用 `WARN_ON_ONCE()` 而不是 `WARN()` 或 `WARN_ON()`，因为一旦出现警告条件，这种情况往往会多次发生。这可能会填满并循环利用内核日志，并且甚至可能使系统变慢到足以让过多的日志记录变成另一个额外的问题。

不要轻易发出警告
*******************

`WARN*()` 用于意料之外、不应该发生的情况。
`WARN*()` 宏不应用于在正常操作中预期会发生的任何情况。例如，这些宏不是预条件或后置断言。再次强调：`WARN*()` 不应用于预期容易触发的条件，比如由用户空间行为触发的条件。如果需要通知用户问题的存在，`pr_warn_once()` 可能是一个可行的替代方案。

不必担心启用 `panic_on_warn` 的用户
**************************************

关于 `panic_on_warn` 的一些额外说明：请记住 `panic_on_warn` 是一个可用的内核选项，许多用户设置了这个选项。这就是为什么上面有“不要轻易发出警告”的说明。但是，存在 `panic_on_warn` 用户并不是避免适当使用 `WARN*()` 的有效理由。这是因为，任何人启用 `panic_on_warn` 都明确要求内核在 `WARN*()` 触发时崩溃，而这类用户必须准备好应对系统更有可能崩溃所带来的后果。

使用 `BUILD_BUG_ON()` 进行编译时断言
**********************************************

使用 `BUILD_BUG_ON()` 是可接受的并且被鼓励的，因为它是一种只在编译时生效的断言，在运行时没有效果。

附录 I) 参考资料
----------------------

《C 程序设计语言》（第二版）
作者：Brian W. Kernighan 和 Dennis M. Ritchie
出版社：Prentice Hall, Inc., 1988
ISBN 0-13-110362-8（平装本），0-13-110370-9（精装本）

《编程实践》
作者：Brian W. Kernighan 和 Rob Pike
出版社：Addison-Wesley, Inc., 1999
ISBN 0-201-61586-X
GNU 手册 - 在符合 K&R 和本文档的地方 - 涵盖了 cpp、gcc、
gcc 内部原理 和 indent，所有这些均可从 https://www.gnu.org/manual/ 获取。

WG14 是编程语言 C 的国际标准化工作组，网址为：http://www.open-std.org/JTC1/SC22/WG14/

Kernel CodingStyle，由 greg@kroah.com 在 2002 年的 OLS 上发表：
http://www.kroah.com/linux/talks/ols_2002_kernel_codingstyle_talk/html/
