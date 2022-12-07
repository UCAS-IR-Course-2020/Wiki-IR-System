import xml.dom.minidom
import re
import os
import time
from  chinese_t2s import T2S
import multiprocessing

class Process_xml():
    def __init__(self,xml_file_list,save_dir,top_n=-1,one_file_save_max=2000):
        self.start_time=time.time()
        self.latest_time = time.time()
        self.xml_file_list=xml_file_list
        self.top_n=top_n
        self.save_dir=save_dir
        self.one_file_save_max=one_file_save_max
        self.file_id_map_dict={}
        self.file_count=0
        self.word_id_dict={}

    def read(self,file):
        dom = xml.dom.minidom.parse(file)
        self.root = dom.documentElement

    def ch_t2s(self,input,output):
        try:
            T2S(infile=input, outfile=output)
            print("All Finished.")
        except Exception as err:
            print(err)

    ## Show_spend_time
    def show_spend_time(self):
        now_time = time.time()
        print("[Time] {}, {}".format(now_time - self.start_time, now_time - self.latest_time))
        self.latest_time = now_time

    def get_page_in_file_list(self):
        for file in self.xml_file_list:
            self.read(file)
            print('[Info] Getiing page from {}'.format(file))
            self.get_page()

        # ch_t2s
        data_file_list = [file for file in os.listdir(self.save_dir) if file.endswith('process.txt')]
        for data_file in data_file_list:
            print(data_file)
            self.ch_t2s(os.path.join(self.save_dir,data_file),os.path.join(self.save_dir,data_file))

            # del s2s's redirect
            with open(os.path.join(self.save_dir,data_file),'r',encoding='utf-8') as f:
                datas=f.readlines()
            with open(os.path.join(self.save_dir,data_file), 'w', encoding='utf-8') as f:
                for data in datas:
                    if(eval(data)['title']==eval(data)['r_d']):
                        # print(data)
                        pass
                    else:
                        f.write(str(data))

    ## Get every article info from a xml file
    def get_page(self):
        pages=self.root.getElementsByTagName('page') if self.root else []

        file_name='{}_xml_process.txt'.format(self.file_count)
        output = open(os.path.join(self.save_dir,file_name), 'w', encoding='utf-8')
        i = 0
        save_count=0

        for page in pages:
            i += 1
            try:
                page_process=Process_page(page)
                redirect,title,id,page_links,text_abstract_end,category_list=page_process.get_data()
            except:
                continue
            #
            # if('Wikipedia:' in title or 'MediaWiki:' in title or 'Help:' in title):
            #     continue

            page_dict = {}
            page_dict['title']=title
            page_dict['id'] = id
            page_dict['r_d']=redirect
            page_dict['pl']=page_links
            page_dict['a_e']=text_abstract_end
            page_dict['ct']=category_list

            output.write(str(page_dict) + "\n")
            save_count += 1

            # Save file separately
            if(save_count>=self.one_file_save_max):
                save_count=0
                output.close()
                self.file_count+=1
                file_name='{}_xml_process.txt'.format(self.file_count)
                output = open(os.path.join(self.save_dir,file_name), 'w', encoding="utf-8")
                # exit()

            if (self.top_n!=-1 and i >self.top_n):
                break
            if(i%self.one_file_save_max==0):
                print('[complete {}]'.format(i))
        output.close()
        self.file_count += 1
        print('[Info] Get {} page done.'.format(i))
        self.show_spend_time()

    ## Creat a file_id_map dict in data dir
    def creat_file_id_map_dict(self):
        self.file_id_map_data_dict={}
        self.data_file_list = [file for file in os.listdir(save_dir) if file.endswith('process.txt')]
        for file in self.data_file_list:
            with open(os.path.join(self.save_dir,file),'r',encoding='utf-8') as f:
                datas=f.readlines()
            first_id=eval(datas[0])['id']
            last_id=eval(datas[-1])['id']
            num=file.split('_')[0]
            self.file_id_map_data_dict[num]=[first_id,last_id]

        with open(os.path.join(self.save_dir,'file_id_map_dict.txt'),'w') as f:
            f.write(str(self.file_id_map_data_dict))
        print('[Info] Creat file_id_map done.')

    ## Get {title:id} from all process file
    def creat_word_id_map_dict(self):
        data_file_list = [file for file in os.listdir(self.save_dir) if file.endswith('process.txt')]
        # print(data_file_list)
        os.makedirs(os.path.join(self.save_dir, 'word_id_map'), exist_ok=True)


        output={}
        for i in range(1,21):
            output[str(i)]=open(os.path.join(self.save_dir, 'word_id_map',str(i)+'.txt'), 'w', encoding='utf-8')
        other_length=open(os.path.join(self.save_dir, 'word_id_map','other'+'.txt'), 'w', encoding='utf-8')

        for file in data_file_list:
            with open(os.path.join(self.save_dir,file),'r', encoding='utf-8') as f:
                for data in f.readlines():
                    word=eval(data)['title']
                    id=eval(data)['id']
                    length=len(word)
                    if(length<21):
                        output[str(length)].write(word+'\t'+id+'\n')
                    else:
                        other_length.write(word+'\t'+id+'\n')

        for i in range(1,21):
            output[str(i)].close()
        other_length.close()
        print('[Info] Creat word_id_map done.')

    ## Give title,return id
    def title2id_ch(self,word):
        return self.word_id_dict.get(word,None)

    ## Get {id:page_link} from a process file
    def creat_id_pl(self):
        for file in os.listdir(os.path.join(self.save_dir,'word_id_map')):
            # self.word_id_dict[file]=[]
            with open(os.path.join(self.save_dir,'word_id_map',file), 'r', encoding='utf-8') as f:
                for data in f.readlines():
                    [now_word, now_id] = data.strip().split('\t')
                    self.word_id_dict[now_word]=now_id
        print('Total title num',len(self.word_id_dict))

        data_file_list = [file for file in os.listdir(self.save_dir) if file.endswith('process.txt')]

        for file in data_file_list:
            num=file.split('_')[0]
            this_file_id_pl={}
            count=0
            # id_pl = open(os.path.join(self.save_dir, '{}_id_pl.txt'.format(num)), 'w', encoding='utf-8')
            with open(os.path.join(self.save_dir,file),'r', encoding='utf-8') as f:
                for data in f.readlines():
                    count+=1
                    now_dict=eval(data)
                    page_link = now_dict['pl']
                    id = now_dict['id']
                    page_link_id_list=[]
                    for link_word in page_link:
                        if(link_word!=''):
                            page_link_id=self.title2id_ch(link_word)
                            if(page_link_id!=None):
                                page_link_id_list.append(page_link_id)
                    this_file_id_pl[id]=page_link_id_list

            with open(os.path.join(self.save_dir, '{}_id_pl.txt'.format(num)), 'w', encoding='utf-8') as f:
                f.write(str(this_file_id_pl))

            print('[Info] get id_pl from {}.'.format(file))
            self.show_spend_time()











