### SPDX 许可证标识符: GPL-2.0

编写测试
=========

测试用例
--------

在 KUnit 中，基本单位是测试用例。一个测试用例是一个具有签名 `void (*)(struct kunit *test)` 的函数。它调用被测函数，并设置*期望*以确定预期的行为。例如：

```c
void example_test_success(struct kunit *test)
{
}

void example_test_failure(struct kunit *test)
{
    KUNIT_FAIL(test, "这个测试永远不会通过。");
}
```

在上面的例子中，`example_test_success` 总是通过，因为它什么也不做；没有设置任何期望值，因此所有期望都默认通过。而 `example_test_failure` 总是失败，因为它调用了 `KUNIT_FAIL`，这是一个特殊的期望值，会记录一条消息并导致测试用例失败。

### 期望
*期望* 指定我们希望一段代码在测试中执行特定行为。期望像函数一样被调用。通过为被测代码的行为设置期望来创建测试。当一个或多个期望失败时，测试用例失败，并记录有关失败的信息。例如：

```c
void add_test_basic(struct kunit *test)
{
    KUNIT_EXPECT_EQ(test, 1, add(1, 0));
    KUNIT_EXPECT_EQ(test, 2, add(1, 1));
}
```

在上面的例子中，`add_test_basic` 对名为 `add` 的函数的行为做了几个断言。第一个参数总是 `struct kunit *` 类型，其中包含当前测试上下文的信息。第二个参数是期望的值，在这种情况下，是期望的值是什么。最后一个值是实际的值。如果 `add` 通过了所有的这些期望，测试用例 `add_test_basic` 将通过；如果有任何一个期望失败，测试用例将失败。
当任何期望被违反时，测试用例*失败*；然而，测试将继续运行，并尝试其他期望直到测试用例结束或以其他方式终止。这与稍后讨论的*断言*不同。
要了解更多 KUnit 的期望，请参阅 `Documentation/dev-tools/kunit/api/test.rst`

**注意**：
单个测试用例应该简短、易于理解，并专注于单一的行为。

例如，如果我们想要严格地测试上述 `add` 函数，可以创建额外的测试用例来测试 `add` 函数应具有的每个属性，如下所示：

```c
void add_test_basic(struct kunit *test)
{
    KUNIT_EXPECT_EQ(test, 1, add(1, 0));
    KUNIT_EXPECT_EQ(test, 2, add(1, 1));
}

void add_test_negative(struct kunit *test)
{
    KUNIT_EXPECT_EQ(test, 0, add(-1, 1));
}

void add_test_max(struct kunit *test)
{
    KUNIT_EXPECT_EQ(test, INT_MAX, add(0, INT_MAX));
    KUNIT_EXPECT_EQ(test, -1, add(INT_MAX, INT_MIN));
}

void add_test_overflow(struct kunit *test)
{
    KUNIT_EXPECT_EQ(test, INT_MIN, add(INT_MAX, 1));
}
```

### 断言

断言类似于期望，只是如果条件不满足，断言会立即终止测试用例。例如：

```c
static void test_sort(struct kunit *test)
{
    int *a, i, r = 1;
    a = kunit_kmalloc_array(test, TEST_LEN, sizeof(*a), GFP_KERNEL);
    KUNIT_ASSERT_NOT_ERR_OR_NULL(test, a);
    for (i = 0; i < TEST_LEN; i++) {
        r = (r * 725861) % 6599;
        a[i] = r;
    }
    sort(a, TEST_LEN, sizeof(*a), cmpint, NULL);
    for (i = 0; i < TEST_LEN-1; i++)
        KUNIT_EXPECT_LE(test, a[i], a[i + 1]);
}
```

在这个例子中，我们需要能够分配数组来测试 `sort()` 函数。所以我们使用 `KUNIT_ASSERT_NOT_ERR_OR_NULL()` 来在分配出错时中止测试。

**注意**：
在其他测试框架中，`ASSERT` 宏通常是通过调用 `return` 实现的，所以它们只适用于从测试函数调用。在 KUnit 中，我们在失败时停止当前的 kthread，因此你可以从任何地方调用它们。

**警告**：
有一个例外：你不应该在套件的 `exit()` 函数或资源的释放函数中使用断言。这些函数在测试关闭时运行，这里的断言会阻止进一步的清理代码运行，可能会导致内存泄漏。

