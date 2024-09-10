SPDX 许可证标识符: GPL-2.0

====================
文件系统挂载 API
====================

.. 目录

 (1) 概览
(2) 文件系统上下文
(3) 文件系统上下文操作
(4) 文件系统上下文安全
(5) VFS 文件系统上下文 API
(6) 超级块创建助手
(7) 参数描述
(8) 参数辅助函数
概览
========

新挂载点的创建现在需要通过多步骤进行：

 (1) 创建一个文件系统上下文
(2) 解析参数并将其附加到上下文中。参数预期从用户空间单独传递，但也可以处理遗留的二进制参数
(3) 验证并预处理上下文
(4) 获取或创建一个超级块（superblock）和可挂载的根
(5) 执行挂载操作
(6) 返回一个附加到上下文中的错误信息
(7) 销毁上下文

为了支持这一点，`file_system_type` 结构体增加了两个新字段：

```c
int (*init_fs_context)(struct fs_context *fc);
const struct fs_parameter_description *parameters;
```

第一个函数被调用来设置文件系统的特定部分，包括额外的空间。第二个指针指向参数描述，在注册时进行验证，并供未来的系统调用查询。

请注意，安全初始化是在调用文件系统之后进行的，以便首先调整命名空间。

文件系统上下文
===============

超级块的创建和重新配置由文件系统上下文控制。这通过 `fs_context` 结构体来表示：

```c
struct fs_context {
    const struct fs_context_operations *ops;
    struct file_system_type *fs_type;
    void *fs_private;
    struct dentry *root;
    struct user_namespace *user_ns;
    struct net *net_ns;
    const struct cred *cred;
    char *source;
    char *subtype;
    void *security;
    void *s_fs_info;
    unsigned int sb_flags;
    unsigned int sb_flags_mask;
    unsigned int s_iflags;
    enum fs_context_purpose purpose : 8;
    ..
};
```

`fs_context` 字段如下：

- `const struct fs_context_operations *ops`

  这些是可以在文件系统上下文中执行的操作（见下文）。这个字段必须由 `file_system_type` 操作 `->init_fs_context()` 设置。

- `struct file_system_type *fs_type`

  指向正在构建或重新配置的文件系统的 `file_system_type`。这保留了类型所有者的引用。
* ::

       void *fs_private

     指向文件系统的私有数据的指针。这是文件系统需要存储其解析的任何选项的地方。

* ::

       struct dentry *root

     指向可挂载树（间接地，也包括该超级块）根目录的指针。这个字段由 `->get_tree()` 操作填充。如果设置了这个字段，则必须同时持有 `root->d_sb` 的活动引用。

* ::

       struct user_namespace *user_ns
       struct net *net_ns

     这些是调用进程使用的命名空间的一个子集。它们对每个命名空间保持引用。订阅的命名空间可能被文件系统替换以反映其他来源，例如自动挂载时父挂载点的超级块。

* ::

       const struct cred *cred

     挂载者的凭证。这保留了对凭证的引用。

* ::

       char *source

     指定源设备。它可以是一个块设备（例如 `/dev/sda1`），或者更复杂一些的东西，如 NFS 所需的 `host:/path`。

* ::

       char *subtype

     这是一个字符串，将被添加到 `/proc/mounts` 中显示的类型中以对其进行限定（FUSE 使用）。如果需要，文件系统可以设置这个值。

* ::

       void *security

     LSMs 可以在这里挂载超级块的安全数据。相关的安全操作在下面描述。

* ::

       void *s_fs_info

     新超级块提议的 `s_fs_info`，由 `sget_fc()` 在超级块中设置。这可用于区分超级块。

* ::

       unsigned int sb_flags
       unsigned int sb_flags_mask

     要在 `super_block::s_flags` 中设置/清除的 `SB_*` 标志位。

* ::

       unsigned int s_iflags

     当创建超级块时，这些标志位将与 `s->s_iflags` 进行按位或运算。
