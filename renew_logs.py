import os.path
import json

save_path = 'logs'
locations = ["aylesbury", "barnstaple", "barrow-in-furness", "basildon", "birmingham", "blackfriars", 
"bolton", "bournemouth", "bradford", "bristol", "burnley", "bury_st_edmunds", 
"caernarfon", "cambridge", "canterbury", "cardiff", "carlisle", "carmarthen", "centralcriminalcourt", 
"chelmsford", "chester", "chichester", "coventry", "croydon", "derby", "dolgellau", "doncaster", 
"dorchester", "durham", "exeter", "gloucester", "greatgrimsby", "guildford", "harrow", "haverfordwest", 
"hereford", "innerlondon", "ipswich", "isleworth", "kings_lynn", 
"kingston-upon-hull", "kingston-upon-thames", "knutsford", "lancaster", "leeds", "leicester", "lewes", 
"lincoln", "liverpool", "luton", "maidstone", "manchestercrownsquare", "manchesterminshullst", 
"merthyrtydfil", "mold", "newcastle-upon-tyne", "newport_crown_court", "newportiow", "northampton", 
"norwich", "nottingham", "oxford", "peterborough", "plymouth", "portsmouth", "preston", "reading", 
"salisbury", "sheffield", "shrewsbury", "snaresbrook", "southampton", "southend", "southwark", "stalbans", 
"stafford", "stoke-on-trent", "swansea", "swindon", "taunton", "teesside", "truro", "warrington", 
"warwick", "wolverhampton", "winchester", "woodgreen", "woolwich", "worcester", "york"]

file = []

for elem in locations:
    file.append(os.path.join(save_path, elem + ".txt"))

# print(file)

updated = [] # Generates fresh last_updated list
for i in range(len(locations)):
    updated.append(" ")

with open("logs/recent.txt", "w") as fp:
    json.dump(updated, fp)

print("Empty recent file generated")

for i in range(len(locations)):
    f = open(file[i], "w")
    f.write("Log file for " + locations[i] + "\n------------------------------")
    f.close()
    print("Empty log file generated for", locations[i])