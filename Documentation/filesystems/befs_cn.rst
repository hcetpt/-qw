SPDX 许可声明标识符: GPL-2.0

=========================
BeOS 文件系统 for Linux
=========================

文档最后更新日期：2001年12月6日

警告
=======
请注意，这是一个 Alpha 阶段的软件。这意味着实现既不完整也未经充分测试。
我对于此代码可能引起的任何不良后果概不负责！

许可
=======
本软件受 GNU 通用公共许可证（GNU General Public License）保护。
请参阅文件 COPYING 以获取完整的许可文本，
或者访问 GNU 网站：<http://www.gnu.org/licenses/licenses.html>

作者
======
大部分代码由 Will Dyson 编写 <will_dyson@pobox.com>。
他自2001年8月13日起一直在开发此代码。详见变更日志。
原作者：Makoto Kato <m_kato@ga2.so-net.ne.jp>

他的原始代码仍可以在以下地址找到：
<http://hp.vector.co.jp/authors/VA008030/bfs/>

有人知道 Makoto 的更当前的电子邮件地址吗？他没有回应上面提供的地址。
这个文件系统目前没有维护者。

这是什么驱动？
====================
该模块实现了 BeOS 的原生文件系统（http://www.beincorporated.com/）
适用于 Linux 2.4.1 及以上内核。目前它是一个只读实现。

是 BFS 还是 BEFS？
=========================
Be, Inc 表示，“BeOS 文件系统正式名称为 BFS，而不是 BeFS。”
但是 Unixware 的启动文件系统也叫 bfs，并且它们已经在内核中了。
由于这种命名冲突，在 Linux 中 BeOS 文件系统被称为 befs。

如何安装
==============
步骤 1. 将 BeFS 补丁安装到 Linux 源代码树中
将补丁文件应用到内核源码树中
假设你的内核源码位于 `/foo/bar/linux`，并且补丁文件名为 `patch-befs-xxx`，你需要执行以下命令：

```shell
cd /foo/bar/linux
patch -p1 < /path/to/patch-befs-xxx
```

如果补丁步骤失败（即有被拒绝的补丁块），你可以尝试自己解决（这不应该很难），或者联系维护者 Will Dyson (`will_dyson@pobox.com`) 寻求帮助。

### 第二步：配置与编译内核

Linux 内核有许多编译时选项。大多数选项超出了本文档的范围。我建议参考《Kernel-HOWTO》文档作为该主题的良好通用参考：[http://www.linuxdocs.org/HOWTOs/Kernel-HOWTO-4.html](http://www.linuxdocs.org/HOWTOs/Kernel-HOWTO-4.html)

然而，要使用 BeFS 模块，你必须在配置时启用它：

```shell
cd /foo/bar/linux
make menuconfig (或 xconfig)
```

BeFS 模块不是 Linux 内核的标准部分，因此你必须首先在“代码成熟度级别”菜单下启用对实验性代码的支持。然后，在“文件系统”菜单下会有一个选项叫做“BeFS 文件系统（实验性）”，或者类似的名字。启用这个选项（将其设置为模块是可行的）。
保存你的内核配置并构建内核。

### 第三步：安装

参见内核 HOWTO [http://www.linux.com/howto/Kernel-HOWTO.html] 以获取这个关键步骤的说明。

### 使用 BeFS
为了使用 BeOS 文件系统，请使用文件系统类型 `befs`：
例如：

```shell
mount -t befs /dev/fd0 /beos
```

### Mount 选项

| 选项      | 描述                                                         |
|-----------|--------------------------------------------------------------|
| uid=nnn   | 分区中的所有文件都将归用户 ID nnn 所有                         |
| gid=nnn   | 分区中的所有文件都属于组 ID nnn                               |
| iocharset=xxx | 使用 xxx 作为 NLS 翻译表的名称                                 |
调试           驱动程序将调试信息输出到系统日志
=============  ===========================================================

如何获取最新版本
=========================

最新版本目前可在以下地址获取：
<http://befs-driver.sourceforge.net/>

已知的问题？
===============
截至2002年1月20日：

	无

特别感谢
==============
多米尼克·詹帕洛 ... 撰写《使用 Be 文件系统的实用文件系统设计》

山田浩之 ... 测试 LinuxPPC
