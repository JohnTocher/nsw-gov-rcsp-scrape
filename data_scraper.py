#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import os,sys
import urllib
import fileinput
import string
import urlparse
import time

from BeautifulSoup import BeautifulSoup

# Threshhold for debug messages
# 0 should show all
GLOBAL_DEBUG_LEVEL = 30

base_URL = "http://www.dlg.nsw.gov.au/dlg/dlghome/dlg_regions.asp?mi=0&ml=8&regiontype=0"

# Where to put the data
# You'll need to update this for your file system

base_folder = '/home/john/' # Native Home

# Address Processor

# ================
# Functions
# ================
    
def clean_region_name( raw_text ):
    
    new_text=raw_text.replace( "&nbsp;" , " " )
    
    bracket_pos = new_text.find("(")
    if bracket_pos>0:
        final_region = new_text[:bracket_pos].rstrip()
    else:
        final_region = new_text
        
    return final_region
    
def clean_region_code( raw_text ):
    
    new_text=raw_text.replace( "&nbsp;" , " " )
    
    equal_pos = new_text.rfind("=")
    if equal_pos > 0:
        final_region_code = new_text[equal_pos+1:]
    else:
        final_region_code = "Error"
        
    return final_region_code
    
def clean_council_name( raw_text ):
    
    new_text=raw_text.replace( "&nbsp;" , " " )
    final_council = new_text.rstrip()
            
    return final_council
    
def clean_generic_text( raw_text ):
    
    new_text=raw_text.replace( "&nbsp;" , " " )
    new_text = new_text.rstrip().lstrip()
            
    return new_text
    
def council_ID_from_URL ( raw_URL ):
    
    final_ID="Error"
    
    id_pos = raw_URL.find("slacode=")
    
    if id_pos > 0:
        end_pos = raw_URL.find("&",id_pos)
        if end_pos > 0:
            final_ID=raw_URL[id_pos+8:end_pos]
            
    return final_ID

    
def debug_print( debugText , debugLevel = 1):
    """ Prints debug text to stdout (or wherever) subject to a global threshhold"""

    if debugLevel > GLOBAL_DEBUG_LEVEL:
        print("{0}".format(debugText) )

# =================
# End of functions
# =================

# =================
# Beginning of main
# =================

start_time = time.time()

debug_print( "Beginning processing...", 1000)

running_count=0
error_list=[]
                
regions = dict()    # Lookup for region code
councils = dict()   # Lookup for council
  
first_page = urllib.urlopen(base_URL).read()
soup = BeautifulSoup(first_page)

# Get the top level links - one per region

links_level_1 = []
link_count = 0
region_table = soup.findAll("table" , { "class" : "information" })
for each_table in region_table:
    anchor_list = each_table.findAll('a', href=True)
    for this_link in anchor_list:
        link_count += 1
        region_name = clean_region_name( this_link.text )
        region_code = clean_region_code( this_link['href'] )
        regions[region_code] = region_name
        debug_print( "Region code for {0} is [{1}]".format( region_name , region_code ) , 5 )
        full_URL =urlparse.urljoin(base_URL,this_link['href'])
        links_level_1.append(full_URL)
        debug_print ( "Link {0:03} [{1}]".format(link_count , full_URL ) , 2 )

debug_print( "\nFound {0} level 1 links\n".format( link_count ) , 100 )
debug_print( "Regions:\n{0}".format( regions ) , 10 )

# Get the 2nd level links - multiple councils per region

link_count = 0
links_level_2 = []

for each_link in links_level_1:
    
    this_page = urllib.urlopen(each_link).read()
    soup = BeautifulSoup(this_page)
    result_table = soup.findAll("table" , { "class" : "information" })
    for each_table in result_table:
        anchor_list = each_table.findAll('a', href=True)
        for this_link in anchor_list:
            council_ID = council_ID_from_URL( this_link['href'] )
            council_name = clean_council_name ( this_link.text )
            debug_print( "Council code for {0} is [{1}]".format( council_name , council_ID ) , 5 )
            councils[council_ID] =  council_name
            link_count += 1
            full_URL =urlparse.urljoin(base_URL,this_link['href'])
            links_level_2.append(full_URL)
            debug_print ( "Link {0:03} [{1}]".format(link_count , full_URL ) , 3 )
        
debug_print( "\nFound {0} level 2 links\n".format( link_count ) , 100 )
debug_print( "Councils:\n{0}".format( councils ) , 10 )


# Process the 2nd level links - multiple Towns per LGA
# This is where we get the actual data we want

town_count=0
link_count=0
links_skipped=0

output_filename=os.path.join(base_folder , "output.csv" )

output_file = open(output_filename, 'w')
output_file.write("Region,LGA,Town,PostCode")

for each_link in links_level_2:
    link_count += 1
    debug_print( "Link is [{0}]".format(each_link) , 35 )
    region = regions[ clean_region_code( each_link ) ]
    council = councils[ council_ID_from_URL(each_link) ]
    
    if (link_count<200):  # Really need to do all of them - just for testing!
        this_page = urllib.urlopen(each_link).read()
        soup = BeautifulSoup(this_page)
        result_table = soup.findAll("table" , { "class" : "information" })
        row_count = 0 
        for each_table in result_table:
            debug_print("Processing table",25)
            row_list = each_table.findAll("tr")
            for this_row in row_list:
                row_count += 1
                row_class=this_row.get("class","not found")
                debug_print("Processing row {0}".format(row_count) ,25)
                if row_class in ("MainBodyContentRow1","MainBodyContentRow2"):
                    town_count += 1
                    debug_print("Processing actual row {0}".format(row_count) ,25)
                    output_file.write( "\n{0},{1}".format( region , council ) )
                    data_list = this_row.findAll("td")
                    for this_data in data_list:
                        clean_data=clean_generic_text(this_data.text)
                        if len(clean_data)>1:
                            #debug_print("Data is  [{0}]".format(clean_data),25)
                            output_file.write( ",{0}".format(clean_data) )
        debug_print("Processed [{0}] rows in [{1}]".format(row_count,each_link) ,35)
    else:
        links_skipped += 1
 
output_file.close()

if len(error_list)>0:
    debug_print("Errors found!",1000)
    [debug_print(each_error, 1000) for each_error in error_list]
else:
    debug_print("All done with no errors!",1000)
    time_now=time.time()
    
debug_print("Processed {0} towns from {1} pages ".format( town_count, link_count) , 1000)
debug_print( "Completed in {0} seconds".format(time_now - start_time), 1000)
        







                         
                
                