### 自定义错误消息

每个 `KUNIT_EXPECT` 和 `KUNIT_ASSERT` 宏都有一个 `_MSG` 变体。这些变体接受格式字符串和参数，以便为自动生成的错误消息提供额外的上下文信息。
### 代码块翻译

```c
char some_str[41];
generate_sha1_hex_string(some_str);

/* 在此之前，很难看出测试失败的原因。*/
KUNIT_EXPECT_EQ(test, strlen(some_str), 40);

/* 之后，我们现在可以看到引起问题的字符串。*/
KUNIT_EXPECT_EQ_MSG(test, strlen(some_str), 40, "some_str='%s'", some_str);
```

或者，可以使用 `KUNIT_FAIL()` 完全控制错误信息，例如：

```c
/* 在此之前 */
KUNIT_EXPECT_EQ(test, some_setup_function(), 0);

/* 之后：对失败消息有完全的控制。*/
if (some_setup_function())
    KUNIT_FAIL(test, "Failed to setup thing for testing");
```

### 测试套件

我们需要许多测试用例来覆盖所有单元的行为。通常会有很多类似的测试。为了减少这些紧密相关的测试中的重复，大多数单元测试框架（包括 KUnit）提供了“测试套件”的概念。测试套件是一组针对某段代码的测试用例，可选地包含在整套测试和/或每个测试用例前后运行的设置和清理函数。
**注释：**
   只有与测试套件关联的测试用例才会运行。

例如：

```c
static struct kunit_case example_test_cases[] = {
    KUNIT_CASE(example_test_foo),
    KUNIT_CASE(example_test_bar),
    KUNIT_CASE(example_test_baz),
    {}
};

static struct kunit_suite example_test_suite = {
    .name = "example",
    .init = example_test_init,
    .exit = example_test_exit,
    .suite_init = example_suite_init,
    .suite_exit = example_suite_exit,
    .test_cases = example_test_cases,
};
kunit_test_suite(example_test_suite);
```

在上面的例子中，测试套件 `example_test_suite` 首先会运行 `example_suite_init`，然后依次运行测试用例 `example_test_foo`、`example_test_bar` 和 `example_test_baz`。每个测试用例在运行前会立即调用 `example_test_init`，运行后会立即调用 `example_test_exit`。最后，在所有操作完成后会调用 `example_suite_exit`。`kunit_test_suite(example_test_suite)` 将测试套件注册到 KUnit 测试框架。
**注释：**
   即使 `init` 或 `suite_init` 失败，`exit` 和 `suite_exit` 函数也会运行。确保它们能够处理由 `init` 或 `suite_init` 遇到错误或提前退出可能产生的任何不一致的状态。

`kunit_test_suite(...)` 是一个宏，它告诉链接器将指定的测试套件放在一个特殊的链接器区域中，以便 KUnit 能够在其后 `late_init` 运行或者当测试模块被加载时运行（如果测试是作为模块构建的话）。
更多信息，请参阅 Documentation/dev-tools/kunit/api/test.rst

### 为其他架构编写测试

最好编写能在 UML 上运行的测试，而不是仅在特定架构下运行的测试。最好编写能在 QEMU 或其他易于获取（且免费）的软件环境中运行的测试，而不是针对特定硬件。不过，仍然有合理的理由编写特定于架构或硬件的测试。例如，我们可能想要测试真正属于 `arch/some-arch/*` 的代码。即便如此，也尽量编写测试使其不依赖物理硬件。我们的某些测试用例可能不需要硬件，只有少数测试确实需要硬件才能进行测试。当没有硬件可用时，与其禁用测试，不如跳过它们。
现在我们已经确切地缩小了哪些部分是硬件特定的，编写和运行测试的实际过程与编写常规的 KUnit 测试相同。
### 重要说明：
我们可能需要重置硬件状态。如果这不可能实现，我们可能只能在每次调用中运行一个测试案例。

### 待办事项（TODO）(brendanhiggins@google.com)：
添加一个实际的架构依赖KUnit测试示例。

### 常见模式
#### 隔离行为

