import csv
import os
import requests
import zipfile
from zipfile import ZipFile, ZIP_DEFLATED
import urllib2
from lxml import html
import json
from datetime import datetime
import collections
import xlsxwriter

class GitDownload(object):

    def csvToJson(self, filename):
        try:
            with open( filename, 'r') as csvFile:
                csvDict = csv.DictReader( csvFile, restkey=None, restval=None, )
                out = [obj for obj in csvDict]
        except IOError:
           return False
        return out

    def downloadGit(self, filename, downPath):

        git_dic_root = os.path.join(os.path.dirname(__file__), downPath)
        if self.testForDir(git_dic_root) == False:
            self.createDir(git_dic_root)

        result = self.csvToJson(filename)

        for dir_name in result:

            # create directory to download source from git.
            parent_dir = dir_name['Project'].split('/')[0]
            child_dir = dir_name['Project'].split('/')[1]
            dir_root = os.path.join(os.path.dirname(__file__), downPath + '/')
            if self.testForDir(dir_root + parent_dir) == False:
                self.createDir(dir_root + parent_dir)

            #create a zip file
            self.createZip(dir_root + parent_dir, child_dir)

            #download git data
            git_url = "https://github.com/"+dir_name['Project']+"/archive/master.zip"

            dir_root += dir_name['Project'] + ".zip"
            if self.testForDir(dir_root) == False:
                result = self.downloadChunks(git_url, dir_root)

    def testForDir(dirname, path):
        return os.path.isdir(path)

    def createDir(dirname, path):
        try:
            os.mkdir(path)
        except OSError as error:
            print error
        return True

    def createZip(spam, zip_path, file_name):
        filename = file_name + ".zip"

        abspath = os.path.join(zip_path, filename)
        # Create zip
        z = ZipFile(abspath, "w", ZIP_DEFLATED)
        z.close()

    def download_git_data(dirname, git_url, dir_root):
        r = requests.get(git_url)
        f = open(dir_root, 'w')
        f.write(r.content)

    def downloadChunks(dirname, url, temp_path):
        #move the file to a more uni path
        os.umask(0002)

        try:
            req = urllib2.urlopen(url)
            CHUNK = 256 * 10240
            with open(temp_path, 'wb') as fp:
                while True:
                    chunk = req.read(CHUNK)

                    # write zip file
                    if not chunk: break
                    fp.write(chunk)

        except urllib2.HTTPError, e:
            print "HTTP Error:",e.code , url
            return False
        except urllib2.URLError, e:
            print "URL Error:",e.reason , url
            return False

        return True

class CollectData(object):

    HEADERS = { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36',
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Charset':'utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding':'gzip,deflate,sdch',
                'Accept-Language':'it-IT,it;q=0.8,en-US;q=0.6,en;q=0.4',
                'Connection':'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                # 'X-Requested-With':'XMLHttpRequest',
                # 'Referer': 'https://wwwapps.ups.com/ctc/request?loc=en_US&WT.svl=PNRO_L1',
                # 'Origin': 'https://wwwapps.ups.com',
                # 'Host': 'wwwapps.ups.com'
                }

    def __init__(self, *args, **kwargs):
        self.session = requests.Session()
        self.session.headers = self.HEADERS

    def getData(self, filename, collprjinf, prjallinfo, downPath):
        gitdown = GitDownload()
        result = gitdown.csvToJson(filename)
        for proname in result:
            prjinfo = {}
            filedata = {}
            giturl = "https://github.com/"
            giturl += proname['Project']

            zipfileurl = os.path.join(os.path.dirname(__file__), downPath) + "/" + proname['Project'] + ".zip"

            filecount, extracted_size, file_extension = self.totFilesCount(zipfileurl)
            prjinfo["TotFilesCount"] = filecount
            prjinfo["TotFileSize"] = extracted_size
            prjinfo["TotFileExtensions"] = file_extension

            filedata["PrjName"] = proname['Project'].split('/')[1]
            filedata["TotFilesCount"] = filecount
            filedata["TotFileSize"] = extracted_size
            filedata["TotFileExtensions"] = file_extension

            self.getJson(giturl, prjinfo, prjallinfo, filedata)

            prjinfo["PrjName"] = proname['Project'].split('/')[1]

            collprjinf.append(prjinfo)

        return collprjinf

    def getJson(self, url, prjinfo, prjallinfo, filedata):
        allgitinfo= {}
        x = self.getHtml(url)
        prjinfo["Stars"]= int(x.xpath(".//a[contains(@class,'social-count')]")[0].text.replace('\n','').replace(',',''))
        prjinfo["Forks"]= int(x.xpath(".//a[contains(@class,'social-count')]")[1].text.replace('\n','').replace(',',''))
        prjinfo["TotCommits"]= int(x.xpath(".//li[contains(@class,'commit')]/a/span/span")[0].tail.replace('\n','').replace(',',''))
        prjinfo["Branches"]= int(x.xpath(".//ul[contains(@class,'numbers-summary')]/li/a/span/span")[1].tail.replace('\n','').replace(',',''))
        prjinfo["Releases"]= int(x.xpath(".//ul[contains(@class,'numbers-summary')]/li/a/span/span")[2].tail.replace('\n','').replace(',',''))
        prjinfo["Contributors"]= int(x.xpath(".//ul[contains(@class,'numbers-summary')]/li/a/span/span")[3].tail.replace('\n','').replace(',',''))

        results = requests.get(url+ "/graphs/contributors-data").text
        page = json.loads(results)

        #get Report period: From, To

        reportdate = page[1]["weeks"]
        fromdate = datetime.fromtimestamp(reportdate[0]['w'])
        todate = datetime.fromtimestamp(reportdate[-1]['w'])
        prjinfo["Report_period_from"] = fromdate.strftime('%Y-%m-%d')
        prjinfo["Report_period_to"] = todate.strftime('%Y-%m-%d')
        prjinfo["Duration"] = (todate - fromdate).days

        addloc = 0
        delloc = 0
        commit = 0
        i = 0

        for author in page:
            commit += author["total"]
            weeksinfo = author["weeks"]
            for week in weeksinfo:
                delloc += week["d"]
                addloc += week["a"]
        prjinfo["TotLOC"] = addloc - delloc
        prjinfo["TotLOCadd"] = addloc
        prjinfo["TotLOCdelete"] = delloc
        durdate = page[0]['weeks']

        for date in durdate:
            date = date['w']
            allgitinfo['Date'] = datetime.fromtimestamp(date).strftime('%Y-%m-%d')
            for j in range(1,21):
                author = page[-j]['author']['login']
                allgitinfo['Author-'+str(j)+'_Name'] = author
                allgitinfo['Author-'+str(j)+'_TotLOC'] = page[-j]['weeks'][i]['a'] - page[-j]['weeks'][i]['d']
                allgitinfo['Author-'+str(j)+'_TotLOCadd'] = page[-j]['weeks'][i]['a']
                allgitinfo['Author-'+str(j)+'_TotLOCdel'] = page[-j]['weeks'][i]['d']
                allgitinfo['Author-'+str(j)+'_TotCommits'] = page[-j]['weeks'][i]['c']
                allgitinfo['PrjName'] = filedata['PrjName']
                allgitinfo['TotFilesCount'] = filedata['TotFilesCount']
                allgitinfo['TotFileSize'] = filedata['TotFileSize']
                allgitinfo['TotFileExtensions'] = filedata['TotFileExtensions']
                allgitinfo['TotLOC'] = prjinfo['TotLOC']
                allgitinfo['TotLOCadd'] = prjinfo['TotLOCadd']
                allgitinfo['TotLOCdel'] = prjinfo['TotLOCdelete']
                allgitinfo['TotCommits'] = prjinfo['TotCommits']
                allgitinfo['NmAuthors'] = prjinfo['Contributors']

            prjallinfo.append(allgitinfo)
            allgitinfo = {}
            i +=1

        return prjinfo, prjallinfo

    def getHtml(self, path):
        resp = self.session.get(path)
        x = html.fromstring(resp.content)
        return x

    def totFilesCount(self, filename):
        zipfilename = zipfile.ZipFile(filename)
        nameList = zipfilename.namelist()
        extensions = collections.defaultdict(int)

        fileCount = 0
        extracted_size = 0
        for item in nameList:
            fileCount += 1
            filenames = item.split('/')[-1]
            extensions[os.path.splitext(filenames)[1].lower()] += 1
        file_extension = []
        for key,value in extensions.items():
             file_extension.append(key)
        extracted_size = os.path.getsize(filename)

        return fileCount, extracted_size, file_extension

