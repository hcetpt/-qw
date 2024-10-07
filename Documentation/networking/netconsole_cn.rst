```
SPDX 许可证标识符: GPL-2.0

==========
Netconsole
==========

由 Ingo Molnar <mingo@redhat.com> 开始，2001年9月17日

2.6 版本端口和 netpoll API 由 Matt Mackall <mpm@selenic.com> 完成，2003年9月9日

IPv6 支持由 Cong Wang <xiyou.wangcong@gmail.com> 完成，2013年1月1日

扩展控制台支持由 Tejun Heo <tj@kernel.org> 完成，2015年5月1日

发布前缀支持由 Breno Leitao <leitao@debian.org> 完成，2023年7月7日

用户数据附加支持由 Matthew Wood <thepacketgeek@gmail.com> 完成，2024年1月22日

请将错误报告发送给 Matt Mackall <mpm@selenic.com>、Satyam Sharma <satyam.sharma@gmail.com> 和 Cong Wang <xiyou.wangcong@gmail.com>

简介：
=============

此模块通过 UDP 日志记录内核的 printk 消息，允许在磁盘日志记录失败且串行控制台不切实际的情况下进行调试。它可以作为内置模块或单独模块使用。作为内置模块时，netconsole 在 NIC 卡初始化后立即启动，并尽可能快地启用指定接口。虽然这无法捕获早期内核恐慌信息，但可以捕获大部分引导过程。

发送者和接收者配置：
==================================

它接受一个字符串配置参数“netconsole”，格式如下：

```
netconsole=[+][r][src-port]@[src-ip]/[<dev>],[tgt-port]@<tgt-ip>/[tgt-macaddr]
```

其中：
+            如果存在，则启用扩展控制台支持
r            如果存在，则在消息前加上内核版本（发布）
src-port     UDP 数据包的源端口（默认为 6665）
src-ip       要使用的源 IP 地址（接口地址）
dev          网络接口（例如 eth0）
tgt-port     日志代理的端口（默认为 6666）
tgt-ip       日志代理的 IP 地址
tgt-macaddr  日志代理的以太网 MAC 地址（广播）

示例：

```
linux netconsole=4444@10.0.0.1/eth1,9353@10.0.0.2/12:34:56:78:9a:bc
```

或者：

```
insmod netconsole netconsole=@/,@10.0.0.2/
```

或者使用 IPv6：

```
insmod netconsole netconsole=@/,@fd00:1:2:3::1/
```

还可以通过分号分隔多个远程代理的参数并在双引号中包含完整字符串来支持记录到多个远程代理：

```
modprobe netconsole netconsole="@/,@10.0.0.2/;@/eth1,6892@10.0.0.3/"
```

内置 netconsole 在 TCP 栈初始化后立即启动，并尝试在指定地址上启用提供的设备。
远程主机有几种选项来接收内核消息，例如：

1) syslogd

2) netcat

   对于使用基于 BSD 的 netcat 版本的发行版（例如 Fedora、openSUSE 和 Ubuntu），监听端口必须在没有 -p 选项的情况下指定：

```
nc -u -l -p <port> 或 nc -u -l <port>
```

或者：

```
netcat -u -l -p <port> 或 netcat -u -l <port>
```

3) socat

```
socat udp-recv:<port> -
```

动态重新配置：
========================

动态重新配置是 netconsole 的一项有用功能，允许通过基于 configfs 的用户空间接口在运行时动态添加、删除远程记录目标或重新配置其参数。要包含此功能，请在构建 netconsole 模块（或内核，如果 netconsole 是内置的）时选择 CONFIG_NETCONSOLE_DYNAMIC。

以下是一些示例（假设 configfs 挂载在 /sys/kernel/config）：

为了添加一个远程记录目标（目标名称可以任意）：

```
cd /sys/kernel/config/netconsole/
mkdir target1
```

请注意，新创建的目标具有默认参数值（如上所述），并且默认是禁用的——必须首先通过写入“1”到“enabled”属性（通常在设置相应参数之后）来启用它们，如下所述。
为了删除一个目标：

```
rmdir /sys/kernel/config/netconsole/othertarget/
```

该接口向用户空间暴露了 netconsole 目标的以下参数：

| 属性名 | 描述 | 类型 |
|--------|------|------|
| enabled | 当前目标是否已启用？ | 读写 |
| extended | 扩展模式是否启用 | 读写 |
| release | 是否在消息前加上内核版本 | 读写 |
| dev_name | 本地网络接口名称 | 读写 |
| local_port | 要使用的源 UDP 端口 | 读写 |
| remote_port | 远程代理的 UDP 端口 | 读写 |
| local_ip | 要使用的源 IP 地址 | 读写 |
| remote_ip | 远程代理的 IP 地址 | 读写 |
| local_mac | 本地接口的 MAC 地址 | 只读 |
| remote_mac | 远程代理的 MAC 地址 | 读写 |

“enabled” 属性还用于控制是否可以更新目标的参数——只有在目标被禁用时（即“enabled”为 0）才能修改其参数。
为了更新一个目标的参数：

```
cat enabled # 检查 enabled 是否为 1
echo 0 > enabled # 禁用目标（如果需要）
echo eth2 > dev_name # 设置本地接口
echo 10.0.0.4 > remote_ip # 更新某个参数
echo cb:a9:87:65:43:21 > remote_mac # 更新更多参数
echo 1 > enabled # 再次启用目标
```

您也可以动态更新本地接口。这对于想要使用新出现的接口特别有用（这些接口在 netconsole 加载或初始化时可能不存在）。
在引导时间（或模块加载时间）通过 `netconsole=` 参数定义的 netconsole 目标会分配名为 `cmdline<index>` 的名称。例如，第一个目标的名称为 `cmdline0`。您可以通过创建具有匹配名称的 configfs 目录来控制和修改这些目标。
```
让我们假设你在启动时定义了两个 netconsole 目标：

