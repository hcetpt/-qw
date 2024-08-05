### SPDX 许可证标识符: GPL-2.0

RISC-V 硬件探测接口
--------------------

RISC-V 硬件探测接口主要基于一个系统调用，该调用在 `<asm/hwprobe.h>` 中定义如下：

    struct riscv_hwprobe {
        __s64 key;
        __u64 value;
    };

    long sys_riscv_hwprobe(struct riscv_hwprobe *pairs, size_t pair_count,
                           size_t cpusetsize, cpu_set_t *cpus,
                           unsigned int flags);

参数被分为三组：键值对数组、CPU集合以及一些标志。键值对需要提供数量。用户空间必须预先填充每个元素的 `key` 字段，如果内核识别该键，则会填充 `value` 字段。如果一个键是内核未知的，其 `key` 字段将被清零为 -1，其 `value` 设为 0。CPU 集合由 `CPU_SET(3)` 定义，大小为 `cpusetsize` 字节。对于像值一样的键（例如，供应商、架构、实现），返回的值只有当给定集合中的所有 CPU 都有相同的值时才有效；否则返回 -1。对于布尔类型的键，返回的值将是指定 CPU 的逻辑与。用户空间可以为 `cpus` 提供 NULL 并将 `cpusetsize` 设置为 0，作为所有在线 CPU 的快捷方式。目前支持的标志包括：

* :c:macro:`RISCV_HWPROBE_WHICH_CPUS`: 此标志基本反转了 `sys_riscv_hwprobe()` 的行为。不是为给定的 CPU 集合填充键的值，而是给出每个键的值，并通过 `sys_riscv_hwprobe()` 减少 CPU 集合以仅包含与每个键值对匹配的 CPU。如何进行匹配取决于键类型。对于值类型的键，匹配意味着与值完全相同；对于布尔类型的键，匹配意味着该对的值与 CPU 值进行逻辑与运算的结果正好等于该对的值。此外，当 `cpus` 是空集时，它将初始化为所有可以容纳在其内的在线 CPU，即返回的 CPU 集合是对所有可以表示为大小为 `cpusetsize` 的 CPU 集合的在线 CPU 的缩减。
所有其他标志保留以备将来兼容性使用，必须为零。成功时返回 0，失败时返回负的错误代码。以下定义了一些键：

* :c:macro:`RISCV_HWPROBE_KEY_MVENDORID`: 包含由 RISC-V 特权架构规范定义的 `mvendorid` 的值
* :c:macro:`RISCV_HWPROBE_KEY_MARCHID`: 包含由 RISC-V 特权架构规范定义的 `marchid` 的值
* :c:macro:`RISCV_HWPROBE_KEY_MIMPLID`: 包含由 RISC-V 特权架构规范定义的 `mimplid` 的值
* :c:macro:`RISCV_HWPROBE_KEY_BASE_BEHAVIOR`: 包含此内核支持的基本用户可见行为的位掩码。以下定义了基本用户 ABIs：

  * :c:macro:`RISCV_HWPROBE_BASE_BEHAVIOR_IMA`: 支持 rv32ima 或 rv64ima，根据用户 ISA 2.2 版本和特权 ISA 1.10 版本定义，已知存在以下例外（可能会添加更多例外，但前提是能够证明用户 ABI 没有被破坏）：

    * 用户空间程序不能直接执行 `fence.i` 指令（可以通过内核控制的机制如 vDSO 在用户空间中执行）
