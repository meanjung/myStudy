import os
import sys
from pathlib import Path
import re
import shutil
import pandas as pd

class calculateCoverage:
    def exec_objdump(self, filename_fullpath):
        objdump = self.binutils_path + "/objdump"
        try:
            os.system(f"{objdump} -x {filename_fullpath} > /dev/null 2>&1")
            print("[*] objdump executed")
            return
        except Exception as e:
            print("[exec objdump ERROR]\n", e)
            sys.exit()
    def exec_lcov(self):
            try:
                os.system(f"lcov --rc lcov_branch_coverage=1 --capture --directory {self.binutils_path}\
                    --output-file {self.binutils_path}/objdump.info > /dev/null 2>&1")
                print("[*] lcov executed - created objdump.info")
                return
            except Exception as e:
                print("[exec lcov ERROR]\n", e)
                sys.exit()
    def exec_genhtml(self):
        try:
            os.system(f"genhtml {self.binutils_path}/objdump.info --branch-coverage --output-directory \
                {self.binutils_path}/output > /dev/null 2>&1")
            print("[*] genhtml executed - created output directory")
            return
        except Exception as e:
            print("[exec genhtml ERROR]\n")
            sys.exit()
    def get_start_time(self):
        with open(f"{self.exp_result_path}/fuzzer_stats", "r") as f:
            for line in f.readlines():
                if "start_time" in line:
                    start_time = int(line.split(":")[-1])
                    break
            print(f"[*] start_time : {start_time}")
            return start_time
    def get_coverage(self):
        index_html_path = self.binutils_path + "/output/index.html"
        percentages = []
        with open(index_html_path, "r") as f:
            for line in f.readlines():
                if "headerCovTableEntryLo" in line:
                    percentages.extend(re.findall("\d+\.\d+", line.strip()))
                else:
                    continue
        coverage_dict = {"lines":percentages[0], "functions":percentages[1], "branches":percentages[2]}
        print("[**] coverage : ", coverage_dict)
        return coverage_dict
    def clear_after_one_loop(self):
        objdump_info_path = self.binutils_path+"/objdump.info"
        genhtml_output_path = self.binutils_path+"/output"
        if os.path.exists(objdump_info_path):
            os.remove(objdump_info_path)
            print(f"[*] deleted objdump.info")
        else:
            print("[*] No objdump.info to delete")
        if os.path.exists(genhtml_output_path):
            shutil.rmtree(genhtml_output_path)
            print("[*] deleted genhtml_output directory")
        else:
            print("[*] No genhtml_output directory to delete")
        return
    def execute(self):
        exp_start_time = self.get_start_time()
        self.allFiles_path = self.exp_result_path + "/allFiles/"
        paths = sorted(Path(self.allFiles_path).iterdir(), key=os.path.getmtime)
        for p in paths:
            filename_fullpath = str(p)
            filename = str(p.name)
            file_mtime = int(os.path.getmtime(f"{self.allFiles_path}{filename}")) # unix time
            if file_mtime < exp_start_time:
                print("[*] file created before start_time... ignore")
                continue
            print(f"{filename} is executing..")
        
            self.exec_objdump(filename_fullpath)
            self.exec_lcov()
            self.exec_genhtml()
            coverage_result = self.get_coverage()
            coverage = {
                "time":[(file_mtime-exp_start_time)/3600], 
                "coverage":[float(coverage_result["branches"])]
            }
            
            df = pd.DataFrame(coverage)
            if not os.path.exists(self.output_csv_filename):
                df.to_csv(self.output_csv_filename, index=False, mode="w", header=False)
            else:
                df.to_csv(self.output_csv_filename, index=False, mode="a", header=False)
        
            self.clear_after_one_loop()
        return
    
    def __init__(self, exp_result_path: str, binutils_path: str, output_csv_filename: str):
        self.exp_result_path = exp_result_path
        self.binutils_path = binutils_path
        self.output_csv_filename = output_csv_filename
        self.execute()
        

class prepareToStart:
    def mkdir_to_gather(self):
        new_dir = f"{self.exp_result_path}/allFiles"
        if os.path.exists(new_dir):
            print(f'[*] {new_dir} already exists. I will delete it')
            shutil.rmtree(new_dir)
        try:
            os.makedirs(f"{new_dir}")
            print('[*] mkdir \"allFiles\"')
        except Exception as e:
            print("[mkdir ERROR]\n", e)
    def copy_exp_result(self):
        for i in ["crashes", "hangs", "queue"]:
            try:
                os.system(f"cp -p {self.exp_result_path}/{i}/* {self.exp_result_path}/allFiles/ > /dev/null 2>&1")
                print(f"[*] copy files in \"{i}\" to new directory")
            except Exception as e:
                print("[accumulate ERROR]\n", e)
    def clear_to_start(self):
        gcda_file = f"{self.binutils_path}/objdump.gcda"
        objdump_info_path = self.binutils_path+"/objdump.info"
        genhtml_output_path = self.binutils_path+"/output"
        if os.path.exists(gcda_file):
            os.remove(gcda_file)
            print(f"[*] deleted {gcda_file}")
        else:
            print("[*] No objdump.gcda file to delete")
        if os.path.exists(objdump_info_path):
            os.remove(objdump_info_path)
            print(f"[*] deleted objdump.info")
        else:
            print("[*] No objdump.info to delete")
        if os.path.exists(genhtml_output_path):
            shutil.rmtree(genhtml_output_path)
            print("[*] deleted genhtml_output directory")
        else:
            print("[*] No genhtml_output directory to delete")
        return
       
    def __init__(self, exp_result_path: str, binutils_path: str):
        self.exp_result_path = exp_result_path
        self.binutils_path = binutils_path
        
        self.mkdir_to_gather()
        self.copy_exp_result()
        self.clear_to_start()


if __name__ == "__main__":
    exp_result_path = "/path/to/AFL/afl-2.52b/output"
    binutils_path = "/path/to/binutils/binutils_gcov/binutils"
    output_csv_file = "output.csv"
    prepareToStart(exp_result_path, binutils_path)
    calculateCoverage(exp_result_path, binutils_path, output_csv_file)
    