from sqlnocturne.safety.native import NativeSafety


def test_native_bridge_is_optional():
    assert isinstance(NativeSafety.available(), bool)