class JsonToCsv(object):

    def collectData(self, results, outCsv1):
        self.creatCSV(outCsv1)
        with open(outCsv1, "w") as output_file:
            csv_out = csv.writer(output_file)
            Header = ['PrjName', 'Stars', 'Forks', 'From','To','Duration', 'TotFilesCount', 'TotFileSize', 'TotLOC', 'TotLOCadd', 'TotLOCdelete', 'TotCommits', 'NmAuthor', 'Branches', 'Releases']
            csv_out.writerow(Header)
            for item in results:
                te = [item['PrjName'],item['Stars'],item['Forks'],item['Report_period_from'], item['Report_period_to'],item['Duration'] ,item['TotFilesCount'],
                      item['TotFileSize'],item['TotLOC'], item['TotLOCadd'],item['TotLOCdelete'],item['TotCommits'], item['Contributors'], item['Branches'], item['Releases']]
                csv_out.writerow(te)

            output_file.close()
        return "ok"
    def alldata(self, results, outCsv2):
        self.creatCSV(outCsv2)
        with open(outCsv2, "w") as output_file:
            csv_out = csv.writer(output_file)
            Header = ['PrjName', 'Date', 'TotFilesCount', 'TotFileSize', 'TotFileExtensions', 'TotLOC', 'TotLOCadd', 'TotLOCdel', 'TotCommits', 'NmAuthors']
            for i in range(1,21):
                Header.append('Author-'+str(i)+'_Name')
                Header.append('Author-'+str(i)+'_TotLOC')
                Header.append('Author-'+str(i)+'_TotLOCadd')
                Header.append('Author-'+str(i)+'_TotLOCdel')
                Header.append('Author-'+str(i)+'_TotCommits')
            csv_out.writerow(Header)
            for item in results:
                te = []
                te = [item['PrjName'], item['Date'], item['TotFilesCount'], item['TotFileSize'], item['TotFileExtensions'], item['TotLOC'], item['TotLOCadd'], item['TotLOCdel'],
                      item['TotCommits'], item['NmAuthors']]
                for i in range(1,21):
                    te.append(item['Author-'+str(i)+'_Name'])
                    te.append(item['Author-'+str(i)+'_TotLOC'])
                    te.append(item['Author-'+str(i)+'_TotLOCadd'])
                    te.append(item['Author-'+str(i)+'_TotLOCdel'])
                    te.append(item['Author-'+str(i)+'_TotCommits'])
                csv_out.writerow(te)

            output_file.close()
        return "ok"

    def creatCSV(self, filename):
        basedir = os.path.dirname(filename)
        if not os.path.exists(basedir):
            workbook = xlsxwriter.Workbook(filename)



