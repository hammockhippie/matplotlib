/* -*- mode: c++; c-basic-offset: 4 -*- */

/* Small utilities that are shared by most extension modules. */

#ifndef _MPLUTILS_H
#define _MPLUTILS_H

#if defined(_MSC_VER) && _MSC_VER <= 1600
typedef unsigned __int8   uint8_t;
#else
#include <stdint.h>
#endif

#ifdef _POSIX_C_SOURCE
#    undef _POSIX_C_SOURCE
#endif
#ifdef _XOPEN_SOURCE
#    undef _XOPEN_SOURCE
#endif

#include <Python.h>

#if PY_MAJOR_VERSION >= 3
#define PY3K 1
#define Py_TPFLAGS_HAVE_NEWBUFFER 0
#else
#define PY3K 0
#endif

#undef CLAMP
#define CLAMP(x, low, high) (((x) > (high)) ? (high) : (((x) < (low)) ? (low) : (x)))

#undef MAX
#define MAX(a, b) (((a) > (b)) ? (a) : (b))

inline double mpl_round(double v)
{
    return (double)(int)(v + ((v >= 0.0) ? 0.5 : -0.5));
}

enum {
    STOP = 0,
    MOVETO = 1,
    LINETO = 2,
    CURVE3 = 3,
    CURVE4 = 4,
    ENDPOLY = 0x4f
};

const size_t NUM_VERTICES[] = { 1, 1, 1, 2, 3, 1 };

extern "C" int add_dict_int(PyObject *dict, const char *key, long val);

#if defined(_MSC_VER) && (_MSC_VER == 1400)

/* Required by libpng and zlib */
#pragma comment(lib, "bufferoverflowU")

/* std::max and std::min are missing in Windows Server 2003 R2
   Platform SDK compiler.  See matplotlib bug #3067191 */
namespace std
{

template <class T>
inline T max(const T &a, const T &b)
{
    return (a > b) ? a : b;
}

template <class T>
inline T min(const T &a, const T &b)
{
    return (a < b) ? a : b;
}
}

#endif

#endif
