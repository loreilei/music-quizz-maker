#!/usr/bin/python

import os
import sys
import csv

def get_title(url):
	return os.popen('youtube-dl -e {0}'.format(url)).read().rstrip()

def download_video(url,
					output,
					start='00:00:00',
					duration='00:00:15',
					fade_in_start=0,
					fade_in_duration=1,
					fade_out_start=15,
					fade_out_duration=1):
	dl_command = 'youtube-dl -q {0} -f bestaudio -o {1}_tmp'.format(url, output)
	print(dl_command)
	os.system(dl_command)
	audio_convert_command = 'ffmpeg -nostats -loglevel 0 -ss {1} -i {0}_tmp -t {2} -vn -af \'afade=in:st={3}:d={4},afade=out:st={5}:d={6}\' -y {0}'.format(
		output,
		start,
		duration,
		fade_in_start,
		fade_in_duration,
		fade_out_start,
		fade_out_duration
		)
	print(audio_convert_command)
	os.system(audio_convert_command)
	if(os.path.exists('{0}_tmp'.format(output))):
		os.system('rm {0}_tmp'.format(output))

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

	answers_file=open('{}/answers.html'.format(name), 'w+')
	answers_file.write('<body><ul>')

	for i in range(len(extracts)):
		extract=extracts[i]
		download_video(	url=extract['url'],
						output='./{0}/extract_{1}.ogg'.format(name, i+1),
						start=extract['start'],
						duration=extract['duration'],
						fade_out_start=seconds(extract['duration'])-1)
		answers_file.write('<li>Extract {0}: <a href="{2}">{1}</a></li>'.format(i+1, get_title(url=extract['url']), extract['url']))

	answers_file.write('</body></ul>')
	answers_file.close()

def csv_to_extracts_list(csv_file_path):
	extracts=[]
	with open(csv_file_path) as csvfile:
		readCSV = csv.reader(csvfile, delimiter=',')
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
	if(len(sys.argv) > 2):
		extracts=csv_to_extracts_list(sys.argv[2])
		make_blind_test(name=sys.argv[1], extracts=extracts)
	else:
		print("Please provide the URL list file and name of blind test.")

if __name__== "__main__":
	main()