对象生命周期调试基础设施
============================================

:作者: Thomas Gleixner

简介
============

`debugobjects` 是一个通用的基础设施，用于跟踪内核对象的生命周期并验证对这些 `debugobjects` 的操作。`debugobjects` 有助于检测以下错误模式：

-  未初始化对象的激活

-  已激活对象的初始化

-  使用已释放/销毁的对象

`debugobjects` 不会改变实际对象的数据结构，因此它可以以最小的运行时影响编译，并且可以通过内核命令行选项按需启用。

如何使用 `debugobjects`
======================

内核子系统需要提供一个数据结构来描述对象类型，并在适当的地方调用调试代码。描述对象类型的该数据结构至少需要包含对象类型的名字。可以提供可选的函数来修正检测到的问题，以便内核能够继续工作，并且可以从运行中的系统获取调试信息，而不是通过串口控制台和监视器的堆栈跟踪转录进行硬核调试。

`debugobjects` 提供的调试调用包括：

-  debug_object_init

-  debug_object_init_on_stack

-  debug_object_activate

-  debug_object_deactivate

-  debug_object_destroy

-  debug_object_free

-  debug_object_assert_init

每个函数都需要传入实际对象的地址以及指向特定于对象类型调试描述结构的指针。

每次检测到的错误都会在统计信息中报告，并且一定数量的错误会打印（printk）出来，包括完整的堆栈跟踪。
统计信息可通过 `/sys/kernel/debug/debug_objects/stats` 获取。它们提供了关于警告数量、成功修复的数量以及内部跟踪对象使用情况的信息，还有内部跟踪对象池的状态。

调试函数
===============

.. kernel-doc:: lib/debugobjects.c
   :functions: debug_object_init

当实际对象的初始化函数被调用时，会调用此函数。
如果实际对象已经被 `debugobjects` 跟踪，则会检查该对象是否可以被初始化。不允许对活跃或已销毁的对象进行初始化。如果 `debugobjects` 检测到错误，则会调用对象类型描述结构中的 fixup_init 函数（如果由调用者提供）。修复函数可以在实际初始化对象之前修正问题。例如，它可以将活跃的对象停用，以防止对子系统的损害。

如果实际对象尚未被 `debugobjects` 跟踪，则 `debugobjects` 会为实际对象分配一个跟踪对象，并将跟踪对象状态设置为 ODEBUG_STATE_INIT。它会验证对象不在调用者的栈上。如果对象确实在调用者的栈上，则会打印（printk）有限数量的警告，包括完整的堆栈跟踪。调用代码必须使用 `debug_object_init_on_stack()` 并在离开分配它的函数前移除该对象。详情请参见下一节。
### `kernel-doc:: lib/debugobjects.c`
#### 函数: `debug_object_init_on_stack`

此函数在堆栈上实际对象的初始化函数被调用时被调用。
- 如果该实际对象已经被`debugobjects`跟踪，则会检查该对象是否可以被初始化。对于活动或已销毁的对象，不允许进行初始化。
- 如果`debugobjects`检测到错误，则会调用由调用者提供的对象类型描述结构中的`fixup_init`函数（如果提供）。`fixup`函数可以在实际初始化对象之前修正问题。例如，它可以停用活动对象以防止对子系统造成损害。
- 如果实际对象尚未被`debugobjects`跟踪，则`debugobjects`会为该实际对象分配一个跟踪器对象，并将跟踪器对象的状态设置为`ODEBUG_STATE_INIT`。它还会验证该对象位于调用者的堆栈上。
- 堆栈上的对象必须在分配该对象的函数返回之前通过调用`debug_object_free()`从跟踪器中移除。否则，我们会持续跟踪无效对象。

### `kernel-doc:: lib/debugobjects.c`
#### 函数: `debug_object_activate`

此函数在实际对象的激活函数被调用时被调用。
- 如果该实际对象已经被`debugobjects`跟踪，则会检查该对象是否可以被激活。对于活动或已销毁的对象，不允许进行激活。
- 如果`debugobjects`检测到错误，则会调用由调用者提供的对象类型描述结构中的`fixup_activate`函数（如果提供）。`fixup`函数可以在实际激活对象之前修正问题。例如，它可以停用活动对象以防止对子系统造成损害。
- 如果实际对象尚未被`debugobjects`跟踪，则会调用`fixup_activate`函数（如果可用）。这是必要的，以便允许合法地激活静态分配和初始化的对象。`fixup`函数会检查该对象是否有效，并调用`debug_objects_init()`函数来初始化对该对象的跟踪。
- 如果激活是合法的，则与之关联的跟踪器对象的状态会被设置为`ODEBUG_STATE_ACTIVE`。

### `kernel-doc:: lib/debugobjects.c`
#### 函数: `debug_object_deactivate`

此函数在实际对象的停用函数被调用时被调用。
- 如果该实际对象被`debugobjects`跟踪，则会检查该对象是否可以被停用。对于未跟踪或已销毁的对象，不允许进行停用。
当停用操作是合法的，那么与之关联的跟踪器对象的状态将被设置为 `ODEBUG_STATE_INACTIVE`。