单元测试将受测代码限制在一个单一单元内。它控制当被测单元调用函数时所运行的代码。当一个函数作为API的一部分被公开，使得该函数的定义可以在不影响其余代码库的情况下改变时，这一点变得尤为明显。在内核中，这一点通过两种构造来实现：类，即包含由实现者提供的函数指针的结构体；以及架构特定函数，其定义在编译时被选定。
##### 类
类并不是C编程语言内置的一种构造；然而，这是一个很容易推导出的概念。因此，在大多数情况下，每一个不使用标准化面向对象库（如GNOME的GObject）的项目都有自己略有不同的面向对象编程方式；Linux内核也不例外。
在内核面向对象编程的核心概念是类。在内核中，“类”是一个包含函数指针的结构体。这在“实现者”和“用户”之间建立了一个契约，因为它迫使他们使用相同的函数签名，而无需直接调用该函数。为了成为一个类，函数指针必须指定类的一个指针（称为“类句柄”）作为参数之一。这样成员函数（也称作“方法”）就可以访问成员变量（也称作“字段”），从而允许同一个实现有多个“实例”。

类可以通过子类进行覆盖，通过在子类中嵌入父类。当子类的方法被调用时，子类的实现知道传递给它的指针位于子类内部的父类。因此，子类可以计算出指向自身的指针，因为父类的指针相对于子类的指针总是有一个固定的偏移量。

这个偏移量就是父类在子类结构中的偏移量。例如：

```c
struct shape {
    int (*area)(struct shape *this);
};

struct rectangle {
    struct shape parent;
    int length;
    int width;
};

int rectangle_area(struct shape *this)
{
    struct rectangle *self = container_of(this, struct rectangle, parent);

    return self->length * self->width;
};

void rectangle_new(struct rectangle *self, int length, int width)
{
    self->parent.area = rectangle_area;
    self->length = length;
    self->width = width;
}
```

在这个例子中，从父类指针计算子类指针是通过`container_of`完成的。
##### 模拟类

为了对调用类中方法的代码进行单元测试，方法的行为必须可控，否则测试就不再是单元测试而是集成测试了。

模拟类实现了与生产环境中不同的代码片段，但从调用者的角度来看，它们的行为相同。

这是为了替换难以处理或速度慢的依赖项。例如，实现一个假EEPROM，将“内容”存储在内部缓冲区中。假设我们有一个表示EEPROM的类：

```c
struct eeprom {
    ssize_t (*read)(struct eeprom *this, size_t offset, char *buffer, size_t count);
    ssize_t (*write)(struct eeprom *this, size_t offset, const char *buffer, size_t count);
};
```

我们想要测试缓存写入EEPROM的代码：

```c
struct eeprom_buffer {
    ssize_t (*write)(struct eeprom_buffer *this, const char *buffer, size_t count);
    int flush(struct eeprom_buffer *this);
    size_t flush_count; /* 当缓冲区超过flush_count时进行刷新。 */
};

struct eeprom_buffer *new_eeprom_buffer(struct eeprom *eeprom);
void destroy_eeprom_buffer(struct eeprom_buffer *eeprom_buffer);
```

我们可以通过“模拟”底层EEPROM来测试这段代码：

```c
struct fake_eeprom {
    struct eeprom parent;
    char contents[FAKE_EEPROM_CONTENTS_SIZE];
};

ssize_t fake_eeprom_read(struct eeprom *parent, size_t offset, char *buffer, size_t count)
{
    struct fake_eeprom *this = container_of(parent, struct fake_eeprom, parent);

    count = min(count, FAKE_EEPROM_CONTENTS_SIZE - offset);
    memcpy(buffer, this->contents + offset, count);

    return count;
}

ssize_t fake_eeprom_write(struct eeprom *parent, size_t offset, const char *buffer, size_t count)
{
    struct fake_eeprom *this = container_of(parent, struct fake_eeprom, parent);

    count = min(count, FAKE_EEPROM_CONTENTS_SIZE - offset);
    memcpy(this->contents + offset, buffer, count);

    return count;
}

void fake_eeprom_init(struct fake_eeprom *this)
{
    this->parent.read = fake_eeprom_read;
    this->parent.write = fake_eeprom_write;
    memset(this->contents, 0, FAKE_EEPROM_CONTENTS_SIZE);
}
```

现在我们可以使用它来测试`struct eeprom_buffer`：

