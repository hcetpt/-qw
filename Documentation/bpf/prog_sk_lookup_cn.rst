SPDX 许可证标识符：(GPL-2.0 或 BSD-2-Clause)

=====================
BPF sk_lookup 程序
=====================

BPF sk_lookup 程序类型（`BPF_PROG_TYPE_SK_LOOKUP`）为传输层在数据包需要本地递送时执行的套接字查找引入了可编程性。
当被调用时，BPF sk_lookup 程序可以通过调用 `bpf_sk_assign()` BPF 辅助函数来选择接收传入数据包的套接字。
对于常见的附加点（`BPF_SK_LOOKUP`），TCP 和 UDP 都存在相应的钩子。

动机
==========

引入 BPF sk_lookup 程序类型的目的是为了处理以下场景，在这些场景中使用 `bind()` 套接字调用来绑定套接字到地址是不切实际的，例如：

1. 在一系列 IP 地址上接收连接，例如 192.0.2.0/24，当由于端口冲突无法使用通配符地址 `INADDR_ANY` 时，
2. 在所有或广泛范围的端口上接收连接，即第 7 层代理的使用案例。
此类设置将要求为范围内的每个 IP 地址/端口创建并使用 `bind()` 绑定一个套接字，这将导致资源消耗增加和潜在的套接字查找延迟峰值。

附加
==========

可以使用 `bpf(BPF_LINK_CREATE, ...)` 系统调用以及 `BPF_SK_LOOKUP` 附加类型和 netns 文件描述符作为附加目标 `target_fd` 将 BPF sk_lookup 程序附加到网络命名空间。
可以将多个程序附加到一个网络命名空间。程序将以它们被附加的相同顺序被调用。

钩子
=====

每当传输层需要为传入的数据包找到监听（TCP）或未连接（UDP）套接字时，都会运行已附加的 BPF sk_lookup 程序。
已建立（TCP）和已连接（UDP）套接字的传入流量将像往常一样被递送，不会触发 BPF sk_lookup 钩子。
已附加的 BPF 程序必须返回 `SK_PASS` 或 `SK_DROP` 的判决代码。与其他充当网络过滤器的 BPF 程序类型一样，`SK_PASS` 表示应继续进行常规的哈希表查找以查找套接字，而 `SK_DROP` 则会导致传输层丢弃该数据包。
一个BPF `sk_lookup` 程序也可以通过调用 `bpf_sk_assign()` BPF辅助函数来选择一个套接字接收数据包。通常，该程序会在存储套接字的映射（如 `SOCKMAP` 或 `SOCKHASH`）中查找套接字，并将 `struct bpf_sock *` 传递给 `bpf_sk_assign()` 辅助函数来记录这个选择。只有当程序以 `SK_PASS` 代码终止时，选择套接字才会生效。

当有多个程序附加时，最终结果根据所有程序返回码的规则决定：

1. 如果任一程序返回了 `SK_PASS` 并选择了有效的套接字，则使用该套接字作为套接字查找的结果。
2. 如果超过一个程序返回了 `SK_PASS` 并选择了套接字，则最后一次的选择生效。
3. 如果任一程序返回了 `SK_DROP`，且没有程序返回 `SK_PASS` 并选择了套接字，则套接字查找失败。
4. 如果所有程序都返回了 `SK_PASS` 但没有选择任何套接字，则继续进行套接字查找。

### API

在它的上下文中，`struct bpf_sk_lookup` 的实例会接收到触发套接字查找的数据包的相关信息。具体包括：

- IP版本 (`AF_INET` 或 `AF_INET6`)，
- 第四层协议标识符 (`IPPROTO_TCP` 或 `IPPROTO_UDP`)，
- 源和目标IP地址，
- 源和目标第四层端口，
- 通过 `bpf_sk_assign()` 选择的套接字。

有关详细信息，请参阅用户API头文件 `linux/bpf.h` 中 `struct bpf_sk_lookup` 的声明以及 `bpf-helpers(7)` 手册页中的 `bpf_sk_assign()` 部分。

### 示例

请参阅 `tools/testing/selftests/bpf/prog_tests/sk_lookup.c` 获取参考实现。
