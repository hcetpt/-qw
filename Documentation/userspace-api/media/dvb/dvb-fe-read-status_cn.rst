.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _dvb-fe-read-status:

***************************************
查询前端状态和统计信息
***************************************

一旦调用了 :ref:`FE_SET_PROPERTY <FE_GET_PROPERTY>`，前端将运行一个内核线程，该线程会定期检查调谐器锁定状态，并提供信号质量的统计信息。
可以使用 :ref:`FE_READ_STATUS` 查询前端调谐器的锁定状态。
信号统计信息通过 :ref:`FE_GET_PROPERTY` 提供。
.. note::

   大多数统计信息需要解调器完全锁定（例如，设置 :c:type:`FE_HAS_LOCK <fe_status>` 位）。更多详细信息请参见 :ref:`前端统计指标 <frontend-stat-properties>`。
