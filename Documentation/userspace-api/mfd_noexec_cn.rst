SPDX 许可证标识符: GPL-2.0

==================================
非可执行 mfd 的介绍
==================================
:作者:
    Daniel Verkamp <dverkamp@chromium.org>
    Jeff Xu <jeffxu@chromium.org>

:贡献者:
    Aleksa Sarai <cyphar@cyphar.com>

自从 Linux 引入了 memfd 特性以来，memfd 始终带有可执行位，并且 memfd_create() 系统调用不允许设置为其他状态。
然而，在默认安全的系统中（如 ChromeOS，其中所有可执行文件都应来自由验证引导保护的根文件系统），memfd 的可执行性质打开了一个绕过 NoExec 的途径，并使“困惑副手攻击”成为可能。例如，在 VRP 漏洞 [1] 中：cros_vm 进程创建了一个 memfd 来与外部进程共享内容，然而该 memfd 被覆盖并用于执行任意代码和提权。[2] 列出了更多此类 VRP 漏洞。
另一方面，可执行的 memfd 也有其合法用途：runc 使用 memfd 的封印和可执行特性来复制二进制文件的内容然后执行它们。对于这样的系统，我们需要一个解决方案来区分 runc 对可执行 memfd 的使用和攻击者的使用 [3]。

为了解决上述问题：
- 允许 memfd_create() 在创建时设置 X 位
- 当 NX 设置时，让 memfd 封印以防止修改 X 位
- 添加一个新的 PID 命名空间 sysctl：vm.memfd_noexec，以帮助应用程序迁移和强制实施不可执行的 MFD

用户 API
========
``int memfd_create(const char *name, unsigned int flags)``

``MFD_NOEXEC_SEAL``
    当在 ``flags`` 中设置了 MFD_NOEXEC_SEAL 位时，memfd 将带有 NX 创建。F_SEAL_EXEC 被设置，memfd 不能被修改以添加 X。同时隐含设置了 MFD_ALLOW_SEALING
这是应用程序使用 memfd 最常见的情况

``MFD_EXEC``
    当在 ``flags`` 中设置了 MFD_EXEC 位时，memfd 将带有 X 创建

注意:
    ``MFD_NOEXEC_SEAL`` 隐含了 ``MFD_ALLOW_SEALING``。如果某个应用程序不希望封印，可以在创建后添加 F_SEAL_SEAL
Sysctl:
========

``pid 命名空间下的 sysctl vm.memfd_noexec``

新的 pid 命名空间下的 sysctl vm.memfd_noexec 有 3 个值：

- 0: MEMFD_NOEXEC_SCOPE_EXEC  
  memfd_create() 在没有设置 MFD_EXEC 也没有设置 MFD_NOEXEC_SEAL 的情况下，行为如同设置了 MFD_EXEC。
- 1: MEMFD_NOEXEC_SCOPE_NOEXEC_SEAL  
  memfd_create() 在没有设置 MFD_EXEC 也没有设置 MFD_NOEXEC_SEAL 的情况下，行为如同设置了 MFD_NOEXEC_SEAL。
- 2: MEMFD_NOEXEC_SCOPE_NOEXEC_ENFORCED  
  memfd_create() 在没有设置 MFD_NOEXEC_SEAL 的情况下将被拒绝。

该 sysctl 允许对 memfd_create 进行更细粒度的控制，以适应旧软件未设置可执行位的情况；例如，在一个容器中设置 vm.memfd_noexec=1 表示旧软件默认会创建不可执行的 memfd，而新软件可以通过设置 MFD_EXEC 来创建可执行的 memfd。

vm.memfd_noexec 的值会在创建子命名空间时传递给子命名空间。此外，该设置是层次化的，即在调用 memfd_create 时，会从当前命名空间一直搜索到根命名空间，并使用最严格的设置。

[1] https://crbug.com/1305267

[2] https://bugs.chromium.org/p/chromium/issues/list?q=type%3Dbug-security%20memfd%20escalation&can=1

[3] https://lwn.net/Articles/781013/
