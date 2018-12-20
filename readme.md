# thesis-openbci-lsl

This is a modified version of [OpenBCI_LSL](https://github.com/OpenBCI/OpenBCI_LSL) for use in my master's thesis.

## Initial Setup

Run these commands in your terminal

```bash
git clone https://github.com/olavblj/thesis-openbci-lsl.git
cd thesis-openbci-lsl
pip install -r requirements.txt
```


## Usage

1. Make sure an OpenBCI headset is connected using the Bluetooth dongle. Consider verifying that it is working by using the OpenBCI GUI application.
2. Navigate to the root directory in your terminal
3. Run `python -m start_stream`

This should detect the port, and start streaming data automatically.

When running the program:
* To stop streaming data, enter `/stop`
* To start streaming data again, enter `/start`
* To exit the program, enter `/exit`

### Dummy data

If you want to run the program without the OpenBCI headset, and just output dummy data, use the `--dummy` flag

```bash
python -m start_stream --dummy
```

## Errors

**Cannot find OpenBCI port**

* Try unplugging the dongle, and turning off the headset. Replug the dongle, and _then_ turn on the headset again.
* Specify the port manually, using `python -m start_stream --port [portname]` 


