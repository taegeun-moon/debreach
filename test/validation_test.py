import os
import re
import mmap
from optparse import OptionParser

INPUT_DIR='./input'

site_REs = {
        'gmail' : re.compile(r'GM_ACTION_TOKEN="(\w*)"')
}

def validate_validation():
    for in_file in os.listdir(INPUT_DIR):
        full_file = INPUT_DIR + '/' + in_file
        print "Processing: " + full_file
        os.system('../minigzip ' + full_file)
        compressed_file = full_file + '.gz'
        br_file =  'decompbrs/' + in_file
        os.system('../minigzip -d ' + compressed_file + ' 2> ' + br_file)
        if not check_br_records(INPUT_DIR + '/' + in_file, br_file):
            print "Byte range check failed. Quitting."
            exit(1)


"""
Needs zlib to be compiled with -DVALIDATE_SEC.
"""
def check_br_records(in_file, br_file):
    with open(in_file, 'rb') as decomp_fd, open(br_file, 'rb') as br_fd:
        dcf_buf = decomp_fd.read()
        while True:
            # see if we got anything left
            br_buf = br_fd.read(1)
            if not br_buf:
                break
            # read two spaces
            first_space = True
            while True:
                temp = br_fd.read(1)
                if temp == ' ' and not first_space:
                    break
                elif temp == ' ':
                    first_space = False
                br_buf += temp

            br1, br2 = br_buf.split(' ', 1)
            br1 = map(int, br1.split('-', 1))
            br2 = map(int, br2.split('-', 1))
            match_len = br1[1] - br1[0] + 1
            # + 1 because we add a new line in output
            matched_string = br_fd.read(match_len + 1)
            # chomp the extra new line
            matched_string = matched_string[:-1]

            if matched_string != dcf_buf[br1[0]:br1[1] + 1]:
                print "Mismatch for br1: "
                print br1
                print "Actual string: " + matched_string
                print "Found: " + dcf_buf[br1[0]:br1[1] + 1]
                print "Found2: " + dcf_buf[br2[0]:br2[1] + 1]
                return False
            if matched_string != dcf_buf[br2[0]:br2[1] + 1]:
                print "Mismatch for br2:"
                print br2
                print "Actual string: " + matched_string
                print "Found: " + dcf_buf[br2[0]:br2[1] + 1]
                return False
        return True

def find_token(input_file, site_id):
    with open(input_file, 'r') as f_ref:
        for line in f_ref:
            match = site_REs[site_id].search(line)
            if match:
                return match.group(1) 
    return None 

# http://stackoverflow.com/questions/6980969/how-to-find-position-of-word-in-file
def find_byte_ranges(input_file, token):
    brs = []
    with open(input_file, 'rb') as f_ref:
        # 0 means the whole file
        mf = mmap.mmap(f_ref.fileno(), 0, prot=mmap.PROT_READ)
        mf.seek(0)
        for match in re.finditer(token, mf):
            brs.append(match.start())
            brs.append(match.end())
    return brs 

def validate_security(input_file, token, num_tokens):
    print "Validating security of " + input_file + " with token " + token
    with open(input_file, 'rb') as f_ref:
        mf = mmap.mmap(f_ref.fileno(), 0, prot=mmap.PROT_READ)
        mf.seek(0)
        found_tokens = 0
        for _ in re.finditer(token, mf):
            found_tokens += 1
        print "Found " + str(found_tokens) + " tokens in compressed file"
        injections_found = True
        injection_file = ('injections/' + input_file.split('/')[-1]).replace('.gz', '')
        if os.path.isfile(injection_file):
            injections = None
            with open(injection_file, 'rb') as inj_f_ref:
                injections = inj_f_ref.read().strip().split(' ')
            mf.seek(0)
            print "Checking injections"
            for injection in injections:
                if not re.search(injection, mf):
                    print "Error: did not find " + injection + " in output"
                    injections_found = False
                    break
                print "Found: " + injection

    return num_tokens == found_tokens and injections_found

br_RE = re.compile(r'^byteranges: [0-9 ]*$')
def validate_brs(br_file, tokens):
    with open(br_file, 'rb') as f_ref:
        line = f_ref.readline()
        while True:
            if not line:
                break
            if br_RE.search(line):
                _, brs_str = line.split(':', 1)
                brs_str = brs_str.strip()

                if not brs_str:
                    line = f_ref.readline()
                    continue

                brs = [int(b) for b in brs_str.split(' ')]

                line = f_ref.readline()
                buf = ""
                while line and not br_RE.search(line):
                    buf += line
                    line = f_ref.readline()

                for i in xrange(0, len(brs), 2):
                    print buf[brs[i]:brs[i+1] + 1]
            line = f_ref.readline()
    # Always True for now, until we implement some type of actual
    # validtion test
    return True

