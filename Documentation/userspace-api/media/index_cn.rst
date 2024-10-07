``SPDX-License-Identifier: GPL-2.0``

``include:: <isonum.txt>``

########################################
Linux 媒体基础设施用户空间 API
########################################

本节包含媒体设备使用的驱动程序开发信息和内核 API。
请参阅：

Documentation/admin-guide/media/index.rst

  - 了解媒体子系统及其支持的驱动程序的使用信息；

Documentation/driver-api/media/index.rst

  - 了解驱动程序开发信息及媒体设备使用的内核 API；

.. toctree::
    :caption: 目录
    :maxdepth: 1

    intro
    v4l/v4l2
    dvb/dvbapi
    rc/remote_controllers
    mediactl/media-controller
    cec/cec-api
    gen-errors

    glossary

    fdl-appendix

    drivers/index

**版权** |copy| 2009-2020 : LinuxTV 开发者

```
许可在 GNU 自由文档许可证（版本 1.1 或自由软件基金会发布的任何后续版本）下复制、分发和/或修改此文档，且没有不变章节。许可的具体内容见“GNU 自由文档许可证”一章。
请注意，媒体用户空间 API 中的一些文档，在其源代码中明确说明时，同时采用 GNU 自由文档许可证（版本 1.1）和 GNU 通用公共许可证进行双重授权。

此文档是自由软件；您可以根据自由软件基金会发布的 GNU 通用公共许可证重新发布和/或修改它；您可以选择使用该许可证的第 2 版，或者（根据您的选择）任何更新的版本。
本程序以希望它有用的方式分发，但没有任何保证；甚至没有对适销性或适合某一特定目的的隐含保证。详情请参阅 GNU 通用公共许可证。
更多详细信息，请参阅 Linux 源码分发中的 COPYING 文件。
```
