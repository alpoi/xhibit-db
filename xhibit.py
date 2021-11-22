import os, os.path, sys, ctypes, json, time, pymongo, requests, hide_cursor
from datetime import datetime
from bs4 import BeautifulSoup
from datetime import datetime

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["xhibit_live"] # You can call your database anything you like
save_path = 'logs/'
locations = ["aylesbury", "barnstaple", "barrow-in-furness", "basildon", "birmingham", "blackfriars", "bolton", "bournemouth", "bradford", "bristol", "burnley", "bury_st_edmunds", 
"caernarfon", "cambridge", "canterbury", "cardiff", "carlisle", "carmarthen", "centralcriminalcourt", "chelmsford", "chester", "chichester", "coventry", "croydon", "derby", "dolgellau", "doncaster", 
"dorchester", "durham", "exeter", "gloucester", "greatgrimsby", "guildford", "harrow", "haverfordwest", "hereford", "innerlondon", "ipswich", "isleworth", "kings_lynn", 
"kingston-upon-hull", "kingston-upon-thames", "knutsford", "lancaster", "leeds", "leicester", "lewes", "lincoln", "liverpool", "luton", "maidstone", "manchestercrownsquare", "manchesterminshullst", 
"merthyrtydfil", "mold", "newcastle-upon-tyne", "newport_crown_court", "newportiow", "northampton", "norwich", "nottingham", "oxford", "peterborough", "plymouth", "portsmouth", "preston", "reading", 
"salisbury", "sheffield", "shrewsbury", "snaresbrook", "southampton", "southend", "southwark", "stalbans", "stafford", "stoke-on-trent", "swansea", "swindon", "taunton", "teesside", "truro", "warrington", 
"warwick", "wolverhampton", "winchester", "woodgreen", "woolwich", "worcester", "york"]

def xhibit_parse(location = "empty", debug = False):
    if location == "empty" and debug == False:
        return "No location was specified. Terminating."

    r = requests.get("http://xhibit.justice.gov.uk/" + location + ".htm")
    url_soup = BeautifulSoup(r.content, "html.parser")

    content = url_soup.find("div", id="content-column")

    if debug == True:
        with open("sample.html") as test_doc:
            test_soup = BeautifulSoup(test_doc,"html.parser")
            content = test_soup.find("div", id="content-column")

    # Some cities have multiple court names
    global court_names
    court_names = [elem for elem in content.find_all("h2")]
    for i in range(len(court_names)):
        court_names[i] = court_names[i].string

    global last_updated
    last_updated = content.p.string

    court_tables = content.find_all("table")
    court_tables = [table.find_all("tr") for table in court_tables]

    for i in range(len(court_tables)):
        del court_tables[i][0] # Removes the table headers

    tr = []

    for table in court_tables:
        tr.append([row.find_all("td") for row in table])
        # Converts tbody into a list of rows

    final_list = []

    for building in tr: # Converts list of rows into lists of row elements
        final_list.append([[list(box.stripped_strings) for box in room] for room in building])

    # td in form td[table][tr][td], or td[building][room][info]

    total = 0 # debugging

    for b in range(len(final_list)):
        for r in range(len(final_list[b])): # Removes empty court rooms
            while r < len(final_list[b]):
                while len(final_list[b][r][1]) == 0: # Avoids index out of range error
                    # total += 1
                    # print("Deleting final_list[",b,"][",r,"] ",total, len(final_list[b]))
                    del final_list[b][r]
                    if r == len(final_list[b]):
                        break       
                break

    # Elements of final list to check for dashes: Last 2 characters in [i][3][0] and First 2 characters in [i][3][-1]

    for b in range(len(final_list)): # Removes the trailing and preceding dash in the event fields
        for i in range(len(final_list[b])): 
            final_list[b][i][3][0] = final_list[b][i][3][0].replace(" -", "")
            final_list[b][i][3][-1] = final_list[b][i][3][-1].replace("- ", "")

    # print("Last updated:", last_updated)

    # print(final_list)

    # for i in range(len(final_list)): # Prints the list in a readable format
    #     for j in range(len(final_list[i])):
    #         print(final_list[i][j])

    return last_updated, final_list

