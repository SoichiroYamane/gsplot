import pytest
import gsplot as gs


def test_init():
    # Test initializing with default value
    gss = gs.Store()
    assert gss.store == False

    # Test initializing with True
    gss = gs.Store(True)
    assert gss.store == True

    # Test initializing with 1
    gss = gs.Store(1)
    assert gss.store == True

    # Test initializing with invalid value raises ValueError
    with pytest.raises(ValueError):
        gss = gs.Store("invalid")


def test_value_getter():
    gss = gs.Store()
    assert gss.store == False

    gss = gs.Store(True)
    assert gss.store == True

    gss = gs.Store(1)
    assert gss.store == True


def test_value_setter():
    gss = gs.Store()

    # Test setting value to True
    gss.store = True
    assert gss.store == True

    # Test setting value to 1
    gss.store = 1
    assert gss.store == True

    # Test setting value to invalid value raises ValueError
    with pytest.raises(ValueError):
        gss.store = "invalid"


# if __name__ == "__main__":
#     test_init()
#     test_value_getter()
#     test_value_setter()
