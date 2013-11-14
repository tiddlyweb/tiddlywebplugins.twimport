def test_compile():
    try:
        import tiddlywebplugins.twimport
        assert True
    except ImportError as exc:
        assert False, exc
