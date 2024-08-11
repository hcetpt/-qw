### SPDX 许可证标识符：GPL-2.0-only

####

### 检查补丁

####

检查补丁（scripts/checkpatch.pl）是一个 Perl 脚本，用于检查补丁中的简单样式违规，并可选地进行修正。检查补丁也可以在没有内核树的情况下运行在文件上下文中。
请注意，检查补丁并不总是正确的。您的判断优先于检查补丁的消息。如果带有违规的代码看起来更好，那么可能最好保持原样。

### 选项

####

本节将描述可以与检查补丁一起使用的选项。
使用方法如下：

```
./scripts/checkpatch.pl [OPTION]... [FILE]..
```

可用选项：

- `-q`, `--quiet`

  启用静默模式
- `-v`, `--verbose`

  启用详细模式。输出额外的详细测试描述，以便提供关于为何显示特定消息的信息
- `--no-tree`

  在没有内核树的情况下运行检查补丁
- `--no-signoff`

  禁用“Signed-off-by”行检查。“签署”是一行简单的文字，位于补丁说明的末尾，证明您编写了它或有权将其作为开源补丁传递
例如：

    Signed-off-by: 随机 J 开发者 <random@developer.example.org>

  设置此标志会阻止在补丁上下文中因缺少签署行而产生的消息
- `--patch`

  将`FILE`视为补丁。这是默认选项，无需明确指定
- --emacs

   将输出设置为 Emacs 编译窗口格式。这允许 Emacs 用户从编译窗口中的错误直接跳转到补丁中引起问题的行。
- --terse

   每份报告仅输出一行。
- --showfile

   显示差异文件的位置，而不是输入文件的位置。
- -g,  --git

   将 FILE 视为单个提交或 Git 修订范围。
   单个提交可通过以下方式指定：

   - <rev>
   - <rev>^
   - <rev>~n

   多个提交可通过以下方式指定：

   - <rev1>..<rev2>
   - <rev1>...<rev2>
   - <rev>-<count>

- -f,  --file

   将 FILE 视为常规源文件。在对内核中的源文件运行 checkpatch 时必须使用此选项。
- --subjective,  --strict

   在 checkpatch 中启用更严格的测试。默认情况下，标记为 CHECK 的测试不会自动激活。使用此标志来激活 CHECK 测试。
- --list-types

   checkpatch 输出的每条消息都有一个关联的类型。添加此标志以显示 checkpatch 中的所有类型。
   注意：当此标志生效时，checkpatch 不会读取输入文件 FILE，并且不会输出任何消息。仅输出 checkpatch 中的类型列表。
- --types TYPE(,TYPE2...)

   仅显示具有指定类型的那些消息。
   示例::

     ./scripts/checkpatch.pl mypatch.patch --types EMAIL_SUBJECT,BRACES

- --ignore TYPE(,TYPE2...)

   checkpatch 不会为指定的类型输出消息。
示例：

     ./scripts/checkpatch.pl mypatch.patch --ignore EMAIL_SUBJECT,BRACES

- --show-types

   默认情况下，checkpatch 不会显示与消息关联的类型。设置此标志以在输出中显示消息类型。
- --max-line-length=n

   设置最大行长度（默认为 100）。如果一行超过指定长度，则会发出 LONG_LINE 消息。
   对于补丁，会发出一个 WARNING。而对于文件，会发出较轻级别的 CHECK。因此，在文件上下文中，
   还必须启用 --strict 标志。
- --min-conf-desc-length=n

   设置 Kconfig 条目的最小描述长度，如果更短，则发出警告。
- --tab-size=n

   设置制表符代表的空间数（默认为 8）。
- --root=PATH

   内核树根目录的路径。
   当从内核根目录之外调用 checkpatch 时，必须指定此选项。
- --no-summary

   抑制每个文件的总结信息。
- --mailback

   仅在出现警告或错误的情况下生成报告。较轻级别的检查将被排除在外。
--summary-file

   在摘要中包含文件名
--debug KEY=[0|1]

   打开或关闭KEY的调试，其中KEY可以是'values'、'possible'、'type'和'attr'之一（默认全部关闭）
--fix

   这是一个实验性功能。如果存在可修正的错误，则会创建一个名为<inputfile>.EXPERIMENTAL-checkpatch-fixes的文件，
   其中包含了自动修正的错误
--fix-inplace

   实验性功能 — 类似于--fix，但会用修复后的内容覆盖原输入文件
   除非你完全确定并且已有备份，请勿使用此标志
--ignore-perl-version

   忽略perl版本检查。启用此标志后，如果perl版本低于最低要求，可能会在运行时遇到错误
--codespell

   使用codespell词典来检查拼写错误
--codespellfile

   使用指定的codespell文件
   默认为'/usr/share/codespell/dictionary.txt'
--typedefsfile

   从此文件读取额外类型定义
### --color[=WHEN]

   使用颜色，可选 'always'（始终）、'never'（从不），或仅当输出是终端时使用 ('auto')。默认为 'auto'。