def clear_dirs():
    os.system('rm output/*')
    os.system('rm output_lits/*')
    os.system('rm debug/*')
    os.system('rm brs/*')
    os.system('rm input/*.gz')

def stored_test():
    clear_dirs()
    for in_file in os.listdir(INPUT_DIR):
        site_id = in_file.split('_')[0]
        print "Processing file: " + in_file
        if site_id not in site_REs:
            print "Error: no regex found for site_id=" + site_id
            exit(1)

        token = find_token(INPUT_DIR + '/' + in_file, site_id)

        if not token:
            print "Error: no token found"
            exit(1)

        tokens = [token]
        byte_ranges = find_byte_ranges(INPUT_DIR + '/' + in_file, token)
        num_tokens = len(byte_ranges) / 2
        print "Num tokens: " + str(num_tokens)
        # run debreach on the test file
        print '../minidebreach-stored -s ' + ','.join(tokens) + ' ' + INPUT_DIR + '/' + in_file + ' 1> output_lits/' + in_file + ' 2> debug/' + in_file
        os.system('../minidebreach-stored -s ' + ','.join(tokens) + ' ' + INPUT_DIR + '/' + in_file + ' 1> output_lits/' + in_file + ' 2> debug/' + in_file)
        os.system('mv ' + INPUT_DIR + '/' + in_file + '.gz output')
        # ensure that we find the token present in the literal output
        # the correct number of times
        if not validate_security('output/' + in_file + '.gz', token, num_tokens):
            print "Error: security validation failed"
            exit(1)
        # validate integreity
        continue
        ret = os.system('gunzip output/' + in_file + '.gz')
        if ret != 0:
            print "Error: non-zero exit status from gunzip"
            exit(1)


def brs_only():
    clear_dirs()
    for in_file in os.listdir(INPUT_DIR):
        site_id = in_file.split('_')[0]
        print "Processing file: " + in_file
        if site_id not in site_REs:
            print "Error: no regex found for site_id=" + site_id
            exit(1)

        token = find_token(INPUT_DIR + '/' + in_file, site_id)

        if not token:
            print "Error: no token found"
            exit(1)
        tokens = [token]
        print "Tokens found: " + ','.join(tokens)
        print '../minidebreach -s ' + ','.join(tokens) + ' ' + INPUT_DIR + '/' + in_file + ' 1> brs/' + in_file
        os.system('../minidebreach -s ' + ','.join(tokens) + ' ' + INPUT_DIR + '/' + in_file + ' 1> brs/' + in_file)
        os.system('mv ' + INPUT_DIR + '/' + in_file + '.gz output')

        # validate the brs
        if not validate_brs('brs/' + in_file, tokens):
            print "Error: bad tainted region"

def full_test():
    clear_dirs()
    for in_file in os.listdir(INPUT_DIR):
        site_id = in_file.split('_')[0]
        print "Processing file: " + in_file
        if site_id not in site_REs:
            print "Error: no regex found for site_id=" + site_id
            exit(1)

        token = find_token(INPUT_DIR + '/' + in_file, site_id)

        if not token:
            print "Error: no token found"
            exit(1)
        print "Token found: " + token
        tokens = [token]
        byte_ranges = find_byte_ranges(INPUT_DIR + '/' + in_file, token)
        num_tokens = len(byte_ranges) / 2
        print "Num tokens: " + str(num_tokens)
        # run debreach on the test file
        print '../minidebreach -s ' + ','.join(tokens) + ' ' + INPUT_DIR + '/' + in_file + ' 1> output_lits/' + in_file + ' 2> debug/' + in_file
        os.system('../minidebreach -s ' + ','.join(tokens) + ' ' + INPUT_DIR + '/' + in_file + ' 1> output_lits/' + in_file + ' 2> debug/' + in_file)
        os.system('mv ' + INPUT_DIR + '/' + in_file + '.gz output')
        # ensure that we find the token present in the literal output
        # the correct number of times
        if not validate_security('output_lits/' + in_file, token, num_tokens):
            print "Error: security validation failed"
            exit(1)
        # validate integreity
        ret = os.system('gunzip output/' + in_file + '.gz')
        if ret != 0:
            print "Error: non-zero exit status from gunzip"
            exit(1)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-b", "--brs-only",
                        action="store_true", dest="brs_only", default=False,
                        help="Only very the byte ranges. Remember to compile with -DBRS_ONLY")
    parser.add_option("-s", "--stored",
                        action="store_true", dest="stored_test", default=False,
                        help="Test the debreach stored module")
    parser.add_option("-v", "--validate-validation",
                        action="store_true", dest="valval", default=False,
                        help="Validate the validation module lol")
    (options, args) = parser.parse_args()
    if options.brs_only:
        brs_only()
    elif options.stored_test:
        stored_test()
    elif options.valval:
        validate_validation()
    else:
        full_test()

