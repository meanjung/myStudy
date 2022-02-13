import os
import sys
from pathlib import Path
import re
import shutil
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# import subprocess

## mkdir new directory for all files
def mkdir_allFiles(output_dir_path):
    newDir = f"{output_dir_path}/allFiles"
    if os.path.exists(newDir):
        print(f'[*] {newDir} already exists. I will delete it')
        shutil.rmtree(newDir)
    try:
        os.makedirs(f"{newDir}") # if already exists -> just go on
        print('[*] mkdir \"allFiles\"')
    except Exception as e:
        print("[mkdir ERROR]\n", e)
        # sys.exit()


def arrange_for_start(binutils_dir_path):
    gcda_file = f"{binutils_dir_path}/objdump.gcda"
    if os.path.exists(gcda_file):
        os.remove(gcda_file)
        print(f"[*] deleted {gcda_file}")
    else:
        print("[*] No objdump.gcda file to delete")
    clear(binutils_dir_path)

        

## copy together
def copy_to_allFiles(output_dir_path):
    for i in ["crashes", "hangs", "queue"]:
        dir_path = output_dir_path + "/" + i
        try:
            os.system(f"cp -p {dir_path}/* {output_dir_path}/allFiles/ > /dev/null 2>&1")
            # retcode = subprocess.Popen(f"cp -p {dir_path}/* {output_dir_path}/allFiles/", 
            #                            shell=True,
            #                            stdout=subprocess.DEVNULL,
            #                            stderr=subprocess.STDOUT)
            # ret = retcode.communicate()
            print(f"[*] copy {i} files to new directory")
        except Exception as e:
            print("[accumulate ERROR]\n", e)
            # sys.exit()

## get start time from fuzzer_stats
def get_start_time(output_dir_path):
    with open(f"{output_dir_path}/fuzzer_stats", "r") as f:
        for line in f.readlines():
            if "start_time" in line:
                start_time = int(line.split(":")[-1])
                break
        print(f"[*] start_time : {start_time}")
        return start_time

## get all files + sort by mtime
def execute(output_dir_path, binutils_dir_path):
    start_time = get_start_time(output_dir_path) # 실험 시작 시간
    dir_path = output_dir_path + "/allFiles/"
    paths = sorted(Path(dir_path).iterdir(), key=os.path.getmtime) # sorted by mtime
    x_time = []
    y_coverage = []
    for p in paths:
        filename_fullpath = str(p)
        filename = str(p.name)
        mtime = int(os.path.getmtime(f"{dir_path}{filename}")) # unix time
        if mtime < start_time:
            print("[*] file created before start_time... ignore")
            continue
        
        print(f"{filename} is executing..")
        
        # objdump 실행
        exec_objdump(filename_fullpath, binutils_dir_path)
        
        # lcov
        exec_lcov(binutils_dir_path)
        
        # genhtml
        exec_genhtml(binutils_dir_path)
        
        # 파싱
        coverage_result = get_coverage(binutils_dir_path)
        
        # # x좌표, y좌표 모으기
        # x_time.append((mtime-start_time)/3600)
        # y_coverage.append(float(coverage_result["branches"]))
        
        # save to csv
        cov = {
            "time":[(mtime-start_time)/3600], 
            "coverage":[float(coverage_result["branches"])]
        }
        df = pd.DataFrame(cov)
        if not os.path.exists('output.csv'):
            df.to_csv('output.csv', index=False, mode="w", header=False)
        else:
            df.to_csv('output.csv', index=False, mode="a", header=False)
    
        clear(binutils_dir_path)
    
    return x_time, y_coverage
        
        
def exec_objdump(filename_fullpath, binutils_dir_path):
    objdump = binutils_dir_path + "/objdump"
    try:
        os.system(f"{objdump} -x {filename_fullpath} > /dev/null 2>&1")
        # retcode = subprocess.Popen(f"{objdump} -x {filename_fullpath}",
        #                                 shell=True,
        #                                 stdout=subprocess.DEVNULL,
        #                                 stderr=subprocess.STDOUT)
        # ret = retcode.communicate()
        print("[*] objdump executed")
        return
    except Exception as e:
        print("[exec objdump ERROR]\n", e)
        sys.exit()

def exec_lcov(binutils_dir_path):
    try:
        os.system(f"lcov --rc lcov_branch_coverage=1 --capture --directory {binutils_dir_path} --output-file {binutils_dir_path}/objdump.info > /dev/null 2>&1")
        # retcode = subprocess.Popen(f"lcov --rc lcov_branch_coverage=1 --capture --directory {binutils_dir_path} --output-file {binutils_dir_path}/objdump.info",
        #                                 shell=True,
        #                                 stdout=subprocess.DEVNULL,
        #                                 stderr=subprocess.STDOUT)
        # ret = retcode.communicate()
        print("[*] lcov executed - created objdump.info")
        return
    except Exception as e:
        print("[exec lcov ERROR]\n", e)
        sys.exit()

def exec_genhtml(binutils_dir_path):
    try:
        os.system(f"genhtml {binutils_dir_path}/objdump.info --branch-coverage --output-directory {binutils_dir_path}/output > /dev/null 2>&1")
        # retcode = subprocess.Popen(f"genhtml {binutils_dir_path}/objdump.info --branch-coverage --output-directory {binutils_dir_path}/output",
        #                                 stdout=subprocess.DEVNULL,
        #                                 stderr=subprocess.STDOUT)
        # ret = retcode.communicate()
        print("[*] genhtml executed - created output directory")
        return
    except Exception as e:
        print("[exec genhtml ERROR]\n")
        sys.exit()

def get_coverage(binutils_dir_path):
    index_html_path = binutils_dir_path + "/output/index.html"
    percentages = []
    with open(index_html_path, "r") as f:
        for line in f.readlines():
            if "headerCovTableEntryLo" in line:
                percentages.extend(re.findall("\d+\.\d+", line.strip()))
            else:
                continue
    coverage_dict = {"lines":percentages[0], "functions":percentages[1], "branches":percentages[2]}
    print("[*] coverage : ", coverage_dict)
    return coverage_dict

def clear(binutils_dir_path):
    objdump_info_path = binutils_dir_path+"/objdump.info"
    genhtml_output = binutils_dir_path+"/output"
    if os.path.exists(objdump_info_path):
        os.remove(objdump_info_path)
        print(f"[*] deleted objdump.info")
    else:
        print("[*] No objdump.info to delete")
        
    if os.path.exists(genhtml_output):
        shutil.rmtree(genhtml_output)
        print("[*] deleted genhtml_output directory")
    else:
        print("[*] No genhtml_output directory to delete")
    return

# def graph(x_time: list, y_coverage: list):
#     plt.xlabel("time")
#     plt.ylabel("branch coverage")
#     plt.plot(x_time, y_coverage)
#     plt.show()
    
    
if __name__ == "__main__":
    # to change
    output_dir_path = "/home/mj/Desktop/AFL/afl-2.52b/default_output"
    binutils_dir_path = "/home/mj/Desktop/binutils/binutils_gcov/binutils"
    
    mkdir_allFiles(output_dir_path) # mkdir new dir to collect
    copy_to_allFiles(output_dir_path) # copy all files to new dir
    arrange_for_start(binutils_dir_path) # prepare to execute objdump
    
    x, y = execute(output_dir_path, binutils_dir_path)
    
    # graph(x, y)
    