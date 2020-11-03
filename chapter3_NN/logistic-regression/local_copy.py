# -*- coding: utf-8 -*-
"""
@File: local_copy.py
@Author: wenjuan.hu & yongqin.xiao
@Date: 2020/09/04
@Desc: 用于拷贝数据到

History:
2020-10-21  comment the result query from DB
2020-10-29  update according to triage-rib app
2020-10-30  currently assuming the disk free space is big enough to store all the images (3*100G+1*100G)
"""
import os
import datetime
import shutil
import time
import csv
import argparse
import threading
from dcm_reader import DcmReader
from prob_tool import DataQuery

# the max waiting seconds for a study to be completed (now wait for 10 minutes)
MAX_WAITING_SECONDS = 600

# img_event = threading.Event()
#
#
# def thread_copy_and_sort():
#     # copy data from usb drive or D:\temp_data to D:\temp\sort_data
#     # when 5 cases finish, release one semaphore
#     img_event.set()
#
#
# def thread_copy_and_calculate():
#     img_event.wait()


def get_content_from_dict(study_dic, item):
    try:
        return study_dic[item]
    except Exception as e:
        print(e)


def calculate_one_by_one(reader, source_path, target_path, csv_path, study_dic, db_ip):
    # create an empty csv file for writing
    with open(csv_path, 'w', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(['No', 'FolderName', 'StudyUid', 'CopyFinished', 'AlgFinished', 'PerformanceTime(s)',
                        'Probability'])
        f.close()
    study_list = os.listdir(source_path)
    data_query = DataQuery(db_ip)
    for index, study in enumerate(study_list):
        study_path = os.path.join(source_path, study)
        series_list = os.listdir(study_path)
        target_file_path = os.path.join(target_path, study)
        if not os.path.exists(target_file_path):
            os.makedirs(target_file_path)
        if os.path.exists(target_file_path):
            try:
                shutil.rmtree(target_file_path)
            except Exception as e:
                print(e)
        try:
            shutil.copytree(study_path, target_file_path)
            # Here is an option to remove the temp files or not.
            shutil.rmtree(study_path)
        except Exception as e:
            print(e)
        try:
            print('{0}: {1} Study folder copy completed！'.format(index, get_content_from_dict(study_dic, study)))
        except Exception as e:
            print(e)
        copy_finish_time = datetime.datetime.now()
        try:
            wait_count = 0
            while not data_query.is_series_list_alg_finished(series_list):
                time.sleep(1)
                wait_count = wait_count + 1
                if wait_count > MAX_WAITING_SECONDS:
                    reader.write_error_info(
                        "Error: calculation cost more than {0} seconds for series: {1}".format(MAX_WAITING_SECONDS,
                                                                                               series_list))
                    break
        except Exception as e:
            print(e)
        alg_finish_time = datetime.datetime.now()
        print('{0}: {1} Study calculation complete！'.format(index, get_content_from_dict(study_dic, study)))
        for series_uid in series_list:
            probability = 0
            try:
                probability = data_query.select_alg_result_probability(series_uid)
            except Exception as e:
                print(e)
            time_performance = (alg_finish_time - copy_finish_time).seconds
            try:
                with open(csv_path, 'a+', newline='') as f:
                    f_csv = csv.writer(f)
                    f_csv.writerow([index, get_content_from_dict(study_dic, series_uid), series_uid,
                                    copy_finish_time.strftime('%Y-%m-%d '
                                                              '%H:%M:%S'),
                                    alg_finish_time.strftime('%Y-%m-%d %H:%M:%S'), time_performance, probability])
                    f.close()
            except Exception as e:
                print(e)


def main(args):
    source_path = args.source_dir
    temp_path = args.temp_dir
    csv_path = args.record_file
    target_path = r"D:\data"
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)
    print("Data is sorting, please wait!")
    print("Please make sure the disk space of drive D: is enough. 3 times of the total 300 cases.")
    reader = DcmReader()
    reader.output_path = temp_path
    reader.input_path = source_path
    # save files according to the study_id and series_id
    study_dic = reader.dcm_analysis_save()
    print(study_dic)
    print("Start copy data to calculate, please wait!")
    # comment for rib test
    calculate_one_by_one(reader, temp_path, target_path, csv_path, study_dic, args.db_address)
    print("The result file path is：", csv_path)
    print("Data calculation has been completed!")


if __name__ == '__main__':
    long_description = 'Copy images from source_dir to the calculation directory'
    parser = argparse.ArgumentParser(description=long_description)
    parser.add_argument('-s', '--source_dir',
                        default=r"D:\temp_data",
                        help='data source dir')

    parser.add_argument('-t', '--temp_dir',
                        default=r"D:\temp\sort_data",
                        help='temp dir for the data to be sorted')

    parser.add_argument('-r', '--record_file',
                        default=r"D:\temp\result.csv",
                        help='The result to be recorded')

    parser.add_argument('-a', '--db_address',
                        default="localhost",
                        help='The ip address of the database. This is for test only.')
    arg = parser.parse_args()
    main(arg)

# end of the script