def to_mongo(parse_result, debug = False):
    single_cases = [[] for i in range(len(court_names))]
    exceptions = []
    for j in range(len(parse_result)): # Seperates cases with multiple _id and name
        for case in parse_result[j]:
            if len(case[1]) > 1 and len(case[2]) == 1:
                for i in range(len(case[1])):
                    single_cases[j].append([case[0], [case[1][i]], case[2], case[3]])
            elif len(case[1]) == len(case[2]) and len(case[1]) != 1:
                for i in range(len(case[1])):
                    single_cases[j].append([case[0], [case[1][i]], [case[2][i]], case[3]])
            elif len(case[1]) == 1 and len(case[2]) > 1:
                single_cases[j].append([case[0], case[1], case[2], case[3]])
            elif len(case[1]) == len(case[2]) == 1:
                single_cases[j].append([case[0], case[1], case[2], case[3]])
            elif len(case[1]) != 0 and len(case[2]) == 0:
                single_cases[j].append([case[0], case[1], ["REDACTED"], case[3]])
                print("Error: name REDACTED.")
            elif len(case[1]) > 1 and len(case[2]) > 1 and len(case[1]) != len(case[2]):
                for i in range(len(case[1])):
                    single_cases[j].append([case[0], [case[1][i]], case[2], case[3]])
                print("Error: len(names), len(_id) > 1 and unequal. Added seperately.")      
            else:
                print("Error: uncaught exception in", case)
                exceptions.append(case)
        if debug == False:
            for case in single_cases[j]:
                if mycol.find_one({"_id": case[1][0]}) == None and len(case[1]) == 1: 
                # and len(case[1]) == 1 enforces unique _id protocol
                    mycol.insert_one({"_id": case[1][0], "building": court_names[j], "room": case[0][0], "name": case[2][0], "updates": [case[3]], "last_updated": [results[0]]})
                elif mycol.find_one({"_id": case[1][0]}) == None and len(case[1]) != 1:
                    print("Error: multiple _id's specified in", case)
                else:
                    if mycol.find_one({"_id" : case[1][0]})["updates"][-1] == case[3]:
                        break
                    else: 
                        mycol.update_one({"_id" : case[1][0]}, {"$push": {"updates": case[3], "last_updated": results[0]}})

    exc_path = "exceptions.json"
    
    if len(exceptions) != 0:
        with open(exc_path, "r") as file:
            x = json.load(file)
        x.append(exceptions)
        with open(exc_path, "w") as file:
            json.dump(x, file)
    else:
        print(">> Added to MongoDB with no exceptions!")
    
    if debug == True:
        return single_cases

def xhibit_run(ignore_recent = False):
    if ignore_recent == False:
        with open("logs/recent.txt", "r") as fp:
            updated = json.load(fp)
    elif ignore_recent == True:
        updated = ["" for i in range(len(locations))]
    count = 0
    for i in range(len(locations)):
        count += 1
        global results
        results = xhibit_parse(locations[i])
        if results[0] == updated[i]:
            print(">> [" + str(count) + "]", locations[i], "had no updates at this time.")
            continue
        else:
            file_name = os.path.join(save_path, locations[i] + ".txt") # plaintext logs
            f = open(file_name,"a")
            f.write("\n" + results[0] + "\n" + str(results[1]) + "\n")
            f.close()
            print(">> [" + str(count) + "]", locations[i], "updated, most recently updated on", results[0] + ".")
            global mycol
            mycol = mydb[locations[i]]
            print(">> Attempting to add", locations[i], "update to MongoDB...")
            to_mongo(results[1])
            print(">> [" + str(count) + "]", locations[i], "added to MongoDB.")
            updated[i] = results[0]
    with open("logs/recent.txt", "w") as fp:
        json.dump(updated, fp)
    print("Completed pass at", datetime.now().strftime("%H:%M"))

while True:
    ctypes.windll.kernel32.SetConsoleTitleW("XHIBIT") # names terminal
    os.system('cls||clear') # clears terminal
    hide_cursor.hide_cursor() # hides blinking cursor

    print(" == XHIBIT ==\n > Waiting until 9am to begin operation...")
    now = datetime.now().strftime("%H:%M")

    #while now != "09:00":
    #    now = datetime.now().strftime("%H:%M")
    #    print(" > Current Time:", now, end="\r")
    #    time.sleep(60)

    fatal_errors = 0
    errors = []

    for interval in range(60):
        print("Starting pass", interval + 1, "of xhibit_run().")
        try:
            xhibit_run()
        except:
            if fatal_errors < 5:
                fatal_errors += 1
                print(">> Fatal error", sys.exc_info())
                errors.append(sys.exc_info())
                time.sleep(600)
                pass
            else:
                print(">> Fatal error counter reached 5. Terminating program.")
                print(errors)
                break
        if fatal_errors >= 5:
            break
        time.sleep(600)

stay_open_please = input()