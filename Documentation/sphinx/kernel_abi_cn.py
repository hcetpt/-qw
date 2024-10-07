```python
# -*- coding: utf-8; mode: python -*-
# coding=utf-8
# SPDX-License-Identifier: GPL-2.0
#
"""
    kernel-abi
    ~~~~~~~~~~

    实现 ``kernel-abi`` reST 指令
:copyright:  版权所有 (C) 2016 Markus Heiser
:copyright:  版权所有 (C) 2016-2020 Mauro Carvalho Chehab
:maintained-by: Mauro Carvalho Chehab <mchehab+huawei@kernel.org>
:license:    GPL 第 2 版，1991 年 6 月发布，详情见 Linux/COPYING
``kernel-abi`` （:py:class:`KernelCmd`）指令调用 scripts/get_abi.pl 脚本来解析内核 ABI 文件
指令参数和选项概览
.. code-block:: rst

        .. kernel-abi:: <ABI 目录位置>
            :debug:

参数 ``<ABI 目录位置>`` 是必需的。它包含要解析的 ABI 文件的位置。
``debug``
      插入一个带有 *原始* reST 的代码块。有时查看生成的 reST 是有帮助的
"""

import codecs
import os
import subprocess
import sys
import re
import kernellog

from docutils import nodes, statemachine
from docutils.statemachine import ViewList
from docutils.parsers.rst import directives, Directive
from docutils.utils.error_reporting import ErrorString
from sphinx.util.docutils import switch_source_input

__version__ = '1.0'

def setup(app):

    app.add_directive("kernel-abi", KernelCmd)
    return dict(
        version=__version__,
        parallel_read_safe=True,
        parallel_write_safe=True
    )

class KernelCmd(Directive):

    """KernelABI（``kernel-abi``）指令"""

    required_arguments = 1
    optional_arguments = 2
    has_content = False
    final_argument_whitespace = True

    option_spec = {
        "debug": directives.flag,
        "rst": directives.unchanged
    }

    def run(self):
        doc = self.state.document
        if not doc.settings.file_insertion_enabled:
            raise self.warning("docutils: 禁用了文件插入")

        srctree = os.path.abspath(os.environ["srctree"])

        args = [
            os.path.join(srctree, 'scripts/get_abi.pl'),
            'rest',
            '--enable-lineno',
            '--dir', os.path.join(srctree, 'Documentation', self.arguments[0]),
        ]

        if 'rst' in self.options:
            args.append('--rst-source')

        lines = subprocess.check_output(args, cwd=os.path.dirname(doc.current_source)).decode('utf-8')
        nodeList = self.nestedParse(lines, self.arguments[0])
        return nodeList

    def nestedParse(self, lines, fname):
        env = self.state.document.settings.env
        content = ViewList()
        node = nodes.section()

        if "debug" in self.options:
            code_block = "\n\n.. code-block:: rst\n    :linenos:\n"
            for l in lines.split("\n"):
                code_block += "\n    " + l
            lines = code_block + "\n\n"

        line_regex = re.compile(r"^\.\. LINENO (\S+)\#([0-9]+)$")
        ln = 0
        n = 0
        f = fname

        for line in lines.split("\n"):
            n = n + 1
            match = line_regex.search(line)
            if match:
                new_f = match.group(1)

                # Sphinx 解析器是懒惰的：如果内容太大，它会在中间停止解析。因此，按输入文件处理
                if new_f != f and content:
                    self.do_parse(content, node)
                    content = ViewList()

                    # 将文件添加到 Sphinx 构建依赖项中
                    env.note_dependency(os.path.abspath(f))

                f = new_f

                # Sphinx 从 0 开始计数行号
                ln = int(match.group(2)) - 1
            else:
                content.append(line, f, ln)

        kernellog.info(self.state.document.settings.env.app, "%s: 解析了 %i 行" % (fname, n))

        if content:
            self.do_parse(content, node)

        return node.children

    def do_parse(self, content, node):
        with switch_source_input(self.state, content):
            self.state.nested_parse(content, 0, node, match_titles=1)
```
