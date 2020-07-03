import React, {Component} from 'react';
import Page from'./Page';
import SearchCom from './search';
import {HashRouter, Route, Switch} from 'react-router-dom';


const BasicRoute = () => (
    <HashRouter>
        <Switch>
            <Route exact path="/search" component={SearchCom}/>
            <Route exact path="/page" component={Page}/>
        </Switch>
    </HashRouter>
);


export default BasicRoute;