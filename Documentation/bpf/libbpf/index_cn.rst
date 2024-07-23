SPDX 许可证标识符：(LGPL-2.1 或 BSD-2-Clause)

.. _libbpf:

======
libbpf
======

如果您打算使用 libbpf 库开发 BPF（Berkeley Packet Filter）应用，此目录包含您应该阅读的重要文档。
要开始，请推荐从 :doc:`libbpf 概览 <libbpf_overview>` 文档着手，它提供了对 libbpf API 及其用法的高层次理解。这将为您奠定坚实的基础，以便开始探索和利用 libbpf 的各种功能来开发您的 BPF 应用。

.. toctree::
   :maxdepth: 1

   libbpf_overview
   API 文档 <https://libbpf.readthedocs.io/en/latest/api.html>
   程序类型
   libbpf 命名约定
   libbpf 构建

所有关于通用 BPF 的问题，包括内核功能、libbpf API 及其应用，都应该发送到 bpf@vger.kernel.org 邮件列表。您可以`订阅 <http://vger.kernel.org/vger-lists.html#bpf>`_邮件列表或搜索其`存档 <https://lore.kernel.org/bpf/>`_。在提出新问题前，请先搜索存档。可能之前已经讨论过或回答过同样的问题。
