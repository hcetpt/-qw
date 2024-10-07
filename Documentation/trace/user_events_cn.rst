=========================================
用户事件：基于用户的事件追踪
=========================================

:作者: Beau Belgrave

概述
------
基于用户的跟踪事件允许用户进程创建可以通过现有工具（如ftrace和perf）查看的事件和跟踪数据。
要启用此功能，请使用CONFIG_USER_EVENTS=y编译内核。
程序可以通过/sys/kernel/tracing/user_events_status查看事件状态，并通过/sys/kernel/tracing/user_events_data注册和写入数据。
程序还可以使用/sys/kernel/tracing/dynamic_events通过u:前缀注册和删除基于用户的事件。动态事件命令的格式与带有u:前缀的ioctl相同。由于事件持久化，这需要CAP_PERFMON权限，否则将返回-EPERM错误。
通常，程序会注册一组它们希望暴露给能够读取跟踪事件（如ftrace和perf）的工具的事件。注册过程告诉内核哪个地址和位会在任何工具启用该事件时被反映，并且应写入数据。注册将返回一个写入索引，在对/sys/kernel/tracing/user_events_data文件调用write()或writev()时描述数据。
本文档中引用的结构包含在源代码树中的/include/uapi/linux/user_events.h文件中。
**注意：** *user_events_status和user_events_data都在tracefs文件系统下，其挂载路径可能与上述不同。*

注册
------
在一个用户进程中进行注册是通过ioctl()调用/sys/kernel/tracing/user_events_data文件完成的。要发出的命令是DIAG_IOCSREG。
此命令需要一个打包后的struct user_reg作为参数：

```c
  struct user_reg {
        /* 输入：正在使用的user_reg结构的大小 */
        __u32 size;

        /* 输入：在enable_addr指定地址处使用的位 */
        __u8 enable_bit;

        /* 输入：地址处启用大小的字节数 */
        __u8 enable_size;

        /* 输入：使用的标志（如果有） */
        __u16 flags;

        /* 输入：启用时更新的地址 */
        __u64 enable_addr;

        /* 输入：指向包含事件名称、描述和标志字符串的指针 */
        __u64 name_args;

        /* 输出：写入数据时使用的事件索引 */
        __u32 write_index;
  } __attribute__((__packed__));
```

struct user_reg要求所有上述输入都适当设置：
+ size: 必须设置为sizeof(struct user_reg)
+ enable_bit: 在enable_addr指定的地址处反映事件状态的位
+ enable_size: 由 enable_addr 指定的值的大小
这必须是 4（32 位）或 8（64 位）。64 位值仅允许在 64 位内核上使用，然而 32 位可以在所有内核上使用。
+ flags: 要使用的标志（如果有的话）
调用者应首先尝试使用标志并重试而不使用标志以确保对较低版本内核的支持。如果不支持某个标志，则返回 -EINVAL。
+ enable_addr: 用于反映事件状态的值的地址
这必须是自然对齐的，并且在用户程序中可写访问。
+ name_args: 描述事件的名称和参数，详见命令格式
当前支持以下标志：
+ USER_EVENT_REG_PERSIST: 事件不会在最后一个引用关闭时删除。如果希望事件在进程关闭或注销后仍然存在，调用者可以使用此标志。需要 CAP_PERFMON 否则返回 -EPERM。
+ USER_EVENT_REG_MULTI_FORMAT: 事件可以包含多种格式。这允许程序在其事件格式更改但仍希望使用相同名称时防止自己被阻塞。当使用此标志时，跟踪点名称将采用新格式 "name.unique_id" 而不是旧格式 "name"。每个唯一的名称和格式组合都会创建一个跟踪点。这意味着如果多个进程使用相同的名称和格式，它们将使用相同的跟踪点。如果另一个进程使用相同的名称但与其他进程不同的格式，它将使用具有新唯一 ID 的不同跟踪点。记录程序需要扫描 tracefs 以查找它们感兴趣的事件名称的各种不同格式。跟踪点的系统名称也将使用 "user_events_multi" 而不是 "user_events"。这可以防止单格式事件名称与 tracefs 中的任何多格式事件名称冲突。唯一 ID 以十六进制字符串形式输出。记录程序应确保跟踪点名称以它们注册的事件名称开头，并且后缀以 . 开头且仅包含十六进制字符。例如，要查找所有版本的事件 "test"，可以使用正则表达式 "^test\.[0-9a-fA-F]+$"。

成功注册后，以下内容将被设置：
+ write_index: 用于写入数据时，代表此事件的文件描述符所使用的索引。该索引是此文件描述符实例在注册时唯一的。详情请参见“写入数据”。

基于用户的事件会像其他子系统中的事件一样出现在 tracefs 中，位于名为 "user_events" 的子系统下。这意味着希望附加到这些事件的工具需要使用 `/sys/kernel/tracing/events/user_events/[name]/enable` 或 `perf record -e user_events:[name]` 进行附加/记录。

**注意：** 默认情况下，事件子系统的名称为 "user_events"。调用者不应假定它总是 "user_events"。操作员保留将来根据进程更改子系统名称以实现事件隔离的权利。此外，如果使用了 USER_EVENT_REG_MULTI_FORMAT 标志，则跟踪点名称将附加一个唯一的 ID，并且系统名称将变为 "user_events_multi"，如上所述。

