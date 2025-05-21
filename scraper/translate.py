import json
import os
import uuid

import requests

# Add your key and endpoint
key = os.getenv("AZURE")
endpoint = "https://api.cognitive.microsofttranslator.com"

# location, also known as region.
# required if you"re using a multi-service or regional (not global) resource. It can be found in the Azure portal on the Keys and Endpoint page.
location = "australiaeast"

path = "/translate"
constructed_url = endpoint + path

params = {
    "api-version": "3.0",
    "from": "id",
    "to": ["en"]
}

headers = {
    "Ocp-Apim-Subscription-Key": key,
    # location required if you"re using a multi-service or regional (not global) resource.
    "Ocp-Apim-Subscription-Region": location,
    "Content-type": "application/json",
    "X-ClientTraceId": str(uuid.uuid4())
}

# You can pass more than one object in body.
body = [{
    "text": """
    Job Highlights
BPJS Ketenagakerja and BPJS Kesehatan
Possibility of having a career growth
Job Description
HANYA UNTUK ORG TINGGAL DI BANDUNG

Tanggung Jawab

Memeriksa Akurasi dan verifikasi data
Membuat laporan informasi data
Berkomunikasi dan menindaklanjuti dokumen-dokumen dan data input di sistem.
Pengarsipan dan organissi dokumen.
Persyaratan

Pengalaman kerja 2 tahun
Microsoft Office
Akurasi dan Orientasi Detail
Sudah vaksinasi sampai ke 3 / booster
FOR BANDUNG RESIDENCE ONLY

Job Description

Checking accuracy and data verification
Create a data information report
Communicate and follow up documents and input data in the system.
Archiving and organizing documents.
Requirements

Experience 2 years
Microsoft Office
Accuracy and Orientation of Details
Vaccinated until 3rd / booster
Send CV at https://s.id/rockstar
    """
}]

request = requests.post(constructed_url, params=params,
                        headers=headers, json=body)  # type: ignore
response = request.json()

print(json.dumps(response, sort_keys=True,
      ensure_ascii=False, indent=4, separators=(",", ": ")))
