==========================
CPU 到 ISA 版本映射
==========================

一些 CPU 版本到相关 ISA 版本的映射  
注意：Power4 和 Power4+ 不受支持
========= ====================================================================
CPU       架构版本
========= ====================================================================
Power10   Power ISA v3.1
Power9    Power ISA v3.0B
Power8    Power ISA v2.07
e6500     Power ISA v2.06（带有一些例外）
e5500     Power ISA v2.06（带有一些例外，不支持 Altivec）
Power7    Power ISA v2.06
Power6    Power ISA v2.05
PA6T      Power ISA v2.04
Cell PPU  - Power ISA v2.02（带有一些较小的例外）
          - 加上 Altivec/VMX 约等于 2.03
Power5++  Power ISA v2.04（无 VMX）
Power5+   Power ISA v2.03
Power5    - PowerPC 用户指令集架构手册 I v2.02
          - PowerPC 虚拟环境架构手册 II v2.02
          - PowerPC 运行环境架构手册 III v2.02
PPC970    - PowerPC 用户指令集架构手册 I v2.01
          - PowerPC 虚拟环境架构手册 II v2.01
          - PowerPC 运行环境架构手册 III v2.01
          - 加上 Altivec/VMX 约等于 2.03
Power4+   - PowerPC 用户指令集架构手册 I v2.01
          - PowerPC 虚拟环境架构手册 II v2.01
          - PowerPC 运行环境架构手册 III v2.01
Power4    - PowerPC 用户指令集架构手册 I v2.00
          - PowerPC 虚拟环境架构手册 II v2.00
          - PowerPC 运行环境架构手册 III v2.00
========= ====================================================================


关键特性
------------

========== ==================
CPU        VMX （即 Altivec）
========== ==================
Power10    支持
Power9     支持
Power8     支持
e6500      支持
e5500      不支持
Power7     支持
Power6     支持
PA6T       支持
Cell PPU   支持
Power5++   不支持
Power5+    不支持
Power5     不支持
PPC970     支持
Power4+    不支持
Power4     不支持
========== ==================

========== ====
CPU        VSX
========== ====
Power10    支持
Power9     支持
Power8     支持
e6500      不支持
e5500      不支持
Power7     支持
Power6     不支持
PA6T       不支持
Cell PPU   不支持
Power5++   不支持
Power5+    不支持
Power5     不支持
PPC970     不支持
Power4+    不支持
Power4     不支持
========== ====

========== ====================================
CPU        事务内存
========== ====================================
Power10    不支持 (* 参见 Power ISA v3.1，“附录 A. 从架构中移除事务内存的说明”)
Power9     支持 (* 参见 transactional_memory.txt)
Power8     支持
e6500      不支持
e5500      不支持
Power7     不支持
Power6     不支持
PA6T       不支持
Cell PPU   不支持
Power5++   不支持
Power5+    不支持
Power5     不支持
PPC970     不支持
Power4+    不支持
Power4     不支持
========== ====================================
