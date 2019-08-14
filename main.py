#!/usr/bin/python

import os
import sys
import csv
import youtube_dl
import ffmpeg
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
import argparse
import shutil

#To log only errors
class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def progress_hook(d):
	pass

def get_title(url):
	ydl_opts = {
	    'format': 'bestaudio/best',
	    'quiet': True,
	}

	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		info = ydl.extract_info(url, download=False)
		return info['title']

def download_video(url,
					output,
					start='00:00:00',
					duration='00:00:15',
					fade_in_start=0,
					fade_in_duration=1,
					fade_out_start=15,
					fade_out_duration=1):
	k = output.rfind(".")
	tmp_output = output[:k] + '_tmp.' + output[k+1:]
	ydl_opts = {
	    'format': 'bestaudio/best',
	    'quiet': True,
	    'outtmpl': tmp_output,
	    'logger': MyLogger(),
	    'progress_hooks': [progress_hook],
	}

	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		ydl.download([url])

	ffmpeg_input = ffmpeg.input(tmp_output, ss=start, t=duration)
	audio = ffmpeg_input.audio.filter("afade", type='in', start_time=fade_in_start, duration=fade_in_duration)
	audio = audio.filter("afade", type='out', start_time=fade_out_start, duration=fade_out_duration)
	out = ffmpeg.output(audio, filename = output, format='ogg')
	out.run(quiet=True, overwrite_output=True)

	if(os.path.exists(tmp_output)):
		os.system('rm {0}'.format(tmp_output))

def seconds(duration):
	splitted = duration.split(':')
	hours = int(splitted[0])
	mins = int(splitted[1])
	secs = int(splitted[2])
	seconds = int(hours * 3600 + mins * 60 + secs)
	return seconds

def make_blind_test(name, extracts):
	if(not os.path.exists(name)):
		os.mkdir(name)

	def download_and_get_answer(name, n, url, start, duration):
		download_video(	url=url,
						output='./{0}/extract_{1}.ogg'.format(name, n),
						start=start,
						duration=duration,
						fade_out_start=seconds(duration)-1)
		return '<li>Extract {0}: <a href="{2}">{1}</a></li>'.format(n, get_title(url), url)

	futures = []
	future_names = dict()
	with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
		for i in range(len(extracts)):
			extract=extracts[i]
			future = executor.submit(download_and_get_answer, name,
																i+1,
																extract['url'],
																extract['start'],
																extract['duration'])
			future_names[future] = 'Extract {}'.format(i+1)
			futures.append(future)

	answers_html = []
	for future in as_completed(futures):
		answers_html.append(future.result())
		print('{} completed'.format(future_names[future]))

	answers_html.sort(key=lambda extract: int(extract[extract.find(' '):extract.find(':')]))

	answers_file=open('{}/answers.html'.format(name), 'w+')
	answers_file.write('<body><ul>')
	answers_file.write(''.join(answers_html))
	answers_file.write('</body></ul>')
	answers_file.close()

def csv_to_extracts_list(csv_file_path):
	extracts=[]
	with open(csv_file_path) as csvfile:
		readCSV = csv.reader(csvfile, delimiter=' ')
		for row in readCSV:
			extract=dict()
			extract['url']=str(row[0])
			try:
				extract['start']=str(row[1])
				if(not extract['start']):
					raise 'Empty start' 
			except:
				extract['start']='00:00:00'
			try:
				extract['duration']=str(row[2])
				if(not extract['duration']):
					raise 'Empty duration' 
			except:
				extract['duration']='00:00:15'
			extracts.append(extract)
	return extracts


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('quizz_name')
	parser.add_argument('extracts_file')
	parser.add_argument('--zip', help='Zip resulting files', action='store_true')
	args = parser.parse_args()

	extracts=csv_to_extracts_list(args.extracts_file)
	make_blind_test(name=args.quizz_name, extracts=extracts)
	if(args.zip):
		shutil.make_archive(args.quizz_name, 'zip', base_dir=args.quizz_name)

if __name__== "__main__":
	main()