命令格式
^^^^^^^^^^^^^^
命令字符串格式如下：

```
name[:FLAG1[,FLAG2...]] [Field1[;Field2...]]
```

支持的标志
^^^^^^^^^^^^^^^
目前不支持任何标志。

字段格式
^^^^^^^^^^^^
```
type name [size]
```

基本类型（如 __data_loc, u32, u64, int, char, char[20] 等）被支持。
建议用户程序使用明确大小的类型，如 u32。

**注意：** 不支持 long 类型，因为其大小在用户空间和内核空间之间可能不同。

大小仅对以 struct 前缀开始的类型有效。这允许用户程序向工具描述自定义结构，如果需要的话。
例如，C 中的一个结构体如下所示：

```c
struct mytype {
    char data[20];
};
```

将表示为以下字段：

```
struct mytype myname 20
```

删除
删除用户进程中的事件是通过 ioctl() 调用到 `/sys/kernel/tracing/user_events_data` 文件完成的。需要发出的命令是 DIAG_IOCSDEL。
此命令只需要一个字符串来指定要删除的事件名称。删除只有在没有对该事件的引用（包括用户空间和内核空间）时才会成功。用户程序应使用单独的文件请求删除，而不是用于注册的文件。
**注释：** 默认情况下，当事件不再有任何引用时，事件将自动删除。如果程序不希望自动删除，必须在注册事件时使用 USER_EVENT_REG_PERSIST 标志。一旦使用了该标志，事件将一直存在，直到调用 DIAG_IOCSDEL。对于持久存在的事件，注册和删除都需要 CAP_PERFMON 权限，否则会返回 -EPERM 错误。当有多个相同事件名称的格式时，所有同名事件都将尝试被删除。如果只想删除特定版本的事件，则应使用 /sys/kernel/tracing/dynamic_events 文件来指定该事件的具体格式。

### 注销

注销
-------------

如果注册事件后不再需要更新，可以通过 ioctl() 调用到 /sys/kernel/tracing/user_events_data 文件将其禁用。
发出的命令是 DIAG_IOCSUNREG。这与删除不同，删除实际上是从系统中移除事件，而注销只是告诉内核你的进程不再关心该事件的更新。

此命令需要一个打包后的 struct user_unreg 结构作为参数：

```c
struct user_unreg {
        /* 输入：正在使用的 user_unreg 结构的大小 */
        __u32 size;

        /* 输入：要禁用的位 */
        __u8 disable_bit;

        /* 输入：保留字段，设置为 0 */
        __u8 __reserved;

        /* 输入：保留字段，设置为 0 */
        __u16 __reserved2;

        /* 输入：要禁用的地址 */
        __u64 disable_addr;
} __attribute__((__packed__));
```

struct user_unreg 需要正确设置上述所有输入项：
- size：必须设置为 sizeof(struct user_unreg)
- disable_bit：必须设置为要禁用的位（与之前通过 enable_bit 注册的位相同）
- disable_addr：必须设置为要禁用的地址（与之前通过 enable_addr 注册的地址相同）

**注释：** 当调用 execve() 时，事件将自动注销。在 fork() 过程中，已注册的事件将被保留，并且如果需要的话，必须在每个进程中手动注销。

状态
------

当工具附加/记录基于用户的事件时，事件的状态会被实时更新。这样用户程序只有在有东西实际附加到事件上时才会产生 write() 或 writev() 的开销。

内核会在工具附加/分离时更新为事件注册的指定位。用户程序只需检查该位是否设置即可判断是否有东西附加。
管理员可以通过直接通过终端读取 `user_events_status` 文件轻松检查所有已注册事件的状态。输出如下所示：

```
名称 [# 注释]
..
活动: 活动计数
忙碌: 忙碌计数
```

例如，在一个只有一个事件的系统上，输出看起来像这样：

```
test

活动: 1
忙碌: 0
```

如果用户通过 ftrace 启用用户事件，输出将变为如下所示：

```
test # 由 ftrace 使用

活动: 1
忙碌: 1
```

写入数据
--------
在注册事件后，可以使用相同的文件描述符来为该事件写入条目。返回的 `write_index` 必须位于数据的开头，然后剩余的数据被视为事件的有效载荷。
例如，如果 `write_index` 返回的值是 1，并且我想写入一个整数有效载荷，则数据必须为 8 字节（2 个整数）大小，前 4 个字节等于 1，最后 4 个字节等于我想要的有效载荷值。
在内存中，这看起来像这样：

```
int index;
int payload;
```

用户程序可能有一些他们希望作为有效载荷发出的已知结构体。在这种情况下，可以使用 `writev()`，其中第一个向量是索引，随后的向量是实际的事件有效载荷。
例如，如果我有一个这样的结构体：

```c
struct payload {
    int src;
    int dst;
    int flags;
} __attribute__((__packed__));
```

建议用户程序执行以下操作：

```c
struct iovec io[2];
struct payload e;

io[0].iov_base = &write_index;
io[0].iov_len = sizeof(write_index);
io[1].iov_base = &e;
io[1].iov_len = sizeof(e);

writev(fd, (const struct iovec*)io, 2);
```

**注意：** *`write_index` 不会记录到正在记录的跟踪中。*

示例代码
--------
请参阅 `samples/user_events` 中的示例代码。
