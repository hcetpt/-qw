SPDX 许可证标识符：仅 GPL-2.0

============
UAPI 检查器
============

UAPI 检查器 (`scripts/check-uapi.sh`) 是一个 shell 脚本，用于检查 UAPI 头文件在 Git 仓库中的用户空间向后兼容性。
选项
=======

此部分将描述 `check-uapi.sh` 可以使用的选项。
用法如下：

    check-uapi.sh [-b BASE_REF] [-p PAST_REF] [-j N] [-l ERROR_LOG] [-i] [-q] [-v]

可用的选项如下：

    -b BASE_REF    用于比较的基本 Git 引用。如果不指定或为空，则使用 UAPI 文件中树中的任何脏变更。如果没有脏变更，则使用 HEAD。
    -p PAST_REF    将 BASE_REF 与 PAST_REF 进行比较（例如 `-p v6.1`）。如果不指定或为空，则使用 BASE_REF^1。PAST_REF 必须是 BASE_REF 的祖先。仅检查在 PAST_REF 上存在的头文件的兼容性。
    -j JOBS        并行运行的检查数（默认：CPU 核心数）
    -l ERROR_LOG   将错误日志写入文件（默认：不生成错误日志）
    -i             忽略可能破坏 UAPI 兼容性或可能不会破坏 UAPI 兼容性的模糊变更
    -q             静默操作
    -v             详细操作（打印有关正在检查的每个头文件的更多信息）

环境变量如下：

    ABIDIFF  自定义 abidiff 二进制文件的路径
    CC       C 编译器（默认为 "gcc"）
    ARCH     C 编译器的目标架构（默认为主机架构）

退出代码如下：

    0) 成功
    1) 检测到 ABI 差异
    2) 未满足先决条件

示例
=======

基本用法
-----------

首先，尝试对 UAPI 头文件进行一个显然不会破坏用户空间的更改：

    cat << 'EOF' | patch -l -p1
    --- a/include/uapi/linux/acct.h
    +++ b/include/uapi/linux/acct.h
    @@ -21,7 +21,9 @@
     #include <asm/param.h>
     #include <asm/byteorder.h>

    -/*
    +#define FOO
    +
    +/*
      *  comp_t 是一个 16 位的“浮点”数，具有 3 位以 8 为基数的指数和 13 位的小数部分
* `comp2_t` 是一个24位的数据类型，包含5位的基数2指数和20位的小数部分。
    diff --git a/include/uapi/linux/bpf.h b/include/uapi/linux/bpf.h
    EOF

现在，让我们使用脚本来验证：

    % ./scripts/check-uapi.sh
    正在从脏树安装面向用户的UAPI头文件... OK
    正在从HEAD安装面向用户的UAPI头文件... OK
    在HEAD与脏树之间检查UAPI头文件的变化...
所有912个与x86兼容的UAPI头文件看起来都是向后兼容的

让我们添加另一个可能会破坏用户空间的变化：

    cat << 'EOF' | patch -l -p1
    --- a/include/uapi/linux/bpf.h
    +++ b/include/uapi/linux/bpf.h
    @@ -74,7 +74,7 @@ struct bpf_insn {
            __u8    dst_reg:4;      /* 目标寄存器 */
            __u8    src_reg:4;      /* 源寄存器 */
            __s16   off;            /* 带符号偏移量 */
    -       __s32   imm;            /* 带符号立即常数 */
    +       __u32   imm;            /* 无符号立即常数 */
     };

     /* BPF_MAP_TYPE_LPM_TRIE条目的键 */
    EOF

脚本将捕获这个变化：

    % ./scripts/check-uapi.sh
    正在从脏树安装面向用户的UAPI头文件... OK
    正在从HEAD安装面向用户的UAPI头文件... OK
    在HEAD与脏树之间检查UAPI头文件的变化...
