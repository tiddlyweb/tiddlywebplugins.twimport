"""
Import tiddlers, Cook recipes,  and TiddlyWikis into TiddlyWeb.

If you wish to use the provided "twimport" twanager command
you must add to twanager_plugins in tiddlywebconfig.py:

    config = {
        'twanager_plugins': ['tiddlywebplugins.twimport'],
    }

twimport has two primary purposes:

    * Using the "twanager twimport" command to import content into a
      running instance.
    * Using the functionality in the plugin to help build instance
      packages using tiddler content stored in many locations.

This latter functionality relies on functionality provided by
"tiddlywebplugins.ibuiler" and uses a modified form of the cook
recipe format. Tiddlers may be referred to with either a local
file path, or a remote URI and have an optional mime type:

    tiddler: <uri> [mime type]

The mime type option is provided to allow setting the mime type
of the stored tiddler. If no type is provided the system will
attempt to determine the mime based on HTTP response headers
or by guessing from the file extension.

If a tiddler uri ends in '.js' it will be processed as a
TiddlyWiki plugin (and, in the absence of a .meta file, get a
systemConfig tag). To avoid this behavior set the mime type
explicitly.

When a tiddler is loaded, the code will look for a meta file
in the same location. This optional file contains meta
information about the tiddler, such as tags, modifier, and
fields. The format is the same as the top section of a .tid
file.
"""

import os

try:
    from urllib2 import urlopen, URLError, HTTPError
    from urllib import splittype
    from urlparse import urljoin, urlparse, urlunparse
except ImportError as exc:
    from urllib.request import urlopen, URLError, HTTPError
    from urllib.parse import splittype, urljoin, urlparse, urlunparse

from html5lib import HTMLParser, treebuilders

from tiddlyweb.model.tiddler import Tiddler, string_to_tags_list
from tiddlyweb.serializer import Serializer
from tiddlyweb.manage import make_command
from tiddlyweb.util import pseudo_binary

from tiddlyweb.fixups import unquote, quote

from tiddlywebplugins.utils import get_store

ACCEPTED_RECIPE_TYPES = ['tiddler', 'plugin', 'recipe']
ACCEPTED_TIDDLER_TYPES = ['js', 'tid', 'tiddler']
COOK_VARIABLES = {
        'TW_TRUNKDIR': 'https://raw.github.com/TiddlyWiki/tiddlywiki/master',
        'TW_ROOT': 'https://raw.github.com/TiddlyWiki/tiddlywiki/master',
}


def init(config):
    """
    Initialize the plugin, establishing twanager commands.
    """

    @make_command()
    def twimport(args):
        """Import tiddlers, recipes, wikis, binary content: <bag> <URI>"""
        bag = args[0]
        urls = args[1:]
        if not bag or not urls:
            raise IndexError('missing args')
        import_list(bag, urls, get_store(config))


def import_list(bag_name, urls, store):
    """
    Import a list of URIs into the named bag.
    """
    for url in urls:
        import_one(bag_name, url, store)


def import_one(bag_name, url, store):
    """
    Import one URI into bag. If the URI has a #fragment it
    will be processed as a TiddlyWiki permaview fragment and
    used to limit the tiddlers that get saved.
    """
    fragments = []
    if '#' in url:
        url, fragment = url.split('#', 1)
        fragments = _parse_fragment(fragment)
    if url.endswith('.recipe'):
        tiddlers = [url_to_tiddler(tiddler_url) for
                tiddler_url in recipe_to_urls(url)]
    elif url.endswith('.wiki') or url.endswith('.html'):
        tiddlers = wiki_to_tiddlers(url)
    else:  # we have a tiddler of some form
        tiddlers = [url_to_tiddler(url)]

    for tiddler in tiddlers:
        if fragments and tiddler.title not in fragments:
            continue
        tiddler.bag = bag_name
        store.put(tiddler)


def recipe_to_urls(url):
    """
    Provided a url or path to a Cook-style recipe, explode the recipe to
    a list of URLs of tiddlers (of various types).
    """
    url, handle = get_url_handle(url)
    return _expand_recipe(handle.read().decode('utf-8', 'replace'), url)


