SPDX 许可声明标识符: GPL-2.0

======================
seq_file 接口
======================

版权所有 2003 Jonathan Corbet <corbet@lwn.net>

此文件最初来自 LWN.net 的驱动移植系列文章：
https://lwn.net/Articles/driver-porting/

设备驱动程序（或其他内核组件）向用户或系统管理员提供信息的方法有很多。一种有用的技术是创建虚拟文件，这些文件可以位于 debugfs、/proc 或其他位置。虚拟文件可以提供易于获取的人类可读输出，而无需任何特殊工具程序；它们还可以使脚本编写者的工作更轻松。不出所料，使用虚拟文件的方法多年来一直在增长。
然而，正确地创建这些文件一直是一个挑战。创建一个返回字符串的虚拟文件并不难。但当输出很长——超过应用程序可能在单次操作中读取的内容时，事情就会变得复杂。处理多次读取（和定位）需要仔细关注读者在虚拟文件中的位置——这个位置很可能处于某行输出的中间。内核传统上有一些实现在这方面存在问题。
2.6 内核包含一组函数（由 Alexander Viro 实现），旨在使虚拟文件创建者能够正确实现这些功能。
seq_file 接口通过 <linux/seq_file.h> 提供。seq_file 有三个方面的内容：

- 一个迭代器接口，允许虚拟文件实现逐个遍历其呈现的对象
- 一些用于格式化对象以输出而不必担心输出缓冲区等问题的实用函数
- 一套预定义的 file_operations，实现了对虚拟文件的大多数操作
我们将通过一个极其简单的例子来介绍 seq_file 接口：一个创建名为 /proc/sequence 的文件的可加载模块。当读取该文件时，它会生成一系列递增的整数值，每行一个值。序列将一直持续到用户失去耐心并找到更好的事情做。该文件是可定位的，即可以执行如下操作：

    dd if=/proc/sequence of=out1 count=1
    dd if=/proc/sequence skip=1 of=out2 count=1

然后将输出文件 out1 和 out2 连接起来，并得到正确的结果。是的，这是一个完全无用的模块，但重点在于展示机制的工作原理，而不会迷失在其他细节中。（希望看到此模块完整源代码的人可以在 https://lwn.net/Articles/22359/ 找到）

已弃用的 create_proc_entry
============================

请注意，上述文章使用了已被内核 3.10 移除的 create_proc_entry。当前版本需要以下更新：

    - entry = create_proc_entry("sequence", 0, NULL);
    - if (entry)
    -     entry->proc_fops = &ct_file_ops;
    + entry = proc_create("sequence", 0, NULL, &ct_file_ops);

迭代器接口
======================

使用 seq_file 实现虚拟文件的模块必须实现一个迭代器对象，允许在“会话”期间（大致相当于一次 read() 系统调用）遍历感兴趣的数据。如果迭代器能够移动到特定位置——就像它们实现的文件一样，尽管可以自由地将位置编号映射到序列中的某个位置——则迭代器只需在会话期间短暂存在。如果迭代器无法轻易找到数字位置，但适用于 first/next 接口，则迭代器可以存储在私有数据区域，并从一个会话延续到下一个会话。
例如，格式化防火墙规则表的 seq_file 实现可以提供一个简单的迭代器，将位置 N 解释为链中的第 N 条规则。而呈现潜在易变的链表内容的 seq_file 实现可能会记录指向该链表的指针，前提是这样做不会导致当前位置被移除的风险。
定位可以以生成数据的一方认为最合适的方式进行，而无需知道位置如何转换为虚拟文件中的偏移量。唯一的明显例外是零位置应表示文件的开头。`/proc/sequence`迭代器仅使用其将输出的下一个数字的计数作为其位置。
为了使迭代器工作，必须实现四个函数。第一个函数名为`start()`，用于开始一个会话，并接受一个位置参数，返回一个将在该位置开始读取的迭代器。传递给`start()`的`pos`始终要么为零，要么为上一会话中使用的最近的`pos`值。
对于简单的序列示例，`start()`函数如下所示：

    static void *ct_seq_start(struct seq_file *s, loff_t *pos)
    {
            loff_t *spos = kmalloc(sizeof(loff_t), GFP_KERNEL);
            if (!spos)
                    return NULL;
            *spos = *pos;
            return spos;
    }

