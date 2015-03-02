__author__ = 'Den'
from scraper import GitDownload, CollectData, JsonToCsv
import sys

def mainRun(filename):
    collproinf = []
    prjallinfo = []
    # filename = 'Scraper_Test.csv'
    csv_data=GitDownload()
    collect_data = CollectData()
    json_to_csv = JsonToCsv()

    csv_data.downloadGit(filename)
    collect_data.getData(filename, collproinf, prjallinfo)

    results = json_to_csv.collectData(collproinf)
    results = json_to_csv.alldata(prjallinfo)
    print results

if __name__ == '__main__':
    filename = (sys.argv[1])
    mainRun(filename)
