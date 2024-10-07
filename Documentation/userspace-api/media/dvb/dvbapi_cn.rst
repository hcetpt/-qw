```
SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. include:: <isonum.txt>

.. _dvbapi:

##############################
第二部分 - 数字电视 API
##############################

.. note::

   此 API 也称为 Linux **DVB API**
   它最初是为了支持欧洲数字电视标准（DVB）而编写的，后来扩展以支持所有数字电视标准
   为了避免混淆，在本文档中选择将其及相关的硬件称为 **数字电视**
   **DVB** 这个词被保留用于：

     - 数字电视 API 版本
       （例如：DVB API 版本 3 或 DVB API 版本 5）；
     - 数字电视数据类型（枚举、结构体、宏等）；
     - 数字电视设备节点（``/dev/dvb/...``）；
     - 欧洲 DVB 标准
**版本 5.10**

.. toctree::
    :caption: 目录
    :maxdepth: 5
    :numbered:

    intro
    frontend
    demux
    ca
    net
    legacy_dvb_apis
    examples
    headers


**************************
修订和版权声明
**************************

作者:

- J. K. Metzler, Ralph <rjkm@metzlerbros.de>

 - 数字电视 API 文档的原始作者
- O. C. Metzler, Marcus <rjkm@metzlerbros.de>

 - 数字电视 API 文档的原始作者
- Carvalho Chehab, Mauro <mchehab+samsung@kernel.org>

 - 将文档移植到 Docbook XML，添加 DVBv5 API，并修复文档中的空白
**版权所有** |copy| 2002-2003 : Convergence GmbH

**版权所有** |copy| 2009-2017 : Mauro Carvalho Chehab

******************
修订历史
******************

:revision: 2.2.0 / 2017-09-01 (*mcc*)

非遗留 API 之间的大部分空白得到了修复
:revision: 2.1.0 / 2015-05-29 (*mcc*)

改进了 DocBook 格式并进行了清理，以便更标准化地记录系统调用，并提供更多关于当前数字电视 API 的描述
:revision: 2.0.4 / 2011-05-06 (*mcc*)

增加了更多关于 DVBv5 API 的信息，更好地描述了前端 GET/SET 属性 ioctl
```
修订版本：2.0.3 / 2010-07-03 (*mcc*)

添加一些前端功能标志，这些标志在内核中存在，但在规范中缺失。

修订版本：2.0.2 / 2009-10-25 (*mcc*)

记录了 `FE_SET_FRONTEND_TUNE_MODE` 和 `FE_DISHETWORK_SEND_LEGACY_CMD` 的 ioctl。

修订版本：2.0.1 / 2009-09-16 (*mcc*)

添加了最初由 Patrick Boettcher 编写的 ISDB-T 测试。

修订版本：2.0.0 / 2009-09-06 (*mcc*)

从 LaTex 转换为 DocBook XML。内容与原始的 LaTex 版本相同。

修订版本：1.0.0 / 2003-07-24 (*rjkm*)

初始版本，使用 LaTex 编写。
