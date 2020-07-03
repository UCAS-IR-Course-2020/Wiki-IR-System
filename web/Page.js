import React,{Component} from 'react';
import ReactDOM from 'react-dom';
import './Page.css';
import search from './search.svg';
import Wikipediaword from './Wikipedia-word.png';
import Wikiresultlogo from './WikiResultlogo.png';
import Wikiresultlogo_zh from './WikiResultlogo_zh.png';
import searchlogo from './searchlogo.png';
import searching from './20200703023012.gif';
import axios from 'axios' ;
var j=0;
var data=[];
var recommendData=[];
let dataLength=0;
var pageAll;
function getData(queryTxt,language){
    let url="http://127.0.0.1:8000/search_"+language+"?query="+queryTxt;
    axios.get(url).then(function (response) {
    data =response.data;
   }).then( ()=>{
   document.getElementById('searching').style.display="none";
   if(data.length!=0){
    dataLength=data.length;
    pageAll=parseInt(dataLength/10)+1;
    deleteData(0);
    showData(0,queryTxt,language);
    pageKey(0,language);
   }
 }
   )

}
function getRecommendList(docID,x,language){
 let url="http://127.0.0.1:8000/recommend_"+language+"?docID="+docID;
  axios.get(url).then(function (response) {
    recommendData =response.data;
   }).then( ()=>{
    if(recommendData.length>0){
    for (var i = 0; i< recommendData.length; i++) {
      document.getElementById('recommendList'+x).innerHTML=document.getElementById('recommendList'+x).innerHTML+" || "+'<a target=\'blank\' href=\''+recommendData[i].url+'\'>'+recommendData[i].title+'</a>';
    }
     }else {
          document.getElementById('recommendList'+x).innerText="no related entries";

        }
   }

   )

}
function showData(a,queryTxt,language){

  var reg =new RegExp(queryTxt,"ig");


  data.filter((value,index) => { 

    if (queryTxt.indexOf("*") != -1) {
       
           var queryTxtAll=queryTxt.replace("*",".*?");
           //var regAll=new RegExp('\\'+queryTxtAll[0]+'.*?\\'+queryTxtAll[queryTxtAll.length-1],"ig");
           var regAll=new RegExp(queryTxtAll,"ig");
           value.text=value.text.replace(regAll, `<span class="keyword">$&</span>`); 
           value.title=value.title.replace(regAll, `<span class="keyword">$&</span>`);
               
    }
      else if (queryTxt.indexOf("?") != -1) {
        var queryTxtSome=queryTxt.replace("?",".?");
        var regSome=new RegExp(queryTxtSome,"ig");
        value.text=value.text.replace(regSome, `<span class="keyword">$&</span>`); 
        value.title=value.title.replace(regSome, `<span class="keyword">$&</span>`);
      }
        
     else if (queryTxt.indexOf(" ") != -1) {
                   
          var queryTxtSplit=queryTxt.split(" ");
          for (var i = 0; i < queryTxtSplit.length; i++) {
          var re_i=new RegExp(queryTxtSplit[i],"ig");
          value.text=value.text.replace(re_i, `<span class="keyword">$&</span>`);
          value.title=value.title.replace(reg, `<span class="keyword">$&</span>`);

    } 
  }
    else {

         value.text=value.text.replace(reg, `<span class="keyword">$&</span>`); 
         value.title=value.title.replace(reg, `<span class="keyword">$&</span>`);//进行替换，并定义高亮的样式
          
          }
 
      
    
  })
  var showlength;
  if (language=="en") {
  document.getElementById("countResult").innerText="The number of results found: "+dataLength;
  }
  if (language=="zh") {
  document.getElementById("countResult").innerText="为您找到约"+dataLength+"个结果";
  }

  var length=dataLength-10*a;
  
  if(length>10){
         showlength=10;
    }else{
      showlength=length;
    } 
     for (var i = 0; i < showlength; i++) {
       var x=10*a+i;
       document.getElementById("resultTitle"+i).innerHTML=data[x].title;
       document.getElementById("resultTitle"+i).href=data[x].url;
       document.getElementById("resultAbstract"+i).innerHTML=data[x].text.substr(0,200);
       if(data[x].dropped_terms.length>0){
        if (language=="en") {
         document.getElementById("dropTerms"+i).innerText="missing words: "+data[x].dropped_terms; 
      }
       if (language=="zh") {
       document.getElementById("dropTerms"+i).innerText="去掉的词是: "+data[x].dropped_terms; 
         }

       }
      if (language=="en") {
      document.getElementById("recommend"+i).innerText="View related entries>>>>>";
    }
    if (language=="zh") {
      document.getElementById("recommend"+i).innerText="查看相关词条>>>>>";
    }
      document.getElementById("docID"+i).innerText=data[x].id;
     }
     
}
function deleteData(b){
  var length=dataLength-10*b;
  var pageNow=b+1;
  var showlength;
  if(length>10){
         showlength=10;
    }else{
      showlength=length;
    } 
     for (var i = 0; i < showlength; i++) {
       var x=10*b+i;
       document.getElementById("resultTitle"+i).innerText="";
       document.getElementById("resultTitle"+i).href="";
       document.getElementById("resultAbstract"+i).innerText="";
        document.getElementById("dropTerms"+i).innerText=""; 
        document.getElementById("countResult").innerText=""; 
        document.getElementById("pageNowBtn").innerText="";
       document.getElementById("pageAllBtn").innerText="";  
       document.getElementById('recommendList'+i).innerHTML="";
       document.getElementById("recommend"+i).innerText="";  
     }
     document.getElementById('pageUp').style.visibility="hidden";
     document.getElementById('pageDown').style.visibility="hidden";

}
function pageKey(c,language){
      
      var pageNow=c+1;
      if(language=="zh"){
        document.getElementById("pageNowBtn").innerText="当前页："+pageNow;
        document.getElementById("pageAllBtn").innerText="总页数："+pageAll;
        document.getElementById("pageUp").innerText="上一页";
        document.getElementById("pageDown").innerText="下一页";
      }
      if(language=="en"){
        document.getElementById("pageNowBtn").innerText="Current Page："+pageNow;
        document.getElementById("pageAllBtn").innerText="Total pages："+pageAll;
        document.getElementById("pageUp").innerText="previous page";
        document.getElementById("pageDown").innerText="next page";
      }     
      if(pageNow==1){
        if(pageAll==1){
            document.getElementById('pageUp').style.visibility="hidden";
            document.getElementById('pageDown').style.visibility="hidden";
        }else{
            document.getElementById('pageDown').style.visibility="visible";
            document.getElementById('pageUp').style.visibility="hidden";
           }
      }else if(pageNow==pageAll){        
            document.getElementById('pageUp').style.visibility="visible";
            document.getElementById('pageDown').style.visibility="hidden";    
      }else {
        document.getElementById('pageUp').style.visibility="visible";
        document.getElementById('pageDown').style.visibility="visible";
      }

}
function pageRender(language){
   
  if (language=="en") {
    document.getElementById('searchBtnxWord').innerText="search";
    document.getElementById('searchTitle').innerText="Search Results";
    document.getElementById('tab').innerText="Special page";
    document.getElementById('mainPage').innerText="Main page";
    document.getElementById('mainPage').href="https://en.wikipedia.org/wiki/Main_Page";
    document.getElementById('contents').innerText="Contents";
    document.getElementById('contents').href="https://en.wikipedia.org/wiki/Wikipedia:Contents";
    document.getElementById('events').innerText="Current events";
    document.getElementById('events').href="https://en.wikipedia.org/wiki/Portal:Current_events";
    document.getElementById('about').innerText="About Wikipedia";
    document.getElementById('about').href="https://en.wikipedia.org/wiki/Wikipedia:About";
    
  }
  if (language=="zh") {
    document.getElementById('searchBtnxWord').innerText="搜索";
    document.getElementById('searchTitle').innerText="搜索结果";
    document.getElementById('tab').innerText="结果页";
    document.getElementById('mainPage').innerText="首页";
    document.getElementById('mainPage').href="https://zh.wikipedia.org/wiki/%E9%A6%96%E9%A1%B5";
    document.getElementById('contents').innerText="分类索引";
    document.getElementById('contents').href="https://zh.wikipedia.org/wiki/Wikipedia:%E5%88%86%E9%A1%9E%E7%B4%A2%E5%BC%95";
    document.getElementById('events').innerText="新闻动态";
    document.getElementById('events').href="https://zh.wikipedia.org/wiki/Portal:%E6%96%B0%E8%81%9E%E5%8B%95%E6%85%8B";
    document.getElementById('about').innerText="关于维基百科";
    document.getElementById('about').href="https://zh.wikipedia.org/wiki/Wikipedia:%E5%85%B3%E4%BA%8E";

  }

}


