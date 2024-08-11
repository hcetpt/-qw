==============================
通用通知机制
==============================

通用通知机制是基于标准管道驱动程序构建的，它有效地将内核生成的通知消息拼接到用户空间打开的管道中。这可以与以下内容结合使用：

  * 密钥/密钥环通知


启用通知缓冲区的方式如下：

	"General setup"/"General notification queue"
	(CONFIG_WATCH_QUEUE)

本文档包含以下部分：

.. contents:: :local:


概述
========

此设施表现为以特殊模式打开的管道。管道内部的环形缓冲区用于保存由内核生成的消息。这些消息随后通过read()读出。对于此类管道，Splice和类似操作被禁用，因为它们在某些情况下想要撤销对环的添加，而这可能会与通知消息交错。管道的所有者需要告诉内核它希望通过该管道监视哪些源。只有已连接到管道的源才会向其中插入消息。请注意，一个源可能绑定到多个管道，并同时向所有这些管道中插入消息。
可以在管道上设置过滤器，以便忽略不感兴趣的特定源类型和子事件。
如果环中没有可用的插槽或没有预分配的消息缓冲区，则会丢弃消息。在这两种情况下，在读取了缓冲区中的最后一条消息后，read()将在输出缓冲区中插入一条WATCH_META_LOSS_NOTIFICATION消息。
请注意，在生成通知时，内核不会等待消费者收集通知，而是继续执行。这意味着即使持有自旋锁也可以生成通知，同时也保护内核免受因用户空间故障而无限期地阻塞。
消息结构
=================

通知消息以短头开始：

```c
	struct watch_notification {
		__u32	type:24;
		__u32	subtype:8;
		__u32	info;
	};
```

"type"指示通知记录的来源，而"subtype"指示来自该来源的记录类型（请参阅下面的监视源部分）。类型也可能是"WATCH_TYPE_META"。这是由监视队列本身内部生成的特殊记录类型。有两种子类型：

  * WATCH_META_REMOVAL_NOTIFICATION
  * WATCH_META_LOSS_NOTIFICATION

第一个表示已安装监视的对象已被移除或销毁，第二个表示一些消息已经丢失。
"info"表示很多内容，包括：

  * 消息的字节长度，包括头部（与WATCH_INFO_LENGTH进行掩码并左移WATCH_INFO_LENGTH__SHIFT位）。这指示记录的大小，其可能在8到127字节之间
* 监视ID（与WATCH_INFO_ID进行掩码并左移WATCH_INFO_ID__SHIFT位）
这指示调用者的监视ID，其可能在0到255之间。多个监视可以共享一个队列，这提供了一种区分它们的方法
* 类型特定字段 (WATCH_INFO_TYPE_INFO)。此字段由通知生产者设置，用于指示与类型和子类型相关的特定含义。
    * 除了长度之外，info 中的所有内容都可用于过滤。
    * 标头之后可以跟随补充信息。这部分的格式由类型和子类型自行定义。

监视列表（通知源）API
====================

“监视列表”是一系列订阅了某个通知源的监视器列表。这样的列表可能绑定到某个对象（例如一个密钥或超级块），也可能全局存在（例如针对设备事件）。从用户空间的角度来看，非全局监视列表通常通过其所归属的对象来引用（如使用 KEYCTL_NOTIFY 并提供要监视的特定密钥的序列号）。
为了管理监视列表，提供了以下功能：

  * ::

      void init_watch_list(struct watch_list *wlist,
                           void (*release_watch)(struct watch *w));

    初始化监视列表。如果 `release_watch` 不为 NULL，则表示当监视列表对象被销毁时应该调用的函数，以丢弃监视列表持有的对被监视对象的任何引用。
* `void remove_watch_list(struct watch_list *wlist);`

    这将移除所有订阅该监视列表的监视，并释放它们，然后销毁监视列表本身。

监视队列（通知输出）API
=====================

“监视队列”是应用程序分配的缓冲区，通知记录将被写入其中。其具体工作方式完全隐藏在管道设备驱动程序内部，但在设置监视时必须获取对它的引用。这些可以通过以下方式管理：

  * `struct watch_queue *get_watch_queue(int fd);`

    由于监视队列通过实现缓冲区的管道文件描述符向内核指示，用户空间必须通过系统调用来传递该文件描述符。
    可以使用此方法根据系统调用来查找指向监视队列的不透明指针。
* `void put_watch_queue(struct watch_queue *wqueue);`

    释放通过 `get_watch_queue()` 获得的引用。

监视订阅 API
=============

“监视”是对监视列表的一种订阅，指定了通知记录应写入的监视队列及其缓冲区。监视队列对象还可能携带由用户空间设定的过滤规则。监视结构中的某些部分可由驱动程序设置：