```
:: 

       enum fs_context_purpose

这表示上下文的用途。可用的值包括：

==========================	======================================
FS_CONTEXT_FOR_MOUNT		用于显式挂载的新超级块
FS_CONTEXT_FOR_SUBMOUNT		现有挂载的新自动子挂载
FS_CONTEXT_FOR_RECONFIGURE	更改现有的挂载
==========================	======================================

挂载上下文通过调用 vfs_new_fs_context() 或 vfs_dup_fs_context() 创建，并通过 put_fs_context() 销毁。请注意，该结构没有引用计数。
VFS、安全性和文件系统挂载选项分别通过 vfs_parse_mount_option() 设置。旧版 mount(2) 系统调用作为一页数据提供的选项可以通过 generic_parse_monolithic() 解析。
在挂载时，允许文件系统从任何指针获取数据并将其附加到超级块（或其他地方），前提是它在挂载上下文中清空该指针。
文件系统还允许分配资源并通过挂载上下文将其固定。例如，NFS 可能会固定相应的协议版本模块。

文件系统上下文操作
==================

文件系统上下文指向一个操作表：
::
    struct fs_context_operations {
        void (*free)(struct fs_context *fc);
        int (*dup)(struct fs_context *fc, struct fs_context *src_fc);
        int (*parse_param)(struct fs_context *fc, struct fs_parameter *param);
        int (*parse_monolithic)(struct fs_context *fc, void *data);
        int (*get_tree)(struct fs_context *fc);
        int (*reconfigure)(struct fs_context *fc);
    };

这些操作由挂载过程的不同阶段调用来管理文件系统上下文。它们如下：

   * ::

        void (*free)(struct fs_context *fc);

当上下文被销毁时，调用此函数来清理文件系统特定部分的文件系统上下文。它应该意识到上下文的部分可能已经被 ->get_tree() 移除并置为 NULL。
* ::

        int (*dup)(struct fs_context *fc, struct fs_context *src_fc);

当文件系统上下文被复制时，调用此函数来复制文件系统的私有数据。如果无法完成复制，则可以返回错误。
.. Warning::

         即使此操作失败，put_fs_context() 也会立即被调用，因此 ->dup() 必须确保文件系统的私有数据对 ->free() 是安全的。
* ::

        int (*parse_param)(struct fs_context *fc, struct fs_parameter *param);

当参数被添加到文件系统上下文时调用此函数。param 指向键名和可能的值对象。VFS 特定的选项已经被过滤，并且在上下文中更新了 fc->sb_flags。
安全选项也被过滤，并且 fc->security 已经更新。
参数可以通过 fs_parse() 和 fs_lookup_param() 进行解析。请注意，源（来源）以名为 "source" 的参数形式呈现。
```
如果成功，应返回0或在出现错误时返回一个负的错误代码。
```
int (*parse_monolithic)(struct fs_context *fc, void *data);
```

当调用mount(2)系统调用时被调用，以一次性传递整个数据页面。如果预期这只是由逗号分隔的“key[=val]”项组成的列表，则可以将其设置为NULL。
返回值与`->parse_param()`相同。
如果文件系统（例如NFS）需要先检查数据，然后发现这是标准的键值列表，则可以将其传递给`generic_parse_monolithic()`处理。

```
int (*get_tree)(struct fs_context *fc);
```

被调用来获取或创建可挂载的根目录和超级块，使用存储在文件系统上下文中的信息（重新配置通过不同的向量进行）。它可以将任何所需的资源从文件系统上下文分离并转移到它创建的超级块中。
成功时，应将`fc->root`设置为可挂载的根目录并返回0。在出现错误的情况下，应返回一个负的错误代码。
对于基于用户空间的上下文，阶段将被设置为仅允许在任何特定上下文中调用一次。

```
int (*reconfigure)(struct fs_context *fc);
```

被调用来使用存储在文件系统上下文中的信息对超级块进行重新配置。它可以将任何所需的资源从文件系统上下文分离并转移到超级块。超级块可以从`fc->root->d_sb`找到。
成功时，应返回0。在出现错误的情况下，应返回一个负的错误代码。
**注意**：`reconfigure`旨在作为`remount_fs`的替代品。
文件系统上下文安全性
===========================

