可重现构建
===================

通常希望使用相同的工具集编译相同的源代码时能够得到完全相同的结果。这使得可以验证二进制发行版或嵌入式系统的构建基础设施是否被篡改。此外，这也便于验证源代码或工具的更改是否对生成的二进制文件有任何影响。`Reproducible Builds项目`_ 提供了关于这一主题的更多信息。本文档将涵盖可能导致内核构建不可重现的各种原因以及如何避免这些问题。

时间戳
----------

内核在三个地方嵌入了时间戳：

* 通过 `uname()` 和 `/proc/version` 显示的版本字符串。

* 嵌入的 initramfs 文件的时间戳。

* 如果通过 `CONFIG_IKHEADERS` 启用，则嵌入内核或相应模块中的内核头文件的时间戳，这些文件可以通过 `/sys/kernel/kheaders.tar.xz` 访问。

默认情况下，时间戳是当前时间，在 `kheaders` 的情况下则是各个文件的修改时间。必须使用 `KBUILD_BUILD_TIMESTAMP`_ 变量覆盖这个时间戳。如果你是从一个 Git 提交进行构建，你可以使用该提交的日期。
内核不使用 `__DATE__` 和 `__TIME__` 宏，并且如果使用这些宏会启用警告。如果你引入了外部代码并且这些代码使用了这些宏，你必须通过设置 `SOURCE_DATE_EPOCH`_ 环境变量来覆盖它们对应的时间戳。

用户和主机
----------

内核会在 `/proc/version` 中嵌入构建用户的用户名和主机名。这些信息必须使用 `KBUILD_BUILD_USER` 和 `KBUILD_BUILD_HOST`_ 变量覆盖。如果你是从一个 Git 提交进行构建，你可以使用该提交者的地址。

绝对文件名
------------------

当内核在外树目录中构建时，调试信息可能包含源文件的绝对路径。这必须通过在 `KCFLAGS`_ 变量中包含 `-fdebug-prefix-map` 选项来覆盖。
根据所使用的编译器，`__FILE__` 宏在外部构建时也可能扩展为绝对路径。Kbuild 自动使用 `-fmacro-prefix-map` 选项来防止这种情况，如果支持的话。

生成文件在源码包中
----------------------------------

在 `tools/` 子目录下的一些程序的构建过程并不完全支持外树构建。这可能会导致使用 `make rpm-pkg` 进行的后续源码包构建包含生成文件。你应该确保在构建源码包之前源码树是干净的，可以通过运行 `make mrproper` 或 `git clean -d -f -x` 来实现这一点。
模块签名
--------------

如果你启用了 ``CONFIG_MODULE_SIG_ALL``，默认行为是为每次构建生成一个不同的临时密钥，从而导致模块无法重现。然而，将签名密钥包含在源代码中显然会违背模块签名的目的。一种方法是将构建过程分为几个部分，以便不可重现的部分可以作为源代码处理：

1. 生成一个持久的签名密钥。将该密钥的证书添加到内核源代码中。
2. 将 ``CONFIG_SYSTEM_TRUSTED_KEYS`` 符号设置为包含签名密钥的证书，将 ``CONFIG_MODULE_SIG_KEY`` 设置为空字符串，并禁用 ``CONFIG_MODULE_SIG_ALL``。构建内核和模块。
3. 为模块创建分离的签名，并将其作为源代码发布。
4. 进行第二次构建，附加模块签名。它可以重新构建模块或使用步骤 2 的输出。

结构随机化
------------------

如果你启用了 ``CONFIG_RANDSTRUCT``，你需要预先生成随机种子文件 ``scripts/basic/randstruct.seed``，以确保每次构建都使用相同的值。详细信息请参见 ``scripts/gen-randstruct-seed.sh``。

调试信息冲突
--------------------

这不是不可重现性的问题，而是生成文件过于可重现的问题。一旦你设置了所有必要的变量进行可重现构建，vDSO 的调试信息即使对于不同版本的内核也可能完全相同。这可能导致不同内核版本的调试信息包之间的文件冲突。

为了避免这种情况，可以通过在 vDSO 中加入任意字符串（“盐”）来使其在不同内核版本中有所不同。
这是由 Kconfig 符号 `CONFIG_BUILD_SALT` 指定的。

Git
---

未提交的更改或 Git 中不同的提交 ID 也可能导致不同的编译结果。例如，在执行 `git reset HEAD^` 后，即使代码相同，编译过程中生成的 `include/config/kernel.release` 文件也会不同，这最终会导致二进制文件的差异。详情请参阅 `scripts/setlocalversion`。
.. _KBUILD_BUILD_TIMESTAMP: kbuild.html#kbuild-build-timestamp
.. _KBUILD_BUILD_USER 和 KBUILD_BUILD_HOST: kbuild.html#kbuild-build-user-kbuild-build-host
.. _KCFLAGS: kbuild.html#kcflags
.. _前缀映射选项: https://reproducible-builds.org/docs/build-path/
.. _可重现构建项目: https://reproducible-builds.org/
.. _SOURCE_DATE_EPOCH: https://reproducible-builds.org/docs/source-date-epoch/