- --kconfig-prefix=WORD

   将 WORD 作为 Kconfig 符号的前缀（默认为 `CONFIG_`）。
- -h, --help, --version

   显示帮助文本。

### 消息级别
####

在 checkpatch 中的消息分为三个级别。这些消息级别表示错误的严重程度。它们分别是：

- **ERROR**

  这是最严格的级别。类型为 ERROR 的消息必须认真对待，因为它们表示极有可能出错的情况。
- **WARNING**

  这是次一级别的严格程度。类型为 WARNING 的消息需要更仔细地审查。但其严格程度低于 ERROR。
- **CHECK**

  这是最宽松的级别。这类情况可能需要一些思考。

### 类型描述
####

本节包含 checkpatch 中所有消息类型的描述。
.. 本节中的类型也被 checkpatch 解析。
.. 根据用途，这些类型被分组到子节中。
分配风格
----------------

  **ALLOC_ARRAY_ARGS**
    对于`kcalloc`或`kmalloc_array`的第一个参数应该是元素的数量。使用`sizeof()`作为第一个参数通常是错误的。
参见: https://www.kernel.org/doc/html/latest/core-api/memory-allocation.html

  **ALLOC_SIZEOF_STRUCT**
    分配风格存在问题。通常，对于使用`sizeof()`来获取内存大小的一系列分配函数，应该避免这样的构造: 

      p = alloc(sizeof(struct foo), ...)

    而应当是:

      p = alloc(sizeof(*p), ...)
      
    参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#allocating-memory

  **ALLOC_WITH_MULTIPLY**
    应优先使用`kmalloc_array`/`kcalloc`而非`kmalloc`/`kzalloc`与`sizeof`乘法一起使用
参见: https://www.kernel.org/doc/html/latest/core-api/memory-allocation.html


API 使用
---------

  **ARCH_DEFINES**
    尽可能避免使用架构特定的宏定义
**ARCH_INCLUDE_LINUX**
    当包含`asm/file.h`且存在`linux/file.h`时，可以转换为后者包含前者的情况（除非特殊情况，例如`signal.h`）
本消息类型仅在从`arch/`目录下的文件中进行包含时产生
**AVOID_BUG**
    完全避免使用`BUG()`或`BUG_ON()` 
推荐使用`WARN()`和`WARN_ON()`，并尽可能优雅地处理“不可能”的错误条件
参见: https://www.kernel.org/doc/html/latest/process/deprecated.html#bug-and-bug-on

  **CONSIDER_KSTRTO**
    `simple_strtol()`、`simple_strtoll()`、`simple_strtoul()`和`simple_strtoull()`函数明确忽略溢出情况，这可能导致调用者处出现意外结果。相应的`kstrtol()`、`kstrtoll()`、`kstrtoul()`和`kstrtoull()`函数往往是正确的替代选择
参见: https://www.kernel.org/doc/html/latest/process/deprecated.html#simple-strtol-simple-strtoll-simple-strtoul-simple-strtoull

  **CONSTANT_CONVERSION**
    下列函数中的`__constant_<foo>`形式的使用被不鼓励：

      __constant_cpu_to_be[x]
      __constant_cpu_to_le[x]
      __constant_be[x]_to_cpu
      __constant_le[x]_to_cpu
      __constant_htons
      __constant_ntohs

    在`include/uapi/`之外使用这些函数时，不推荐使用`__constant_`前缀，因为当参数为常量时，使用这些函数和没有该前缀的效果是一样的。
在大端系统中，宏如`__constant_cpu_to_be32(x)`和`cpu_to_be32(x)`扩展为相同的表达式：

```c
#define __constant_cpu_to_be32(x) ((__force __be32)(__u32)(x))
#define __cpu_to_be32(x)          ((__force __be32)(__u32)(x))
```

在小端系统中，宏`__constant_cpu_to_be32(x)`和`cpu_to_be32(x)`扩展为`__constant_swab32`和`__swab32`。`__swab32`有一个`__builtin_constant_p`检查：

```c
#define __swab32(x)				\
        (__builtin_constant_p((__u32)(x)) ?	\
        ___constant_swab32(x) :			\
        __fswab32(x))
```

因此，它们对常量有特殊处理。
列表中的所有宏都是类似的情况。因此，在`include/uapi`之外使用`__constant_...`形式是不必要的冗长，并不推荐使用。
详情参见：https://lore.kernel.org/lkml/1400106425.12666.6.camel@joe-AO725/

**DEPRECATED_API**
检测到使用了已弃用的RCU API。建议替换旧版风味的RCU API为其新的vanilla-RCU版本。
完整的RCU API列表可以从内核文档查看：
详情参见：https://www.kernel.org/doc/html/latest/RCU/whatisRCU.html#full-list-of-rcu-apis

**DEPRECATED_VARIABLE**
`EXTRA_{A,C,CPP,LD}FLAGS`已被废弃，应替换为通过提交`f77bf01425b1`（"kbuild: 引入ccflags-y, asflags-y 和 ldflags-y"）添加的新标志。
以下转换方案可以采用：

