# -*- coding: utf-8 -*-
"""
Outputs the frequency of each word that occurs in an .srt file to a .csv file.

usage:
python srt_freqs.py filepath.srt
python srt_freqs.py folderpath

"""
import sys
import glob
from bs4 import BeautifulSoup
import pysrt
import csv
import os
import numpy as np

if len(sys.argv) != 2:
    print('Usage:\npython srt_freqs.py filepath.srt\npython srt_freqs.py folderpath')
    exit()

input_arg = sys.argv[1]
if input_arg[-4:] == '.srt':
    target_files = [input_arg]
else:
    all_files = glob.glob("{}/*".format(input_arg))
    target_files = []
    srt_names = []
    for file in all_files:
        if file[-4:] == '.srt':
            target_files.append(file)
            temp_string = r'{}'.format(file)
            srt_name = temp_string.split('\\')[-1]
            srt_names.append(srt_name)
    if len(target_files) == 0:
        raise FileNotFoundError("No files found in folder '{}'. Include '.srt' extension to analyse individual file.".format(input_arg))

output_file = 'srt_frequencies.csv'  # should be a .csv file


def get_SD(numbers_list, p_or_s):
    # note:
    # 'p' gives population SD
    # 's' gives sample SD
    # if not defined, sample SD is default
    distancesSqSum = float(0)
    M = sum(numbers_list) / len(numbers_list)
    for i in numbers_list:
        distanceSq = (i - M) ** 2
        distancesSqSum += distanceSq
    pVariance = distancesSqSum / len(numbers_list)
    sVariance = distancesSqSum / (len(numbers_list) - 1)
    pSD = np.sqrt(pVariance)
    sSD = np.sqrt(sVariance)
    if p_or_s.lower() == 'p':
        return pSD
    else:
        return sSD


def process_srt(srt_file):
    subs = pysrt.open(srt_file)
    global total_subs_count
    total_subs_count += len(subs)
    if len(subs) == 0:
        return
    # parse to find words
    full_list = []
    for x in range (0, len(subs)):
        # remove html (italic, bold, etc.)
        line = BeautifulSoup(subs[x].text, 'html.parser').text
        for word in line.split():
            # remove punctuation (note, will not support numbers, e.g. '126' not processed and '3rd' becomes 'rd'
            while word:
                if not word[-1:].isalpha():
                    word = word[:-1]
                if not word[:1].isalpha():
                    word = word[1:]
                if word[:1].isalpha() and word[-1:].isalpha():
                    break
            # add word to list
            if word:
                full_list.append(word.lower())
        percent_done = (x / len(subs)) * 100
        print('  parsing... {0}%\r'.format(round(percent_done)), end = '')
    # add len(full_list) to the word count
    global word_count
    word_count += len(full_list)
    # count instances of each word
    dupeless_list = list(set(full_list))
    reps_counts = []
    reps_fpmw = []
    reps_zipf = []
    for word in dupeless_list:
        global instances
        global file_word_dict
        reps_counts.append(full_list.count(word))
        word_fpmw = (full_list.count(word)/len(full_list)) * 1000000
        reps_fpmw.append(word_fpmw)
        reps_zipf.append(np.log10(word_fpmw)+3)
        file_word_ref = '{0}_{1}'.format(srt_file, word)
        if word in instances:
            instances[word] += full_list.count(word)
        else:
            instances[word] = full_list.count(word)
        if file_word_ref in file_word_dict:
            file_word_dict[file_word_ref] += full_list.count(word)
        else:
            file_word_dict[file_word_ref] = full_list.count(word)
        percent_done = (dupeless_list.index(word) / len(dupeless_list)) * 100
        print('  analysing... {0}%\r'.format(round(percent_done)), end = '')
    global file_words_count
    file_words_count[srt_file] = len(full_list)
    print('                                \r', end = '')
    print(' -{0} subtitles'.format(len(subs)))
    print(' -{0} total words'.format(len(full_list)))
    print(' -{0} unique words'.format(len(dupeless_list)))
    mean_reps = sum(reps_counts) / len(reps_counts)
    SD = get_SD(reps_counts, "s")
    print(' -M frequency = {0} (SD = {1})'.format(round(mean_reps, 2), round(SD, 2)))
    mean_fpmw = sum(reps_fpmw) / len(reps_fpmw)
    SD = get_SD(reps_fpmw, "s")
    print(' -M fpmw = {0} (SD = {1})'.format(round(mean_fpmw, 2), round(SD, 2)))
    mean_zipf = sum(reps_zipf) / len(reps_zipf)
    SD = get_SD(reps_zipf, "s")
    print(' -M zipf = {0} (SD = {1})'.format(round(mean_zipf, 2), round(SD, 2)))

instances = {}
file_counter = 0
word_count = 0
non_srt_error = []
total_subs_count = 0
file_word_dict = {}
file_words_count = {}
if len(target_files) > 1:
    print("{0} .srt files found in folder '{1}'...".format(len(target_files), input_arg))
for file in target_files:
    file_counter += 1
    print("File {0}/{1}: '{2}'".format(file_counter, len(target_files), file))
    try:
        process_srt(file)
    except:
        print(' -ERROR: Could not process as .srt format?')
        non_srt_error.append(file)

print('Summary:')
# sort on frequency into list with tuples of (word, freq)
sorted_instances = [(k, instances[k]) for k in sorted(instances, key=instances.get, reverse=True)]
print(' -{0}/{1} files successfully processed'.format(len(target_files) - len(non_srt_error), len(target_files)))
print(' -{0} subtitles'.format(total_subs_count))
print(' -{0} total words'.format(word_count))
print(' -{0} unique words'.format(len(instances)))
reps_counts = []
reps_fpmw = []
reps_zipf = []
for word in sorted_instances:
    word_reps = word[1]
    reps_counts.append(word_reps)
    word_fpmw = (word[1] / word_count) * 1000000
    reps_fpmw.append(word_fpmw)
    reps_zipf.append(np.log10(word_fpmw) + 3)
