版权所有 2010 Nicolas Palix <npalix@diku.dk>
版权所有 2010 Julia Lawall <julia@diku.dk>
版权所有 2010 Gilles Muller <Gilles.Muller@lip6.fr>

.. 突出显示: 无

.. _开发工具_coccinelle:

Coccinelle
==========

Coccinelle 是一种用于模式匹配和文本转换的工具，它在内核开发中有多种用途，包括应用复杂的、涉及整个树的补丁以及检测有问题的编程模式。
获取 Coccinelle
------------------

内核中包含的语义补丁使用了由 Coccinelle 版本 1.0.0-rc11 及以上提供的功能和选项。
使用早期版本将失败，因为 Coccinelle 文件和 coccicheck 使用的选项名称已被更新。
可以通过许多发行版的包管理器获得 Coccinelle，例如：

- Debian
- Fedora
- Ubuntu
- OpenSUSE
- Arch Linux
- NetBSD
- FreeBSD

一些发行版的包已过时，建议从 Coccinelle 官网 http://coccinelle.lip6.fr/ 获取最新版本。

或者从 Github 获取：

https://github.com/coccinelle/coccinelle

安装完成后，运行以下命令：

```
./autogen
./configure
make
```

作为普通用户运行，并通过以下命令进行安装：

```
sudo make install
```

从源代码构建更详细的安装说明可以在以下位置找到：

https://github.com/coccinelle/coccinelle/blob/master/install.txt

补充文档
--------------------------

对于补充文档，请参阅 wiki：

https://bottest.wiki.kernel.org/coccicheck

wiki 文档始终引用脚本的 linux-next 版本。
对于语义补丁语言 (SmPL) 语法文档，请参阅：

https://coccinelle.gitlabpages.inria.fr/website/docs/main_grammar.html

在 Linux 内核上使用 Coccinelle
------------------------------------

顶级 Makefile 中定义了一个特定于 Coccinelle 的目标。此目标名为 `coccicheck`，并调用 `scripts` 目录中的 `coccicheck` 前端。
定义了四种基本模式：`patch`、`report`、`context` 和 `org`。要使用的模式通过设置 MODE 变量指定，即 `MODE=<mode>`。
- `patch` 在可能的情况下提出修复方案
- `report` 生成如下格式的列表：
  文件:行:列-列: 消息

- `context` 以类似于 diff 的样式突出显示感兴趣的行及其上下文。感兴趣的行用 `-` 表示
- `org` 生成 Emacs 的 Org mode 格式的报告
请注意，并非所有语义补丁都实现了所有模式。为了方便使用 Coccinelle，默认模式为 "report"。
其他两种模式提供了一些这些模式的常见组合：
- `chain` 按上述顺序尝试前面的模式，直到其中一个成功为止
- `rep+ctxt` 依次运行报告模式和上下文模式
应当与选项 C（稍后描述）一起使用，该选项基于文件检查代码
示例
~~~~~~

要为每个语义补丁生成报告，请运行以下命令：

		make coccicheck MODE=report

要生成补丁，请运行：

		make coccicheck MODE=patch

目标 coccicheck 将应用 `scripts/coccinelle` 子目录中可用的所有语义补丁到整个 Linux 内核上。
对于每个语义补丁，都会提出一个提交信息。它提供了由语义补丁检查的问题的描述，并包含对 Coccinelle 的引用。
如同任何静态代码分析工具一样，Coccinelle 会产生误报。因此，必须仔细检查报告，并审查补丁。
要启用详细消息，请设置变量 V=，例如：

   make coccicheck MODE=report V=1

Coccinelle 并行化
-------------------

默认情况下，coccicheck 尽可能地并行运行。要更改并行程度，请设置变量 J=。例如，在 4 个 CPU 上运行：

   make coccicheck MODE=report J=4

从 Coccinelle 1.0.2 版本开始，Coccinelle 使用 Ocaml parmap 进行并行化；如果检测到对此的支持，您将受益于 parmap 并行化。
当 parmap 启用时，coccicheck 通过使用 `--chunksize 1` 参数来启用动态负载平衡。这确保我们一次一次地向线程分配工作，
从而避免了大部分工作仅由少数几个线程完成的情况。有了动态负载平衡，如果某个线程提前完成，我们会继续向它分配更多的工作。
当 parmap 启用时，如果在 Coccinelle 中发生错误，这个错误值会被传播回来，并且 `make coccicheck` 命令的返回值会捕获这个返回值。
使用 Coccinelle 及单个语义补丁
---------------------------------------------