```c
EXTRA_AFLAGS    ->  asflags-y
EXTRA_CFLAGS    ->  ccflags-y
EXTRA_CPPFLAGS  ->  cppflags-y
EXTRA_LDFLAGS   ->  ldflags-y
```

详情参见：

1. https://lore.kernel.org/lkml/20070930191054.GA15876@uranus.ravnborg.org/
2. https://lore.kernel.org/lkml/1313384834-24433-12-git-send-email-lacombar@gmail.com/
3. https://www.kernel.org/doc/html/latest/kbuild/makefiles.html#compilation-flags

**DEVICE_ATTR_FUNCTIONS**
在`DEVICE_ATTR`中使用的函数名不常见。
通常，存储和显示函数与`<attr>_store`和`<attr>_show`一起使用，其中`<attr>`是设备的命名属性变量。
考虑以下示例：

```c
static DEVICE_ATTR(type, 0444, type_show, NULL);
static DEVICE_ATTR(power, 0644, power_show, power_store);
```

函数名应当遵循上述模式。
详情参见：https://www.kernel.org/doc/html/latest/driver-api/driver-model/device.html#attributes

**DEVICE_ATTR_RO**
可以使用`DEVICE_ATTR_RO(name)`辅助宏代替`DEVICE_ATTR(name, 0444, name_show, NULL)`。

注意，该宏会自动将`_show`附加到设备的命名属性变量上以供显示方法使用。
详情参见：https://www.kernel.org/doc/html/latest/driver-api/driver-model/device.html#attributes

**DEVICE_ATTR_RW**
可以使用`DEVICE_ATTR_RW(name)`辅助宏代替`DEVICE_ATTR(name, 0644, name_show, name_store)`。

注意，该宏会自动将`_show`和`_store`附加到设备的命名属性变量上以供显示和存储方法使用。
查看：https://www.kernel.org/doc/html/latest/driver-api/driver-model/device.html#attributes

  **DEVICE_ATTR_WO**
    可以使用 DEVICE_ATTR_WO(name) 帮助宏代替
    DEVICE_ATTR(name, 0200, NULL, name_store);

    注意，该宏会自动在设备的命名属性变量后添加 _store
    作为存储方法。

查看：https://www.kernel.org/doc/html/latest/driver-api/driver-model/device.html#attributes

  **DUPLICATED_SYSCTL_CONST**
    提交 d91bff3011cf ("proc/sysctl: 为范围检查添加共享变量")
    添加了一些共享的常量变量来替代每个源文件中的局部副本。
    考虑将 sysctl 范围检查值替换为 include/linux/sysctl.h 中的共享值。可以采用以下转换方案：

      &zero     ->  SYSCTL_ZERO
      &one      ->  SYSCTL_ONE
      &int_max  ->  SYSCTL_INT_MAX

    查看：

      1. https://lore.kernel.org/lkml/20190430180111.10688-1-mcroce@redhat.com/
      2. https://lore.kernel.org/lkml/20190531131422.14970-1-mcroce@redhat.com/

  **ENOSYS**
    ENOSYS 表示调用了一个不存在的系统调用
    之前错误地用于表示对有效系统调用的无效操作等情形。新代码中应避免这种做法。
查看：https://lore.kernel.org/lkml/5eb299021dec23c1a48fa7d9f2c8b794e967766d.1408730669.git.luto@amacapital.net/

  **ENOTSUPP**
    ENOTSUPP 不是一个标准的错误代码，并且应该在新的补丁中避免使用
    应该使用 EOPNOTSUPP 代替。
查看：https://lore.kernel.org/netdev/20200510182252.GA411829@lunn.ch/

  **EXPORT_SYMBOL**
    应当立即在要导出的符号后面使用 EXPORT_SYMBOL

**IN_ATOMIC**
    in_atomic() 并不是用于驱动程序的，因此任何这样的使用都会被报告为 ERROR。
    同时，in_atomic() 经常被用来判断是否允许睡眠，但这种方法并不可靠。因此，其使用被强烈不推荐。
    然而，in_atomic() 在核心内核中的使用是允许的。
**LOCKDEP**
已添加 lockdep_no_validate 类作为一种临时措施，以防止在将 device->sem 转换为 device->mutex 时出现警告。
它不应用于任何其他目的。
参见：https://lore.kernel.org/lkml/1268959062.9440.467.camel@laptop/

**MALFORMED_INCLUDE**
#include 语句的路径格式不正确。这是因为作者不小心在路径名中包含了一个双斜杠 "//"。
参见：https://lore.kernel.org/lkml/20080320201723.b87b3732.akpm@linux-foundation.org/

**USE_LOCKDEP**
应当优先使用 lockdep_assert_held() 注解，而不是基于 spin_is_locked() 的断言。
参见：https://www.kernel.org/doc/html/latest/locking/lockdep-design.html#annotations

**UAPI_INCLUDE**
在 include/uapi 中不应该有任何 #include 语句使用 uapi/ 路径。

