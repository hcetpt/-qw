### RISC-V Linux 的向量扩展支持

本文档简要概述了Linux为用户空间提供的接口，以支持RISC-V向量扩展的使用。

#### 1. `prctl()` 接口

新增加了两个 `prctl()` 调用来允许程序管理用户空间中向量使用的启用状态。这些接口的设计目的是给初始化系统一种方式来修改在其领域下运行的进程对V的可用性。不建议在库例程中调用这些接口，因为库不应该覆盖父进程中配置的策略。此外，用户需要注意这些接口不适用于非Linux或非RISC-V环境，因此不鼓励在可移植代码中使用它们。要获取ELF程序中的V的可用性，请阅读辅助向量中的宏 `ELF_HWCAP` 的 `COMPAT_HWCAP_ISA_V` 位。

* `prctl(PR_RISCV_V_SET_CONTROL, unsigned long arg)`

    设置调用线程的向量启用状态，其中控制参数由两个2位的启用状态和一个继承模式位组成。调用进程的其他线程不受影响。
    启用状态是一个三态值，每个占用控制参数中的2位空间：
    
    * `PR_RISCV_V_VSTATE_CTRL_DEFAULT`：在 `execve()` 时使用系统范围内的默认启用状态。可以通过sysctl接口（参见下面的sysctl部分）控制系统范围内的默认设置。
    * `PR_RISCV_V_VSTATE_CTRL_ON`：允许线程运行向量。
    * `PR_RISCV_V_VSTATE_CTRL_OFF`：禁止向量。在这种情况下执行向量指令将导致陷阱并终止该线程。
    参数 `arg` 是一个5位值，由3个部分组成，通过3个掩码分别访问：
    这3个掩码 `PR_RISCV_V_VSTATE_CTRL_CUR_MASK`、`PR_RISCV_V_VSTATE_CTRL_NEXT_MASK` 和 `PR_RISCV_V_VSTATE_CTRL_INHERIT` 分别代表位[1:0]、位[3:2]和位[4]。位[1:0]表示当前线程的启用状态，而位[3:2]表示下一个 `execve()` 时的设置。位[4]定义位[3:2]设置的继承模式。
    
    * `PR_RISCV_V_VSTATE_CTRL_CUR_MASK`：位[1:0]：表示调用线程的向量启用状态。一旦启用了向量，调用线程就不能再禁用它。如果此掩码中的值为 `PR_RISCV_V_VSTATE_CTRL_OFF` 但当前启用状态不是关闭状态，则 `prctl()` 调用将以EPERM失败。在此处设置 `PR_RISCV_V_VSTATE_CTRL_DEFAULT` 不会产生效果，只会恢复原始启用状态。
    * `PR_RISCV_V_VSTATE_CTRL_NEXT_MASK`：位[3:2]：表示调用线程在下一个 `execve()` 系统调用时的向量启用设置。如果在此掩码中使用 `PR_RISCV_V_VSTATE_CTRL_DEFAULT`，则当 `execve()` 发生时，启用状态将由系统范围内的启用状态决定。
*:c:macro:`PR_RISCV_V_VSTATE_CTRL_INHERIT`: 位[4]：为PR_RISCV_V_VSTATE_CTRL_NEXT_MASK中的设置指定的继承模式。如果该位被设置，则接下来的execve()调用将不会清除PR_RISCV_V_VSTATE_CTRL_NEXT_MASK和PR_RISCV_V_VSTATE_CTRL_INHERIT中的设置。

此设置在系统默认值发生变化时仍然保持有效。
返回值：
        * 成功时返回0；
        * EINVAL: 向量不受支持，当前或下一个掩码的有效状态无效；
        * EPERM: 如果调用线程已启用向量，则在PR_RISCV_V_VSTATE_CTRL_CUR_MASK中关闭向量；
成功时：
        * 对PR_RISCV_V_VSTATE_CTRL_CUR_MASK的有效设置会立即生效。PR_RISCV_V_VSTATE_CTRL_NEXT_MASK中指定的有效状态会在下一个execve()调用时生效，或者如果PR_RISCV_V_VSTATE_CTRL_INHERIT位被设置，则在所有后续的execve()调用中生效。
* 每次成功的调用都会覆盖调用线程之前的设置
* prctl(PR_RISCV_V_GET_CONTROL)

    获取调用线程相同的向量启用状态。下一次execve()调用的设置和继承位全部进行逻辑或运算
需要注意的是，ELF程序可以通过读取辅助向量中:c:macro:`ELF_HWCAP`的:c:macro:`COMPAT_HWCAP_ISA_V`位来获取自身是否支持V。
返回值：
        * 成功时返回非负值；
        * EINVAL: 向量不受支持
2. 系统运行时配置（sysctl）
-----------------------------------------

为了减轻信号栈扩展对ABI的影响，提供了一种策略机制供管理员、发行版维护者和开发者控制用户空间进程的默认向量启用状态，形式为sysctl旋钮：

* /proc/sys/abi/riscv_v_default_allow

    将0或1的文本表示写入此文件可设置新启动的用户空间程序的系统默认启用状态。有效值为：

    * 0: 默认情况下不允许执行向量代码的新进程
* 1: 默认情况下允许执行向量代码的新进程
阅读此文件会返回当前系统的默认启用状态。
在每次执行execve()调用时，新进程的启用状态将被设置为系统默认值，除非：

      * 对于调用进程设置了PR_RISCV_V_VSTATE_CTRL_INHERIT，并且PR_RISCV_V_VSTATE_CTRL_NEXT_MASK中的设置不是
        PR_RISCV_V_VSTATE_CTRL_DEFAULT。或者，

      * PR_RISCV_V_VSTATE_CTRL_NEXT_MASK中的设置不是
        PR_RISCV_V_VSTATE_CTRL_DEFAULT
修改系统默认的启用状态不会影响任何未进行execve()调用的现有进程或线程的启用状态。
3. 系统调用间的向量寄存器状态
---------------------------------------------

根据V扩展版本1.0的指示[1]，向量寄存器会被系统调用破坏。
1: https://github.com/riscv/riscv-v-spec/blob/master/calling-convention.adoc
