### SPDX 许可证标识符: GPL-2.0

#### Netconsole

##### 开始于2001年9月17日，由 Ingo Molnar <mingo@redhat.com>

2.6版本端口和 netpoll API 由 Matt Mackall <mpm@selenic.com> 在2003年9月9日开发。

IPv6支持由 Cong Wang <xiyou.wangcong@gmail.com> 在2013年1月1日添加。

扩展控制台支持由 Tejun Heo <tj@kernel.org> 在2015年5月1日增加。

发布预置支持由 Breno Leitao <leitao@debian.org> 在2023年7月7日加入。

用户数据后置支持由 Matthew Wood <thepacketgeek@gmail.com> 在2024年1月22日添加。

请将错误报告发送给 Matt Mackall <mpm@selenic.com>, Satyam Sharma <satyam.sharma@gmail.com> 和 Cong Wang <xiyou.wangcong@gmail.com>

### 简介：

此模块通过UDP记录内核的printk消息，适用于磁盘记录失败或串行控制台不实用的情况进行调试。它可以作为内置模块或独立模块使用。作为内置模块时，netconsole会在网卡初始化后立即启动，并尽可能快地激活指定接口。虽然这样无法捕捉到早期的内核恐慌信息，但它能够捕获大部分启动过程的信息。
发送者和接收者的配置：
------------------------------

它接受一个格式化的字符串配置参数“netconsole”，格式如下：

```
netconsole=[+][r][src-port]@[src-ip]/[<dev>],[tgt-port]@<tgt-ip>/[tgt-macaddr]
```

其中：
- `+`：如果存在，则启用扩展控制台支持。
- `r`：如果存在，则在消息前附加内核版本（发布）。
- `src-port`：UDP包的源端口（默认为6665）。
- `src-ip`：要使用的源IP地址（接口地址）。
- `dev`：网络接口（例如eth0）。
- `tgt-port`：日志代理的端口（默认为6666）。
- `tgt-ip`：日志代理的IP地址。
- `tgt-macaddr`：日志代理的以太网MAC地址（广播）。

示例：

```
linux netconsole=4444@10.0.0.1/eth1,9353@10.0.0.2/12:34:56:78:9a:bc
```

或者：

```
insmod netconsole netconsole=@/,@10.0.0.2/
```

或者使用IPv6：

```
insmod netconsole netconsole=@/,@fd00:1:2:3::1/
```

也可以通过在分号分隔的多个参数中指定多个远程代理，并将整个字符串用引号括起来，来支持向多个远程代理记录日志，例如：

```
modprobe netconsole netconsole="@/,@10.0.0.2/;@/eth1,6892@10.0.0.3/"
```

内置的netconsole在TCP堆栈初始化后立即启动，并尝试在提供的地址上激活提供的设备。
远程主机有几种选项来接收内核消息，例如：

1. syslogd

2. netcat

   对于使用基于BSD的netcat版本的发行版（例如Fedora、openSUSE和Ubuntu），监听端口必须不带 `-p` 参数指定：

   ```
   nc -u -l -p <port> / nc -u -l <port>
   ```

   或者：

   ```
   netcat -u -l -p <port> / netcat -u -l <port>
   ```

3. socat

   ```
   socat udp-recv:<port> -
   ```

### 动态重新配置：

动态重新配置是netconsole的一个有用补充功能，允许远程记录目标在运行时通过基于configfs的用户空间接口被动态添加、移除或重新配置参数。
为了包含此功能，在构建netconsole模块（或内核，如果netconsole是内置的）时选择 CONFIG_NETCONSOLE_DYNAMIC 配置项。
以下是一些示例（假设configfs挂载在 `/sys/kernel/config` 目录下）。
要添加一个远程记录目标（目标名称可以是任意的）：

```
cd /sys/kernel/config/netconsole/
mkdir target1
```

注意新创建的目标具有默认参数值（如上所述），并且默认是禁用的——它们首先必须通过写入“1”到“enabled”属性（通常在设置相应参数之后）来启用，如下所述。
要移除一个目标：

```
rmdir /sys/kernel/config/netconsole/othertarget/
```

该接口向用户空间暴露了netconsole目标的以下参数：

| 属性 | 描述 | 读写类型 |
| --- | --- | --- |
| enabled | 当前此目标是否启用？ | 读写 |
| extended | 扩展模式是否启用 | 读写 |
| release | 是否在消息前附加内核版本 | 读写 |
| dev_name | 本地网络接口名称 | 读写 |
| local_port | 要使用的源UDP端口 | 读写 |
| remote_port | 远程代理的UDP端口 | 读写 |
| local_ip | 要使用的源IP地址 | 读写 |
| remote_ip | 远程代理的IP地址 | 读写 |
| local_mac | 本地接口的MAC地址 | 只读 |
| remote_mac | 远程代理的MAC地址 | 读写 |

“enabled”属性还用于控制是否可以更新目标的参数——只有当“enabled”为0（即目标已禁用）时，才能修改其参数。
要更新目标的参数：