```
netconsole=4444@10.0.0.1/eth1,9353@10.0.0.2/12:34:56:78:9a:bc;4444@10.0.0.1/eth1,9353@10.0.0.3/12:34:56:78:9a:bc
```

你可以在运行时通过创建以下目标来修改这些目标：

```
mkdir cmdline0
cat cmdline0/remote_ip
10.0.0.2

mkdir cmdline1
cat cmdline1/remote_ip
10.0.0.3
```

附加用户数据
-------------

启用 netconsole 动态配置后，可以将自定义用户数据附加到消息的末尾。用户数据条目可以在不更改目标“enabled”属性的情况下进行修改。`userdata` 目录（键）的最大长度限制为 53 个字符，而 `userdata/<key>/value` 中的数据最大长度限制为 200 字节：

```
cd /sys/kernel/config/netconsole && mkdir cmdline0
cd cmdline0
mkdir userdata/foo
echo bar > userdata/foo/value
mkdir userdata/qux
echo baz > userdata/qux/value
```

现在消息将包含这些额外的用户数据：

```
echo "This is a message" > /dev/kmsg
```

发送内容如下：

```
12,607,22085407756,-;This is a message
foo=bar
qux=baz
```

预览将要附加的用户数据：

```
cd /sys/kernel/config/netconsole/cmdline0/userdata
for f in `ls userdata`; do echo $f=$(cat userdata/$f/value); done
```

如果创建了一个 `userdata` 条目但没有向 `value` 文件写入任何数据，则该条目将从 netconsole 消息中省略：

```
cd /sys/kernel/config/netconsole && mkdir cmdline0
cd cmdline0
mkdir userdata/foo
echo bar > userdata/foo/value
mkdir userdata/qux
```

由于 `qux` 没有值，因此会被省略：

```
echo "This is a message" > /dev/kmsg
12,607,22085407756,-;This is a message
foo=bar
```

使用 `rmdir` 删除 `userdata` 条目：

```
rmdir /sys/kernel/config/netconsole/cmdline0/userdata/qux
```

.. warning::
   当向用户数据值写入字符串时，输入会在 configfs 存储调用中按行分割，这可能会导致令人困惑的行为：

   ```
     mkdir userdata/testing
     printf "val1\nval2" > userdata/testing/value
     # 用户数据存储值被调用了两次，第一次是 "val1\n"，然后是 "val2"
     # 所以最后存储的是 "val2"
     cat userdata/testing/value
     val2
   ```

   建议不要在用户数据值中写入换行符。

扩展控制台：
============

如果在配置行前加上 '+' 或将 "extended" 配置文件设置为 1，则启用扩展控制台支持。一个示例启动参数如下：

```
linux netconsole=+4444@10.0.0.1/eth1,9353@10.0.0.2/12:34:56:78:9a:bc
```

日志消息将以扩展元数据头格式传输，其格式与 `/dev/kmsg` 相同：

```
<level>,<sequnum>,<timestamp>,<contflag>;<message text>
```

如果启用了 'r'（发布）功能，则内核版本号会附加到消息的开头。例如：

```
6.4.0,6,444,501151268,-;netconsole: network logging started
```

<message text> 中的不可打印字符使用 "\xff" 符号进行转义。如果消息包含可选字典，则使用换行符作为分隔符。
如果消息超出一定字节数（目前为 1000 字节），则 netconsole 会将消息拆分为多个片段，并添加 "ncfrag" 头字段：

```
ncfrag=<byte-offset>/<total-bytes>
```

例如，假设一个较小的块大小，消息 "the first chunk, the 2nd chunk." 可能拆分为：

```
6,416,1758426,-,ncfrag=0/31;the first chunk,
6,416,1758426,-,ncfrag=16/31; the 2nd chunk
```

其他注意事项：
=============

.. Warning::
   默认的目标以太网设置使用广播以太网地址发送数据包，这可能会增加同一以太网段上其他系统的负载。

.. Tip::
   一些局域网交换机可能配置为抑制以太网广播，因此建议从传递给 netconsole 的配置参数中显式指定远程代理的 MAC 地址。

.. Tip::
   要找出例如 10.0.0.2 的 MAC 地址，你可以尝试使用：

   ```
   ping -c 1 10.0.0.2 ; /sbin/arp -n | grep 10.0.0.2
   ```

.. Tip::
   如果远程日志代理位于与发送者不同的局域网子网中，建议尝试指定默认网关的 MAC 地址作为远程 MAC 地址（你可以使用 `/sbin/route -n` 查找它）。

.. note::
   网络设备（如上面例子中的 eth1）可以运行任何类型的网络流量，netconsole 不会干扰。如果内核消息量很大，netconsole 可能会导致其他流量略有延迟，但不应有其他影响。

.. note::
   如果你发现远程日志代理未接收到或打印所有来自发送者的消息，可能是你在发送者端设置了 “console_loglevel” 参数，仅发送高优先级消息到控制台。你可以使用以下命令在运行时更改此设置：

   ```
   dmesg -n 8
   ```

   或者在启动内核时指定 "debug" 以发送所有内核消息到控制台。也可以使用 "loglevel" 内核启动选项设置该参数的具体值。详情请参阅 `dmesg(8)` 手册页和 `Documentation/admin-guide/kernel-parameters.rst`。

netconsole 设计尽可能即时，以便记录最严重的内核错误。它可以在中断上下文中工作，并且在发送数据包时不启用中断。由于这些独特的需求，配置不能更加自动化，且存在一些基本限制：只支持 IP 网络、UDP 数据包和以太网设备。
当然，请提供您需要翻译的文本。
