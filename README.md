# Wiki-IR-System
本项目是中国科学院大学网络空间安全学院2020春季学期《信息检索导论》的课程大作业, 实现了针对中英文维基百科的检索系统.

## 参与人员及分工
- [Ren Li](https://github.com/renli1024): 检索模块
- [jisongyang](https://github.com/jisongyang): 数据处理模块
- [Alice828](https://github.com/Alice828): 界面展示模块

## 介绍
针对中、英文维基百科的检索系统, 数据使用官方wiki dump, 不借助任何索引构建和检索工具, 实现了倒排表构建、VSM检索、PageRank链接分析、标题检索、短语检索、通配符检索、查询补全、相关文档推荐等功能, 并进行了若干检索速度和内存占用的优化. 

目前在35w文档数 (5个wiki dump multistream文件), 1.3亿链接数的情况下, 在普通8G内存计算机上, 平均top 10检索时长为1s左右.

![英文检索](example_images/英文检索.png)

![中文检索](example_images/中文检索.png)

![查询补全](example_images/查询补全.png)

![检索流程](example_images/检索流程.png)

## 相关优化
1. 使用倒排表对文档进行预筛选 (相当于布尔检索的 or 查询), 提前剔除掉无关文档; 
2. 在VSM模型中计算向量相似度时, 仅仅计算查询中所出现词项的相似度；
3. 倒排表存储在文件中，通过维护一个倒排记录和相应文件位置的映射表，使得读取文件的时间复杂度从O(n)降低为了O(1)，且无需占用内存空间；
4. 底层矩阵存储优化为稀疏矩阵, 可显著节省内存空间和计算时间。词项文档矩阵空间复杂度从O(mn)降为O(t), m为文档数, n为词项数目, t为词汇总数, 通常mn要远大于t; 链接重要性矩阵的空间复杂度从O(m^2)降低为O(e), e为链接数, 通常远小于m^2。
5. 文档相关度排序操作使用partition-sort, 相比快排, 选取前topk结果的时间复杂度由O(nlogn)降低为O(klogk), n为文档总数, k为设定的前top k数量.

## 代码结构
- query.py: 核心检索功能的实现文件
- utils.py: 系统辅助类的实现文件
- config.py: 配置文件
- web/: web服务器配置文件
- data_preprocess/: 数据预处理文件, 解析原始wiki dump文件 (解析数据借助了开源工具[wikiextractor](https://github.com/attardi/wikiextractor)).

### 程序运行
1. 首先在wiki官网下载wiki dump multistream文件, 使用`data_preprocess/`解析文件, 产生解析后的文档和倒排记录表.
2. 调用检索utils.SystemHelper和query.QueryHelper类, 完成检索操作, 主要函数:
    - QueryHelper.search(): 检索函数;
    - QueryHelper.complete_query(): 查询补全函数;
    - QueryHelper.recommend_sim_doc(): 推荐相似文档.
3. 使用`web/`完成界面展示.
    1. 下载nodejs, 创建项目, 替换项目中的src文件为该web文件；
    2. 使用"npm start"命令启动前端页面；
    3. 运行server.py启动python服务。
- 注: 界面展示模块并非必须, 也可直接通过query.py文件以终端的形式搜索.

- `data_preprocess/`解析文件步骤
```shell
# step1
 cd  data_preprocess/xml_process/wikiextractor-master
 (1)  .bz2 file here
 (2)  unzip .bz2 file here
 "python .\WikiExtractor.py --json -b 10M .\enwiki-20200420-pages-articles-multistream8.xml-p1268692p1791079.bz2"

# step2
 cd  data_preprocess/xml_process
 (1) choose unzip .bz2 file path in .py file
 "python xml_process.py"
 "python xml_process_zh.py"
 
# step3
 cd data_preprocess
 (1) choose  wikiextractor output file path in .py file
 "python data_process.py"
 "python data_process_zh.py"
```

