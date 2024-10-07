SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _dvb_ca:

####################
数字电视 CA 设备
####################

数字电视 CA 设备控制条件访问硬件。它可以通过 ``/dev/dvb/adapter?/ca?`` 进行访问。数据类型和 ioctl 定义可以通过在应用程序中包含 ``linux/dvb/ca.h`` 来访问。
.. note::

   在此 API 中有三个未文档化的 ioctl：
   :ref:`CA_GET_MSG`，:ref:`CA_SEND_MSG` 和 :ref:`CA_SET_DESCR`
欢迎提供它们的文档说明。
.. toctree::
    :maxdepth: 1

    ca_data_types
    ca_function_calls
    ca_high_level
