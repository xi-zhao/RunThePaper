"""Build a compact, reproducible label and voltage dataset from NIST QFlow lite."""

import _codecs
import argparse
import csv
from hashlib import file_digest, sha256
import io
import json
from pathlib import Path
import pickle
import zipfile

import numpy as np


NIST = "https://data.nist.gov/od/ds/66492819760D3FF6E05324570681BA721894/"
ARCHIVE_BYTES = 913_524_076
MULTIARRAY = np._core.multiarray
PICKLE_CLASSES = {
    ("_codecs", "encode"): _codecs.encode,
    ("numpy", "dtype"): np.dtype,
    ("numpy", "ndarray"): np.ndarray,
    **{(module, name): getattr(MULTIARRAY, name)
       for module in ("numpy.core.multiarray", "numpy._core.multiarray")
       for name in ("_reconstruct", "scalar")},
}


class ArrayReader(pickle.Unpickler):
    def find_class(self, module, name):
        try:
            return PICKLE_CLASSES[module, name]
        except KeyError:
            raise pickle.UnpicklingError(f"Unexpected object class: {module}.{name}") from None


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def read_npy_dict(raw):
    with io.BytesIO(raw) as stream:
        version = np.lib.format.read_magic(stream)
        if version == (1, 0):
            shape, _, dtype = np.lib.format.read_array_header_1_0(stream)
        elif version == (2, 0):
            shape, _, dtype = np.lib.format.read_array_header_2_0(stream)
        else:
            raise ValueError(f"Unsupported NPY version: {version}")
        assert shape == () and dtype == np.dtype(object)
        obj = ArrayReader(stream, encoding="latin1").load()
        assert stream.read(1) == b""
    assert isinstance(obj, np.ndarray) and obj.shape == () and obj.dtype == np.dtype(object)
    x = obj.item()
    assert isinstance(x, dict)
    return x


def read_device(raw):
    x = read_npy_dict(raw)
    assert x["type"] == "V_P_map" and isinstance(x["physics"], dict) and len(x["output"]) == 10_000
    axes = np.stack([x["V_P1_vec"], x["V_P2_vec"]])
    assert axes.shape == (2, 100) and np.all(np.isfinite(axes))
    differences = np.diff(axes, axis=1)
    assert np.all(np.all(differences > 0, axis=1) | np.all(differences < 0, axis=1))
    rows = x["output"]
    assert all(set(row) == {"state", "current", "charge", "sensor"} for row in rows)
    labels = np.array([row["state"] for row in rows])
    assert np.all(np.isin(labels, [-1, 0, 1, 2]))
    return axes, labels.astype(np.int8).reshape(100, 100)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("sample", type=Path)
    p.add_argument("csv", type=Path)
    p.add_argument("out", type=Path)
    p.add_argument("manifest", type=Path)
    args = p.parse_args()

    assert args.archive.stat().st_size == ARCHIVE_BYTES
    control_axes, control = read_device(args.sample.read_bytes())
    with args.csv.open(newline="") as f:
        rows = list(csv.DictReader(f))
    csv_voltages = np.array([[float(r["'V_P1"]), float(r["'V_P2"])] for r in rows])
    control_voltages = np.column_stack([np.repeat(control_axes[0], 100), np.tile(control_axes[1], 100)])
    assert np.array_equal(control_voltages, csv_voltages)
    assert np.array_equal(control.ravel(), [int(r["state"]) for r in rows])

    names, voltages, labels, members = [], [], [], []
    with zipfile.ZipFile(args.archive) as archive:
        infos = sorted(
            (info for info in archive.infolist() if not info.is_dir()
             and info.filename.endswith(".npy") and "__MACOSX" not in info.filename),
            key=lambda info: info.filename,
        )
        assert len(infos) == len({info.filename for info in infos}) == 1001
        for info in infos:
            assert 0 < info.file_size < 10_000_000, info.filename
            raw = archive.read(info)
            axes, states = read_device(raw)
            names.append(info.filename)
            voltages.append(axes)
            labels.append(states)
            members.append(dict(name=info.filename, sha256=sha256(raw).hexdigest(),
                                crc32=f"{info.CRC:08x}", bytes=info.file_size))
            if len(names) % 250 == 0:
                print(f"Read {len(names)} of {len(infos)} devices", flush=True)
    np.savez_compressed(args.out, names=np.asarray(names), axes=np.stack(voltages), labels=np.stack(labels))
    report = dict(archive_url=NIST + "data_qflow_lite.zip", archive_bytes=ARCHIVE_BYTES,
                  archive_sha256=digest(args.archive), labels_sha256=digest(args.out),
                  plos_s2_sha256=digest(args.sample), plos_s3_sha256=digest(args.csv),
                  sample_label_and_coordinate_comparison="all 10000 match",
                  matching_grid_and_label_members=[name for name, v, s in zip(names, voltages, labels)
                                                   if np.array_equal(s, control) and np.array_equal(v, control_axes)],
                  device_count=len(names), label_points=len(names) * 10_000, members=members)
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(report["archive_sha256"], report["matching_grid_and_label_members"], flush=True)


if __name__ == "__main__":
    main()
