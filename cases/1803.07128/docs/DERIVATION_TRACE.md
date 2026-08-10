# Derivation Trace

## From squeezing to the kernel

For fixed squeezing strength `c`, the printed state has only even photon numbers,

```text
|(c,phi)> = sqrt(sech c) sum_n sqrt((2n)!)/(2^n n!)
             (-exp(i phi) tanh c)^n |2n>.
```

Taking the inner product makes the factorial series a central-binomial generating function. Summing it gives

```text
<(c,phi)|(c,phi')> = sech(c) / sqrt(1-exp(i(phi'-phi)) tanh(c)^2).
```

The multimode product state turns this into a product over input coordinates. Because the overlap is complex, Sec. II.C prescribes its absolute square for a real kernel. The implementation therefore uses

```text
K_R(x,x';c) = product_i sech(c)^2 /
              |1-exp(i(x'_i-x_i)) tanh(c)^2|.
```

An independent 120-even-term Fock sum agrees with the closed form to `8.77e-13`; the test Gram matrix is symmetric and PSD.

## From the feature state to the perceptron

For a two-dimensional input, two compact even-Fock vectors are tensor multiplied. Fig. 6 explicitly restricts the perceptron to the real subspace, so T003 trains on `Re[|(c,x1)> tensor |(c,x2)>]`. Fourteen even terms per mode give 196 real coordinates. The paper's analytic appendix proves linear independence in the infinite-dimensional limit; the numerical check asks whether the declared finite truncation reaches unit training accuracy.

## From printed gates to the variational classifier

Each of the four blocks applies:

1. `BS(u,v)=exp[u(exp(iv)a1†a2-exp(-iv)a1a2†)]`;
2. one displacement per mode;
3. `P(u)=exp(i u x^2/2)` per mode;
4. `V(u)=exp(i u x^3/3)` per mode.

The caption fixes four repetitions and 32 parameters, which implies eight real parameters per block. In an 8-state-per-mode Fock truncation the matrices act on a 64-dimensional joint state. The outputs are the normalized probabilities of `|2,0>` and `|0,2>`. The program differentiates through the matrix exponentials and performs the printed 5000 minibatch steps.

## Trace table

| Formula | Source | Numerical role | Code |
| --- | --- | --- | --- |
| EQ001 | squeezed-state display | Fock coefficients | `model.py::truncated_squeezed_state` |
| EQ002 | Eq. (6) | two-mode feature map | `model.py::real_fock_features` |
| EQ003 | Eqs. (7)--(8) | complex overlap | `model.py::single_mode_overlap` |
| EQ004 | Sec. II.C | real PSD kernel | `model.py::squeezing_kernel` |
| EQ005 | representer theorem/Fig. 5 | SVC decision | `reproduction.py::_run_svm` |
| EQ006 | Fig. 6/Appendix B | Fock perceptron | `reproduction.py::_run_perceptron` |
| EQ007 | Fig. 7(c) gate equations | variational unitary | `reproduction.py::_run_variational` |
| EQ008 | output-normalization display | class probabilities/loss | `reproduction.py::_run_variational` |