def url_to_tiddler(url):
    """
    Given a url to a tiddlers of some form,
    return a Tiddler object.
    """
    mime_type = None
    if ' ' in url:
        uri, mime_type = url.split(' ', 1)
        if '/' in mime_type:
            url = uri
    url, handle = get_url_handle(url)

    if url.endswith('.js') and not mime_type:
        tiddler = from_plugin(url, handle)
    elif url.endswith('.tid'):
        tiddler = from_tid(url, handle)
    elif url.endswith('.tiddler'):
        tiddler = from_tiddler(handle)
    else:
        # binary tiddler
        tiddler = from_special(url, handle, mime=mime_type)
    return tiddler


def wiki_to_tiddlers(url):
    """
    Retrieve a .wiki or .html as a TiddlyWiki and extract the
    contained tiddlers.
    """
    url, handle = get_url_handle(url)
    return wiki_string_to_tiddlers(handle.read().decode('utf-8', 'replace'))


def wiki_string_to_tiddlers(content):
    """
    Turn a string that is a TiddlyWiki into individual tiddlers.
    """
    parser = HTMLParser(tree=treebuilders.getTreeBuilder('dom'))
    doc = parser.parse(content)
    # minidom will not provide working getElementById without
    # first having a valid document, which means some very specific
    # doctype hooey. So we traverse
    body = doc.getElementsByTagName('body')[0]
    body_divs = body.getElementsByTagName('div')
    is_wiki = False
    for div in body_divs:
        if div.hasAttribute('id') and div.getAttribute('id') == 'storeArea':
            divs = div.getElementsByTagName('div')
            is_wiki = True
            break

    if is_wiki:
        tiddlers = []
        for tiddler_div in divs:
            tiddlers.append(_get_tiddler_from_div(tiddler_div))
        return tiddlers
    else:
        raise ValueError('content not a tiddlywiki 2.x')


def from_plugin(uri, handle):
    """
    Generate a tiddler from a JavaScript (and accompanying meta) file
    If there is no .meta file, title and tags assume default values.
    """
    default_title = _get_title_from_uri(uri)
    default_tags = 'systemConfig'

    meta_uri = '%s.meta' % uri
    try:
        meta_content = _get_url(meta_uri)
    except (HTTPError, URLError, IOError, OSError):
        meta_content = 'title: %s\ntags: %s\n' % (default_title, default_tags)
    try:
        title = [line for line in meta_content.split('\n')
                if line.startswith('title:')][0]
        title = title.split(':', 1)[1].strip()
    except IndexError:
        title = default_title
    tiddler_meta = '\n'.join(line for line in meta_content.split('\n')
            if not line.startswith('title:')).rstrip()
    tiddler_meta = 'type: text/javascript\n%s' % tiddler_meta

    plugin_content = handle.read().decode('utf-8', 'replace')
    tiddler_text = '%s\n\n%s' % (tiddler_meta, plugin_content)

    return _from_text(title, tiddler_text)


def from_special(uri, handle, mime=None):
    """
    Import a binary or pseudo binary tiddler. If a mime is provided,
    set the type of the tiddler to that. Otherwise use the type determined
    by the URL handler. If a meta file is present and has a type, it will
    be used.

    This code is inspired by @bengillies bimport.
    """
    title = _get_title_from_uri(uri)
    if mime:
        content_type = mime
    else:
        content_type = handle.headers['content-type'].split(';')[0]
    data = handle.read()

    meta_uri = '%s.meta' % uri
    try:
        meta_content = _get_url(meta_uri)
        tiddler = _from_text(title, meta_content + '\n\n')
    except (HTTPError, URLError, IOError, OSError):
        tiddler = Tiddler(title)

    if not tiddler.type and content_type:
        tiddler.type = content_type

    if pseudo_binary(tiddler.type):
        data = data.decode('utf-8', 'ignore')

    tiddler.text = data

    return tiddler


def from_tid(uri, handle):
    """
    generates a tiddler from a TiddlyWeb-style .tid file
    """
    title = _get_title_from_uri(uri)
    return _from_text(title, handle.read().decode('utf-8', 'replace'))


def from_tiddler(handle):
    """
    generates a tiddler from a Cook-style .tiddler file
    """
    content = handle.read().decode('utf-8', 'replace')
    content = _escape_brackets(content)

    parser = HTMLParser(tree=treebuilders.getTreeBuilder('dom'))
    dom = parser.parse(content)
    node = dom.getElementsByTagName('div')[0]

    return _get_tiddler_from_div(node)


