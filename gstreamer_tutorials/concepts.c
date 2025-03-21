#include<gst/gst.h>

int tutorial_main(int argc,char *argv[]){
    GstElement *pipeline,*source,*vertigo,*videocon,*sink;
    GstBus *bus;
    GstMessage *msg;
    GstStateChangeReturn ret;

    gst_init(&argc,&argv);

    /*gst_element_factory_make(type,name) */
    source = gst_element_factory_make("videotestsrc","source");
    vertigo = gst_element_factory_make("vertigotv","vertigo");
    videocon = gst_element_factory_make("videoconvert","videocon");
    sink = gst_element_factory_make("autovideosink","sink");

    pipeline =gst_pipeline_new("test-pipeline");

    if(!pipeline || !source || !vertigo ||!sink){
        g_printerr("Not all elements could be created\n");
        return -1;
    }

    gst_bin_add_many(GST_BIN (pipeline),source,vertigo,videocon,sink,NULL);
    if(gst_element_link(source,vertigo) != TRUE || gst_element_link(vertigo,videocon)!=TRUE || gst_element_link(videocon,sink)!=TRUE){
        g_printerr("Elements source<>vertigo could not be linked.\n");
        gst_object_unref(pipeline);
        return -1;
    }

    g_object_set(source,"pattern",0,NULL);

    ret = gst_element_set_state(pipeline,GST_STATE_PLAYING);

    if (ret==GST_STATE_CHANGE_FAILURE){
        g_printerr("Unable to set the pipeline to the playing state.\n");
        gst_object_unref(pipeline);
        return -1;
    }

    bus = gst_element_get_bus(pipeline);
    msg = gst_bus_timed_pop_filtered(bus,GST_CLOCK_TIME_NONE,GST_MESSAGE_ERROR | GST_MESSAGE_EOS);

    if (msg!=NULL){
        GError *err;
        gchar *debug_info;
        
        switch(GST_MESSAGE_TYPE(msg)){
            case GST_MESSAGE_ERROR:
                gst_message_parse_error(msg,&err,&debug_info);
                g_printerr("Error received  from element %s: %s\n",GST_OBJECT_NAME(msg->src),err->message);
                g_printerr("Debugging Information : %s\n.",debug_info ? debug_info:"none");
                g_clear_error(&err);
                g_free(debug_info);
                break;
            case GST_MESSAGE_EOS:
                g_print("End of stream reached\n");
                break;
            default:
                g_printerr("Unexpected turn of events\n.");
                break;
        }
        gst_message_unref(msg);
    }

    gst_object_unref(bus);
    gst_element_set_state(pipeline,GST_STATE_NULL);
    gst_object_unref(pipeline);
    return 0;
}

int main (int argc,char *argv[]){
    return tutorial_main(argc,argv);
}



