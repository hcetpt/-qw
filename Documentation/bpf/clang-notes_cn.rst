内容:
... contents ::
... sectnum ::

==========================
Clang 实现说明
==========================

本文件提供了有关 Clang/LLVM 对 eBPF 指令集实现的更多详细信息。
版本
========

Clang 定义了“CPU”版本，其中 CPU 版本 3 对应当前的 eBPF ISA。
Clang 可以使用 `-mcpu=v3` 等来选择 eBPF ISA 的版本，例如选择版本 3。
算术指令
=======================

对于 CPU 版本低于 3 的情况，从 Clang v7.0 及更高版本开始，可以使用 `-Xclang -target-feature -Xclang +alu32` 来启用 `BPF_ALU` 支持。在 CPU 版本 3 中，该支持自动包含。
跳转指令
=================

如果使用 `-O0`，Clang 将生成 `BPF_CALL | BPF_X | BPF_JMP` (0x8d) 指令，该指令不被 Linux 内核验证器支持。
原子操作
=================

当启用 `-mcpu=v3` 时，Clang 默认可以生成原子指令。如果为 `-mcpu` 设置了较低的版本，则 Clang 仅能生成不带 `BPF_FETCH` 的 `BPF_ADD` 原子指令。如果你需要在保持较低的 `-mcpu` 版本的同时启用原子特性，可以使用 `-Xclang -target-feature -Xclang +alu32`。
