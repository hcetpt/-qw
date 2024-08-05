==============================
Linux 内核 VFP 支持代码发布说明
==============================

日期：2005年5月20日

作者：Russell King

这是 Linux 内核 VFP 支持代码的第一个版本。它提供了对 ARM926EJ-S 上的 VFP 硬件引发的异常的支持。
此版本已通过 John R. Hauser 使用 TestFloat-2a 测试套件针对 SoftFloat-2b 库进行了验证。有关该库和测试套件的详细信息可以在以下位置找到：

   http://www.jhauser.us/arithmetic/SoftFloat.html

使用此包测试的操作包括：

- fdiv
- fsub
- fadd
- fmul
- fcmp
- fcmpe
- fcvtd
- fcvts
- fsito
- ftosi
- fsqrt

以上所有操作都通过了软浮点测试，除了以下情况：

- fadd/fsub 在处理正零和负零结果时，在输入操作数符号不同的情况下会有一些差异
- 处理下溢出异常的方式略有不同。如果一个结果在舍入前下溢出，但在舍入后变为规范化数字，则我们不会触发下溢出异常
其他通过基本汇编语言测试进行测试的操作包括：

- fcpy
- fabs
- fneg
- ftoui
- ftosiz
- ftouiz

组合操作尚未经过测试：

- fmac
- fnmac
- fmsc
- fnmsc
- fnmul
