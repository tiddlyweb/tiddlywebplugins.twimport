"""
First stab, parsing recipes.
"""
import os

from tiddlywebplugins.twimport import recipe_to_urls

SAMPLE='./test/samples/alpha/index.html.recipe'
URL_SAMPLE='file:' + os.path.abspath(SAMPLE)


def test_parse_recipe_path_or_url():
    urls_path = recipe_to_urls(SAMPLE)
    urls_url = recipe_to_urls(URL_SAMPLE)

    assert urls_path == urls_url

def test_parse_recipe_results():
    urls = recipe_to_urls(SAMPLE)

    assert 'http://svn.tiddlywiki.org/Trunk/core/shadows/ColorPalette.tiddler' in urls
    assert 'http://svn.tiddlywiki.org/Trunk/core/shadows/ViewTemplate.tiddler' in urls

    filenames = [os.path.basename(url) for url in urls]

    assert len(filenames) == 9

    assert 'aplugin.js' in filenames
    assert 'bplugin.js' in filenames
    assert 'Welcome.tid' in filenames
    assert 'Greetings.tiddler' in filenames
    assert 'Empty.tiddler' in filenames
    assert 'Hello.tid' in filenames
    assert 'hole.js' in filenames
    assert 'ColorPalette.tiddler' in filenames
    assert 'ViewTemplate.tiddler' in filenames
