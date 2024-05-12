import os
import inspect
import argparse
import re
import json
import platform
import html

parser = argparse.ArgumentParser()
parser.add_argument("project_folder", help="UWP Project folder to scan")
parser.add_argument("template_folder", help="Templates file (JSON)")
parser.add_argument("-o", dest="report_output", default="./ult_scan_report.html", help="Report output file (html)")
args = parser.parse_args()

project_folder = args.project_folder
template_folder = args.template_folder
report_output = args.report_output

final_report_results = []
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
        
        file.close()
        
        return data
    except Exception as error:
        exception(error, inspect.currentframe().f_code.co_name)

def report():
    raw_results = json.dumps(final_report_results).replace('<', '\\u003c').replace('>', '\\u003e')
    
    final_report = '''
    <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>window.scan_results = ''' + raw_results + '''</script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.7.2/styles/dracula.min.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.7.2/highlight.min.js"></script>
            <style>
                /* Styling for the list */
                .list-container {
                    width: 90%;
                    margin: 20px auto;
                }
                .list-item {
                    margin-bottom: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 10px;
                    list-style-type: none;
                    background-color: #f9f9f9;
                }
                .item-content {
                    display: flex;
                    align-items: center;
                }
                .expand-button {
                    cursor: pointer;
                    color: #fff;
                    background-color: #007bff;
                    border: none;
                    border-radius: 5px;
                    padding: 5px 10px;
                    margin-left: auto;
                }
                .expand-button:hover {
                    background-color: #0056b3;
                }
                .hidden {
                    display: none;
                }

                .code-snippet {
                    background-color: #282a36;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 20px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    overflow-x: auto; /* Enable horizontal scrolling for long lines */
                    white-space: pre-wrap; /* Preserve line breaks */
                    list-style-type: none;
                }

                h1, h2, h3 {
                    color: #007bff;
                }
                
                .search-bar {
                    width: 90%;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-sizing: border-box;
                }
                .dropdown {
                    display: inline-block;
                    position: relative;
                    margin-left: 10px; /* Adjust margin as needed */
                }

                .dropdown-btn {
                    background-color: #007bff;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }

                .dropdown-btn:hover {
                    background-color: #0056b3;
                }

                .dropdown-option {
                    display: none;
                    position: absolute;
                    background-color: #f9f9f9;
                    min-width: 160px;
                    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
                    z-index: 1;
                    border-radius: 5px;
                    margin-top: 5px; /* Adjust margin as needed */
                }

                .dropdown-option a {
                    color: black;
                    padding: 12px 16px;
                    text-decoration: none;
                    display: block;
                }

                .dropdown-option a:hover {
                    background-color: #f1f1f1;
                }

                .dropdown:hover .dropdown-option {
                    display: block;
                }
            </style>
        </head>
        
        <body>
            <h1 style="text-align: center;">Scan Results</h1>
            <br>
            <br>
            <div class="search-bar-container">
                <input type="text" id="searchBar" class="search-bar" placeholder="Search...">
                
                <div class="dropdown" id="dropdown">
                    <button class="dropdown-btn" onclick="toggleDropdown()">Syncs</button>
                    <div id="dropdown-options" class="dropdown-option">
                        <a href="#" onclick="selectOption('Option 1')">Option 1</a>
                        <a href="#" onclick="selectOption('Option 2')">Option 2</a>
                        <a href="#" onclick="selectOption('Option 3')">Option 3</a>
                    </div>
                </div>
            </div>
            <br>
            <br>
            <div id="listContainer" class="list-container"></div>
        </body>
        <script>
            function selectOption(option) {
                searchBar.value = option;
                createList(option);
                dropdownOption.style.display = 'none';
            }

            function toggleDropdown() {
                var dropdownOption = document.querySelector('.dropdown-option');
                dropdownOption.style.display = dropdownOption.style.display === 'block' ? 'none' : 'block';
            }
            
            // Function to create the list
            function createList(filter) {
                const listContainer = document.getElementById('listContainer');
                const dropdown_options = document.getElementById('dropdown-options');
           
                match_names  = []
                
                dropdown_options.innerHTML = "";
                listContainer.innerHTML = "";

                scan_results.forEach(item => {
                    for (let key in item) {
                        // Create template title
                        template_name = key;
                        console.log(template_name);
                        base_template_node = item[key];

                        const title = document.createElement('h2');
                        title.innerText = template_name;
                        title.style.marginTop = '20px';
                        listContainer.appendChild(title);
                        
                        for (let key in base_template_node) {
                            console.log('filename: ' + key);
                            filename = key;

                            const listItem = document.createElement('div');
                            listItem.className = 'list-item';

                            const itemContent = document.createElement('div');
                            itemContent.className = 'item-content';

                            const titleElement = document.createElement('h3');
                            titleElement.textContent = key;

                            const button = document.createElement('button');
                            button.className = 'expand-button';
                            button.textContent = 'Show results';

                            const resultsList = document.createElement('ul');
                            resultsList.className = 'hidden';
                            
                            has_results = false;
                            
                            base_template_node[filename].results.forEach(result => {
                                match_name = "";

                                for (let key in result){
                                    match_name = key;
                                }
                                
                                if (match_names.includes(match_name) !== true){
                                    match_names.push(match_name)
                                    
                                    option_link = document.createElement('a');
                                    option_link.href="#";
                                    option_link.setAttribute('onclick', "selectOption('" + match_name.replaceAll("'", "\\'") + "');");
                                    option_link.innerText = match_name
                                    
                                    dropdown_options.appendChild(option_link)
                                }
                                
                                if (filter !== ''){
                                    if (match_name.toLowerCase().includes(filter.toLowerCase())){
                                        console.log(filter + ' matches ' + match_name);
                                    }else{
                                        return;
                                    }
                                }
                                
                                has_results = true;
                                
                                const resultItem = document.createElement('li');
                                resultItem.className = 'list-item'; // Apply same style as parent item

                                // Create result title element
                                const resultTitle = document.createElement('span');
                                resultTitle.textContent = match_name + ': ';

                                // Create button to show subresults
                                const resultButton = document.createElement('button');
                                resultButton.className = 'expand-button';
                                resultButton.textContent = 'Show code';

                                // Create subresults list element
                                const subresultsList = document.createElement('ul');
                                subresultsList.className = 'hidden';

                                // Populate subresults list
                                result[match_name].forEach(subresult => {
                                    const subresultItem = document.createElement('li');
                                    subresultItem.className = 'code-snippet javascript';
                                    subresultItem.textContent = subresult;
                                    subresultsList.appendChild(subresultItem);
                                    hljs.highlightElement(subresultItem);
                                });

                                // Toggle subresults visibility on button click
                                resultButton.addEventListener('click', () => {
                                    subresultsList.classList.toggle('hidden');
                                    resultButton.textContent = subresultsList.classList.contains('hidden') ? 'Show code' : 'Hide code';
                                });

                                // Append elements to result item
                                resultItem.appendChild(resultTitle);
                                resultItem.appendChild(resultButton);
                                resultItem.appendChild(subresultsList);

                                resultsList.appendChild(resultItem);
                            });

                            // Toggle results visibility on button click
                            button.addEventListener('click', () => {
                                resultsList.classList.toggle('hidden');
                                button.textContent = resultsList.classList.contains('hidden') ? 'Show results' : 'Hide results';
                            });
                            
                            if (has_results){
                                // Append elements to item content
                                itemContent.appendChild(titleElement);
                                
                                itemContent.appendChild(button);
                                

                                // Append item content and results to list item
                                listItem.appendChild(itemContent);
                                listItem.appendChild(resultsList);

                                // Append list item to list container
                                listContainer.appendChild(listItem);
                            }
                        }
                    }
                });
                
            }

            // Call the function to create the list
            createList('');
            
            searchBar.addEventListener('input', function() {
                createList(this.value);
            });
            
        </script>

    </html>
    '''

    save_to_file(final_report, report_output)
    
    print("\n[DONE] Report Saved: file://" + os.path.realpath(report_output))
    

