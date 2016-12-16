"""
Takes in a single har file and outputs a bunch of docs
"""
import sys
import json
import os

def get_headers(response_obj):
    headers = {}
    for header in response_obj["headers"]:
        headers[header["name"]] = header["value"]
    return headers

def har2docs(in_file, output_dir):
    har_data = json.load(open(in_file, 'rb'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 'pair' cause they are request/response pairs
    for pair in har_data["log"]["entries"]:
        content = pair["response"]["content"]
        if int(content["size"]) == 0:
            print content
            print "Size 0"
            continue
        if "text" not in content:
            print "No text"
            continue
        c_type = content.get("mimeType", "other/other").split(';')[0]
        base_type = c_type.split('/')[0]

        # check that output directory exists
        if not os.path.isdir(output_dir + '/' + base_type):
            os.makedirs(output_dir + '/' + base_type)

        # find a name that hasn't been take
        counter = 0
        out_file = output_dir + '/' + c_type + '_'
        while os.path.isfile(out_file + str(counter)): counter += 1
        out_file += str(counter)

        # write the data
        with open(out_file, 'w+') as fd:
            if "encoding" in content and content["encoding"] == "base64":
                fd.write(content["text"].decode('base64'))
            else:
                fd.write(content["text"])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Invalid number of args"
        print "Usage: python har2docs <input-har-file> <output-dir>"
        exit(1)
    reload(sys)
    sys.setdefaultencoding('utf8')
    har2docs(sys.argv[1].rstrip('/'), sys.argv[2].rstrip('/'))