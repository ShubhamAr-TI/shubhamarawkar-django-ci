import concurrent.futures
import urllib.request
from collections import defaultdict
from datetime import datetime

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def validate_input(data):
    if 'logFiles' not in data:
        raise ValidationError("Log Files is required")
    if 'parallelFileProcessingCount' not in data:
        raise ValidationError("Parallel File Processing count is required")
    if data['parallelFileProcessingCount'] <= 0:
        raise ValidationError(
            "Parallel File Processing count must be greater than zero!")


def load_url(url, timeout):
    timewise_split = defaultdict(lambda: defaultdict(lambda: 0))
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        for line in conn:
            if line[-2:] == b'\r\n':
                line = line[:-2]
            timestamp, exception = int(line[13:26].decode(
                'utf-8')), line[27:].decode('utf-8')
            dt = datetime.fromtimestamp(
                timestamp // (1000 * 60 * 15) * 60 * 15)
            timewise_split[dt][exception] += 1
    return timewise_split


def serialize_timesplits(data):
    formatted = []
    for dt, exceptions in data.items():
        obj = {}
        obj["ts"] = dt
        obj["logs"] = []
        for exception, count in exceptions.items():
            obj["logs"].append({
                "exception": exception,
                "count": count
            })
        obj["logs"].sort(key=lambda x: x["exception"])
        formatted.append(obj)
    formatted.sort(key=lambda x: x["ts"])
    for x in formatted:
        dt = x['ts']
        (hr, mn) = dt.hour, dt.minute
        nhm = mn + 15
        nhr = (hr + nhm // 60) % 24
        nhm = nhm % 60

        x["timestamp"] = "{:02d}:{:02d}-{:02d}:{:02d}".format(hr, mn, nhr, nhm)
        del x['ts']

    return {"response": formatted}


def aggregate_data(data, timewise_split):
    for ts, exceptions in data.items():
        for exception, count in exceptions.items():
            timewise_split[ts][exception] += count


class ProcessLogs(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        # logger.error(json.dumps(request.data))
        try:
            validate_input(payload)
        except ValidationError as ve:
            print(ve)
            return Response({
                "status": "failure",
                "reason": ve.message
            }, status=status.HTTP_400_BAD_REQUEST)
        timewise_split = defaultdict(lambda: defaultdict(lambda: 0))
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=payload['parallelFileProcessingCount'])
        # Start the load operations and mark each future with its URL
        future_to_url = {
            executor.submit(
                load_url,
                url,
                60): url for url in payload['logFiles']}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            data = future.result()
            aggregate_data(data, timewise_split)

        return Response(
            serialize_timesplits(timewise_split),
            status=status.HTTP_200_OK)


class RemoteLogs(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("this stuff", request.data)
        return Response(status=status.HTTP_204_NO_CONTENT)