==== 在从HEAD到脏树的include/linux/bpf.h中检测到ABI差异 ====
        [C] 'struct bpf_insn' 发生了变化：
          类型大小没有改变
          1个数据成员变化：
            类型 '__s32 imm' 改变：
              类型定义名称从 __s32 改为 __u32 在 int-ll64.h:27:1
              底层类型 'int' 改变：
                类型名称从 'int' 改为 'unsigned int'
                类型大小没有改变
    ==================================================================================

    错误 - 912个与x86兼容的UAPI头文件中有1个似乎 _不是_ 向后兼容的

在这种情况下，脚本报告类型变化是因为它可能破坏传递负数的用户空间程序。现在，假设你知道没有任何用户空间程序可能在 `imm` 中使用负值，因此在那里改为无符号类型不应该有任何问题。你可以通过 `-i` 标志来忽略用户空间向后兼容性模糊的变化：

    % ./scripts/check-uapi.sh -i
    正在从脏树安装面向用户的UAPI头文件... OK
    正在从HEAD安装面向用户的UAPI头文件... OK
    在HEAD与脏树之间检查UAPI头文件的变化...
所有912个与x86兼容的UAPI头文件看起来都是向后兼容的

现在，让我们做一个类似的变化，这 _将会_ 破坏用户空间：

    cat << 'EOF' | patch -l -p1
    --- a/include/uapi/linux/bpf.h
    +++ b/include/uapi/linux/bpf.h
    @@ -71,8 +71,8 @@ enum {

     struct bpf_insn {
            __u8    code;           /* 操作码 */
    -       __u8    dst_reg:4;      /* 目标寄存器 */
            __u8    src_reg:4;      /* 源寄存器 */
    +       __u8    dst_reg:4;      /* 目标寄存器 */
            __s16   off;            /* 带符号偏移量 */
            __s32   imm;            /* 带符号立即常数 */
     };
    EOF

由于我们正在重新排序现有的结构成员，所以没有歧义，并且即使你传递 `-i`，脚本也会报告破坏情况：

    % ./scripts/check-uapi.sh -i
    正在从脏树安装面向用户的UAPI头文件... OK
    正在从HEAD安装面向用户的UAPI头文件... OK
    在HEAD与脏树之间检查UAPI头文件的变化...
==== 在从HEAD到脏树的include/linux/bpf.h中检测到ABI差异 ====
        [C] 'struct bpf_insn' 发生了变化：
          类型大小没有改变
          2个数据成员变化：
            '__u8 dst_reg' 的偏移量从8（以比特计）变为12（增加4比特）
            '__u8 src_reg' 的偏移量从12（以比特计）变为8（减少4比特）
    ==================================================================================

    错误 - 912个与x86兼容的UAPI头文件中有1个似乎 _不是_ 向后兼容的

让我们提交破坏性的更改，然后再提交一个无辜的更改：

    % git commit -m '破坏UAPI的更改' include/uapi/linux/bpf.h
    [脱离HEAD f758e574663a] 破坏UAPI的更改
     1个文件更改，1个插入（+），1个删除（-）
    % git commit -m '无辜UAPI的更改' include/uapi/linux/acct.h
    [脱离HEAD 2e87df769081] 无辜UAPI的更改
     1个文件更改，3个插入（+），1个删除（-）

现在，让我们再次运行没有任何参数的脚本：

    % ./scripts/check-uapi.sh
    正在从HEAD安装面向用户的UAPI头文件... OK
    正在从HEAD^1安装面向用户的UAPI头文件... OK
    在HEAD^1与HEAD之间检查UAPI头文件的变化...
所有912个与x86兼容的UAPI头文件看起来都是向后兼容的

它没有捕获任何破坏性的更改，因为默认情况下，它只比较 `HEAD` 和 `HEAD^1`。破坏性的更改是在 `HEAD~2` 提交的。如果我们希望搜索范围更进一步，我们必须使用 `-p` 选项来传递不同的过去参考。在这种情况下，让我们向脚本传递 `-p HEAD~2`，以便它检查 `HEAD~2` 和 `HEAD` 之间的UAPI变化：

    % ./scripts/check-uapi.sh -p HEAD~2
    正在从HEAD安装面向用户的UAPI头文件... OK
    正在从HEAD~2安装面向用户的UAPI头文件... OK
    在HEAD~2与HEAD之间检查UAPI头文件的变化...
==== 在从HEAD~2到HEAD的include/linux/bpf.h中检测到ABI差异 ====
        [C] 'struct bpf_insn' 发生了变化：
          类型大小没有改变
          2个数据成员变化：
            '__u8 dst_reg' 的偏移量从8（以比特计）变为12（增加4比特）
            '__u8 src_reg' 的偏移量从12（以比特计）变为8（减少4比特）
    ==============================================================================

    错误 - 912个与x86兼容的UAPI头文件中有1个似乎 _不是_ 向后兼容的

或者，我们也可以用 `-b HEAD~` 运行。这会将基参考设置为 `HEAD~`，然后脚本将其与 `HEAD~^1` 进行比较。
特定架构的头文件
-------------------

考虑以下更改：

    cat << 'EOF' | patch -l -p1
    --- a/arch/arm64/include/uapi/asm/sigcontext.h
    +++ b/arch/arm64/include/uapi/asm/sigcontext.h
    @@ -70,6 +70,7 @@ struct sigcontext {
     struct _aarch64_ctx {
            __u32 magic;
            __u32 size;
    +       __u32 new_var;
     };

     #define FPSIMD_MAGIC   0x46508001
    EOF

这是一个对特定于arm64的UAPI头文件的更改。在这个例子中，我正在从一台带有x86编译器的x86机器上运行脚本，因此，默认情况下，脚本只检查与x86兼容的UAPI头文件：

    % ./scripts/check-uapi.sh
    正在从脏树安装面向用户的UAPI头文件... OK
    正在从HEAD安装面向用户的UAPI头文件... OK
    在HEAD与脏树之间没有应用UAPI头文件的变化

使用x86编译器，我们无法检查 `arch/arm64` 中的头文件，因此脚本甚至不尝试这样做。
如果我们要检查该头文件，我们将不得不使用arm64编译器并相应地设置 `ARCH` ：

    % CC=aarch64-linux-gnu-gcc ARCH=arm64 ./scripts/check-uapi.sh
    正在从脏树安装面向用户的UAPI头文件... OK
    正在从HEAD安装面向用户的UAPI头文件... OK
    在HEAD与脏树之间检查UAPI头文件的变化...
==== 在从HEAD到脏树的include/asm/sigcontext.h中检测到ABI差异 ====
        [C] 'struct _aarch64_ctx' 发生了变化：
          类型大小从64变为96（以比特计）
          1个数据成员插入：
            '__u32 new_var'，偏移量64（以比特计）在sigcontext.h:73:1
        -- 省略 --
        [C] 'struct zt_context' 发生了变化：
          类型大小从128变为160（以比特计）
          2个数据成员变化（1个被过滤）：
            '__u16 nregs' 的偏移量从64变为96（以比特计）（增加32比特）
            '__u16 __reserved[3]' 的偏移量从80变为112（以比特计）（增加32比特）
    =======================================================================================

    错误 - 884个与arm64兼容的UAPI头文件中有1个似乎 _不是_ 向后兼容的

我们可以看到，在为文件正确设置了 `ARCH` 和 `CC` 的情况下，ABI变化被正确地报告。同时请注意，脚本检查的UAPI头文件总数发生了变化。这是因为为arm64平台安装的头文件数量与x86不同。
跨依赖破坏
--------------------------

考虑以下变更：

```shell
cat << 'EOF' | patch -l -p1
--- a/include/uapi/linux/types.h
+++ b/include/uapi/linux/types.h
@@ -52,7 +52,7 @@ typedef __u32 __bitwise __wsum;
     #define __aligned_be64 __be64 __attribute__((aligned(8)))
     #define __aligned_le64 __le64 __attribute__((aligned(8)))

    -typedef unsigned __bitwise __poll_t;
    +typedef unsigned short __bitwise __poll_t;

     #endif /*  __ASSEMBLY__ */
     #endif /* _UAPI_LINUX_TYPES_H */
EOF
```

这里，我们正在 `types.h` 中更改一个 `typedef`。这不会破坏 `types.h` 中的 UAPI，但树中的其他 UAPI 可能会因这个变更而受到影响：

```shell
% ./scripts/check-uapi.sh
安装面向用户的 UAPI 头文件来自未提交的工作树... OK
安装面向用户的 UAPI 头文件来自 HEAD... OK
检查 HEAD 和未提交工作树之间 UAPI 头文件的变化...
==== 发现在从 HEAD 到未提交工作树的 include/linux/eventpoll.h 中存在 ABI 差异 ====
        [C] 'struct epoll_event' 改变：
          类型大小从 96 变为 80（按位计算）
          2 个数据成员变化：
            类型 '__poll_t events' 的变化：
              基础类型 'unsigned int' 改变：
                类型名称从 'unsigned int' 变为 'unsigned short int'
                类型大小从 32 变为 16（按位计算）
            '__u64 data' 的偏移量从 32 变为 16（按位计算）（减少了 16 位）
======================================================================================
include/linux/eventpoll.h 在 HEAD 和未提交工作树之间没有变化..
可能是其中一个它包含的头文件导致了这个错误：
    #include <linux/fcntl.h>
    #include <linux/types.h>
```

请注意，脚本注意到失败的头文件本身没有改变，
因此它假设必须是其中一个被包含的文件导致了破坏。确实，
我们可以看到 `linux/types.h` 被 `eventpoll.h`
UAPI 头文件移除
--------------------

考虑以下变更：

```shell
cat << 'EOF' | patch -l -p1
diff --git a/include/uapi/asm-generic/Kbuild b/include/uapi/asm-generic/Kbuild
index ebb180aac74e..a9c88b0a8b3b 100644
--- a/include/uapi/asm-generic/Kbuild
+++ b/include/uapi/asm-generic/Kbuild
@@ -31,6 +31,6 @@ mandatory-y += stat.h
     mandatory-y += statfs.h
     mandatory-y += swab.h
     mandatory-y += termbits.h
    -mandatory-y += termios.h
    +#mandatory-y += termios.h
     mandatory-y += types.h
     mandatory-y += unistd.h
EOF
```

此脚本将 UAPI 头文件从安装列表中删除。让我们运行脚本：

```shell
% ./scripts/check-uapi.sh
安装面向用户的 UAPI 头文件来自未提交的工作树... OK
安装面向用户的 UAPI 头文件来自 HEAD... OK
检查 HEAD 和未提交工作树之间 UAPI 头文件的变化...
==== UAPI 头文件 include/asm/termios.h 在从 HEAD 到未提交工作树之间被移除 ====

    错误 - 912 个与 x86 兼容的 UAPI 头文件中有 1 个似乎 _不_ 向后兼容

移除 UAPI 头文件被视为破坏性变更，脚本将会将其标记为这样
检查历史 UAPI 兼容性
------------------------------

您可以使用 `-b` 和 `-p` 选项来检查 git 树的不同部分。例如，要检查标签 v6.0 和 v6.1 之间的所有已变更 UAPI 头文件，您将运行：

```shell
% ./scripts/check-uapi.sh -b v6.1 -p v6.0
安装面向用户的 UAPI 头文件来自 v6.1... OK
安装面向用户的 UAPI 头文件来自 v6.0... OK
检查 v6.0 和 v6.1 之间 UAPI 头文件的变化...
--- 省略 ---
    错误 - 907 个与 x86 兼容的 UAPI 头文件中有 37 个似乎 _不_ 向后兼容
```

注意：在 v5.3 之前，脚本所需的一个头文件不存在，
因此脚本无法检查那时之前的变化。
您会注意到脚本检测到许多不向后兼容的 UAPI 变更。考虑到内核 UAPI 应该永远保持稳定，
这是一个令人担忧的结果。这带我们进入下一节：
注意事项
========

UAPI 检查器不对作者意图做任何假设，因此某些类型的变更可能会被标记，即使它们有意破坏 UAPI
重构或废弃时的移除
---------------------------------------

有时非常旧的硬件驱动会被移除，例如在此示例中：

```shell
% ./scripts/check-uapi.sh -b ba47652ba655
安装面向用户的 UAPI 头文件来自 ba47652ba655... OK
安装面向用户的 UAPI 头文件来自 ba47652ba655^1... OK
检查 ba47652ba655^1 和 ba47652ba655 之间 UAPI 头文件的变化...
```
== UAPI头文件 include/linux/meye.h 在 ba47652ba655^1 和 ba47652ba655 之间被移除 ==

    错误 - 910个与x86兼容的UAPI头文件中出现了 _不向后兼容_ 的情况

脚本总是会标记移除操作（即使这些移除是有意为之）
结构扩展
---------

根据内核空间中结构体的处理方式，一个扩展结构的操作可能是非破坏性的。
如果一个结构体作为 ioctl 的参数使用，则内核驱动必须能够处理任何大小的 ioctl 命令。除此之外，在从用户复制数据时你需要小心。例如，假设 `struct foo` 这样变化： 

    struct foo {
        __u64 a; /* 版本1中添加 */
    +   __u32 b; /* 版本2中添加 */
    +   __u32 c; /* 版本2中添加 */
    }

默认情况下，脚本会标记这种变化以供进一步审查：

    [C] 'struct foo' 变化：
      类型大小从 64 改为 128（按位计算）
      插入了2个数据成员：
        '__u32 b'，偏移量 64（按位计算）
        '__u32 c'，偏移量 96（按位计算）

然而，这种改变可能是安全进行的。
如果用户空间程序是基于版本1构建的，它将认为 `sizeof(struct foo)` 是 8。这个大小将会编码在传递给内核的 ioctl 值中。如果内核是基于版本2构建的，它将认为 `sizeof(struct foo)` 是 16。
内核可以使用 `_IOC_SIZE` 宏获取用户传递的 ioctl 代码中编码的大小，然后使用 `copy_struct_from_user()` 来安全地复制值：

    int handle_ioctl(unsigned long cmd, unsigned long arg)
    {
        switch _IOC_NR(cmd) {
        0x01: {
            struct foo my_cmd;  /* 内核中的大小为 16 */

            ret = copy_struct_from_user(&my_cmd, arg, sizeof(struct foo), _IOC_SIZE(cmd));
            ..
`copy_struct_from_user` 将会在内核中清零结构体，并仅复制从用户传入的字节（使新成员保持清零状态）。
如果用户传入更大的结构体，额外的成员会被忽略。
如果你确定内核代码已经考虑到了这种情况，你可以通过给脚本添加 `-i` 参数来忽略这种结构扩展。
灵活数组迁移
--------------

虽然脚本能够处理对现有灵活数组的扩展，但它仍然会标记从1元素假灵活数组到真实灵活数组的初始迁移。例如：

    struct foo {
          __u32 x;
    -     __u32 flex[1]; /* 假灵活数组 */
    +     __u32 flex[];  /* 真实灵活数组 */
    };

这种变化会被脚本标记：

    [C] 'struct foo' 变化：
      类型大小从 64 改为 32（按位计算）
      1个数据成员变化：
        类型 '__u32 flex[1]' 发生变化：
          类型名从 '__u32[1]' 改为 '__u32[]'
          数组类型大小从 32 改为 '未知'
          数组类型子范围1的长度从 1 改为 '未知'

目前没有过滤这类变化的方法，因此请注意可能出现的假阳性。
总结
------

虽然脚本过滤了很多类型的假阳性，但也有可能存在脚本标记了一些不会破坏 UAPI 的变更的情况。同样，也可能存在一些确实破坏用户空间的变更未被脚本标记的情况。虽然该脚本已经在大部分内核历史中运行过，但仍可能存在一些尚未考虑到的边缘情况。
本脚本的目的是用于快速检查，供维护人员或自动化工具使用，而不是作为判断补丁兼容性的终极标准。最好记住：运用你的最佳判断力（理想情况下还包括用户空间的单元测试）来确保你的UAPI变更与旧版本兼容！
