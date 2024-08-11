.. title:: 关于 Kernel-doc 注释的编写

===========================
编写 Kernel-doc 格式的注释
===========================

Linux 内核源文件中可以包含以 Kernel-doc 格式编写的结构化文档注释，用于描述函数、类型及代码设计。当文档嵌入到源文件中时，更容易保持其更新。
.. note:: Kernel-doc 的格式与 javadoc、gtk-doc 或 Doxygen 非常相似，但由于历史原因又有所不同。内核源码中包含了数以万计的 Kernel-doc 注释，请遵循此处描述的风格。
.. note:: Kernel-doc 不适用于 Rust 代码：请参阅 `Documentation/rust/general-information.rst` 而不是本指南。

从这些注释中提取出 Kernel-doc 结构，并生成带有锚点的 `Sphinx C Domain`_ 函数和类型描述。这些描述经过过滤，以便突出显示特殊的 Kernel-doc 特性并建立交叉引用。详细信息见下文。
.. _Sphinx C Domain: http://www.sphinx-doc.org/en/stable/domains.html

使用 `EXPORT_SYMBOL` 或 `EXPORT_SYMBOL_GPL` 导出到可加载模块的所有函数都应该有 Kernel-doc 注释。同样地，预期被模块使用的头文件中的函数和数据结构也应该有 Kernel-doc 注释。

良好的做法是为对外可见（非 `static` 标记）的其他内核文件中的函数提供 Kernel-doc 格式的文档。我们还建议为私有的（文件级 `static`）例程提供 Kernel-doc 格式的文档，以保持内核源代码布局的一致性。这相对较低优先级，由该内核源文件的维护者自行决定。
如何格式化 Kernel-doc 注释
------------------------------

Kernel-doc 注释使用开头的注释标记 ``/**``。`kernel-doc` 工具将提取这样标记的注释。注释的其余部分像常规多行注释一样格式化，在左侧有一列星号，并且以单独一行的 ``*/`` 结束。

函数和类型的 Kernel-doc 注释应紧接在其描述的对象之前放置，以便最大化代码变更者同时变更文档的可能性。概览性的 Kernel-doc 注释可以放在最顶部的缩进级别上的任何位置。

可以通过提高 `kernel-doc` 工具的详细度并在不实际生成输出的情况下运行它来验证文档注释的正确格式。例如：

```
scripts/kernel-doc -v -none drivers/foo/bar.c
```

当请求进行额外的 gcc 检查时，内核构建过程会验证文档格式：

```
make W=n
```

函数文档
--------------

函数和类似函数的宏的 Kernel-doc 注释的一般格式如下：

```
/**
 * function_name() - 函数的简要描述
 * @arg1: 描述第一个参数
```
在函数名称后的简短描述可以跨越多行，并以参数描述、空的注释行或整个注释块的结尾为结束。
函数参数
~~~~~~~~

每个函数参数应按顺序立即跟随简短的函数描述进行说明。不要在函数描述和参数之间，以及参数之间留有空行。
每个 ``@参数:`` 描述可以跨越多行。

* `@arg2`: 描述第二个参数
    * 可以为参数提供多行描述

* 更长的描述，包含更多关于函数 `function_name()` 的讨论，这可能对使用或修改它的人员有用。从一个空的注释行开始，并且可以包含额外嵌入的空注释行。

* 长描述可能包含多个段落。

* 上下文: 描述函数是否可以休眠，它获取了什么锁，释放了什么锁，或者期望被持有的锁。它可以跨越多行。

* 返回值: 描述 `function_name` 的返回值。

    * 返回值描述也可以包含多个段落，并且应该放在注释块的末尾。
### 注意：

- 如果`@argument`的描述有多行，描述的后续内容应当从与前一行相同的列开始，例如：

  * @argument: 某些长描述
  *            在下一行继续

- 或者：

  * @argument:
  *		某些长描述
  *		在下一行继续

- 如果一个函数有可变数量的参数，其描述应当用内核文档注解的方式写为：

  * @...: 描述

### 函数上下文

- 应当在一个名为“上下文”的部分中描述函数可以被调用的上下文。这应包括该函数是否休眠或可以从中断上下文中调用，以及它获取、释放了哪些锁，并期望调用者持有何种锁。
  示例：

  * 上下文：任何上下文
  * 上下文：任何上下文。获取并释放RCU锁
  * 上下文：任何上下文。期望<lock>由调用者持有
  * 上下文：进程上下文。如果@gfp标志允许，则可能休眠
  * 上下文：进程上下文。获取并释放<mutex>
  * 上下文：软中断或进程上下文。获取并释放<lock>，BH安全
  * 上下文：中断上下文