var $ = function (id) {
    return "string" == typeof id ? document.getElementById(id) : id;
}
  var Bind=function(object,fun){
    return function(){
      return fun.apply(object,arguments);
    }
  }
  function AutoComplete(obj,autoObj,arr,complete){
    this.obj=$(obj);
    this.autoObj=$(autoObj);
    this.value_arr=arr;
    this.index=-1;
    this.search_value="";

  }
  AutoComplete.prototype={
    init:function(){
        this.autoObj.style.left = this.obj.offsetLeft + "px";
        this.autoObj.style.top  = this.obj.offsetTop + this.obj.offsetHeight + "px";
        this.autoObj.style.width= this.obj.offsetWidth - 2 + "px";//减去边框的长度2px
    },
    deleteDIV:function(){
       while(this.autoObj.hasChildNodes()){
            this.autoObj.removeChild(this.autoObj.firstChild);
        }
        this.autoObj.className="auto_hidden";
    },
    setValue:function(_this){
       return function(){
            _this.obj.value=this.seq;
            _this.autoObj.className="auto_hidden";
        }      

    },
    autoOnmouseover:function(_this,_div_index){
      return function(){
            _this.index=_div_index;
            var length = _this.autoObj.children.length;
            for(var j=0;j<length;j++){
                if(j!=_this.index ){       
                    _this.autoObj.childNodes[j].className='auto_onmouseout';
                }else{
                    _this.autoObj.childNodes[j].className='auto_onmouseover';
                }
            }
        }
    },
    //更改classname
    changeClassname: function(length){
        for(var i=0;i<length;i++){
            if(i!=this.index ){       
                this.autoObj.childNodes[i].className='auto_onmouseout';
            }else{
                this.autoObj.childNodes[i].className='auto_onmouseover';
                this.obj.value=this.autoObj.childNodes[i].seq;
            }
        }
    },
    //响应键盘
    pressKey: function(event){
        var length = this.autoObj.children.length;
        //光标键"↓"
        if(event.keyCode==40){
            ++this.index;
            if(this.index>length){
                this.index=0;
            }else if(this.index==length){
                this.obj.value=this.search_value;
            }
            this.changeClassname(length);
        }
        //光标键"↑"
        else if(event.keyCode==38){
            this.index--;
            if(this.index<-1){
                this.index=length - 1;
            }else if(this.index==-1){
                this.obj.value=this.search_value;
            }
            this.changeClassname(length);
        }
        //回车键
        else if(event.keyCode==13){
            this.autoObj.className="auto_hidden";
            this.index=-1;
        }else{
            this.index=-1;
        }
    },
    //程序入口
    start: function(event){
        if(event.keyCode!=13&&event.keyCode!=38&&event.keyCode!=40){
            this.init();
            this.deleteDIV();
            this.search_value=this.obj.value;
            var valueArr=this.value_arr;
            valueArr.sort();
            if(this.obj.value.replace(/(^\s*)|(\s*$)/g,'')==""){ return; }//值为空，退出
            try{ var reg = new RegExp("(" + this.obj.value + ")","i");}
            catch (e){ return; }
            var reg1=new RegExp("[0-9]");
            var div_index=0;//记录创建的DIV的索引
            for(var i=0;i<valueArr.length;i++){
                if(!reg1.test(valueArr[i])&&valueArr[i]!=""){
                    var div = document.createElement("div");
                    div.className="auto_onmouseout";
                    div.seq=valueArr[i];
                    div.onclick=this.setValue(this);
                    div.onmouseover=this.autoOnmouseover(this,div_index);
                    div.innerHTML=valueArr[i].replace(reg,"<strong>$1</strong>");//搜索到的字符粗体显示
                    this.autoObj.appendChild(div);
                    this.autoObj.className="auto_show";
                    div_index++;
                }
          }
        }
        this.pressKey(event);
        window.onresize=Bind(this,function(){this.init();});
    }
}
//获取input框的历史记录
//设置localStorage
function setCookie(name, value) {
    localStorage.setItem(name, value);
}

