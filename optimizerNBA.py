from lxml import html
import requests
import pandas as pd
import pulp
import numpy as np
from re import sub
from decimal import Decimal
page = requests.get("https://www.numberfire.com/nba/daily-fantasy/daily-basketball-projections")
tree = html.fromstring(page.content)
#get the player names
players = tree.xpath('//a[@class="full"]/text()')
new_players = []
for item in players:
    new_players.append(str(item.strip()))
#get the player's projected fantasy points
fantasy_p = tree.xpath('//td[@class="fp active"]/text()')
fantasy_points = []
for item in fantasy_p:
    fantasy_points.append(float(item.strip()))
#get the player's salary
sal = tree.xpath('//td[@class="cost"]/text()')
salary = []
for item in sal:
    temp_val = item.strip()
    value = Decimal(sub(r'[^\d.]', '', temp_val))
    salary.append(value)
#get the player's position
pos_temp = tree.xpath('//span[@class="player-info--position"]/text()')
pos = []
for item in pos_temp:
    pos.append(str(item))

is_drafted = []

#create data frame
raw_data = pd.DataFrame(list(zip(new_players, fantasy_points, salary, pos)), columns = ['player', 'fp', 'sal', 'pos'])

model = pulp.LpProblem("FanDuel", pulp.LpMaximize)

raw_data["PG"] = (raw_data["pos"] == 'PG').astype(float)
raw_data["SG"] = (raw_data["pos"] == 'SG').astype(float)
raw_data["PF"] = (raw_data["pos"] == 'PF').astype(float)
raw_data["SF"] = (raw_data["pos"] == 'SF').astype(float)
raw_data["C"] = (raw_data["pos"] == 'C').astype(float)
raw_data["Salary"] = raw_data["sal"].astype(float)

print(raw_data)
total_points = {}
cost = {}
PGs = {}
SGs = {}
PFs = {}
SFs = {}
Cs = {}
number_of_players = {}

# i = row index, player = player attributes
for i, player in raw_data.iterrows():
    var_name = 'x' + str(i) #variable name
    decision_var = pulp.LpVariable(var_name, cat='Binary') #Initialize Variables

    total_points[decision_var] = player["fp"] #Create Projection Dictionary
    cost[decision_var] = player["sal"] # Create Cost Dictionary

    # Create Dictionary for Player Types
    PGs[decision_var] = player["PG"]
    SGs[decision_var] = player["SG"]
    PFs[decision_var] = player["PF"]
    SFs[decision_var] = player["SF"]
    Cs[decision_var] = player["C"]
    number_of_players[decision_var] = 1.0

PG_constraint = pulp.LpAffineExpression(PGs)
SG_constraint = pulp.LpAffineExpression(SGs)
PF_constraint = pulp.LpAffineExpression(PFs)
SF_constraint = pulp.LpAffineExpression(SFs)
C_constraint = pulp.LpAffineExpression(Cs)
total_players = pulp.LpAffineExpression(number_of_players)

objective_function = pulp.LpAffineExpression(total_points)
model += (objective_function)

total_cost = pulp.LpAffineExpression(cost)
model += (total_cost <= 60000)

model += (PG_constraint == 2)
model += (SG_constraint == 2)
model += (PF_constraint == 2)
model += (SF_constraint == 2)
model += (C_constraint == 1)
model += (total_players == 9)

model.solve()

final_df = pd.DataFrame(columns = ["Player", "Projected Fantasy Points", "Salary", "Position"])

for var in model.variables():
    if var.varValue == 1.0:
        s = int(var.name[1:])
        row = [raw_data.iloc[s, 0], raw_data.iloc[s, 1], raw_data.iloc[s, 2], raw_data.iloc[s, 3]]
        final_df.loc[len(final_df)] = row

print(final_df)

objective_sum = final_df["Projected Fantasy Points"].sum()
print(objective_sum)

##for x in range(1, 2):
##    temp_model = pulp.LpProblem("Temp", pulp.LpMaximize)
##    temp_model += (objective_function <= 100000000) 
##    temp_model += (total_cost <= 60000)
##    temp_model += (PG_constraint == 2)
##    temp_model += (SG_constraint == 2)
##    temp_model += (PF_constraint == 2)
##    temp_model += (SF_constraint == 2)
##    temp_model += (C_constraint == 1)
##    temp_model += (total_players == 9)
##    temp_model.solve()
##    final_df = pd.DataFrame(columns = ["Player", "Projected Fantasy Points", "Salary", "Position"])
##    for var in model.variables():
##        if var.varValue == 1.0:
##            s = int(var.name[1:])
##            row = [raw_data.iloc[s, 0], raw_data.iloc[s, 1], raw_data.iloc[s, 2], raw_data.iloc[s, 3]]
##            final_df.loc[len(final_df)] = row
##    print(final_df)
##    objective_sum = final_df["Projected Fantasy Points"].sum()


