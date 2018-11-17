# Installation

The application is written in Python2 using several third-party libraries
specified in the requirements.txt file. These libraries may be installed using
the pip command. Setting up a separate virtual environment prior to pip
installation is recommended. It keeps these libraries separate from the global
Python environment and avoids possible version conflicts. For example, using the
virtualenv tool:


```
virtualenv venv
source venv/bin/activate
```

Then, install the packages:

```
pip install -r requirements.txt
```

Run the server:

```
./run_flask_builtin_server.py
```

Test from browser:

```
http://0.0.0.0:5000/
```

When finished, CTRL+C to quit. If you are using virtualenv, exit that via:
```
deactivate
```
