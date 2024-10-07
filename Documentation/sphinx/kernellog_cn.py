# SPDX 许可证标识符: GPL-2.0
#
# Sphinx 已弃用了其旧的日志记录接口，但替代接口仅回溯到 1.6 版本。因此，在我们支持 1.4 版本期间，这里提供了一个包装层以保持兼容。
#
# 我们不再支持 1.4 版本，但我们会保留这些包装函数，直到我们将所有代码修改为不再使用它们为止 :)
#
import sphinx
from sphinx.util import logging

logger = logging.getLogger('kerneldoc')

def warn(app, message):
    logger.warning(message)

def verbose(app, message):
    logger.verbose(message)

def info(app, message):
    logger.info(message)
