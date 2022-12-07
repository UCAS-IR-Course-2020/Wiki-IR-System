import os

class Article():
    def __init__(self,data_dir,xml_result_dir):
        self.data_dir=data_dir
        self.xml_result_dir=xml_result_dir
        with open(os.path.join(xml_result_dir,'file_id_map_dict.txt'),'r',encoding='utf-8') as f:
            self.file_id_map_xml_result=eval(f.readline())
        with open(os.path.join(data_dir,'file_id_map_dict.txt'),'r',encoding='utf-8') as f:
            self.file_id_map_data=eval(f.readline())


    ## If this is not in the data_dir, it will be find in xml result
    ## The differen is :
    ## data_dir include: [id,url,title,text]
    ## xml result include:[title,id,redirect,page_link,abstract_end]
    def find_article_by_id(self,id):
        if(id!=None):
            for key,value in self.file_id_map_data.items():
                if(int(value[0])<=int(id)<=int(value[1])):
                    with open(os.path.join(data_dir,key),'r',encoding='utf-8') as f:
                        for data in f.readlines():
                            now_dict=eval(data)
                            if(id==now_dict['id']):
                                return now_dict
                    break
            for key, value in self.file_id_map_xml_result.items():

                now_file=str(key)+'_xml_process.txt'
                if(int(value[0])<=int(id)<=int(value[1])):
                    with open(os.path.join(xml_result_dir,now_file),'r',encoding='utf-8') as f:
                        for data in f.readlines():
                            now_dict=eval(data)
                            if(id==now_dict['id']):
                                return now_dict
                    break
            return None
        else:
            return None

    ## Given title,return id 
    def title2id(self,word):
        if(word[0].encode('utf-8').isalpha()):
            file=os.path.join(self.xml_result_dir,'word_id_map',word[0].upper()+'.txt')
        else:
            file = os.path.join(self.xml_result_dir, 'word_id_map','other'+'.txt')
        with open(file,'r',encoding='utf-8') as f:
            for data in f.readlines():
                [now_word,now_id]=data.strip().split('\t')
                if(now_word==word):
                    return now_id
        return None

    def find_article_by_title(self,title):
        id=self.title2id(title)
        return self.find_article_by_id(id)

    def find_page_link_id_list_by_id(self, id):
        if(id!=None):
            for key, value in self.file_id_map_xml_result.items():
                now_file = str(key) + '_id_pl.txt'
                if (int(value[0]) <= int(id) <= int(value[1])):
                    with open(os.path.join(xml_result_dir, now_file), 'r', encoding='utf-8') as f:
                        now_dict=eval(f.readline())
                        return now_dict.get(id,None)
        else:
            return None

    def find_page_link_id_list_by_title(self, title):
        id=self.title2id(title)
        return self.find_page_link_id_list_by_id(id)


if __name__=='__main__':

    data_dir='xml_process/enwiki/wikiextractor-master/text/'
    xml_result_dir = 'xml_process/enwiki/xml_result'

    # article
    article=Article(data_dir,xml_result_dir)
    print(article.find_article_by_id('10'))
    print(article.find_article_by_id('1780699'))
    print(article.find_article_by_id('12'))
    id=article.title2id('Anarchism')
    print(article.find_article_by_id(id))
    print(article.find_article_by_title('Anarchism'))

    print(article.find_page_link_id_list_by_id('1780699'))
    print(article.find_page_link_id_list_by_id('11'))
    print(article.find_page_link_id_list_by_id('12'))

    print(article.find_page_link_id_list_by_title('Anarchism'))