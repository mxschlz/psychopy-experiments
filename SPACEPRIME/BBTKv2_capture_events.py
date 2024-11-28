import bbtkv2


# define config file
BBTK_CONF_FILE = "SPACEPRIME/bbtkv2.toml"  # change to the conf file you created
# instantiate BBTKv2 object
bb = bbtkv2.BlackBoxToolKit(BBTK_CONF_FILE)
# clear the internal memory of the BBTKv2
bb.clear_timing_data()
# capture events
text = bb.capture(1)   # start capturing events
# convert the results into human readable formats:
df1 = bbtkv2.capture_output_to_dataframe(text)
processed_events = bbtkv2.capture_dataframe_to_events(df1)
print(processed_events)