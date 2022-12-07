import sys
import os
import opencc
from optparse import OptionParser


class T2S(object):
    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile
        self.cc = opencc.OpenCC('t2s')
        self.t_corpus = []
        self.s_corpus = []
        self.read(self.infile)
        self.t2s()
        self.write(self.s_corpus, self.outfile)

    def read(self, path):
        if os.path.isfile(path) is False:
            print("path is not a file")
            exit()
        now_line = 0
        with open(path, encoding="UTF-8") as f:
            for line in f:
                now_line += 1
                line = line.replace("\n", "").replace("\t", "")
                self.t_corpus.append(line)
        print("read finished")

    def t2s(self):
        now_line = 0
        all_line = len(self.t_corpus)
        for line in self.t_corpus:
            now_line += 1
            if now_line % 1000 == 0:
                sys.stdout.write("\rhandling with the {} line, all {} lines.".format(now_line, all_line))
            self.s_corpus.append(self.cc.convert(line))
        sys.stdout.write("\rhandling with the {} line, all {} lines.".format(now_line, all_line))
        print("\nhandling finished")

    def write(self, list, path):
        print("writing now......")
        if os.path.exists(path):
            os.remove(path)
        file = open(path, encoding="UTF-8", mode="w")
        for line in list:
            file.writelines(line + "\n")
        file.close()
        print("writing finished.")


if __name__ == "__main__":
    print("Traditional Chinese to Simplified Chinese")
    
    # input_dir = "zhwiki/wikiextractor-master/text/stream1"
    # output_dir = "zhwiki/wikiextractor-master/text/stream1_simple"
    input_dir = "zhwiki/wikiextractor-master/text/stream2"
    output_dir = "zhwiki/wikiextractor-master/text/stream2_simple"

    os.makedirs(output_dir,exist_ok=True)
    # T2S(infile=input, outfile=output) 

    # parser = OptionParser()
    # parser.add_option("--input", dest="input", default="", help="traditional file")
    # parser.add_option("--output", dest="output", default="", help="simplified file")
    # (options, args) = parser.parse_args()
    #
    # input = options.input
    # output = options.output

    for file in os.listdir(input_dir):
        input=os.path.join(input_dir,file)
        output=os.path.join(output_dir,file)

        try:
            T2S(infile=input, outfile=output)
            print("All Finished.")
        except Exception as err:
            print(err)