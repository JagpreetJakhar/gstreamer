import gi
import sys

gi.require_version('Gtk', '3.0')
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')

from gi.repository import Gtk, Gst, GLib

Gst.init(None)

class MediaPlayer:
    def __init__(self):
        self.duration = Gst.CLOCK_TIME_NONE
        self.state = Gst.State.NULL

        # Create playbin element
        self.playbin = Gst.ElementFactory.make('playbin', 'playbin')
        if not self.playbin:
            print("Failed to create playbin.")
            sys.exit(1)

        # Create video sink
        self.video_sink = self._create_video_sink()
        if not self.video_sink:
            print("Failed to create video sink.")
            sys.exit(1)

        self.playbin.set_property('video-sink', self.video_sink)

        # Build UI
        self._build_ui()

        # Set URI
        self.playbin.set_property(
            'uri',
            'https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm'
        )

        # Connect tags-changed signals
        self.playbin.connect('video-tags-changed', self._tags_cb)
        self.playbin.connect('audio-tags-changed', self._tags_cb)
        self.playbin.connect('text-tags-changed', self._tags_cb)

        # Set up bus
        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect('message::error', self._on_error)
        bus.connect('message::eos', self._on_eos)
        bus.connect('message::state-changed', self._on_state_changed)
        bus.connect('message::application', self._on_application)

        # Start playback immediately
        self.playbin.set_state(Gst.State.PLAYING)

        # Refresh UI periodically
        GLib.timeout_add_seconds(1, self._refresh_ui)

    def _create_video_sink(self):
        # Try gtkglsink
        gtkglsink = Gst.ElementFactory.make('gtkglsink', 'gtkglsink')
        if gtkglsink:
            glsinkbin = Gst.ElementFactory.make('glsinkbin', 'glsinkbin')
            if glsinkbin:
                glsinkbin.set_property('sink', gtkglsink)
                self.video_widget = gtkglsink.get_property('widget')
                return glsinkbin

        # Fallback to gtksink
        gtksink = Gst.ElementFactory.make('gtksink', 'gtksink')
        if gtksink:
            self.video_widget = gtksink.get_property('widget')
            return gtksink

        return None

    def _build_ui(self):
        self.window = Gtk.Window(title="GStreamer GTK Player")
        self.window.set_default_size(640, 480)
        self.window.connect('delete-event', self._on_delete_event)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.add(main_box)

        video_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.pack_start(video_box, True, True, 0)

        video_box.pack_start(self.video_widget, True, True, 0)

        self.streams_list = Gtk.TextView()
        self.streams_list.set_editable(False)
        video_box.pack_start(self.streams_list, False, False, 0)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        main_box.pack_start(controls, False, False, 0)

        play_button = Gtk.Button.new_from_icon_name(
            "media-playback-start",
            Gtk.IconSize.SMALL_TOOLBAR
        )
        play_button.connect('clicked', self._on_play)
        controls.pack_start(play_button, False, False, 0)

        pause_button = Gtk.Button.new_from_icon_name(
            "media-playback-pause",
            Gtk.IconSize.SMALL_TOOLBAR
        )
        pause_button.connect('clicked', self._on_pause)
        controls.pack_start(pause_button, False, False, 0)

        stop_button = Gtk.Button.new_from_icon_name(
            "media-playback-stop",
            Gtk.IconSize.SMALL_TOOLBAR
        )
        stop_button.connect('clicked', self._on_stop)
        controls.pack_start(stop_button, False, False, 0)

        # Single slider connection
        self.slider = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.slider.set_draw_value(False)
        self.slider_update_signal_id = self.slider.connect(
            'value-changed', self._on_slider_changed
        )
        controls.pack_start(self.slider, True, True, 0)

        self.window.show_all()

    def _on_play(self, button):
        self.playbin.set_state(Gst.State.PLAYING)

    def _on_pause(self, button):
        self.playbin.set_state(Gst.State.PAUSED)

    def _on_stop(self, button):
        self.playbin.set_state(Gst.State.READY)

    def _on_delete_event(self, widget, event):
        self._on_stop(None)
        Gtk.main_quit()

    def _on_slider_changed(self, scale):
        seek_time = scale.get_value()
        self.playbin.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            int(seek_time * Gst.SECOND)
        )

    def _refresh_ui(self):
        if self.state < Gst.State.PAUSED:
            return True

        if self.duration == Gst.CLOCK_TIME_NONE:
            success, self.duration = self.playbin.query_duration(Gst.Format.TIME)
            if success:
                self.slider.set_range(0, self.duration / Gst.SECOND)

        success, current = self.playbin.query_position(Gst.Format.TIME)
        if success:
            # block the one handler we have
            self.slider.handler_block(self.slider_update_signal_id)
            self.slider.set_value(current / Gst.SECOND)
            self.slider.handler_unblock(self.slider_update_signal_id)

        return True

    def _tags_cb(self, playbin, stream):
        structure = Gst.Structure.new_empty("tags-changed")
        msg = Gst.Message.new_application(playbin, structure)
        playbin.get_bus().post(msg)

    def _on_error(self, bus, msg):
        err, debug = msg.parse_error()
        print(f"Error: {err.message}")
        if debug:
            print(f"Debug info: {debug}")
        self.playbin.set_state(Gst.State.READY)

    def _on_eos(self, bus, msg):
        print("End-Of-Stream reached.")
        self.playbin.set_state(Gst.State.READY)

    def _on_state_changed(self, bus, msg):
        if msg.src == self.playbin:
            old, new, _ = msg.parse_state_changed()
            self.state = new
            print(f"State changed to {Gst.Element.state_get_name(new)}")
            if old == Gst.State.READY and new == Gst.State.PAUSED:
                self._refresh_ui()

    def _on_application(self, bus, msg):
        if msg.get_structure().get_name() == "tags-changed":
            self._analyze_streams()

    def _analyze_streams(self):
        buf = self.streams_list.get_buffer()
        buf.set_text("")

        n_video = self.playbin.get_property("n-video")
        n_audio = self.playbin.get_property("n-audio")
        n_text = self.playbin.get_property("n-text")

        for i in range(n_video):
            tags = self.playbin.emit("get-video-tags", i)
            if tags:
                codec = tags.get_string(Gst.TAG_VIDEO_CODEC)[1]
                buf.insert_at_cursor(f"video stream {i}:\n  codec: {codec}\n")

        for i in range(n_audio):
            tags = self.playbin.emit("get-audio-tags", i)
            if tags:
                codec = tags.get_string(Gst.TAG_AUDIO_CODEC)[1]
                lang  = tags.get_string(Gst.TAG_LANGUAGE_CODE)[1]
                rate  = tags.get_uint(Gst.TAG_BITRATE)[1]
                buf.insert_at_cursor(
                    f"\naudio stream {i}:\n"
                    f"  codec: {codec}\n"
                    f"  language: {lang}\n"
                    f"  bitrate: {rate}\n"
                )

        for i in range(n_text):
            tags = self.playbin.emit("get-text-tags", i)
            if tags:
                lang = tags.get_string(Gst.TAG_LANGUAGE_CODE)[1]
                buf.insert_at_cursor(
                    f"\nsubtitle stream {i}:\n"
                    f"  language: {lang}\n"
                )

def main():
    player = MediaPlayer()
    Gtk.main()

if __name__ == "__main__":
    main()