.. kernel-doc:: lib/debugobjects.c
   :functions: debug_object_destroy

此函数用于标记一个对象已被销毁。这对于防止使用仍然存在于内存中的无效对象非常有用：这些对象可能是静态分配的对象，也可能是稍后才释放的对象。
当实际对象被 debugobjects 跟踪时，会检查该对象是否可以被销毁。不允许销毁处于活动状态或已被销毁的对象。如果 debugobjects 检测到错误，则会调用由调用者提供的对象类型描述结构中的 `fixup_destroy` 函数（如果提供的话）。修复函数可以在实际销毁对象之前解决问题。例如，它可以停用活动对象以防止对子系统造成损害。
当销毁操作是合法的，那么与之关联的跟踪器对象的状态将被设置为 `ODEBUG_STATE_DESTROYED`。

.. kernel-doc:: lib/debugobjects.c
   :functions: debug_object_free

此函数在对象被释放前被调用。
当实际对象被 debugobjects 跟踪时，会检查该对象是否可以被释放。不允许释放处于活动状态的对象。如果 debugobjects 检测到错误，则会调用由调用者提供的对象类型描述结构中的 `fixup_free` 函数（如果提供的话）。修复函数可以在实际释放对象之前解决问题。例如，它可以停用活动对象以防止对子系统造成损害。
请注意，`debug_object_free` 会从跟踪器中移除该对象。之后对该对象的使用将由其他调试检查来检测。

.. kernel-doc:: lib/debugobjects.c
   :functions: debug_object_assert_init

此函数用于断言一个对象已经被初始化。
当实际对象未被 debugobjects 跟踪时，它会调用由调用者提供的对象类型描述结构中的 `fixup_assert_init`，并带有硬编码的对象状态 `ODEBUG_NOT_AVAILABLE`。修复函数可以通过调用 `debug_object_init` 和其他特定的初始化函数来纠正问题。
当实际对象已经被 debugobjects 跟踪时，此操作将被忽略。
### 修复函数
#### 调试对象类型描述结构

##### .. kernel-doc:: include/linux/debugobjects.h
   :internal:

### fixup_init
---

此函数在检测到 `debug_object_init` 中出现问题时由调试代码调用。该函数接收对象的地址和当前记录在追踪器中的状态。当对象状态为：

-  ODEBUG_STATE_ACTIVE

函数成功修复时返回真，否则返回假。返回值用于更新统计信息。注意，该函数需要在修复损坏后再次调用 `debug_object_init()` 函数以保持状态一致。

### fixup_activate
---

此函数在检测到 `debug_object_activate` 中存在问题时由调试代码调用。
当对象状态为：

-  ODEBUG_STATE_NOTAVAILABLE
-  ODEBUG_STATE_ACTIVE

函数成功修复时返回真，否则返回假。返回值用于更新统计信息。注意，该函数需要在修复损坏后再次调用 `debug_object_activate()` 函数以保持状态一致。
静态初始化对象的激活是一个特殊情况。如果 `debug_object_activate()` 对于这个对象地址没有追踪的对象，则会以 `ODEBUG_STATE_NOTAVAILABLE` 的对象状态调用 `fixup_activate()`。修复函数需要检查这是否是合法的静态初始化对象的情况。如果是，则调用 `debug_object_init()` 和 `debug_object_activate()` 使对象对追踪器可见并标记为活动状态。在这种情况下，函数应返回假，因为这不是真正的修复。

### fixup_destroy
---

此函数在检测到 `debug_object_destroy` 中存在问题时由调试代码调用。
当对象状态为：

-  ODEBUG_STATE_ACTIVE

函数成功修复时返回真，否则返回假。返回值用于更新统计信息。

### fixup_free
---

此函数在检测到 `debug_object_free` 中存在问题时由调试代码调用。此外，当从 `debug_check_no_obj_freed()` 的合理性检查中检测到活动对象时，它还可以从 kfree/vfree 的调试检查中被调用。
当对象状态为以下情况时，从 `debug_object_free()` 或 `debug_check_no_obj_freed()` 被调用：

-  `ODEBUG_STATE_ACTIVE`

该函数在修复成功时返回 `true`，否则返回 `false`。返回值用于更新统计信息。

`fixup_assert_init`
-------------------

此函数在检测到 `debug_object_assert_init` 中存在问题时由调试代码调用。
当在调试桶中未找到对象时，从 `debug_object_assert_init()` 调用，带有硬编码的状态 `ODEBUG_STATE_NOTAVAILABLE`。
该函数在修复成功时返回 `true`，否则返回 `false`。返回值用于更新统计信息。
注意，此函数应在返回前确保已调用 `debug_object_init()`。
静态初始化对象的处理是一个特殊情况。修复函数应检查这是不是合法的静态初始化对象。在这种情况下，仅调用 `debug_object_init()` 以使追踪器知晓该对象。然后函数应返回 `false`，因为这不是真正的修复。
已知问题与假设
==========================

目前没有已知问题（敲木头）。