mean_reps = sum(reps_counts) / len(reps_counts)
SD = get_SD(reps_counts, 's')
print(' -M frequency = {0} (SD = {1})'.format(round(mean_reps, 2), round(SD, 2)))
mean_fpmw = sum(reps_fpmw) / len(reps_fpmw)
SD = get_SD(reps_fpmw, "s")
print(' -M fpmw = {0} (SD = {1})'.format(round(mean_fpmw, 2), round(SD, 2)))
mean_zipf = sum(reps_zipf) / len(reps_zipf)
SD = get_SD(reps_zipf, "s")
print(' -M zipf = {0} (SD = {1})'.format(round(mean_zipf, 2), round(SD, 2)))


# print details on file-processing errors
if len(non_srt_error) != 0:
    print(' -Could not process the following {} files as .srt (check they are in unicode format?):'.format(len(non_srt_error)))
    for each in non_srt_error:
        print("   '{}'".format(each))


# find zipf values from zipf freqs file for comparison & domPoS classification
# location of zipfFreqs.csv
# (columns should be: Spelling, nchar, LogFreq_Zipf, DomPoS)
freqsCsvLoc='zipfFreqs.csv'
# prevents headers from being processed (e.g. prevents processing LogFreq_Zipf as float)
csvHasHeaders=True
# zipf data import
print('SUBTLEX-UK word frequency data from {0}:'.format(freqsCsvLoc))
try:
  reader = csv.reader(open(freqsCsvLoc))
  dataDict = {}
  csvIter=0
  for row in reader:
    if csvHasHeaders:
      if csvIter==0:
        pass
    if not csvHasHeaders or csvIter!=0:
        key = row[0].lower()
        if key in dataDict:
            # implement any duplicate row handling here. (May also want to do csvIter-=1 here)
          pass
        dataDict[key]=row[1:]
    csvIter+=1
    print('  importing... {0} entries\r'.format(csvIter), end = '')
  print('                                    \r', end = '')
  print(' -imported {0} entries'.format(len(dataDict)))
  includeZipf = True
except:
  print(" -Couldn't import from '{0}'. Will analyse without SUBTLEX-UK data.".format(freqsCsvLoc))
  includeZipf = False


# save as csv
print("Output to '{0}':".format(output_file))
# headings
with open(output_file, 'w', newline='') as csvfile:
    dataexporter = csv.writer(csvfile, delimiter=',')
    csvHeadings = ['Word', 'Len', 'N', 'Proportion', 'Fpmw', 'Zipf']
    if includeZipf == True:
        csvHeadings.extend(['SubtlexukProportion', 'SubtlexukFpmw', 'SubtlexukZipf', 'SubtlexukDomPoS'])
    if len(target_files) > 1:
        for file in srt_names:
            csvHeadings.append('{}_N'.format(file))
        for file in srt_names:
            csvHeadings.append('{}_Fpmw'.format(file))
        for file in srt_names:
            csvHeadings.append('{}_Zipf'.format(file))
    dataexporter.writerow(csvHeadings)
# rows
with open(output_file, 'a', newline='') as csvfile:
    dataexporter = csv.writer(csvfile, delimiter=',')
    for item in sorted_instances:
        fpmw = item[1] / word_count * 1000000
        csvRowList = [item[0], len(item[0]), item[1], item[1] / word_count, fpmw, np.log10(fpmw) + 3]
        # zipf data
        if includeZipf == True:
            try:
                target_word = item[0]
                zipf = float("".join(dataDict[target_word][1:2]))
                domPoS = str("".join(dataDict[target_word][2:3]))
                fpmw = 10**(zipf-3)
                proportion = fpmw/1000000
            except KeyError:
                zipf = 'NA'
                domPoS = 'NA'
                fpmw = 'NA'
                proportion = 'NA'
            csvRowList.extend([proportion, fpmw, zipf, domPoS])
        # frequency per file
        if len(target_files) > 1:
            # N
            for file in target_files:
                if file in non_srt_error:
                    csvRowList.append('NA')
                else:
                    file_word_ref = '{0}_{1}'.format(file, item[0])
                    if file_word_ref in file_word_dict:
                        csvRowList.append(file_word_dict[file_word_ref])
                    else:
                        csvRowList.append(0)
            # fpmw
            for file in target_files:
                if file in non_srt_error:
                    csvRowList.append('NA')
                else:
                    file_word_ref = '{0}_{1}'.format(file, item[0])
                    if file_word_ref in file_word_dict:
                        file_fpmw = file_word_dict[file_word_ref] / file_words_count[file] * 1000000
                        csvRowList.append(file_fpmw)
                    else:
                        csvRowList.append(0)
            # zipf
            for file in target_files:
                if file in non_srt_error:
                    csvRowList.append('NA')
                else:
                    file_word_ref = '{0}_{1}'.format(file, item[0])
                    if file_word_ref in file_word_dict:
                        file_fpmw = file_word_dict[file_word_ref] / file_words_count[file] * 1000000
                        file_zipf = np.log10(file_fpmw) + 3
                        csvRowList.append(file_zipf)
                    else:
                        csvRowList.append(0)
        dataexporter.writerow(csvRowList)
        percent_done = (sorted_instances.index(item)/len(sorted_instances)) * 100
        print('  writing... {0}%\r'.format(round(percent_done)), end = '')

print('                    \r', end = '')
print(' -written to file')
print('  opening...\r', end = '')
os.system('start {0}'.format(output_file))
print('                    \r', end = '')
print(' -opened')