### 返回值

- 如果有的话，返回值应当在一个专门命名为“返回”（或“Returns”）的部分中描述。

### 注意：

1. 提供的多行描述性文本不识别换行符，因此如果你尝试格式化一些文本，如：

   * 返回：
   * %0 - 正常
   * %-EINVAL - 无效参数
   * %-ENOMEM - 内存不足

   这将全部连在一起，产生：

   返回: 0 - 正常 -EINVAL - 无效参数 -ENOMEM - 内存不足

   因此，为了产生所需的换行，你需要使用ReST列表，例如：

   * 返回：
   * * %0		- 允许运行时挂起设备
   * * %-EBUSY	- 设备不应被运行时挂起

2. 如果提供的描述性文本中有以某些短语后跟冒号开头的行，这些短语将被视为新的小节标题，这可能不会产生预期的效果。
结构体、联合体和枚举的文档说明
-----------------------------------------------

结构体、联合体及枚举的内核文档注释的一般格式如下：

```c
/**
 * struct 结构体名称 - 简要描述
 * @成员1: 成员1的描述
 * @成员2: 成员2的描述
 *           可以为成员提供多行描述
 *
 * 结构体的详细描述
 */
```

在上述示例中，您可以将 `struct` 替换为 `union` 或 `enum` 来描述联合体或枚举。`成员` 用于表示结构体和联合体中的成员名称以及枚举中的枚举值。

紧跟在结构体名称后面的简要描述可以跨越多行，并以成员描述、空白注释行或注释块的结束作为终止。

### 成员

结构体、联合体和枚举的成员应当像函数参数那样进行文档说明；它们紧随简短描述之后，并且可以跨越多行。

在结构体或联合体的描述中，您可以使用 `private:` 和 `public:` 注释标签。位于 `private:` 区域内的结构体字段不会出现在生成的输出文档中。

`private:` 和 `public:` 标签必须紧跟着 `/*` 注释标记开始。这些标签可选地在 `: ` 和结束的 `*/` 标记之间包含注释内容。
示例：

  /**
   * 结构体 my_struct - 简短描述
   * @a: 第一个成员
   * @b: 第二个成员
   * @d: 第四个成员
   *
   * 更长的描述
   */
  struct my_struct {
      int a;
      int b;
  /* private: 仅供内部使用 */
      int c;
  /* public: 下一个成员是公开的 */
      int d;
  };

嵌套结构体/联合体
~~~~~~~~~~~~~~~~~~~~~

可以为嵌套的结构体和联合体添加文档注释，例如：

      /**
       * 结构体 nested_foobar - 包含嵌套的联合体和结构体
       * @memb1: 匿名联合体/匿名结构体的第一个成员
       * @memb2: 匿名联合体/匿名结构体的第二个成员
       * @memb3: 匿名联合体/匿名结构体的第三个成员
       * @memb4: 匿名联合体/匿名结构体的第四个成员
       * @bar: 非匿名联合体
       * @bar.st1: 联合体 @bar 内的结构体 st1
       * @bar.st2: 联合体 @bar 内的结构体 st2
       * @bar.st1.memb1: 联合体 bar 中结构体 st1 的第一个成员
       * @bar.st1.memb2: 联合体 bar 中结构体 st1 的第二个成员
       * @bar.st2.memb1: 联合体 bar 中结构体 st2 的第一个成员
       * @bar.st2.memb2: 联合体 bar 中结构体 st2 的第二个成员
       */
      struct nested_foobar {
        /* 匿名联合体/结构体 */
        union {
          struct {
            int memb1;
            int memb2;
          };
          struct {
            void *memb3;
            int memb4;
          };
        };
        union {
          struct {
            int memb1;
            int memb2;
          } st1;
          struct {
            void *memb1;
            int memb2;
          } st2;
        } bar;
      };

.. 注意::

   #) 在记录嵌套的结构体或联合体时，如果结构体/联合体 ``foo`` 有命名，则其内部成员 ``bar`` 应该记录为 ``@foo.bar:``
   #) 当嵌套的结构体/联合体是匿名的，其中的成员 ``bar`` 应该记录为 ``@bar:``

内联成员文档注释
~~~~~~~~~~~~~~~~~~~~~

