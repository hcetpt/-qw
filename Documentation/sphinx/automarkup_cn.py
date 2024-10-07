```python
# SPDX 许可声明标识符: GPL-2.0
# 版权所有 2019 Jonathan Corbet <corbet@lwn.net>
#
# 在初始文档处理完成后应用内核特定的调整
#
from docutils import nodes
import sphinx
from sphinx import addnodes
from sphinx.errors import NoUri
import re
from itertools import chain

#
# Python 2 缺乏 re.ASCII..
#
try:
    ascii_p3 = re.ASCII
except AttributeError:
    ascii_p3 = 0

#
# 正则表达式的复杂性。当然
# 尝试识别未被其他方式标记的 "function()"。Sphinx 不喜欢在 :c:func: 块后紧跟很多内容（例如 ":c:func:`mmap()`s" 会出问题），因此最后一部分试图限制不会产生问题的匹配
#
RE_function = re.compile(r'\b(([a-zA-Z_]\w+)\(\))', flags=ascii_p3)

#
# Sphinx 2 使用相同的 :c:type 角色表示 struct、union、enum 和 typedef
#
RE_generic_type = re.compile(r'\b(struct|union|enum|typedef)\s+([a-zA-Z_]\w+)',
                             flags=ascii_p3)

#
# Sphinx 3 对每个 struct、union、enum 和 typedef 使用不同的 C 角色
#
RE_struct = re.compile(r'\b(struct)\s+([a-zA-Z_]\w+)', flags=ascii_p3)
RE_union = re.compile(r'\b(union)\s+([a-zA-Z_]\w+)', flags=ascii_p3)
RE_enum = re.compile(r'\b(enum)\s+([a-zA-Z_]\w+)', flags=ascii_p3)
RE_typedef = re.compile(r'\b(typedef)\s+([a-zA-Z_]\w+)', flags=ascii_p3)

#
# 检测以 Documentation/... 形式引用文档页面，带有可选扩展名
#
RE_doc = re.compile(r'(\bDocumentation/)?((\.\./)*[\w\-/]+)\.(rst|txt)')

RE_namespace = re.compile(r'^\s*..\s*c:namespace::\s*(\S+)\s*$')

#
# 跨引用时应跳过的保留 C 词
#
Skipnames = ['for', 'if', 'register', 'sizeof', 'struct', 'unsigned']

#
# 文档中许多地方都提到了常见的系统调用。尝试跨引用它们是毫无意义的，并且如果有人使用这些名称定义函数，则可能会导致错误和混淆的跨引用。所以对于这些名称就不要尝试跨引用了
#
Skipfuncs = ['open', 'close', 'read', 'write', 'fcntl', 'mmap',
             'select', 'poll', 'fork', 'execve', 'clone', 'ioctl',
             'socket']

c_namespace = ''

#
# 检测对提交的引用
#
RE_git = re.compile(r'commit\s+(?P<rev>[0-9a-f]{12,40})(?:\s+\(".*?"\))?',
                    flags=re.IGNORECASE | re.DOTALL)

def markup_refs(docname, app, node):
    t = node.astext()
    done = 0
    repl = []
    #
    # 将每个正则表达式与将标记其匹配项的函数关联起来
    #
    markup_func_sphinx2 = {
        RE_doc: markup_doc_ref,
        RE_function: markup_c_ref,
        RE_generic_type: markup_c_ref
    }

    markup_func_sphinx3 = {
        RE_doc: markup_doc_ref,
        RE_function: markup_func_ref_sphinx3,
        RE_struct: markup_c_ref,
        RE_union: markup_c_ref,
        RE_enum: markup_c_ref,
        RE_typedef: markup_c_ref,
        RE_git: markup_git
    }

    if sphinx.version_info[0] >= 3:
        markup_func = markup_func_sphinx3
    else:
        markup_func = markup_func_sphinx2

    match_iterators = [regex.finditer(t) for regex in markup_func]
    #
    # 按文本中的起始位置对所有引用进行排序
    #
    sorted_matches = sorted(chain(*match_iterators), key=lambda m: m.start())
    for m in sorted_matches:
        #
        # 包含任何匹配之前的文本作为普通文本节点
        #
        if m.start() > done:
            repl.append(nodes.Text(t[done:m.start()]))

        #
        # 调用与匹配此文本的正则表达式相关的函数，并将其返回值附加到文本中
        #
        repl.append(markup_func[m.re](docname, app, m))

        done = m.end()
    if done < len(t):
        repl.append(nodes.Text(t[done:]))
    return repl

#
# 记录失败的跨引用查找，以便我们不必再次执行它们
#
failed_lookups = {}
def failure_seen(target):
    return target in failed_lookups

def note_failure(target):
    failed_lookups[target] = True

#
# 在 Sphinx 3 中，我们可以跨引用到 C 宏和函数，每个都有自己的 C 角色，但它们都匹配相同的正则表达式，所以我们尝试两者
#
def markup_func_ref_sphinx3(docname, app, match):
    cdom = app.env.domains['c']
    #
    # 执行从 C 领域获取跨引用的操作
    #
    base_target = match.group(2)
    target_text = nodes.Text(match.group(0))
    xref = None
    possible_targets = [base_target]
    # 检查此文档是否有命名空间，如果有，则首先尝试在此命名空间内进行跨引用
```

