版权所有 2004 Linus Torvalds
版权所有 2004 Pavel Machek <pavel@ucw.cz>
版权所有 2006 Bob Copeland <me@bobcopeland.com>

Sparse
======

Sparse 是一个用于 C 程序的语义检查器；它可以用来找出内核代码中可能存在的若干问题。请参阅 https://lwn.net/Articles/689907/ 以了解 Sparse 的概览；本文档包含了一些针对内核的 Sparse 特定信息。更多关于 Sparse 的信息，主要是关于其内部结构的，可以在其官方页面 https://sparse.docs.kernel.org 找到。
使用 Sparse 进行类型检查
-----------------------------

"`__bitwise`" 是一个类型属性，因此你需要像这样操作：

        typedef int __bitwise pm_request_t;

        enum pm_request {
                PM_SUSPEND = (__force pm_request_t) 1,
                PM_RESUME = (__force pm_request_t) 2
        };

这使得 `PM_SUSPEND` 和 `PM_RESUME` 成为 "bitwise" 类型的整数（这里之所以使用 "`__force`" 是因为 Sparse 会抱怨对 bitwise 类型的转换，但在这种情况下我们确实需要强制转换）。由于枚举值都是同一类型，现在 "enum pm_request" 也会是该类型。
而在使用 gcc 编译时，所有的 "`__bitwise`"/"`__force`" 标记都会被忽略，最终看起来就像是普通的整数。
坦率地说，你并不一定需要那个枚举。上述内容实际上简化为一种特殊的 "int __bitwise" 类型。
因此更简单的方法是只做如下操作：

        typedef int __bitwise pm_request_t;

        #define PM_SUSPEND ((__force pm_request_t) 1)
        #define PM_RESUME ((__force pm_request_t) 2)

现在你拥有了严格类型检查所需的所有基础设施。
一个小提示：常量整数 "0" 是特殊的。你可以将常量零用作 bitwise 整数类型，而不会引起 Sparse 的警告。
这是因为 "bitwise"（正如其名字所暗示的）设计用于确保 bitwise 类型不被混淆（小端模式与大端模式与 CPU 端模式等），而这里的常量 "0" 确实是特殊的。
使用 Sparse 进行锁检查
------------------------------

以下宏在 gcc 中未定义，在 Sparse 运行期间定义以利用 Sparse 的 "context" 跟踪特性，应用于锁。这些注解告诉 Sparse 在标注函数的入口和出口时锁是否被持有：
`__must_hold` - 指定的锁在函数入口和出口时被持有
翻译为中文：

`__acquires` - 指定的锁在函数退出时持有，但在进入函数时未持有。
`__releases` - 指定的锁在函数进入时持有，但在退出函数时未持有。
如果函数在不持有锁的情况下进入和退出，并在函数内部以平衡的方式获取和释放锁，则无需注释。上述三种注释适用于 Sparse 否则会报告上下文不平衡的情况。

获取 Sparse
--------------

您可以从以下位置获取最新发布的版本的 tarball：
https://www.kernel.org/pub/software/devel/sparse/dist/

或者，您可以使用 git 克隆的方式来获取 Sparse 的最新开发版本：

```shell
git clone git://git.kernel.org/pub/scm/devel/sparse/sparse.git
```

一旦您获得了它，只需执行如下命令：

```shell
make
make install
```

作为普通用户运行，它会在您的 `~/bin` 目录中安装 Sparse。

使用 Sparse
--------------

进行内核编译时添加参数 `make C=1` 来对所有需要重新编译的 C 文件运行 Sparse，或者使用 `make C=2` 不管文件是否需要重新编译都运行 Sparse。后者是在已经构建了整个树后快速检查整棵树的一种方法。
可选的 make 变量 `CF` 可用于向 Sparse 传递参数。构建系统自动向 Sparse 传递 `-Wbitwise` 参数。
请注意，Sparse 定义了预处理器符号 `__CHECKER__`。
