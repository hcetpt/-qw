GPU RFC 部分
===============

对于复杂的工作，特别是在引入新的用户空间 API（uapi）时，在陷入代码细节之前确定高层设计问题通常是有益的。此部分旨在承载此类文档：

* 每个 RFC 应该是本文件中的一个章节，解释目标和主要的设计考虑。特别是对于 uapi，请确保抄送所有相关的项目邮件列表以及 dri-devel 之外的相关人员。
* 对于 uapi 结构体，在此目录中添加一个文件，并像处理真实的 uapi 头文件那样提取 kerneldoc 文档。
* 一旦代码合并后，将所有文档移至主核心、辅助或驱动部分的适当位置。

.. toctree::

    i915_gem_lmem.rst

.. toctree::

    i915_scheduler.rst

.. toctree::

    i915_small_bar.rst

.. toctree::

    i915_vm_bind.rst