//获取localStorage
function getCookie(count) {
     var inputHistory=[];
     for (var i = 0; i < count; i++) {
      var key=localStorage.getItem('inputHistory_'+i);
       inputHistory.push(key);
     }
     return inputHistory;
     
}
function unique(arr){
  return arr.filter(function(item, index, arr) {
    //当前元素，在原始数组中的第一个索引==当前索引值，否则返回当前元素
    return arr.indexOf(item, 0) === index;
  });
}

class Page extends Component{
  constructor(props,context){
    super(props,context);
    this.state={
      val: this.props.location.state.val,
      language:this.props.location.state.language,
      count:1
    }
   
  }
hideAuto=()=>{
    document.getElementById('auto').className="auto_hidden";
}
componentDidMount() {
    document.getElementById('inputformx').value=this.state.val;
    document.getElementById('languageboxResult').value=this.state.language;
    pageRender(this.state.language);
    getData(this.state.val,this.state.language);
    document.addEventListener('click', this.hideAuto);
}


handleClick=()=>{
    var queryTxt=document.getElementById('inputformx').value; 
    setCookie('inputHistory_'+ this.state.count,queryTxt);
    var countNow=this.state.count+1;
    this.setState({count:countNow});
    deleteData(0);
    var selectLanguageID=document.getElementById("languageboxResult")
    var index=selectLanguageID.selectedIndex; 
    var language=selectLanguageID.options[index].value;
    pageRender(language);
    document.getElementById("searching").style.display="block";
    getData(queryTxt,language);    
    
   
}
handlePageUpClick=()=>{
    deleteData(j);
    if(j>0) j=j-1;
    var queryTxt=document.getElementById('inputformx').value;
    var selectLanguageID=document.getElementById("languageboxResult")
    var index=selectLanguageID.selectedIndex; 
    var language=selectLanguageID.options[index].value;
    showData(j,queryTxt,language);
    pageKey(j,language);  
}
handlePageDownClick=()=>{
  deleteData(j);
  if(j< pageAll-1) j=j+1;
  var queryTxt=document.getElementById('inputformx').value;
  var selectLanguageID=document.getElementById("languageboxResult")
  var index=selectLanguageID.selectedIndex; 
  var language=selectLanguageID.options[index].value;
  showData(j,queryTxt,language);
  pageKey(j,language);     
}
handleKeyUp=(e)=>{
    var completeTxt=document.getElementById('inputformx').value;
    var selectLanguageID=document.getElementById("languageboxResult")
    var index=selectLanguageID.selectedIndex; 
    var selectedlanguage=selectLanguageID.options[index].value;
    let url="http://127.0.0.1:8000/complete_"+selectedlanguage+"?inputWord="+completeTxt;
    var searchData;
    var historyData=getCookie(this.state.count);
    var regHistory = new RegExp("(" + completeTxt + ")","i");
     axios.get(url).then(function (response) {
     searchData =response.data;
      }).then( ()=>{
     if(searchData != null){
       var dataComplete=[];      
       for (var key in searchData) {
            dataComplete.push(key);
       }
   }else{
        dataComplete=[];
   }  
   var dataCombine=dataComplete;
   for (var i = 0; i < historyData.length; i++) {
   if(regHistory.test(historyData[i])){
         dataCombine.push(historyData[i]);
       }
   }
   var dataUnique=unique(dataCombine);
  
   var autoComplete=new AutoComplete('inputformx','auto',dataUnique);
    autoComplete.start(e);
 }
   )
  
       
}
handleRecommend=(x)=>{
 var docIDtxt=document.getElementById("docID"+x).innerText;
 var docID=parseInt(docIDtxt);
 var completeTxt=document.getElementById('inputformx').value;
 var selectLanguageID=document.getElementById("languageboxResult")
 var index=selectLanguageID.selectedIndex; 
 var language=selectLanguageID.options[index].value;
 getRecommendList(docID,x,language);
  
}

