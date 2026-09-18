// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

#include <Python.h>

#define CONCAT_IMPL(left, right) left##right
#define CONCAT(left, right) CONCAT_IMPL(left, right)
#define STRINGIFY_IMPL(value) #value
#define STRINGIFY(value) STRINGIFY_IMPL(value)

typedef struct TSLanguage TSLanguage;
const TSLanguage *LANGUAGE_SYMBOL(void);

static PyObject *language(PyObject *Py_UNUSED(self), PyObject *Py_UNUSED(args)) {
    return PyCapsule_New((void *)LANGUAGE_SYMBOL(), "tree_sitter.Language", NULL);
}

static PyMethodDef methods[] = {
    {"language", language, METH_NOARGS, "Return the bundled grammar as a Tree-sitter language capsule."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    STRINGIFY(LANGUAGE_MODULE),
    NULL,
    0,
    methods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC CONCAT(PyInit_, LANGUAGE_MODULE)(void) {
    return PyModule_Create(&module);
}
