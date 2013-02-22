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

    assert 'https://raw.github.com/TiddlyWiki/tiddlywiki/master/shadows/ColorPalette.tid' in urls
    assert 'https://raw.github.com/TiddlyWiki/tiddlywiki/master/shadows/ViewTemplate.tid' in urls

    # split is required for optional type
    filenames = [os.path.basename(url.split(' ', 1)[0]) for url in urls]
    assert len(filenames) == 10

    assert 'aplugin.js' in filenames
    assert 'bplugin.js' in filenames
    assert 'Welcome.tid' in filenames
    assert 'Greetings.tiddler' in filenames
    assert 'Empty.tiddler' in filenames
    assert 'Hello.tid' in filenames
    assert 'hole.js' in filenames
    assert 'ColorPalette.tid' in filenames
    assert 'ViewTemplate.tid' in filenames
    assert 'normalize.css' in filenames
