# Rerunning the NMQA calculation / 复算方法

Use Python 3.13 and the pinned requirements in the case code directory. The default command in the code README reruns the square field at ten budgets with 50 held-out trials each. It writes a new result directory and reports the maximum naive-to-adaptive budget ratio in the common observed error range. Choose `--field step`, `--field gauss` or `--field parallel2`, `parallel10`, `parallel15`, `parallel50` for other conditions. `--tuning published` uses the parameter pairs used by the published-tuning comparison.

The runner uses frozen parameter pairs from the audit and repeats the held-out evaluation. The original parameter search evaluated 250 candidate pairs against separate training seeds. The selected pairs, geometry, budgets and measurement batches are recorded in the public parameters file. The frozen figure shows the calculated SSIM curves for both tunings. Its six-ion curves are calculations that sample the upstream labels, while the other three fields use simulated Bernoulli outcomes. [Parameters](../code/parameters.json) · [Frozen scalar checks](../outputs/checks/numerical-checks.json)

## Optional six-ion reanalysis

Download the two author assets separately if you want to rerun the ion field or the camera classifier. The commands verify the pinned SHA-256 values and read only numeric arrays from the NPZ. [Camera archive](https://raw.githubusercontent.com/qcl-sydney/nmqa/810268706582fc81ac93733a3dc7660388f44e98/expt_data/ramseydata.zip) · [Published label bank](https://raw.githubusercontent.com/qcl-sydney/nmqa/810268706582fc81ac93733a3dc7660388f44e98/expt_qslam/rf_fulldata_ramsey.npz)

Run these commands in the case's `code` directory after placing the two author files there.

```bash
python scripts/run_reproduction.py --field ion --labels-file rf_fulldata_ramsey.npz
python scripts/reanalyze_camera.py --archive ramseydata.zip \
  --labels-file rf_fulldata_ramsey.npz --output camera-threshold
python -m pip install -r requirements-camera.txt
python scripts/reanalyze_camera.py --archive ramseydata.zip \
  --labels-file rf_fulldata_ramsey.npz --method rf --output camera-rf
```

默认命令复算方形场。用 `--field` 切换几何或每轮测量次数。脚本按冻结的参数对重做留出样本，输出相位图、SSIM 均值与共同误差范围内的预算比。相机复算用上方两个固定版本的作者文件，输出每种分类的逐位一致率和最大相位差。[公开计算代码](../code/README.md)
