#!/usr/bin/env python
from ontparser import app

if __name__ == "__main__":
    app.run(
        # Use 0.0.0.0 to run from all interfaces, not just local host
        # (127.0.0.1).
        host='0.0.0.0',

        # While under development, server restarts automatically if code
        # is changed.
        debug=True,
    )