结构体成员也可以在定义中直接记录文档。有两种样式：单行注释，其中“/**”和“*/”都在同一行；多行注释，它们各自位于单独的一行，就像所有其他内核文档注释一样：

  /**
   * 结构体 foo - 简短描述
* @foo: Foo 成员
*/
  struct foo {
        int foo;
        /**
         * @bar: Bar 成员
*/
        int bar;
        /**
         * @baz: Baz 成员
*
         * 这里，成员描述可以包含多个段落
*/
        int baz;
        union {
                /** @foobar: 单行描述。 */
                int foobar;
        };
        /** @bar2: 结构体 @bar2 在 @foo 中的描述 */
        struct {
                /**
                 * @bar2.barbar: 描述 @foo.bar2 内的 @barbar
                 */
                int barbar;
        } bar2;
  };

类型别名文档
---------------------

类型别名内核文档注释的一般格式如下：

  /**
   * typedef 类型名称 - 简短描述
*
   * 类型描述
*/

带有函数原型的类型别名也可以被记录文档：

  /**
   * typedef 类型名称 - 简短描述
* @arg1: arg1 的描述
   * @arg2: arg2 的描述
   *
   * 类型描述
*/
### Translation into Chinese:

#### 锁定上下文 (Locking context)
```
typedef void (*type_name)(struct v4l2_ctrl *arg1, void *arg2);
```

**对象宏文档**
----------------------

对象宏与函数宏是不同的。它们的区别在于：对于函数宏，宏名后直接跟着一个左括号 '('；而对于对象宏，则没有紧随其后的左括号。

函数宏在`scripts/kernel-doc`中被当作函数处理。它们可能有参数列表。而对象宏则没有参数列表。
对象宏的内核文档注释的一般格式如下：

```markdown
/**
 * 定义 object_name - 简要描述
 *
 * 对象的详细描述
 */
```

**示例**

```markdown
/**
 * 定义 MAX_ERRNO - 支持的最大错误码值
 *
 * 内核指针包含冗余信息，因此我们可以使用一种方案，使得我们可以通过相同的返回值返回一个错误代码或一个常规指针。
 */
#define MAX_ERRNO	4095
```

**示例**

```markdown
/**
 * 定义 DRM_GEM_VRAM_PLANE_HELPER_FUNCS - 初始化用于 VRAM 处理的 struct drm_plane_helper_funcs
 *
 * 此宏初始化 struct drm_plane_helper_funcs 使用相应的辅助函数。
 */
#define DRM_GEM_VRAM_PLANE_HELPER_FUNCS \
	.prepare_fb = drm_gem_vram_plane_helper_prepare_fb, \
	.cleanup_fb = drm_gem_vram_plane_helper_cleanup_fb
```

**高亮和交叉引用**
----------------------

在内核文档注释的描述性文本中，以下特殊模式会被识别并转换为适当的reStructuredText标记和`Sphinx C Domain`_ 引用。
以下内容**仅**在`kernel-doc`注释中被识别，**不**在普通的reStructuredText文档中被识别：

``funcname()``
  函数引用
``@parameter``
  函数参数的名称。（没有交叉引用功能，仅格式化。）

``%CONST``
  常量的名称。（没有交叉引用功能，仅格式化。）

````literal````
  应按原样处理的字面值块。输出将使用`等宽字体`。
对于需要使用在`kernel-doc`脚本或reStructuredText中有特殊含义的特殊字符时非常有用。
特别是在函数描述中需要使用诸如``%ph``之类的内容时尤其有用。

``$ENVVAR``
  环境变量的名称。（没有交叉引用功能，仅格式化。）

``&struct name``
  结构体引用
``&enum name``
  枚举引用
``&typedef name``
  类型定义（typedef）引用
``&struct_name->member`` 或 ``&struct_name.member``
  结构体或联合体成员引用。交叉引用指向的是结构体或联合体定义，而不是直接指向成员本身。
``&name``
  泛型类型引用。建议尽可能使用上面所述的完整引用。这主要用于遗留注释中。
从 reStructuredText 中进行交叉引用
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在从 reStructuredText 文档中交叉引用内核文档注释中定义的函数和类型时，无需额外的语法。只需在函数名后加上 ``()``，并在类型前写上 ``struct``、``union``、``enum`` 或 ``typedef`` 即可。例如：

  参见 foo()
参见 struct foo
参见 union bar
参见 enum baz
参见 typedef meh

然而，如果你想在交叉引用链接中使用自定义文本，可以通过以下语法实现：

  参见 :c:func:`我为函数 foo 自定义的链接文本 <foo>`
参见 :c:type:`我为 struct bar 自定义的链接文本 <bar>`

