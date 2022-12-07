import numpy as np
from os.path import join
from os.path import exists
import pickle
import config
import time
import torch
import scipy.sparse as sp
import re
from functools import wraps
import os

"""
The document title remains case-sensitive: some document titles are only different in case (usually redirect pages), so if the case is ignored, the document cannot be located by title.

The document category ignore case: the category will be tokenized to count tf-idf value, so the case should be unified.

doc_tt2field_dic: map from title to field, doc_id2field_dic: map from id to field.
doc_id2index_dic: map from id to index. 
doc_index2id_dic: mao from index to id. 
field: document attributes, like id, title, is_redirect 是否是重定向页, is_updated (only for redirect pages, whether update the index)

Three types of document: 
1. Real document:
    doc_tt2field_dic/doc_id2field_dic: 
        ['redirect']=''
        ['is_redirect']=False
    doc_id2index_dic: normal index
2. Redirect document & the page redirected to is in the dataset:
    doc_tt2field_dic/doc_id2field_dic: 
        ['redirect']=title of the page redirected to
        ['is_redirect']=True
    doc_id2index_dic: index of the page redirected to   
3. Redirect document & the page redirected to is NOT in the dataset:
    doc_tt2field_dic/doc_id2field_dic: 
        ['redirect']=title of the page redirected to
        ['is_redirect']=True
    doc_id2index_dic: -1
"""