可选的 make 变量 COCCI 可用于检查单个
语义补丁。在这种情况下，变量必须初始化为要应用的
语义补丁的名称。
例如::

    make coccicheck COCCI=<my_SP.cocci> MODE=patch

或者::

    make coccicheck COCCI=<my_SP.cocci> MODE=report


控制哪些文件被 Coccinelle 处理
-----------------------------------

默认情况下，整个内核源代码树都会被检查。
为了将 Coccinelle 应用于特定目录，可以使用 `M=`。
例如，要检查 drivers/net/wireless/ 目录，可以这样写::

    make coccicheck M=drivers/net/wireless/

为了基于文件而非目录来应用 Coccinelle，makefile 中使用的 C 变量
用于选择需要处理的文件。
此变量可用于对整个内核、特定目录或单个文件运行脚本。
例如，要检查 drivers/bluetooth/bfusb.c 文件，将值 1
传递给 C 变量以检查 make 认为需要编译的文件。::

    make C=1 CHECK=scripts/coccicheck drivers/bluetooth/bfusb.o

将值 2 传递给 C 变量以检查文件，无论它们是否需要编译。::

    make C=2 CHECK=scripts/coccicheck drivers/bluetooth/bfusb.o

在这些基于文件的工作模式中，不会显示有关语义补丁的信息，
也不会提出提交消息。
这默认会运行 scripts/coccinelle 中的每个语义补丁。
还可以使用 COCCI 变量仅应用一个语义补丁，如前一节所示。
"report" 模式是默认模式。你可以使用上面解释的 MODE 变量选择其他模式。

调试 Coccinelle SmPL 补丁
-----------------------------

使用 coccicheck 是最好的，因为它在 spatch 命令行中提供了与编译内核时使用的选项相匹配的包含选项。
你可以通过使用 V=1 来了解这些选项是什么；然后
可以手动运行 Coccinelle，并添加调试选项。
或者，您可以通过要求将标准错误重定向到标准错误来调试运行在SmPL补丁上的Coccinelle。默认情况下，标准错误被重定向到`/dev/null`；如果您想捕获标准错误，可以为`coccicheck`指定`DEBUG_FILE="file.txt"`选项。例如：

    rm -f cocci.err
    make coccicheck COCCI=scripts/coccinelle/free/kfree.cocci MODE=report DEBUG_FILE=cocci.err
    cat cocci.err

您可以使用`SPFLAGS`添加调试标志；例如，在调试时，您可能想要向`SPFLAGS`中添加`--profile --show-trying`。例如，您可能希望使用：

    rm -f err.log
    export COCCI=scripts/coccinelle/misc/irqf_oneshot.cocci
    make coccicheck DEBUG_FILE="err.log" MODE=report SPFLAGS="--profile --show-trying" M=./drivers/mfd

现在`err.log`将包含配置文件信息，而标准输出将随着Coccinelle继续处理工作提供一些进度信息。

**注意：**

`DEBUG_FILE`支持仅在使用Coccinelle版本>=1.0.2时可用。
目前，`DEBUG_FILE`支持仅适用于检查文件夹，而不适用于单个文件。这是因为检查一个单独的文件需要调用`spatch`两次，导致`DEBUG_FILE`被设置为相同的值两次，从而引发错误。

**.cocciconfig 支持**
------------------------

Coccinelle支持读取`.cocciconfig`以获取每次启动`spatch`时应使用的默认Coccinelle选项。对于`.cocciconfig`变量的优先级顺序如下：

- 首先处理当前用户的家目录
- 接下来处理从其中调用`spatch`的目录
- 如果使用了`--dir`选项，则最后处理提供的目录

由于`coccicheck`通过`make`运行，它自然会从内核主目录运行；因此，上述第二条规则适用于使用`make coccicheck`时拾取`.cocciconfig`。

`make coccicheck`还支持使用`M=`目标。如果您不提供任何`M=`目标，则假定您要针对整个内核。
内核的`coccicheck`脚本包含：

    if [ "$KBUILD_EXTMOD" = "" ] ; then
        OPTIONS="--dir $srctree $COCCIINCLUDE"
    else
        OPTIONS="--dir $KBUILD_EXTMOD $COCCIINCLUDE"
    fi