**USLEEP_RANGE**
应优先使用 usleep_range() 而不是 udelay()。使用 usleep_range() 的正确方法已在内核文档中说明。
参见：https://www.kernel.org/doc/html/latest/timers/timers-howto.html#delays-information-on-the-various-kernel-delay-sleep-mechanisms

---

**注释**

**BLOCK_COMMENT_STYLE**
注释样式不正确。对于多行注释，首选的样式是：

```c
/*
* 这是首选的样式
* 对于多行注释
*/
```

网络文件中的注释风格略有不同，第一行不会像前者那样为空：

```c
/* 这是首选的注释风格
* 对于 net/ 和 drivers/net/ 文件中的注释
*/
```

参见：https://www.kernel.org/doc/html/latest/process/coding-style.html#commenting

**C99_COMMENTS**
不应使用 C99 风格的单行注释（//）。
建议使用块注释风格。
参见：https://www.kernel.org/doc/html/latest/process/coding-style.html#commenting

**DATA_RACE**
data_race() 的应用应该有一个注释来记录为什么认为它是安全的原因。
参见：https://lore.kernel.org/lkml/20200401101714.44781-1-elver@google.com/

**FSF_MAILING_ADDRESS**
内核维护者拒绝接受新的 GPL 锅炉板段落实例，该段落指示人们写信给 FSF 获取 GPL 的副本，因为 FSF 在过去曾经搬家，并且将来可能还会搬家。
---

### 关于向自由软件基金会的邮寄地址撰写段落
不要撰写关于向自由软件基金会邮寄地址写信的大段文字。
参见：https://lore.kernel.org/lkml/20131006222342.GT19510@leaf/

### 提交信息
--------------

  **BAD_SIGN_OFF**
    签名行不符合社区规定的标准
参见：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#developer-s-certificate-of-origin-1-1

  **BAD_STABLE_ADDRESS_STYLE**
    稳定版的电子邮件格式不正确
一些正确的稳定版地址格式选项包括：

      1. stable@vger.kernel.org
      2. stable@kernel.org

    若要添加版本信息，应使用以下注释样式：

      stable@vger.kernel.org # 版本信息

  **COMMIT_COMMENT_SYMBOL**
    开头为 '#' 的提交日志行会被 Git 忽略为注释。解决此问题只需在日志行前添加一个空格即可。
**COMMIT_MESSAGE**
    补丁缺少提交描述。应添加简短描述以说明补丁所做的更改。
参见：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#describe-your-changes

  **EMAIL_SUBJECT**
    在主题行中命名发现该问题的工具并不是很有用。一个好的主题应该总结补丁带来的更改。
参见：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#describe-your-changes

  **FROM_SIGN_OFF_MISMATCH**
    作者的电子邮件与 Signed-off-by: 行中的电子邮件不匹配。这有时可能是因为电子邮件客户端配置不当导致的。
出现此消息的原因可能包括：

      - 电子邮件名称不匹配
- 电子邮件地址不匹配
- 电子邮件子地址不匹配
邮件中的评论内容不匹配
**MISSING_SIGN_OFF**
    补丁缺少 Signed-off-by 行。应根据开发者的起源证书添加签核行。
更多信息：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#sign-your-work-the-developer-s-certificate-of-origin

  **NO_AUTHOR_SIGN_OFF**
    补丁的作者没有对补丁进行签核。在补丁解释的末尾，需要有一条简单的签核行来表明作者编写了此补丁或拥有将其作为开源补丁传递的权利。
更多信息：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#sign-your-work-the-developer-s-certificate-of-origin

  **DIFF_IN_COMMIT_MSG**
    避免在提交消息中包含差异内容
当尝试应用一个既包含变更日志又包含差异的文件时，这会导致问题，因为 patch(1) 会尝试应用它在变更日志中找到的差异。
更多信息：https://lore.kernel.org/lkml/20150611134006.9df79a893e3636019ad2759e@linux-foundation.org/

  **GERRIT_CHANGE_ID**
    为了被 Gerrit 捕获，提交消息的脚注可能包含一个类似下面的 Change-Id：
      
      Change-Id: Ic8aaa0728a43936cd4c6e1ed590e01ba8f0fbf5b
      Signed-off-by: A. U. Thor <author@example.com>
      
    提交前必须移除 Change-Id 这一行。
