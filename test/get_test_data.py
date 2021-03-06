import sys, os, glob, shutil
import re

OUTPUT_DIR = "input"
TOKENS_DIR = "tokens"
TEST_DATA_DIR = "test_data"
DOCS_DIR = "docs"
IGNORE_DIRS = ["crafted", "token_res"]

TOKEN_RE_FILE = "test_data/token_res" 

FIND_TOKENS = {}
for line in open(TOKEN_RE_FILE, 'rb'):
    site, regex = line.strip().split(' ', 1)
    FIND_TOKENS[site] = re.compile(regex)

def get_files(site_name, data_type):
    files_dir = TEST_DATA_DIR + "/" + site_name + "/" + DOCS_DIR
    return glob.glob(files_dir + "/" + data_type + "*")

def find_tokens(input_file, site_id):
    tokens = set()
    with open(input_file, 'r') as f_ref:
        for line in f_ref:
            for match in FIND_TOKENS[site_id].finditer(line):
                tokens.add(match.group(1))
    return tokens 

def find_all_tokens(site_name):
    files_dir = TEST_DATA_DIR + "/" + site_name + "/" + DOCS_DIR
    tokens = set()
    for data_type in ["text/*", "application/*"]:
        for file_name in glob.iglob(files_dir + "/" + data_type):
            tokens |= find_tokens(file_name, site_name)
    return tokens

def skim_nontoken_files(files, tokens):
    token_re = re.compile(r'|'.join(re.escape(token) for token in tokens))
    new_file_list = []
    for f in files:
        for line in open(f, 'rb'):
            if token_re.search(line):
                new_file_list.append(f)
                break

    return new_file_list

def move_files(files, site_name):
    for f in files:
        shutil.copyfile(f, OUTPUT_DIR + "/" + site_name + "_" + "_".join(f.split('/')[-2:]))

def main(options):
    for f in glob.glob(OUTPUT_DIR + "/*"):
        os.unlink(f)

    for site_name in os.listdir(TEST_DATA_DIR):
        if site_name in IGNORE_DIRS:
            continue

        files = get_files(site_name, options.data_type)

        if options.tokens_only:
            tokens = find_all_tokens(site_name)
            print "Tokens found for " + site_name + ":"
            print tokens
            with open(TOKENS_DIR + "/" + site_name, 'wb') as f_ref:
                f_ref.write("\n".join(tokens))
            files = skim_nontoken_files(files, tokens)

        move_files(files, site_name)

if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-d", "--data-type",
            dest="data_type", default="*/*", help="The data types to extract specified in HTTP format. Ex: 'text/*' gives all text documents. '*/*' gives everything.")
    parser.add_option("-t", "--tokens-only",
            action="store_true", dest="tokens_only", default=False,
            help="Only get test data that contains tokens.")

    (options, args) = parser.parse_args()

    main(options)
