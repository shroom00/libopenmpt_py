# libopenmpt_py

Python bindings for libopenmpt. Libopenmpt is a "cross-platform C++ and C library to decode tracked music files".
The docs can be found here: <https://lib.openmpt.org/doc/>
The bindings are based on the documentation here specifically: <https://lib.openmpt.org/doc/group__libopenmpt__c.html>.

Better documentation (and examples) soon, I hope. :p

NOTE: Line 20 of libopenmpt.py says `LIBOPENMPT = ctypes.cdll.LoadLibrary("libopenmpt_binaries/bin/x86/libopenmpt.dll")`. You should change the library location to fit the binary of your CPU architecture.