```c
struct eeprom_buffer_test {
    struct fake_eeprom *fake_eeprom;
    struct eeprom_buffer *eeprom_buffer;
};

static void eeprom_buffer_test_does_not_write_until_flush(struct kunit *test)
{
    struct eeprom_buffer_test *ctx = test->priv;
    struct eeprom_buffer *eeprom_buffer = ctx->eeprom_buffer;
    struct fake_eeprom *fake_eeprom = ctx->fake_eeprom;
    char buffer[] = {0xff};

    eeprom_buffer->flush_count = SIZE_MAX;

    eeprom_buffer->write(eeprom_buffer, buffer, 1);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[0], 0);

    eeprom_buffer->write(eeprom_buffer, buffer, 1);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[1], 0);

    eeprom_buffer->flush(eeprom_buffer);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[0], 0xff);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[1], 0xff);
}

static void eeprom_buffer_test_flushes_after_flush_count_met(struct kunit *test)
{
    struct eeprom_buffer_test *ctx = test->priv;
    struct eeprom_buffer *eeprom_buffer = ctx->eeprom_buffer;
    struct fake_eeprom *fake_eeprom = ctx->fake_eeprom;
    char buffer[] = {0xff};

    eeprom_buffer->flush_count = 2;

    eeprom_buffer->write(eeprom_buffer, buffer, 1);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[0], 0);

    eeprom_buffer->write(eeprom_buffer, buffer, 1);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[0], 0xff);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[1], 0xff);
}

static void eeprom_buffer_test_flushes_increments_of_flush_count(struct kunit *test)
{
    struct eeprom_buffer_test *ctx = test->priv;
    struct eeprom_buffer *eeprom_buffer = ctx->eeprom_buffer;
    struct fake_eeprom *fake_eeprom = ctx->fake_eeprom;
    char buffer[] = {0xff, 0xff};

    eeprom_buffer->flush_count = 2;

    eeprom_buffer->write(eeprom_buffer, buffer, 1);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[0], 0);

    eeprom_buffer->write(eeprom_buffer, buffer, 2);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[0], 0xff);
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[1], 0xff);
    /* 应该只刷新前两个字节。 */
    KUNIT_EXPECT_EQ(test, fake_eeprom->contents[2], 0);
}

static int eeprom_buffer_test_init(struct kunit *test)
{
    struct eeprom_buffer_test *ctx;

    ctx = kunit_kzalloc(test, sizeof(*ctx), GFP_KERNEL);
    KUNIT_ASSERT_NOT_ERR_OR_NULL(test, ctx);

    ctx->fake_eeprom = kunit_kzalloc(test, sizeof(*ctx->fake_eeprom), GFP_KERNEL);
    KUNIT_ASSERT_NOT_ERR_OR_NULL(test, ctx->fake_eeprom);
    fake_eeprom_init(ctx->fake_eeprom);

    ctx->eeprom_buffer = new_eeprom_buffer(&ctx->fake_eeprom->parent);
    KUNIT_ASSERT_NOT_ERR_OR_NULL(test, ctx->eeprom_buffer);

    test->priv = ctx;

    return 0;
}

static void eeprom_buffer_test_exit(struct kunit *test)
{
    struct eeprom_buffer_test *ctx = test->priv;

    destroy_eeprom_buffer(ctx->eeprom_buffer);
}
```

### 针对多种输入进行测试

仅仅测试几个输入是不足以确保代码正确工作的，例如：测试一个哈希函数。
我们可以编写一个辅助宏或函数。该函数对每个输入都被调用。
例如，为了测试 ``sha1sum(1)``，我们可以这样写：

.. code-block:: c

	#define TEST_SHA1(in, want) \
		sha1sum(in, out); \
		KUNIT_EXPECT_STREQ_MSG(test, out, want, "sha1sum(%s)", in);

	char out[40];
	TEST_SHA1("hello world",  "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed");
	TEST_SHA1("hello world!", "430ce34d020724ed75a196dfc2ad67c77772d169");

请注意在辅助宏中使用了 ``KUNIT_EXPECT_STREQ`` 的 ``_MSG`` 版本来打印更详细的错误信息，并使断言更加清晰。
当相同的期望被多次调用（在一个循环或辅助函数中）时，仅靠行号不足以确定是哪里出错，这时 ``_MSG`` 变体就显得非常有用。