当使用明确带有`M=`的目标时，`KBUILD_EXTMOD`会被设置。在这两种情况下都使用了`spatch`的`--dir`参数，因此无论是否使用`M=`，第三条规则都适用，并且当使用`M=`时，目标目录可以有自己的`.cocciconfig`文件。当未将`M=`作为参数传递给`coccicheck`时，目标目录与调用`spatch`的目录相同。

如果不使用内核的`coccicheck`目标，请保持上述`.cocciconfig`读取的优先级顺序逻辑。如果使用内核的`coccicheck`目标，则使用`SPFLAGS`覆盖内核的任何`.cocciconfig`设置。

我们通过一套针对Linux的合理默认选项帮助Coccinelle在Linux上使用我们自己的Linux `.cocciconfig`。这提示Coccinelle可以使用`git grep`查询通过coccigrep进行git搜索。目前200秒的超时应该足够。

Coccinelle在读取`.cocciconfig`时所选择的选项不会作为参数出现在系统上运行的`spatch`进程中。要确认Coccinelle将使用的选项，请运行：

      spatch --print-options-only

您可以通过使用`SPFLAGS`覆盖自己的索引选项。请注意，当存在冲突选项时，Coccinelle会优先考虑最后传递的选项。使用`.cocciconfig`可以使用idutils，但是考虑到Coccinelle遵循的优先级顺序，由于内核现在携带了自己的`.cocciconfig`，如果需要使用idutils，您需要使用`SPFLAGS`。有关如何使用idutils的更多详细信息，请参阅下面的“附加标志”部分。

**附加标志**
---------------

可以通过`SPFLAGS`变量向`spatch`传递附加标志。这是因为Coccinelle在选项发生冲突时尊重最后给出的标志。例如：

    make SPFLAGS=--use-glimpse coccicheck

Coccinelle也支持idutils，但需要Coccinelle版本>=1.0.6。
当没有指定 ID 文件时，Coccinelle 假定你的 ID 数据库文件位于内核顶层的 `.id-utils.index` 文件中。Coccinelle 自带了一个脚本 `scripts/idutils_index.sh`，用于创建数据库：

```bash
mkid -i C --output .id-utils.index
```

如果你有其他的数据库文件名，也可以通过符号链接使用这个名字：

```bash
make SPFLAGS=--use-idutils coccicheck
```

或者，你可以显式地指定数据库文件名，例如：

```bash
make SPFLAGS="--use-idutils /full-path/to/ID" coccicheck
```

要了解更多关于 spatch 的选项，请查看 `spatch --help`。
需要注意的是，`--use-glimpse` 和 `--use-idutils` 选项需要外部工具来对代码进行索引。因此，默认情况下这些选项都是不激活的。但是，通过使用其中一个工具对代码进行索引，并根据使用的 cocci 文件，spatch 可能会更快地处理整个代码库。

### SmPL 补丁的特定选项

SmPL 补丁可以有自己的选项需求。SmPL 补丁特定的选项可以通过在 SmPL 补丁的顶部提供它们来指定，例如：

```plaintext
// Options: --no-includes --include-headers
```

### SmPL 补丁 Coccinelle 需求

随着 Coccinelle 功能的增加，一些更高级的 SmPL 补丁可能需要更新版本的 Coccinelle。如果一个 SmPL 补丁要求最低版本的 Coccinelle，则可以按如下方式指定，例如如果要求至少 Coccinelle >= 1.0.5：

```plaintext
// Requires: 1.0.5
```

### 提交新的语义补丁

内核开发者可以提议并提交新的语义补丁。为了清晰起见，它们应该组织在 `scripts/coccinelle/` 子目录中。

### “报告”模式的详细描述

“报告”生成如下格式的列表：

```plaintext
file:line:column-column: message
```

#### 示例

运行以下命令：

```bash
make coccicheck MODE=report COCCI=scripts/coccinelle/api/err_cast.cocci
```

将执行 SmPL 脚本的以下部分：

```plaintext
<smpl>
@r depends on !context && !patch && (org || report)@
expression x;
position p;
@@

  ERR_PTR@p(PTR_ERR(x))

@script:python depends on report@
p << r.p;
x << r.x;
@@

msg="ERR_CAST can be used with %s" % (x)
coccilib.report.print_report(p[0], msg)
</smpl>
```

这个 SmPL 摘要会在标准输出上生成条目，如下面所示：

