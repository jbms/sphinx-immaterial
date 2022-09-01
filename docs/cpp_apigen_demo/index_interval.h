#ifndef CPP_APIGEN_DEMO_INDEX_INTERVAL_H
#define CPP_APIGEN_DEMO_INDEX_INTERVAL_H

#include "fake_stdlib.h"

namespace cpp_apigen_demo {

/// Demonstrates a non-template class.
///
/// \ingroup indexing
class IndexInterval {
 public:
  /// Constructs an interval.
  ///
  /// \param lower Lower bound.
  /// \param upper Upper bound.
  explicit IndexInterval(int lower, int upper);

  /// Prints a string representation to `os`.
  friend std::ostream& operator<<(std::ostream& os, IndexInterval x);

  /// Returns the lower bound.
  ///
  //! @returns The lower bound.
  int lower() const;

  /// Returns the upper bound.
  int upper() const;
};

/// Computes the union of two intervals.
///
/// \relates IndexInterval
IndexInterval Union(IndexInterval a, IndexInterval b);

}  // namespace cpp_apigen_demo

#endif  // CPP_APIGEN_DEMO_INDEX_INTERVAL_H
