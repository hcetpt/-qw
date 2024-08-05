============================
NUMA资源关联性
============================

关联性表示平台资源在性能上大致相似的域中的各种组合。一个给定域内的资源子集相对于该域内其他资源子集表现出更佳性能时，这些资源子集被视为属于一个子组合域。这种性能特性在Linux内核中以NUMA节点距离的形式来描述。
从平台角度来看，这些组也被称为域。
PAPR接口目前支持不同的方式将这些资源分组详情传达给操作系统。这些被称为形式0、形式1和形式2的关联性分组。形式0是最古老的形式，现在被认为是过时的。
通过"ibm,architecture-vec-5"属性，虚拟机指示所使用的关联性类型/形式。
"ibm,architecture-vec-5"属性的第5字节的第0位表示使用的是形式0还是形式1。
值为1表示使用形式1的关联性。对于形式2的关联性，
"ibm,architecture-vec-5"属性的第5字节的第2位被用来表示。

形式0
------
形式0的关联性只支持两种NUMA距离（本地和远程）。

形式1
------
形式1通过组合使用"ibm,associativity-reference-points"和"ibm,associativity"设备树属性来确定资源组/域之间的NUMA距离。
"ibm,associativity"属性包含一个或多个数字（域ID）列表，代表资源的平台分组域。
"ibm,associativity-reference-points"属性包含一个或多个数字（域ID索引）列表，表示关联性列表中基于1的序号。
域ID索引列表表示资源分组的递增层级结构。
例如：
{ 主域ID索引, 次级域ID索引, 三级域ID索引... }

Linux 内核使用主域ID索引处的域ID作为NUMA节点ID。
Linux 内核通过递归比较两个域是否属于相同的高级别域来计算两个域之间的NUMA距离。对于资源组层级上的每次不匹配，内核都会将比较域之间的NUMA距离翻倍。

形式2
------
形式2关联性格式添加了表示NUMA节点距离的独立设备树属性，从而使节点距离计算变得灵活。形式2还允许主域编号灵活。由于NUMA距离计算不再依赖于“ibm,associativity-reference-points”属性中的索引值，形式2允许在相同的域ID索引处存在大量的主域ID，这些主域代表具有不同性能/延迟特性的资源组。
虚拟机监控程序使用“ibm,architecture-vec-5”属性中字节5的第2位指示使用形式2关联性。
“ibm,numa-lookup-index-table”属性包含一个或多个数字列表，表示系统中存在的域ID。此属性中域ID的偏移量用于计算NUMA距离信息时作为索引。“ibm,numa-distance-table”属性。
属性编码数组：用encode-int编码的域ID数量N，随后是用encode-int编码的N个域ID。

例如：
"ibm,numa-lookup-index-table" = {4, 0, 8, 250, 252}。域ID 8的偏移量（2）用于计算域8与其他系统中存在的域的距离。本文档后续部分将把此偏移量称为域距离偏移。
"ibm,numa-distance-table"属性包含一个或多个数字列表，表示系统中存在的资源组/域之间的NUMA距离。
属性编码数组：用encode-int编码的距离值数量N，随后是用encode-bytes编码的N个距离值。我们可以编码的最大距离值为255。
数量N必须等于m的平方，其中m是numa-lookup-index-table中的域ID数量。
### 示例说明：

```
ibm,numa-lookup-index-table = <3 0 8 40>;
ibm,numa-distance-table = <9>, /bits/ 8 < 10  20  80 20  10 160 80 160  10>;
```

### 表格表示形式：

```
     | 0    8   40
-----|------------
     |
 0   | 10   20  80
     |
 8   | 20   10  160
     |
 40  | 80   160 10
```

### 对于节点 0、8 和 40 中的资源，一个可能的“ibm,associativity”属性为：

- { 3, 6, 7, 0 }
- { 3, 6, 9, 8 }
- { 3, 6, 7, 40}

### 其中，“ibm,associativity-reference-points”为 { 0x3 }。

- “ibm,lookup-index-table”有助于实现距离矩阵的紧凑表示。
- 由于域ID可能是稀疏的，因此距离矩阵也可能有效地是稀疏的。
- 利用“ibm,lookup-index-table”，我们可以实现距离信息的紧凑表示。
