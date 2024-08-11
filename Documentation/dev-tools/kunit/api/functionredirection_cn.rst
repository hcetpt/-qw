SPDX 许可证标识符: GPL-2.0

========================
函数重定向 API
========================

概述
========

在编写单元测试时，能够将被测代码与其他内核部分隔离至关重要。这确保了测试的可靠性（它不会受到外部因素的影响），减少了对特定硬件或配置选项的依赖（使测试更容易运行），并保护了系统的其余部分的稳定性（降低了测试特定状态干扰系统其余部分的可能性）。
对于某些代码（通常是通用的数据结构、辅助函数和其他“纯函数”）来说，这一点很容易做到，而对于其他代码（如设备驱动程序、文件系统、核心子系统）则与内核的其他部分紧密耦合。
这种耦合通常以某种形式的全局状态为原因：可能是全局设备列表、文件系统或一些硬件状态。测试需要谨慎管理、隔离和恢复这些状态，或者通过替换访问和修改这些状态的方法来完全避免它们，使用一种“假”或“模拟”的变体。
通过重构对这种状态的访问，例如引入一层间接层来使用或模拟一套独立的测试状态。然而，这样的重构也有其自身的成本（并且在能够编写测试之前进行大规模重构是次优的选择）。
一种更简单的方式来拦截并替换一些函数调用是使用静态存根进行函数重定向。
静态存根
============

静态存根是一种将对一个函数（“真实”函数）的调用重定向到另一个函数（“替代”函数）的方式。
它的工作原理是在“真实”函数中添加一个宏，该宏检查是否正在运行测试，并且是否有可用的替代函数。如果有，则调用该函数代替原始函数。
使用静态存根相当直接：

1. 在“真实”函数的开头添加 KUNIT_STATIC_STUB_REDIRECT() 宏
这应该是函数中的第一条语句，在任何变量声明之后。KUNIT_STATIC_STUB_REDIRECT() 需要传入函数名，后面跟着传递给实际函数的所有参数。
例如：

   .. code-block:: c

      void send_data_to_hardware(const char *str)
      {
          KUNIT_STATIC_STUB_REDIRECT(send_data_to_hardware, str);
          /* 实际实现 */
      }

2. 编写一个或多个替代函数
这些函数应该与实际函数具有相同的函数签名。如果需要访问或修改特定于测试的状态，它们可以使用 `kunit_get_current_test()` 来获取一个 `struct kunit` 指针。然后该指针可以传递给期望/断言宏，或者用于查找 KUnit 资源。

例如：

   .. 代码块:: c

      void fake_send_data_to_hardware(const char *str)
      {
          struct kunit *test = kunit_get_current_test();
          KUNIT_EXPECT_STREQ(test, str, "Hello World!");
      }

3. 在你的测试中激活静态桩
在测试内部，可以通过 `kunit_activate_static_stub()` 启用重定向，它接受一个 `struct kunit` 指针、实际函数和替代函数。你可以多次调用这个函数，使用不同的替代函数来替换该函数的实现。

在我们的示例中，这将是：

   .. 代码块:: c

      kunit_activate_static_stub(test,
                                 send_data_to_hardware,
                                 fake_send_data_to_hardware);

4. 调用（可能间接地）实际函数
一旦重定向被激活，对实际函数的所有调用将调用替代函数代替。这种调用可能深埋在另一个函数的实现中，但必须从测试的 kthread 中发生。
例如：

   .. 代码块:: c

      send_data_to_hardware("Hello World!"); /* 成功 */
      send_data_to_hardware("Something else"); /* 测试失败。 */

5. （可选）禁用桩
当你不再需要时，可以使用 `kunit_deactivate_static_stub()` 禁用重定向（从而恢复实际函数的原始行为）。否则，当测试退出时，它将自动禁用。
例如：

   .. 代码块:: c

      kunit_deactivate_static_stub(test, send_data_to_hardware);

也可以使用这些替代函数来测试函数是否被调用，例如：

.. 代码块:: c

   void send_data_to_hardware(const char *str)
   {
       KUNIT_STATIC_STUB_REDIRECT(send_data_to_hardware, str);
       /* 实际实现 */
   }

   /* 在测试文件中 */
   int times_called = 0;
   void fake_send_data_to_hardware(const char *str)
   {
       times_called++;
   }
   ..
   /* 在测试案例中，为测试期间重定向调用 */
   kunit_activate_static_stub(test, send_data_to_hardware, fake_send_data_to_hardware);

   send_data_to_hardware("hello");
   KUNIT_EXPECT_EQ(test, times_called, 1);

   /* 如果需要，也可以提前禁用桩 */
   kunit_deactivate_static_stub(test, send_data_to_hardware);

   send_data_to_hardware("hello again");
   KUNIT_EXPECT_EQ(test, times_called, 1);

API 参考
========

.. kernel-doc:: include/kunit/static_stub.h
   :internal:
