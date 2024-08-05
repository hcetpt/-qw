==================
S390 调试特性
==================

文件:
      - arch/s390/kernel/debug.c
      - arch/s390/include/asm/debug.h

描述:
------------
此特性的目标是提供一个内核调试日志API，使得日志记录能够高效地存储在内存中，每个组件（例如设备驱动程序）可以有一个独立的调试日志。其一个目的是在生产系统崩溃后检查调试日志以分析崩溃原因。如果系统仍在运行但仅使用dbf的子组件失败，则可以通过Linux的debugfs文件系统在活动系统上查看调试日志。此调试特性对于内核和驱动程序开发也非常有用。
设计:
-------
内核组件（如设备驱动程序）可以通过调用函数 :c:func:`debug_register()` 来向调试特性注册自己。该函数为调用者初始化一个调试日志。对于每个调试日志都存在多个调试区域，其中恰好有一个是活动的。每个调试区域由内存中的连续页组成。在调试区域内存储调试条目（日志记录），这些记录是由事件和异常调用写入的。
一个事件调用将指定的调试条目写入活动调试区域，并更新活动区域的日志指针。如果达到活动调试区域的末尾，则进行循环（环形缓冲区），下一个调试条目将写入活动调试区域的起始位置。
一个异常调用将指定的调试条目写入日志并切换到下一个调试区域。这是为了确保当当前区域发生循环时，描述异常来源的记录不会被覆盖。
调试区域本身也以环形缓冲区的形式排序。当在最后一个调试区域中抛出异常时，随后的调试条目将再次写入第一个区域。
事件和异常调用有四个版本：一个用于记录原始数据，一个用于文本，一个用于数字（无符号整数和长整型），还有一个用于类似`sprintf`格式化的字符串。

每个调试条目包含以下数据：

- 时间戳
- 调用任务的CPU编号
- 调试条目的级别（0...6）
- 返回到调用者的地址
- 标志，指示该条目是否为异常

可以在实时系统中通过`debugfs`文件系统中的条目来检查调试日志。在顶级目录“`s390dbf`”下，每个已注册组件都有一个以其相应的组件命名的目录。通常，`debugfs`应该挂载到`/sys/kernel/debug`，因此可以在`/sys/kernel/debug/s390dbf`访问调试功能。
目录的内容是代表调试日志不同视图的文件。每个组件可以通过使用函数`debug_register_view()`注册它们所使用的视图。提供了预定义的hex/ascii和`sprintf`数据视图。也可以定义其他视图。通过读取对应的`debugfs`文件可以简单地检查视图的内容。

所有调试日志都有一个实际的调试级别（范围从0到6）。默认级别为3。事件和异常函数有一个`level`参数。只有级别低于或等于实际级别的调试条目才会被写入日志。这意味着，在记录事件时，高优先级的日志条目应具有较低的级别值，而低优先级的条目则应具有较高的级别值。
实际的调试级别可以通过`debugfs`文件系统更改，方法是将数字字符串"x"写入为每个调试日志提供的`level` `debugfs`文件。完全关闭调试可以通过在`level` `debugfs`文件中使用"-"实现。
例如：

```sh
echo "-" > /sys/kernel/debug/s390dbf/dasd/level
```

还可以全局禁用所有调试日志的调试功能。你可以使用`/proc/sys/s390dbf`中的两个`sysctl`参数来改变行为：

目前有两种可能的触发器，可以全局停止调试功能。第一种可能是使用`debug_active` `sysctl`。如果设置为1，则调试功能运行；如果`debug_active`设置为0，则调试功能关闭。
第二种触发器是内核oops，这也会停止调试功能。
This text describes how to manage and interact with debug features in the Linux kernel specifically for the s390 architecture. Below is the translation into Chinese.

这防止了调试功能覆盖在系统崩溃(oops)之前发生的调试信息。系统崩溃后，您可以通过将数字1通过管道传递给`/proc/sys/s390dbf/debug_active`来重新激活调试功能。然而，在生产环境中使用发生过系统崩溃的内核并不被建议。
如果您希望禁止调试功能的停用，您可以使用`debug_stoppable`的sysctl设置。如果将`debug_stoppable`设置为0，则调试功能无法被停止。如果调试功能已经停止，则会保持停用状态。

