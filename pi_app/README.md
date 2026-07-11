# Raspberry Pi Checkpoint 4 Application

This application receives one camera node's framed JPEG stream over USB CDC, validates and atomically preserves the original, records timing/resource evidence, and displays the result on the Raspberry Pi touchscreen.

Run tests from the repository root:

```bash
python3 -m unittest discover -s pi_app/tests -v
```

Run the application:

```bash
python3 -m pi_app.bullettime.main --config pi_app/config.json
```

Use `--headless` for receiver/storage testing without the fullscreen UI. The application searches `/dev/serial/by-id`, `/dev/ttyACM*`, and `/dev/ttyUSB*`; the node UID in the protocol, not the Linux device number, controls logical camera identity.

