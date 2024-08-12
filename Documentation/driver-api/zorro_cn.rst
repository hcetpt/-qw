为Zorro设备编写设备驱动程序
========================================

:作者: 由Geert Uytterhoeven <geert@linux-m68k.org> 编写
:最后修订日期: 2003年9月5日


简介
------------

Zorro总线是Amiga系列计算机中使用的总线。由于AutoConfig™技术，它实现了100%的即插即用功能。
有两种类型的Zorro总线：Zorro II和Zorro III：

  - Zorro II地址空间为24位，并位于Amiga地址映射的前16MB内。
- Zorro III是Zorro II的32位扩展，与Zorro II向后兼容。Zorro III的地址空间位于前16MB之外。
探测Zorro设备
-------------------------

通过调用`zorro_find_device()`来查找Zorro设备，该函数返回指向具有指定Zorro ID的下一个Zorro设备的指针。对于具有Zorro ID `ZORRO_PROD_xxx`的板卡的探测循环如下所示：

```c
struct zorro_dev *z = NULL;

while ((z = zorro_find_device(ZORRO_PROD_xxx, z))) {
    if (!zorro_request_region(z->resource.start+MY_START, MY_SIZE, "我的解释"))
    ..
}
```

`ZORRO_WILDCARD`作为通配符使用，可以查找任何Zorro设备。如果你的驱动支持不同类型的板卡，可以使用类似下面的结构：

```c
struct zorro_dev *z = NULL;

while ((z = zorro_find_device(ZORRO_WILDCARD, z))) {
    if (z->id != ZORRO_PROD_xxx1 && z->id != ZORRO_PROD_xxx2 && ...)
        continue;
    if (!zorro_request_region(z->resource.start+MY_START, MY_SIZE, "我的解释"))
    ..
}
```


Zorro资源
--------------

在访问Zorro设备的寄存器之前，需要确保其尚未被使用。这可以通过I/O内存空间资源管理函数实现：

```c
request_mem_region()
release_mem_region()
```

还提供了快捷方式以声明整个设备的地址空间：

```c
zorro_request_device
zorro_release_device
```


访问Zorro地址空间
-----------------------------

Zorro设备资源中的地址区域是Zorro总线地址区域。由于Zorro总线上物理地址与总线地址之间的等同映射，它们也是CPU的物理地址。
这些区域的处理取决于Zorro空间的类型：

  - Zorro II地址空间总是被映射，不需要使用`z_ioremap()`显式地进行映射。
转换从总线/物理Zorro II地址到内核虚拟地址及其反向转换使用：

```c
virt_addr = ZTWO_VADDR(bus_addr);
bus_addr = ZTWO_PADDR(virt_addr);
```

  - Zorro III地址空间必须首先使用`z_ioremap()`显式映射才能访问：
  
```c
virt_addr = z_ioremap(bus_addr, size);
..
z_iounmap(virt_addr);
```


参考文献
--------------

1. linux/include/linux/zorro.h
2. linux/include/uapi/linux/zorro.h
3. linux/include/uapi/linux/zorro_ids.h
4. linux/arch/m68k/include/asm/zorro.h
5. linux/drivers/zorro
6. /proc/bus/zorro
