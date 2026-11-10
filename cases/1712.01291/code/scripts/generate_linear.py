"""Run linear prediction for Figs. 4–7."""
from pathlib import Path
import json
from linear import SCENARIOS, linear_case

for index, scenario in enumerate(SCENARIOS):
    row = linear_case(index)
    Path(f"results/linear-{index:02d}.json").write_text(json.dumps(row,allow_nan=False)+"\n")
    print("linear", index, scenario[0], "written", flush=True)