**GIT_COMMIT_ID**
    正确引用提交 ID 的方式是：
    commit <12+ 个 sha1 字符> ("<标题行>")
    
    示例可能是：

      Commit e21d2170f36602ae2708 ("video: 删除不必要的
      platform_set_drvdata()") 删除了不必要的
      platform_set_drvdata()，但留下了未使用的变量 "dev"，删除它。
更多信息：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#describe-your-changes

  **BAD_FIXES_TAG**
    Fixes: 标签格式错误或不符合社区约定
如果标签被拆分为多行（例如，在启用了自动换行的电子邮件程序中粘贴时），则可能会发生这种情况。
更多信息：https://www.kernel.org/doc/html/latest/process/submitting-patches.html#describe-your-changes


比较风格
----------

  **ASSIGN_IN_IF**
    不要在 if 条件中使用赋值操作
### 示例：

如果代码写成这样：

```c
if ((foo = bar(...)) < BAZ) {
```

应该重写为：

```c
foo = bar(...);
if (foo < BAZ) {
```

**BOOL_COMPARISON**
将 `A` 与 `true` 和 `false` 进行比较最好写成 `A` 和 `!A`。
参考：[https://lore.kernel.org/lkml/1365563834.27174.12.camel@joe-AO722/](https://lore.kernel.org/lkml/1365563834.27174.12.camel@joe-AO722/)

**COMPARISON_TO_NULL**
以 `(foo == NULL)` 或 `(foo != NULL)` 形式与 `NULL` 比较，最好写成 `(!foo)` 和 `(foo)`。
**CONSTANT_COMPARISON**
在测试中左侧使用常量或大写字母标识符的比较应避免。

### 缩进和换行

**CODE_INDENT**
代码缩进应使用制表符（tab）而不是空格。
除了注释、文档和 Kconfig 文件之外，不应使用空格进行缩进。
参考：[https://www.kernel.org/doc/html/latest/process/coding-style.html#indentation](https://www.kernel.org/doc/html/latest/process/coding-style.html#indentation)

**DEEP_INDENTATION**
使用 6 个或更多制表符的缩进通常表示缩进过多。
建议重构 if/else/for/do/while/switch 语句中的过度缩进。
参考：[https://lore.kernel.org/lkml/1328311239.21255.24.camel@joe2Laptop/](https://lore.kernel.org/lkml/1328311239.21255.24.camel@joe2Laptop/)

**SWITCH_CASE_INDENT_LEVEL**
`switch` 应与 `case` 保持相同的缩进级别。
示例：

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

参考：[https://www.kernel.org/doc/html/latest/process/coding-style.html#indentation](https://www.kernel.org/doc/html/latest/process/coding-style.html#indentation)

**LONG_LINE**
该行已超出指定的最大长度。
要使用不同的最大行长度，可以在调用 `checkpatch` 时添加 `--max-line-length=n` 选项。
早些时候，默认的行长度为80列。提交 bdc48fa11e46 ("checkpatch/编码风格：弃用80列警告") 将限制增加到了100列。这同样不是一个硬性限制，并且在可能的情况下，最好保持在80列以内。
详情参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#breaking-long-lines-and-strings

  **LONG_LINE_STRING**
    一个字符串开始于但超出最大行长度
若要使用不同的最大行长度，可以在调用 checkpatch 时添加 --max-line-length=n 选项。
详情参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#breaking-long-lines-and-strings

  **LONG_LINE_COMMENT**
    一条注释开始于但超出最大行长度
若要使用不同的最大行长度，可以在调用 checkpatch 时添加 --max-line-length=n 选项。
详情参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#breaking-long-lines-and-strings

  **SPLIT_STRING**
    在用户空间中出现并可以被 grep 的被引号包围的字符串不应该跨多行分割。
详情参见: https://lore.kernel.org/lkml/20120203052727.GA15035@leaf/

  **MULTILINE_DEREFERENCE**
    单个指针解除引用标识符分布在多行上，例如：

      结构体标识符->成员[索引]
成员 = <foo>;

    通常难以理解。它很容易导致打字错误，从而使得代码容易出现bug。
如果修复多行指针解除引用会导致80列违规，则要么以更简单的方式重写代码，要么如果指针解除引用标识符的起始部分相同且在多个地方使用，则将其存储在一个临时变量中，并仅在所有这些地方使用该临时变量。例如，如果有两个指针解除引用标识符：

      成员1->成员2->成员3.字段1;
      成员1->成员2->成员3.字段2;

    则将成员1->成员2->成员3部分存储在一个临时变量中。
这样做不仅有助于避免80列违规，而且还通过移除不必要的指针解除引用减少了程序大小。
但如果上述方法都无法适用，则忽略超过80列的限制，因为在一个单行中阅读解除引用的标识符会更容易。

**尾随语句**
    尾随语句（例如，在任何条件语句之后）应该位于下一行。
例如：

      if (x == y) break;

应当写作：

      if (x == y)
              break;

**宏、属性和符号**

  **数组大小**
    对于查找数组中的元素数量，应当优先使用 ARRAY_SIZE(foo) 宏而不是 sizeof(foo)/sizeof(foo[0])
该宏定义在 include/linux/kernel.h 中：

      #define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

  **避免extern**
    在 .h 文件中不需要将函数原型声明为 extern。这是编译器默认假设的，因此没有必要。

**避免使用L前缀**
    应当避免使用以 `.L` 开头的本地符号名，因为这在汇编器中有特殊含义；不会在符号表中生成符号条目。这可能会阻止 `objtool` 生成正确的反向追踪信息。
具有 STB_LOCAL 绑定的符号仍然可以使用，且 `.L` 前缀的本地符号名通常仍可在函数内部使用，但不应使用 `.L` 前缀的本地符号名来标记代码区域的开始或结束位置，如通过 `SYM_CODE_START_LOCAL`/`SYM_CODE_END`。

  **位宏**
    如：1 << <数字> 可能被替换为 BIT(数字)
BIT() 宏是通过 include/linux/bits.h 定义的：

      #define BIT(nr)         (1UL << (nr))

  **常量读取为主**
    当一个变量被打上 __read_mostly 注解时，这是对编译器的一个信号，表明对该变量的访问主要是读取，而写入很少（但并非从不）
const __read_mostly 没有意义，因为常量数据已经是只读的。因此，应当移除 __read_mostly 注解。

**日期与时间**
    通常希望使用相同的工具集编译相同的源代码时输出结果是可重复的，即输出总是完全相同的。
内核不使用 ``__DATE__`` 和 ``__TIME__`` 宏，并且如果使用这些宏会启用警告，因为它们可能导致构建结果的非确定性。
**参见:** https://www.kernel.org/doc/html/latest/kbuild/reproducible-builds.html#timestamps

  **DEFINE_ARCH_HAS**
    使用“ARCH_HAS_xyz”和“ARCH_HAVE_xyz”的模式是错误的。
对于大型概念性特性，应使用Kconfig符号。而对于较小的情况（其中我们有兼容性的回退函数但希望架构能够通过优化版本覆盖它们），我们可以选择使用弱函数（适用于某些情况）或者保护这些函数的符号应该与我们使用的符号相同。
参见: https://lore.kernel.org/lkml/CA+55aFycQ9XJvEOsiM3txHL5bjUc8CeKWJNR_H+MiicaddB42Q@mail.gmail.com/

  **DO_WHILE_MACRO_WITH_TRAILING_SEMICOLON**
    “do {} while(0)” 宏不应该在结尾带有分号。

  **INIT_ATTRIBUTE**
    常量初始化定义应该使用`__initconst`而不是`__initdata`。
同样地，不带`const`的初始化定义需要单独使用`const`。

  **INLINE_LOCATION**
    `inline`关键字应当位于存储类别和类型之间。
例如，下面的段落：

      inline static int example_function(void)
      {
              ..
      }

    应该写作：

      static inline int example_function(void)
      {
              ..
      }

  **MISPLACED_INIT**
    可能会以GCC无法理解的方式（至少不是按照开发者的意图）在变量上使用段落标记：

      static struct __initdata samsung_pll_clock exynos4_plls[nr_plls] = {

    这不会将`exynos4_plls`置于`.initdata`段中。`__initdata`标记几乎可以出现在行中的任何位置，除了紧接在`struct`后面。推荐的位置是在`=`符号之前如果有这个符号，或者在末尾的`;`之前如果没有这个符号。
参见: https://lore.kernel.org/lkml/1377655732.3619.19.camel@joe-AO722/

  **MULTISTATEMENT_MACRO_USE_DO_WHILE**
    具有多个语句的宏应该被包含在一个`do - while`块中。对于以`if`开头的宏也应该是这样，以避免逻辑缺陷：

      #define macrofun(a, b, c)                 \
        do {                                    \
                if (a == 5)                     \
                        do_this(b, c);          \
        } while (0)

    参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#macros-enums-and-rtl

  **PREFER_FALLTHROUGH**
    使用`fallthrough;`伪关键字代替`/* fallthrough */`这样的注释。
### TRAILING_SEMICOLON
宏定义不应该以分号结尾。宏的调用风格应当与函数调用保持一致。
这可以防止任何意外的代码路径：

```c
#define MAC do_something;
```

如果这个宏在 if-else 语句中使用，例如：

```c
if (some_condition)
        MAC;

else
        do_something;
```

那么编译时会出现错误，因为当宏展开后会有两个尾随的分号，导致 else 分支成为孤儿。
参见: https://lore.kernel.org/lkml/1399671106.2912.21.camel@joe-AO725/

### MACRO_ARG_UNUSED
如果函数式宏不使用某个参数，可能会导致构建警告。我们提倡使用静态内联函数来替代此类宏。
例如，对于如下宏：

```c
#define test(a) do { } while (0)
```

会有一个如下的警告：

```c
WARNING: 参数 'a' 在函数式宏中未被使用
```
参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#macros-enums-and-rtl

### SINGLE_STATEMENT_DO_WHILE_MACRO
对于多语句宏，必须使用 do-while 循环来避免不可预测的代码路径。do-while 循环有助于将多个语句组合成一个单一语句，以便函数式宏可以像函数一样使用。
但对于单语句宏，没有必要使用 do-while 循环。虽然语法上是正确的，但使用 do-while 循环是冗余的。因此，对于单语句宏，移除 do-while 循环。
### WEAK_DECLARATION
使用弱声明（如 __attribute__((weak)) 或 __weak）可能会导致非预期的链接缺陷。避免使用它们。

### 函数和变量

#### CAMELCASE
避免使用 CamelCase 标识符。
参见: https://www.kernel.org/doc/html/latest/process/coding-style.html#naming

#### CONST_CONST
使用 `const <type> const *` 通常应写为 `const <type> * const`。

#### CONST_STRUCT
使用 const 通常是好主意。checkpatch 读取一个经常使用的 struct 列表，这些 struct 总是或几乎总是常量。
现有结构体列表可以从以下位置查看：
    `scripts/const_structs.checkpatch`
详情请参见：https://lore.kernel.org/lkml/alpine.DEB.2.10.1608281509480.3321@hadrien/

  **EMBEDDED_FUNCTION_NAME**
    嵌入式函数名称不太适合作为引用，因为重构可能会导致函数重命名。建议使用
    "%s", __func__ 而不是嵌入式函数名称。
请注意，这不适用于 `-f (--file)` checkpatch 选项，
因为它依赖于提供函数名称的补丁上下文。

  **FUNCTION_ARGUMENTS**
    产生此警告的原因可能包括：

      1. 函数声明的参数没有紧随标识符名之后。例如：

           void foo
           (int bar, int baz)

         应该更正为：

           void foo(int bar, int baz)

      2. 函数定义的一些参数没有标识符名称。例如：

           void foo(int)

         所有参数都应具有标识符名称。

  **FUNCTION_WITHOUT_ARGS**
    没有参数的函数声明如：

      int foo()

    应改为：

      int foo(void)

  **GLOBAL_INITIALISERS**
    全局变量不应显式初始化为 0（或 NULL、false 等）。你的编译器（或者更确切地说，你的加载器，它负责将相关部分清零）会自动为你完成这一操作。

  **INITIALISED_STATIC**
    静态变量不应显式初始化为零。你的编译器（或者更确切地说，你的加载器）会自动为你完成这一操作。

  **MULTIPLE_ASSIGNMENTS**
    在一行中进行多次赋值会使代码变得过于复杂。因此，在一行中只对一个变量赋值，这使得代码更具可读性，并有助于避免打字错误。

  **RETURN_PARENTHESES**
    `return` 不是一个函数，因此不需要括号：

      return (bar);

    可以简化为：

      return bar;

权限
--------------

  **DEVICE_ATTR_PERMS**
    在 DEVICE_ATTR 中使用的权限较为特殊。
通常仅使用三种权限 - 0644（读写），0444（只读）
    和 0200（只写）。
### EXECUTE_PERMISSIONS
   源文件没有理由设置为可执行。安全地移除可执行位是合理的。

### EXPORTED_WORLD_WRITABLE
   导出可由全世界写入的`sysfs`/`debugfs`文件通常是一件坏事。如果随意进行这种操作，可能会引入严重的安全漏洞。过去，某些`debugfs`漏洞似乎允许任何本地用户向设备寄存器中写入任意值——这种情况几乎不会带来好的结果。
   参见：https://lore.kernel.org/linux-arm-kernel/cover.1296818921.git.segoon@openwall.com/

### NON_OCTAL_PERMISSIONS
   权限位应该使用四位八进制权限（例如 0700 或 0444）。避免使用其他进制如十进制表示。

### SYMBOLIC_PERMS
   八进制形式的权限位比其符号形式更易于阅读和理解，因为许多命令行工具都采用这种表示法。经验丰富的内核开发者已经使用了数十年的传统Unix权限位，因此他们发现八进制表示法比符号宏更容易理解。例如，与0644相比，S_IWUSR|S_IRUGO更难阅读，这掩盖了开发者的意图而不是使其清晰化。
   参见：https://lore.kernel.org/lkml/CA+55aFw5v23T-zvDZp-MmD_EYxF8WbafwwB59934FV7g21uMGQ@mail.gmail.com/


### Spacing and Brackets
#### ASSIGNMENT_CONTINUATIONS
   分配运算符不应位于新行的开始位置，而应紧跟在上一行的操作数之后。

#### BRACES
   大括号的放置在风格上是不正确的。
**括号位置**

将大括号放在行的最后是最优选的方式，关闭括号放在行的开始部分：

```
if (x is true) {
        we do y
}
```

这一规则适用于所有非函数块。

然而，有一个特殊情况就是函数：它们的大括号在下一行的开始处。因此：

```
int function(int x)
{
        body of function
}
```

请参阅：https://www.kernel.org/doc/html/latest/process/coding-style.html#placing-braces-and-spaces

**BRACKET_SPACE**

禁止在方括号'['之前添加空格。

有一些例外情况：

1. 当左侧有类型时：

   ```
   int [] a;
   ```

2. 在行的开始用于切片初始化器时：

   ```
   [0...10] = 5,
   ```

3. 在花括号内：

   ```
   = { [0...10] = 5 }
   ```

**CONCATENATED_STRING**

连接元素之间应该有空格。
示例：

```
printk(KERN_INFO"bar");
```

应该改为：

```
printk(KERN_INFO "bar");
```

**ELSE_AFTER_BRACE**

`else {` 应该跟在闭合块 `}` 的同一行之后。
请参阅：https://www.kernel.org/doc/html/latest/process/coding-style.html#placing-braces-and-spaces

**LINE_SPACING**

当使用多个空白行时，垂直空间会被浪费，这在编辑器窗口可以显示的行数有限的情况下尤为明显。
请参阅：https://www.kernel.org/doc/html/latest/process/coding-style.html#spaces

**OPEN_BRACE**

大括号应该紧随函数定义在下一行。对于任何非函数块，它应该与最后一个构造在同一行上。
请参阅：https://www.kernel.org/doc/html/latest/process/coding-style.html#placing-braces-and-spaces

**POINTER_LOCATION**

在使用指针数据或返回指针类型的函数时，更优选的是将 '*' 放在数据名称或函数名称旁边，而不是类型名称旁边。
示例：

```
char *linux_banner;
unsigned long long memparse(char *ptr, char **retptr);
char *match_strdup(substring_t *s);
```

请参阅：https://www.kernel.org/doc/html/latest/process/coding-style.html#spaces

**SPACING**

内核源代码中使用的空格样式在内核文档中有详细描述。
请参阅：https://www.kernel.org/doc/html/latest/process/coding-style.html#spaces

**TRAILING_WHITESPACE**

始终应移除尾随空格。
一些编辑器会高亮显示尾随空格，并在编辑文件时造成视觉干扰。
### 不必要的括号 (UNNECESSARY_PARENTHESES)

在以下情况下不需要使用括号：

1. 函数指针调用：

   ```c
   (foo->bar)();
   ```

   可以写为：

   ```c
   foo->bar();
   ```

2. 在 `if` 语句中的比较：

   ```c
   if ((foo->bar) && (foo->baz))
   if ((foo == bar))
   ```

   可以写为：

   ```c
   if (foo->bar && foo->baz)
   if (foo == bar)
   ```

3. 对单个左值取地址/解引用：

   ```c
   &(foo->bar)
   *(foo->bar)
   ```

   可以写为：

   ```c
   &foo->bar
   *foo->bar
   ```

### 循环后的大括号 (WHILE_AFTER_BRACE)

`while` 应该跟在闭合的大括号后面，并且在同一行上：

```c
do {
        ..
} while(something);
```

参考：https://www.kernel.org/doc/html/latest/process/coding-style.html#placing-braces-and-spaces

### 其他

#### 配置描述 (CONFIG_DESCRIPTION)

Kconfig 符号应该有完整的帮助文本来描述它。

#### 腐败的补丁 (CORRUPTED_PATCH)

补丁似乎被破坏了或者某些行被包裹了，请重新生成补丁文件再发送给维护者。

#### CVS 关键字 (CVS_KEYWORD)

自从 Linux 迁移到 Git，CVS 标记就不再使用。因此，不应添加 CVS 风格的关键字（如 `$Id$`、`$Revision$`、`$Log$`）。

#### 默认情况缺少 break (DEFAULT_NO_BREAK)

`switch` 语句中的 `default` 情况有时被写为 `"default:;"`。这可能会导致在 `default` 下方新增的情况出现错误。
应在空的 `default` 语句后添加一个 `break;` 来避免意外的穿透执行。

#### DOS 行结束符 (DOS_LINE_ENDINGS)

对于 DOS 格式的补丁，每行末尾有多余的 `^M` 符号。这些符号应该被移除。

#### 设备树绑定格式 (DT_SCHEMA_BINDING_PATCH)

设备树绑定已从自由格式文本转换为基于 JSON Schema 的格式。
**DT_SPLIT_BINDING_PATCH**
   设备树绑定应该单独成为一个补丁。这是因为
   绑定在逻辑上独立于驱动程序的实现，
   它们有不同的维护者（尽管它们经常
   通过同一棵树应用），并且这会让使用 `git-filter-branch` 创建的仅设备树的提交历史更加清晰。
   参见：https://www.kernel.org/doc/html/latest/devicetree/bindings/submitting-patches.html#i-for-patch-submitters

**EMBEDDED_FILENAME**
   在文件内部嵌入完整的文件路径并不是特别有用，因为文件路径经常会被移动而变得不正确。

**FILE_PATH_CHANGES**
   当文件被添加、移动或删除时，`MAINTAINERS` 文件中的模式可能会不同步或过时。
   因此，在这些情况下可能需要更新 `MAINTAINERS` 文件。

**MEMSET**
   使用 `memset` 看起来是不正确的。这可能是由于参数顺序不当造成的。
   请重新检查其用法。

**NOT_UNIFIED_DIFF**
   补丁文件似乎不是统一差异格式（unified-diff）。请
   在发送给维护者之前重新生成补丁文件。

**PRINTF_0XDECIMAL**
   在十进制输出前加上 `0x` 前缀是有缺陷的，应该予以修正。

**SPDX_LICENSE_TAG**
   源文件缺少或具有不正确的 SPDX 标识符标签。
   Linux 内核要求所有源文件中都包含精确的 SPDX 标识符，并且在内核文档中对此有详细的说明。
   参见：https://www.kernel.org/doc/html/latest/process/license-rules.html

**TYPO_SPELLING**
   有些单词可能拼写错误。考虑审查它们。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