这段代码翻译为中文注释，解释了每个部分的功能和意图。
以下是提供的代码片段的中文翻译：

```python
if c_namespace:
    possible_targets.insert(0, c_namespace + "." + base_target)

if base_target not in Skipnames:
    for target in possible_targets:
        if (target not in Skipfuncs) and not failure_seen(target):
            lit_text = nodes.literal(classes=['xref', 'c', 'c-func'])
            lit_text += target_text
            pxref = addnodes.pending_xref('', refdomain='c',
                                          reftype='function',
                                          reftarget=target,
                                          modname=None,
                                          classname=None)
            # 
            # XXX Latex生成器在此处会抛出NoUri异常，通过忽略它们来解决这个问题
            #
            try:
                xref = cdom.resolve_xref(app.env, docname, app.builder,
                                         'function', target, pxref,
                                         lit_text)
            except NoUri:
                xref = None

            if xref:
                return xref
            note_failure(target)

return target_text

def markup_c_ref(docname, app, match):
    class_str = {  # Sphinx 2 及以上版本
        RE_function: 'c-func',
        RE_generic_type: 'c-type',
        # Sphinx 3+ 版本
        RE_struct: 'c-struct',
        RE_union: 'c-union',
        RE_enum: 'c-enum',
        RE_typedef: 'c-type',
    }
    reftype_str = {  # Sphinx 2 及以上版本
        RE_function: 'function',
        RE_generic_type: 'type',
        # Sphinx 3+ 版本
        RE_struct: 'struct',
        RE_union: 'union',
        RE_enum: 'enum',
        RE_typedef: 'type',
    }

    cdom = app.env.domains['c']
    #
    # 从C域获取交叉引用的过程
    #
    base_target = match.group(2)
    target_text = nodes.Text(match.group(0))
    xref = None
    possible_targets = [base_target]
    # 检查当前文档是否有命名空间，并在有命名空间的情况下首先尝试在其中进行交叉引用
    if c_namespace:
        possible_targets.insert(0, c_namespace + "." + base_target)

    if base_target not in Skipnames:
        for target in possible_targets:
            if not (match.re == RE_function and target in Skipfuncs):
                lit_text = nodes.literal(classes=['xref', 'c', class_str[match.re]])
                lit_text += target_text
                pxref = addnodes.pending_xref('', refdomain='c',
                                              reftype=reftype_str[match.re],
                                              reftarget=target,
                                              modname=None,
                                              classname=None)
                # 
                # XXX Latex生成器在此处会抛出NoUri异常，通过忽略它们来解决这个问题
                #
                try:
                    xref = cdom.resolve_xref(app.env, docname, app.builder,
                                             reftype_str[match.re], target, pxref,
                                             lit_text)
                except NoUri:
                    xref = None

                if xref:
                    return xref

    return target_text

#
# 尝试将形式为Documentation/...的文档引用替换为指向该页面的交叉引用
#
def markup_doc_ref(docname, app, match):
    stddom = app.env.domains['std']
    #
    # 从标准域获取交叉引用的过程
    #
    absolute = match.group(1)
    target = match.group(2)
    if absolute:
        target = "/" + target
    xref = None
    pxref = addnodes.pending_xref('', refdomain='std', reftype='doc',
                                  reftarget=target, modname=None,
                                  classname=None, refexplicit=False)
    # 
    # XXX Latex生成器在此处会抛出NoUri异常，通过忽略它们来解决这个问题
    #
    try:
        xref = stddom.resolve_xref(app.env, docname, app.builder, 'doc',
                                   target, pxref, None)
    except NoUri:
        xref = None
    # 
    # 如果我们得到了交叉引用则返回它；否则返回纯文本
    #
    if xref:
        return xref
    else:
        return nodes.Text(match.group(0))

def get_c_namespace(app, docname):
    source = app.env.doc2path(docname)
    with open(source) as f:
        for line in f:
            match = RE_namespace.search(line)
            if match:
                return match.group(1)
    return ''

def markup_git(docname, app, match):
    # 虽然我们可以假设运行在一个git仓库中，但不能确定，因此只是机械地将其转换为git.kernel.org链接而不验证其有效性。（也许将来可以做些工作，在明确请求时警告这些引用。）
    text = match.group(0)
    rev = match.group('rev')
    return nodes.reference('', nodes.Text(text),
                           refuri=f'https://git.kernel.org/torvalds/c/{rev}')

def auto_markup(app, doctree, name):
    global c_namespace
    c_namespace = get_c_namespace(app, name)
    def text_but_not_a_reference(node):
        # nodes.literal测试捕获“literal text”，其目的是避免对显式标记为cc:func:的函数添加交叉引用
        if not isinstance(node, nodes.Text) or isinstance(node.parent, nodes.literal):
            return False

        child_of_reference = False
        parent = node.parent
        while parent:
            if isinstance(parent, nodes.Referential):
                child_of_reference = True
                break
            parent = parent.parent
        return not child_of_reference

    # 
    # 这个循环最终可以改进。将来我们可能需要一个适当的树遍历，具有更多节点类型的感知能力。但现在这样工作得很好
    #
    for para in doctree.traverse(nodes.paragraph):
        for node in para.traverse(condition=text_but_not_a_reference):
            node.parent.replace(node, markup_refs(name, app, node))

def setup(app):
    app.connect('doctree-resolved', auto_markup)
    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
```

希望这个翻译对你有所帮助！
