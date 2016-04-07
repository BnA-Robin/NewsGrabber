import threading
import time
import os
import re
import shutil
import time
import random
import string

def processfiles():
	try:
		print('Starting movefiles thread')
		threading.Thread(target = movefiles).start()
		time.sleep(3)
		print('Starting uploader thread')
		threading.Thread(target = uploader).start()
	except:
		pass #for now

def uploader():
	print('Scanning ready folder for warcs')
	for root, dirs, files in os.walk("./ready"):
		for file in files:
			if re.match(r'news', file) and file.endswith(".warc.gz") and not os.path.isfile(os.path.join(root, file) + ".upload"):
				print('Creating .upload file')
				open(os.path.join(root, file) + ".upload", 'a').close()
				print('starting upload folder for file in thread: ' + str(file))
				threading.Thread(target = upload, args = (file,)).start()
				print('upload thread has been started, sleeping for 2 seconds and continueing loop')
				time.sleep(2)

def upload(filename):
	print('Upload function start, reading rsync_target')
	with open('rsync_target', 'r') as file:
		rsync_target = file.read().replace('\n', '').replace('\r', '')
	print('Starting rsync process')
	rsync_exit_code = os.system("rsync -avz --no-o --no-g --progress --remove-source-files ./ready/" + filename + " " + rsync_target)
	print('rsync process returned: ' + str(rsync_exit_code))
	if rsync_exit_code == 0:
		print('File synced successfully to the storage server.')
	else:
		print('Your received exit code ' + str(rsync_exit_code) + ' while syncing file to storage server.')
	if os.path.isfile('./ready/'+ filename + '.upload'):
		print('.upload file exists, removing it now!')
		os.remove('./ready/'+ filename + '.upload')

def check(files, num):
	print('check function: checking files for warc nr:' + str(num))
	for file in files:
		print('checking files in loop, current file: ' + file)
		if file.endswith("0000" + num + ".warc.gz"):
		print('found a match for warc')
			return True
	print('>>> NO MATCH WAS FOUND!!')
	return False

def warcnum(folder):
	count = 0
	for root, dirs, files in os.walk("./" + folder):
		for file in files:
			#print(file)
			if file.endswith(".warc.gz"):
				count += 1
		return count

def movefiles():
	list = []
	done = True
	for folder in next(os.walk('.'))[1]:
		if not (folder == 'services' or folder == 'temp' or folder == 'donefiles'):
			for root, dirs, files in os.walk("./" + folder):
		#		if re.search(r'-[0-9a-z]{8}$', folder):
		#			writehtmllist(folder)
				if (check(files, "0") == False or check(files, "1") == True) and not folder == "ready":
					startnum = "0"
					firstnum = None
					moved = False
					while True:
						if not os.path.isfile("./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz"):
							if firstnum > 0:
								break
						if os.path.isfile("./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz"):
							print('hi')
							if firstnum == None:
								firstnum = int(startnum)
							if not startnum == "0" and not firstnum == int(startnum):
								print(os.path.join(root, folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz"))
								moved = True
								print('moving file ' + "./" + folder + "/" + folder + "-" + (5-len(startnum))*"0" + startnum + ".warc.gz" + ' to ready folder!')
								os.rename(os.path.join(root, folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz"), "./ready/" + folder + "-" + str((5-len(str(int(startnum)-1)))*"0") + str(int(startnum)-1) + ".warc.gz")
						startnum = str(int(startnum) + 1)
						if warcnum(folder) <= 1:
							break
						if warcnum(folder) == 2 and os.path.isfile("./" + folder + "/" + folder + "-meta.warc.gz"):
							break
			if os.path.isfile("./" + folder + "/" + folder + "-meta.warc.gz") and not folder == "ready":
				for root, dirs, files in os.walk("./" + folder):
					for file in files:
						if file.endswith(".warc.gz"):
							list.append("./ready/" + file)
							os.rename(os.path.join(root, file), "./ready/" + file)
					for file in files:
						if file.endswith(".warc.gz") and not os.path.isfile("./ready/" + file):
							print("not done > ./ready/" + file)
							done = False
					if done == True:
						print('this file is done, removing folder!: ' + folder)
						shutil.rmtree("./" + folder)
	for root, dirs, files in os.walk("./ready"):
		for file in files:
			os.rename(os.path.join(root, file), os.path.join(root, re.sub(".*-list(?:-videos)?(?:-immediate)?(?:_temp)?(?:[01]\.[0-9]+)?", "news", file)))
	print("All finished WARCs have been moved.")

def grab_new_lists():
	for new_list in os.listdir('./new_lists'):
		random_string = ''.join(random.choice(string.ascii_lowercase) for num in range(10))
		os.rename('./new_lists/' + new_list, './old_lists/' + new_list + random_string)
		threading.Thread(target = grab_list, args = (new_list + random_string,)).start()

def grab_list(listname):
	videostring = ''
	extraargs = ' --1'
	if '-videos' in listname:
		videostring = '--youtube-dl '
		extraargs = ' --1'
	returned_code = os.system('~/.local/bin/grab-site --input-file ./old_lists/' + listname + ' --level=0 --ua="ArchiveTeam; Googlebot/2.1" --no-sitemaps --concurrency=5' + extraargs + ' --warc-max-size=524288000 --wpull-args="' + videostring + '--no-check-certificate --timeout=300" > /dev/null 2>&1')
	if returned_code != 0:
		os.rename('./old_lists/' + listname, './new_lists/' + listname)

def main():
	if not os.path.isdir('./new_lists'):
		os.makedirs('./new_lists')
	if not os.path.isdir('./old_lists'):
		os.makedirs('./old_lists')
	if not os.path.isfile('rsync_target'):
		raise Exception('Please add a rsync target to file \'rsync_target\'')
	grab_new_lists()
	processfiles()

if __name__ == '__main__':
	main()
