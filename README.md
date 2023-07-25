# cpython-interop

cpython-interop is a set of cmake functions and utilties that generate code to seamlessly interoperate between a C API and Python via ctypes bindings.

For example, a C function that looks like

`EXPORT_API Result createHandle(HandleParams params, Handle* handle);`

can be called using the Python code

```
handle=Handle()
params=HandleParams()
assert(createHandle(params, byref(handle)) == OK)
```

Callbacks in a C API can also be easily declared and used, like so

```
@HandleCallbackFuncType def handleCallback(context, contextSizeBytes, handle) -> Result:
    return OK
...
# Set our callback function in HandleParams
params.handleCallbackFunc = handleCallback

```

In order to generate the bindings, all we need to do is to add the following lines of CMake in the `CMakeLists.txt` of the C library

```
# Include our function(s) from cpython-interop
include(${CMAKE_SOURCE_DIR}/cpython-interop/ctypes_bindings.cmake)

...

# Generate ctypes bindings for Python -> C calls
ctypes_bindings(${PROJECT_NAME} 
    ${CMAKE_CURRENT_SOURCE_DIR}/capi.h
    ${CMAKE_CURRENT_BINARY_DIR}/capi.py)

```

And that's it! The function will also add an install target to copy the generated bindings to the Python site library. See the [example(s)](https://github.com/aniongithub/cpython-interop-examples/tree/main/examples) here.
