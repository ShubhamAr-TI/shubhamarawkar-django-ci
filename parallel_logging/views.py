from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor
from rest_framework import status
from collections import defaultdict
import concurrent.futures
import urllib.request
from django.core.exceptions import ValidationError
from datetime import datetime
# Create your views here.

def validateInput(data):
    if 'logFiles' not in data:
        raise ValidationError("Log Files is required")
    if 'parallelFileProcessingCount' not in data:
        raise ValidationError("Parallel File Processing count is required")
    if data['parallelFileProcessingCount'] <= 0 :
        raise ValidationError("Parallel File Processing count must be greater than zero!")

def load_url(url, timeout):
    timewise_split = defaultdict(lambda: defaultdict(lambda: 0))
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        lines = []
        for line in conn:
            if line[-2:] == b'\r\n':
                line = line[:-2]
            timestamp,exception = int(line[13:26].decode('utf-8')),line[27:].decode('utf-8')
            quartet_time = datetime.fromtimestamp(timestamp//(1000*60+15)*60*15)
            timewise_split[(quartet_time.hour,quartet_time.minute)][exception] += 1
    return timewise_split

def serialize_timesplits(data):
    formatted = []
    for (hr,mn),exceptions in data.items():
        obj = {}
        nhr = hr
        if mn == 45:
            nhr = (mn + 1)%24
        nmn = mn+15 if mn < 45 else 00
        obj["ts"] = (hr,mn)
        obj["timestamp"] = "{:02d}:{:02d}-{:02d}:{:02d}".format(hr,mn,nhr,nmn)
        obj["logs"] = []
        for exception,count in exceptions.items():
            obj["logs"].append({
                "exception": exception,
                "count": 1
            })
        obj["logs"].sort(key=lambda x: x["exception"])
        formatted.append(obj)
    formatted.sort(key=lambda x: x["ts"])
    pre = []
    post = []
    for x in formatted:
        if x['ts'][0] < 9:
            pre.append(x)
        else:
            post.append(x)
        del x['ts']
    formatted = post + pre
            
    return {"response":formatted}

class ProcessLogs(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        try:
            validateInput(payload)
        except ValidationError as ve:
            print(ve)
            return Response({
                "status": "failure",
                "reason": ve.message
            },status=status.HTTP_400_BAD_REQUEST)
        timewise_split = defaultdict(lambda: defaultdict(lambda: 0))
        with concurrent.futures.ThreadPoolExecutor(max_workers=payload['parallelFileProcessingCount']) as executor:
            # Start the load operations and mark each future with its URL
            future_to_url = {executor.submit(load_url, url, 60): url for url in payload['logFiles']}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    for ts,exceptions in data.items():
                        for exception,count in exceptions.items():
                            timewise_split[ts][exception] += count
                except Exception as exc:
                    print('%r generated an exception: %s' % (url, exc))
        return Response(serialize_timesplits(timewise_split),status=status.HTTP_200_OK)