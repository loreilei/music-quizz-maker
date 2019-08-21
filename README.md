# What is it

This script makes use of youtube-dl and ffmpeg to prepare some playlists for music quizz.

It is provided as is, without warranty of working on your system.

# Required modules

It requires Python 3.7. Find the correct version for your OS at https://www.python.org/downloads/release/python-374/.
It also need ffmpeg installed or available as an executable. You can download it at https://ffmpeg.org/download.html#build-windows

This script needs youtube-dl, ffmpeg-python and PyQt5.
To install them do
```bash
pip install --user youtube-dl
pip install --user ffmpeg-python
pip install --user PyQt5
```

# Usage

```bash
python music_quizz_maker.py <your quizz name> <the csv file describing the information to extract>
```

You can do
```bash
python main.py -h
```
for more information about the possible options.

If the script is launched without command line parameters, it will pop a GUI where most of these parameters can be set.

You can specify the ffmpeg executable to use with the `--ffmpeg_exec` option or by setting it in the GUI (useful if ffmpeg is not installed system wide).

# Format of the csv file

Each line must have maximum 3 values, separated by spaces:
- the url to the youtube video
- the starting time
- the duration of the extract

The url is mandatory, the starting time dans the duration are optional, defaulted to 0s and 15s respectively.
The format to use for the starting time and duration field is `HH:MM:SS`, with `HH` being the hours, `MM` the minutes and `SS` the seconds.
See the example file `test.csv`.

# Output

The script will output one OGG VOrbis file contraining the extract per URL.
It also output a basic html file that contains the 'answers', meaning the link to the original youtube video.
It is possible to create a ZIP archive instead of a folder.
It is possible to set where to generate files.