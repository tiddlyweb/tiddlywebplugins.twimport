
from tiddlyweb.config import config
from tiddlyweb.store import Store, NoBagError
from tiddlyweb.model.bag import Bag
from tiddlywebplugins.twimport import import_one

def setup_module(module):
    module.store = Store(config['server_store'][0],
            config['server_store'][1], {'tiddlyweb.config': config})
    bag = Bag('testone')
    try:
        module.store.delete(bag)
    except NoBagError:
        pass # first timer
    module.store.put(bag)

def test_import_one_wiki():
    import_one('testone', 'test/samples/tiddlers.wiki', store)

    bag = store.get(Bag('testone'))
    assert len(bag.list_tiddlers()) == 9

def test_import_one_html_wiki():
    import_one('testone', 'test/samples/tiddlers.html', store)

    bag = store.get(Bag('testone'))
    assert len(bag.list_tiddlers()) == 9 # tiddlers overwritten

def test_import_one_recipe():
    import_one('testone', 'test/samples/alpha/index.html.recipe', store)

    bag = store.get(Bag('testone'))
    assert len(bag.list_tiddlers()) == 18

def test_import_one_tiddler():
    import_one('testone', 'test/samples/alpha/plugins/bplugin.js', store)

    bag = store.get(Bag('testone'))
    assert len(bag.list_tiddlers()) == 18 # bplugin already in store