文件系统上下文包含一个安全指针，LSM（Linux 安全模块）可以使用该指针来构建要挂载的超级块的安全上下文。新挂载代码为此目的使用了以下几种操作：

   * ::

	int security_fs_context_alloc(struct fs_context *fc, struct dentry *reference);

     调用此函数以初始化 fc->security（预设为 NULL）并分配所需资源。成功时应返回 0，失败时返回负错误码。
     如果上下文是为超级块重新配置（FS_CONTEXT_FOR_RECONFIGURE）创建的，则 reference 将非空，并且表示要重新配置的超级块的根目录项。在子挂载（FS_CONTEXT_FOR_SUBMOUNT）的情况下，它也非空，并表示自动挂载点。
* ::

	int security_fs_context_dup(struct fs_context *fc, struct fs_context *src_fc);

     调用此函数以初始化 fc->security（预设为 NULL）并分配所需资源。原始文件系统上下文由 src_fc 指向，并可用于参考。成功时应返回 0，失败时返回负错误码。
* ::

	void security_fs_context_free(struct fs_context *fc);

     调用此函数以清理与 fc->security 相关的内容。注意，在 get_tree 过程中，内容可能已转移到超级块，并清除了指针。
* ::

	int security_fs_context_parse_param(struct fs_context *fc, struct fs_parameter *param);

     对每个挂载参数（包括源）调用此函数。参数与 ->parse_param() 方法相同。如果参数应传递给文件系统，则返回 0；如果参数应丢弃，则返回 1；如果参数应被拒绝，则返回错误。
     param 所指向的值可以被修改（如果是字符串）或被“窃取”（只要将值指针置为空）。如果被窃取，必须返回 1 以防止其传递给文件系统。
* ::

	int security_fs_context_validate(struct fs_context *fc);

     在解析所有选项后调用此函数以验证整个集合并进行必要的分配，以便使 security_sb_get_tree() 和 security_sb_reconfigure() 不太可能失败。应返回 0 或负错误码。
     在重新配置的情况下，目标超级块可通过 fc->root 访问。
* ::

	int security_sb_get_tree(struct fs_context *fc);

     在挂载过程中调用此函数以验证指定的超级块是否允许挂载并将安全数据转移过去。应返回 0 或负错误码。
* ::

	void security_sb_reconfigure(struct fs_context *fc);

     调用此函数以应用任何对 LSM 上下文的重新配置。它不应失败。错误检查和资源分配必须提前通过参数解析和验证钩子完成。
```c
int security_sb_mountpoint(struct fs_context *fc,
                           struct path *mountpoint,
                           unsigned int mnt_flags);
```

在挂载过程中调用，以验证附加到上下文的根目录项是否允许附加到指定的挂载点。成功时应返回0，失败时返回负的错误代码。

VFS 文件系统上下文 API
==========================

有四个操作用于创建文件系统上下文，一个用于销毁上下文：

```c
struct fs_context *fs_context_for_mount(struct file_system_type *fs_type,
                                        unsigned int sb_flags);
```

为设置新挂载分配文件系统上下文，无论是使用新的超级块还是共享现有的超级块。这设置了超级块标志，初始化安全机制，并调用 `fs_type->init_fs_context()` 来初始化文件系统的私有数据。`fs_type` 指定了将要管理该上下文的文件系统类型，而 `sb_flags` 预设了存储在其中的超级块标志。

```c
struct fs_context *fs_context_for_reconfigure(
    struct dentry *dentry,
    unsigned int sb_flags,
    unsigned int sb_flags_mask);
```

为重新配置现有超级块分配文件系统上下文。`dentry` 提供了要配置的超级块的引用。`sb_flags` 和 `sb_flags_mask` 指示需要更改哪些超级块标志以及更改为多少。

```c
struct fs_context *fs_context_for_submount(
    struct file_system_type *fs_type,
    struct dentry *reference);
```

为创建自动挂载点或其他派生超级块的新挂载分配文件系统上下文。`fs_type` 指定了将要管理该上下文的文件系统类型，而引用目录项提供了参数。命名空间从引用目录项的超级块传播。

注意，不要求引用目录项与 `fs_type` 具有相同的文件系统类型。