### 内核接口：
------------------
```markdown
.. kernel-doc:: arch/s390/kernel/debug.c
.. kernel-doc:: arch/s390/include/asm/debug.h
```

### 预定义视图：
-------------------

```c
extern struct debug_view debug_hex_ascii_view;

extern struct debug_view debug_sprintf_view;
```

### 示例
--------------

#### `hex_ascii`视图示例
```c
/*
 * hex_ascii视图示例
 */

#include <linux/init.h>
#include <asm/debug.h>

static debug_info_t *debug_info;

static int init(void)
{
    /* 注册4个调试区域，每个区域一个页，数据字段大小为4字节 */

    debug_info = debug_register("test", 1, 4, 4 );
    debug_register_view(debug_info, &debug_hex_ascii_view);

    debug_text_event(debug_info, 4 , "one ");
    debug_int_exception(debug_info, 4, 4711);
    debug_event(debug_info, 3, &debug_info, 4);

    return 0;
}

static void cleanup(void)
{
    debug_unregister(debug_info);
}

module_init(init);
module_exit(cleanup);
```

#### `sprintf`视图示例
```c
/*
 * sprintf视图示例
 */

#include <linux/init.h>
#include <asm/debug.h>

static debug_info_t *debug_info;

static int init(void)
{
    /* 注册4个调试区域，每个区域一个页，数据字段用于存储格式字符串指针+2个可变参数（等于3倍long类型的大小） */

    debug_info = debug_register("test", 1, 4, sizeof(long) * 3);
    debug_register_view(debug_info, &debug_sprintf_view);

    debug_sprintf_event(debug_info, 2 , "first event in %s:%i\n",__FILE__,__LINE__);
    debug_sprintf_exception(debug_info, 1, "pointer to debug info: %p\n",&debug_info);

    return 0;
}

static void cleanup(void)
{
    debug_unregister(debug_info);
}

module_init(init);
module_exit(cleanup);
```

### 调试文件系统(Debugfs)接口
-------------------
可以透过读取相应的debugfs文件来查看调试日志的视图：

#### 示例
```bash
> ls /sys/kernel/debug/s390dbf/dasd
flush  hex_ascii  level pages
> cat /sys/kernel/debug/s390dbf/dasd/hex_ascii | sort -k2,2 -s
00 00974733272:680099 2 - 02 0006ad7e  07 ea 4a 90 | ...
00 00974733272:682210 2 - 02 0006ade6  46 52 45 45 | FREE
  00 00974733272:682213 2 - 02 0006adf6  07 ea 4a 90 | ...
00 00974733272:682281 1 * 02 0006ab08  41 4c 4c 43 | EXCP
  01 00974733272:682284 2 - 02 0006ab16  45 43 4b 44 | ECKD
  01 00974733272:682287 2 - 02 0006ab28  00 00 00 04 | ...
01 00974733272:682289 2 - 02 0006ab3e  00 00 00 20 | ..
01 00974733272:682297 2 - 02 0006ad7e  07 ea 4a 90 | ...
01 00974733272:684384 2 - 00 0006ade6  46 52 45 45 | FREE
  01 00974733272:684388 2 - 00 0006adf6  07 ea 4a 90 | ...
```
有关上述输出的解释，请参见预定义视图部分！

### 更改调试级别
-------------------

#### 示例
```bash
> cat /sys/kernel/debug/s390dbf/dasd/level
3
> echo "5" > /sys/kernel/debug/s390dbf/dasd/level
> cat /sys/kernel/debug/s390dbf/dasd/level
5
```

### 刷新调试区域
--------------------
可以通过向debugfs文件“flush”管道输入所需的调试区域编号(0...n)来刷新调试区域。使用“-”则刷新所有调试区域。

#### 示例

1. 刷新调试区域0:
   ```bash
   > echo "0" > /sys/kernel/debug/s390dbf/dasd/flush
   ```

2. 刷新所有调试区域:
   ```bash
   > echo "-" > /sys/kernel/debug/s390dbf/dasd/flush
   ```

