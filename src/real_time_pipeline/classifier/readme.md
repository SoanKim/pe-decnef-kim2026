# Real-time DecNef Framework

This directory contains the experimental implementation of the 5-day neurofeedback protocol. I implemented and modified this pipeline by utilizing existing open-source frameworks to handle real-time neural decoding and feedback delivery.

### System Architecture
The software infrastructure for this project relies on the integration of two primary open-source tools:
* **Real-time Communication:** The closed-loop feedback and data streaming are managed by the **[pyDecNef](https://github.com/pedromargolles/pyDecNef)** framework.
* **Decoding Logic:** Neural classification is performed using the **[logistic regression classifier](https://github.com/nmningmei/simple_tensorflow_logistic_regression_classifier)** implementation.