在复杂的情况下，我们建议使用 *表格驱动的测试* 而不是辅助宏变体，例如：

.. code-block:: c

	int i;
	char out[40];

	struct sha1_test_case {
		const char *str;
		const char *sha1;
	};

	struct sha1_test_case cases[] = {
		{
			.str = "hello world",
			.sha1 = "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed",
		},
		{
			.str = "hello world!",
			.sha1 = "430ce34d020724ed75a196dfc2ad67c77772d169",
		},
	};
	for (i = 0; i < ARRAY_SIZE(cases); ++i) {
		sha1sum(cases[i].str, out);
		KUNIT_EXPECT_STREQ_MSG(test, out, cases[i].sha1,
		                      "sha1sum(%s)", cases[i].str);
	}

虽然涉及更多的样板代码，但它可以：

* 在有多个输入/输出的情况下更具可读性（因为有字段名称）
* 例如，请参阅 ``fs/ext4/inode-test.c``
* 如果测试用例可以在多个测试间共享，则减少重复代码
* 例如：如果我们想要测试 ``sha256sum``，我们只需添加一个 ``sha256`` 字段并重用 ``cases``
* 转换成一个“参数化测试”

参数化测试
~~~~~~~~~~~

表格驱动的测试模式很常见，因此 KUnit 对其提供了特殊支持。
通过重用上面的同一个 ``cases`` 数组，我们可以将测试写成一个“参数化测试”，如下所示：
下面是提供的C代码及注释的中文翻译：

```c
// 这段代码是从上面复制过来的
typedef struct {
    const char *str; // 测试字符串
    const char *sha1; // 对应的SHA-1散列值
} sha1_test_case;

const sha1_test_case cases[] = {
    { // 第一个测试案例
        .str = "hello world",
        .sha1 = "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed",
    },
    { // 第二个测试案例
        .str = "hello world!",
        .sha1 = "430ce34d020724ed75a196dfc2ad67c77772d169",
    },
};

// 创建`sha1_gen_params()`来遍历`cases`，并使用结构体成员`str`作为测试描述
KUNIT_ARRAY_PARAM_DESC(sha1, cases, str);

// 看起来和普通的测试函数一样
static void sha1_test(struct kunit *test)
{
    // 这个函数可以只包含for循环的内容
    // 原来的`cases[i]`可以通过`test->param_value`访问
    char out[40];
    sha1_test_case *test_param = (sha1_test_case *)(test->param_value);

    sha1sum(test_param->str, out); // 计算SHA-1散列值
    KUNIT_EXPECT_STREQ_MSG(test, out, test_param->sha1,
                           "sha1sum(%s)", test_param->str); // 检查SHA-1散列值是否正确
}

// 不再使用KUNIT_CASE，而是使用KUNIT_CASE_PARAM，并传入由KUNIT_ARRAY_PARAM或KUNIT_ARRAY_PARAM_DESC声明的函数
static struct kunit_case sha1_test_cases[] = {
    KUNIT_CASE_PARAM(sha1_test, sha1_gen_params),
    {}
};

// 分配内存
// -----------------
// 在你可能使用`kzalloc`的地方，你可以改为使用`kunit_kzalloc`。因为KUnit会确保一旦测试完成就会释放这些内存。
// 这很有用，因为它让我们可以在不担心忘记调用`kfree`的情况下，使用`KUNIT_ASSERT_EQ`宏提前退出测试。
// 例如：
```c
void example_test_allocation(struct kunit *test)
{
    char *buffer = kunit_kzalloc(test, 16, GFP_KERNEL); // 分配内存
    /* 确保分配成功。 */
    KUNIT_ASSERT_NOT_ERR_OR_NULL(test, buffer);

    KUNIT_ASSERT_STREQ(test, buffer, ""); // 检查内存内容是否为空字符串
}
```

// 注册清理操作
// ------------------
// 如果你需要执行一些简单的`kunit_kzalloc`之外的清理工作，你可以注册一个自定义的“延迟执行”动作，
// 即一个在测试结束时（无论是正常结束还是因断言失败而退出）运行的清理函数。
// 动作是带有单个`void*`上下文参数、无返回值的简单函数，它们扮演着Python和Go测试中的“清理”函数、
// 支持它们的语言中的“defer”语句以及某些情况下RAII语言中的析构函数的角色。
```
这些对于从全局列表中注销项目、关闭文件或其他资源或释放资源非常有用。
例如：

