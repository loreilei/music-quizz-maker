#What is it

This script makes use of youtube-dl and ffmpeg to prepare some playlists for music quizz.

You need to have a youtube-dl installed and ffmpeg for it to work.

It is provided as is, without warranty of working on your system.

#Usage

```bash
python main.rb <your quizz name> <the csv file describing the information to extract>
```

#Format of the csv file

Each line must have maximum 3 values, separated by spaces:
- the url to the youtube video
- the starting time
- the duration of the extract

The url is mandatory, the starting time dans the duration are optional, defaulted to 0s and 15s respectively.
The format to use for the starting time and duration field is `HH:MM:SS`, with `HH` being the hours, `MM` the minutes and `SS` the seconds.
See the example file `test.csv`.

#Output

The script will output one OGG VOrbis file contraining the extract per URL.
It also output a basic html file that contains the 'answers', meaning the link to the original youtube video.