```
cat enabled  # 检查enabled是否为1
echo 0 > enabled  # 禁用目标（如果需要）
echo eth2 > dev_name  # 设置本地接口
echo 10.0.0.4 > remote_ip  # 更新某个参数
echo cb:a9:87:65:43:21 > remote_mac  # 更新更多参数
echo 1 > enabled  # 再次启用目标
```

您还可以动态更新本地接口。这对于想要使用新出现的接口（在netconsole加载或初始化时可能不存在）特别有用。
通过`netconsole=`参数在启动时间（或模块加载时间）定义的netconsole目标被分配名为`cmdline<index>`。例如，第一个目标的名称为`cmdline0`。您可以通过创建与之匹配名称的configfs目录来控制和修改这些目标。
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

追加用户数据
------------

启用 netconsole 动态配置后，可以将自定义的用户数据附加到消息末尾。可以在不改变目标的“enabled”属性的情况下修改用户数据条目。
`userdata`目录（键）的长度限制为53个字符，并且`userdata/<key>/value`中的数据长度限制为200字节：

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

发送：

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

如果创建了一个`userdata`条目但没有向`value`文件写入任何数据，则该条目将从 netconsole 消息中省略：

```
cd /sys/kernel/config/netconsole && mkdir cmdline0
cd cmdline0
mkdir userdata/foo
echo bar > userdata/foo/value
mkdir userdata/qux
```

`qux`键被省略，因为它没有值：

```
echo "This is a message" > /dev/kmsg
12,607,22085407756,-;This is a message
 foo=bar
```

使用`rmdir`删除`userdata`条目：

```
rmdir /sys/kernel/config/netconsole/cmdline0/userdata/qux
```

**警告**：
当向用户数据值写入字符串时，输入会在configfs存储调用中按行分割，这可能会导致令人困惑的行为：

```
mkdir userdata/testing
printf "val1\nval2" > userdata/testing/value
# userdata 存储值被调用了两次，第一次是"val1\n"，然后是"val2"
# 所以"val2"被存储，因为它是最后存储的值
cat userdata/testing/value
val2
```

建议不要在用户数据值中写入带有换行符的内容。

扩展控制台：
=============

如果在配置行前加上'+'或"extended"配置文件设置为1，则启用扩展控制台支持。下面是一个示例启动参数：

```
linux netconsole=+4444@10.0.0.1/eth1,9353@10.0.0.2/12:34:56:78:9a:bc
```

日志消息以扩展元数据头的形式传输，格式与/dev/kmsg相同：

```
<level>,<sequnum>,<timestamp>,<contflag>;<message text>
```

如果启用了'r'（发布）功能，内核版本号会前置在消息开始处。例如：

```
6.4.0,6,444,501151268,-;netconsole: network logging started
```

<message text>中的非可打印字符使用"\xff"符号进行转义。如果消息包含可选词典，则使用实际的换行符作为分隔符。
如果一条消息无法装入一定数量的字节（目前为1000字节），netconsole 将消息拆分为多个片段。这些片段在传输时会添加"ncfrag"头字段：

```
ncfrag=<byte-offset>/<total-bytes>
```

例如，假设一个更小的数据块大小，消息"the first chunk, the 2nd chunk."可能会被拆分为如下所示：

```
6,416,1758426,-,ncfrag=0/31;the first chunk,
6,416,1758426,-,ncfrag=16/31; the 2nd chunk.
```

杂项说明：
==========

**警告**：
默认的目标以太网设置使用广播以太网地址发送数据包，这可能导致同一以太网段上的其他系统的负载增加。

**提示**：
某些局域网交换机可能配置为抑制以太网广播，因此建议从 netconsole 的配置参数中明确指定远程代理的MAC地址。

**提示**：
要找出例如 10.0.0.2 的 MAC 地址，你可以尝试使用以下命令：

```
ping -c 1 10.0.0.2 ; /sbin/arp -n | grep 10.0.0.2
```

**提示**：
如果远程记录代理位于与发送者不同的局域网子网中，建议尝试指定默认网关的 MAC 地址（你可以使用/sbin/route -n 来找出它）作为远程 MAC 地址。

**注意**：
网络设备（如上述情况中的 eth1）可以运行任何类型的其他网络流量，netconsole 不会干扰。如果内核消息的数量很高，netconsole 可能会导致其他流量略有延迟，但不应产生其他影响。

**注意**：
如果你发现远程记录代理没有接收或打印所有来自发送者的消息，很可能是你设置了"console_loglevel"参数（在发送者上），仅发送高优先级消息到控制台。你可以使用以下命令在运行时更改此设置：

```
dmesg -n 8
```

或者在启动时在内核命令行中指定"debug"，以便将所有内核消息发送到控制台。也可以使用"loglevel"内核启动选项设置此参数的具体值。有关详细信息，请参阅 dmesg(8) 手册页和 Documentation/admin-guide/kernel-parameters.rst。

netconsole 设计尽可能即时，以使能够记录最严重的内核错误。它也可以从中断上下文中工作，并在发送数据包时不启用中断。由于这些独特的需求，配置不能更自动化，一些根本性的限制将仍然存在：只支持IP网络、UDP数据包和以太网设备。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
