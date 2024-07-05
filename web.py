from flask import Flask, render_template
import json
from flask_sock import Sock
import numpy as np
from matplotlib import colors, colormaps, cm

import serial

arduino_port = "/dev/cu.usbmodem101"  # serial port of Arduino, go to tools-->port
baud = 9600  # your baud rate
ser = serial.Serial(arduino_port, baud)
print("Connected to Arduino port:" + arduino_port)

app = Flask(__name__)
sock = Sock(app)


class DataIncoming:
    """
    handles incoming serial date
    """

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.xyz = [0, 0, 0]

    def update(self, phi: float, theta: float, r: int):
        sinPhi = r * np.sin(phi)
        self.y = r * np.cos(phi)
        self.z = sinPhi * np.cos(theta)
        self.x = sinPhi * np.sin(theta)
        self.xyz[0] = self.x
        self.xyz[1] = self.y
        self.xyz[2] = self.z


di = DataIncoming()

# assuming the max distance will be 500 cm and min distance will be 5cm
norm = colors.Normalize(vmin=5, vmax=500)
f2rgb = cm.ScalarMappable(norm=norm, cmap=colormaps['plasma'])


class IDX:
    """
    keeps track of completion
    """

    def __init__(self, size):
        self.size = size
        self.idx = 0

    def update(self, val=1):
        self.idx += val
        self.idx = self.idx % self.size


counter = IDX(54000)  # 600 * 90
cInv = 100 / 54000


# @app.route("/")
# def index():
#     return render_template("index_bloom.html")


@app.route("/")
def index():
    return render_template("index.html")


@sock.route('/echo')
def echo(sock):
    while True:
        try:
            lidarData = ser.readline()
            lidarDataSplit = lidarData.decode('utf-8')[0:-1].split('-')
            distance = int(lidarDataSplit[2])
            di.update(float(lidarDataSplit[0]), -float(lidarDataSplit[1]), distance)
            data = {
                'xyz': di.xyz,
                'rgb': f2rgb.to_rgba(distance)[:3],
                'size': (distance - 5) / 495 + 1  # ~normalized from 1<>2
            }
            print(f"running...: {counter.idx * cInv:.2f}%, distance: {distance}")
            sock.send(json.dumps(data))
            counter.update()
        except Exception as e:
            print("error: ", e)
            counter.update()
            pass


if __name__ == "__main__":
    app.run()
