SPDX 许可证标识符：(LGPL-2.1 或 BSD-2-Clause)

构建 libbpf
==========

libelf 和 zlib 是 libbpf 的内部依赖项，因此需要链接到系统上，以便应用程序能够正常工作。
默认使用 pkg-config 来查找 libelf，调用的程序可以通过 PKG_CONFIG 进行覆盖。
如果在构建时不想使用 pkg-config，可以通过设置 NO_PKG_CONFIG=1 在调用 make 时禁用它。
要同时构建静态库 libbpf.a 和共享库 libbpf.so：

.. code-block:: bash

    $ cd src
    $ make

仅在目录 build/ 中构建静态库 libbpf.a，并将它们与 libbpf 头文件一起安装到暂存目录 root/：

.. code-block:: bash

    $ cd src
    $ mkdir build root
    $ BUILD_STATIC_ONLY=y OBJDIR=build DESTDIR=root make install

针对安装在 /build/root/ 的自定义 libelf 依赖项，同时构建静态库 libbpf.a 和共享库 libbpf.so，并将它们与 libbpf 头文件一起安装到构建目录 /build/root/：

.. code-block:: bash

    $ cd src
    $ PKG_CONFIG_PATH=/build/root/lib64/pkgconfig DESTDIR=/build/root make
