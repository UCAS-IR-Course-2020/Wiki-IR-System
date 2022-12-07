import os
import time
import string
import math
import pickle
import multiprocessing
import json

class Process_data():
    def __init__(self,data_dir,xml_result_dir,save_reverse_index_dir,stop_word_list,only_english=False):
        self.start_time=time.time()
        self.latest_time = time.time()
        self.data_dir=data_dir
        self.xml_result_dir=xml_result_dir
        self.save_dir=save_reverse_index_dir
        self.stop_word_list=stop_word_list
        self.only_english=only_english

        # Get wiki data file list
        stream_dir_list=[file for file in os.listdir(data_dir)]
        self.data_file_list=[]
        for stream_dir in stream_dir_list:
            if('stream' in stream_dir):
                self.data_file_list.extend([os.path.join(stream_dir,file)
                                            for file in os.listdir(os.path.join(data_dir,stream_dir)) if file.startswith('wiki')])
        print('[Info] Total {} file in data dir.'.format(len(self.data_file_list)))

        # Get xml result file list
        self.xml_result_file_list = [file for file in os.listdir(self.xml_result_dir) if file.endswith('process.txt')]
        print('[Info] Total {} file in xml result.'.format(len(self.xml_result_file_list)))

        with open(os.path.join(xml_result_dir,'file_id_map_dict.txt'),'r',encoding='utf-8') as f:
            self.file_id_map_xml_result=eval(f.readline())

        ## creat_file_id_map_data
        if(not os.path.exists(os.path.join(data_dir,'file_id_map_dict.txt'))):
            self.creat_file_id_map_dict()

        self.word_reverse_index = {}
        self.article_num=0
        self.word_id=-1
        self.category_reverse_index = {}
        self.category_id = -1
        self.category_num=0

    ## Show_spend_time
    def show_spend_time(self):
        now_time = time.time()
        print("[Time] {}, {}".format(now_time - self.start_time, now_time - self.latest_time))
        self.latest_time = now_time

    ## Creat a file_id_map dict in data dir
    def creat_file_id_map_dict(self):
        self.file_id_map_data_dict={}
        for file in self.data_file_list:
            with open(os.path.join(self.data_dir,file),'r',encoding='utf-8') as f:
                datas=f.readlines()
            first_id=eval(datas[0])['id']
            last_id=eval(datas[-1])['id']
            self.file_id_map_data_dict[file]=[first_id,last_id]

        with open(os.path.join(self.data_dir,'file_id_map_dict.txt'),'w') as f:
            f.write(str(self.file_id_map_data_dict))

    ## Find word from xml result, include: [title,id,redirect,page_link,abstract_end]
    def find_word_in_xml_result(self,id):
        for key,value in self.file_id_map_xml_result.items():
            now_file = str(key) + '_xml_process.txt'
            if(int(value[0])<=int(id)<=int(value[1])):
                with open(os.path.join(self.xml_result_dir,now_file),'r',encoding='utf-8') as f:
                    for data in f.readlines():
                        now_dict=eval(data)
                        if(id==now_dict['id']):
                            return now_dict
                return None
        return None

    ## Get abstract from text
    def get_abstract(self,id,text_list):
        word=self.find_word_in_xml_result(id)
        if(word!=None):
            abstract_end=word['a_e']
            # print(word['id'],word['title'],abstract_end)
            if(int(abstract_end)>=1):
                return text_list[1:int(abstract_end)+1]
            else:
                return text_list[1:4]
        else:
            return None

    ## Get word_reverse_index from one file in data_dir
    def get_word_reverse_index_from_one_file(self,file):
        self.word_reverse_index = {}
        # Word stay or not
        def word_is_stay(word, only_english):
            if (word in self.stop_word_list or len(word) == 0 or len(word) > 30):
                return False

            if (only_english):
                if (word.encode('utf-8').isalpha()):
                    return True
                else:
                    return False
            else:
                return True

        with open(file,'r',encoding='utf-8') as f:
            for data in f.readlines():
                self.article_num+=1
                now_dict=eval(data)
                id=now_dict['id']
                # print(now_dict['text'])
                total_text_list=now_dict['text'].split('\n')

                use_text_list=[]
                for sent in total_text_list:
                    if(sent!='' and sent!='\n'):
                        use_text_list.append(sent)
                abstract=self.get_abstract(id,use_text_list)
                abstract=' '.join(abstract).translate(str.maketrans('', '', string.punctuation))
                now_lis=[]
                for word in abstract.split(' '):
                    if (word_is_stay(word, self.only_english)):
                        now_lis.append(word)

                for word_index in range(len(now_lis)):
                    now_word = now_lis[word_index].lower()
                    if (now_word) not in self.word_reverse_index:
                        self.word_id+=1
                        self.word_reverse_index[now_word] = {'wi':self.word_id,'Attr':{}}
                    if (id not in self.word_reverse_index[now_word]['Attr']):
                        self.word_reverse_index[now_word]['Attr'][id] = [word_index]
                    else:
                        self.word_reverse_index[now_word]['Attr'][id].append(word_index)


        save_path=os.path.join(self.save_dir,file.split('\\')[-2]+'_'+file.split('\\')[-1]+'_word_reverse_index.txt')
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(str(self.word_reverse_index))
        print('[Info] {} get word_reverse_index done'.format(file.split('\\')[-2]+'_'+file.split('\\')[-1]))
        self.show_spend_time()


    def get_multi_data_file_list(self):
        return self.data_file_list

    ## Get word_reverse_index from data_dir
    def get_word_reverse_index(self):
        ## Merge word_reverse_index
        file_list = [file for file in os.listdir(self.save_dir) if 'wiki' in file]
        print('[Info] Total wiki word_reverse_index {}'.format(len(file_list)))
        self.word_reverse_index = {}
        self.word_id=-1
        for file in file_list:
            with open(os.path.join(self.save_dir, file), 'r', encoding='utf-8') as f:
                now_dict = eval(f.readline())
            for key,value in now_dict.items():
                key=key.strip()
                if(key not in self.word_reverse_index):
                    self.word_id+=1
                    self.word_reverse_index[key]={'wi':str(self.word_id),'Attr':value['Attr']}
                else:
                    self.word_reverse_index[key]['Attr'].update(value['Attr'])
            print('[Info] Merge {} done'.format(file))


        print('[Info] Get {} words.'.format(len(self.word_reverse_index)))
        self.show_spend_time()

        ## Save word_reverse_index_no_idf
        no_idf_path=os.path.join(self.save_dir, 'word_reverse_index_no_idf.txt')
        with open(no_idf_path, 'w', encoding='utf-8') as f:
            for key,value in self.word_reverse_index.items():
                f.write(key+'\t'+json.dumps(value)+'\n')
        print('[Info] Get word_reverse_index without tfidf done.')
        self.show_spend_time()
        del self.word_reverse_index

    ## Get word_reverse_index with tfidf
    def get_word_reverse_index_with_tfidf(self):
        # Calculate tf_idf
        def generate_tf_idf(one_word_dict):
            idf = round(math.log(article_num / len(one_word_dict), 10), 4)
            new_dict = {}
            for id, location_list in one_word_dict.items():
                one_article_dict = {}
                one_article_dict['lc'] = location_list
                tf = round((1 + math.log(len(location_list), 10)), 4)
                tf_idf = round(tf * idf, 4)
                one_article_dict['tfidf'] = [tf, tf_idf]
                new_dict[id] = one_article_dict
            return new_dict,idf

        # Get article_num
        article_num = 0
        for file in self.data_file_list:
            with open(os.path.join(self.data_dir, file), 'r', encoding='utf-8') as f:
                article_num += len(f.readlines())
        print('[Info] Total article num {} in {} files'.format(article_num,len(self.data_file_list)))


        no_idf_path=os.path.join(self.save_dir, 'word_reverse_index_no_idf.txt')
        save_path=os.path.join(self.save_dir,'word_reverse_index.txt')
        pure_path = save_path[:-4] + '_pure.txt'

        # Get word num
        word_count = -1
        for word_count, line in enumerate(open(no_idf_path, 'rU',encoding='utf-8')):
            pass
        word_count += 1
        print('[Info] Total word num {} in word_reverse_index'.format(word_count))

        # f_all: word id, article id, tfidf, location
        # f_pure: word id, article id, tfidf
        f_all=open(save_path, 'w', encoding='utf-8')
        f_pure=open(pure_path, 'w', encoding='utf-8')
        with open(no_idf_path, 'r', encoding='utf-8') as f:
            for data in f.readlines():
                key=data.split('\t')[0]
                value = json.loads(data.split('\t')[1])
                value['Attr'], idf = generate_tf_idf(value['Attr'])
                value['idf']=idf
                f_all.write(key + '\t' + json.dumps(value) + '\n')

                now_attr={}
                for id,id_value in value['Attr'].items():
                    now_attr[id]=id_value['tfidf']
                pure_value= {'wi': value['wi'], 'Attr': now_attr,'idf':value['idf']}
                f_pure.write(key + '\t' + json.dumps(pure_value) + '\n')

        print('[Info] Get tf-idf done.')
        print('[Info] Save word_reverse_index_pure done.')
        print('[Info] Save word_reverse_index done.')
        self.show_spend_time()
        f_all.close()
        f_pure.close()


    ## Get category_reverse_index from one file in data_dir
    def get_category_reverse_index_from_one_file(self,file):
        # Word stay or not
        def category_is_stay(word, only_english):
            if (word in self.stop_word_list or len(word) == 0 or len(word) > 30):
                return False
            if (only_english):
                if (word.encode('utf-8').isalpha()):
                    return True
                else:
                    return False
            else:
                return True

        with open(file,'r',encoding='utf-8') as f:
            for data in f.readlines():
                self.article_num+=1
                now_dict=eval(data)
                id = now_dict['id']
                title=now_dict['title']
                ct=now_dict['ct']
                # ct.extend(title.split(':'))
                # total_category_list=' '.join(ct).translate(str.maketrans('', '', string.punctuation)).split(' ')
                total_category_list = ' '.join(ct).split(' ')

                use_category_list = []
                for category in total_category_list:
                    category=category.lower()
                    if(category_is_stay(category,only_english=False)):
                        use_category_list.append(category)
                now_lis=use_category_list

                if(len(now_lis)>0):
                    self.category_num+=1
                else:
                    continue

                for category_index in range(len(now_lis)):
                    now_category = now_lis[category_index]
                    now_category = now_category.strip()
                    if (now_category) not in self.category_reverse_index:
                        self.category_id+=1
                        self.category_reverse_index[now_category] = {'ci':self.category_id,'Attr':{}}
                    if (id not in self.category_reverse_index[now_category]['Attr']):
                        self.category_reverse_index[now_category]['Attr'][id] = [category_index]
                    else:
                        self.category_reverse_index[now_category]['Attr'][id].append(category_index)


    ## Get category_reverse_index from data_dir
    def get_category_reverse_index(self,save_dir,stop_word_list,only_english=False):

        # Calculate tf_idf
        def generate_tf_idf(one_word_dict):
            idf = round(math.log(self.category_num / len(one_word_dict), 10), 4)
            new_dict = {}
            for id, location_list in one_word_dict.items():
                one_article_dict = {}
                one_article_dict['lc'] = location_list
                tf = round((1 + math.log(len(location_list), 10)), 4)
                tf_idf = round(tf * idf, 4)
                one_article_dict['tfidf'] = [tf, tf_idf]
                new_dict[id] = one_article_dict
            return new_dict,idf

        self.stop_word_list=stop_word_list
        self.only_english=only_english
        for file in self.xml_result_file_list:
            self.get_category_reverse_index_from_one_file(os.path.join(self.xml_result_dir,file))
            print('[Info] get category_reverse_index from {}'.format(file))
            self.show_spend_time()
        print('[Info] Get {} categorys in category_reverse_index.'.format(len(self.category_reverse_index)))

        # Get tf_idf
        print('total category num (article num):', self.category_num)
        for key,value in self.category_reverse_index.items():
            value['Attr'],idf=generate_tf_idf(value['Attr'])
            value['idf']=idf
            self.category_reverse_index[key]=value
        print('[Info] Get tf-idf done.')

        save_path = os.path.join(save_dir, 'category_reverse_index.txt')
        with open(save_path, 'w', encoding='utf-8') as f:
            for key,value in self.category_reverse_index.items():
                f.write(key+'\t'+json.dumps(value)+'\n')
        print('[Info] Save category_reverse_index done.')




