SPDX 许可证标识符：(GPL-2.0 或 BSD-2-Clause)

=====================
BPF sk_lookup 程序
=====================

BPF sk_lookup 程序类型（`BPF_PROG_TYPE_SK_LOOKUP`）为传输层在数据包需要本地递送时查找套接字的过程引入了可编程性。
当被调用时，BPF sk_lookup 程序可以通过调用 `bpf_sk_assign()` BPF 辅助函数来选择将接收传入数据包的套接字。
对于常见的绑定点（`BPF_SK_LOOKUP`），TCP 和 UDP 都存在相应的钩子。
动机
==========

引入 BPF sk_lookup 程序类型的目的是为了处理以下场景，在这些场景中使用 `bind()` 套接字调用来绑定套接字到地址是不切实际的，例如：

1. 在一系列 IP 地址上（如 192.0.2.0/24）接收连接，当由于端口冲突而无法绑定到通配符地址 `INADDR_ANY` 时，
2. 在所有或广泛范围的端口上接收连接，即第 7 层代理的使用案例
这样的设置将要求为范围内的每个 IP 地址/端口创建并绑定一个套接字，这将导致资源消耗增加和套接字查找时潜在的延迟峰值。
绑定
==========

BPF sk_lookup 程序可以使用 `bpf(BPF_LINK_CREATE, ...)` 系统调用，并使用 `BPF_SK_LOOKUP` 类型以及网络命名空间文件描述符作为绑定目标 `target_fd` 来绑定到网络命名空间。
多个程序可以绑定到同一个网络命名空间。程序将以它们被绑定的相同顺序被调用。
钩子
=====

已绑定的 BPF sk_lookup 程序会在传输层需要为传入的数据包找到监听（TCP）或未连接（UDP）套接字时运行。
已建立（TCP）和已连接（UDP）套接字的传入流量将像往常一样递送，不会触发 BPF sk_lookup 钩子。
已绑定的 BPF 程序必须返回 `SK_PASS` 或 `SK_DROP` 的判决代码。与其它作为网络过滤器的 BPF 程序类型一样，`SK_PASS` 表示套接字查找应继续进行常规的哈希表查找，而 `SK_DROP` 则会导致传输层丢弃该数据包。
一个BPF `sk_lookup` 程序也可以通过调用 `bpf_sk_assign()` BPF辅助函数来选择一个套接字接收数据包。通常，该程序会在存储套接字的映射（如 `SOCKMAP` 或 `SOCKHASH`）中查找套接字，并将 `struct bpf_sock *` 传递给 `bpf_sk_assign()` 辅助函数来记录这个选择。只有当程序以 `SK_PASS` 代码终止时，选择套接字才会生效。

当有多个程序被附加时，最终结果根据所有程序返回码的以下规则确定：

1. 如果任何程序返回了 `SK_PASS` 并选择了有效的套接字，则使用此套接字作为套接字查找的结果。
2. 如果不止一个程序返回了 `SK_PASS` 并选择了套接字，则最后一个选择生效。
3. 如果任何程序返回了 `SK_DROP`，且没有程序返回 `SK_PASS` 并选择了套接字，则套接字查找失败。
4. 如果所有程序都返回了 `SK_PASS` 而没有选择任何套接字，则继续进行套接字查找。

### API

在它的上下文中，一个 `struct bpf_sk_lookup` 实例会接收到触发套接字查找的数据包的相关信息，具体包括：

* IP版本 (`AF_INET` 或 `AF_INET6`)，
* 第四层协议标识符 (`IPPROTO_TCP` 或 `IPPROTO_UDP`)，
* 源和目的IP地址，
* 源和目的第四层端口，
* 使用 `bpf_sk_assign()` 选择的套接字。

请参考 `linux/bpf.h` 用户API头文件中 `struct bpf_sk_lookup` 的声明，以及 `bpf-helpers(7)` 手册页中的 `bpf_sk_assign()` 部分获取详细信息。

### 示例

请参阅 `tools/testing/selftests/bpf/prog_tests/sk_lookup.c` 获取参考实现。
