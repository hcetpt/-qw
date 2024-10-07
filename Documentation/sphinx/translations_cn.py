```python
# SPDX-License-Identifier: GPL-2.0
#
# 版权所有 © 2023，Oracle 及其关联公司
# 作者：Vegard Nossum <vegard.nossum@oracle.com>
#
# 在文档顶部添加翻译链接
#

import os

from docutils import nodes
from docutils.transforms import Transform

import sphinx
from sphinx import addnodes
from sphinx.errors import NoUri

all_languages = {
    # 英语始终是第一个
    None: '英语',

    # 其余的语言按字母顺序排列
    'zh_CN': '中文（简体）',
    'zh_TW': '中文（繁体）',
    'it_IT': '意大利语',
    'ja_JP': '日语',
    'ko_KR': '韩语',
    'sp_SP': '西班牙语',
}

class LanguagesNode(nodes.Element):
    pass

class TranslationsTransform(Transform):
    default_priority = 900

    def apply(self):
        app = self.document.settings.env.app
        docname = self.document.settings.env.docname

        this_lang_code = None
        components = docname.split(os.sep)
        if components[0] == 'translations' and len(components) > 2:
            this_lang_code = components[1]

            # 将 docname 规范化为未翻译的版本
            docname = os.path.join(*components[2:])

        new_nodes = LanguagesNode()
        new_nodes['current_language'] = all_languages[this_lang_code]

        for lang_code, lang_name in all_languages.items():
            if lang_code == this_lang_code:
                continue

            if lang_code is None:
                target_name = docname
            else:
                target_name = os.path.join('translations', lang_code, docname)

            pxref = addnodes.pending_xref('', refdomain='std',
                reftype='doc', reftarget='/' + target_name, modname=None,
                classname=None, refexplicit=True)
            pxref += nodes.Text(lang_name)
            new_nodes += pxref

        self.document.insert(0, new_nodes)

def process_languages(app, doctree, docname):
    for node in doctree.traverse(LanguagesNode):
        if app.builder.format not in ['html']:
            node.parent.remove(node)
            continue

        languages = []

        # 遍历子节点；任何已解析的链接将具有类型 'nodes.reference'，
        # 而未解析的链接将是类型 'nodes.Text'
        languages = list(filter(lambda xref:
            isinstance(xref, nodes.reference), node.children))

        html_content = app.builder.templates.render('translations.html',
            context={
                'current_language': node['current_language'],
                'languages': languages,
            })

        node.replace_self(nodes.raw('', html_content, format='html'))

def setup(app):
    app.add_node(LanguagesNode)
    app.add_transform(TranslationsTransform)
    app.connect('doctree-resolved', process_languages)

    return {
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
```

以上是代码段的中文翻译。
