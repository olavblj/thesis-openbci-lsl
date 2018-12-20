'''
  streamerlsl.py
  ---------------

  This is the module that handles the creation and function of LSL using OpenBCI data.
  
  If the GUI application is used, the GUI controls the parameters of the stream, and calls
  the functions of this class to create, run, and stop each stream instance.

  If the command line application is used, this module creates the LSL instances
  using default parameters, and then allows the user interaction with the stream via the CLI.


'''
import atexit
import random
import sys
import threading
import time
from collections import OrderedDict

from pylsl import StreamInfo, StreamOutlet

import lib.open_bci_v3 as bci


class StreamerLSL:
    def __init__(self, port=None, ch_names=None):
        self.default_settings = OrderedDict()
        self.current_settings = OrderedDict()

        self.ch_names = ch_names if ch_names is not None else ["C3", "C4", "P3", "P4"]

        print("\n-------INSTANTIATING BOARD-------")

        if port is None:
            self.board = bci.OpenBCIBoard()
        else:
            self.board = bci.OpenBCIBoard(port=port)

        self.n_eeg_channels = self.board.getNbEEGChannels()
        self.sample_rate = self.board.getSampleRate()

        self.init_board_settings()

    def init_board_settings(self):
        # set default board configuration

        # default to 16 channels initially
        self.default_settings["Number_Channels"] = [b'C']
        for i in range(16):
            current = "channel{}".format(i + 1)
            self.default_settings[current] = []
            self.default_settings[current].append(b'x')
            self.default_settings[current].append(str(i + 1).encode())
            self.default_settings[current].append(b'0')
            self.default_settings[current].append(b'6')
            self.default_settings[current].append(b'0')
            self.default_settings[current].append(b'1')
            self.default_settings[current].append(b'1')
            self.default_settings[current].append(b'0')
            self.default_settings[current].append(b'X')
        self.default_settings["SD_Card"] = b" "
        self.current_settings = self.default_settings.copy()

    def set_board_settings(self):
        for item in self.current_settings:
            if self.current_settings[item] != self.default_settings[item]:
                for byte in self.current_settings[item]:
                    self.board.ser.write(byte)
                    time.sleep(.2)

    def send(self, sample):
        try:
            self.outlet_eeg.push_sample(sample.channel_data)
        except:
            print("Error! Check LSL settings")

    def create_lsl(self, default=True, stream1=None):
        if default:
            random_id = random.randint(0, 255)
            # default parameters
            eeg_name = 'openbci_eeg'
            eeg_type = 'EEG'
            n_eeg_chan = self.n_eeg_channels
            eeg_hz = self.sample_rate
            eeg_dtype = 'float32'
            eeg_id = 'openbci_eeg_id' + str(random_id)
            # create StreamInfo
            self.info_eeg = StreamInfo(eeg_name, eeg_type, n_eeg_chan, eeg_hz, eeg_dtype, eeg_id)
        else:
            # user input parameters
            eeg_name = stream1['name']
            eeg_type = stream1['type']
            n_eeg_chan = stream1['channels']
            eeg_hz = stream1['sample_rate']
            eeg_dtype = stream1['datatype']
            eeg_id = stream1['id']
            # create StreamInfo
            self.info_eeg = StreamInfo(eeg_name, eeg_type, n_eeg_chan, eeg_hz, eeg_dtype, eeg_id)

        # channel locations
        channels = self.info_eeg.desc().append_child('channels')
        for ch_name in self.ch_names:
            ch = channels.append_child("channel")
            ch.append_child_value('label', ch_name)
            ch.append_child_value('unit', 'microvolts')
            ch.append_child_value('type', 'EEG')

        # additional Meta Data
        self.info_eeg.desc().append_child_value('manufacturer', 'OpenBCI Inc.')

        # create StreamOutlet
        self.outlet_eeg = StreamOutlet(self.info_eeg)

        print(
            "\n-------------CONFIG--------------\n" +
            "LSL Configuration: \n" +
            "  Stream 1: \n" +
            "      Name: " + eeg_name + " \n" +
            "      Type: " + eeg_type + " \n" +
            "      Channel Count: " + str(n_eeg_chan) + "\n" +
            "      Sampling Rate: " + str(eeg_hz) + "\n" +
            "      Channel Format: " + eeg_dtype + " \n" +
            "      Source Id: " + eeg_id + " \n"
        )

        print(
            "\n-------------MONTAGE-------------\n" +
            "Locations: \n" +
            "      " + str(self.ch_names) + "\n\n" +
            "IMPORTANT: Ensure these are correct before progressing.\n"
        )

    def cleanUp(self):
        self.board.disconnect()
        print("Disconnecting...")
        atexit.register(self.cleanUp)

    def start_streaming(self):
        board_thread = threading.Thread(target=self.board.start_streaming, args=(self.send, -1))
        board_thread.daemon = True  # will stop on exit
        board_thread.start()
        print("Current streaming: {} EEG channels at {} Hz\n".format(self.n_eeg_channels, self.sample_rate))

    def stop_streaming(self):
        self.board.stop()

        # clean up any leftover bytes from serial port
        # self.board.ser.reset_input_buffer()
        time.sleep(.1)
        line = ''
        while self.board.ser.inWaiting():
            # print("doing this thing")
            c = self.board.ser.read().decode('utf-8', errors='replace')
            line += c
            time.sleep(0.001)
            if c == '\n':
                line = ''
        print("Streaming paused.\n")

    def begin(self, autostart=False):
        print("\n-------------INFO----------------")
        print(
            "Commands: \n" + \
            "    Type \"/start\" to stream to LSL.\n" + \
            "    Type \"/stop\" to stop stream.\n" + \
            "    Type \"/exit\" to disconnect the board. \n" + \
            "Advanced command map available at http://docs.openbci.com\n")

        print("\n-------------BEGIN---------------")

        # Init board state
        # s: stop board streaming; v: soft reset of the 32-bit board (no effect with 8bit board)
        s = 'sv'
        # Tell the board to enable or not daisy module
        if self.board.daisy:
            s = s + 'C'
        else:
            s = s + 'c'
        # d: Channels settings back to default
        s = s + 'd'

        if autostart:
            for c in s:
                if sys.hexversion > 0x03000000:
                    self.board.ser.write(bytes(c, 'utf-8'))
                else:
                    self.board.ser.write(bytes(c))
                time.sleep(0.100)

            s = "/start"

        while s != "/exit":
            # Send char and wait for registers to set
            if not s:
                pass
            elif "help" in s:
                print("View command map at:" + \
                      "http://docs.openbci.com/software/01-OpenBCI_SDK.\n" + \
                      "For user interface: read README or view" + \
                      "https://github.com/OpenBCI/OpenBCI_Python")

            elif self.board.streaming and s != "/stop":
                print(
                    "Error: the board is currently streaming data, please type '/stop' before issuing new commands.")
            else:
                # read silently incoming packet if set (used when stream is stopped)
                flush = False

                if '/' == s[0]:
                    s = s[1:]
                    rec = False  # current command is recognized or fot

                    if "start" in s:
                        # start streaming in a separate thread so we could always send commands in here
                        board_thread = threading.Thread(target=self.board.start_streaming, args=(self.send, -1))
                        board_thread.daemon = True  # will stop on exit
                        try:
                            board_thread.start()
                            print("Streaming data...")
                        except:
                            raise
                        rec = True
                    elif 'test' in s:
                        test = int(s[s.find("test") + 4:])
                        self.board.test_signal(test)
                        rec = True
                    elif 'stop' in s:
                        self.board.stop()
                        rec = True
                        flush = True
                    elif 'loc' in s:
                        self.change_locations(s[4:])
                        rec = True
                        flush = True
                    if not rec:
                        print("Command not recognized...")

                elif s:
                    for c in s:
                        if sys.hexversion > 0x03000000:
                            self.board.ser.write(bytes(c, 'utf-8'))
                        else:
                            self.board.ser.write(bytes(c))
                        time.sleep(0.100)

                line = ''
                time.sleep(0.1)  # Wait to see if the board has anything to report
                while self.board.ser.inWaiting():
                    c = self.board.ser.read().decode('utf-8', errors='replace')
                    line += c
                    time.sleep(0.001)
                    if (c == '\n') and not flush:
                        print('%\t' + line[:-1])
                        line = ''
                if not flush:
                    print(line)

            # Take user input
            # s = input('--> ')
            if sys.hexversion > 0x03000000:
                s = input('--> ')
            else:
                s = input('--> ')

    def change_locations(self, locs):
        new_locs = [loc for loc in locs.split(',')]

        channels = self.info_eeg.desc().child('channels')
        ch = channels.child("channel")
        for label in new_locs:
            ch.set_child_value('label', label)
            ch = ch.next_sibling()

        print("New Channel Montage:")
        print(str(new_locs))

        # create StreamOutlet
        self.outlet_eeg = StreamOutlet(self.info_eeg)
        self.outlet_aux = StreamOutlet(self.info_aux)
