==================
IMA 模板管理机制
==================

简介
============

原始的 ``ima`` 模板具有固定长度，包含文件数据哈希值和路径名。文件数据哈希值被限制为20字节（md5/sha1）。路径名是一个以空字符终止的字符串，被限制为255个字符。为了克服这些限制并添加额外的文件元数据，有必要通过定义额外的模板来扩展当前版本的 IMA。例如，可以报告的信息包括inode的UID/GID或inode及访问它的进程的LSM标签。
然而，引入这一功能的主要问题是：每当定义一个新的模板时，生成和显示测量列表的函数将包含处理新格式的代码，并且随着时间的推移会显著增长。
提出的解决方案通过将模板管理与其余的 IMA 代码分离来解决这个问题。这个解决方案的核心是定义两种新的数据结构：一个模板描述符，用于确定测量列表中应包含哪些信息；一个模板字段，用于生成和显示特定类型的数据。
使用这些结构来管理模板非常简单。为了支持一种新的数据类型，开发人员需要定义字段标识符并实现两个函数，init() 和 show()，分别用于生成和显示测量条目。定义一个新的模板描述符需要通过 ``ima_template_fmt`` 内核命令行参数指定模板格式（由字段标识符组成的、用 ``|`` 字符分隔的字符串）。在启动时，IMA 通过将格式转换为来自支持的模板字段结构集的数组来初始化所选的模板描述符。
初始化步骤之后，IMA 将调用 ``ima_alloc_init_template()``（新模板管理机制补丁中定义的新函数），使用内核配置或新引入的 ``ima_template`` 和 ``ima_template_fmt`` 内核命令行参数选择的模板描述符来生成一个新的测量条目。
正是在这个阶段，新架构的优势变得明显：该函数不会包含处理特定模板的具体代码，而是简单地调用与所选模板描述符关联的模板字段的 ``init()`` 方法，并将结果（指向分配的数据的指针和数据长度）存储在测量条目结构中。
同样的机制用于显示测量条目。函数 ``ima[_ascii]_measurements_show()`` 对于每个条目，检索用于生成该条目的模板描述符，并对模板字段结构数组中的每一项调用 show() 方法。
支持的模板字段和描述符
=====================

以下是支持的模板字段列表 `('<标识符>': 描述)`，可用于通过向格式字符串中添加其标识符来定义新的模板描述符（稍后将支持更多数据类型）：

 - 'd': 事件的摘要（即已测量文件的摘要），使用 SHA1 或 MD5 哈希算法计算；
 - 'n': 事件的名称（即文件名），长度最多为 255 字节；
 - 'd-ng': 使用任意哈希算法计算的事件摘要（字段格式：<哈希算法>:摘要）；
 - 'd-ngv2': 与 'd-ng' 相同，但以 "ima" 或 "verity" 摘要类型作为前缀（字段格式：<摘要类型>:<哈希算法>:摘要）；
 - 'd-modsig': 不附加 modsig 的事件摘要；
 - 'n-ng': 无大小限制的事件名称；
 - 'sig': 文件签名，基于文件或 fsverity 的摘要 [1]，或如果 'security.ima' 包含文件哈希，则基于 EVM 可移植签名；
 - 'modsig': 附加的文件签名；
 - 'buf': 用于生成哈希值的缓冲区数据，无大小限制；
 - 'evmsig': EVM 可移植签名；
 - 'iuid': 索引节点的 UID；
 - 'igid': 索引节点的 GID；
 - 'imode': 索引节点的模式；
 - 'xattrnames': 如果存在扩展属性，则为扩展属性名称列表（用 ``|`` 分隔）；
 - 'xattrlengths': 如果存在扩展属性，则为扩展属性长度列表（u32）；
 - 'xattrvalues': 扩展属性值列表；


下面是定义的模板描述符列表：

 - "ima": 其格式为 ``d|n``；
 - "ima-ng"（默认）: 其格式为 ``d-ng|n-ng``；
 - "ima-ngv2": 其格式为 ``d-ngv2|n-ng``；
 - "ima-sig": 其格式为 ``d-ng|n-ng|sig``；
 - "ima-sigv2": 其格式为 ``d-ngv2|n-ng|sig``；
 - "ima-buf": 其格式为 ``d-ng|n-ng|buf``；
 - "ima-modsig": 其格式为 ``d-ng|n-ng|sig|d-modsig|modsig``；
 - "evm-sig": 其格式为 ``d-ng|n-ng|evmsig|xattrnames|xattrlengths|xattrvalues|iuid|igid|imode``；


使用
====

为了指定用于生成度量条目的模板描述符，目前支持以下方法：

 - 从内核配置中支持的模板描述符中选择一个（`ima-ng` 是默认选择）；
 - 通过内核命令行参数 `ima_template=` 指定模板描述符名称；
 - 通过内核命令行参数 `ima_template_fmt=` 注册具有自定义格式的新模板描述符。
