.. SPDX 许可证标识符: GPL-2.0

.. _GPIOHANDLE_SET_CONFIG_IOCTL:

***************************
GPIOHANDLE_SET_CONFIG_IOCTL
***************************

.. warning::
    此 ioctl 是 chardev_v1.rst 的一部分，并已被 gpio-v2-line-set-config-ioctl.rst 废弃。

名称
====

GPIOHANDLE_SET_CONFIG_IOCTL - 更新之前请求的线路配置

概要
====

.. c:macro:: GPIOHANDLE_SET_CONFIG_IOCTL

``int ioctl(int handle_fd, GPIOHANDLE_SET_CONFIG_IOCTL, struct gpiohandle_config *config)``

参数
====

``handle_fd``
    GPIO 字符设备的文件描述符，由 gpio-get-linehandle-ioctl.rst 返回的 :c:type:`request.fd<gpiohandle_request>`。
``config``
    要应用于已请求线路的新 :c:type:`配置<gpiohandle_config>`。

描述
====

在不释放线路或引入潜在故障的情况下更新之前请求的线路配置。
此配置适用于所有已请求的线路。
当请求线路时适用的相同 :ref:`gpio-get-linehandle-config-rules` 和 :ref:`gpio-get-linehandle-config-support` 在更新线路配置时也适用，但额外限制是必须设置方向标志。请求无效配置（包括未设置方向标志）将导致错误 (**EINVAL**)。
此命令的主要使用场景是在输入和输出之间改变双向线路的方向，但它也可以更广泛地用于无缝地将线路从一个配置状态移动到另一个配置状态。
要仅更改输出线路的值，请使用 gpio-handle-set-line-values-ioctl.rst。
首次在 5.5 版本中添加。
返回值
============

成功时返回 0
出错时返回 -1，并且 ``errno`` 变量会被相应地设置
常见的错误代码在 error-codes.rst 中有描述
