```python
# -*- coding: utf-8; mode: python -*-
# pylint: disable=R0903, C0330, R0914, R0912, E0401

import os
import sys
from sphinx.util.osutil import fs_encoding

# ------------------------------------------------------------------------------
def loadConfig(namespace):
# ------------------------------------------------------------------------------

    u"""将一个额外的配置文件加载到 *namespace* 中。
配置文件的名字从环境变量 ``SPHINX_CONF`` 获取。外部配置文件扩展（或覆盖）了原始 ``conf.py`` 中的配置值。通过这种方式，您可以维护 *构建主题*。"""

    config_file = os.environ.get("SPHINX_CONF", None)
    if (config_file is not None
        and os.path.normpath(namespace["__file__"]) != os.path.normpath(config_file)):
        config_file = os.path.abspath(config_file)

        # 避免仅因 latex_documents 而生成一个 conf.py 文件
        start = config_file.find('Documentation/')
        if start >= 0:
            start = config_file.find('/', start + 1)

        end = config_file.rfind('/')
        if start >= 0 and end > 0:
            dir = config_file[start + 1:end]

            print("源目录: %s" % dir)
            new_latex_docs = []
            latex_documents = namespace['latex_documents']

            for l in latex_documents:
                if l[0].find(dir + '/') == 0:
                    has = True
                    fn = l[0][len(dir) + 1:]
                    new_latex_docs.append((fn, l[1], l[2], l[3], l[4]))
                    break

            namespace['latex_documents'] = new_latex_docs

        # 如果有额外的 conf.py 文件，加载它
        if os.path.isfile(config_file):
            sys.stdout.write("加载额外的 Sphinx 配置: %s\n" % config_file)
            config = namespace.copy()
            config['__file__'] = config_file
            with open(config_file, 'rb') as f:
                code = compile(f.read(), fs_encoding, 'exec')
                exec(code, config)
            del config['__file__']
            namespace.update(config)
        else:
            config = namespace.copy()
            config['tags'].add("subproject")
            namespace.update(config)
```