* :c:macro:`RISCV_HWPROBE_KEY_IMA_EXT_0`: 包含与 :c:macro:`RISCV_HWPROBE_BASE_BEHAVIOR_IMA` 兼容的扩展的位掩码：基础系统行为
* :c:macro:`RISCV_HWPROBE_IMA_FD`: 支持 F 和 D 扩展，如 RISC-V ISA 手册中提交 cd20cee ("FMIN/FMAX 现在实现 minimumNumber/maximumNumber，而非 minNum/maxNum") 所定义的那样
* :c:macro:`RISCV_HWPROBE_IMA_C`: 支持 C 扩展，如 RISC-V ISA 手册版本 2.2 中所定义的那样
* :c:macro:`RISCV_HWPROBE_IMA_V`: 支持 V 扩展，如 RISC-V 向量扩展手册版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBA`: 支持 Zba 地址生成扩展，如位操作 ISA 扩展版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBB`: 支持 Zbb 扩展，如位操作 ISA 扩展版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBS`: 支持 Zbs 扩展，如位操作 ISA 扩展版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZICBOZ`: 支持 Zicboz 扩展，如 riscv-CMOs 中提交 3dd606f ("创建 cmobase-v1.0.pdf") 所批准的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBC`: 支持 Zbc 扩展，如位操作 ISA 扩展版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBKB`: 支持 Zbkb 扩展，如标量密码 ISA 扩展版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBKC`: 支持 Zbkc 扩展，如标量密码 ISA 扩展版本 1.0 中所定义的那样
* :c:macro:`RISCV_HWPROBE_EXT_ZBKX`：支持 Zbkx 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZKND`：支持 Zknd 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZKNE`：支持 Zkne 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZKNH`：支持 Zknh 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZKSED`：支持 Zksed 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZKSH`：支持 Zksh 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZKT`：支持 Zkt 扩展，如标量密码 ISA 扩展版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZVBB`：支持 Zvbb 扩展，如 RISC-V 密码扩展第二卷版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZVBC`：支持 Zvbc 扩展，如 RISC-V 密码扩展第二卷版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZVKB`：支持 Zvkb 扩展，如 RISC-V 密码扩展第二卷版本 1.0 中所定义。
* :c:macro:`RISCV_HWPROBE_EXT_ZVKG`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvkg 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZVKNED`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvkned 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZVKNHA`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvknha 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZVKNHB`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvknhb 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZVKSED`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvksed 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZVKSH`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvksh 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZVKT`: 根据 RISC-V 加密扩展第二卷版本 1.0 中的定义，支持 Zvkt 扩展
* :c:macro:`RISCV_HWPROBE_EXT_ZFH`: 根据 RISC-V ISA 手册中的定义，支持 Zfh 扩展版本 1.0
* :c:macro:`RISCV_HWPROBE_EXT_ZFHMIN`: 根据 RISC-V ISA 手册中的定义，支持 Zfhmin 扩展版本 1.0
* :c:macro:`RISCV_HWPROBE_EXT_ZIHINTNTL`: 根据 RISC-V ISA 手册中的定义，支持 Zihintntl 扩展版本 1.0
* :c:macro:`RISCV_HWPROBE_EXT_ZVFH`：从提交 e2ccd0548d6c 开始（"移除 Zvfh[min] 的草案警告"），根据 RISC-V 向量手册定义，支持 Zvfh 扩展。
* :c:macro:`RISCV_HWPROBE_EXT_ZVFHMIN`：从提交 e2ccd0548d6c 开始（"移除 Zvfh[min] 的草案警告"），根据 RISC-V 向量手册定义，支持 Zvfhmin 扩展。
* :c:macro:`RISCV_HWPROBE_EXT_ZFA`：从提交 056b6ff467c7 开始（"Zfa 已被采纳"），根据 RISC-V ISA 手册定义，支持 Zfa 扩展。
* :c:macro:`RISCV_HWPROBE_EXT_ZTSO`：从提交 5618fb5a216b 开始（"Ztso 现已被采纳"），根据 RISC-V ISA 手册定义，支持 Ztso 扩展。
* :c:macro:`RISCV_HWPROBE_EXT_ZACAS`：从提交 5059e0ca641c 开始（"更新至已采纳版本"），根据原子比较与交换（CAS）指令手册定义，支持 Zacas 扩展。
* :c:macro:`RISCV_HWPROBE_EXT_ZICOND`：从提交 95cf1f9 开始（"添加 Ved 在签署过程中要求的更改"），根据 RISC-V 整数条件操作扩展（Zicond）手册定义，支持 Zicond 扩展。
* :c:macro:`RISCV_HWPROBE_EXT_ZIHINTPAUSE`：从提交 d8ab5c78c207 开始（"Zihintpause 已被采纳"），根据 RISC-V ISA 手册定义，支持 Zihintpause 扩展。
* :c:macro:`RISCV_HWPROBE_KEY_CPUPERF_0`：一个包含选定处理器组性能信息的位掩码。
* :c:macro:`RISCV_HWPROBE_MISALIGNED_UNKNOWN`：未对齐访问的性能未知。
* :c:macro:`RISCV_HWPROBE_MISALIGNED_EMULATED`：通过软件在内核级别或以下级别模拟未对齐访问。这些访问始终极其缓慢。
* :c:macro:`RISCV_HWPROBE_MISALIGNED_SLOW`：未对齐访问比等效字节访问慢。未对齐访问可能直接由硬件支持，或者被捕获并通过软件模拟。
* :c:macro:`RISCV_HWPROBE_MISALIGNED_FAST`：未对齐访问比等效字节访问快。
* :c:macro:`RISCV_HWPROBE_MISALIGNED_UNSUPPORTED`：完全不支持未对齐的访问，这将生成一个未对齐地址错误
* :c:macro:`RISCV_HWPROBE_KEY_ZICBOZ_BLOCK_SIZE`：一个无符号整数，表示 Zicboz 块的大小（以字节为单位）