if __name__=='__main__':

    data_dir = '../data/xml_result/en/wikiextractor-master/text'
    xml_result_dir='../data/xml_result/en/xml_result'
    save_reverse_index_dir='../data/inverted_index/en'

    os.makedirs(save_reverse_index_dir, exist_ok=True)

    stop_word_list=[]
    with open('stop_word.txt','r') as f:
        for data in f.readlines():
            stop_word_list.append(data.strip())
    print('stop_word_num',len(stop_word_list))


    data_process=Process_data(data_dir,xml_result_dir,save_reverse_index_dir,stop_word_list,only_english=True)

    ###############################
    #  Get category_reverse_indexx from xmlprocess files
    ###############################
    # data_process.get_category_reverse_index(save_dir=save_reverse_index_dir, stop_word_list=stop_word_list,only_english=True)

    # ############################### 
    # #  Get word_reverse_index from wiki files by multiprocessing
    # ###############################
    # data_file_list=data_process.get_multi_data_file_list()
    # print('total_title_num:',len(data_file_list))
    # data_file_list_now=[]
    # for file in data_file_list:
    #     if(not os.path.exists(os.path.join(save_reverse_index_dir,file.split('\\')[-2]+'_'+file.split('\\')[-1]+'_word_reverse_index.txt'))):
    #         data_file_list_now.append(file)
    # print('need to process file num:',len(data_file_list_now))
    #
    # pool = multiprocessing.Pool(processes=4)
    # for file in data_file_list_now:
    #     file=os.path.join(data_dir, file)
    #     pool.apply_async(data_process.get_word_reverse_index_from_one_file, (file,))
    # pool.close()
    # pool.join()

    # ###############################
    # #  Merge word_reverse_index
    # ###############################
    data_process.get_word_reverse_index()

    # ###############################
    # #  Calculate tf_idf in word_reverse_index
    # ###############################
    data_process.get_word_reverse_index_with_tfidf()