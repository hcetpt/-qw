```python
# -*- coding: utf-8; mode: python -*-
# pylint: disable=W0141,C0113,C0103,C0325
u"""
    cdomain
    ~~~~~~~

    替换 Sphinx 的 c-domain
:copyright:  Copyright (C) 2016  Markus Heiser
    :license:    GPL Version 2, June 1991 参见 Linux/COPYING 以获取详细信息
自定义列表：

    * 将函数声明的 *重复 C 对象描述* 警告移到 nitpicky 模式中。参见 Sphinx 文档中的配置值 `nitpick` 和 `nitpick_ignore`
* 在 "c:function:" 指令中添加选项 'name'。使用选项 'name' 可以修改函数的引用名称。例如：::

          .. c:function:: int ioctl( int fd, int request )
             :name: VIDIOC_LOG_STATUS

      函数名称（如 ioctl）仍然出现在输出中，但引用名称从 'ioctl' 更改为 'VIDIOC_LOG_STATUS'。通过以下方式引用该函数：::

          * :c:func:`VIDIOC_LOG_STATUS` 或
          * :any:`VIDIOC_LOG_STATUS`（``:any:`` 需要 Sphinx 1.3）

    * 妥善处理函数宏的签名。不要尝试推断函数宏的参数类型
"""

from docutils import nodes
from docutils.parsers.rst import directives

import sphinx
from sphinx import addnodes
from sphinx.domains.c import c_funcptr_sig_re, c_sig_re
from sphinx.domains.c import CObject as Base_CObject
from sphinx.domains.c import CDomain as Base_CDomain
from itertools import chain
import re

__version__  = '1.1'

# 获取 Sphinx 版本
major, minor, patch = sphinx.version_info[:3]

# 用于拼接到完整名称前的命名空间
namespace = None

#
# 处理 Sphinx 3.1 c domain 标签中的简单新标签
# - 如果找到 ".. c:namespace::" 标签，则存储命名空间
#
RE_namespace = re.compile(r'^\s*..\s*c:namespace::\s*(\S+)\s*$')

def markup_namespace(match):
    global namespace

    namespace = match.group(1)

    return ""

#
# 处理 c:macro 用于函数风格的声明
#
RE_macro = re.compile(r'^\s*..\s*c:macro::\s*(\S+)\s+(\S.*)\s*$')
def markup_macro(match):
    return ".. c:function:: " + match.group(1) + ' ' + match.group(2)

#
# 处理新的 c domain 标签，以便与 Sphinx < 3.0 兼容
#
RE_ctype = re.compile(r'^\s*..\s*c:(struct|union|enum|enumerator|alias)::\s*(.*)$')

def markup_ctype(match):
    return ".. c:type:: " + match.group(2)

#
# 处理新的 c domain 标签，以便与 Sphinx < 3.0 兼容
#
RE_ctype_refs = re.compile(r':c:(var|struct|union|enum|enumerator)::`([^\`]+)`')
def markup_ctype_refs(match):
    return ":c:type:`" + match.group(2) + '`'

#
# 简单地将 :c:expr: 和 :c:texpr: 转换为文字块
#
RE_expr = re.compile(r':c:(expr|texpr):`([^\`]+)`')
def markup_c_expr(match):
    return '\\ ``' + match.group(2) + '``\\ '

#
# 解析 Sphinx 3.x C 标记，并用向后兼容的方式替换它们
#
def c_markups(app, docname, source):
    result = ""
    markup_func = {
        RE_namespace: markup_namespace,
        RE_expr: markup_c_expr,
        RE_macro: markup_macro,
        RE_ctype: markup_ctype,
        RE_ctype_refs: markup_ctype_refs,
    }

    lines = iter(source[0].splitlines(True))
    for n in lines:
        match_iterators = [regex.finditer(n) for regex in markup_func]
        matches = sorted(chain(*match_iterators), key=lambda m: m.start())
        for m in matches:
            n = n[:m.start()] + markup_func[m.re](m) + n[m.end():]

        result = result + n

    source[0] = result

#
# 实现对 cdomain 命名空间逻辑的支持
#

def setup(app):

    # 处理简单的 Sphinx 3.1+ 新标签：:c:expr 和 .. c:namespace::
    app.connect('source-read', c_markups)
    app.add_domain(CDomain, override=True)

    return dict(
        version = __version__,
        parallel_read_safe = True,
        parallel_write_safe = True
    )

class CObject(Base_CObject):

    """
    描述一个 C 语言对象
"""
    option_spec = {
        "name" : directives.unchanged
    }

    def handle_func_like_macro(self, sig, signode):
        u"""处理函数宏的签名
如果 objtype 是 'function' 并且签名 ``sig`` 是一个
        函数宏，则返回宏的名称。否则返回 ``False``。"""

        global namespace

        if not self.objtype == 'function':
            return False

        m = c_funcptr_sig_re.match(sig)
        if m is None:
            m = c_sig_re.match(sig)
            if m is None:
                raise ValueError('no match')

        rettype, fullname, arglist, _const = m.groups()
        arglist = arglist.strip()
        if rettype or not arglist:
            return False

        arglist = arglist.replace('`', '').replace('\\ ', '') # 移除标记
        arglist = [a.strip() for a in arglist.split(",")]

        # 第一个参数是否有类型？
        if len(arglist[0].split(" ")) > 1:
            return False

        # 这是一个函数宏，其参数没有类型！
        signode  += addnodes.desc_name(fullname, fullname)
        paramlist = addnodes.desc_parameterlist()
        signode  += paramlist

        for argname in arglist:
            param = addnodes.desc_parameter('', '', noemph=True)
            # 在输出中用不换行空格分隔
            param += nodes.emphasis(argname, argname)
            paramlist += param

        if namespace:
            fullname = namespace + "." + fullname

        return fullname

    def handle_signature(self, sig, signode):
        """将 C 签名转换为 RST 节点。"""

        global namespace

        fullname = self.handle_func_like_macro(sig, signode)
        if not fullname:
            fullname = super(CObject, self).handle_signature(sig, signode)

        if "name" in self.options:
            if self.objtype == 'function':
                fullname = self.options["name"]
            else:
                # FIXME: 处理其他声明类型的 :name: 值？
                pass
        else:
            if namespace:
                fullname = namespace + "." + fullname

        return fullname

    def add_target_and_index(self, name, sig, signode):
        # 对于 C API 项，我们添加一个前缀，因为名称通常不会由模块名称限定，
        # 因此容易与节标题等发生冲突
        targetname = 'c.' + name
        if targetname not in self.state.document.ids:
            signode['names'].append(targetname)
            signode['ids'].append(targetname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)
            inv = self.env.domaindata['c']['objects']
            if (name in inv and self.env.config.nitpicky):
                if self.objtype == 'function':
                    if ('c:func', name) not in self.env.config.nitpick_ignore:
                        self.state_machine.reporter.warning(
                            '重复 C 对象描述 %s，' % name +
                            '另一个实例在 ' + self.env.doc2path(inv[name][0]),
                            line=self.lineno)
            inv[name] = (self.env.docname, self.objtype)

        indextext = self.get_index_text(name)
        if indextext:
            self.indexnode['entries'].append(
                    ('single', indextext, targetname, '', None))

class CDomain(Base_CDomain):

    """C 语言域。"""
    name = 'c'
    label = 'C'
    directives = {
        'function': CObject,
        'member':   CObject,
        'macro':    CObject,
        'type':     CObject,
        'var':      CObject,
    }
```
