#ifndef CPP_APIGEN_DEMO_ARRAY_H
#define CPP_APIGEN_DEMO_ARRAY_H

#include "fake_stdlib.h"

namespace cpp_apigen_demo {

/// Specifies the array data order.
///
/// \ingroup array
enum class DataOrder {
  /// C order
  C = 0,
  /// Fortran order
  F = 1,
};

/// Prints a string representation of a data order.
///
/// \relates DataOrder
std::ostream& operator<<(std::ostream& os, DataOrder order);

/// Defines a multi-dimensional array view.
///
/// \ingroup array
/// \tparam T Array element type.
/// \tparam Rank Number of dimensions.
template <class T, int Rank>
class Array {
 public:
  /// Constructs an array.
  ///
  /// \param data The data pointer.
  /// \param shape The shape of the array.
  /// \id data, shape
  Array(T* data, std::array<int, Rank> shape, DataOrder order = DataOrder::C);

  /// Converts from a compatible array.
  ///
  /// \tparam U Compatible array element type.
  /// \id convert
  template <typename U, typename = std::enable_if_t<
                            std::is_convertible_v<U (*)[], T (*)[]>>>
  Array(const Array<U, Rank>& other);

  /// Returns the data pointer.
  T* data() const;

  /// Returns the shape pointer.
  const std::array<int, Rank>& shape() const;

  /// Returns the data order.
  DataOrder order() const;

  /// Returns the element at the specified index or index vector.
  ///
  /// \param index The index vector, or an integer index in the case that `Rank == 1`.
  template <int SfinaeRank = Rank, typename = std::enable_if_t<SfinaeRank == 1>>
  T operator[](int index);
  T operator[](std::array<int, Rank> index);
};

}  // namespace cpp_apigen_demo

#endif  // CPP_APIGEN_DEMO_ARRAY_H
