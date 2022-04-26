import os
import inspect
import argparse
import re
import json
import platform

parser = argparse.ArgumentParser()
parser.add_argument("project_folder", help="UWP Project folder to scan")
parser.add_argument("template_folder", help="Templates file (JSON)")
parser.add_argument("-o", dest="report_output", default="./ult_scan_report.html", help="Report output file (html)")
args = parser.parse_args()

project_folder = args.project_folder
template_folder = args.template_folder
report_output = args.report_output

final_report_results = {}
templates = []

type_string = "string"
type_list = "list"
type_regex = "regex"

sys_os = str(platform.system()).lower()

if sys_os == "windows":
    file_separator = "\\"
else:
    file_separator = "/"

def get_all_files(dir_name):
    list_of_file = os.listdir(dir_name)
    all_files = list()
    for entry in list_of_file:
        full_path = os.path.join(dir_name, entry)
        if os.path.isdir(full_path):
            all_files = all_files + get_all_files(full_path)
        else:
            all_files.append(full_path)

    return all_files

def check_file(name):
    blocked_extensions = ["gif", "jpeg", "jpg", "mp3", "mpeg", "mpg", "pdf", "pif", "png", "ram", "scr", "snp", "swf", "tif", "wav", "tiff", "css"]

    for extension in blocked_extensions:
        if name.endswith(extension):
            return False

    return True

def get_printable(function, data):
    splited = data.split(function)
    if len(splited) > 1:
        return (splited[0][-44:] + function + splited[1][:44]).replace("\n", "").replace("\r", "")
    else:
        pass

def exception(message, function_name):
    print(function_name + " :: " + str(message))

def save_to_file(data, file_name):
    file = open(file_name, "w")
    file.write(data)
    file.close()

def read_file(name, type):
    try:
        file = open(name, "r", encoding="latin1")
        data = ""
        if type == type_string:
            data = file.read()
        elif type == type_list:
            data = file.readlines()
            for i in range(0, len(data)):
                data[i] = data[i][:-1]
        else:
            exception("Invalid data type", "read_file")
            exit(0)

        return data
    except Exception as error:
        exception(error, inspect.currentframe().f_code.co_name)

def report():
    final_report = '<html><head></head><body><h1 style="text-align: center; color: blue;">Universal Leet Tool</h1><br><br>'


    for template in templates:

        name = template["name"]
        final_report += '<h2 style="color: blue;">' + name + '</h2>'

        if len(final_report_results[name]) > 0:
            for result in final_report_results[name]:
                final_report += result

        final_report += "<br><br>"

    #END
    final_report += "</body></html>"

    save_to_file(final_report, report_output)

    print("\n[DONE] Report Saved: file://" + os.path.realpath(report_output))

def start_string_scan(key, value, file_name, file_data, template_name):
    if type(value) == list:
        for str in value:
            string_scan(key, str, file_name, file_data, template_name)
    else:
        string_scan(key, value, file_name, file_data, template_name)

def string_scan(key, value, file_name, file_data, template_name):
    results = file_data.count(value)

    if results > 0:
        preview = get_printable(value, file_data).replace("<", "&#x3C;").replace(">", "&#x3E;")
        result = '<h>&nbsp;&nbsp;[Found ' + str(results) + ' Function(s)] <b>' + key + '</b> :: <b style="color: red;">' + preview + '</b>... :: <a href="file://' + os.path.abspath(file_name) + '" target="_blank">' + file_name.split(file_separator)[len(file_name.split(file_separator)) - 1] + '</a></h></br>'

        print("[FOUND " + str(file_data.count(value)) + " Function(s)] " + key + " :: " + preview + "... :: " + file_name)

        final_report_results[template_name].append(result)

def regex_scan(key, value, file_name, file_data, template_name):
    results = re.findall(value, file_data)
    if len(results) > 0:
        results[0] = str(results[0])

        preview = results[0][:44].replace("\n", "").replace("\r", "").replace("<", "&#x3C;").replace(">", "&#x3E;")
        result = '<h>&nbsp;&nbsp;[Found ' + str(len(results)) + ' Pattern(s)] <b>' + key + '</b> :: <b style="color: red;">' + preview + '</b>... :: <a href="file://' + os.path.abspath(file_name) + '" target="_blank">' + file_name.split(file_separator)[len(file_name.split(file_separator)) - 1] + '</a></h></br>'

        final_report_results[template_name].append(result)

        print("[FOUND " + str(len(results)) + " Pattern(s)] " + key + " :: " + preview + "... :: " + file_name)

def start_regex_scan(key, value, file_data, file_name, template_name):
    if type(value) == list:
        for regex in value:
            regex_scan(key, regex, file_name, file_data, template_name)
    else:
        regex_scan(key, value, file_name, file_data, template_name)

def scan(file):
    file_data = read_file(file, type_string)

    for template in templates:
        for key, value in template["content"].items():
            if template["type"] == type_string:
                start_string_scan(key, value, file, file_data, template["name"])
            elif template["type"] == type_regex:
                start_regex_scan(key, value, file_data, file, template["name"])

def initialize_templates():
    templates_files = get_all_files(template_folder)

    for file in templates_files:
        if not file.endswith(".json"):
            continue
        template = json.loads(read_file(file, type_string))
        templates.append(template)
        final_report_results.update({template["name"]:[]})

def main():
    initialize_templates()
    files = get_all_files(project_folder)

    for file in files:
        if os.path.isfile(file) and check_file(file):
            scan(file)

    report()

main()