```c
struct watch {
    union {
        u32 info_id; /* 将要与 info 字段进行 OR 操作的 ID */
        ..
```
```c
/* 
 * 结构体中的字段：
 *     private: 被监视对象的私有数据
 *     id: 内部标识符
 *     ...
 */

/* `info_id` 值应是从用户空间获取的 8 位数字，并通过 WATCH_INFO_ID__SHIFT 进行移位。
 * 如果通知被写入到关联的监视队列缓冲区，则将其与 struct watch_notification::info 中的
 * WATCH_INFO_ID 字段进行按位或操作。
 * `private` 字段是与监视列表相关的驱动程序数据，由 `watch_list::release_watch()` 方法清理。
 * `id` 字段是源的 ID。使用不同 ID 发布的通知将被忽略。
 * 以下函数用于管理监视器：
 * 
 *   void init_watch(struct watch *watch, struct watch_queue *wqueue);
 * 
 *     初始化监视对象，设置指向监视队列的指针，并使用适当的屏障避免锁依赖（lockdep）警告。
 * 
 *   int add_watch_to_object(struct watch *watch, struct watch_list *wlist);
 * 
 *     将监视器订阅到监视列表（通知源）。在调用此函数之前，监视结构体中由驱动程序设定的字段必须已经设置好。
 * 
 *   int remove_watch_from_object(struct watch_list *wlist, struct watch_queue *wqueue, u64 id, false);
 * 
 *     从监视列表中移除监视器，其中监视器必须匹配指定的监视队列 (`wqueue`) 和对象标识符 (`id`)。
 *     向监视队列发送通知 (`WATCH_META_REMOVAL_NOTIFICATION`) 以表明监视器已被移除。
 * 
 *   int remove_watch_from_object(struct watch_list *wlist, NULL, 0, true);
 * 
 *     从监视列表中移除所有监视器。预计这将在销毁前调用，并且此时监视列表将不再接受新的监视器。
 *     向每个已订阅监视器的监视队列发送通知 (`WATCH_META_REMOVAL_NOTIFICATION`) 以表明监视器已被移除。
 * 
 * 通知发布 API
 * =============
 * 
 * 为了向监视列表发布通知以便订阅的监视器能够看到它，应使用以下函数：
 *
 *   void post_watch_notification(struct watch_list *wlist, struct watch_notification *n, const struct cred *cred, u64 id);
 * 
 * 通知应预先格式化，并传递其头部的指针 (`n`)。通知可能比这更大，其大小（以缓冲槽为单位）记录在 `n->info & WATCH_INFO_LENGTH` 中。
 * `cred` 结构表示来源（主体）的凭据，并传递给 LSM（如 SELinux），允许或抑制根据队列（客体）的凭据来记录每条通知。
 */
```
```plaintext
"id" 是源对象的ID（例如钥匙上的序列号）。
只有设置了相同ID的监视器才能看到此通知。
监视源
=============

任何特定的缓冲区都可以从多个源接收数据。源包括：

  * WATCH_TYPE_KEY_NOTIFY

    此类型的通告指示钥匙和密钥环的变化，包括密钥环内容或钥匙属性的变化。
更多信息请参阅 Documentation/security/keys/core.rst
事件过滤
===============

创建监视队列后，可以设置一组过滤器来限制接收到的事件，使用如下命令：

    struct watch_notification_filter filter = {
        ..
    };
    ioctl(fd, IOC_WATCH_QUEUE_SET_FILTER, &filter)

过滤器描述是一个如下类型的变量：

    struct watch_notification_filter {
        __u32 nr_filters;
        __u32 __reserved;
        struct watch_notification_type_filter filters[];
    };

其中 "nr_filters" 是 filters[] 数组中的过滤器数量，而 "__reserved" 应该为0。"filters" 数组的元素具有以下类型：

    struct watch_notification_type_filter {
        __u32 type;
        __u32 info_filter;
        __u32 info_mask;
        __u32 subtype_filter[8];
    };

其中：

  * `type` 是要过滤的事件类型，应为如 "WATCH_TYPE_KEY_NOTIFY" 这样的值。

  * `info_filter` 和 `info_mask` 作为对通告记录中 info 字段的过滤器。只有当：
    
      (watch.info & info_mask) == info_filter
    
    时，才会将通告写入缓冲区。
    
    例如，这可用于忽略那些不是正好在监视点上的事件。
  * `subtype_filter` 是一个位掩码，表示感兴趣的子类型。subtype_filter[0] 的第0位对应子类型0，第1位对应子类型1，依此类推。
如果 ioctl() 的参数为 NULL，则会移除过滤器，并且来自被监视源的所有事件都会通过。
用户空间代码示例
======================

可以通过类似以下方式创建一个缓冲区：

    pipe2(fds, O_TMPFILE);
    ioctl(fds[1], IOC_WATCH_QUEUE_SET_SIZE, 256);

然后可以将其设置为接收密钥环更改通告：

    keyctl(KEYCTL_WATCH_KEY, KEY_SPEC_SESSION_KEYRING, fds[1], 0x01);

接着可以通过类似以下方式消费这些通告：

    static void consumer(int rfd, struct watch_queue_buffer *buf)
    {
        unsigned char buffer[128];
        ssize_t buf_len;

        while ((buf_len = read(rfd, buffer, sizeof(buffer))) > 0) {
            void *p = buffer;
            void *end = buffer + buf_len;
            while (p < end) {
                union {
                    struct watch_notification n;
                    unsigned char buf1[128];
                } n;
                size_t largest, len;

                largest = end - p;
                if (largest > 128)
                    largest = 128;
                memcpy(&n, p, largest);

                len = (n.n.info & WATCH_INFO_LENGTH) >>
                    WATCH_INFO_LENGTH__SHIFT;
                if (len == 0 || len > largest)
                    return;

                switch (n.n.type) {
                case WATCH_TYPE_META:
                    got_meta(&n.n);
                    break;
                case WATCH_TYPE_KEY_NOTIFY:
                    saw_key_change(&n.n);
                    break;
                }

                p += len;
            }
        }
    }
```
```
