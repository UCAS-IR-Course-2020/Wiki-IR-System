import React,{Component} from 'react';
import ReactDOM from 'react-dom';
import './search.css';
import { History } from 'react-router';
import search from './search.svg';
import Wikipedialogo from './Wikipedia-logo.png';
import Wikipediaword from './Wikipedia-word.png';

import axios from 'axios' ;
 
var $ = function (id) {
    return "string" == typeof id ? document.getElementById(id) : id;
}
  var Bind=function(object,fun){
  	return function(){
  		return fun.apply(object,arguments);
  	}
  }
  function AutoComplete(obj,autoObj,arr){
  	this.obj=$(obj);
  	this.autoObj=$(autoObj);
  	this.value_arr=arr;
  	this.index=-1;
  	this.search_value="";

  }
  AutoComplete.prototype={
  	init:function(){
      if(this.obj!=null){
  		  this.autoObj.style.left = this.obj.offsetLeft + "px";
        this.autoObj.style.top  = this.obj.offsetTop + this.obj.offsetHeight + "px";
        this.autoObj.style.width= this.obj.offsetWidth - 2 + "px";//减去边框的长度2px
        }
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
            var div_index=0;//记录创建的DIV的索引
            for(var i=0;i<valueArr.length;i++){
                if(reg.test(valueArr[i])){
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
        window.onresize=Bind(this,function(){this.init();});
    }
}
function setCookie(name, value) {
    localStorage.setItem(name, value);
}
 
export default class SearchCom extends Component{
  constructor(){
  	super();
  	this.state={
  		val:"",
      language:""
  	}
  }

  handleKeyUp=(e)=>{
  	var completeTxt=document.getElementById('inputform').value;
    var selectLanguageID=document.getElementById("select")
    var index=selectLanguageID.selectedIndex ; 
    var selectedlanguage=selectLanguageID.options[index].value;
    let url="http://127.0.0.1:8000/complete_"+selectedlanguage+"?inputWord="+completeTxt;
    var searchData;
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
   var autoComplete=new AutoComplete('inputform','auto',dataComplete);
    autoComplete.start(e);
 }
   )


}
handleClick=()=>{
  var data;
  var queryText=document.getElementById("inputform").value;
  setCookie('inputHistory_0',queryText);
  var selectLanguageID=document.getElementById("select")
  var index=selectLanguageID.selectedIndex ; 
  var selectedlanguage=selectLanguageID.options[index].text;
  this.props.history.push({pathname:'/page',state:{val:queryText,language:selectedlanguage}});
  

}

  render(){
  	return(
  <div>
    <div className="Wikiword">
       <img src={Wikipediaword}  alt="word" />
    </div>
  	<div className="Wikilogo">
  	   <img src={Wikipedialogo}  alt="logo" />
  	</div>
  	<div className="searchbox">
       <input type="text" ref='input' className="inputform" autoComplete="off" id="inputform" onKeyUp={this.handleKeyUp}/>
       <select name="language" id="select" className="languagebox">       
         <option>en</option>
         <option>zh</option>
       </select>      
       <button className="searchBtn" onClick={this.handleClick}>
          <img src={search}  alt="search" className="searchlogo" />
       </button>
       
  	</div>
  	<div  className="auto_hidden" id="auto"></div>
  </div>
  	)
  }
}


/*ReactDOM.render(
  <React.StrictMode>
    <SearchCom />
  </React.StrictMode>,
  document.getElementById('root')
);*/



