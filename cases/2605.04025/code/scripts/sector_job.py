"""Run the same physical circuit with a particle-number preserving truncation."""
import generate
import tebd
from sector_tebd import SectorChain

if __name__=="__main__":
    tebd.Chain=SectorChain
    generate.main()
