#ifndef CPP_APIGEN_DEMO_FAKE_STDLIB_H
#define CPP_APIGEN_DEMO_FAKE_STDLIB_H

namespace std {
class ostream;
template <typename T, int N>
class array;
template <bool Condition, typename T = void>
using enable_if_t = T;
template <typename T, typename U>
constexpr inline bool is_convertible_v = true;
}  // namespace std

#endif // CPP_APIGEN_DEMO_FAKE_STDLIB_H
