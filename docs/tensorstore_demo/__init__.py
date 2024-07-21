"""Demo file for Python API documentation generation.

Some of the docstrings have unusual syntax because they match the output from
pybind11.
"""

from __future__ import annotations
import typing

from ._tensorstore import *  # noqa: F403

# fmt: off


class Dim():
    """1-d index interval with optionally-implicit bounds and dimension label.

    Examples:

        >>> ts.Dim('x')
        Dim(label="x")
        >>> ts.Dim(inclusive_min=3, exclusive_max=10, label='x')
        Dim(inclusive_min=3, exclusive_max=10, label="x")

    See also:
      :py:obj:`IndexDomain`

    Group:
      Indexing
    """
    def __init__(self, *args, **kwargs) -> None:
        """__init__(*args, **kwargs)
Overloaded function.

1. __init__(self: tensorstore_demo.Dim, label: Optional[str] = None, *, implicit_lower: bool = True, implicit_upper: bool = True) -> None


Constructs an unbounded interval ``(-inf, +inf)``.

Args:
  label: Dimension label.
  implicit_lower: Indicates whether the lower bound is
    implicit.
  implicit_upper: Indicates whether the upper bound is
    implicit.

Examples:

    >>> x = ts.Dim()
    >>> print(x)
    (-inf*, +inf*)
    >>> x.finite
    False

    >>> x = ts.Dim("x", implicit_upper=False)
    >>> print(x)
    "x": (-inf*, +inf)
    >>> x.finite
    False

Overload:
  unbounded


2. __init__(self: tensorstore_demo.Dim, size: Optional[int], label: Optional[str] = None, *, inclusive_min: Optional[int] = None, implicit_lower: bool = False, implicit_upper: Optional[bool] = None) -> None


Constructs a sized interval ``[inclusive_min, inclusive_min+size)``.

Args:
  size: Size of the interval.
  label: Dimension label.
  inclusive_min: Inclusive lower bound.  Defaults to :python:`0`.
  implicit_lower: Indicates whether the lower bound is
    implicit.
  implicit_upper: Indicates whether the upper bound is
    implicit.  Defaults to :python:`False` if
    :python:`size` is specified, otherwise :python:`True`.

Examples:

    >>> x = ts.Dim(10)
    >>> print(x)
    [0, 10)
    >>> print(ts.Dim(inclusive_min=5, size=10))
    [5, 15)

Overload:
  size


3. __init__(self: tensorstore_demo.Dim, inclusive_min: Optional[int] = -inf, exclusive_max: Optional[int] = +inf, *, label: Optional[str] = None, implicit_lower: Optional[bool] = None, implicit_upper: Optional[bool] = None) -> None


Constructs a half-open interval ``[inclusive_min, exclusive_max)``.

Args:
  inclusive_min: Inclusive lower bound.
  exclusive_max: Exclusive upper bound.
  label: Dimension label.
  implicit_lower: Indicates whether the lower bound is
    implicit.  Defaults to :python:`False` if
    ``inclusive_min`` is specified, otherwise :python:`True`.
  implicit_upper: Indicates whether the upper bound is
    implicit.  Defaults to :python:`False` if
    ``exclusive_max`` is specified, otherwise :python:`True`.

Examples:

    >>> x = ts.Dim(5, 10)
    >>> x
    Dim(inclusive_min=5, exclusive_max=10)
    >>> print(x)
    [5, 10)

Overload:
  exclusive_max


4. __init__(self: tensorstore_demo.Dim, *, inclusive_min: Optional[int] = -inf, inclusive_max: Optional[int] = +inf, label: Optional[str] = None, implicit_lower: Optional[bool] = None, implicit_upper: Optional[bool] = None) -> None


Constructs a closed interval ``[inclusive_min, inclusive_max]``.

Args:
  inclusive_min: Inclusive lower bound.
  inclusive_max: Inclusive upper bound.
  label: Dimension label.
  implicit_lower: Indicates whether the lower bound is
    implicit.  Defaults to :python:`False` if
    ``inclusive_min`` is specified, otherwise :python:`True`.
  implicit_upper: Indicates whether the upper bound is
    implicit.  Defaults to :python:`False` if
    ``exclusive_max`` is specified, otherwise :python:`True`.

Examples:

    >>> x = ts.Dim(inclusive_min=5, inclusive_max=10)
    >>> x
    Dim(inclusive_min=5, exclusive_max=11)
    >>> print(x)
    [5, 11)

Overload:
  inclusive_max
"""
    @property
    def exclusive_max(self) -> int:
        """Exclusive upper bound of the interval.

        Equal to :python:`self.inclusive_max + 1`.  If the interval is unbounded above,
        equal to the special value of ``+inf+1``.

        Example:

            >>> ts.Dim(inclusive_min=5, inclusive_max=10).exclusive_max
            11
            >>> ts.Dim(exclusive_max=5).exclusive_max
            5
            >>> ts.Dim().exclusive_max
            4611686018427387904

        Group:
          Accessors


        """
    @property
    def inclusive_min(self) -> int:
        """Inclusive lower bound of the interval.

        Equal to :python:`self.exclusive_min + 1`.  If the interval is unbounded below,
        equal to the special value of ``-inf``.

        Example:

            >>> ts.Dim(5).inclusive_min
            0
            >>> ts.Dim(inclusive_min=5, inclusive_max=10).inclusive_min
            5
            >>> ts.Dim().inclusive_min
            -4611686018427387903

        Group:
          Accessors


        """
    @property
    def label(self) -> str:
        """Dimension label, or the empty string to indicate an unlabeled dimension.

        Example:

            >>> ts.Dim().label
            ''
            >>> ts.Dim(label='x').label
            'x'

        Group:
          Accessors


        """
    @label.setter
    def label(self, arg1: str) -> None:
        """Dimension label, or the empty string to indicate an unlabeled dimension.

        Example:

            >>> ts.Dim().label
            ''
            >>> ts.Dim(label='x').label
            'x'

        Group:
          Accessors
        """
    @property
    def size(self) -> int:
        """Size of the interval.

        Equal to :python:`self.exclusive_max - self.inclusive_min`.

        Example:

            >>> ts.Dim(5).size
            5
            >>> ts.Dim(inclusive_min=3, inclusive_max=7).size
            5
            >>> ts.Dim().size
            9223372036854775807

        Note:

          If the interval is unbounded below or above
          (i.e. :python:`self.finite == False`), this value it not particularly
          meaningful.

        Group:
          Accessors


        """
    size_alias = size

    __hash__ = None
    pass