.. code-block:: C

    static void cleanup_device(void *ctx)
    {
        struct device *dev = (struct device *)ctx;

        device_unregister(dev);
    }

    void example_device_test(struct kunit *test)
    {
        struct my_device dev;

        device_register(&dev);

        kunit_add_action(test, &cleanup_device, &dev);
    }

请注意，对于像 `device_unregister` 这样只接受一个指针大小参数的函数，可以使用 `KUNIT_DEFINE_ACTION_WRAPPER()` 宏自动生成包装器，例如：

.. code-block:: C

    KUNIT_DEFINE_ACTION_WRAPPER(device_unregister, device_unregister_wrapper, struct device *);
    kunit_add_action(test, &device_unregister_wrapper, &dev);

您应该优先采用这种方式，而不是手动将函数转换为 `kunit_action_t` 类型，因为转换函数指针会破坏控制流完整性（CFI）。
`kunit_add_action` 可能会失败，例如系统内存不足时。您可以使用 `kunit_add_action_or_reset` 替代，如果不能延迟执行则立即运行动作。
如果您需要更多地控制清理函数何时被调用，可以使用 `kunit_release_action` 来提前触发它，或者使用 `kunit_remove_action` 完全取消它。
测试静态函数
--------------

如果我们不想为了测试而暴露函数或变量，一个选项是条件性地导出使用的符号。例如：

.. code-block:: c

    /* 在 my_file.c 中 */

    VISIBLE_IF_KUNIT int do_interesting_thing();
    EXPORT_SYMBOL_IF_KUNIT(do_interesting_thing);

    /* 在 my_file.h 中 */

    #if IS_ENABLED(CONFIG_KUNIT)
        int do_interesting_thing(void);
    #endif

或者，您可以在您的 .c 文件末尾有条件地 `#include` 测试文件。例如：

.. code-block:: c

    /* 在 my_file.c 中 */

    static int do_interesting_thing();

    #ifdef CONFIG_MY_KUNIT_TEST
    #include "my_kunit_test.c"
    #endif

注入仅用于测试的代码
---------------------

与上面所示类似，我们可以添加仅用于测试的逻辑。例如：

.. code-block:: c

    /* 在 my_file.h 中 */

    #ifdef CONFIG_MY_KUNIT_TEST
        /* 在 my_kunit_test.c 中定义 */
        void test_only_hook(void);
    #else
        void test_only_hook(void) { }
    #endif

此仅用于测试的代码可以通过访问当前 `kunit_test` 而变得更加有用，如下一节所述：*访问当前测试*
访问当前测试
--------------

在某些情况下，我们需要从测试文件之外调用仅用于测试的代码。这在提供函数的假实现或从错误处理器内使任何当前测试失败时是有帮助的。
我们可以通过 `task_struct` 中的 `kunit_test` 字段来做到这一点，该字段可以通过 `kunit/test-bug.h` 中的 `kunit_get_current_test()` 函数访问。
即使 KUnit 没有启用，`kunit_get_current_test()` 也是安全的。如果没有启用 KUnit 或者当前任务没有运行测试，则返回 `NULL`。这编译后几乎不消耗性能，或者是一个静态键检查，因此在没有运行测试时对性能的影响微乎其微。
下面的例子展示了如何使用这个方法来实现一个函数 `foo` 的“模拟”实现：

.. code-block:: c

    #include <kunit/test-bug.h> /* 为了 kunit_get_current_test */

    struct test_data {
        int foo_result;
        int want_foo_called_with;
    };

    static int fake_foo(int arg)
    {
        struct kunit *test = kunit_get_current_test();
        struct test_data *test_data = test->priv;

        KUNIT_EXPECT_EQ(test, test_data->want_foo_called_with, arg);
        return test_data->foo_result;
    }

    static void example_simple_test(struct kunit *test)
    {
        /* 假设 priv（私有成员，用于从初始化函数传递测试数据）在套件的 .init 中分配 */
        struct test_data *test_data = test->priv;

        test_data->foo_result = 42;
        test_data->want_foo_called_with = 1;

        /* 在实际测试中，我们可能会将 fake_foo 的指针通过操作结构体等途径传递，而不是直接调用它。 */
        KUNIT_EXPECT_EQ(test, fake_foo(1), 42);
    }

