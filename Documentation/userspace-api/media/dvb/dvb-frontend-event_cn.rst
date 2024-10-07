.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later

.. c:type:: dvb_frontend_event

***************
前端事件 (Frontend Events)
***************

.. code-block:: c

     struct dvb_frontend_event {
         fe_status_t status;
         struct dvb_frontend_parameters parameters;
     };
