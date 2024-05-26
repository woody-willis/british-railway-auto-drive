
# British Railway Auto Drive

A Python script that aims to automatically drives trains in the [British Railway](https://www.roblox.com/games/10082031223/British-Railway) game on Roblox.

The script is currently tuned for the Class 170 but I aim to have it work well for a variety of other trains. The script may work with other trains but it is at your own risk.

# Caveats

* Trains do not stop automatically at stations. They only slow down for you to manually stop them.
* The Roblox window size/screen size must be 1920*1080

# Features

* Automatically speeds up and slows down for stations
* Sticks to the speed limit
* Follows signal instructions
* Operates doors automatically / Supports guards

# Usage

## Install tesseract

Windows: https://github.com/UB-Mannheim/tesseract/wiki

Mac: `brew install tesseract`

## Install dependencies

```bash
pip3 install -r requirements.txt
```

## Start script

Start a route in British Railway with a class 170 then

```bash
python3 main.py
```

and switch back to the Roblox window.