在此示例中，我们使用 `struct kunit` 的 `priv` 成员作为从初始化函数向测试传递数据的方式。通常 `priv` 是一个可用于任何用户数据的指针。这种方式优于使用静态变量，因为它避免了并发问题。
如果我们需要更灵活的方式，我们可以使用命名的 ``kunit_resource``
每个测试可以有多个资源，这些资源通过字符串名称提供与 ``priv`` 成员相同的灵活性，同时还可以让辅助函数创建资源而不会相互冲突。对于每个资源也可以定义清理函数，使得避免资源泄露变得简单。更多信息，请参阅 `Documentation/dev-tools/kunit/api/resource.rst`
使当前测试失败
------------------------

如果我们想要使当前测试失败，我们可以使用 ``kunit_fail_current_test(fmt, args...)``
这个函数定义在 ``<kunit/test-bug.h>`` 中，并不需要引入 ``<kunit/test.h>``
例如，我们有一个选项可以在某些数据结构上启用一些额外的调试检查，如下所示：

.. code-block:: c

	#include <kunit/test-bug.h>

	#ifdef CONFIG_EXTRA_DEBUG_CHECKS
	static void validate_my_data(struct data *data)
	{
		if (is_valid(data))
			return;

		kunit_fail_current_test("data %p is invalid", data);

		/* 正常的、非KUnit的错误报告代码放这里。 */
	}
	#else
	static void my_debug_function(void) { }
	#endif

``kunit_fail_current_test()`` 即使在未启用KUnit的情况下调用也是安全的。如果
没有启用KUnit，或者当前任务中没有运行任何测试，它将什么都不做。这编译下来会变成一个无操作指令或静态键检查，因此当没有测试运行时对性能的影响可以忽略不计。
管理假设备和驱动程序
------------------------------

在测试驱动程序或与驱动程序交互的代码时，许多函数都需要 ``struct device`` 或 ``struct device_driver``。在许多情况下，为了测试特定功能并不需要设置真实的设备，所以可以使用假设备代替。
KUnit提供了帮助函数来创建和管理这些假设备，这些设备内部类型为 ``struct kunit_device``，并且连接到一个特殊的 ``kunit_bus`` 上。这些设备支持受管理的设备资源（devres），具体描述请参考 `Documentation/driver-api/driver-model/devres.rst`

要创建一个由KUnit管理的 ``struct device_driver``，可以使用 ``kunit_driver_create()``，
这将创建一个指定名称的驱动程序，在 ``kunit_bus`` 上。该驱动程序将在相应的测试完成后自动销毁，但也可以手动使用 ``driver_unregister()`` 销毁。
要创建一个假设备，可以使用 ``kunit_device_register()``，
这将创建并注册一个设备，使用通过 ``kunit_driver_create()`` 创建的新KUnit管理的驱动程序
若要提供一个特定的、非KUnit管理的驱动程序，则应使用 ``kunit_device_register_with_driver()``。
如同管理驱动程序一样，KUnit管理的假设备会在测试完成后自动清理，但也可以通过 ``kunit_device_unregister()`` 早期手动清理。
KUnit设备应当优先于 ``root_device_register()`` 使用，并且在设备不是平台设备的情况下代替 ``platform_device_register()`` 使用。
例如：

.. code-block:: c

	#include <kunit/device.h>

	static void test_my_device(struct kunit *test)
	{
		struct device *fake_device;
		const char *dev_managed_string;

		// 创建一个假设备
这段代码可以翻译为如下中文描述：

`fake_device = kunit_device_register(test, "my_device");` 这一行创建了一个名为 "my_device" 的虚拟设备。

`KUNIT_ASSERT_NOT_ERR_OR_NULL(test, fake_device)` 确保 `fake_device` 创建成功且不为空。

// 将该虚拟设备传递给需要设备参数的函数
`dev_managed_string = devm_kstrdup(fake_device, "Hello, World!");`

// 当测试结束时，所有资源会自动清理
}

简而言之，此段代码的主要目的是创建一个虚拟设备并使用它来分配一些字符串资源，并确保在测试结束后这些资源会被自动清理。
