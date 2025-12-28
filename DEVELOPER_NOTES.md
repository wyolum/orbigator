# Orbigator Developer Notes

## Serial Port Management (Thonny vs mpremote)

### Clearing the Serial Port
If `mpremote` locks the serial port (`/dev/ttyACM0`) or if Thonny cannot connect due to a "Device is busy" error, the following command is the most effective way to force-clear the connection:

```bash
pkill -9 -f mpremote
```

Run this command in the terminal to immediately kill any background `mpremote` processes and free up the USB resource. This is safe to use between deployment scripts and Thonny sessions.
