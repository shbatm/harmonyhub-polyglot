#!/usr/bin/python

import yaml,collections,re

pfx = "write_profile:"

config_file = open('config.yaml', 'r')
config_data = yaml.load(config_file)
config_file.close

# TODO: Check that server node & name are defined.
#if 'server' in config and config['host'] is not None:
#    # use what the user has defined.
#    this_host = config['host']

NODEDEF_TMPL_A = """
  <nodeDef id="%s" nodeType="139" nls="%s">
    <sts>
      <st id="ST" editor="HUBST" />
      <st id="GV3" editor="%s" />
    </sts>
    <cmds>
      <sends>
	<cmd id="DON" />
      </sends>
      <accepts>
        <cmd id="SET_ACTIVITY">
          <p id="" editor="%s" init="%s"/>
        </cmd>
	<cmd id="REBOOT" />
	<cmd id="QUERY" />
      </accepts>
    </cmds>
  </nodeDef>
"""
NODEDEF_TMPL_D = """
  <nodeDef id="%s" nodeType="139" nls="%s">
    <sts />
    <cmds>
      <sends />
      <accepts>
        <cmd id="SET_BUTTON">
          <p id="" editor="%s"/>
        </cmd>
      </accepts>
    </cmds>
  </nodeDef>
"""
EDITOR_TMPL_S = """
  <editor id="%s">
    <range uom="25" subset="%s" nls="%s"/>
  </editor>
"""
EDITOR_TMPL_MM = """
  <editor id="%s">
    <range uom="25" min="%d" max="%d" nls="%s"/>
  </editor>
"""
# The NLS entries for the node definition
NLS_NODE_TMPL = """
ND-%s-NAME = %s
ND-%s-ICON = Input
"""
# The NLS entry for each indexed item
NLS_TMPL = "%s-%d = %s\n"

#
# Remove our old data from the nls file if present
#
nls_file = "en_US.txt"
nls = open("profile/nodedef/"+nls_file, "r")
found = False
nls_lines = []
split_line = "# Below is generated from the harmony hubs"
p = re.compile(split_line)
for line in file:
    if not found:
        if p.match(line):
            found = True
        else:
            nls_lines.append(line)
nls.close()

nodedef = open("profile/nodedef/custom.xml", "w")
editor  = open("profile/editor/custom.xml", "w")
nls     = open("profile/nls/"+nls_file, "w")
for line in nls_lines:
    nls.write(line)

editor.write("<editors>\n")
nodedef.write("<nodeDefs>\n")

#
# This is all the activities available for all hubs.
#
activites = collections.OrderedDict()
ai = 0
#
# This is all the button functions available for all devices.
#
buttons = collections.OrderedDict()
bi = 0
#
# Loop over each Hub in the config data.
#
for key in config_data:
    # Ignore server.
    if key != "server":
        #
        # Process this hub.
        #
        host = config_data[key]['host']
        name = config_data[key]['name']
        info = "Hub: %s '%s'" % (key,name)
        nodedef.write("\n  <!-- === %s -->\n" % (info))
        nodedef.write(NODEDEF_TMPL_A % (key, 'HARMONYHUB', 'Act' + key, 'Act' + key, 'GV3'))
        nls.write("\n# %s" % (info))
        nls.write(NLS_NODE_TMPL % (key, name, key))
        #
        # Connect to the hub and get the configuration
        print(pfx + " Initializing Client")
        client = harmony_hub_client(host=host)
        print(pfx + " Client: " + str(client))
        harmony_config = client.get_config()
        client.disconnect(send_close=True)
        #
        # Build the activities
        #
        ais = ai
        for a in harmony_config['activity']:
            # Print the Harmony Activities to the log
            print("%s Activity: %s  Id: %s" % (pfx, a['label'], a['id']))
            if a['id'] != "-1":
                aname = "%s (%s)" % (a['label'],a['id'])
                nls.write(NLS_TMPL % (key.upper(), ai, aname))
                ai += 1
        editor.write(EDITOR_TMPL_S % ('Act'+key, "%d-%d" % (ais, ai-1)),key.upper()))
        #
        # Build all the devices
        #
        for d in harmony_config['device']:
            info = "Device '%s', Type=%s, Manufacturer=%s, Model=%s" % (d['label'],d['type'],d['manufacturer'],d['model'])
            subset = []
            nodedef.write("\n  <!-- === %s -->" % info)
            nodedef.write(NODEDEF_TMPL_D % ('d' + d['id'], 'D' + d['id'], 'Btn' + d['id']))
            nls.write("\n# %s" % info)
            nls.write(NLS_NODE_TMPL % ('d' + d['id'], d['label'], 'd' + d['id']))
            print("%s   Device: %s  Id: %s" % (pfx, d['label'], d['id']))
            #
            # Build all the button functions, these are global to all devices
            #
            for cg in d['controlGroup']:
                for f in cg['function']:
                    bname = f['name']
                    if not bname in buttons:
                        buttons[bname] = bi
                        bi += 1
                    cb = buttons[bname]
                    print("%s     Function: Index: %d, Name: %s,  Label: %s" % (pfx, cb, f['name'], f['label']))
                    #nls.write("# Button name: %s, label: %s\n" % (f['name'], f['label']))
                    # This is the list of button numbers in this device.
                    subset.append(cb)
            #
            # Turn the list of button numbers, into a compacted subset string for the editor.
            #
            subset_str = ""
            subset.sort()
            editor.write("\n  <!-- === %s -->\n" % info)
            editor.write("  <!-- full subset = %s -->" % ",".join(map(str,subset)))
            while len(subset) > 0:
                x = subset.pop(0)
                if subset_str != "":
                    subset_str += ","
                subset_str += str(x)
                y = False
                while len(subset) > 0 and (y == False or y == subset[0] - 1):
                    y = subset.pop(0)
                if y is not False:
                    subset_str += "-" + str(y)
            editor.write(EDITOR_TMPL_S % ('Btn' + d['id'], subset_str, 'BTN'))

    
nls.write("\n\n")
for key in buttons:
    nls.write(NLS_TMPL % ('BTN', buttons[key], key))
    
editor.write("</editors>")
nodedef.write("</nodeDefs>")
            
nodedef.close()
editor.close()
nls.close()

print(pfx + " done.")
exit
