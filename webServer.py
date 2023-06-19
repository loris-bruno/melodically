from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
from musicModule import make_song, setSounds
from camModule import capture_camera
from gpio import GPIOThread
import os


app = Flask(__name__)
socketio = SocketIO(app)

# get the sound names form the directory
sounds = next(os.walk('./sounds'))[1]

sound = sounds[0] # selected sound
setSounds(sound)

imageName = 'frame.jpg'

playing = False

@socketio.on('connect')
def connect():
    global playing
    emit('playing', playing)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
     'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/start', methods = ['POST'])
def start_experience():
    global playing
    global imageName
    
    if not playing:
        print("start playing")
        playing = True
        socketio.emit('playing', playing)
        capture_camera(imageName)
        result = make_song(imageName)
        socketio.emit('result', result)
        playing = False
        socketio.emit('playing', playing)
    else:
        print("busy!")
    return ""

@app.route('/setsounds', methods = ['POST'])
def set_sounds():
    global sound
    newSounds = request.form['sound']
    sound = newSounds
    print(newSounds)

    setSounds(newSounds)
    return newSounds


@app.route('/')
def index():
    global sound
    templateData = {
      'title' : 'Music!',
      'sounds' : sounds,
      'selectedSound': sound
    }
    print("index")
    return render_template('index.html', **templateData)

buttonThread = GPIOThread(start_experience)
buttonThread.start()



if __name__ == '__main__':
    app.run(debug=False, port=5000, host='0.0.0.0')
