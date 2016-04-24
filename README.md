# Kingdom-Rewards-Calculator
A calculator that determines the optimal settings for a minigame in the MMORPG Old School RuneScape

TL;DR for people who have played or are playing OSRS / RS3 / Runescape:

  This program collected data from the OSRS GE and stores the value of picking certain options for your Kingdom
    management minigame, so you can judge the value of putting all your workers on all resources over time. I don't
    include the farming resource, because I cant find the data for the seeds generated. I also dont account for:
    
      Gems from mining
      Herb seeds from the herbs/flax resource
      caskets from fishing
      loop/tooth halfs
      other random resources that don't make up a significant portion of profit / I cant find data for
      
    I do however include birds nests and their expected value based on the prices of seeds you can get from them
    
    Sources for my data are in the source code for relevent Python objects.
    
TL;DR for people who have played an MMO before:

  This program takes auctionhouse data (how items are traded in old school runescape) data for the current day and calculates
    the optimal settings for a minigame that generates ingame resources.
    
TL;DR for programmers:

  This Python 2.7 program takes the JSON data from the web API provided by Jagex and calculates out the best settings for a 
  resource generating minigame based on current item prices, and stores them in a SQLite database. I use matplotlib for graphing

To set this up:

  First run Database.py to set up your SQLite database
  Then run main.py to get the item data for the day and store it in your database, I recommend setting Python 2.7 as a windows task
    with the path to main.py as an argument
    
  running graph.py plots the data in your database. You will need to install matplotlib first. (I recommend installing PIP
    and doing "PIP install matplotlib" in the cmd prompt) 
  