class DimExpression():
    """Specifies an advanced indexing operation.

    Dimension expressions permit indexing using
    dimension labels, and also support additional operations
    that cannot be performed with plain NumPy indexing.

    Group:
      Indexing

    Operations
    ==========
    """
    class _Label():
        def __getitem__(self, *args, **kwargs) -> None:
            """__getitem__(self: tensorstore_demo.DimExpression._Label, labels: Union[str, Sequence[str]]) -> tensorstore_demo.DimExpression


            Sets (or changes) the labels of the selected dimensions.

            Examples:

                >>> ts.IndexTransform(3)[ts.d[0].label['x']]
                Rank 3 -> 3 index space transform:
                  Input domain:
                    0: (-inf*, +inf*) "x"
                    1: (-inf*, +inf*)
                    2: (-inf*, +inf*)
                  Output index maps:
                    out[0] = 0 + 1 * in[0]
                    out[1] = 0 + 1 * in[1]
                    out[2] = 0 + 1 * in[2]
                >>> ts.IndexTransform(3)[ts.d[0, 2].label['x', 'z']]
                Rank 3 -> 3 index space transform:
                  Input domain:
                    0: (-inf*, +inf*) "x"
                    1: (-inf*, +inf*)
                    2: (-inf*, +inf*) "z"
                  Output index maps:
                    out[0] = 0 + 1 * in[0]
                    out[1] = 0 + 1 * in[1]
                    out[2] = 0 + 1 * in[2]
                >>> ts.IndexTransform(3)[ts.d[:].label['x', 'y', 'z']]
                Rank 3 -> 3 index space transform:
                  Input domain:
                    0: (-inf*, +inf*) "x"
                    1: (-inf*, +inf*) "y"
                    2: (-inf*, +inf*) "z"
                  Output index maps:
                    out[0] = 0 + 1 * in[0]
                    out[1] = 0 + 1 * in[1]
                    out[2] = 0 + 1 * in[2]
                >>> ts.IndexTransform(3)[ts.d[0, 1].label['x', 'y'].translate_by[2]]
                Rank 3 -> 3 index space transform:
                  Input domain:
                    0: (-inf*, +inf*) "x"
                    1: (-inf*, +inf*) "y"
                    2: (-inf*, +inf*)
                  Output index maps:
                    out[0] = -2 + 1 * in[0]
                    out[1] = -2 + 1 * in[1]
                    out[2] = 0 + 1 * in[2]

            The new dimension selection is the same as the prior dimension selection.

            Args:
              labels: Dimension labels for each selected dimension.

            Returns:
              Dimension expression with the label operation added.

            Raises:
              IndexError: If the number of labels does not match the number of selected
                dimensions, or if the resultant domain would have duplicate labels.

            Group:
              Operations
            """
        __iter__ = None
        pass
    class _TranslateTo():
        def __getitem__(self, *args, **kwargs) -> None:
            """__getitem__(self: tensorstore_demo.DimExpression._TranslateTo, origins: Union[Sequence[Optional[int]], Optional[int]]) -> tensorstore_demo.DimExpression


            Translates the domains of the selected input dimensions to the specified
            origins without affecting the output range.

            Examples:

               >>> transform = ts.IndexTransform(input_shape=[4, 5, 6],
               ...                               input_labels=['x', 'y', 'z'])
               >>> transform[ts.d['x', 'y'].translate_to[10, 20]]
               Rank 3 -> 3 index space transform:
                 Input domain:
                   0: [10, 14) "x"
                   1: [20, 25) "y"
                   2: [0, 6) "z"
                 Output index maps:
                   out[0] = -10 + 1 * in[0]
                   out[1] = -20 + 1 * in[1]
                   out[2] = 0 + 1 * in[2]
               >>> transform[ts.d['x', 'y'].translate_to[10, None]]
               Rank 3 -> 3 index space transform:
                 Input domain:
                   0: [10, 14) "x"
                   1: [0, 5) "y"
                   2: [0, 6) "z"
                 Output index maps:
                   out[0] = -10 + 1 * in[0]
                   out[1] = 0 + 1 * in[1]
                   out[2] = 0 + 1 * in[2]
               >>> transform[ts.d['x', 'y'].translate_to[10]]
               Rank 3 -> 3 index space transform:
                 Input domain:
                   0: [10, 14) "x"
                   1: [10, 15) "y"
                   2: [0, 6) "z"
                 Output index maps:
                   out[0] = -10 + 1 * in[0]
                   out[1] = -10 + 1 * in[1]
                   out[2] = 0 + 1 * in[2]

            The new dimension selection is the same as the prior dimension selection.

            Args:

              origins: The new origins for each of the selected dimensions.  May also be a
                scalar, e.g. :python:`5`, in which case the same origin is used for all
                selected dimensions.  If :python:`None` is specified for a given dimension,
                the origin of that dimension remains unchanged.

            Returns:
              Dimension expression with the translation operation added.

            Raises:

              IndexError:
                If the number origins does not match the number of selected dimensions.

              IndexError:
                If any of the selected dimensions has a lower bound of :python:`-inf`.

            Group:
              Operations
            """
        __iter__ = None
        pass
    class _Vindex():
        def __getitem__(self, *args, **kwargs) -> None:
            """__getitem__(self: tensorstore_demo.DimExpression._Vindex, indices: typing.Any) -> tensorstore_demo.DimExpression


            Applies a NumPy-style indexing operation with vectorized indexing semantics.

            This is similar to :py:obj:`DimExpression.__getitem__`, but differs in that if
            :python:`indices` specifies any array indexing terms, the broadcasted array
            dimensions are unconditionally added as the first dimensions of the result
            domain:

            Examples:

               >>> transform = ts.IndexTransform(input_labels=['x', 'y', 'z'])
               >>> transform[ts.d['y', 'z'].vindex[[1, 2, 3], [4, 5, 6]]]
               Rank 2 -> 3 index space transform:
                 Input domain:
                   0: [0, 3)
                   1: (-inf*, +inf*) "x"
                 Output index maps:
                   out[0] = 0 + 1 * in[1]
                   out[1] = 0 + 1 * bounded((-inf, +inf), array(in)), where array =
                     {{1}, {2}, {3}}
                   out[2] = 0 + 1 * bounded((-inf, +inf), array(in)), where array =
                     {{4}, {5}, {6}}

            Returns:
              Dimension expression with the indexing operation added.

            Group:
              Operations
            """
        __iter__ = None
        pass
    def __getitem__(self, *args, **kwargs) -> None:
        """__getitem__(self: tensorstore_demo.DimExpression, indices: typing.Any) -> tensorstore_demo.DimExpression


        Applies a NumPy-style indexing operation with default index array semantics.

        When using NumPy-style indexing with a dimension expression, all selected
        dimensions must be consumed by a term of the indexing spec; there is no implicit
        addition of an `Ellipsis` term to consume any remaining dimensions.

        Returns:
          Dimension expression with the indexing operation added.

        Group:
          Operations

        Examples
        ========

        Integer indexing
        ----------------

           >>> transform = ts.IndexTransform(input_labels=['x', 'y', 'z'])
           >>> transform[ts.d['x'][5]]
           Rank 2 -> 3 index space transform:
             Input domain:
               0: (-inf*, +inf*) "y"
               1: (-inf*, +inf*) "z"
             Output index maps:
               out[0] = 5
               out[1] = 0 + 1 * in[0]
               out[2] = 0 + 1 * in[1]
           >>> transform[ts.d['x', 'z'][5, 6]]
           Rank 1 -> 3 index space transform:
             Input domain:
               0: (-inf*, +inf*) "y"
             Output index maps:
               out[0] = 5
               out[1] = 0 + 1 * in[0]
               out[2] = 6

        A single scalar index term applies to all selected dimensions:

           >>> transform[ts.d['x', 'y'][5]]
           Rank 1 -> 3 index space transform:
             Input domain:
               0: (-inf*, +inf*) "z"
             Output index maps:
               out[0] = 5
               out[1] = 5
               out[2] = 0 + 1 * in[0]

        Interval indexing
        -----------------

           >>> transform = ts.IndexTransform(input_labels=['x', 'y', 'z'])
           >>> transform[ts.d['x'][5:10]]
           Rank 3 -> 3 index space transform:
             Input domain:
               0: [5, 10) "x"
               1: (-inf*, +inf*) "y"
               2: (-inf*, +inf*) "z"
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[1]
               out[2] = 0 + 1 * in[2]
           >>> transform[ts.d['x', 'z'][5:10, 20:30]]
           Rank 3 -> 3 index space transform:
             Input domain:
               0: [5, 10) "x"
               1: (-inf*, +inf*) "y"
               2: [20, 30) "z"
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[1]
               out[2] = 0 + 1 * in[2]

        As an extension, TensorStore allows the ``start``, ``stop``, and ``step``
        :py:obj:`python:slice` terms to be vectors rather than scalars:

           >>> transform[ts.d['x', 'z'][[5, 20]:[10, 30]]]
           Rank 3 -> 3 index space transform:
             Input domain:
               0: [5, 10) "x"
               1: (-inf*, +inf*) "y"
               2: [20, 30) "z"
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[1]
               out[2] = 0 + 1 * in[2]
           >>> transform[ts.d['x', 'z'][[5, 20]:30]]
           Rank 3 -> 3 index space transform:
             Input domain:
               0: [5, 30) "x"
               1: (-inf*, +inf*) "y"
               2: [20, 30) "z"
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[1]
               out[2] = 0 + 1 * in[2]

        As with integer indexing, a single scalar slice applies to all selected
        dimensions:

           >>> transform[ts.d['x', 'z'][5:30]]
           Rank 3 -> 3 index space transform:
             Input domain:
               0: [5, 30) "x"
               1: (-inf*, +inf*) "y"
               2: [5, 30) "z"
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[1]
               out[2] = 0 + 1 * in[2]

        Adding singleton dimensions
        ---------------------------

        Specifying a value of ``newaxis`` (equal to `None`) adds a new
        dummy/singleton dimension with implicit bounds
        :math:`[0, 1)`:

           >>> transform = ts.IndexTransform(input_labels=['x', 'y'])
           >>> transform[ts.d[1][ts.newaxis]]
           Rank 3 -> 2 index space transform:
             Input domain:
               0: (-inf*, +inf*) "x"
               1: [0*, 1*)
               2: (-inf*, +inf*) "y"
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[2]
           >>> transform[ts.d[0, -1][ts.newaxis, ts.newaxis]]
           Rank 4 -> 2 index space transform:
             Input domain:
               0: [0*, 1*)
               1: (-inf*, +inf*) "x"
               2: (-inf*, +inf*) "y"
               3: [0*, 1*)
             Output index maps:
               out[0] = 0 + 1 * in[1]
               out[1] = 0 + 1 * in[2]

        As with integer indexing, if only a single :python:`ts.newaxis` term is
        specified, it applies to all selected dimensions:

           >>> transform[ts.d[0, -1][ts.newaxis]]
           Rank 4 -> 2 index space transform:
             Input domain:
               0: [0*, 1*)
               1: (-inf*, +inf*) "x"
               2: (-inf*, +inf*) "y"
               3: [0*, 1*)
             Output index maps:
               out[0] = 0 + 1 * in[1]
               out[1] = 0 + 1 * in[2]

        ``newaxis`` terms are only permitted in the first operation of a
        dimension expression, since in subsequent operations all dimensions of the
        dimension selection necessarily refer to existing dimensions:

        .. admonition:: Error
           :class: failure

           >>> transform[ts.d[0, 1].translate_by[5][ts.newaxis]]
           Traceback (most recent call last):
               ...
           IndexError: tensorstore_demo.newaxis (`None`) not valid in chained indexing operations

        It is also an error to use ``newaxis`` with dimensions specified by
        label:

        .. admonition:: Error
           :class: failure

           >>> transform[ts.d['x'][ts.newaxis]]
           Traceback (most recent call last):
               ...
           IndexError: New dimensions cannot be specified by label

        Ellipsis
        --------

        Specifying the special `Ellipsis` value (:python:`...`) is equivalent to
        specifying as many full slices :python:`:` as needed to consume the remaining
        selected dimensions not consumed by other indexing terms:

            >>> transform = ts.IndexTransform(input_rank=4)
            >>> transform[ts.d[:][1, ..., 5].translate_by[3]]
            Rank 2 -> 4 index space transform:
              Input domain:
                0: (-inf*, +inf*)
                1: (-inf*, +inf*)
              Output index maps:
                out[0] = 1
                out[1] = -3 + 1 * in[0]
                out[2] = -3 + 1 * in[1]
                out[3] = 5

        An indexing spec consisting solely of an `Ellipsis` term has no effect:

           >>> transform[ts.d[:][...]]
           Rank 4 -> 4 index space transform:
             Input domain:
               0: (-inf*, +inf*)
               1: (-inf*, +inf*)
               2: (-inf*, +inf*)
               3: (-inf*, +inf*)
             Output index maps:
               out[0] = 0 + 1 * in[0]
               out[1] = 0 + 1 * in[1]
               out[2] = 0 + 1 * in[2]
               out[3] = 0 + 1 * in[3]

        Integer array indexing
        ----------------------

        Specifying an ``array_like`` *index array* of integer values selects the
        coordinates given by the elements of the array of the selected dimension:

            >>> x = ts.array([[1, 2, 3], [4, 5, 6]], dtype=ts.int32)
            >>> x = x[ts.d[:].label['x', 'y']]
            >>> x[ts.d['y'][[1, 1, 0]]]
            TensorStore({
              'array': [[2, 2, 1], [5, 5, 4]],
              'context': {'data_copy_concurrency': {}},
              'driver': 'array',
              'dtype': 'int32',
              'transform': {
                'input_exclusive_max': [2, 3],
                'input_inclusive_min': [0, 0],
                'input_labels': ['x', ''],
              },
            })

        As in the example above, if only a single
        index array term is specified, the dimensions of the index array are added to
        the result domain in place of the selected dimension, consistent with
        direct NumPy-style indexing in the default
        index array mode.

        However, when using NumPy-style indexing with a dimension expression, if more
        than one index array term is specified, the broadcast dimensions of the index
        arrays are always added to the beginning of the result domain, i.e. exactly the
        behavior of :py:obj:`DimExpression.vindex`.  Unlike with direct NumPy-style
        indexing (not with a dimension expression), the behavior does not depend on
        whether the index array terms apply to consecutive dimensions, since consecutive
        dimensions are not well-defined for dimension expressions:

            >>> x = ts.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]], dtype=ts.int32)
            >>> x = x[ts.d[:].label['x', 'y', 'z']]
            >>> x[ts.d['z', 'y'][[1, 0], [1, 1]]]
            TensorStore({
              'array': [[4, 3], [8, 7]],
              'context': {'data_copy_concurrency': {}},
              'driver': 'array',
              'dtype': 'int32',
              'transform': {
                'input_exclusive_max': [2, 2],
                'input_inclusive_min': [0, 0],
                'input_labels': ['x', ''],
              },
            })

        Boolean array indexing
        ----------------------

        Specifying an ``array_like`` of `bool` values is equivalent to
        specifying a sequence of integer index arrays containing the
        coordinates of `True` values (in C order), e.g. as obtained from
        ``numpy.nonzero``:

        Specifying a 1-d `bool` array is equivalent to a single index array of the
        non-zero coordinates:

            >>> x = ts.array([[1, 2, 3], [4, 5, 6]], dtype=ts.int32)
            >>> x = x[ts.d[:].label['x', 'y']]
            >>> x[ts.d['y'][[False, True, True]]]
            TensorStore({
              'array': [[2, 3], [5, 6]],
              'context': {'data_copy_concurrency': {}},
              'driver': 'array',
              'dtype': 'int32',
              'transform': {
                'input_exclusive_max': [2, 2],
                'input_inclusive_min': [0, 0],
                'input_labels': ['x', ''],
              },
            })

        Equivalently, using an index array:

            >>> x[ts.d['y'][[1, 2]]]
            TensorStore({
              'array': [[2, 3], [5, 6]],
              'context': {'data_copy_concurrency': {}},
              'driver': 'array',
              'dtype': 'int32',
              'transform': {
                'input_exclusive_max': [2, 2],
                'input_inclusive_min': [0, 0],
                'input_labels': ['x', ''],
              },
            })

        More generally, specifying an ``n``-dimensional `bool` array is equivalent to
        specifying ``n`` 1-dimensional index arrays, where the ``i``\\ th index array specifies
        the ``i``\\ th coordinate of the `True` values:

            >>> x = ts.array([[[1, 2, 3], [4, 5, 6]], [[7, 8, 9], [10, 11, 12]]],
            ...              dtype=ts.int32)
            >>> x = x[ts.d[:].label['x', 'y', 'z']]
            >>> x[ts.d['x', 'z'][[[True, False, False], [True, True, False]]]]
            TensorStore({
              'array': [[1, 4], [7, 10], [8, 11]],
              'context': {'data_copy_concurrency': {}},
              'driver': 'array',
              'dtype': 'int32',
              'transform': {
                'input_exclusive_max': [3, 2],
                'input_inclusive_min': [0, 0],
                'input_labels': ['', 'y'],
              },
            })

        Equivalently, using an index array:

            >>> x[ts.d['x', 'z'][[0, 1, 1], [0, 0, 1]]]
            TensorStore({
              'array': [[1, 4], [7, 10], [8, 11]],
              'context': {'data_copy_concurrency': {}},
              'driver': 'array',
              'dtype': 'int32',
              'transform': {
                'input_exclusive_max': [3, 2],
                'input_inclusive_min': [0, 0],
                'input_labels': ['', 'y'],
              },
            })

        Note that as with integer array indexing, when using NumPy-styling indexing with
        a dimension expression, if boolean arrays are applied to more than one selected
        dimension, the added dimension corresponding to the `True` values is always
        added to the beginning of the result domain, i.e. exactly the behavior of
        :py:obj:`DimExpression.vindex`.

        """
    @property
    def diagonal(self) -> DimExpression:
        """Extracts the diagonal of the selected dimensions.

        The selection dimensions are removed from the resultant index space, and a new
        dimension corresponding to the diagonal is added as the first dimension, with an
        input domain equal to the intersection of the input domains of the selection
        dimensions.  The new dimension selection is equal to :python:`ts.d[0]`,
        corresponding to the newly added diagonal dimension.

        The lower and upper bounds of the new diagonal dimension are
        implicit<implicit if, and only if, the lower or upper bounds,
        respectively, of every selected dimension are implicit.

        Examples:

            >>> transform = ts.IndexTransform(input_shape=[2, 3],
            ...                               input_labels=["x", "y"])
            >>> transform[ts.d['x', 'y'].diagonal]
            Rank 1 -> 2 index space transform:
              Input domain:
                0: [0, 2)
              Output index maps:
                out[0] = 0 + 1 * in[0]
                out[1] = 0 + 1 * in[0]
            >>> transform = ts.IndexTransform(3)
            >>> transform[ts.d[0, 2].diagonal]
            Rank 2 -> 3 index space transform:
              Input domain:
                0: (-inf*, +inf*)
                1: (-inf*, +inf*)
              Output index maps:
                out[0] = 0 + 1 * in[0]
                out[1] = 0 + 1 * in[1]
                out[2] = 0 + 1 * in[0]

        Note:

          If zero dimensions are selected, :py:obj:`.diagonal` simply results in a new singleton
          dimension as the first dimension, equivalent to :python:`[ts.newaxis]`:

          >>> transform = ts.IndexTransform(1)
          >>> transform[ts.d[()].diagonal]
          Rank 2 -> 1 index space transform:
            Input domain:
              0: (-inf*, +inf*)
              1: (-inf*, +inf*)
            Output index maps:
              out[0] = 0 + 1 * in[1]

          If only one dimension is selected, :py:obj:`.diagonal` is equivalent to
          :python:`.label[''].transpose[0]`:

          >>> transform = ts.IndexTransform(input_labels=['x', 'y'])
          >>> transform[ts.d[1].diagonal]
          Rank 2 -> 2 index space transform:
            Input domain:
              0: (-inf*, +inf*)
              1: (-inf*, +inf*) "x"
            Output index maps:
              out[0] = 0 + 1 * in[1]
              out[1] = 0 + 1 * in[0]

        Group:
          Operations

        """
    @property
    def label(self) -> DimExpression._Label:
        pass
    @property
    def translate_to(self) -> DimExpression._TranslateTo:
        pass
    @property
    def vindex(self) -> DimExpression._Vindex:
        pass
    __iter__ = None
    pass
