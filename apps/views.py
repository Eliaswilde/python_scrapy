from django.shortcuts import render
from scraper import GitDownload, CollectData, JsonToCsv
from apps.models import InputForm

def index(request):
    if request.method == 'POST':
        form = InputForm(request.POST)
        # return HttpResponse(form.cleaned_data)
        if form.is_valid():
            filename = form.cleaned_data['insertCsv']
            outCsv1 = form.cleaned_data['outCsv1']
            outCsv2 = form.cleaned_data['outCsv2']
            downPath = form.cleaned_data['downPath']

            collproinf = []
            prjallinfo = []

            csv_data=GitDownload()
            collect_data = CollectData()
            json_to_csv = JsonToCsv()

            result = csv_data.csvToJson(filename)
            if result:
                csv_data.downloadGit(filename, downPath)
                collect_data.getData(filename, collproinf, prjallinfo, downPath)

                json_to_csv.collectData(collproinf, outCsv1)
                results = json_to_csv.alldata(prjallinfo, outCsv2)
            else:
                results = "There is no "+ filename +" in directory"

            context = {'results':results}
            return render(request, 'index.html', context)
        else:
            context = {'results': 'The data introduced is not valid.'}
            return render(request, 'index.html', context)
    else:
        form = InputForm()
        context = {'results': ''}
        return render(request, 'index.html', context)
