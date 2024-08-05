应用数据完整性 (ADI)
=====================

SPARC M7 处理器增加了应用数据完整性 (ADI) 功能。
ADI 允许任务为其地址空间的任何子集设置版本标签。一旦启用了 ADI 并为任务的地址空间范围设置了版本标签，处理器会将指向这些范围内存中的指针中的标签与应用程序之前设置的版本进行比较。只有当给定指针中的标签与应用程序设置的标签匹配时，才允许访问内存。如果不匹配，处理器会引发异常。
要完全启用 ADI，任务必须采取以下步骤：

1. 设置用户模式下的 PSTATE.mcde 位。这作为任务整个地址空间的主开关，用于为该任务启用或禁用 ADI。
2. 对应于启用 ADI 的地址范围的任何 TLB 条目上设置 TTE.mcd 位。MMU 仅在设置了 TTE.mcd 位的页面上检查版本标签。
3. 使用 stxa 指令和其中一个 MCD 特定的 ASI 为虚拟地址设置版本标签。每个 stxa 指令为 ADI 块大小数量的字节设置给定的标签。此步骤必须在整个页面上重复执行以针对整个页面设置标签。

平台的 ADI 块大小由虚拟机监控程序提供给内核的机器描述表中给出。虚拟机监控程序还提供了虚拟地址中指定版本标签的最高位数。一旦为内存位置设置了版本标签，该标签就会存储在物理内存中，并且呈现给 MMU 的虚拟地址的 ADI 版本标签位中必须存在相同的标签。例如，在 SPARC M7 处理器上，MMU 使用位 63-60 作为版本标签，ADI 块大小等于缓存行大小，即 64 字节。如果任务在内存范围内设置 ADI 版本为 10，则必须使用包含位 63-60 中值 0xa 的虚拟地址来访问该内存。

使用带有 PROT_ADI 标志的 mprotect() 启用一组页面上的 ADI。
当任务首次启用一组页面上的 ADI 时，内核会为该任务设置 PSTATE.mcde 位。使用 ASI_MCD_PRIMARY 或 ASI_MCD_ST_BLKINIT_PRIMARY 在地址上使用 stxa 指令设置内存地址的版本标签。ADI 块大小由虚拟机监控程序提供给内核。内核通过辅助向量与其他 ADI 信息一起返回 ADI 块大小的值。内核提供的辅助向量如下：

	============	===========================================
	AT_ADI_BLKSZ	ADI 块大小。这是 ADI 版本化的粒度和
			对齐方式，单位为字节
	AT_ADI_NBITS	虚拟地址中的 ADI 版本位数
	============	===========================================

重要说明
========

- 版本标签值 0x0 和 0xf 是保留的。这些值与虚拟地址中的任何标签匹配，且永远不会产生不匹配异常。
- 版本标签是在用户空间为虚拟地址设置的，尽管标签存储在物理内存中。标签是在为任务分配物理页并为它创建了页表条目之后设置的。
当一个任务释放了它曾设置版本标签的内存页时，该页会返回到空闲页池。当这个页被重新分配给一个任务时，内核使用块初始化ASI（Address Space Initialization）来清除该页，同时也会清除该页上的版本标签。如果分配给一个任务的页被释放后又重新分配给了同一个任务，那么该任务原先在这个页上设置的老版本标签将不再存在。

对于未触发错误的加载操作，不会检测ADI（Address Data Integrity）标签不匹配的情况。

内核不对用户页设置任何标签，完全由任务负责设置任何版本标签。内核确保如果一个页被交换到磁盘然后再换回时，其版本标签得以保留。同样地，如果一个页被迁移时，其版本标签也会被保留。

ADI适用于任何大小的页。用户空间的任务在使用ADI时不必关心页大小。它可以简单地选择一个虚拟地址范围，使用mprotect()启用该范围内的ADI，并为整个范围设置版本标签。mprotect()确保所选范围对齐到页大小并且是页大小的倍数。

ADI标签只能设置在可写内存中。例如，不能在只读映射上设置ADI标签。

ADI相关的陷阱
==============

启用ADI时，可能会发生以下新的陷阱：

破坏性的内存损坏
-------------------

当一个存储访问了一个具有TTE.mcd=1的内存位置，且任务正在以ADI启用状态运行（PSTATE.mcde=1），以及使用的地址中的ADI标签（位63:60）与相应缓存行上的标签不匹配时，会发生内存损坏陷阱。默认情况下，这是一个破坏性陷阱，并首先发送给hypervisor。hypervisor创建一个sun4v错误报告，并向内核发送一个可恢复错误（TT=0x7e）的陷阱。内核向导致此陷阱的任务发送SIGSEGV信号，信息如下所示：

    siginfo.si_signo = SIGSEGV;
    siginfo.errno = 0;
    siginfo.si_code = SEGV_ADIDERR;
    siginfo.si_addr = addr; /* 第一次不匹配发生的PC地址 */
    siginfo.si_trapno = 0;

精确的内存损坏
------------------