此迭代器的整个数据结构是一个`loff_t`值，用于保存当前位置。序列迭代器没有上限，但对于大多数其他`seq_file`实现来说并非如此；在大多数情况下，`start()`函数应该检查是否“超出文件末尾”，并在必要时返回NULL。
对于更复杂的应用程序，可以在`seq_file`结构的私有字段中存储会话之间的状态。还有一个特殊值可以由`start()`函数返回，称为`SEQ_START_TOKEN`；如果希望指示下面描述的`show()`函数在输出顶部打印标题，则可以使用它。但是，`SEQ_START_TOKEN`只能在偏移量为零时使用。`SEQ_START_TOKEN`对核心`seq_file`代码没有特殊意义。它是为了方便`start()`函数与`next()`和`show()`函数通信而提供的。
接下来要实现的函数令人惊讶地命名为`next()`；它的任务是将迭代器向前移动到序列中的下一个位置。示例模块可以简单地将位置递增1；更有用的模块将执行遍历某些数据结构所需的操作。`next()`函数返回一个新的迭代器或在序列完成时返回NULL。以下是示例版本：

    static void *ct_seq_next(struct seq_file *s, void *v, loff_t *pos)
    {
            loff_t *spos = v;
            *pos = ++*spos;
            return spos;
    }

`next()`函数应将`*pos`设置为`start()`可用于找到序列中新位置的值。当迭代器存储在私有数据区域而不是每次重新初始化时，似乎只需将`*pos`设置为任何非零值（零始终告诉`start()`重启序列）就足够了。然而，由于历史问题，这样做是不够的。
历史上，许多`next()`函数在文件末尾时不更新`*pos`。如果该值随后被`start()`用来初始化迭代器，这可能导致文件中的最后一个条目在输出中出现两次的情况。为了避免这种错误再次出现，核心`seq_file`代码现在会在`next()`函数不改变`*pos`的值时发出警告。因此，`next()`函数必须改变`*pos`的值，并且当然必须将其设置为非零值。
`stop()`函数关闭一个会话；其任务当然是清理。如果为迭代器动态分配了内存，`stop()`是释放内存的地方；如果`start()`获取了锁，`stop()`必须释放该锁。在调用`stop()`之前`next()`设置的`*pos`值会被记住，并用于下一个会话的第一个`start()`调用，除非已经对文件调用了`lseek()`；在这种情况下，下一个`start()`将被要求从位置零开始：

    static void ct_seq_stop(struct seq_file *s, void *v)
    {
            kfree(v);
    }

最后，`show()`函数应格式化当前迭代器指向的对象以便输出。示例模块的`show()`函数如下：

    static int ct_seq_show(struct seq_file *s, void *v)
    {
            loff_t *spos = v;
            seq_printf(s, "%lld\n", (long long)*spos);
            return 0;
    }

如果一切顺利，`show()`函数应返回零。通常形式的负错误代码表示出了问题；它将被传回用户空间。此函数也可以返回`SEQ_SKIP`，这会导致跳过当前项；如果`show()`函数在返回`SEQ_SKIP`之前已经生成了输出，则该输出将被丢弃。
我们稍后将讨论`seq_printf()`。但首先，通过创建包含我们刚刚定义的四个函数的`seq_operations`结构来完成`seq_file`迭代器的定义：

    static const struct seq_operations ct_seq_ops = {
            .start = ct_seq_start,
            .next  = ct_seq_next,
            .stop  = ct_seq_stop,
            .show  = ct_seq_show
    };

此结构将用于将我们的迭代器与`/proc`文件关联起来。
值得注意的是，`start()`返回并由其他函数操作的迭代器值被认为是完全不透明的，`seq_file`代码对此没有任何了解。因此，它可以是任何有助于遍历要输出的数据的有用内容。计数器可能很有用，但它也可以是直接指向数组或链表的指针。任何东西都可以，只要程序员意识到在调用迭代器函数之间可能会发生一些事情即可。然而，`seq_file`代码（设计上）不会在调用`start()`和`stop()`之间休眠，所以在那段时间内持有锁是合理的做法。`seq_file`代码也会避免在迭代器活跃期间获取其他任何锁。
迭代器通过 `start()` 或 `next()` 返回的值保证会被传递给后续的 `next()` 或 `stop()` 调用。这使得可以可靠地释放像锁这样的资源。然而，没有保证该迭代器会被传递给 `show()` 函数，尽管在实践中这种情况经常发生。

格式化输出
===========

`seq_file` 代码管理了由迭代器生成的输出位置，并将其放入用户的缓冲区。但为了实现这一点，这些输出必须被传递给 `seq_file` 代码。已经定义了一些实用函数来简化这一任务。

大多数代码将简单地使用 `seq_printf()`，其工作方式与 `printk()` 类似，但需要一个 `seq_file` 指针作为参数。

对于直接的字符输出，可以使用以下函数：

```c
seq_putc(struct seq_file *m, char c);
seq_puts(struct seq_file *m, const char *s);
seq_escape(struct seq_file *m, const char *s, const char *esc);
```

前两个函数分别输出单个字符和字符串，正如预期的那样。`seq_escape()` 类似于 `seq_puts()`，不同之处在于 `s` 中任何出现在 `esc` 字符串中的字符将在输出中以八进制形式表示。

还有两个用于打印文件名的函数：

```c
int seq_path(struct seq_file *m, const struct path *path,
             const char *esc);
int seq_path_root(struct seq_file *m, const struct path *path,
                  const struct path *root, const char *esc);
```