class IndexDomain():
    """Domain (including bounds and optional dimension labels) of an N-dimensional index space.

    Logically, an :py:class:`.IndexDomain` is the cartesian product of a sequence of :py:obj:`.Dim` objects.

    Note:

       Index domains are immutable, but dimension expressions may be applied
       using :py:obj:`.__getitem__(expr)` to obtain a modified domain.

    Group:
      Indexing

    """
    def __init__(self, *args, **kwargs) -> None:
        """__init__(*args, **kwargs)
Overloaded function.

1. __init__(self: tensorstore_demo.IndexDomain, rank: Optional[int] = None, *, inclusive_min: Optional[Sequence[int]] = None, implicit_lower_bounds: Optional[Sequence[bool]] = None, exclusive_max: Optional[Sequence[int]] = None, inclusive_max: Optional[Sequence[int]] = None, shape: Optional[Sequence[int]] = None, implicit_upper_bounds: Optional[Sequence[bool]] = None, labels: Optional[Sequence[Optional[str]]] = None) -> None


Constructs an index domain from component vectors.

Args:
  rank: Number of dimensions.  Only required if no other parameter is specified.
  inclusive_min: Inclusive lower bounds for each dimension.  If not specified,
      defaults to all zero if ``shape`` is specified, otherwise unbounded.
  implicit_lower_bounds: Indicates whether each lower bound is
      implicit or explicit.  Defaults to all explicit if
      ``inclusive_min`` or ``shape`` is specified, otherwise defaults to all
      implicit.
  exclusive_max: Exclusive upper bounds for each dimension.  At most one of
      ``exclusive_max``, ``inclusive_max``, and ``shape`` may be specified.
  inclusive_max: Inclusive upper bounds for each dimension.
  shape: Size for each dimension.
  implicit_upper_bounds: Indicates whether each upper bound is
      implicit or explicit.  Defaults to all explicit if
      ``exclusive_max``, ``inclusive_max``, or ``shape`` is specified, otherwise
      defaults to all implicit.
  labels: Dimension labels.  Defaults to all unlabeled.

Examples:

    >>> ts.IndexDomain(rank=5)
    { (-inf*, +inf*), (-inf*, +inf*), (-inf*, +inf*), (-inf*, +inf*), (-inf*, +inf*) }
    >>> ts.IndexDomain(shape=[2, 3])
    { [0, 2), [0, 3) }

Overload:
  components


2. __init__(self: tensorstore_demo.IndexDomain, dimensions: Sequence[tensorstore_demo.Dim]) -> None


Constructs an index domain from a :py:class`.Dim` sequence.

Args:
  dimensions: :py:obj:`Sequence<python:typing.Sequence>` of :py:class`.Dim` objects.

Examples:

    >>> ts.IndexDomain([ts.Dim(5), ts.Dim(6, label='y')])
    { [0, 5), "y": [0, 6) }

Overload:
  dimensions


3. __init__(self: tensorstore_demo.IndexDomain, *, json: Any) -> None


Constructs an index domain from its JSON representation.

Examples:

    >>> ts.IndexDomain(
    ...     json={
    ...         "inclusive_min": ["-inf", 7, ["-inf"], [8]],
    ...         "exclusive_max": ["+inf", 10, ["+inf"], [17]],
    ...         "labels": ["x", "y", "z", ""]
    ...     })
    { "x": (-inf, +inf), "y": [7, 10), "z": (-inf*, +inf*), [8*, 17*) }

Overload:
  json
"""
    def __eq__(self, *args, **kwargs) -> None:
        """__eq__(self: tensorstore_demo.IndexDomain, arg0: tensorstore_demo.IndexDomain) -> bool
        """
    def __getitem__(self, *args, **kwargs) -> None:
        """__getitem__(*args, **kwargs)
Overloaded function.

1. __getitem__(self: tensorstore_demo.IndexDomain, identifier: Union[int, str]) -> tensorstore_demo.Dim


Returns the single dimension specified by :python:`identifier`.

Args:
  identifier: Specifies a dimension by integer index or label.  As with
      :py:obj:`python:list`, a negative index specifies a dimension starting
      from the last dimension.

Examples:

    >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3],
    ...                         exclusive_max=[4, 5, 6],
    ...                         labels=['x', 'y', 'z'])
    >>> domain[0]
    Dim(inclusive_min=1, exclusive_max=4, label="x")
    >>> domain['y']
    Dim(inclusive_min=2, exclusive_max=5, label="y")
    >>> domain[-1]
    Dim(inclusive_min=3, exclusive_max=6, label="z")

Overload:
  identifier

Group:
  Sequence accessors


2. __getitem__(self: tensorstore_demo.IndexDomain, selection: typing.Any) -> tensorstore_demo.IndexDomain


Returns a new domain with a subset of the dimensions.

Args:

  selection: Specifies the dimensions to include, either by index or label.  May
      be any value or sequence of values convertible to a
      dimension selection.

Raises:
   ValueError: If any dimension is specified more than once.

Examples:

    >>> a = ts.IndexDomain(inclusive_min=[1, 2, 3],
    ...                    exclusive_max=[4, 5, 6],
    ...                    labels=['x', 'y', 'z'])
    >>> a[:2]
    { "x": [1, 4), "y": [2, 5) }
    >>> a[0, -1]
    { "x": [1, 4), "z": [3, 6) }
    >>> a['y', 'x']
    { "y": [2, 5), "x": [1, 4) }
    >>> a['y', 1]
    Traceback (most recent call last):
        ...
    ValueError: Input dimensions {1} specified more than once

Overload:
  selection

Group:
  Indexing


3. __getitem__(self: tensorstore_demo.IndexDomain, other: tensorstore_demo.IndexDomain) -> tensorstore_demo.IndexDomain


Slices this domain by another domain.

The result is determined by matching dimensions of :python:`other` to dimensions
of :python:`self` either by label or by index, according to one of the following
three cases:

.. list-table::
   :widths: auto

   * - :python:`other` is entirely unlabeled

     - Result is
       :python:`self[ts.d[:][other.inclusive_min:other.exclusive_max]`.
       It is an error if :python:`self.rank != other.rank`.

   * - :python:`self` is entirely unlabeled

     - Result is
       :python:`self[ts.d[:][other.inclusive_min:other.exclusive_max].labels[other.labels]`.
       It is an error if :python:`self.rank != other.rank`.

   * - Both :python:`self` and :python:`other` have at least one labeled dimension.

     - Result is
       :python:`self[ts.d[dims][other.inclusive_min:other.exclusive_max]`, where
       the sequence of :python:`other.rank` dimension identifiers :python:`dims`
       is determined as follows:

       1. If :python:`other.labels[i]` is specified (i.e. non-empty),
          :python:`dims[i] = self.labels.index(other.labels[i])`.  It is an
          error if no such dimension exists.

       2. Otherwise, ``i`` is the ``j``\\ th unlabeled dimension of :python:`other`
          (left to right), and :python:`dims[i] = k`, where ``k`` is the ``j``\\ th
          unlabeled dimension of :python:`self` (left to right).  It is an error
          if no such dimension exists.

       If any dimensions of :python:`other` are unlabeled, then it is an error
       if :python:`self.rank != other.rank`.  This condition is not strictly
       necessary but serves to avoid a discrepancy in behavior with normal
       domain alignment.

.. admonition:: Example with all unlabeled dimensions
   :class: example

   >>> a = ts.IndexDomain(inclusive_min=[0, 1], exclusive_max=[5, 7])
   >>> b = ts.IndexDomain(inclusive_min=[2, 3], exclusive_max=[4, 6])
   >>> a[b]
   { [2, 4), [3, 6) }

.. admonition:: Example with fully labeled dimensions
   :class: example

   >>> a = ts.IndexDomain(inclusive_min=[0, 1, 2],
   ...                    exclusive_max=[5, 7, 8],
   ...                    labels=["x", "y", "z"])
   >>> b = ts.IndexDomain(inclusive_min=[2, 3],
   ...                    exclusive_max=[6, 4],
   ...                    labels=["y", "x"])
   >>> a[b]
   { "x": [3, 4), "y": [2, 6), "z": [2, 8) }

.. admonition:: Example with mixed labeled and unlabeled dimensions
   :class: example

   >>> a = ts.IndexDomain(inclusive_min=[0, 0, 0, 0],
   ...                    exclusive_max=[10, 10, 10, 10],
   ...                    labels=["x", "", "", "y"])
   >>> b = ts.IndexDomain(inclusive_min=[1, 2, 3, 4],
   ...                    exclusive_max=[6, 7, 8, 9],
   ...                    labels=["y", "", "x", ""])
   >>> a[b]
   { "x": [3, 8), [2, 7), [4, 9), "y": [1, 6) }

Note:

  On :python:`other`, implicit bounds indicators have no effect.

Overload:
  domain

Group:
  Indexing


4. __getitem__(self: tensorstore_demo.IndexDomain, expr: tensorstore_demo.DimExpression) -> tensorstore_demo.IndexDomain


Transforms the domain by a dimension expression.

Args:
  expr: Dimension expression to apply.

Examples:

    >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3],
    ...                         exclusive_max=[6, 7, 8],
    ...                         labels=['x', 'y', 'z'])
    >>> domain[ts.d[:].translate_by[5]]
    { "x": [6, 11), "y": [7, 12), "z": [8, 13) }
    >>> domain[ts.d['y'][3:5]]
    { "x": [1, 6), "y": [3, 5), "z": [3, 8) }
    >>> domain[ts.d['z'][5]]
    { "x": [1, 6), "y": [2, 7) }

Note:

   For the purpose of applying a dimension expression, an
   :py:class:`IndexDomain` behaves like an IndexTransform with an
   output rank of 0.  Consequently, operations that primarily affect the output
   index mappings, like integer array indexing, are not very useful, though they
   are still permitted.

       >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3],
       ...                         exclusive_max=[6, 7, 8],
       ...                         labels=['x', 'y', 'z'])
       >>> domain[ts.d['z'][[3, 5, 7]]]
       { "x": [1, 6), "y": [2, 7), [0, 3) }

Overload:
  expr

Group:
  Indexing


5. __getitem__(self: tensorstore_demo.IndexDomain, transform: Any) -> tensorstore_demo.IndexDomain


Transforms the domain using an explicit index transform.

Example:

    >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3],
    ...                         exclusive_max=[6, 7, 8])
    >>> transform = ts.IndexTransform(
    ...     input_rank=4,
    ...     output=[
    ...         ts.OutputIndexMap(offset=5, input_dimension=3),
    ...         ts.OutputIndexMap(offset=-7, input_dimension=0),
    ...         ts.OutputIndexMap(offset=3, input_dimension=1),
    ...     ])
    >>> domain[transform]
    { [9, 14), [0, 5), (-inf*, +inf*), [-4, 1) }

Args:

  transform: Index transform, :python:`transform.output_rank` must equal
    :python:`self.rank`.

Returns:

  New domain of rank :python:`transform.input_rank`.

Note:

   This is equivalent to composing an identity transform over :python:`self`
   with :py:param:`.transform`,
   i.e. :python:`ts.IndexTransform(self)[transform].domain`.  Consequently,
   operations that primarily affect the output index mappings, like integer
   array indexing, are not very useful, though they are still permitted.

Overload:
  transform

Group:
  Indexing

        """
    def to_json(self, *args, **kwargs) -> None:
        """to_json(self: tensorstore_demo.IndexDomain) -> Any


        Returns the JSON representation.

        Group:
          Accessors
        """
    @property
    def exclusive_max(self) -> typing.Tuple[int, ...]:
        """Exclusive upper bound of the domain.

        Example:

            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3], shape=[3, 4, 5])
            >>> domain.exclusive_max
            (4, 6, 8)

        Group:
          Accessors


        """
    @property
    def inclusive_min(self) -> typing.Tuple[int, ...]:
        """Inclusive lower bound of the domain, alias of :py:obj:`.origin`.

        Example:

            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3], shape=[3, 4, 5])
            >>> domain.inclusive_min
            (1, 2, 3)

        Group:
          Accessors


        """
    @property
    def labels(self) -> typing.Tuple[str, ...]:
        """Dimension labels for each dimension.

        Example:

            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3], shape=[3, 4, 5])
            >>> domain.labels
            ('', '', '')
            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3],
            ...                         shape=[3, 4, 5],
            ...                         labels=['x', 'y', 'z'])
            >>> domain.labels
            ('x', 'y', 'z')

        Group:
          Accessors


        """
    @property
    def origin(self) -> typing.Tuple[int, ...]:
        """Inclusive lower bound of the domain.

        Example:

            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3], shape=[3, 4, 5])
            >>> domain.origin
            (1, 2, 3)

        Group:
          Accessors


        """
    @property
    def rank(self) -> int:
        """Number of dimensions in the index space.

        Example:

          >>> domain = ts.IndexDomain(shape=[100, 200, 300])
          >>> domain.rank
          3

        Group:
          Accessors


        """
    @property
    def shape(self) -> typing.Tuple[int, ...]:
        """Shape of the domain.

        Example:

            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3], shape=[3, 4, 5])
            >>> domain.shape
            (3, 4, 5)

        Group:
          Accessors


        """
    @property
    def size(self) -> int:
        """Total number of elements in the domain.

        This is simply the product of the extents in :py:obj:`.shape`.

        Example:

            >>> domain = ts.IndexDomain(inclusive_min=[1, 2, 3], shape=[3, 4, 5])
            >>> domain.size
            60

        Group:
          Accessors


        """
    __hash__ = None
    pass
class VeryLongClassNameForTestingOutWordWrapping:
    """This is a class with a very long name.

    Group:
      Some other group
    """

    def very_long_method_name_for_testing_out_word_wrapper(self, x: int) -> int:
        """This is a method with a very long name."""

class DimensionSelection(DimExpression):
    """This extends :py:obj:`DimExpression`.

    Group:
      Indexing
    """

    def foo(self, bar: int) -> None:
        """Non-inherited method."""
        pass
