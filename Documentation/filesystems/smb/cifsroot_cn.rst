SPDX 许可证标识符: GPL-2.0

===========================================
通过 SMB（cifs.ko）挂载根文件系统
===========================================

2019 年由 Paulo Alcantara 编写 <palcantara@suse.de>

2019 年由 Aurelien Aptel 编写 <aaptel@suse.com>

CONFIG_CIFS_ROOT 选项启用了通过 SMB 协议使用 cifs.ko 的实验性根文件系统支持。它引入了一个新的内核命令行选项 'cifsroot='，该选项会告诉内核通过网络利用 SMB 或 CIFS 协议来挂载根文件系统。

为了进行挂载，还需要通过 'ip=' 配置选项设置网络堆栈。更多详细信息，请参阅 Documentation/admin-guide/nfs/nfsroot.rst。

目前，CIFS 根挂载需要使用 SMB1+UNIX 扩展功能，这仅由 Samba 服务器支持。SMB1 是该协议的旧版且已被弃用，但它已经扩展以支持 POSIX 特性（见 [1]）。较新推荐版本（SMB3）的等效扩展尚未完全实现，这意味着 SMB3 不支持某些必需的 POSIX 文件系统对象（例如块设备、管道、套接字）。

因此，目前 CIFS 根挂载默认使用 SMB1，但可以通过 'vers=' 挂载选项更改使用的版本。一旦 SMB3 POSIX 扩展功能完全实现，此默认值将会改变。

服务器配置
====================

要在 Samba smb.conf 中启用 SMB1+UNIX 扩展功能，您需要设置以下全局选项：

```plaintext
[global]
server min protocol = NT1
unix extension = yes        # 默认值
```

内核命令行
===================

```plaintext
root=/dev/cifs
```

这是一个虚拟设备，基本上告诉内核通过 SMB 协议挂载根文件系统。

```plaintext
cifsroot=//<server-ip>/<share>[,options]
```

此选项使内核能够挂载位于 <server-ip> 和 <share> 指定位置的 SMB 上的根文件系统。

默认挂载选项设置在 fs/smb/client/cifsroot.c 中。

- server-ip：服务器的 IPv4 地址。
- share：SMB 共享（根文件系统）的路径。
选项
可选的挂载选项。更多信息，请参见 `mount.cifs(8)`。

示例
====

在 smb.conf 文件中将根文件系统导出为 Samba 共享：

```
..
[linux]
    path = /path/to/rootfs
    read only = no
    guest ok = yes
    force user = root
    force group = root
    browseable = yes
    writeable = yes
    admin users = root
    public = yes
    create mask = 0777
    directory mask = 0777
..
```

重启 smb 服务：

```
# systemctl restart smb
```

在 QEMU 中使用启用了 CONFIG_CIFS_ROOT 和 CONFIG_IP_PNP 选项的内核进行测试：

```
# qemu-system-x86_64 -enable-kvm -cpu host -m 1024 \
-mkernel /path/to/linux/arch/x86/boot/bzImage -nographic \
-append "root=/dev/cifs rw ip=dhcp cifsroot=//10.0.2.2/linux,username=foo,password=bar console=ttyS0 3"
```

参考资料：
1: https://wiki.samba.org/index.php/UNIX_Extensions
