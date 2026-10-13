"""Select Packed inside each spawned worker, rather than only in its parent.

v1's multiprocessing workers used the full coherent base solver. Those outputs
remain valid full-space calculations, but do not demonstrate packed execution.
"""
import generate_coherent_gs as base
from generate_coherent_packed import Packed

original_job=base.job

def packed_job(args):
    base.CoherentHybrid=Packed
    return original_job(args)

if __name__=='__main__':
    base.job=packed_job
    base.main()