### 更改调试区域的大小
-------------------------
可以通过向debugfs文件“pages”管道输入页数来更改调试区域的大小。调整大小请求也会刷新调试区域。
定义调试功能 "dasd" 的调试区域中的4页：

  > echo "4" > /sys/kernel/debug/s390dbf/dasd/pages

停止调试功能
-----------------
示例：

1. 检查是否允许停止：

     > cat /proc/sys/s390dbf/debug_stoppable

2. 停止调试功能：

     > echo 0 > /proc/sys/s390dbf/debug_active

crash 工具接口
-----------------
从版本5.1.0开始，`crash`工具内置了一个命令 `s390dbf` 来显示所有调试日志或将其导出到文件系统。
使用这个工具可以在运行的系统上调查调试日志，并在系统崩溃后的内存转储中进行调查。
调查原始内存
--------------------
另一种可能是在运行的系统上以及系统崩溃后查看原始内存来调查调试日志。这可以通过虚拟机或服务元素实现。
可以通过 `System map` 中的 `debug_area_first` 符号找到调试日志的锚点。然后需要遵循 `debug.h` 中定义的数据结构中的正确指针以在内存中找到调试区域。
通常，使用调试功能的模块也会有一个指向调试日志的全局变量。通过跟随这个指针，也可以在内存中找到调试日志。
对于这种方法，建议使用 '16 * x + 4' 字节（x = 0..n）作为 :c:func:`debug_register()` 中数据字段的长度，以便清晰地格式化显示调试条目。
预定义视图
-----------------

有两个预定义的视图：hex_ascii 和 sprintf。
hex_ascii 视图以十六进制和ASCII形式显示数据字段（例如，“45 43 4b 44 | ECKD”）。
sprintf 视图将调试条目格式化为与 `sprintf` 函数相同的方式。`sprintf` 事件/异常函数向调试条目写入一个指向格式字符串的指针（大小等于 `sizeof(long)`），以及每个可变参数的 `long` 值。因此，例如，对于包含格式字符串和两个可变参数的调试条目，你需要在 `debug_register()` 函数中分配一个 `(3 * sizeof(long))` 字节的数据区域。
重要提示：
  在 `sprintf` 事件函数中使用 "%s" 是危险的。只有当传递的字符串内存在整个调试功能存在期间可用时，你才能在 `sprintf` 事件函数中使用 "%s"。原因是出于性能考虑，只存储指向字符串的指针。如果你记录一个之后被释放的字符串，当你检查调试功能时会遇到 OOPS 错误，因为此时调试功能会访问已经被释放的内存。
### 注意：
如果使用`sprintf`视图，请勿使用除`sprintf`事件和异常函数之外的其他事件/异常功能。
`hex_ascii`和`sprintf`视图的格式如下：

- 区域编号
- 时间戳（自1970年1月1日00:00:00协调世界时（UTC）以来，以秒和微秒为单位格式化）
- 调试条目级别
- 异常标志（*=异常）
- 调用任务的CPU编号
- 返回调用者的地址
- 数据字段

`hex_ascii`视图的一行典型示例如下（第一行仅用于解释，在查看视图时不会显示）：

```
区域  时间             级别  异常 CPU 调用者      数据(十六进制+ASCII)
-------------------------------------------------------------------
00    00964419409:440690 1 -   00  88023fe
```

### 定义视图

视图通过`debug_view`结构指定。定义了回调函数，用于读取和写入debugfs文件：

```c
struct debug_view {
    char name[DEBUG_MAX_PROCF_LEN];
    debug_prolog_proc_t* prolog_proc;
    debug_header_proc_t* header_proc;
    debug_format_proc_t* format_proc;
    debug_input_proc_t*  input_proc;
    void*                private_data;
};
```

其中：

```c
typedef int (debug_header_proc_t) (debug_info_t* id,
                                   struct debug_view* view,
                                   int area,
                                   debug_entry_t* entry,
                                   char* out_buf);

typedef int (debug_format_proc_t) (debug_info_t* id,
                                   struct debug_view* view, char* out_buf,
                                   const char* in_buf);
typedef int (debug_prolog_proc_t) (debug_info_t* id,
                                   struct debug_view* view,
                                   char* out_buf);
typedef int (debug_input_proc_t) (debug_info_t* id,
                                  struct debug_view* view,
                                  struct file* file, const char* user_buf,
                                  size_t in_buf_size, loff_t* offset);
```

