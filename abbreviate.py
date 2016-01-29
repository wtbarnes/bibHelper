#name: abbreviate.py
#author: Will Barnes
#date: 27 January 2016
#description: scrape ADS Journal abbreviation bib codes and replace in .bib file


#Import needed modules
import os
import sys
import urllib
import html
from datetime import datetime
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import xml.dom.minidom as xdm


class Abbreviate(object):
    """Class for scraping ADS journal abbreviations and replacing in .bib file"""
    def __init__(self,bib_file=None, abbrev_db=None, ads_abbrev_url=None, extra_abbrev_db=None):
        #default references file
        if not bib_file:
            self.bib_file = os.path.join(os.environ['HOME'],'Library/texmf/bibtex/bib/references.bib')
        else:
            self.bib_file = bib_file
        #default abbreviations database
        if not abbrev_db:
            self.abbrev_db = os.path.join(os.environ['HOME'],'Library/texmf/bibtex/abbrev.db.xml')
        else:
            self.abbrev_db = abbrev_db
        #default URL to scrape abbreviations from
        if not ads_abbrev_url:
            self.ads_abbrev_url = 'http://adsabs.harvard.edu/abs_doc/refereed.html'
        else:
            self.ads_abbrev_url = ads_abbrev_url
        #extra db file (those not on webpage)
        self.extra_abbrev_db = extra_abbrev_db

    def check_db(self):
        """Check existence of database. Build it if it does not exist"""
        if os.path.isfile(self.abbrev_db):
            print("Abbreviations database found at: %s"%self.abbrev_db)
            #TODO: add more sophisticated checking (i.e. can it be parsed?)
        else:
            print("No abbreviations database found at: %s"%self.abbrev_db)
            print("Building database...")
            self.build_db()
            #TODO:add checks on database updates


    def build_db(self):
        """Build abbreviations database"""

        #Get soup
        soup = self._request_page()

        #Get pre tag content
        abbrev_keys = soup.pre
        if soup.pre is None:
            print("Cannot parse page. Expected tag <pre></pre> not found.")
            sys.exit(1)

        #set up XML document
        root = ET.Element('root')
        journals = ET.SubElement(root,'journals')

        #counter
        j_count = 0
        #iterate over pre tag if not empty
        for child in abbrev_keys:
            #check the child
            if self._check_tag(child):
                #create journal element
                element = ET.SubElement(journals,'journal')
                #feed abbreviation and name to XML tree
                element.set('abbreviation'," ".join(html.unescape(child.get_text()).split()))
                element.set('name'," ".join(html.unescape(str(child.next_sibling)).split()))
                #increment counter
                j_count += 1
            else:
                pass

        #append supplementary abbreviations
        self._append_extras(journals)

        #record number of records
        element = ET.SubElement(root,'num_journals')
        element.text = str(j_count)
        #record date last updated
        element = ET.SubElement(root,'last_updated')
        element.text = str(datetime.now())

        #Write to file
        self._print_db(root)


    def _print_db(self,root):
        """Print XML document tree to file."""
        #put all to string
        unformatted = ET.tostring(root)
        #format to DOM
        xdmparse = xdm.parseString(unformatted)
        #prettify
        prettyXml = xdmparse.toprettyxml(indent="    ")
        #write to file
        with open(self.abbrev_db,'w') as f:
            f.write(prettyXml)
        f.close()


    def _request_page(self):
        """Request page and return BeautifulSoup structure"""
        #Get page
        try:
            with urllib.request.urlopen(self.ads_abbrev_url) as url:
                w = url.read()
        except URLError:
            print("Could not reach %s"%self.ads_abbrev_url)
            print("Try again later or use a new URL.")
            sys.exit(1)
        #Make soup
        return BeautifulSoup(w)


    def _check_tag(self,child):
        """Checks on tag before parsing"""
        read_tag = True
        if type(child).__name__ != 'Tag':
            read_tag = False
        else:
            if 'name' in child.attrs:
                read_tag = False

        return read_tag


    def _append_extras(self,journals_element):
        """Append extra abbreviations if we have them"""
        if not self.extra_abbrev_db:
            print("No extra abbreviations found.")
            return

        #parse XML
        tree = ET.parse(self.extra_abbrev_db)
        #TODO:check if parse successful, handle errors
        #get root element
        root = tree.getroot()
        #find the journals element
        extra_journals = root.find('journals')
        #iterate over abbreviations
        for child in extra_journals:
            #create journal element
            element = ET.SubElement(journals_element,'journal')
            #feed abbreviation and name to XML tree
            element.set('abbreviation',child.get('abbreviation'))
            element.set('name',child.get('name'))


    def abbreviate_bibs(self):
        """Search through abbreviations database and replace all names with abbreviations"""

        #SED template for find and replace
        sed_temp = """sed -i '' 's/["{]%s["}]/%s/g' %s"""

        #open the database
        tree = ET.parse(self.abbrev_db)
        #TODO:check if parse successful, handle errors
        #get root element
        root = tree.getroot()
        #find the journals element
        journals = root.find('journals')
        #TODO:handle not found exception
        #progress counter
        i_progress = 0
        for child in journals:
            #Retrieve name and abbreviation
            name = child.get('name').replace('&','\\\\\&')
            abb = '{' + child.get('abbreviation').replace('&','\\\\\&') +'}'
            #Find and replace
            os.system(sed_temp%(name,abb,self.bib_file))
            #TODO: more pythonic way to do this, i.e. not sed
            #progress
            if (i_progress+1)%100 == 0:
                print("Processing abbreviation %d"%(i_progress+1))
            i_progress += 1


def main():
    #instantiate class and run
    #test
    abbreviator = Abbreviate(bib_file=os.path.join(os.environ['HOME'],'Library/texmf/bibtex/bib/references.bib'), abbrev_db=os.path.join(os.environ['HOME'],'Library/texmf/bibtex/abbrev.db.xml'), extra_abbrev_db=os.path.join(os.environ['HOME'],'Library/texmf/bibtex/supplementary_abbrev.db.xml'))
    abbreviator.check_db()
    abbreviator.abbreviate_bibs()

if __name__=='__main__':
    main()
