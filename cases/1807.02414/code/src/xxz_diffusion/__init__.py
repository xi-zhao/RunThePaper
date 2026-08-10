"""Independent root-of-unity XXZ hydrodynamic reproduction."""

__all__ = ["RootOfUnityXXZ", "StationaryState", "build_domain_wall_profiles"]


def __getattr__(name: str):
    """Load public objects lazily so isolated solvers keep minimal dependencies."""

    if name == "build_domain_wall_profiles":
        from .reproduction import build_domain_wall_profiles

        return build_domain_wall_profiles
    if name in {"RootOfUnityXXZ", "StationaryState"}:
        from .tba import RootOfUnityXXZ, StationaryState

        return {"RootOfUnityXXZ": RootOfUnityXXZ, "StationaryState": StationaryState}[name]
    raise AttributeError(name)