当一个存储访问了一个具有TTE.mcd=1的内存位置，且任务正在以ADI启用状态运行（PSTATE.mcde=1），以及使用的地址中的ADI标签（位63:60）与相应缓存行上的标签不匹配时，会发生内存损坏陷阱。如果启用了MCD精确异常（MCDPERR=1），则会向内核发送一个TT=0x1a的精确异常。内核向导致此陷阱的任务发送SIGSEGV信号，信息如下所示：

    siginfo.si_signo = SIGSEGV;
    siginfo.errno = 0;
    siginfo.si_code = SEGV_ADIPERR;
    siginfo.si_addr = addr; /* 导致陷阱的地址 */
    siginfo.si_trapno = 0;

**注意：**
        在加载过程中ADI标签不匹配总是导致精确陷阱。
MCD禁用
--------

当一个任务没有启用ADI并试图在一个内存地址上设置ADI版本时，处理器会发送一个MCD禁用陷阱。此陷阱首先由hypervisor处理，hypervisor通过将此陷阱作为数据访问异常陷阱（故障类型设置为0xa，即无效ASI）转发给内核。当这种情况发生时，内核向任务发送SIGSEGV信号，信息如下：

    siginfo.si_signo = SIGSEGV;
    siginfo.errno = 0;
    siginfo.si_code = SEGV_ACCADI;
    siginfo.si_addr = addr; /* 导致陷阱的地址 */
    siginfo.si_trapno = 0;

使用ADI的示例程序
------------------

下面的示例程序旨在说明如何使用ADI功能：

```c
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <elf.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/mman.h>
#include <asm/asi.h>

#ifndef AT_ADI_BLKSZ
#define AT_ADI_BLKSZ 48
#endif
#ifndef AT_ADI_NBITS
#define AT_ADI_NBITS 49
#endif

#ifndef PROT_ADI
#define PROT_ADI 0x10
#endif

#define BUFFER_SIZE 32*1024*1024UL

int main(int argc, char* argv[], char* envp[])
{
        unsigned long i, mcde, adi_blksz, adi_nbits;
        char *shmaddr, *tmp_addr, *end, *veraddr, *clraddr;
        int shmid, version;
        Elf64_auxv_t *auxv;

        adi_blksz = 0;

        while(*envp++ != NULL);
        for (auxv = (Elf64_auxv_t *)envp; auxv->a_type != AT_NULL; auxv++) {
                switch (auxv->a_type) {
                case AT_ADI_BLKSZ:
                        adi_blksz = auxv->a_un.a_val;
                        break;
                case AT_ADI_NBITS:
                        adi_nbits = auxv->a_un.a_val;
                        break;
                }
        }
        if (adi_blksz == 0) {
                fprintf(stderr, "Oops! ADI is not supported\n");
                exit(1);
        }

        printf("ADI capabilities:\n");
        printf("\tBlock size = %ld\n", adi_blksz);
        printf("\tNumber of bits = %ld\n", adi_nbits);

        if ((shmid = shmget(2, BUFFER_SIZE, IPC_CREAT | SHM_R | SHM_W)) < 0) {
                perror("shmget failed");
                exit(1);
        }

        shmaddr = shmat(shmid, NULL, 0);
        if (shmaddr == (char *)-1) {
                perror("shm attach failed");
                shmctl(shmid, IPC_RMID, NULL);
                exit(1);
        }

        if (mprotect(shmaddr, BUFFER_SIZE, PROT_READ|PROT_WRITE|PROT_ADI)) {
                perror("mprotect failed");
                goto err_out;
        }

        /* 在共享内存段上设置ADI版本标签 */
        version = 10;
        tmp_addr = shmaddr;
        end = shmaddr + BUFFER_SIZE;
        while (tmp_addr < end) {
                asm volatile(
                        "stxa %1, [%0]0x90\n\t"
                        :
                        : "r" (tmp_addr), "r" (version));
                tmp_addr += adi_blksz;
        }
        asm volatile("membar #Sync\n\t");

        /* 通过在最高adi_nbits位放置版本标签来从常规地址创建一个带有版本的地址 */
        tmp_addr = (void *) ((unsigned long)shmaddr << adi_nbits);
        tmp_addr = (void *) ((unsigned long)tmp_addr >> adi_nbits);
        veraddr = (void *) (((unsigned long)version << (64-adi_nbits))
                      | (unsigned long)tmp_addr);

        printf("开始写入：\n");
        for (i = 0; i < BUFFER_SIZE; i++) {
                veraddr[i] = (char)(i);
                if (!(i % (1024 * 1024)))
                        printf(".");
        }
        printf("\n");

        printf("验证数据...");
        fflush(stdout);
        for (i = 0; i < BUFFER_SIZE; i++)
                if (veraddr[i] != (char)i)
                        printf("\n索引 %lu 不匹配\n", i);
        printf("完成。\n");

        /* 禁用ADI并清理 */
        if (mprotect(shmaddr, BUFFER_SIZE, PROT_READ|PROT_WRITE)) {
                perror("mprotect failed");
                goto err_out;
        }

        if (shmdt((const void *)shmaddr) != 0)
                perror("detach失败");
        shmctl(shmid, IPC_RMID, NULL);

        exit(0);

err_out:
        if (shmdt((const void *)shmaddr) != 0)
                perror("detach失败");
        shmctl(shmid, IPC_RMID, NULL);
        exit(1);
}
```
```