```c
struct fs_context *vfs_dup_fs_context(struct fs_context *src_fc);
```

复制文件系统上下文，复制其中记录的任何选项，并复制或另外引用持有的任何资源。此功能可用于文件系统必须在一个挂载内获取另一个挂载的情况，例如 NFS4 通过内部挂载目标服务器的根，然后进行私有的路径遍历到目标目录。新上下文的目的继承自旧上下文。

```c
void put_fs_context(struct fs_context *fc);
```

销毁文件系统上下文，释放其持有的任何资源。这会调用 `->free()` 操作。此函数旨在由创建文件系统上下文的任何人调用。
警告：

    文件系统上下文不会被引用计数，因此这会导致无条件的销毁。
在上述所有操作中，除了put操作外，返回的是一个挂载上下文指针或一个负的错误代码。
对于其余的操作，如果发生错误，将返回一个负的错误代码。
* ::

        int vfs_parse_fs_param(struct fs_context *fc,
			       struct fs_parameter *param);

     向文件系统上下文提供一个挂载参数。这包括指定源/设备，该设备作为"source"参数指定（如果文件系统支持多次指定，则可以多次指定）。
param指定了参数键名和值。参数首先会检查是否对应于一个标准挂载标志（在这种情况下，它将用于设置一个SB_xxx标志并被消耗）或安全选项（在这种情况下，LSM会消耗它），然后再传递给文件系统。
参数值是类型化的，可以是以下之一：

	====================		=============================
	fs_value_is_flag		参数没有给定值
	fs_value_is_string		值是一个字符串
	fs_value_is_blob		值是一个二进制块
	fs_value_is_filename		值是一个文件名* + dirfd
	fs_value_is_file		值是一个打开的文件（file*）
	====================		=============================

     如果有值，这个值会被存储在结构体中的union的一个成员中，即param->{string, blob, name, file}。请注意，函数可能会窃取并清除指针，但随后将负责处理该对象。
* ::

       int vfs_parse_fs_string(struct fs_context *fc, const char *key,
			       const char *value, size_t v_size);

     vfs_parse_fs_param()的包装器，复制传入的值字符串。
* ::

       int generic_parse_monolithic(struct fs_context *fc, void *data);

     解析sys_mount()数据页，假设其形式为由逗号分隔的键[=值]选项组成的文本列表。列表中的每一项都会传递给vfs_mount_option()。当->parse_monolithic()方法为NULL时，这是默认行为。
* ::

       int vfs_get_tree(struct fs_context *fc);

     使用文件系统上下文中的参数来获取或创建可挂载的根目录和超级块。这会调用->get_tree()方法。
* ::

       struct vfsmount *vfs_create_mount(struct fs_context *fc);

     根据指定的文件系统上下文中的参数创建一个挂载点。
请注意，这不会将挂载点附加到任何地方。

超级块创建助手
===========================

有许多VFS助手可供文件系统使用，用于创建或查找超级块。
* ::

       struct super_block *
       sget_fc(struct fs_context *fc,
	       int (*test)(struct super_block *sb, struct fs_context *fc),
	       int (*set)(struct super_block *sb, struct fs_context *fc));

     这是核心例程。如果 `test` 非 NULL，则它会根据 `fs_context` 中的条件搜索现有的超级块，使用 `test` 函数进行匹配。如果没有找到匹配项，则创建一个新的超级块，并调用 `set` 函数来设置它。
在调用 `set` 函数之前，`fc->s_fs_info` 将被转移到 `sb->s_fs_info` —— 如果 `set` 返回成功（即返回 0），则 `fc->s_fs_info` 将被清空。
以下助手都包装了 `sget_fc()`：

	(1) `vfs_get_single_super`

	    系统中只能存在一个这样的超级块。任何进一步尝试获取新的超级块都将得到这个超级块（并且忽略任何参数差异）。
(2) `vfs_get_keyed_super`

	    可能存在多个此类超级块，并且它们通过其 `s_fs_info` 指针键控（例如，这可能指代命名空间）。
