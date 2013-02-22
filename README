Import tiddlers, Cook recipes, and [TiddlyWikis](http://tiddlywiki.com)
into a [TiddlyWeb](http://tiddlyweb.com) [store](http://tiddlyweb.tiddlyspace.com/store).

If you wish to use the provided `twimport` twanager command
you must add to `twanager_plugins` in `tiddlywebconfig.py`:

```
config = {
    'twanager_plugins': ['tiddlywebplugins.twimport'],
}
```

twimport has two primary purposes:

* Using the `twanager twimport` command to import content into a
  running [instance](http://tiddlyweb.tiddlyspace.com/instance).
* Using the functionality in the plugin to help build instance
  packages (e.g [tiddlywebwiki](https://github.com/tiddlyweb/tiddlywebwiki)
  and [tiddlyspace](https://github.com/tiddlyspace/tiddlyspace))using
  tiddler content stored in many locations.

This latter functionality relies on functionality provided by
[tiddlywebplugins.ibuiler](https://github.com/cdent/tiddlywebplugins.ibuilder)
and uses a modified form of the cook recipe format. Tiddlers
may be referred to with either a local file path, or a remote URI
and have an optional mime type:

```
tiddler: <uri> [mime type]
```

The mime type option is provided to allow setting the mime type
of the stored tiddler. If no type is provided the system will
attempt to determine the type based on HTTP response headers 
or by guessing from the file extension.

If a tiddler uri ends in `.js` it will be processed as a
TiddlyWiki plugin (and, in the absence of a `.meta` file, get a
`systemConfig` tag). To avoid this behavior set the mime type
explicitly.

When a tiddler is loaded, the code will look for a meta file
in the same location. This optional file contains meta
information about the tiddler, such as tags, modifier, and
fields. The format is the same as the top section of a `.tid`
file.