对于更多细节，请参考 `Sphinx C 领域`_ 文档。
### 概览文档注释
-------------------------------

为了便于将源代码和注释紧密地结合在一起，您可以包含自由形式的内核文档（kernel-doc）注释块，而不是为函数、结构体、联合体、枚举或类型定义提供内核文档。这可以用于描述驱动程序或库代码的工作原理等。
这是通过使用带有部分标题的 `DOC:` 关键字来实现的。
概览或高级文档注释的一般格式如下：

  /**
   * DOC: 工作原理
   *
   * Whizbang Foobar 是一个非常厉害的小工具。它能够随时完成你想要的任何事情。它能读懂你的想法。以下是其工作方式：
   *
   * foo bar splat
   *
   * 这个小工具唯一的缺点是有时可能会损坏硬件、软件或目标对象。
*/

`DOC:` 后面的标题在源文件中作为小节标题，同时也作为提取文档注释的标识符。因此，该标题必须在文件内部保持唯一性。

### 包含内核文档注释

可以使用专门的内核文档 Sphinx 指令扩展将文档注释包含在任何 reStructuredText 文档中。
内核文档指令的格式如下：

  .. kernel-doc:: source
     :option:

其中 *source* 是相对于内核源码树的源文件路径。以下是一些支持的指令选项：

- export: *[source-pattern ...]*
  包含在 *source* 中使用 `EXPORT_SYMBOL` 或 `EXPORT_SYMBOL_GPL` 导出的所有函数的文档，这些函数可以在 *source* 或由 *source-pattern* 指定的文件中找到。
  当内核文档注释被放置在头文件中，而 `EXPORT_SYMBOL` 和 `EXPORT_SYMBOL_GPL` 在函数定义旁边时，*source-pattern* 非常有用。

示例：

    .. kernel-doc:: lib/bitmap.c
       :export:

    .. kernel-doc:: include/net/mac80211.h
       :export: net/mac80211/*.c

- internal: *[source-pattern ...]*
  包含在 *source* 中未使用 `EXPORT_SYMBOL` 或 `EXPORT_SYMBOL_GPL` 导出的所有函数和类型的文档，无论是在 *source* 还是在由 *source-pattern* 指定的文件中。

示例：

    .. kernel-doc:: drivers/gpu/drm/i915/intel_audio.c
       :internal:

- identifiers: *[ function/type ...]*
  包含 *source* 中每个 *function* 和 *type* 的文档。
如果未指定任何*函数*，则*源代码*中所有函数和类型的文档都将被包含。
示例：

    .. kernel-doc:: lib/bitmap.c
       :identifiers: bitmap_parselist bitmap_parselist_user

    .. kernel-doc:: lib/idr.c
       :identifiers:

no-identifiers: *[ 函数/类型 ...]*
  排除*源代码*中每个*函数*和*类型*的文档。
示例：

    .. kernel-doc:: lib/bitmap.c
       :no-identifiers: bitmap_parselist

functions: *[ 函数/类型 ...]*
  这是'identifiers'指令的别名，并已被废弃。
doc: *标题*
  包括在*源代码*中由*标题*标识的``DOC:``段落的文档。*标题*允许包含空格；不要给*标题*加引号。*标题*仅用于标识段落，并不包含在输出中。请确保在包含的reStructuredText文档中有适当的标题。
示例：

    .. kernel-doc:: drivers/gpu/drm/i915/intel_audio.c
       :doc: 高清音频通过HDMI和显示端口

如果没有选项，kernel-doc指令将包含来自源文件的所有文档注释。
kernel-doc扩展包含在内核源码树中，位于``Documentation/sphinx/kerneldoc.py``。内部，它使用``scripts/kernel-doc``脚本来从源码提取文档注释。
.. _kernel_doc:

如何使用kernel-doc生成手册页
-------------------------------------------

如果您只想使用kernel-doc来生成手册页，可以从内核git仓库执行如下命令：

  $ scripts/kernel-doc -man \
    $(git grep -l '/\*\*' -- :^Documentation :^tools) \
    | scripts/split-man.pl /tmp/man

某些较旧版本的git可能不支持路径排除语法的一些变体。以下命令之一可能适用于这些版本：

  $ scripts/kernel-doc -man \
    $(git grep -l '/\*\*' -- . ':!Documentation' ':!tools') \
    | scripts/split-man.pl /tmp/man

  $ scripts/kernel-doc -man \
    $(git grep -l '/\*\*' -- . ":(exclude)Documentation" ":(exclude)tools") \
    | scripts/split-man.pl /tmp/man
