# -*- coding: utf-8 -*-
"""
@File: prob_tool.py
@Author: huiting.jiang & yongqin.xiao
@Date: 2020/09/04
@Desc: query the algorithm detection result from database and calculate the posibility

Usage:
    python prob_tool.py -o output_dir -a serveraddress

Example:
    python prob_tool.py
    
    #after the execution the file rib_fracture_probability1.csv will be created in the current folder.
History:
2020-10-23  init version
2020-10-23  update for triage-rib (xyq)
"""

import os
import argparse
import pymysql
import csv


# class tool to query from database
class DataQuery:
    ip = ""
    port = ""
    user = ""
    password = ""
    database = ""
    db = None
    cursor = None

    def __init__(self, ip, port=3306, user="root", password="Uii!20171120", database="ai_portal"):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def connect(self):
        self.db = pymysql.connect(host=self.ip, port=3306, user="root", password="Uii!20171120",
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
        self.connect()
        for series_uid in series_uid_list:
            script = 'SELECT AlgStatus FROM tb_series_status WHERE SeriesInstanceUID="{0}";'.format(series_uid)
            self.cursor.execute(script)
            is_finish = self.cursor.fetchone()
            if is_finish is None or is_finish[0] == 0:
                self.close()
                return False
        self.close()
        return True

    def select_alg_result_probability(self, series_uid):
        self.connect()
        script = "select FindingType,PreFindingType,Probality from tb_finding_ct_rib where SeriesInstanceUID='{0}';".format(
            series_uid)
        self.cursor.execute(script)
        result = self.cursor.fetchall()
        if result is None:
            self.close()
            # if there is no record the probability is 0
            return 0
        else:
            prob_list = []
            for row in result:
                rib_fracture_type = row[0]
                prefinding_type = row[1]
                probability = row[2]
                if int(prefinding_type) == 1:
                    # Distinguish between rib fractures and spine fractures
                    if 0 < int(rib_fracture_type) < 4:
                        prob_list.append(probability)
            probability = 0
            if len(prob_list) >= 3:
                prob_list.sort()
                if prob_list[-3] > 0.65:
                    probability = prob_list[-3]

            self.close()
            return probability

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
