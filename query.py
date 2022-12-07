import numpy as np
from utils import SystemHelper
import math
import config
import Levenshtein
import time
import re
from utils import time_recorder
import jieba
'''
Some Notes: 

Compared to common search engine, wikipedia search should focus more on title mathcing, instead of document content.

Doucment similarity measuring: title overlap, category overlap, VSM score, pagerank score

Document abstract demonstration: The first sentence + infobox content.

Three types of search situations: 
1. Wildcard search: 
    - dropped terms = [] : no dropped terms
    - bold range = regular expression mathcing results will be bolden
2. Title search: strict matching
    - if matching successes, the result will always show in the first place
    - dropped terms = [] : no dropped terms
    - bold range = the title will be bolden
3. Comprehensive Search: 
    - dropped terms = removed stop words
    - bold range = the term matched
'''


class QueryHelper:
    def __init__(self, language: str, system_helper: SystemHelper):
        self.sys_helper = system_helper
        self.language = language
        assert self.language in ['en', 'zh'], '请输入正确语言选项'

    @time_recorder
    def search(self, query: str, topn=6):
        query = query.lower()
        # 首先判断是否进行通配符查询
        if ('*' in query) or ('?' in query):
            docs = self.wildcard_search(query, topn)
            return docs
        s = time.time()
        # 进行title查询
        tt_search_doc = self.title_search(query)
        if tt_search_doc is not None:
            self.add_bold_indexes([r'\b'+query+r'\b'], tt_search_doc)
        # 对query预处理
        query_terms, dropped_terms = self.preprocess_query(query)
        query_inverted_index = self.get_query_inverted_index(query_terms)
        # 进行综合查询
        doc_term_mat, doc_term_mat_norm, pagerank_score, phrase_score, map_indexes = \
            self.doc_filtering(query_terms, query_inverted_index)
        vsm_results = self.VSM_query(query_terms, doc_term_mat, doc_term_mat_norm, query_inverted_index)
        # 综合vsm和pagerank的查询结果, 并进行排序
        scores = vsm_results + 10000*pagerank_score + phrase_score
        e = time.time()
        print(e - s)
        if int(scores.shape[0]) < topn:
            topn = int(scores.shape[0])
        indexes = np.argpartition(scores, -topn)[-topn:]
        sorted_indexes = indexes[np.argsort(-scores[indexes])]
        real_doc_indexes = map_indexes[sorted_indexes]
        # indexes = np.argsort(-scores)
        # real_doc_indexes = map_indexes[indexes[:topn]]
        docs = []
        term_patterns = [(r'\b' + term + r'\b') for term in query_terms]
        for ind in real_doc_indexes:
            doc_id = self.sys_helper.doc_index2id_dic[ind]
            doc = self.sys_helper.find_doc(doc_id)
            doc['dropped_terms'] = dropped_terms
            self.add_bold_indexes(term_patterns, doc)
            docs.append(doc)
        e = time.time()
        print(e - s)
        # 融合title search的结果, 将title search结果加到第一位
        if tt_search_doc is not None:
            pop_index = -1
            for i, doc in enumerate(docs):
                if tt_search_doc['id'] == doc['id']:
                    pop_index = i
                    break
            docs.pop(pop_index)
            docs.insert(0, tt_search_doc)

        return docs

    def get_query_inverted_index(self, query_terms):
        query_inverted_index = dict()
        for term in query_terms:
            value = self.sys_helper.get_term_inverted_posting(term)
            query_inverted_index[term] = value
        return query_inverted_index

    def preprocess_query(self, query):
        """
        对query进行预处理, 分词+去停用词
        :param query:
        :return: 分词的list
        """
        if self.language == 'en':
            query_segs = query.split(' ')
        else:
            query_segs = jieba.cut(query, cut_all=False)
        query_terms = []
        dropped_terms = []
        for term in query_segs:
            # 满足条件: 非停用词 & 词典中存在, 两个条件才算是正常词项
            if (term not in self.sys_helper.stop_words) and \
                    (term in self.sys_helper.inverted_index_map.keys()):
                query_terms.append(term)
            else:
                dropped_terms.append(term)
        return query_terms, dropped_terms

    @time_recorder
    def doc_filtering(self, query_terms, inverted_index):
        """
        根据倒排记录表过滤文档
        1. 过滤文档, 只返回包含查询中词项的文档, 相当于or查询;
        2. 过滤词项维度, 只保留query中出现的词项.
        :param query_terms: 分词后的query term list
        :param inverted_index: 仅包含查询词项的倒排记录表
        :return:
        filtered_doc_term_mat：过滤后的此项文档矩阵
        filtered_pageran_vec：过滤后的pagerank向量
        phrase_score：文档中的短语出现情况，已转换为分值
        doc_indexes: 上述三个向量中的文档所对应的index,
        即doc_term_mat[i]对应的文档index是doc_indexes[i]
        """
        including_docs = set()
        term_indexes = []
        # 过滤倒排表, 只选取包含查询词项的文档, 合并倒排记录表
        # 同时实现短语检索
        two_grams = [[query_terms[i], query_terms[i+1]] for i in range(len(query_terms)-1)]
        postings = []  # 每一个查询词项对应倒排记录, 用于实现短语检索
        for term in query_terms:
            pst = inverted_index[term]
            postings.append(pst)
            for doc_id in inverted_index[term]['Attr']:
                including_docs.add(int(doc_id))
            term_indexes.append(int(inverted_index[term]['wi']))
        # 记录查询词项连续出现情况的向量
        phrase_score = np.zeros(len(including_docs), dtype=np.float32)
        for i, gram in enumerate(two_grams):
            pst1 = postings[i]
            pst2 = postings[i + 1]
            for doc_order, doc_id in enumerate(including_docs):
                if str(doc_id) in pst1['Attr'].keys() and str(doc_id) in pst2['Attr'].keys():
                    # 两个term同时出现在一篇文档中
                    # 再判断是否是连续的
                    locations1 = pst1['Attr'][str(doc_id)]['lc']
                    locations2 = pst2['Attr'][str(doc_id)]['lc']
                    for lc1 in locations1:
                        for lc2 in locations2:
                            if lc1 == lc2 - 1:
                                # 出现一次短语连续情况, 加一定分
                                phrase_score[doc_order] = phrase_score[doc_order] + 0.5
                            elif lc1 < lc2 - 1:
                                # 后边的lc2更不可能
                                break
                            elif lc1 >= lc2:
                                continue

        doc_indexes = []
        for doc_id in including_docs:
            index = self.sys_helper.doc_id2index_dic[doc_id]
            doc_indexes.append(index)
        filtered_doc_term_mat = self.sys_helper.doc_term_mat[doc_indexes][:, term_indexes]
        filtered_doc_term_mat = filtered_doc_term_mat.toarray()
        filtered_doc_term_mat_norm = self.sys_helper.doc_term_mat_norm[doc_indexes]
        filtered_pageran_vec = self.sys_helper.pagerank_vec[doc_indexes]
        return filtered_doc_term_mat, filtered_doc_term_mat_norm, filtered_pageran_vec, phrase_score, np.array(doc_indexes)

    @time_recorder
    def VSM_query(self, query_terms, doc_term_mat, doc_term_mat_norm, inverted_index):
        """
        根据VSM模型进行查询
        :param query_terms: 分词后的query term list
        :param doc_term_mat: 文档-词项矩阵
        :param doc_term_mat_norm: 文档-词项矩阵在axis上的范数向量
        :param inverted_index: 事先计算好的和query相关的倒排记录
        :return: list, 各元素是表示各个文档的字典, 已按照相关度从高到低排序
        """
        # 根据query中term的index, 手动计算tf-idf值, 构造query_vec
        # 对query分词
        query_term_frequency = dict()
        for term in query_terms:
            if term not in query_term_frequency.keys():
                query_term_frequency[term] = 1
            else:
                query_term_frequency[term] += 1
        query_vec = np.zeros(len(query_terms), dtype=np.float)
        for i, (term, value) in enumerate(query_term_frequency.items()):
            tf = math.log(value, 10) + 1
            idf = inverted_index[term]['idf']
            tf_idf = tf * idf
            # ind = self.sys_helper.inverted_index[term]['wi']
            query_vec[i] = tf_idf
            # msg = 'term: {0}, index: {1}, tf: {2}, idf: {3}, tfidf: {4}'
            # print(msg.format(term, term_index, tf, idf, tf_idf))

        # msg1 = 'doc 911, timeline: {0}, anarchism: {1}, norm: {2}'
        # msg2 = 'doc anarchism, timeline: {0}, anarchism: {1}, norm: {2}'
        # print(msg1.format(doc_term_mat[4][16], doc_term_mat[4][0], torch.norm(torch.from_numpy(doc_term_mat[4]))))
        # print(msg2.format(doc_term_mat[3][16], doc_term_mat[3][0], torch.norm(torch.from_numpy(doc_term_mat[3]))))
        # similarity = self.cosine_similarity(query_vec, doc_term_mat)
        similarity = np.dot(doc_term_mat, query_vec)
        norm = np.linalg.norm(query_vec) * doc_term_mat_norm
        similarity = similarity**2 / norm
        # print(1)
        # # 计算最相似的文档
        # if top_n > int(doc_term_mat.shape[0]):
        #     top_n = int(doc_term_mat.shape[0])
        # topn_results, topn_indexes = self.find_VSM_simiar_doc(query_vec, doc_term_mat, top_n)

        return similarity

    @time_recorder
    def complete_query(self, query: str, hint_num: int = 6) -> dict:
        """
        查询补全, 提示所有可能的文档.
        :param query: 待补全的query
        :param hint_num: 提示的文档数量
        :return: 提示的结果, 字典, 且已按照pagerank值降序排序 (按照此顺序显示)
            key为doc title,
            value为{'id'=文档id, 'pagerank'=pagerank值, 'redirect'=重定向信息}
        """

        def add_pagerank_field(field_dic: dict):
            # 添加pagerank字段
            doc_index = self.sys_helper.doc_id2index_dic[field_dic['id']]
            if field_dic['is_redirect']:
                # 重定向页
                if doc_index == -1:
                    # 目标页不在数据集中
                    field_dic['pagerank'] = -1.
                else:
                    # 目标页在数据集中, 使用目标页的pagerank值即可
                    field_dic['pagerank'] = float(self.sys_helper.pagerank_vec[doc_index])
            else:
                # 真实页面
                field_dic['pagerank'] = float(self.sys_helper.pagerank_vec[doc_index])

        # 查找所有包含前缀的页面
        # 完全匹配的显示为第一个, 其余的按pagerank排序
        prefix_serach_results = dict()
        query_len = len(query)
        for k, v in self.sys_helper.doc_tt2field_dic.items():
            if len(k) < query_len:
                continue
            if k[:query_len].lower() == query:
                # 添加page rank字段
                temp_v = v.copy()
                add_pagerank_field(temp_v)
                # 如果完全匹配, 则默认显示到第一个
                if len(k) == query_len:
                    temp_v['pagerank'] = float('inf')
                prefix_serach_results[k] = temp_v

        # 对prefix搜索结果按pagerank从高到低排序
        prefix_serach_results = sorted(prefix_serach_results.items(),
                                       key=lambda x: x[1]['pagerank'], reverse=True)
        # 转回字典形式
        prefix_serach_results = dict(prefix_serach_results)
        # print(prefix_serach_results)
        # print(len(prefix_serach_results))
        # print('----------')

        hint_results = prefix_serach_results.copy()
        if len(hint_results) >= hint_num:
            # 数量已满足, 直接返回前hint_num个结果
            cut_hint_results = dict()
            for i, (k, v) in enumerate(hint_results.items()):
                cut_hint_results[k] = v
                if i + 1 == hint_num:
                    break
            return cut_hint_results
        else:
            # 先进行编辑距离修正, 再查找匹配的界面 (去除长度的影响)
            min_dis = query_len
            lev_search_results = dict()
            for k, v in self.sys_helper.doc_tt2field_dic.items():
                if len(k) < query_len:
                    continue
                else:
                    if k in hint_results.keys():
                        continue
                    prefix = k[:query_len].lower()
                    dis = Levenshtein.distance(prefix, query)
                    if dis < min_dis:
                        min_dis = dis
                        lev_search_results = dict()
                        temp_v = v.copy()
                        add_pagerank_field(temp_v)
                        lev_search_results[k] = temp_v
                    elif dis == min_dis:
                        temp_v = v.copy()
                        add_pagerank_field(temp_v)
                        lev_search_results[k] = temp_v
            # 纠错结果不理想, 舍弃
            if min_dis >= int(0.8 * query_len):
                return hint_results
            # 对lev搜索结果排序
            lev_search_results = sorted(lev_search_results.items(),
                                        key=lambda x: x[1]['pagerank'], reverse=True)
            lev_search_results = dict(lev_search_results)
            # print(lev_search_results)
            # print(len(lev_search_results))

            # 合并两个搜索结果
            for i, (k, v) in enumerate(lev_search_results.items()):
                hint_results[k] = v
                if i + 1 == hint_num - len(prefix_serach_results):
                    break
            return hint_results

    def wildcard_search(self, query: str, top_n):
        """
        带通配符的搜索, 正则表达式匹配
        * ?两种情况, *匹配多个任意字符, ?匹配单个任意字符
        特殊情况: *和?都不能跨单词匹配
        :param query:
        :param top_n:
        :return:
        """
        # 中间不能带有空格和连字符
        pattern = query.replace('*', r'[^\-\s]*')
        pattern = pattern.replace('?', r'[^\-\s]')
        # 两边可以是连字符, 空格后者单词分界
        pattern = r'\b{0}\b|\b{1}\-|\-{2}\b|\-{3}\-'.format(pattern, pattern, pattern, pattern)
        # pattern = r'\b(.*-)?' + pattern + r'(-.*)?\b'
        reg = re.compile(pattern, flags=re.I)
        results = []
        for title, value in self.sys_helper.doc_tt2field_dic.items():
            # if reg.search(title) and ('Wikipedia:' not in title):
            if reg.search(title):
                v = value.copy()
                lev_dis = Levenshtein.distance(title.lower(), query)
                v['lev_dis'] = lev_dis
                results.append(v)
        # 排序
        results = sorted(results, key=lambda x: x['lev_dis'], reverse=False)
        docs = []
        for i, v in enumerate(results):
            doc = self.sys_helper.find_doc(v['id'])
            doc['dropped_terms'] = []
            self.add_bold_indexes([pattern], doc)
            docs.append(doc)
            if len(docs) == top_n:
                break
        return docs

    @time_recorder
    def title_search(self, query: str):
        doc_id = -1
        for t, v in self.sys_helper.doc_tt2field_dic.items():
            title = t.lower()
            if query == title:
                doc_id = v['id']
                break
        if doc_id == -1:
            return None
        else:
            doc = self.sys_helper.find_doc(doc_id)
            doc['dropped_terms'] = []
            return doc

    @time_recorder
    def recommend_sim_doc(self, doc_id: int, topn=5):
        """
        根据文档的category信息进行推荐. 将文档的category看作词项, 构造倒排表和词项文档矩阵, 根据tf-idf的思想计算其最相似的文档.
        :param doc_id:
        :param topn:
        :return:
        """
        helper = self.sys_helper
        doc_index = helper.doc_id2index_dic[doc_id]
        assert doc_index >= 0, '目标页不在当前数据集中'

        categories = helper.doc_id2field_dic[doc_id]['categories']
        cat_set = set()
        for cat in categories:
            if self.language == 'en':
                # 分词并去除大小写
                cat_terms = cat.lower().split(' ')
            else:
                # self.language == 'zh'
                cat_terms = jieba.cut(cat, cut_all=False)
            for t in cat_terms:
                if (t not in helper.kword_inverted_index_map.keys()) or (t in helper.stop_words):
                    continue
                cat_set.add(t)
        cat_indexes = []
        doc_including_cat = set()
        # s = time.time()
        for cat in cat_set:
            posting = helper.get_kword_inverted_posting(cat)
            # 当关键词较多时, 去掉非常普遍的词
            # if len(cat_set) > 2 and posting['idf'] < 2.:
            #     continue
            ind = posting['ci']
            cat_indexes.append(ind)
            docs = list(posting['Attr'].keys())
            for doc in docs:
                doc_ind = helper.doc_id2index_dic[int(doc)]
                # 去除当前文档本身
                if doc_ind == doc_index:
                    continue
                doc_including_cat.add(doc_ind)
        if not doc_including_cat:
            return []
        doc_including_cat = list(doc_including_cat)
        doc_including_cat = np.array(doc_including_cat)
        filterd_doc_cat_mat = helper.doc_kword_mat[doc_including_cat][:, cat_indexes]
        filterd_doc_cat_mat = filterd_doc_cat_mat.toarray()
        filterd_doc_norm = helper.doc_kword_mat_norm[doc_including_cat]
        doc_vec = helper.doc_kword_mat[doc_index][:, cat_indexes]
        doc_vec = doc_vec.toarray()
        # 计算cosine
        # doc_vec: (1, kword_num), filterd_doc_cat_mat: (doc_num, kword_num)
        # filterd_doc_norm: (doc_num, )
        norm = np.linalg.norm(doc_vec) * filterd_doc_norm
        inner_dot = np.sum(doc_vec*filterd_doc_cat_mat, axis=1)
        cos = inner_dot / norm
        # e = time.time()
        # print(e-s)
        # 从高到低排序
        # argpartion, 仅仅作区分, 并不全部排序
        sorted_inds = np.argpartition(cos, -topn)[-topn:]  # 得到topn的坐标值 (未排序)
        # 将topn坐标值排序
        sorted_doc_inds = doc_including_cat[sorted_inds[np.argsort(-cos[sorted_inds])]]

        # sorted_inds = np.argsort(-cos)[:topn]
        # sorted_doc_inds = doc_including_cat[sorted_inds]
        sorted_docs = []
        for ind in sorted_doc_inds:
            d_id = helper.doc_index2id_dic[ind]
            d = helper.find_doc(d_id)
            sorted_docs.append(d)
        # e = time.time()
        # print(e-s)
        return sorted_docs

    @staticmethod
    def add_bold_indexes(patterns_to_bold: list, doc: dict):
        """
        根据结果确定需要加粗的字符串范围
        :return:
        """
        regs = [re.compile(pattern=p, flags=re.I) for p in patterns_to_bold]

        range_list = []
        text = doc['text']
        # 搜索各个正则表达式
        for reg in regs:
            match_iter = reg.finditer(text)
            for match in match_iter:
                match_range = (match.start(), match.end())
                range_list.append(match_range)

        doc['bold range'] = range_list


if __name__ == '__main__':
    # zh_helper = SystemHelper(config.zh_inverted_index_dir,
    #                          config.zh_doc_text_dir, config.zh_doc_field_dir,
    #                          config.zh_stop_words_path, config.zh_cache_dir)
    # zh_query = QueryHelper('zh', zh_helper)
    # r1 = zh_query.search('腾讯公司')
    # r2 = zh_query.complete_query('数')
    # r3 = zh_query.recommend_sim_doc(18)
    # r4 = zh_query.search('哲学')
    # print(1)

    en_helper = SystemHelper(config.en_inverted_index_dir,
                              config.en_doc_text_dir, config.en_doc_field_dir,
                              config.en_stop_words_path, config.en_cache_dir)
    en_query = QueryHelper('en', en_helper)
    sim_docs = en_query.recommend_sim_doc(400508)
    hint_res = en_query.complete_query('google')
    
    r1 = en_query.search('the timeline of anarchism', 6)
    # r2 = en_query.search('Triumph of the Will', 6)
    # r3 = en_query.search('an*chism', 6)
    # r4 = en_query.search('g*gle', 6)
    print(1)