(3) `vfs_get_independent_super`

	    可能存在多个独立的此类超级块。此函数永远不会匹配现有的超级块，而总是创建一个新的超级块。

参数描述
=====================

参数使用在 `linux/fs_parser.h` 中定义的结构进行描述。
有一个核心描述结构，将所有内容链接在一起::

    struct fs_parameter_description {
        const struct fs_parameter_spec *specs;
        const struct fs_parameter_enum *enums;
    };

例如::

    enum {
        Opt_autocell,
        Opt_bar,
        Opt_dyn,
        Opt_foo,
        Opt_source,
    };

    static const struct fs_parameter_description afs_fs_parameters = {
        .specs = afs_param_specs,
        .enums = afs_param_enums,
    };

成员如下：

 (1) ::

       const struct fs_parameter_specification *specs;

     参数规范表，以空条目终止，其中条目的类型为::

    struct fs_parameter_spec {
        const char *name;
        u8 opt;
        enum fs_parameter_type type:8;
        unsigned short flags;
    };

     字段 `name` 是一个字符串，用于精确匹配参数键（没有通配符、模式且不区分大小写），字段 `opt` 是在成功匹配的情况下 `fs_parser()` 函数将返回的值。
字段 `type` 表示所需的值类型，必须是以下之一：

	=======================	=======================	=====================
	类型名称		期望的值		结果存储位置
	=======================	=======================	=====================
	fs_param_is_flag	无值		不适用
	fs_param_is_bool	布尔值		result->boolean
	fs_param_is_u32		32位无符号整数	result->uint_32
	fs_param_is_u32_octal	32位八进制整数	result->uint_32
	fs_param_is_u32_hex	32位十六进制整数	result->uint_32
	fs_param_is_s32		32位有符号整数	result->int_32
	fs_param_is_u64		64位无符号整数	result->uint_64
	fs_param_is_enum	枚举值名称	result->uint_32
	fs_param_is_string	任意字符串	param->string
	fs_param_is_blob	二进制数据块	param->blob
	fs_param_is_blockdev	块设备路径		* 需要查找
	fs_param_is_path	路径			* 需要查找
	fs_param_is_fd		文件描述符	result->int_32
	fs_param_is_uid		用户ID (u32)           result->uid
	fs_param_is_gid		组ID (u32)          result->gid
	=======================	=======================	=====================

     注意，如果值类型为 `fs_param_is_bool`，`fs_parse()` 将尝试将任何字符串值与 "0"、"1"、"no"、"yes"、"false"、"true" 进行匹配。
每个参数也可以用'标志'进行限定：

| 标志                           | 描述                                                                 |
|-------------------------------|----------------------------------------------------------------------|
| fs_param_v_optional           | 值是可选的                                                            |
| fs_param_neg_with_no          | 如果键以"no"开头，则设置结果的取反标志                                 |
| fs_param_neg_with_empty       | 如果值为""，则设置结果的取反标志                                       |
| fs_param_deprecated           | 参数已弃用                                                             |

这些标志被一系列方便的宏所封装：

| 宏                            | 指定的内容                                                            |
|-------------------------------|-----------------------------------------------------------------------|
| fsparam_flag()                | fs_param_is_flag                                                      |
| fsparam_flag_no()             | fs_param_is_flag, fs_param_neg_with_no                                |
| fsparam_bool()                | fs_param_is_bool                                                      |
| fsparam_u32()                 | fs_param_is_u32                                                       |
| fsparam_u32oct()              | fs_param_is_u32_octal                                                 |
| fsparam_u32hex()              | fs_param_is_u32_hex                                                   |
| fsparam_s32()                 | fs_param_is_s32                                                       |
| fsparam_u64()                 | fs_param_is_u64                                                       |
| fsparam_enum()                | fs_param_is_enum                                                      |
| fsparam_string()              | fs_param_is_string                                                    |
| fsparam_blob()                | fs_param_is_blob                                                      |
| fsparam_bdev()                | fs_param_is_blockdev                                                  |
| fsparam_path()                | fs_param_is_path                                                      |
| fsparam_fd()                  | fs_param_is_fd                                                        |
| fsparam_uid()                 | fs_param_is_uid                                                       |
| fsparam_gid()                 | fs_param_is_gid                                                       |

