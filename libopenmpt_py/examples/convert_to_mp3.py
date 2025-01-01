from libopenmpt_py import libopenmpt
from io import BytesIO
import subprocess
import ctypes
import warnings
import os


def log_callback(user_data, level, message):
    pass


def error_callback(user_data, message):
    pass


def libopenmpt_example_print_error(
    func_name: ctypes.c_char, mod_err: int, mod_err_str: ctypes.c_char
):
    if not func_name:
        func_name = ctypes.c_char(b"unknown function")

    if mod_err == libopenmpt.OPENMPT_ERROR_OUT_OF_MEMORY:
        mod_err_str = libopenmpt.openmpt_error_string(mod_err)
        if not mod_err_str:
            warnings.warn("Error: OPENMPT_ERROR_OUT_OF_MEMORY")
        else:
            warnings.warn(f"Error: {mod_err_str}")
            mod_err_str = None
    else:
        if not mod_err_str:
            mod_err_str = libopenmpt.openmpt_error_string(mod_err)
            if not mod_err_str:
                warnings.warn(f"Error: {func_name} failed.")
            else:
                warnings.warn(f"Error: {func_name} failed: {mod_err_str}")
            libopenmpt.openmpt_free_string(mod_err_str)
            mod_err_str = None


openmpt_log_func = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
)
openmpt_error_func = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
)
load_mod = libopenmpt.openmpt_module_create_from_memory2

SAMPLERATE = 48000
BUFFERSIZE = 480

buffer = (ctypes.c_int16 * (BUFFERSIZE * 2))()
pcm_data = BytesIO()

filename = os.path.join(os.path.dirname(__file__), "xrtd_-_osc.xm")

with open(filename, "rb") as f:
    module_data = f.read()
    module_size = len(module_data)

ctls = ctypes.c_void_p()
error = ctypes.c_int()
error_message = ctypes.c_char_p()
error = ctypes.c_int()
error_message = ctypes.c_char_p()

header_size = libopenmpt.openmpt_probe_file_header_get_recommended_size()
can_read = libopenmpt.openmpt_probe_file_header(
    ctypes.c_uint64(libopenmpt.OPENMPT_PROBE_FILE_HEADER_FLAGS_DEFAULT), # uint_64t flags
    module_data, # const void * data
    header_size, # size_t size
    module_size, # uint_64t filesize
    openmpt_log_func(log_callback), # openmpt_log_func logfunc
    None, # void * loguser
    openmpt_error_func(error_callback),  # openmpt_error_func errfunc
    None,  # void * erruser
    ctypes.byref(error),  # int * error
    ctypes.byref(error_message),  # const char ** error_message
)

if can_read == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_SUCCESS:
    pass
elif can_read == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_FAILURE:
    raise TypeError("The file is not supported by libopenmpt.")
elif libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_WANTMOREDATA:
    raise NotImplementedError("An answer could not be determined with the amount of data provided. You may have to manually change the header_size")
elif can_read == libopenmpt.OPENMPT_PROBE_FILE_HEADER_RESULT_ERROR:
    raise SystemError("An internal error occured.")

mod = load_mod(
    module_data,  # const void * filedata
    module_size,  # size_t filesize
    openmpt_log_func(log_callback),  # openmpt_log_func logfunc
    None,  # void * loguser
    openmpt_error_func(error_callback),  # openmpt_error_func errfunc
    None,  # void * erruser
    ctypes.byref(error),  # int * error
    ctypes.byref(error_message),  # const char ** error_message
    ctls,  # const openmpt_module_initial_ctl * ctls
)

metadata = {
    key: libopenmpt.openmpt_module_get_metadata(mod, ctypes.c_char_p(key))
    for key in libopenmpt.openmpt_module_get_metadata_keys(mod).split(b";")
}

artist_name = metadata[b"artist"]
title = metadata[b"title"]
comment = metadata[b"message"]

while True:
    libopenmpt.openmpt_module_error_clear(mod)
    count = libopenmpt.openmpt_module_read_interleaved_stereo(
        mod, SAMPLERATE, BUFFERSIZE, buffer
    )
    mod_err = libopenmpt.openmpt_module_error_get_last(mod)
    mod_err_str = libopenmpt.openmpt_module_error_get_last_message(mod)
    if mod_err != libopenmpt.OPENMPT_ERROR_OK:
        libopenmpt_example_print_error(
            "openmpt_module_read_interleaved_stereo()", mod_err, mod_err_str
        )
        libopenmpt.openmpt_free_string(mod_err_str)
        mod_err_str = None
    if count == 0:
        break
    size = count * 2 * ctypes.sizeof(ctypes.c_int16)
    written = pcm_data.write(bytes(buffer))
    # if written != size:
    #     print('Error: file write error', written, size, f"{count}, {ctypes.sizeof(ctypes.c_int16)}")
    #     break

pcm_data.seek(0)
pcm_bytes = pcm_data.read()

# arguments for the mp3lame encoder. uses a 48kb buffer and converts the track to 128kbps mp3.
lame_cmd = [
    "encoders/lame.exe",
    "-r",
    "-s",
    "48",
    "-b",
    "128",
    "--ta",
    artist_name,
    "--tt",
    title,
    "-",
    "-",
]
lame_proc = subprocess.Popen(lame_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

mp3_bytes, _ = lame_proc.communicate(input=pcm_bytes)

with open(f'{title.decode() or "".join(filename.split(".")[:-1])}.mp3', "wb") as f:
    f.write(mp3_bytes)
