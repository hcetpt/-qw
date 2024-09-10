SPDX 许可证标识符: GPL-2.0

======================================================
eCryptfs：用于 Linux 的分层加密文件系统
======================================================

eCryptfs 是自由软件。详情请参见 COPYING 文件。
文档请参见 doc/ 子目录中的文件。编译和安装说明请参见 INSTALL 文件。
:维护者: Phillip Hellewell
:首席开发者: Michael A. Halcrow <mhalcrow@us.ibm.com>
:开发者: Michael C. Thompson
         Kent Yoder
:网站: http://ecryptfs.sf.net

该软件目前正在进行开发。请确保备份任何写入 eCryptfs 的数据。
eCryptfs 需要用户空间工具，可以从 SourceForge 网站下载：

http://sourceforge.net/projects/ecryptfs/

用户空间要求包括：

- David Howells 的用户空间密钥环头文件和库（版本 1.0 或更高），可从
  http://people.redhat.com/~dhowells/keyutils/ 获取
- Libgcrypt

.. 注意::

   在 eCryptfs 的测试版/实验版中，当您升级 eCryptfs 时，应将文件复制到未加密的位置，
   然后将文件重新复制到新的 eCryptfs 挂载点以迁移文件。

全挂载密码短语
=====================

创建一个新目录，eCryptfs 将在此目录中写入其加密文件（例如，/root/crypt）。
然后，创建挂载点目录（例如，/mnt/crypt）。现在可以挂载 eCryptfs 了：

    mount -t ecryptfs /root/crypt /mnt/crypt

您应该会被提示输入密码和盐（盐可以为空）
尝试写入一个新文件：

    echo "Hello, World" > /mnt/crypt/hello.txt

操作将完成。注意在 /root/crypt 中有一个至少为 12288 字节大小的新文件（取决于您的主机页大小）。
这是您刚刚写入内容的底层加密文件。为了测试读取过程，请先清除用户会话密钥环：

    keyctl clear @u

然后卸载 /mnt/crypt 并根据上述说明重新挂载：

    cat /mnt/crypt/hello.txt

注意事项
=====

eCryptfs 版本 0.1 只能挂载到（1）空目录或（2）仅包含由 eCryptfs 创建的文件的目录。
如果您挂载了一个包含非 eCryptfs 创建的现有文件的目录，则行为是不确定的。
除非您出于调试或开发目的，否则不要在更高的详细级别下运行 eCryptfs，
因为这样会导致秘密值被写入系统日志。
Mike Halcrow
mhalcrow@us.ibm.com