def start_string_scan(key, value, file_name, file_data, template_name):
    if type(value) == list:
        for str in value:
            string_scan(key, str, file_name, file_data, template_name)
    else:
        string_scan(key, value, file_name, file_data, template_name)

def string_scan(key, value, file_name, file_data, template_name):
    escaped_string = re.escape(value)
    regex_pattern = f"({escaped_string})"
    
    regex_scan(key, regex_pattern, file_name, file_data, template_name)

def regex_scan(key, value, file_name, file_data, template_name):
    results = re.findall(value, file_data)
    if len(results) > 0:
        file_link_address = '<a href="file://' + os.path.abspath(file_name) + '" target="_blank">' + file_name.split(file_separator)[len(file_name.split(file_separator)) - 1] + '</a>'
        
        for item in final_report_results:
            for item_key in item.keys():
                if item_key == template_name:
                    if item.get(template_name).get(file_name) == None:
                        item.get(template_name).update({
                            file_name: {
                                    "file_link_address": file_link_address,
                                    "results":[]
                                }
                        })

        #

        regex_pattern = re.compile(value)
        matches = [(match.start(), match.end()) for match in regex_pattern.finditer(file_data)]
        # Extract 50 bytes before and after each found substring
        results = []
        for start, end in matches:
            # Determine the start and end indices for the substring context
            context_start = max(0, start - 200)
            context_end = min(len(file_data), end + 200)
            
            # Extract the substring context
            context = file_data[context_start:context_end]
            results.append(context)

        for item in final_report_results:
            for item_key in item.keys():
                if item_key == template_name:
                    item.get(template_name).get(file_name).get("results").append({key:results})
        

def start_regex_scan(key, value, file_name, file_data, template_name):
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
                start_regex_scan(key, value, file, file_data, template["name"])

def initialize_templates():
    templates_files = get_all_files(template_folder)

    for file in templates_files:
        if not file.endswith(".json"):
            continue
        template = json.loads(read_file(file, type_string))
        templates.append(template)
        final_report_results.append({template["name"]:{}})

def main():
    initialize_templates()
    files = get_all_files(project_folder)

    for file in files:
        if os.path.isfile(file) and check_file(file):
            scan(file)

    report()

main()