def time_recorder(func):
    @wraps(func)
    def wrap_func(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print("func {0}() time usage: {1:.2f}".format(func.__name__, end-start))
        return result
    return wrap_func


class SystemHelper:
    @time_recorder
    def __init__(self, inverted_index_dir, doc_text_dir, doc_field_dir, stop_words_path, cache_dir):
        s = time.time()
        self.inverted_index_dir = inverted_index_dir
        self.doc_text_dir = doc_text_dir
        self.doc_field_dir = doc_field_dir
        self.stop_words_path = stop_words_path
        self.cache_dir = cache_dir
        if not exists(cache_dir):
            os.makedirs(self.cache_dir)

        # 综合的倒排记录表, 包含位置信息, tf-idf值等
        inverted_index_path = join(self.inverted_index_dir,
                                   'word_reverse_index.txt')
        self.inverted_index_file = open(inverted_index_path, 'r', encoding='utf-8')
        self.inverted_index_map = self.get_inverted_index_map(self.inverted_index_file)

        # category 倒排记录表
        cat_inverted_index_path = join(self.inverted_index_dir,
                                        'category_reverse_index.txt')
        self.kword_inverted_index_file = open(cat_inverted_index_path, 'r', encoding='utf-8')
        self.kword_inverted_index_map = self.get_inverted_index_map(self.kword_inverted_index_file)

        e = time.time()
        print('加载数据时间: {:.2f}'.format(e-s))

        # doc text解析文件
        doc_text_file_map = join(self.doc_text_dir, 'file_id_map_dict.txt')
        for line in open(doc_text_file_map, 'r', encoding='utf-8'):
            line = line.strip()
            doc_text_file_map = eval(line)
            # 存储各个文件中的边界id
            self.text_file_id_map = doc_text_file_map

        # doc field解析文件, 包括: title, id, redirect, outlink (不包括text)
        doc_field_map = join(self.doc_field_dir, 'file_id_map_dict.txt')
        for line in open(doc_field_map, 'r', encoding='utf-8'):
            line = line.strip()
            dic = eval(line)
            self.doc_field_file_num = len(dic)

        # 文档属性相关的转换字典
        id2index_path = join(self.cache_dir, 'doc_id2index_dic')
        index2id_path = join(self.cache_dir, 'doc_index2id_dic')
        tt2field_path = join(self.cache_dir, 'doc_tt2field_dic')
        id2field_path = join(self.cache_dir, 'doc_id2field_dic')
        if exists(id2index_path) and exists(index2id_path) \
                and exists(tt2field_path) and exists(id2field_path):
            self.doc_id2index_dic = pickle.load(open(id2index_path, 'rb'))
            self.doc_index2id_dic = pickle.load(open(index2id_path, 'rb'))
            self.doc_tt2field_dic = pickle.load(open(tt2field_path, 'rb'))
            self.doc_id2field_dic = pickle.load(open(id2field_path, 'rb'))
        else:
            self.doc_id2index_dic, self.doc_index2id_dic, \
                self.doc_tt2field_dic, self.doc_id2field_dic = self.construct_doc_dic()
            pickle.dump(self.doc_id2index_dic, open(id2index_path, 'wb'))
            pickle.dump(self.doc_index2id_dic, open(index2id_path, 'wb'))
            pickle.dump(self.doc_tt2field_dic, open(tt2field_path, 'wb'))
            pickle.dump(self.doc_id2field_dic, open(id2field_path, 'wb'))

        self.real_doc_num = len(self.doc_index2id_dic)
        self.term_num = len(self.inverted_index_map)

        # 文档-词项矩阵相关文件
        dtm_path = join(self.cache_dir, 'doc_term_mat')
        dtmn_path = join(self.cache_dir, 'doc_term_mat_norm')
        dkm_path = join(self.cache_dir, 'doc_kword_mat')
        dkmn_path = join(self.cache_dir, 'doc_kword_mat_norm')
        if exists(dtm_path) and exists(dtmn_path) and exists(dkm_path) and exists(dkmn_path):
            self.doc_term_mat = pickle.load(open(dtm_path, 'rb'))
            self.doc_term_mat_norm = pickle.load(open(dtmn_path, 'rb'))
            self.doc_kword_mat = pickle.load(open(dkm_path, 'rb'))
            self.doc_kword_mat_norm = pickle.load(open(dkmn_path, 'rb'))
        else:
            self.doc_term_mat = self.compute_doc_term_mat()
            pickle.dump(self.doc_term_mat, open(dtm_path, 'wb'))
            self.doc_term_mat_norm = self.compute_doc_mat_norm(self.doc_term_mat)
            pickle.dump(self.doc_term_mat_norm, open(dtmn_path, 'wb'))
            self.doc_kword_mat = self.compute_doc_kword_mat()
            pickle.dump(self.doc_kword_mat, open(dkm_path, 'wb'))
            self.doc_kword_mat_norm = self.compute_doc_mat_norm(self.doc_kword_mat)
            pickle.dump(self.doc_kword_mat_norm, open(dkmn_path, 'wb'))

        # 链接矩阵和pagerank值
        # 使用稀疏格式保存链接矩阵, pickle有可能会超内存
        ilm_path = join(self.cache_dir, 'inlink_mat.npz')
        pgv_path = join(self.cache_dir, 'pagerank_vec')
        # inlink_mat = sp.load_npz(ilm_path)
        # print('link num: ', inlink_mat.count_nonzero())
        # print('doc num: ', len(self.doc_id2index_dic.keys()))
        # self.pagerank_vec = self.compute_pagerank(inlink_mat)
        # pickle.dump(self.pagerank_vec, open(pgv_path, 'wb'))
        # print(1)
        if exists(ilm_path) and exists(pgv_path):
            # 仅读取计算好的pagerank结果即可, 无需读取链接矩阵
            self.pagerank_vec = pickle.load(open(pgv_path, 'rb'))
        else:
            inlink_mat = self.get_inlink_mat()
            sp.save_npz(ilm_path, inlink_mat)
            # s = np.sum(inlink_mat, axis=0)
            # print('--', s)
            self.pagerank_vec = self.compute_pagerank(inlink_mat)
            pickle.dump(self.pagerank_vec, open(pgv_path, 'wb'))

        # 读取停用词表
        self.stop_words = self.get_stop_words()

    @staticmethod
    def get_inverted_index_map(file):
        """
        构建词项-倒排表文件相应位置的映射表/字典, 取倒排表信息时临时去文件中读取
        :return:
        """
        inverted_index_map = {}
        offset = file.tell()
        line = file.readline()
        i = 0
        while line:
            line = line.strip()
            key, _ = line.split('\t')
            inverted_index_map[key] = offset
            offset = file.tell()
            line = file.readline()
            i += 1
        # 重置读写头的位置
        file.seek(0)
        return inverted_index_map

    def get_term_inverted_posting(self, term: str):
        """
        获取词项倒排表的posting
        :param term:
        :return:
        """
        offset = self.inverted_index_map[term]
        f = self.inverted_index_file
        f.seek(offset)
        line = f.readline()
        line = line.strip()
        key, value = line.split('\t')
        posting_dic = eval(value)
        return posting_dic

    def get_kword_inverted_posting(self, cat: str):
        """
        获取category的posting
        :param cat:
        :return:
        """
        offset = self.kword_inverted_index_map[cat]
        f = self.kword_inverted_index_file
        f.seek(offset)
        line = f.readline()
        line = line.strip()
        key, value = line.split('\t')
        posting_dic = eval(value)
        return posting_dic

    @time_recorder
    def compute_doc_mat_norm(self, doc_mat):
        """
        提前计算出文档向量的范数, 便于后期算cosine
        :return:
        """
        doc_norms = []
        for i in range(self.real_doc_num):
            doc_cat_vec = doc_mat[i].toarray()
            d_norm = np.linalg.norm(doc_cat_vec)
            doc_norms.append(d_norm)
        doc_norms = np.array(doc_norms)
        return doc_norms

    @time_recorder
    def compute_doc_term_mat(self):
        """
        构建文档词项矩阵
        :return:
        """
        # 以稀疏矩阵的格式构造
        term_doc_mat = sp.lil_matrix((self.term_num, self.real_doc_num), dtype=np.float)
        for term, offset in self.inverted_index_map.items():
            value = self.get_term_inverted_posting(term)
            term_index = int(value['wi'])
            for k, v in value['Attr'].items():
                doc_id = int(k)
                doc_index = self.doc_id2index_dic[doc_id]
                assert doc_index >= 0
                tf_idf = v['tfidf'][1]
                term_doc_mat[term_index, doc_index] = tf_idf
        doc_term_mat = term_doc_mat.transpose()
        return doc_term_mat

    @time_recorder
    def compute_doc_kword_mat(self):
        total_kword_num = len(self.kword_inverted_index_map)
        # 以稀疏矩阵的格式构造
        cat_doc_mat = sp.lil_matrix((total_kword_num, self.real_doc_num), dtype=np.float)
        for category in self.kword_inverted_index_map.keys():
            posting = self.get_kword_inverted_posting(category)
            cat_index = int(posting['ci'])
            for k, v in posting['Attr'].items():
                doc_id = int(k)
                doc_index = self.doc_id2index_dic[doc_id]
                assert doc_index >= 0
                tf_idf = v['tfidf'][1]
                cat_doc_mat[cat_index, doc_index] = tf_idf
        doc_cat_mat = cat_doc_mat.transpose()
        return doc_cat_mat

    @time_recorder
    def construct_doc_dic(self):
        """
        构建和文档相关的辅助字典:
        id2index_dic: doc id -> doc index, index是doc在各种矩阵中的位置
        index2id_dic: doc index -> doc id
        tt2field_dic: doc title -> doc field, field 为doc的各种信息, 主要是重定向信息
        id2field_dic: doc id -> doc field
        :return:
        """
        index = 0
        id2index_dic = dict()
        # key为title, value为{'id': xx, 'redirect': ''}
        tt2field_dic = dict()
        id2field_dic = dict()
        # 存储所有重定向页的doc id
        redirect_docs = []
        for i in range(self.doc_field_file_num):
            file_path = join(self.doc_field_dir, "{}_xml_process.txt".format(i))
            file = open(file_path, 'r', encoding='utf-8')
            for line in file:
                line = line.strip()
                doc = eval(line)
                doc_id = int(doc['id'])
                # 文档标题不能去除大小写, 因为有些文档标题只有大小写的区别
                doc_title = doc['title']
                doc_redirect_to = doc['r_d']
                categories = doc['ct']
                # categories = ' '.join(categories).lower()  # 将目录拼成一个大字符串
                tt2field_dic[doc_title] = {'id': doc_id,
                                           'redirect': doc_redirect_to,
                                           'categories': categories}
                id2field_dic[doc_id] = {'title': doc_title,
                                        'redirect': doc_redirect_to,
                                        'categories': categories}
                if doc_redirect_to == '':
                    # 正常页面
                    id2index_dic[doc_id] = index
                    id2field_dic[doc_id]['is_redirect'] = False
                    tt2field_dic[doc_title]['is_redirect'] = False
                    index += 1
                else:
                    # 重定向页
                    id2index_dic[doc_id] = '重定向页'
                    # is_redirect: 是否是重定向页
                    # is_updated: 该重定向页的属性(index)是否被更新
                    id2field_dic[doc_id]['is_redirect'] = True
                    id2field_dic[doc_id]['is_updated'] = False
                    tt2field_dic[doc_title]['is_redirect'] = True
                    tt2field_dic[doc_title]['is_updated'] = False
                    redirect_docs.append(doc_id)
            file.close()

        # 翻转dict
        # 去除所有redirect的doc
        index2id_dic = dict()
        for doc_id, doc_index in id2index_dic.items():
            if id2field_dic[doc_id]['is_redirect']:
                continue
            index2id_dic[doc_index] = doc_id

        # 处理重定向页
        # 更新id2index_dic, 将重定向页面的index更新为其所对应文档的的index
        # 如果重定向页的目标页不在数据集中, 则其index为-1
        # 更新id2field_dic/tt2field_dic, 将重定向页面的'redirect'字段更新为其所对应文档的id
        # 因为存在多跳重定向页的情况, 因此一次只能更新一轮
        remain_redirect_docs = []
        while redirect_docs:
            for doc_id in redirect_docs:
                field = id2field_dic[doc_id]
                title = field['title']
                redirect_title = field['redirect']
                # 判断目标页是否在数据集中
                if redirect_title not in tt2field_dic.keys():
                    tt2field_dic[title]['is_updated'] = True
                    id2field_dic[doc_id]['is_updated'] = True
                    id2index_dic[doc_id] = -1
                    continue
                # 判断是单跳重定向还是多跳重定向(重定向页还是重定向页)
                if tt2field_dic[redirect_title]['is_redirect']:
                    # 多跳重定向页
                    if not tt2field_dic[redirect_title]['is_updated']:
                        remain_redirect_docs.append(doc_id)
                        continue
                # 单跳重定向页 或是 目标页已更新的多跳重定向页
                tt2field_dic[title]['is_updated'] = True
                id2field_dic[doc_id]['is_updated'] = True
                redirect_id = tt2field_dic[redirect_title]['id']
                redirect_index = id2index_dic[redirect_id]
                id2index_dic[doc_id] = redirect_index
            redirect_docs = remain_redirect_docs
            remain_redirect_docs = []
        return id2index_dic, index2id_dic, tt2field_dic, id2field_dic

    @time_recorder
    def get_inlink_mat(self, suffer_num: int = 1000):
        """
        根据出链信息构建入链矩阵
        :return:
        """
        outlink_id_dic = dict()  # 出链信息词典, key: outlink doc id, value: 所有的inlink doc id
        for i in range(self.doc_field_file_num):
            file_path = join(self.doc_field_dir, "{}_id_pl.txt".format(i))
            file = open(file_path, 'r', encoding='utf-8')
            for line in file:
                line = line.strip()
                line_dic = eval(line)
                outlink_id_dic.update(line_dic)
            file.close()

        outlink_mat = sp.lil_matrix((self.real_doc_num, self.real_doc_num), dtype=np.float)
        # outlink_mat = np.zeros((self.real_doc_num, self.real_doc_num), dtype=np.float)
        for k, v in outlink_id_dic.items():
            # key: 'id', value: ['id1', 'id2', ...]
            doc_id = int(k)
            if self.doc_id2field_dic[doc_id]['is_redirect']:
                # 重定向页
                # 不能按照inlink_dic中的v是否为[]来判断, 因为还有可能是无外链的情况
                continue
            doc_index = self.doc_id2index_dic[doc_id]
            indoc_indexes = set()
            for indoc_id in v:
                indoc_id = int(indoc_id)
                ind = self.doc_id2index_dic[indoc_id]
                if ind < 0:
                    # 重定向页, 且目标页不在数据集中
                    continue
                indoc_indexes.add(ind)
                # # 链接的页面也可能是重定向页, 因此还需要判断
                # if ind >= 0:
                #     indoc_indexes.append(ind)
                # else:
                #     # 重定向页, 且目标页不再
                #     continue
                # elif ind == -float('inf'):
                #     continue
                # else:
                #     indoc_indexes.append(-ind)
            indoc_indexes = list(indoc_indexes)
            inlink_num = len(indoc_indexes)
            if inlink_num == 0:
                # 对没有出链的节点, 设置其出链为对所有节点
                # outlinks_to_all = np.full(self.real_doc_num, 1 / self.real_doc_num)
                indoc_indexes = np.random.randint(0, self.real_doc_num, suffer_num)
                outlink_mat[doc_index, indoc_indexes] = 1 / suffer_num
            else:
                outlink_mat[doc_index, indoc_indexes] = 1 / inlink_num
        inlink_mat = outlink_mat.transpose()
        inlink_mat = inlink_mat.tocsr()
        return inlink_mat

    @time_recorder
    def compute_pagerank(self, inlink_mat, iter_num: int = 100, suffer_term=0.85, eps=1e-4):
        """
        迭代法计算page rank值.
        有两种特殊情况需要关注:
        1. 某些节点只有入链没有出链, 会使得总page rank值流失.
        解决: 对没有出链的节点, 设置其出链为所有节点
        2. rank sink情况, 一部分节点形成循环, 且没有向外的出度, 但有指向其的入度.
        会导致循环的节点值增加, 其他节点的rank值变为0.
        解决: 加入随机suffer系数d来缓解.
        :param inlink_mat: 入链矩阵
        :param iter_num: 最大迭代轮数
        :param suffer_term: suffer系数
        :param eps: 终止误差
        :return:
        """
        node_num = inlink_mat.shape[0]
        # 迭代计算page rank
        r = np.random.rand(node_num)
        # 除以1范数
        r = r / np.linalg.norm(r, ord=1)
        is_convergence = False
        for i in range(iter_num):
            # 加入随机sufer的概率, 使pagerank值不那么极端
            r_t = inlink_mat.dot(r)*suffer_term + (1-suffer_term)/node_num * r
            # r_t = suffer_term*inlink_mat.dot(r)
            # r_t = suffer_term*r_t + (1-suffer_term)/node_num * r
            delta = r_t - r
            if np.linalg.norm(delta, ord=1) < eps:
                is_convergence = True
                break
            r = r_t
        print('是否收敛: {}'.format(is_convergence))
        return r

    def find_doc(self, doc_id: int):
        """
        根据doc id查询文档
        :param doc_id: doc id
        :return: 查询到的文档, 字典形式
            {'title'=文档标题, 'redirect_from'=从哪个页面重定向而来,
            'page_exist'=重定向的目标页面是否存在, 'url'=文档url, 'id'=文档id,
            'text': 文档正文内容}
        redirect_from和page_exist有三种情况:
            正常页面: redirect_from='', page_exist=True
            重定向页, 且重定向目标存在: redirect_from=原先文档标题, page_exist=True
            重定向页, 但重定向目标不存在: redirect_from=原先文档标题, page_exist=False
        """
        assert doc_id in self.doc_id2index_dic.keys(), 'dod id不存在'
        doc_dic = dict()
        if self.doc_id2field_dic[doc_id]['is_redirect']:
            # 重定向页
            redirect_index = self.doc_id2index_dic[doc_id]
            origin_title = self.doc_id2field_dic[doc_id]['title']
            doc_dic['redirect_from'] = origin_title
            if redirect_index == -1:
                # 目标页不在数据集内
                doc_dic['page_exist'] = False
                doc_dic.update(dict(id='', url='', title='', text=''))
                return doc_dic
            else:
                # 目标页在数据集内
                doc_dic['page_exist'] = True
                redirect_id = self.doc_index2id_dic[redirect_index]
                doc_id = redirect_id
        else:
            # 真实页面
            origin_title = self.doc_id2field_dic[doc_id]['title']
            doc_dic['redirect_from'] = ''
            doc_dic['page_exist'] = True

        file_path = 'null'
        for k, v in self.text_file_id_map.items():
            left_bound = int(v[0])
            right_bound = int(v[1])
            if left_bound <= doc_id <= right_bound:
                file_path = k.split('\\')
                file_path = join(self.doc_text_dir, file_path[0], file_path[1])
                break

        is_found = False
        f = open(file_path, 'r', encoding='utf-8')
        for line in f:
            line = line.strip()
            d = eval(line)
            if int(d['id']) == doc_id:
                doc_dic.update(d)
                title_match = re.search(r'\b.*\n\n', doc_dic['text'])
                doc_dic['text'] = doc_dic['text'][title_match.end():]
                is_found = True
                break
        f.close()
        if (not is_found) and (doc_id in self.doc_id2field_dic.keys()):
            doc_dic['url'] = 'https://zh.wikipedia.org/wiki?curid='.format(doc_id)
            doc_dic['title'] = self.doc_id2field_dic[doc_id]['title']
            doc_dic['text'] = ''
            doc_dic['id'] = str(doc_id)
            is_found = True
        assert is_found, '未找到doc text记录, id: {0}, title: {1}'.format(doc_id, origin_title)
        return doc_dic

    def get_stop_words(self) -> list:
        stop_word_list = []
        f = open(self.stop_words_path, 'r', encoding='utf-8')
        for line in f:
            line = line.strip()
            stop_word_list.append(line)
        f.close()
        return stop_word_list


def modify_inverted_index(path, new_path):
    file = open(path, 'r', encoding='utf-8')
    new_file = open(new_path, 'w', encoding='utf-8')
    term_set = set()
    offset = 0
    for i, line in enumerate(file):
        if i % 1000 == 0:
            print(i, flush=True)
        line = line.strip()
        key, value = line.split('\t')
        value = eval(value)
        if key in term_set:
            offset -= 1
            continue
        term_set.add(key)
        value['wi'] = int(value['wi']) + offset
        new_line = key + '\t' + str(value) + '\n'
        new_file.write(new_line)
    file.close()
    new_file.close()


if __name__ == '__main__':
    pass

    # sys_helper = SystemHelper(config.en_inverted_index_dir,
    #                           config.en_doc_text_dir, config.en_doc_field_dir,
    #                           config.en_stop_words_path, config.en_cache_dir)
    #
    # print(sys_helper.doc_id2index_dic[253639])

