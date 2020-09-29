import gc
import os
import html
import argparse
import collections
import defusedxml.ElementTree as DET

class UnescapeEntity():
    def __getitem__(self, key):
        return html.unescape(key)

parser = argparse.ArgumentParser()
parser.add_argument("-x", "--xml", type=str, help="The XML File")
parser.add_argument("-t", "--tag", type=str, help="The tag")
parser.add_argument("-k", "--keepfield", type=str, default="", help="fileds to keep, split by comma ',' ")
parser.add_argument("-s", "--speparator", type=str, default="\t", help="the separator between each field. Please don't use comma ',' ")
parser.add_argument("-o", "--output", type=str, default=None, help="output file.")
parser.add_argument("-d", "--dtd", type=str, default=None, help="The dtd file. All avaliable files will be listed")
args = parser.parse_args()

parser = DET.XMLParser()
parser.parser.UseForeignDTD(True)
parser.entity = UnescapeEntity()



def read_dtd_line(dtd):
    line = ""
    mark = 0
    while True:
        c = dtd.read(1)
        if c == "":
            break
        elif c == "<":
            mark += 1
        elif c == ">":
            mark -= 1
            if mark <= 0:
                line += c
                break
        
        if mark > 0 and c != "\n":
            line += c
    
    return line

def read_dtd_line_iter(dtdname, nocomment=True) -> str:
    if dtdname is None or not os.path.isfile(dtdname):
        yield ""
        return
    dtdfile = open(dtdname, "r")
    line = ""
    while True:
        line = read_dtd_line(dtdfile)
        if line == "":
            break
        if nocomment and line[0:4] == "<!--":
            continue
        yield line
    dtdfile.close()


if not args.dtd is None:
    # create glbal dict
    allfields = []
    maxlen = 0
    for line in read_dtd_line_iter(args.dtd): # type:str
        if not line.startswith("ELEMENT", 2):
            continue
        lineme = line.split(" ", 3)
        allfields.append(lineme[1])
        maxlen = max(maxlen, len(lineme[1]))

    print("fields:\n")
    for i, fid in enumerate(sorted(allfields)):
        print(fid.ljust(maxlen), end="")
        if i % 6 == 5:
            print("\n", end="")
        else:
            print("\t", end="")
    print("\n\n")
    exit(0)

allfields = args.keepfield.split(",")
dictGlobal = collections.OrderedDict([
    (k, i) for i, k in enumerate(allfields)
])
buflistGlobal = ["" for _ in allfields]

outfilename = args.output

if outfilename is None:
    cnt = 0
    while True:
        outfilename = "{}-{:03d}.txt".format(args.xml, cnt)
        if not os.path.exists(outfilename):
            break
        else:
            cnt += 1

tsvOut = open(outfilename, "w")
tsvOut.write(args.speparator.join(allfields))
tsvOut.write("\n")
tsvOut.flush()

vaildfield = False
index = 0
for event, node in DET.iterparse(args.xml, parser=parser):
    # print(event, node.tag)
    if node.tag == args.tag and vaildfield:
        vaildfield = False
        # write
        ibg = dictGlobal[node.tag]
        tsvOut.write(args.speparator.join(buflistGlobal[ibg]))
        tsvOut.write("\n")

        index += 1

        # clear current dict
        buflistGlobal.clear()
        del buflistGlobal
        buflistGlobal = ["" for _ in allfields]
        if index % (1<<10) == 0:
            print("\rrunning {}".format(index).ljust(8), end="")
            gc.collect()
            tsvOut.flush()


    else:
        text = node.text # type: str
        if (text is None) or text.isspace() or (not node.tag in dictGlobal):
            continue
        vaildfield = True
        text = text.strip().replace("\n", "").replace("\t", " ")
        ibg = dictGlobal[node.tag]
        if buflistGlobal[ibg] != "":
            buflistGlobal[ibg] += ", " + text
        else:
            buflistGlobal[ibg] = text
        
tsvOut.close()