  render(){
    return(
    <div>    
    <div className="pageLeft" id="pageLeft">
      <img src={Wikiresultlogo}/>
      <a href="" target='_blank' id="mainPage" className="entabWiki"></a>
      <a href="" target='_blank' id="contents" className="entabWiki"></a>
      <a href="" target='_blank' id="events"className="entabWiki"></a>
      <a href="" target='_blank' id="about" className="entabWiki"></a>
    </div>
    <p className="tab" id="tab"></p>
    <div className="tabTop">
    </div>
    <div className="searchResult">
    <p id="searchTitle"></p>
    </div>
    <div className="searchboxx"> 
       <div className="searchContainer">
       <input type="text" ref='input' className="inputformx" id="inputformx" autoComplete="off" onKeyUp={this.handleKeyUp}/> 
       <select name="language" id="languageboxResult" className="languageboxResult">       
         <option>en</option>
         <option>zh</option>
       </select> 
       <button className="searchBtnx" onClick={this.handleClick}>
          <p className="searchBtnxWord" id="searchBtnxWord"></p>
       </button>
       </div> 
       <div  className="auto_hidden" id="auto"></div>   
    </div>
    <div className="resultContainerAll">
    <img src={searching} className="searching" id="searching"/>
    <p className="countResult" id="countResult"></p>
    <div  className="resultContainer" id="resultContainer0">
    <p className='docID' id='docID0'></p>
    <a  id="resultTitle0" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract0" ></div>
    <p id='dropTerms0' className='dropTerms'></p>
    <button id="recommend0"className="recommend" onClick={this.handleRecommend.bind(this,0)}></button>
     <div className="recommendList" id="recommendList0"></div>
    </div>
    <div  className="resultContainer" id="resultContainer1">
    <p className='docID' id='docID1'></p>
    <a  id="resultTitle1" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract1"></div>
    <p id='dropTerms1' className='dropTerms'></p>
    <button id="recommend1"className="recommend" onClick={this.handleRecommend.bind(this,1)}></button>
    <div className="recommendList" id="recommendList1"></div>
    </div>
    <div  className="resultContainer" id="resultContainer2">
    <p className='docID' id='docID2'></p>
    <a  id="resultTitle2" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract2"></div>
    <p id='dropTerms2' className='dropTerms'></p>
    <button id="recommend2"className="recommend" onClick={this.handleRecommend.bind(this,2)}></button>
    <div className="recommendList" id="recommendList2"></div>
    </div>
    <div  className="resultContainer" id="resultContainer3">
    <p className='docID' id='docID3'></p>
    <a  id="resultTitle3" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract3"></div>
    <p id='dropTerms3' className='dropTerms'></p>
    <button id="recommend3"className="recommend" onClick={this.handleRecommend.bind(this,3)}></button>
    <div className="recommendList" id="recommendList3"></div>
    </div>
    <div  className="resultContainer" id="resultContainer4">
    <p className='docID' id='docID4'></p>
    <a  id="resultTitle4" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract4"></div>
    <p id='dropTerms4' className='dropTerms'></p>
    <button id="recommend4"className="recommend" onClick={this.handleRecommend.bind(this,4)}></button>
    <div className="recommendList" id="recommendList4"></div>
    </div>
    <div  className="resultContainer" id="resultContainer5">
    <p className='docID' id='docID5'></p>
    <a  id="resultTitle5" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract5"></div>
    <p id='dropTerms5' className='dropTerms'></p>
    <button id="recommend5"className="recommend" onClick={this.handleRecommend.bind(this,5)}></button>
    <div className="recommendList" id="recommendList5"></div>
    </div>
    <div  className="resultContainer" id="resultContainer6">
    <p className='docID' id='docID6'></p>
    <a  id="resultTitle6" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract6" ></div>
    <p id='dropTerms6' className='dropTerms'></p>
    <button id="recommend6"className="recommend"  onClick={this.handleRecommend.bind(this,6)}></button>
    <div className="recommendList" id="recommendList6"></div>
    </div>
    <div  className="resultContainer" id="resultContainer7">
    <p className='docID' id='docID7'></p>
    <a  id="resultTitle7" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract7"></div>
    <p id='dropTerms7' className='dropTerms'></p>
    <button id="recommend7"className="recommend" onClick={this.handleRecommend.bind(this,7)}></button>
    <div className="recommendList" id="recommendList7"></div>
    </div>
    <div  className="resultContainer" id="resultContainer8">
    <p className='docID' id='docID8'></p>
    <a  id="resultTitle8" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract8"></div>
    <p id='dropTerms8' className='dropTerms'></p>
    <button id="recommend8"className="recommend" onClick={this.handleRecommend.bind(this,8)}></button>
    <div className="recommendList" id="recommendList8"></div>
    </div>
    <div  className="resultContainer" id="resultContainer9">
    <p className='docID' id='docID9'></p>
    <a  id="resultTitle9" target='_blank' className="resultTitle"></a>
    <p className="autoShowRedirect">Redriect from</p>
    <div className="resultAbstract" id="resultAbstract9"></div>
    <p id='dropTerms9' className='dropTerms'></p>
    <button id="recommend9"className="recommend" onClick={this.handleRecommend.bind(this,9)}></button>
    <div className="recommendList" id="recommendList9"></div>
    </div>
    <div className="pgeBtn">
      <button id="pageUp" style={{visibility:'hidden'}} className="pageKeyBtn" onClick={this.handlePageUpClick}></button>
      <a id="pageNowBtn" className="pageNowBtn"></a>
      <button id="pageDown" style={{visibility:'hidden'}} className="pageKeyBtn" onClick={this.handlePageDownClick}></button>
      <a id="pageAllBtn" className="pageAllBtn"></a>
    </div>
    </div>
    </div>
    )
  }
}

export default Page;
