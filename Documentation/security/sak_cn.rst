=============================
Linux 安全注意键 (SAK) 处理
=============================

:日期: 2001年3月18日
:作者: Andrew Morton

操作系统的安全注意键（Secure Attention Key，简称SAK）是一种安全工具，旨在防止特洛伊木马密码捕获程序。这是一种不可被击败的方法，可以杀死所有可能伪装成登录应用程序的程序。用户需要学会在登录系统之前输入这个键序列。

从PC键盘来看，Linux提供了两种相似但不同的方式来提供SAK。一种是ALT-SYSRQ-K序列。你不应该使用这个序列。它只有在内核编译时启用了sysrq支持的情况下才可用。
生成SAK的正确方法是使用`loadkeys`定义键序列。这无论是否在内核中编译了sysrq支持都能工作。
当键盘处于原始模式时，SAK能正常工作。这意味着一旦定义好，SAK将能够终止运行中的X服务器。如果系统处于运行级别5，X服务器将会重启。这是你希望发生的情况。
你应该使用哪个键序列呢？嗯，CTRL-ALT-DEL用于重新启动机器。CTRL-ALT-BACKSPACE对X服务器有特殊作用。我们将选择CTRL-ALT-PAUSE。
在你的rc.sysinit（或rc.local）文件中添加如下命令::

    echo "control alt keycode 101 = SAK" | /bin/loadkeys

就这样！只有超级用户才能重新编程SAK键。
.. note::

  1. 据说Linux SAK并不是C2级安全系统所要求的“真正的SAK”。作者并不知道原因。
  2. 在PC键盘上，SAK会杀死所有打开/dev/console的应用程序。
不幸的是，这包括了一些你实际上不希望被杀死的东西。这是因为这些应用程序错误地保持/dev/console打开。一定要向你的Linux发行版提供商投诉这个问题！

你可以通过以下命令来识别会被SAK杀死的进程::

    # ls -l /proc/[0-9]*/fd/* | grep console
    l-wx------    1 root     root           64 Mar 18 00:46 /proc/579/fd/0 -> /dev/console

然后::

    # ps aux|grep 579
    root       579  0.0  0.1  1088  436 ?        S    00:43   0:00 gpm -t ps/2

因此，“gpm”将被SAK杀死。这是一个gpm的bug。它应该关闭标准输入。你可以通过找到启动gpm的初始化脚本并进行如下修改来解决这个问题：

旧的配置::

    daemon gpm

新的配置::

    daemon gpm < /dev/null

Vixie cron似乎也有同样的问题，并且需要同样的处理。
此外，一个著名的Linux发行版在其rc.sysinit和rc脚本中有以下三行代码::

    exec 3<&0
    exec 4>&1
    exec 5>&2

这些命令会导致**所有**由初始化脚本启动的守护进程将其文件描述符3、4和5附加到/dev/console。因此，SAK会杀死它们。解决办法是简单地删除这些行，但这可能会导致系统管理应用程序出现故障——请彻底测试一切。
当然，请提供您需要翻译的文本。
