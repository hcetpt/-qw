.. SPDX-许可证标识符: GPL-2.0

.. _GPIO_V2_LINE_SET_CONFIG_IOCTL:

*******************************
GPIO_V2_LINE_SET_CONFIG_IOCTL
*******************************

名称
====

GPIO_V2_LINE_SET_CONFIG_IOCTL - 更新先前请求的线路配置

概要
====

.. c:macro:: GPIO_V2_LINE_SET_CONFIG_IOCTL

``int ioctl(int req_fd, GPIO_V2_LINE_SET_CONFIG_IOCTL, struct gpio_v2_line_config *config)``

参数
====

``req_fd``
    GPIO 字符设备的文件描述符，由 gpio-v2-get-line-ioctl.rst 中的 :c:type:`request.fd<gpio_v2_line_request>` 返回。
``config``
    应用于所请求线路的新 :c:type:`配置<gpio_v2_line_config>`。

描述
====

在不释放线路或引入潜在毛刺的情况下更新先前请求的线路配置。新配置必须为所有请求的线路指定一个配置。当请求线路时适用的相同 :ref:`gpio-v2-get-line-config-rules` 和 :ref:`gpio-v2-get-line-config-support` 在更新线路配置时也适用，但额外限制是必须设置方向标志以启用重新配置。如果给定线路的配置中没有设置方向标志，则该线路的配置保持不变。此命令的主要用例是在输入和输出之间更改双向线路的方向，但它也可以用于动态控制边沿检测，或者更广泛地说，无缝地将线路从一个配置状态转移到另一个配置状态。若仅需更改输出线路的值，请使用 gpio-v2-line-set-values-ioctl.rst。

返回值
====

成功时返回 0。
在出现错误 -1 时，`errno` 变量会被相应地设置
常见的错误代码在 error-codes.rst 中有描述
