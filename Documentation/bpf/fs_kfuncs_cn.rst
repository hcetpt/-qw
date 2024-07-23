SPDX 许可证标识符：GPL-2.0

.. _fs_kfuncs-header-label:

=====================
BPF 文件系统 kfuncs
=====================

BPF LSM 程序需要从 LSM 钩子中访问文件系统数据。以下 BPF kfuncs 可用于获取这些数据：
* ``bpf_get_file_xattr()``

* ``bpf_get_fsverity_digest()``

为了避免递归，这些 kfuncs 遵循以下规则：

1. 这些 kfuncs 仅允许从 BPF LSM 函数中调用。
2. 这些 kfuncs 不应调用其他 LSM 钩子，即 security_*()。例如，``bpf_get_file_xattr()`` 不使用 ``vfs_getxattr()``，因为后者会调用 LSM 钩子 ``security_inode_getxattr``。
