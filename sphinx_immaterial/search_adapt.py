"""Modifies the sphinx search index.

- object synopses are added

- instead of the list of docnames, there is a list of URLs.  That way we don't
  need to duplicate in JavaScript the logic of determining a URL from a page
  name.

- the unused list of filenames is removed, since it just bloated the index.
"""

import io
from typing import cast, Any, Dict, IO, List, Tuple, Union, Optional, Set

import sphinx
import sphinx.search
import sphinx.application
import sphinx.builders.html
import sphinx.util.logging

logger = sphinx.util.logging.getLogger(__name__)


def _get_all_objects(
    env: sphinx.environment.BuildEnvironment,
) -> Set[Tuple[str, str, str, str]]:
    objs = set()
    for domain_name, domain in env.domains.items():
        for (
            name,
            dispname,
            objtype,
            docname,
            anchor,
            priority,
        ) in domain.get_objects():
            objs.add((docname, anchor, domain_name, objtype))
    return objs


def _get_all_synopses(
    env: sphinx.environment.BuildEnvironment,
) -> Dict[Tuple[Optional[str], str], str]:
    synopses: Dict[Tuple[Optional[str], str], str] = {}
    for domain_name, domain in env.domains.items():
        get_object_synopses = getattr(domain, "get_object_synopses", None)
        if get_object_synopses is not None:
            for key, synopsis in get_object_synopses():
                synopses.setdefault(key, synopsis or "")
    return synopses


class IndexBuilder(sphinx.search.IndexBuilder):
    def get_objects(  # type: ignore[override]
        self, fn2index: Dict[str, int]
    ) -> Dict[
        str,
        Union[
            # From sphinx 4.3 onwards the children dict is now a list
            Dict[str, Tuple[int, int, int, Union[int, str]]],
            List[Tuple[int, int, int, Union[int, str], str]],
        ],
    ]:
        rv = super().get_objects(fn2index)
        onames = self._objnames
        docindex_to_docname = {i: docname for docname, i in fn2index.items()}
        all_objs = _get_all_objects(self.env)
        synopses = _get_all_synopses(self.env)

        for prefix, prefix_value in rv.items():
            if prefix:
                name_prefix = prefix + "."
            else:
                name_prefix = ""
            if sphinx.version_info >= (4, 3):
                # From sphinx 4.3 onwards the children dict is now a list
                children = prefix_value
            else:
                children = [
                    (*values, name)  # type: ignore[misc]
                    for name, values in cast(dict, prefix_value).items()
                ]
            for i, (docindex, typeindex, prio, shortanchor, name) in enumerate(
                children
            ):
                objtype_entry = onames[typeindex]
                domain_name = objtype_entry[0]
                objtype = objtype_entry[1]

                docname = docindex_to_docname.get(docindex)

                # Workaround for problems with the `shortanchor` encoding
                # https://github.com/sphinx-doc/sphinx/issues/10380

                # First decode `shortanchor` into the actual anchor based on the
                # full set of `(docname, anchor, domain_name, objtype)` tuples.

                full_name = name_prefix + name

                anchor = shortanchor
                key = (docname, anchor, domain_name, objtype)
                if shortanchor == "":
                    # The anchor could either be the actual empty string, or `full_name`.
                    if key not in all_objs:
                        # Anchor is probably `full_name`
                        anchor = full_name
                elif shortanchor == "-":
                    # The anchor could either by "-" or `objtype+"-"+full_name`
                    if key not in all_objs:
                        anchor = objtype + "-" + full_name

                key = (docname, anchor, domain_name, objtype)
                if key not in all_objs:
                    logger.warning(
                        "Unable to determine anchor for object with docname=%r, domain=%r, objtype=%r, full_name=%r",
                        docname,
                        domain_name,
                        objtype,
                        full_name,
                    )

                synopsis = synopses.get((docname, anchor), "")

                # Encode `anchor` into a lossless `shortanchor`.
                new_shortanchor: Union[int, str]
                if anchor == full_name:
                    new_shortanchor = 0
                elif anchor == objtype + "-" + full_name:
                    new_shortanchor = 1
                else:
                    new_shortanchor = anchor

                if sphinx.version_info >= (4, 3):
                    prefix_value[i] = (  # type: ignore
                        docindex,  # type: ignore
                        typeindex,
                        prio,
                        new_shortanchor,
                        name,
                        synopsis,
                    )
                else:
                    prefix_value[name] = (  # type: ignore
                        docindex,
                        typeindex,
                        prio,
                        new_shortanchor,
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
        self,
        stream: IO,
        format: Any,
    ) -> None:
        if isinstance(format, str):
            format = self.formats[format]
        frozen = format.load(stream)
        # Reconstruct `docnames` and `filenames` from `docurls` since they are
        # expected by `IndexBuilder`.
        builder = self.env.app.builder
        assert isinstance(builder, sphinx.builders.html.StandaloneHTMLBuilder)
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
                filenames.append(str(self.env.doc2path(docname, False)))
        frozen["docnames"] = docnames
        frozen["filenames"] = filenames
        new_data = format.dumps(frozen)
        if isinstance(new_data, str):
            stream = io.StringIO(new_data)
        else:
            stream = io.BytesIO(new_data)
        super().load(stream, format)


def _monkey_patch_index_builder():
    sphinx.search.IndexBuilder = IndexBuilder  # type: ignore[misc]


def setup(app: sphinx.application.Sphinx):
    _monkey_patch_index_builder()
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
