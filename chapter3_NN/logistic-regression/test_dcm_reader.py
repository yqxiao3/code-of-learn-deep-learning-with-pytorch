# -*- coding: utf-8 -*-
"""
@File: dcm_reader.py
@Author: wenjuan.hu & yongqin.xiao
@Date: 2020/06/11
@Desc: 1.修改dcm图片的tag值（增、删、改）
       2.归档dcm图片数据（归档为3层结构study/series/image）

2020-11-03 only copy one dcm file to the target folder
"""
import os
import pydicom
import datetime


class DcmReader:
    output_path = None
    input_path = None

    def __init__(self):
        self.dcm_tag = {'StudyInstanceUID': ((0x0020, 0x000D), 'UI'),
                        'SeriesInstanceUID': ((0x0020, 0x000E), 'UI'),
                        'SOPInstanceUID': ((0x0008, 0x0018), 'UI'),
                        'PatientID': ((0x0010, 0x0020), 'UI'),
                        'Modality': ((0x0008, 0x0060), 'CS'),
                        'PatientName': ((0x0010, 0x0010), 'PN'),
                        'Manufacturer': ((0x0008, 0x0070), 'LO'),
                        'InstitutionName': ((0x0008, 0x0080), 'LO'),
                        'SliceThickness': ((0x0018, 0x0050), 'DS'),
                        'InstanceNumber': ((0x0020, 0x0013), 'IS'),
                        'StudyDate': ((0x0008, 0x0020), 'DA'),
                        'SeriesDate': ((0x0008, 0x0021), 'DA'),
                        'AcquisitionDate': ((0x0008, 0x0022), 'DA'),
                        'StudyTime': ((0x0008, 0x0030), 'TM'),
                        'SeriesTime': ((0x0008, 0x0031), 'TM'),
                        'AcquisitionTime': ((0x0008, 0x0032), 'TM'),
                        'AccessionNumber': ((0x0008, 0x0050), 'SH'),
                        'PatientSex': ((0x0010, 0x0040), 'CS'),
                        'SeriesDescription': ((0x0008, 0x103E), 'LO'),
                        'StudyDescription': ((0x0008, 0x1030), 'LO'),
                        'BodyPartExamined': ((0x0018, 0x0015), 'CS'),
                        'ProtocolName': ((0x0018, 0x1030), 'LO'),
                        'PhotometricInterpretation': ((0x0028, 0x0004), 'CS'),
                        'ManufacturerModelName': ((0x0008, 0x1090), 'LO'),
                        'PerformedProcedureStepDescription': ((0x0040, 0x0254), 'LO'),
                        'StudyID': ((0x0020, 0x0010), 'SH'),
                        'PatientAge': ((0x0010, 0x1010), 'AS')
                        }

    def list_series_path(self, input_path, series_path_list):
        """
        获取input_path中的序列路径列表
        Args:
            input_path: 图像文件夹
            series_path_list: input_path中的序列路径列表

        Returns:
            series_path_list: input_path中的序列路径列表

        """
        try:
            if len(os.listdir(input_path)) == 0:
                return
            # make sure all files from one series should put to one folder
            temp_list = os.listdir(input_path)
            temp_list.sort()
            for item in temp_list:
                if os.path.isfile(os.path.join(input_path, item)):
                    series_path_list.append(input_path)
                    print(input_path)
                    break
                else:
                    new_dir = os.path.join(input_path, item)
                    if len(series_path_list) < 10:
                        self.list_series_path(new_dir, series_path_list)
            return series_path_list
        except Exception as e:
            self.write_error_info(str(e))
            return

    def list_study_path(self):
        study_path_list = []
        series_path_list = []
        self.list_series_path(self.input_path, series_path_list)
        for series_path in series_path_list:
            study_path_list.append(os.path.split(series_path)[0])
        print("study path list:")
        study_path_list = list(set(study_path_list))
        print(study_path_list)
        return study_path_list

    # save the images to the output_path with its study_uid, series_uid and instance_uid as path and name
    # return 0  success
    # return -1 error happen
    def _save_dcm(self, dcm, id_list):
        dcm_info = {'study_id': dcm.StudyInstanceUID, 'series_id': dcm.SeriesInstanceUID,
                    'instance_id': dcm.SOPInstanceUID}
        study_dir = os.path.join(self.output_path, dcm_info['study_id'])
        series_dir = os.path.join(study_dir, dcm_info['series_id'])
        file_dir = os.path.join(series_dir, dcm_info['instance_id'] + '.dcm')
        id_list["study_id"] = dcm_info['study_id']
        id_list["series_id"] = dcm_info['series_id']
        id_list["study_path"] = study_dir
        id_list["series_path"] = series_dir
        if not os.path.exists(series_dir):
            os.makedirs(series_dir)
        try:
            dcm.save_as(file_dir)
        except Exception as e:
            print(e)
            return -1
        return 0

    def dcm_analysis_save(self):
        study_dic = {}
        series_path_list = []
        series_path_list = self.list_series_path(self.input_path, series_path_list)
        count = len(series_path_list)

        for index, series_path in enumerate(series_path_list):
            study_id = None
            series_id = None
            id_list = {}
            for img_name in os.listdir(series_path):
                img_path = os.path.join(series_path, img_name)
                try:
                    dcm = pydicom.read_file(img_path)
                    if 0 == self._save_dcm(dcm, id_list):
                        if study_id is None:
                            study_id = id_list["study_id"]
                            series_id = id_list["series_id"]
                            study_dic[study_id] = series_path
                            study_dic[series_id] = series_path
                        else:
                            if study_id != id_list["study_id"]:
                                study_id = id_list["study_id"]
                                study_dic[study_id] = series_path
                                self.write_error_info("Different study_id for the same series {0}.".format(img_path))
                            if series_id != id_list["series_id"]:
                                series_id = id_list["series_id"]
                                study_dic[series_id] = series_path
                                self.write_error_info("Different series_id for the same series {0}.".format(img_path))
                        # only copy one dcm file to the target folder
                        break
                    else:
                        self.write_error_info("Fail to re-save dcm file: {0}".format(img_path))
                except Exception as e:
                    print(e)
            print(str(index + 1) + '/' + str(count))
        return study_dic

    # write the error information of dicom files analysis
    def write_error_info(self, description):
        try:
            print(description)
            if not os.path.exists(r"D:\UAI_Log"):
                os.makedirs(r"D:\UAI_Log")
            with open(os.path.join(r"D:\UAI_Log", "DicomFile_Analysis_Error_{0}_{1}.log").format(
                    datetime.datetime.now().month, datetime.datetime.now().day), "a+") as f:
                f.write("{0} : {1}\n".format(datetime.datetime.now(), description))
                f.close()
        except Exception as e:
            print(e)

