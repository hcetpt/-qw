### 在用户空间应用程序中使用XSTATE特性

x86架构支持通过CPUID枚举的浮点扩展。应用程序通过CPUID咨询并使用XGETBV来评估内核XCR0已启用哪些特性。直到AVX-512和PKRU状态，如果可用，这些特性会由内核自动启用。像AMX TILE_DATA（XSTATE组件18）这样的特性也由XCR0启用，但是相关的指令首次使用时会被内核捕获，因为默认情况下所需的大型XSTATE缓冲区不会自动分配。

#### 动态特性的目的

传统的用户空间库通常为备用信号栈硬编码静态大小，通常使用MINSIGSTKSZ，其通常是2KB。该栈必须能够存储至少内核在跳转到信号处理程序之前设置的信号帧。该信号帧必须包含由CPU定义的XSAVE缓冲区。
然而，这意味着信号栈的大小是动态的，而不是静态的，因为不同的CPU具有不同大小的XSAVE缓冲区。对于现有的应用程序来说，编译时固定的2KB大小对于新的CPU特性如AMX来说太小了。而不是普遍要求更大的栈，通过动态启用特性，内核可以强制用户空间应用程序拥有适当大小的备用栈。

### 在用户空间应用程序中使用动态启用的XSTATE特性

内核提供了一个基于arch_prctl(2)的机制，供应用程序请求使用此类特性。与此相关的arch_prctl(2)选项包括：

- **ARCH_GET_XCOMP_SUPP**

```c
arch_prctl(ARCH_GET_XCOMP_SUPP, &features);
```

`ARCH_GET_XCOMP_SUPP`将支持的特性存储在用户空间类型为uint64_t的存储中。第二个参数是指向该存储的指针。

- **ARCH_GET_XCOMP_PERM**

```c
arch_prctl(ARCH_GET_XCOMP_PERM, &features);
```

`ARCH_GET_XCOMP_PERM`将用户空间进程具有权限的特性存储在用户空间类型为uint64_t的存储中。第二个参数是指向该存储的指针。

- **ARCH_REQ_XCOMP_PERM**

```c
arch_prctl(ARCH_REQ_XCOMP_PERM, feature_nr);
```

`ARCH_REQ_XCOMP_PERM`允许请求动态启用的特性或特性集的权限。一个特性集可以映射到一个功能，例如AMX，并且可能需要启用一个或多个XSTATE组件。
特性参数是某个功能工作所需最高XSTATE组件的编号。
当请求某项功能的权限时，内核会检查该功能是否可用。内核确保进程的任务中的`sigaltstack`足够大以容纳由此产生的大型信号帧。它在`ARCH_REQ_XCOMP_SUPP`期间以及任何后续的`sigaltstack(2)`调用中都会强制执行这一点。如果已安装的`sigaltstack`小于由此产生的`sigframe`大小，则`ARCH_REQ_XCOMP_SUPP`会导致`-ENOSUPP`错误。此外，如果请求的`altstack`对于允许的功能来说太小，则`sigaltstack(2)`会导致`-ENOMEM`错误。
一旦授予的权限对每个进程都是有效的。这些权限会在`fork(2)`时被继承，并在`exec(3)`时被清除。
动态启用功能相关的指令首次使用时会被内核捕获。捕获处理程序会检查进程是否有权使用该功能。如果进程没有权限，内核则向应用程序发送`SIGILL`信号。如果进程有权限，则处理程序为任务分配更大的xstate缓冲区以便于上下文切换。在不太可能发生的情况下，如果分配失败，内核会发送`SIGSEGV`信号。

### AMX TILE_DATA 启用示例
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

下面是用户空间应用程序如何动态启用TILE_DATA的一个例子：

  1. 应用程序首先需要查询内核以确认是否支持AMX：

        ```c
        #include <asm/prctl.h>
        #include <sys/syscall.h>
        #include <stdio.h>
        #include <unistd.h>

        #ifndef ARCH_GET_XCOMP_SUPP
        #define ARCH_GET_XCOMP_SUPP  0x1021
        #endif

        #ifndef ARCH_XCOMP_TILECFG
        #define ARCH_XCOMP_TILECFG   17
        #endif

        #ifndef ARCH_XCOMP_TILEDATA
        #define ARCH_XCOMP_TILEDATA  18
        #endif

        #define MASK_XCOMP_TILE      ((1 << ARCH_XCOMP_TILECFG) | \
                                      (1 << ARCH_XCOMP_TILEDATA))

        unsigned long features;
        long rc;

        ...
        rc = syscall(SYS_arch_prctl, ARCH_GET_XCOMP_SUPP, &features);

        if (!rc && (features & MASK_XCOMP_TILE) == MASK_XCOMP_TILE)
            printf("AMX is available.\n");
        ```

  2. 确定支持AMX后，应用程序必须明确请求使用权限：

        ```c
        #ifndef ARCH_REQ_XCOMP_PERM
        #define ARCH_REQ_XCOMP_PERM  0x1023
        #endif

        ...
        rc = syscall(SYS_arch_prctl, ARCH_REQ_XCOMP_PERM, ARCH_XCOMP_TILEDATA);

        if (!rc)
            printf("AMX is ready for use.\n");
        ```

注意此示例不包括`sigaltstack`的准备步骤。

### 信号帧中的动态功能
动态启用的功能不会在信号进入时写入信号帧，除非该功能处于其初始配置状态。这与非动态功能不同，非动态功能无论其配置如何都会被写入。信号处理程序可以通过检查XSAVE缓冲区中的XSTATE_BV字段来确定某个功能是否被写入了。

### 虚拟机中的动态功能
客户机状态组件的权限需要与主机分开管理，因为它们是相互独立的。为了控制客户机权限，提供了以下几种选项：

- `ARCH_GET_XCOMP_GUEST_PERM`

    ```c
    arch_prctl(ARCH_GET_XCOMP_GUEST_PERM, &features);
    ```

    `ARCH_GET_XCOMP_GUEST_PERM`是`ARCH_GET_XCOMP_PERM`的一个变体。因此，它提供了相同的功能和语义，但针对的是客户机组件。

- `ARCH_REQ_XCOMP_GUEST_PERM`

    ```c
    arch_prctl(ARCH_REQ_XCOMP_GUEST_PERM, feature_nr);
    ```

    `ARCH_REQ_XCOMP_GUEST_PERM`是`ARCH_REQ_XCOMP_PERM`的一个变体。它为客户机权限提供了相同的语义。虽然提供了类似的功能，但它有一个限制：权限在第一个VCPU创建时就会被冻结。在此之后试图改变权限将被拒绝。因此，在创建第一个VCPU之前必须请求权限。
需要注意的是，某些虚拟机监控器（VMM）可能已经建立了一套支持的状态组件。这些选项并不假定支持任何特定的VMM。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
