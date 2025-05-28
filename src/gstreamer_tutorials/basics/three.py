def main():
    import sys
    import logging
    import gi

    gi.require_version("Gst", "1.0")
    gi.require_version("GObject", "2.0")
    from gi.repository import Gst, GObject

    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
    logger = logging.getLogger(__name__)
    class CustomData:
        def __init__(self):
            self.pipeline = None
            self.source = None
            self.aconvert = None
            self.vconvert=None
            self.aresample = None
            self.asink = None
            self.vsink=None


    def pad_added_handler(src, new_pad, data):
        asink_pad = data.aconvert.get_static_pad("sink")
        vsink_pad = data.vconvert.get_static_pad("sink")
        if asink_pad.is_linked() and vsink_pad.is_linked():
            logger.info("Audio sink already linked. Ignoring.")
            return

        new_pad_caps = new_pad.get_current_caps()
        new_pad_struct = new_pad_caps.get_structure(0)
        new_pad_type = new_pad_struct.get_name()
        

        if not new_pad_type.startswith("audio/x-raw") and not new_pad_type.startswith("video/x-raw"):
            logger.info(f"It has type '{new_pad_type}' which is not raw audio. Ignoring.")
            return
        aret = new_pad.link(asink_pad)
        vret = new_pad.link(vsink_pad)
        if aret == Gst.PadLinkReturn.OK:
            logger.info(f"Link succeeded (type '{new_pad_type}').")
        elif vret == Gst.PadLinkReturn.OK:
            logger.info(f"Link succeeded (type '{new_pad_type}').")
        else:
            logger.warning(f"Type is '{new_pad_type}' but link failed.")


    Gst.init(sys.argv[1:])

    data = CustomData()

    data.source = Gst.ElementFactory.make("uridecodebin", "source")
    data.aconvert = Gst.ElementFactory.make("audioconvert", "convert")
    data.aresample = Gst.ElementFactory.make("audioresample", "resample")
    data.asink = Gst.ElementFactory.make("autoaudiosink", "sink")
    data.vconvert=Gst.ElementFactory.make("videoconvert","vcon")
    data.vsink = Gst.ElementFactory.make("autovideosink","vsink")

    data.pipeline = Gst.Pipeline.new("test-pipeline")

    if not all([data.pipeline, data.source, data.aconvert,data.vconvert, data.aresample, data.asink,data.vsink]):
        logger.error("Not all elements could be created.")
        sys.exit(1)

    data.pipeline.add(data.source)
    data.pipeline.add(data.aconvert)
    data.pipeline.add(data.aresample)
    data.pipeline.add(data.asink)
    data.pipeline.add(data.vsink)
    data.pipeline.add(data.vconvert)

    if not data.aconvert.link(data.aresample):
        logger.error("Could not link aconvert -> aresample")
        sys.exit(1)
    if not data.aresample.link(data.asink):
        logger.error("Could not link aresample -> asink")
        sys.exit(1)
    if not data.vconvert.link(data.vsink):
        logger.error("Could not link vconv -> vsink")
        sys.exit(1)
    
    data.source.set_property("uri", "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm")
    data.source.connect("pad-added", pad_added_handler, data)

    ret = data.pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        logger.error("Unable to set the pipeline to the playing state.")
        sys.exit(1)

    bus = data.pipeline.get_bus()

    terminate = False
    while not terminate:
        msg = bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE,
            Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS
        )

        if msg:
            if msg.type == Gst.MessageType.ERROR:
                err, debug_info = msg.parse_error()
                logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
                logger.error(f"Debugging information: {debug_info or 'none'}")
                terminate = True
            elif msg.type == Gst.MessageType.EOS:
                logger.info("End-Of-Stream reached.")
                terminate = True
            elif msg.type == Gst.MessageType.STATE_CHANGED and msg.src == data.pipeline:
                old, new, pending = msg.parse_state_changed()
                logger.info(f"Pipeline state changed from {Gst.Element.state_get_name(old)} to {Gst.Element.state_get_name(new)}")
            else:
                logger.warning(f"Unexpected message type: {msg.type}, from: {msg.src.get_name()}")

    data.pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    main()

