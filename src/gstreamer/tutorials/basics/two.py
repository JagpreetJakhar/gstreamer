def main():
    import sys
    import gi
    import logging

    gi.require_version("GLib","2.0")
    gi.require_version("GObject","2.0")
    gi.require_version("Gst","1.0")

    from gi.repository import Gst,GLib,GObject

    logging.basicConfig(level=logging.DEBUG,format="[%(name)s] [%(levelname)8s] - %(message)s")
    logger = logging.getLogger(__name__)

    Gst.init(sys.argv[1:])

    source = Gst.ElementFactory.make("videotestsrc","source") #type,name
    sink = Gst.ElementFactory.make("autovideosink","sink")
    
    filt = Gst.ElementFactory.make("vertigotv","filter")
    vcc = Gst.ElementFactory.make("videoconvert","converter")
    pipeline = Gst.Pipeline.new("test-pipeline")

    if not pipeline or not source or not sink or not filt:
        logger.error("Not all elements could be created")
        sys.exit(1)


    pipeline.add(source)
    pipeline.add(sink)
    pipeline.add(filt)
    pipeline.add(vcc)
    if not source.link(filt):
        logger.error("Elements could not be linked")
        sys.exit(1)
    if not filt.link(vcc):
        logger.error("Filter and videoconvert could not be linked")
        sys.exit(1)
    if not vcc.link(sink):
        logger.error("videoconvert and sink could not be linked")
        sys.exit(1)
        
    source.props.pattern=0

    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        logger.error("Unable to set pipeline state to playing state")
        sys.exit(1)

    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE,Gst.MessageType.ERROR | Gst.MessageType.EOS)

    if msg:
        if msg.type==Gst.MessageType.ERROR:
            err,debug_info =msg.parse_error()
            logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
            logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")
        elif msg.type==Gst.MessageType.EOS:
            logger.info("End of Stream--")
        else:
            logger.error("Unexpected Exit")
    pipeline.set_state(Gst.State.NULL)
if __name__=="__main__":
    main()
