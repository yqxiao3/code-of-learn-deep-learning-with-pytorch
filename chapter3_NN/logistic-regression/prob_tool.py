# -*- coding: utf-8 -*-
"""
@File: prob_tool.py
@Author: huiting.jiang & yongqin.xiao
@Date: 2020/09/04
@Desc: query the algorithm detection result from database and calculate the probability

Usage:
    python prob_tool.py -o output_dir -a db_address

Example:
    python prob_tool.py

History:
2020-10-23  init version
2020-10-23  update for triage-rib (xyq)
2020-11-06  update the check condition of algorithm finish and add the an output of the result query from db
2020-11-09  Add a struct to record the calculation result
2020-12-29  Update connection 
"""

import os
import argparse
import pymysql
import csv


class Perf_Obj:
    def __init__(self):
        self.series_uid = ''
        self.alg_status = 1
        self.alg_start = 0
        self.alg_end = 0
        self.alg_count = 0
        self.prob = 0


# class tool to query from database
class DataQuery:
    ip = ""
    port = ""
    user = ""
    password = ""
    database = ""
    db = None
    cursor = None

    def __init__(self, reader, ip, port=3306, user="", password="", database="ai_portal"):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.reader = reader

    def connect(self):
        self.db = pymysql.connect(host=self.ip, port=3306, user="", password="",
                                  database="ai_portal", charset='utf8')
        self.cursor = self.db.cursor()
        return self.db, self.cursor

    def close(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.db:
                self.db.close()
        except Exception as e:
            print(e)

    # check if this series calculation is done
    def is_series_list_alg_finished(self, series_uid_list):
        try:
            is_all_finish = True
            is_finish = None
            self.connect()
            for series_uid in series_uid_list:
                script = 'SELECT AlgStatus FROM tb_series_status WHERE SeriesInstanceUID="{0}";'.format(series_uid)
                self.cursor.execute(script)
                is_finish = self.cursor.fetchone()
                if is_finish is None or is_finish[0] == 0:
                    is_all_finish = False
                    break
            self.close()
            if is_all_finish:
                self.reader.write_error_info("AlgStatus of series: {0} , value={1}".format(series_uid, is_finish))
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    def select_alg_result_probability(self, series_uid):
        self.connect()
        script_prob = "select FindingType,PreFindingType,Probality from tb_finding_ct_rib where SeriesInstanceUID='{0}';".format(
            series_uid)
        script_series = "select AlgStatus, AlgStart,AlgEnd,PerformanceCounter from tb_series_status where SeriesInstanceUID='{0}';".format(
            series_uid)

        self.cursor.execute(script_series)
        result = self.cursor.fetchall()
        if result is None:
            self.reader.write_error_info("No record in tb_series_status for series id: {0};".format(series_uid))
            self.close()
            # if there is no record the probability is 0
            return None
        else:
            # read the info of this series
            obj = Perf_Obj()
            obj.series_uid = series_uid
            obj.alg_status = result[0][0]
            obj.alg_start = result[0][1]
            obj.alg_end = result[0][2]
            obj.alg_count = result[0][3]
            # then read probability from tb_finding_ct_rib
            self.cursor.execute(script_prob)
            result = self.cursor.fetchall()
            if result is None:
                # there is no finding of rib fracture, so the probability is 0
                obj.prob = 0
                self.close()
                return obj
            else:
                prob_list = []
                for row in result:
                    rib_fracture_type = row[0]
                    pre_finding_type = row[1]
                    probability = row[2]
                    if int(pre_finding_type) == 1:
                        # Distinguish between rib fractures and spine fractures
                        if 0 < int(rib_fracture_type) < 4:
                            prob_list.append(probability)
                probability = 0
                if len(prob_list) >= 3:
                    prob_list.sort()
                    if prob_list[-3] > 0.65:
                        probability = prob_list[-3]
                obj.prob = probability
                self.close()
                return obj

    # select needed data from the series table
    def select_alg_result(self):
        self.connect()
        script = "select SeriesInstanceUID,UpdateTime,FindingType,PreFindingType,Probality from tb_finding_ct_rib"
        self.cursor.execute(script)
        result = self.cursor.fetchall()
        if result is None:
            self.close()
            return -1
        else:
            result = list(result)
            self.close()
            return result


# function to calculate the probability from algorithm calculation
def calculate_probability(ipaddress, output_dir):
    # calculate the probability of patient from  rib fracture detected results

    series_uid_list = []  # df_finding["SeriesInstanceUID"].to_list()
    update_time_list = []  # df_finding["UpdateTime"].to_list()
    rib_fracture_type_list = []  # df_finding["FindingType"].to_list()
    prefindingtype_list = []  # df_finding['PreFindingType'].to_list()
    probability_list = []  # df_finding["Probality"].to_list()

    records = DataQuery(ipaddress).select_alg_result()
    if -1 == records:
        print("Fail to read records from database.")
        return
    for row in records:
        series_uid_list.append(row[0])
        update_time_list.append(row[1])
        rib_fracture_type_list.append(row[2])
        prefindingtype_list.append(row[3])
        probability_list.append(row[4])

    # analyze the result
    dict_results = {}
    for idx, uid in enumerate(series_uid_list):
        # print(idx,uid)
        if uid not in dict_results.keys():
            # print("empty",uid)
            dict_results[uid] = []

        if int(prefindingtype_list[idx]) == 1:
            # Distinguish between rib fractures and spine fractures
            if 0 < int(rib_fracture_type_list[idx]) < 4:
                dict_results[uid].append(probability_list[idx])

    # find the proper probability from the detection results of each series
    contents = []
    for idx, uid in enumerate(dict_results.keys()):
        idx_in_csv = series_uid_list.index(uid)
        prob_list = dict_results[uid]
        print(prob_list)
        if len(prob_list) >= 3:
            prob_list.sort()
            if prob_list[-3] > 0.65:
                contents.append([uid, series_uid_list[idx_in_csv], update_time_list[idx_in_csv], prob_list[-3]])
            else:
                contents.append([uid, series_uid_list[idx_in_csv], update_time_list[idx_in_csv], 0])
        else:
            contents.append([uid, series_uid_list[idx_in_csv], update_time_list[idx_in_csv], 0])
    # write probability into csv file
    with open(os.path.join(output_dir, "rib_fracture_probability.csv"), "w") as file:
        writer = csv.writer(file)
        writer.writerow(["SN", "SeriesInstanceUID", "Probability", "UpdateTime"])
        i = 0
        for row in contents:
            i = i + 1
            writer.writerow([i, row[0], row[3], row[2]])
    print('Output csv: ', os.path.join(output_dir, "rib_fracture_probability.csv"))


if __name__ == '__main__':
    long_description = 'Calculate the probability of the patient level'
    parser = argparse.ArgumentParser(description=long_description)
    parser.add_argument('-o', '--output_dir',
                        default='',
                        help='output folder')

    parser.add_argument('-a', '--ipaddress',
                        default='localhost',
                        help='ip address of the database')

    args = parser.parse_args()
    # calculate_probability(args.ipaddress, args.output_dir)
