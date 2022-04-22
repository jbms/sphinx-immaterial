"""Modifies the sphinx search index.

- object synopses are added

- instead of the list of docnames, there is a list of URLs.  That way we don't
  need to duplicate in JavaScript the logic of determining a URL from a page
  name.

- the unused list of filenames is removed, since it just bloated the index.
"""

import io
from typing import cast, Any, Dict, IO, List, Tuple, Union

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
        docindex_to_docname = {i: docname for docname, i in fn2index.items()}
        synopses = {}
        all_anchors = {}
        for domain_name, domain in self.env.domains.items():
            get_object_synopses = getattr(domain, "get_object_synopses", None)
            if get_object_synopses is not None:
                for key, synopsis in get_object_synopses():
                    synopses.setdefault(key, synopsis or "")
            for (
                name,
                dispname,
                objtype,
                docname,
                anchor,
                priority,
            ) in domain.get_objects():
                synopses.setdefault((docname, anchor), "")

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
                objtype = objtype_entry[1]
                domain = self.env.domains[domain_name]

                docname = docindex_to_docname.get(docindex)

                # Workaround for problems with the `shortanchor` encoding
                # https://github.com/sphinx-doc/sphinx/issues/10380

                # First decode `shortanchor` into the actual anchor based on the
                # full set of `(docname, anchor)` pairs.

                full_name = name_prefix + name

                anchor = shortanchor
                synopsis = synopses.get((docname, anchor))
                if shortanchor == "":
                    # The anchor could either be the actual empty string, or `full_name`.
                    if synopsis is None:
                        # Anchor is probably `full_name`
                        anchor = full_name
                        synopsis = synopses.get((docname, anchor))
                elif shortanchor == "-":
                    # The anchor could either by "-" or `objtype
                    if synopsis is None:
                        anchor = objtype + "-" + full_name
                        synopsis = synopses.get((docname, anchor))

                # Encode `anchor` into a lossless `shortanchor`.
                if anchor == full_name:
                    shortanchor = 0
                elif anchor == objtype + "-" + full_name:
                    shortanchor = 1
                else:
                    shortanchor = anchor

                synopsis = synopsis or ""

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
        return cast(Any, rv)

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