class Process_page():
    def __init__(self,page):
        title_node = self.get_xmlnode(page, 'title')
        self.title = self.get_nodevalue(title_node[0])
        id_node = self.get_xmlnode(page, 'id')
        self.id = self.get_nodevalue(id_node[0])
        text_node = self.get_xmlnode(page, 'text')
        self.text = self.get_nodevalue(text_node[0])
        self.page_link=[]
        self.text_list=[]
        self.text_abstract_end='0'
        self.category_text_list=[]
        self.category_list = []
        try:
            redirect_node=self.get_xmlnode(page,'redirect')
            self.redirect=self.get_attrvalue(redirect_node[0],'title')
        except:
            self.redirect=''

    def get_attrvalue(self,node, attrname):
        return node.getAttribute(attrname) if node else ''

    def get_nodevalue(self,node, index=0):
        return node.childNodes[index].nodeValue if node else ''

    def get_xmlnode(self,node, name):
        return node.getElementsByTagName(name) if node else []

    def get_data(self):
        if(self.redirect!=''):
            self.text_main=''
        else:
            self.text_clear(self.text)
        return self.redirect,self.title,self.id,self.page_link,self.text_abstract_end,self.category_list

    def string_clear(self,this_str):
        result = re.sub(r'<ref.*?</ref>', '', this_str)

        pattern = re.compile(r'\[\[.*?\]\]?')
        result_list = pattern.findall(result)
        for state in result_list:
            new_state = re.sub(r'\[\[|]]', '', state)
            new_state = new_state.split('|')[-1]
            result = result.replace(state, new_state, 1)

        result = re.sub(r'{{.*?}}', '', result)
        result = re.sub(r'<.*?>', '', result)
        result = re.sub(r'\'\'\'|}}|{{|;|\|', '', result)
        result = re.sub(r' {2,}', '', result)
        result = re.sub(r',{2,}', '', result)
        result = re.sub(r'\(\)|\(, \)|\( \)| , |\( ,\)|\(,\)', '', result)

        result = re.sub(r'\(,|\(, |\( ,|\( ', '(', result)
        result = re.sub(r', \)|,\)| \)', ')', result)
        result=re.sub(r'\(\)|\(\'\'\)|\(\'\)', '', result)

        return result

    def extract_page_link(self,this_str):
        now_page_link = []
        result = re.sub(r'<ref.*?</ref>', '', this_str)
        pattern = re.compile(r'\[\[.*?\]\]?')
        result_list = pattern.findall(result)
        for state in result_list:
            new_state = re.sub(r'\[\[|]]', '', state)
            new_state = new_state.split('|')[0]
            new_state=new_state.split('#')[0]
            now_page_link.append(new_state)

        return now_page_link

    def page_link_generate(self,text_list):
        # chose main text
        main_text_list=['']
        text_start = False
        for sent in text_list:
            if((not sent[0].isalpha()) and (not sent.startswith('\'\'\''))):
                pass
            if ((sent[0].isalpha()) or (sent.startswith('\'\'\''))):
                text_start=True
            if(text_start):
                rule1 = re.compile(r'^<!--.*?-->$')
                rule2=re.compile(r'^{{.*?}}$')
                rule3=re.compile(r'^[\u4E00-\u9FFF].*$')
                if(rule1.match(sent) is None and rule2.match(sent) is None):
                    # if(sent.startswith('</ref>') or main_text_list[-1].endswith('<ref>') or sent.startswith('|') or sent.startswith(' |') or sent.startswith(' }}') or sent.startswith('}}')):
                    # print(rule3.match(sent) is None,sent)
                    if( (rule3.match(sent) is None) and not(sent.startswith('{') or sent.startswith('[') or sent.startswith('('))):

                        main_text_list[-1]+=sent
                    else:
                        main_text_list.append(sent)
        # print(main_text_list)

        for sent in main_text_list:
            # print(sent)
            if(sent!='' and '[[Category' not in sent):
                # self.text_main=self.text_main+self.string_clear(sent)+'\t'
                self.page_link.extend(self.extract_page_link(sent))

        self.text_abstract_end=str(len(main_text_list))
        # print(self.text_abstract_end)

    def category_generate(self,category_text_list):
        for sent in category_text_list:
            category=re.split(':|]]|\|',sent)[1]
            self.category_list.append(category)

    def text_clear(self,text):
        infobox_note = False
        text_note = True
        text_end=False
        empty_note=True
        for sent in text.split('\n'):
            if (sent.startswith('==')):
                text_end=True
            if(sent.startswith('[[Category')):
                self.category_text_list.append(sent)
                continue
            if(('{{Infobox' in sent) and empty_note):
                infobox_note=True
                empty_note=False
                self.text_list=[]
                text_note=False
            if(infobox_note and sent=='}}'):
                infobox_note=False
                text_note=True
            if(text_note and sent!=''and not text_end):
                self.text_list.append(sent)

        if(self.text_list!=[]):
            self.page_link_generate(self.text_list)
        if(self.category_text_list!=[]):
            self.category_generate(self.category_text_list)

if __name__=='__main__':
    file_list= ['zhwiki/wikiextractor-master/zhwiki-20200420-pages-articles-multistream1.xml-p1p162886',
                'zhwiki/wikiextractor-master/zhwiki-20200420-pages-articles-multistream2.xml-p162887p544644']

    # save_dir='zhwiki/xml_result' 
    save_dir='../data/xml_result/zn/xml_result'
    os.makedirs(save_dir,exist_ok=True)

    process_file=Process_xml(file_list,save_dir,top_n=-1,one_file_save_max=10000)
    process_file.get_page_in_file_list()
    process_file.creat_file_id_map_dict()
    process_file.creat_word_id_map_dict()
    process_file.creat_id_pl()


