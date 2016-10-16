#!/usr/bin/env python3

import sys
from usb_pdml import USBPDML
from protocol import USBPacket, USBPacketFeed, load_msg
import protocol
import pickle

if __name__ == "__main__":
    if (sys.argv[1].endswith(".pickle3")):
        with open(sys.argv[1], "rb") as f:
            interactions = pickle.load(f)
    else:
        conversation = USBPDML(sys.argv[1])
        conversation.parse_file()
        interactions = conversation.interaction()
        with open(sys.argv[1] + ".pickle3", "wb") as f:
            pickle.dump(interactions, f)

    start_time = None
    index = 0
    dir_specific = {
        ">":{
            "feed":USBPacketFeed(),
            "cmds": {},
            "color":"\033[1;32m{0}\033[00m",
        },
        "<":{
            "feed":USBPacketFeed(),
            "cmds": {},
            "color":"\033[1;34m{0}\033[00m",
        }
    }
    incoming_data = bytearray([])
    for msg in interactions:
        index += 1
        customstring = ""
        if (start_time == None):
            start_time = msg["time"]
        t = msg["time"] - start_time
        
        if "data" in msg:
            usb_packet = USBPacket.read(bytes(msg["data"]))
            direction = msg["direction"]
            res = dir_specific[direction]["feed"].packet(usb_packet)
            if (res):
                packet = load_msg(res)
                print(dir_specific[direction]["color"].format("#{:>5d} {:r}".format(index, packet)))
                command_dir = (packet.command.command, packet.command.direction)
                if (not command_dir in dir_specific[direction]["cmds"]):
                    dir_specific[direction]["cmds"][command_dir] = 0
                dir_specific[direction]["cmds"][command_dir] += 1
                if ((direction == "<") and (type(packet) == protocol.DataReply)):
                    incoming_data += packet.content()
            #print(usb_packet)
        # print("#{:0>5d}".format(index))
    print(dir_specific[">"]["color"].format("outgoing (>):"))
    print("\n".join([str(a) for a in dir_specific[">"]["cmds"].items()]))
    print(dir_specific["<"]["color"].format("Incoming (<):"))
    print("\n".join([str(a) for a in dir_specific["<"]["cmds"].items()]))

    with open("/tmp/reconstructed_data.bin", "wb") as f:
        f.write(incoming_data)