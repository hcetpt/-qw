.. 许可证标识符：GPL-2.0
.. 版权所有 (C) 2022 Casey Schaufler <casey@schaufler-ca.com>
.. 版权所有 (C) 2022 Intel Corporation

=====================================
Linux 安全模块
=====================================

:作者: Casey Schaufler
:日期: 2023年7月

Linux 安全模块（LSM）提供了一种机制来实现对 Linux 安全策略的额外访问控制。各种安全模块可以支持以下任何属性：

- `LSM_ATTR_CURRENT` 是进程当前活动的安全上下文。
  - 该值在 `/proc/self/attr/current` 中提供。
  - 这由 SELinux、Smack 和 AppArmor 安全模块支持。
  - Smack 还在 `/proc/self/attr/smack/current` 中提供该值。
  - AppArmor 还在 `/proc/self/attr/apparmor/current` 中提供该值。

- `LSM_ATTR_EXEC` 是进程在执行当前镜像时的安全上下文。
  - 该值在 `/proc/self/attr/exec` 中提供。
  - 这由 SELinux 和 AppArmor 安全模块支持。
  - AppArmor 还在 `/proc/self/attr/apparmor/exec` 中提供该值。
``LSM_ATTR_FSCREATE`` 是在创建文件系统对象时所使用的进程的安全上下文。
该值由 proc 文件系统在 ``/proc/self/attr/fscreate`` 中提供。
这是由 SELinux 安全模块支持的。

``LSM_ATTR_KEYCREATE`` 是在创建密钥对象时所使用的进程的安全上下文。
该值由 proc 文件系统在 ``/proc/self/attr/keycreate`` 中提供。
这是由 SELinux 安全模块支持的。

``LSM_ATTR_PREV`` 是在设置当前安全上下文时的进程的安全上下文。
该值由 proc 文件系统在 ``/proc/self/attr/prev`` 中提供。
这是由 SELinux 和 AppArmor 安全模块支持的。
AppArmor 也在 ``/proc/self/attr/apparmor/prev`` 中提供该值。
``LSM_ATTR_SOCKCREATE`` 是在创建套接字对象时所使用的进程的安全上下文。
该值可以通过 ``/proc/self/attr/sockcreate`` 在 proc 文件系统中获取。
这是由 SELinux 安全模块支持的。

内核接口
=========

设置当前进程的安全属性
--------------------------

.. kernel-doc:: security/lsm_syscalls.c
    :identifiers: sys_lsm_set_self_attr

获取当前进程指定的安全属性
----------------------------

.. kernel-doc:: security/lsm_syscalls.c
    :identifiers: sys_lsm_get_self_attr

.. kernel-doc:: security/lsm_syscalls.c
    :identifiers: sys_lsm_list_modules

附加文档
=========

* 文档/security/lsm.rst
* 文档/security/lsm-development.rst
