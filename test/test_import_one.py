
from tiddlyweb.config import config
from tiddlyweb.store import Store, NoBagError
from tiddlyweb.model.tiddler import Tiddler
from tiddlyweb.model.bag import Bag
from tiddlywebplugins.twimport import import_one

def setup_module(module):
    module.store = Store(config['server_store'][0],
            config['server_store'][1], {'tiddlyweb.config': config})
    _cleanup(module.store)

def _cleanup(store):
    bag = Bag('testone')
    try:
        store.delete(bag)
    except NoBagError:
        pass # first timer
    store.put(bag)

def test_import_one_wiki():
    import_one('testone', 'test/samples/tiddlers.wiki', store)

    bag = store.get(Bag('testone'))
    assert len(list(store.list_bag_tiddlers(bag))) == 9

def test_import_one_html_wiki():
    import_one('testone', 'test/samples/tiddlers.html', store)

    bag = store.get(Bag('testone'))
    assert len(list(store.list_bag_tiddlers(bag))) == 9 # tiddlers overwritten

def test_import_one_recipe():
    import_one('testone', 'test/samples/alpha/index.html.recipe', store)

    bag = store.get(Bag('testone'))
    assert len(list(store.list_bag_tiddlers(bag))) == 19

def test_import_one_tiddler():
    import_one('testone', 'test/samples/alpha/plugins/bplugin.js', store)

    bag = store.get(Bag('testone'))
    assert len(list(store.list_bag_tiddlers(bag))) == 19 # bplugin already in store

    tiddler = store.get(Tiddler('bplugin', 'testone'))
    assert tiddler.type == 'text/javascript'
    assert tiddler.text == "alert('i am here');"

def test_import_one_wiki_fragment():
    _cleanup(store)
    import_one('testone', 'test/samples/tiddlers.wiki#codeblocked', store)

    bag = store.get(Bag('testone'))
    tiddlers = list(store.list_bag_tiddlers(bag))
    assert len(tiddlers) == 1
    assert tiddlers[0].title == 'codeblocked'

def test_import_one_recipe_fragment():
    _cleanup(store)
    import_one('testone', 'test/samples/alpha/index.html.recipe#Greetings', store)

    bag = store.get(Bag('testone'))
    tiddlers = list(store.list_bag_tiddlers(bag))
    assert len(tiddlers) == 1
    assert tiddlers[0].title == 'Greetings'

def test_import_one_js_meta():
    import_one('testone', 'test/samples/alpha/plugins/metaplugin.js', store)

    tiddler = store.get(Tiddler('metaplugin', 'testone'))

    assert tiddler.title == 'metaplugin'
    assert tiddler.tags == ['alpha', 'beta']

def test_import_one_css_meta():
    import_one('testone', 'test/samples/alpha/fnord.css', store)

    tiddler = store.get(Tiddler('fnord.css', 'testone'))

    assert tiddler.title == 'fnord.css'
    assert tiddler.type == 'text/css'
    assert tiddler.tags == ['alpha', 'beta']

def test_import_one_css_type():
    import_one('testone', 'https://github.com/necolas/normalize.css/raw/master/normalize.css text/css', store)
    tiddler = store.get(Tiddler('normalize.css', 'testone'))

    assert tiddler.title == 'normalize.css'
    assert tiddler.type == 'text/css'
    assert tiddler.tags == []