所有这些宏都接受两个参数：名称字符串和选项编号。例如：

```c
static const struct fs_parameter_spec afs_param_specs[] = {
    fsparam_flag("autocell", Opt_autocell),
    fsparam_flag("dyn", Opt_dyn),
    fsparam_string("source", Opt_source),
    fsparam_flag_no("foo", Opt_foo),
    {}
};
```

此外还提供了一个扩展宏 `__fsparam()`，它接受额外的一对参数来指定类型和标志，适用于不匹配上述宏的情况。

```c
const struct fs_parameter_enum *enums;
```

枚举值名称到整数映射表，以空条目终止。其类型如下：

```c
struct fs_parameter_enum {
    u8 opt;
    char name[14];
    u8 value;
};
```

数组是一个未排序的列表，包含 { 参数ID, 名称 } 键值元素，表示要映射的值，例如：

```c
static const struct fs_parameter_enum afs_param_enums[] = {
    { Opt_bar, "x", 1 },
    { Opt_bar, "y", 23 },
    { Opt_bar, "z", 42 },
};
```

如果遇到类型为 `fs_param_is_enum` 的参数，`fs_parse()` 将尝试在枚举表中查找该值，并将结果存储在解析结果中。

解析器应通过文件系统类型的解析器指针指向，这将在注册时提供验证（如果 CONFIG_VALIDATE_FS_PARSER=y），并允许用户空间使用 `fsinfo()` 系统调用来查询描述信息。

参数辅助函数
=============

提供了多个辅助函数来帮助文件系统或 LSM 处理给定的参数。

```c
int lookup_constant(const struct constant_table tbl[],
                    const char *name, int not_found);
```

根据名称在名称到整数映射表中查找常量。表是一个以下类型的元素数组：

```c
struct constant_table {
    const char *name;
    int value;
};
```

如果找到匹配项，则返回相应的值；如果没有找到匹配项，则返回 `not_found` 值。

```c
bool validate_constant_table(const struct constant_table *tbl,
                             size_t tbl_size,
                             int low, int high, int special);
```

验证一个常量表。检查所有元素是否适当排序、没有重复项且值位于 `low` 和 `high` 之间（含），但允许有一个特殊值超出该范围。如果没有特殊值需求，`special` 应设置在 `low` 到 `high` 范围内。

如果一切正常，返回 `true`；如果表无效，则记录错误到内核日志缓冲区并返回 `false`。

```c
bool fs_validate_description(const struct fs_parameter_description *desc);
```

对参数描述进行一些验证检查。如果描述有效则返回 `true`，否则返回 `false` 并记录错误到内核日志缓冲区。

```c
int fs_parse(struct fs_context *fc,
             const struct fs_parameter_description *desc,
             struct fs_parameter *param,
             struct fs_parse_result *result);
```

这是主要的参数解释器。它使用参数描述通过键名查找参数，并将其转换为选项编号（返回）。
如果成功，并且参数类型指示结果是布尔值、整数、枚举、uid 或 gid 类型，该函数将转换该值并将结果存储在 `result->{boolean, int_32, uint_32, uint_64, uid, gid}` 中。

如果没有初始匹配，键将加上前缀 "no" 并进行查找。如果此时没有值存在，则尝试查找去掉前缀后的键。如果这与设置了 `fs_param_neg_with_no` 标志的参数类型匹配，则会进行匹配并将 `result->negated` 设置为 `true`。

如果参数未匹配到，将返回 `-ENOPARAM`；如果参数匹配到了但值有误，将返回 `-EINVAL`；否则将返回参数的选项编号。
:: 

    int fs_lookup_param(struct fs_context *fc,
                        struct fs_parameter *value,
                        bool want_bdev,
                        unsigned int flags,
                        struct path *_path);

此函数接受一个携带字符串或文件名类型的参数，并尝试对其进行路径查找。如果参数期望的是块设备（blockdev），则会检查该inode是否实际表示一个块设备。

如果成功，返回 0 并设置 `*_path`；如果不成功，返回负的错误码。