```plaintext
/home/user/linux/crypto/ctr.c:188:9-16: ERR_CAST can be used with alg
/home/user/linux/crypto/authenc.c:619:9-16: ERR_CAST can be used with auth
/home/user/linux/crypto/xts.c:227:9-16: ERR_CAST can be used with alg
```

### “补丁”模式的详细描述

当“补丁”模式可用时，它为每个发现的问题提供修复建议。

#### 示例

运行以下命令：

```bash
make coccicheck MODE=patch COCCI=scripts/coccinelle/api/err_cast.cocci
```

将执行 SmPL 脚本的以下部分：

```plaintext
<smpl>
@ depends on !context && patch && !org && !report @
expression x;
@@

- ERR_PTR(PTR_ERR(x))
+ ERR_CAST(x)
</smpl>
```

这个 SmPL 摘要会在标准输出上生成补丁块，如下面所示：

```plaintext
diff -u -p a/crypto/ctr.c b/crypto/ctr.c
--- a/crypto/ctr.c 2010-05-26 10:49:38.000000000 +0200
+++ b/crypto/ctr.c 2010-06-03 23:44:49.000000000 +0200
@@ -185,7 +185,7 @@ static struct crypto_instance *crypto_ct
 	alg = crypto_attr_alg(tb[1], CRYPTO_ALG_TYPE_CIPHER,
 				  CRYPTO_ALG_TYPE_MASK);
 	if (IS_ERR(alg))
-		return ERR_PTR(PTR_ERR(alg));
+		return ERR_CAST(alg);

 	/* Block size must be >= 4 bytes. */
 	err = -EINVAL;
```

### “上下文”模式的详细描述

“上下文”以类似 diff 的样式突出显示感兴趣的行及其上下文

**注意**：生成的类似 diff 的输出并不是可应用的补丁。“上下文”模式的目的是突出显示重要的行（用减号 `-` 标注），并给出一些周围的上下文行。此输出可以在 Emacs 的 diff 模式中用来审查代码。

#### 示例

运行以下命令：

```bash
make coccicheck MODE=context COCCI=scripts/coccinelle/api/err_cast.cocci
```

将执行 SmPL 脚本的以下部分：

```plaintext
<smpl>
@ depends on context && !patch && !org && !report@
expression x;
@@

* ERR_PTR(PTR_ERR(x))
</smpl>
```

这个 SmPL 摘要会在标准输出上生成 diff 块，如下面所示：

```plaintext
diff -u -p /home/user/linux/crypto/ctr.c /tmp/nothing
--- /home/user/linux/crypto/ctr.c	2010-05-26 10:49:38.000000000 +0200
+++ /tmp/nothing
@@ -185,7 +185,6 @@ static struct crypto_instance *crypto_ct
 	alg = crypto_attr_alg(tb[1], CRYPTO_ALG_TYPE_CIPHER,
 				  CRYPTO_ALG_TYPE_MASK);
 	if (IS_ERR(alg))
-		return ERR_PTR(PTR_ERR(alg));

 	/* Block size must be >= 4 bytes. */
 	err = -EINVAL;
```

### “Org”模式的详细描述

“Org”生成 Emacs 的 Org 模式格式的报告。

#### 示例

运行以下命令：

```bash
make coccicheck MODE=org COCCI=scripts/coccinelle/api/err_cast.cocci
```

将执行 SmPL 脚本的以下部分：

```plaintext
<smpl>
@r depends on !context && !patch && (org || report)@
expression x;
position p;
@@

  ERR_PTR@p(PTR_ERR(x))

@script:python depends on org@
p << r.p;
x << r.x;
@@

msg="ERR_CAST can be used with %s" % (x)
msg_safe=msg.replace("[","@(").replace("]",")")
coccilib.org.print_todo(p[0], msg_safe)
</smpl>
```

这个 SmPL 摘要会在标准输出上生成 Org 条目，如下面所示：

```plaintext
* TODO [[view:/home/user/linux/crypto/ctr.c::face=ovl-face1::linb=188::colb=9::cole=16][ERR_CAST can be used with alg]]
* TODO [[view:/home/user/linux/crypto/authenc.c::face=ovl-face1::linb=619::colb=9::cole=16][ERR_CAST can be used with auth]]
* TODO [[view:/home/user/linux/crypto/xts.c::face=ovl-face1::linb=227::colb=9::cole=16][ERR_CAST can be used with alg]]
```
