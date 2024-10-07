SPDX 许可证标识符: BSD-3-Clause

=====================================
使用 Netlink 协议规范
=====================================

本文档是一个快速入门指南，用于使用 Netlink 协议规范。对于规范的详细描述，请参阅 :doc:`specs`
简易命令行界面 (CLI)
==================

内核自带一个简易的 CLI 工具，在开发与 Netlink 相关的代码时可能会非常有用。该工具是用 Python 实现的，并且可以使用 YAML 规范向内核发送 Netlink 请求。目前仅支持通用 Netlink。该工具位于 ``tools/net/ynl/cli.py``。它接受一些参数，其中最重要的几个是：

 - ``--spec`` - 指定规范文件的位置
 - ``--do $name`` / ``--dump $name`` - 发送请求 ``$name``
 - ``--json $attrs`` - 提供请求所需的属性
 - ``--subscribe $group`` - 接收来自 ``$group`` 的通知

YAML 规范文件可以在 ``Documentation/netlink/specs/`` 下找到。示例用法如下：

  $ ./tools/net/ynl/cli.py --spec Documentation/netlink/specs/ethtool.yaml \
        --do rings-get \
	--json '{"header":{"dev-index": 18}}'
  {'header': {'dev-index': 18, 'dev-name': 'eni1np1'},
   'rx': 0,
   'rx-jumbo': 0,
   'rx-jumbo-max': 4096,
   'rx-max': 4096,
   'rx-mini': 0,
   'rx-mini-max': 4096,
   'tx': 0,
   'tx-max': 4096,
   'tx-push': 0}

输入参数被解析为 JSON 格式，而输出则仅以 Python 的格式打印。这是因为在某些情况下，Netlink 类型不能直接表示为 JSON。如果在输入中需要此类属性，则需要对脚本进行修改。
规范和 Netlink 内部实现作为一个独立的库提取出来——这使得编写重用 ``cli.py`` 中代码的 Python 工具或测试变得容易。
生成内核代码
======================

``tools/net/ynl/ynl-regen.sh`` 扫描内核目录，查找需要更新的自动生成文件。使用此工具是最简单的生成或更新自动生成代码的方法。
默认情况下，只有当规范比源代码更新时才会重新生成代码；若要强制重新生成，请使用 ``-f`` 参数。
``ynl-regen.sh`` 在文件内容中搜索 ``YNL-GEN`` 标记（注意，它只扫描 git 索引中的文件，即仅跟踪 git 的文件！）。例如，内核源文件 ``fou_nl.c`` 包含以下内容：

  /*	Documentation/netlink/specs/fou.yaml */
  /* YNL-GEN kernel source */

``ynl-regen.sh`` 将找到这个标记，并根据 fou.yaml 替换文件内容。
根据规范生成新文件的最简单方法是在文件中添加上述两个标记行，将该文件添加到 git，并运行再生工具。通过 grep 查找树中的 ``YNL-GEN`` 可以看到其他示例。
代码生成本身由 ``tools/net/ynl/ynl-gen-c.py`` 完成，但由于它需要几个参数，因此直接调用它来逐个处理文件会变得很麻烦。
YNL库
======

``tools/net/ynl/lib/`` 包含了一个C库的实现（基于libmnl），该库与由 ``tools/net/ynl/ynl-gen-c.py`` 生成的代码结合，创建易于使用的Netlink包装器。

YNL基础
--------

YNL库由两部分组成——通用代码（函数以 ``ynl_`` 开头）和每个家族自动生成的代码（以家族名称开头）。
要创建一个YNL套接字，请调用 `ynl_sock_create()` 并传入家族结构体（家族结构体由自动生成的代码导出）。
`ynl_sock_destroy()` 用于关闭套接字。

YNL请求
--------

发出YNL请求的步骤最好通过一个例子来解释。此示例中的所有函数和类型均来自自动生成的代码（本例中为netdev家族）：

```c
// 0. 请求和响应指针
struct netdev_dev_get_req *req;
struct netdev_dev_get_rsp *d;

// 1. 分配一个请求
req = netdev_dev_get_req_alloc();
// 2. 设置请求参数（如有需要）
netdev_dev_get_req_set_ifindex(req, ifindex);

// 3. 发送请求
d = netdev_dev_get(ys, req);
// 4. 释放请求参数
netdev_dev_get_req_free(req);
// 5. 错误检查（检查第3步的返回值）
if (!d) {
    // 6. 打印YNL生成的错误信息
    fprintf(stderr, "YNL: %s\n", ys->err.msg);
    return -1;
}

// ... 使用响应@d进行处理

// 7. 释放响应
netdev_dev_get_rsp_free(d);
```

YNL转储
---------

执行转储遵循与请求类似的模式。转储返回一个对象列表，以特殊标记结束，或者在出错时返回NULL。使用 ``ynl_dump_foreach()`` 来遍历结果。

YNL通知
--------

YNL库支持在同一套接字上使用通知和请求。如果在处理请求期间收到通知，它们会被内部排队，并且可以在稍后的时间检索。
要订阅通知，请使用 ``ynl_subscribe()``。
必须从套接字中读取通知，`ynl_socket_get_fd()` 返回底层套接字文件描述符，可以将其插入适当的异步I/O API，如 ``poll`` 或 ``select``。
通知可以通过 `ynl_ntf_dequeue()` 获取，并且需要使用 `ynl_ntf_free()` 释放。由于我们事先不知道通知的类型，因此通知以 `struct ynl_ntf_base_type *` 的形式返回，用户需要根据 `cmd` 成员将它们转换为适当的完整类型。
