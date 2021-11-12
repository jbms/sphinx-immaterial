"""Modifies the sphinx search index.

- object synopses are added

- instead of the list of docnames, there is a list of URLs.  That way we don't
  need to duplicate in JavaScript the logic of determining a URL from a page
  name.

- the unused list of filenames is removed, since it just bloated the index.
"""

import io
from typing import Any, Dict, IO, List, Tuple, Union

import sphinx.search
import sphinx.application


class IndexBuilder(sphinx.search.IndexBuilder):
    def get_objects(
        self, fn2index: Dict[str, int]
    ) -> Dict[
        str,
        Union[
            # From sphinx 4.3 onwards the children dict is now a list
            Dict[str, Tuple[int, int, int, str]],
            List[Tuple[int, int, int, str, str]],
        ],
    ]:
        rv = super().get_objects(fn2index)
        onames = self._objnames
        for prefix, prefix_value in rv.items():
            if prefix:
                name_prefix = prefix + "."
            else:
                name_prefix = ""
            if sphinx.version_info >= (4, 3):
                # From sphinx 4.3 onwards the children dict is now a list
                children = prefix_value
            else:
                children = [(*values, name) for name, values in prefix_value.items()]
            for i, (docindex, typeindex, prio, shortanchor, name) in enumerate(
                children
            ):
                objtype_entry = onames[typeindex]
                domain_name = objtype_entry[0]
                domain = self.env.domains[domain_name]
                synopsis = ""
                get_object_synopsis = getattr(domain, "get_object_synopsis", None)
                if get_object_synopsis:
                    objtype = objtype_entry[1]
                    full_name = name_prefix + name
                    synopsis = get_object_synopsis(objtype, full_name)
                    if synopsis:
                        synopsis = synopsis.strip()
                if sphinx.version_info >= (4, 3):
                    prefix_value[i] = (
                        docindex,
                        typeindex,
                        prio,
                        shortanchor,
                        name,
                        synopsis,
                    )
                else:
                    prefix_value[name] = (
                        docindex,
                        typeindex,
                        prio,
                        shortanchor,
                        synopsis,
                    )
        return rv

    def freeze(self):
        result = super().freeze()

        # filenames are unused
        result.pop("filenames")

        docnames = result.pop("docnames")

        builder = self.env.app.builder
        result.update(docurls=[builder.get_target_uri(docname) for docname in docnames])
        return result

    def load(
        self, stream: IO, format: Any  # pylint: disable=redefined-builtin
    ) -> None:
        if isinstance(format, str):
            format = self.formats[format]
        frozen = format.load(stream)
        # Reconstruct `docnames` and `filenames` from `docurls` since they are
        # expected by `IndexBuilder`.
        builder = self.env.app.builder
        url_to_docname = {
            builder.get_target_uri(docname): docname
            for docname in self.env.all_docs.keys()
        }
        docurls = frozen["docurls"]
        # Note: For documents that have been removed (and are therefore missing
        # from `url_to_docname`), `docnames` and `filenames` will just contain
        # the URL rather than the docname/filename.  However, since these will
        # be pruned anyway it does not hurt.
        docnames = []
        filenames = []
        for url in docurls:
            docname = url_to_docname.get(url, None)
            if docname is None:
                docnames.append(url)
                filenames.append(url)
            else:
                docnames.append(docname)
                filenames.append(self.env.doc2path(docname, False))
        frozen["docnames"] = docnames
        frozen["filenames"] = filenames
        new_data = format.dumps(frozen)
        if isinstance(new_data, str):
            stream = io.StringIO(new_data)
        else:
            stream = io.BytesIO(new_data)
        super().load(stream, format)


def _monkey_patch_index_builder():
    sphinx.search.IndexBuilder = IndexBuilder


def setup(app: sphinx.application.Sphinx):
    _monkey_patch_index_builder()
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