这里，`path` 表示感兴趣的文件，而 `esc` 是一组应在输出中转义的字符。调用 `seq_path()` 将输出相对于当前进程文件系统根目录的路径。如果需要不同的根目录，则可以使用 `seq_path_root()`。如果发现 `path` 无法从 `root` 访问，`seq_path_root()` 将返回 `SEQ_SKIP`。

生成复杂输出的函数可能希望检查：

```c
bool seq_has_overflowed(struct seq_file *m);
```

如果返回 `true`，则应避免进一步调用 `seq_<output>` 函数。

`seq_has_overflowed` 返回 `true` 表示 `seq_file` 缓冲区将被丢弃，并且 `seq_show` 函数将尝试分配更大的缓冲区并重试打印。

使一切正常工作
==================

到目前为止，我们有一组可以在 `seq_file` 系统内生成输出的函数，但我们还没有将其转换为用户可见的文件。在内核中创建文件当然需要创建一组实现对该文件操作的 `file_operations`。`seq_file` 接口提供了一组预定义的操作来完成大部分工作。但是，虚拟文件作者仍需实现 `open()` 方法来连接所有组件。`open` 函数通常只有一行，如示例模块所示：

```c
static int ct_open(struct inode *inode, struct file *file)
{
    return seq_open(file, &ct_seq_ops);
}
```

在这里，调用 `seq_open()` 会取我们之前创建的 `seq_operations` 结构体，并设置好迭代虚拟文件所需的配置。

在成功打开时，`seq_open()` 会在 `file->private_data` 中存储 `struct seq_file` 指针。如果你的应用程序中同一个迭代器可用于多个文件，可以在 `seq_file` 结构体的 `private` 字段中存储任意指针；然后迭代器函数可以检索这个值。

还有一个名为 `seq_open_private()` 的包装函数，它会分配一块零填充内存，并将其指针存储在 `seq_file` 结构体的 `private` 字段中，在成功时返回 0。块大小在函数的第三个参数中指定，例如：

```c
static int ct_open(struct inode *inode, struct file *file)
{
    return seq_open_private(file, &ct_seq_ops,
                            sizeof(struct mystruct));
}
```

还有一个变体函数 `__seq_open_private()`，功能相同，只是成功时返回分配内存块的指针，允许进一步初始化，例如：

```c
static int ct_open(struct inode *inode, struct file *file)
{
    struct mystruct *p =
        __seq_open_private(file, &ct_seq_ops, sizeof(*p));

    if (!p)
        return -ENOMEM;

    p->foo = bar; /* 初始化我的数据 */
    ..
}
```
```c
p->baz = true;

	return 0;
}

```

一个对应的关闭函数 `seq_release_private()` 可用，它会在相应的打开操作中释放分配的内存。其他感兴趣的函数——`read()`、`llseek()` 和 `release()`——都是由 `seq_file` 代码本身实现的。因此，一个虚拟文件的 `file_operations` 结构看起来像这样：

```c
static const struct file_operations ct_file_ops = {
	.owner   = THIS_MODULE,
	.open    = ct_open,
	.read    = seq_read,
	.llseek  = seq_lseek,
	.release = seq_release
};
```

还有一个 `seq_release_private()` 函数，在释放结构之前将 `seq_file` 的私有字段内容传递给 `kfree()`。

最后一步是创建 `/proc` 文件本身。在示例代码中，这是通过初始化代码以通常的方式完成的：

```c
static int ct_init(void)
{
        struct proc_dir_entry *entry;

        proc_create("sequence", 0, NULL, &ct_file_ops);
        return 0;
}

module_init(ct_init);
```

这就是全部内容了。

### seq_list

如果你的文件需要遍历一个链表，你可能会发现这些函数很有用：

```c
struct list_head *seq_list_start(struct list_head *head, loff_t pos);
struct list_head *seq_list_start_head(struct list_head *head, loff_t pos);
struct list_head *seq_list_next(void *v, struct list_head *head, loff_t *ppos);
```

这些辅助函数会将 `pos` 解释为链表中的位置，并相应地进行迭代。你的 `start()` 和 `next()` 函数只需使用适当的 `list_head` 结构指针调用 `seq_list_*` 辅助函数即可。

### 极简版本

对于极其简单的虚拟文件，有一个更简单的接口。模块可以只定义 `show()` 函数，该函数应生成虚拟文件中包含的所有输出。文件的 `open()` 方法然后调用：

```c
int single_open(struct file *file,
                int (*show)(struct seq_file *m, void *p),
                void *data);
```

当输出时间到来时，`show()` 函数将被调用一次。传递给 `single_open()` 的 `data` 值可以在 `seq_file` 结构的私有字段中找到。当使用 `single_open()` 时，程序员应在 `file_operations` 结构中使用 `single_release()` 而不是 `seq_release()`，以避免内存泄漏。
