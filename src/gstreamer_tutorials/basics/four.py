import sys
import gi
import time

gi.require_version("GLib","2.0")
gi.require_version("GObject","2.0")
gi.require_version("Gst","1.0")

from gi.repository import Gst,GLib,GObject
class CustomData:
    def __init__(self):
        self.playbin = None
        self.playing = False
        self.terminate = False
        self.seek_enabled = False
        self.seek_done = False
        self.duration = Gst.CLOCK_TIME_NONE

def handle_message(data, msg):
    t = msg.type
    if t == Gst.MessageType.ERROR:
        err, debug = msg.parse_error()
        print(f"Error received from element {msg.src.get_name()}: {err.message}")
        print(f"Debugging information: {debug if debug else 'none'}")
        data.terminate = True

    elif t == Gst.MessageType.EOS:
        print("\nEnd-Of-Stream reached.")
        data.terminate = True

    elif t == Gst.MessageType.DURATION_CHANGED:
        data.duration = Gst.CLOCK_TIME_NONE

    elif t == Gst.MessageType.STATE_CHANGED:
        if msg.src == data.playbin:
            old_state, new_state, pending_state = msg.parse_state_changed()
            print(f"Pipeline state changed from {Gst.Element.state_get_name(old_state)} to {Gst.Element.state_get_name(new_state)}:")
            data.playing = (new_state == Gst.State.PLAYING)

            if data.playing:
                # Query if seeking is supported
                query = Gst.Query.new_seeking(Gst.Format.TIME)
                if data.playbin.query(query):
                    fmt, data.seek_enabled, start, end = query.parse_seeking()
                    if data.seek_enabled:
                        print(f"Seeking is ENABLED from {start // Gst.SECOND}s to {end // Gst.SECOND}s")
                    else:
                        print("Seeking is DISABLED for this stream.")
                else:
                    print("Seeking query failed.")
    else:
        print("Unexpected message received.")

def main():
    Gst.init(None)

    data = CustomData()
    data.playbin = Gst.ElementFactory.make("playbin", "playbin")
    if not data.playbin:
        print("Not all elements could be created.")
        return 1

    data.playbin.set_property("uri", "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm")
    ret = data.playbin.set_state(Gst.State.PLAYING)

    if ret == Gst.StateChangeReturn.FAILURE:
        print("Unable to set the pipeline to the playing state.")
        data.playbin.set_state(Gst.State.NULL)
        return 1

    bus = data.playbin.get_bus()

    try:
        while not data.terminate:
            msg = bus.timed_pop_filtered(
                100 * Gst.MSECOND,
                Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR |
                Gst.MessageType.EOS | Gst.MessageType.DURATION_CHANGED)

            if msg:
                handle_message(data, msg)
            else:
                if data.playing:
                    success, current = data.playbin.query_position(Gst.Format.TIME)
                    if not success:
                        print("Could not query current position.")
                        continue

                    if data.duration == Gst.CLOCK_TIME_NONE:
                        success, data.duration = data.playbin.query_duration(Gst.Format.TIME)
                        if not success:
                            print("Could not query current duration.")
                            continue

                    print(f"Position {current // Gst.SECOND}s / {data.duration // Gst.SECOND}s", end='\r')

                    if data.seek_enabled and not data.seek_done and current > 10 * Gst.SECOND:
                        print("\nReached 10s, performing seek...")
                        data.playbin.seek_simple(
                            Gst.Format.TIME,
                            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                            20 * Gst.SECOND
                        )
                        data.seek_done = True
    finally:
        # Always clean up the pipeline
        data.playbin.set_state(Gst.State.NULL)

    return 0

if __name__ == "__main__":
    sys.exit(main())

