import sys

import lib.streamerlsl as streamerlsl
from lib.dummylsl import DummyLSL


def main(argv):
    # if no arguments are provided, default to streaming real data
    if not argv:
        lsl = streamerlsl.StreamerLSL()
        lsl.create_lsl()
        lsl.begin(autostart=True)
    else:
        if argv[0] == '--dummy':
            lsl = DummyLSL()
        elif argv[0] == '--port':
            port = argv[1]
            lsl = streamerlsl.StreamerLSL(port=port)
        elif argv[0] == '--channels':
            ch_names = []
            for ch in argv[1:]:
                ch_names.append(ch)
            lsl = streamerlsl.StreamerLSL(ch_names=ch_names)
        else:
            lsl = streamerlsl.StreamerLSL()

        lsl.create_lsl()
        lsl.begin(autostart=True)


if __name__ == '__main__':
    main(sys.argv[1:])