def _escape_brackets(content):
    """
    escapes angle brackets in tiddler's HTML representation
    """
    open_pre = content.index('<pre>')
    close_pre = content.rindex('</pre>')
    start = content[0:open_pre + 5]
    middle = content[open_pre + 5:close_pre]
    end = content[close_pre:]
    middle = middle.replace('>', '&gt;').replace('<', '&lt;')
    return start + middle + end


def _get_title_from_uri(uri):
    """
    Turn a uri of tiddler into the title of a tiddler,
    by looking at the final segment of the path.
    """
    title = uri.split('/')[-1]
    title = _strip_extension(title)
    title = unquote(title)
    return title


def _strip_extension(title):
    """
    If the title ends with a tiddler extension, then strip
    it off. Otherwise, leave it.
    """
    name, extension = title.rsplit('.', 1)
    if extension in ACCEPTED_TIDDLER_TYPES:
        return name
    else:
        return title


def _expand_recipe(content, url=''):
    """
    Expand a recipe into a list of usable URLs.

    Content is a string, potentially with URL quoted strings.
    """
    urls = []
    for line in content.splitlines():
        line = line.lstrip().rstrip()
        try:
            target_type, target = line.split(':', 1)
        except ValueError:
            continue  # blank line in recipe
        if target_type in ACCEPTED_RECIPE_TYPES:
            target = target.lstrip().rstrip()
            # translate well-known variables
            for name in COOK_VARIABLES:
                target = target.replace('$%s' % name, COOK_VARIABLES[name])
            # Check to see if the target is a URL (has a scheme)
            # if not we want to join it to the current url before
            # carrying on.
            scheme, _ = splittype(target)
            if not scheme:
                if not '%' in target:
                    target = quote(target)
                target = urljoin(url, target)
            if target_type == 'recipe':
                urls.extend(recipe_to_urls(target))
            else:
                urls.append(target)
    return urls


def _get_url(url):
    """
    Load a URL and decode it to unicode.
    """
    content = urlopen(url).read().decode('utf-8', 'replace')
    return content.replace('\r', '')


def _from_text(title, content):
    """
    Generates a tiddler from an RFC822-style string

    This corresponds to TiddlyWeb's text serialization of TiddlerS.
    """
    tiddler = Tiddler(title)
    serializer = Serializer('text')
    serializer.object = tiddler
    serializer.from_string(content)
    return tiddler


def _get_text(nodelist):
    """
    Traverse a list of dom nodes extracting contained text.
    """
    text = ''
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            text = text + node.data
        if node.childNodes:
            text = text + _get_text(node.childNodes)
    return text


def _get_tiddler_from_div(node):
    """
    Create a Tiddler from an HTML div element.
    """
    tiddler = Tiddler(node.getAttribute('title'))
    tiddler.text = _html_decode(_get_text(node.getElementsByTagName('pre')))

    for attr, value in node.attributes.items():
        data = value
        if data and attr != 'tags':
            if attr in (['creator', 'modifier', 'created', 'modified']):
                tiddler.__setattr__(attr, data)
            elif (attr not in ['title', 'changecount'] and
                    not attr.startswith('server.')):
                tiddler.fields[attr] = data
    if not node.attributes.get('modified', None) and tiddler.created:
        tiddler.modified = tiddler.created
    tiddler.tags = string_to_tags_list(node.getAttribute('tags'))

    return tiddler


def get_url_handle(url):
    """
    Open the url using urllib2.urlopen. If the url is a filepath
    transform it into a file url.
    """
    try:
        try:
            try:
                handle = urlopen(url)
            except (URLError, OSError):
                (scheme, netloc, path, params, query,
                        fragment) = urlparse(url)
                path = quote(path)
                newurl = urlunparse((scheme, netloc, path,
                    params, query, fragment))
                handle = urlopen(newurl)
        except ValueError:
            # If ValueError happens again we want it to raise
            url = 'file://' + os.path.abspath(url)
            handle = urlopen(url)
        return url, handle
    except HTTPError as exc:
        raise ValueError('%s: %s' % (exc, url))


def _html_decode(text):
    """
    Decode HTML entities used in TiddlyWiki content into the 'real' things.
    """
    return text.replace('&gt;', '>').replace('&lt;', '<').replace(
            '&amp;', '&').replace('&quot;', '"')


def _parse_fragment(fragment):
    """
    Turn a TiddlyWiki permaview into a list of tiddlers.
    """
    fragment = unquote(fragment)
    return string_to_tags_list(fragment)