`private_data`成员可以用作指向特定视图数据的指针；它本身不由调试特性使用。

从debugfs读取视图时的输出结构如下：

```
"prolog_proc 输出"

"header_proc 输出 1"  "format_proc 输出 1"
"header_proc 输出 2"  "format_proc 输出 2"
"header_proc 输出 3"  "format_proc 输出 3"
..
```

当从debugfs读取视图时，Debug特性会调用一次`prolog_proc`来写入序言。
然后对于每个存在的调试条目都会调用`header_proc`和`format_proc`。
`input_proc`可用于实现向视图写入时的功能（例如：`echo "0" > /sys/kernel/debug/s390dbf/dasd/level`）。
对于`header_proc`，可以使用默认函数`debug_dflt_header_fn()`，该函数在debug.h中定义，并且产生的头输出与预定义视图相同。例如：

```
00 00964419409:440761 2 - 00 88023ec
```

为了了解如何使用这些回调函数，请参考默认视图的实现！

### 示例：

```c
#include <asm/debug.h>

#define UNKNOWNSTR "数据: %08x"

const char* messages[] = {
    "这个错误...........\n",
    "那个错误...........\n",
    "问题..............\n",
    "有些事情出错了。\n",
    "一切正常........\n",
    NULL
};

static int debug_test_format_fn(
    debug_info_t *id, struct debug_view *view,
    char *out_buf, const char *in_buf
) {
    int i, rc = 0;

    if (id->buf_size >= 4) {
        int msg_nr = *((int*)in_buf);
        if (msg_nr < sizeof(messages) / sizeof(char*) - 1)
            rc += sprintf(out_buf, "%s", messages[msg_nr]);
        else
            rc += sprintf(out_buf, UNKNOWNSTR, msg_nr);
    }
    return rc;
}

struct debug_view debug_test_view = {
    "myview",                 /* 视图名称 */
    NULL,                     /* 无序言 */
    &debug_dflt_header_fn,    /* 每个条目的默认头部 */
    &debug_test_format_fn,    /* 自定义格式函数 */
    NULL,                     /* 无输入函数 */
    NULL                      /* 无私有数据 */
};

// 测试代码省略
```

### 测试
测试代码部分省略。
```c
// 注册一个名为 "test" 的调试信息，起始值为 0，计数间隔为 4，重复次数也为 4。
debug_info = debug_register("test", 0, 4, 4);
// 将注册的调试信息与一个名为 debug_test_view 的视图关联起来。
debug_register_view(debug_info, &debug_test_view);
// 循环 10 次，并使用调试信息触发整数事件，事件类型为 1，事件数据依次为 0 到 9。
for (i = 0; i < 10; i++)
    debug_int_event(debug_info, 1, i);
```

```
// 查看 /sys/kernel/debug/s390dbf/test/myview 中的内容
> cat /sys/kernel/debug/s390dbf/test/myview
00 00964419734:611402 1 - 00 88042ca   This error..........
00 00964419734:611405 1 - 00 88042ca   That error..........
00 00964419734:611408 1 - 00 88042ca   Problem.............
00 00964419734:611411 1 - 00 88042ca   Something went wrong
00 00964419734:611414 1 - 00 88042ca   Everything ok.......
00 00964419734:611417 1 - 00 88042ca   data: 00000005
00 00964419734:611419 1 - 00 88042ca   data: 00000006
00 00964419734:611422 1 - 00 88042ca   data: 00000007
00 00964419734:611425 1 - 00 88042ca   data: 00000008
00 00964419734:611428 1 - 00 88042ca   data: 00000009
```

这段代码首先创建了一个调试信息实例 `debug_info`，然后将其与一个视图关联起来。接着通过循环触发了 10 个整数事件，并将这些事件的数据写入到了内核调试文件系统中指定路径的文件里。

查看该文件内容可以看到，文件中记录了一系列的调试信息，包括一些错误和状态描述，以及从 5 到 9 的整数数据。这可能是由于前四次整数事件触发时输出了其他调试信息（如错误信息），而之后的事件只输出了整数数据。
