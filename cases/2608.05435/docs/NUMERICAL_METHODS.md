# Rerun / 复算

Matrix propagation and explicit 100-qubit compilation verify the convolutional QFT. The three-angle 100-qubit circuit has 590 CX gates, and 28 small matrix comparisons agree to 8.17e-16.

Use the [code instructions](../code/README.md). The default stages run into a new directory.

- `generate.py`

The default runner selects its own deterministic 50-, 80- and 100-qubit targets. It reruns the circuit checks without redistributing the published target list.

[Selected numerical results](../outputs/data/overview.json) · [Scientific scope](../outputs/checks/completion_assessment.json)
