## Compilation Instructions

To compile the `pipe.c` file using GCC with GStreamer, use the following command:

```sh
gcc pipe.c -o pipe $(pkg-config --cflags --libs gstreamer-1.0)

