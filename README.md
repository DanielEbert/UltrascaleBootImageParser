# Ultrascale Boot Image Parser

Extract information from a Ultrascale Boot Image in human readable format.

### Install

~~~
python3 -m pip install -r requirements.txt
~~~

### Run

~~~
./main.py --boot_image_bin example/boot.bin --parsed_json output.json
~~~

Read the output.json file with e.g. your test editor or jq:
~~~

jq . output.json
~~~
