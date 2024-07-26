SPDX 许可证标识符: (LGPL-2.1 或 BSD-2-Clause)

.. _libbpf:

======
libbpf
======

如果您打算使用 libbpf 库开发 BPF 应用程序，本目录包含您应该阅读的重要文档。要开始，请建议从 :doc:`libbpf 概览 <libbpf_overview>` 文档开始，该文档提供了对 libbpf API 及其使用方法的高级理解。这将为您奠定坚实的基础，以开始探索和利用 libbpf 的各种功能来开发您的 BPF 应用程序。

.. toctree::
   :maxdepth: 1

   libbpf_overview
   API 文档 <https://libbpf.readthedocs.io/en/latest/api.html>
   程序类型
   libbpf 命名约定
   libbpf 构建

所有一般性的 BPF 问题，包括内核功能、libbpf API 及其应用，都应该发送到 bpf@vger.kernel.org 邮件列表。您可以 `订阅 <http://vger.kernel.org/vger-lists.html#bpf>`_ 此邮件列表或搜索其 `存档 <https://lore.kernel.org/bpf/>`_。在提出新问题之前，请先搜索存档。可能这些问题之前已经被讨论过或回答过了。
