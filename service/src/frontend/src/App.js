import React, { Component } from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Redirect,
  Link
} from "react-router-dom";
import './App.css';

import Assignment from './Assignment.js';
import Class from './Class.js';
import Classes from './Classes.js';
import Header from './Header.js';

class App extends Component {

  constructor(props) {
    super(props);
    this.state = {
      token: null,
      id: null,
    };
  }

	render () {
    const token = this.state.token;
    const backend = 'REACT_APP_BACKEND_URL' in process.env ? process.env.REACT_APP_BACKEND_URL : window.location.origin;
    
    function PrivateRoute({ children, ...rest}) {
      return (<Route
        {...rest}
        render={({ location }) =>
                token ? (
                  children
                ) : (
                  <Redirect
                    to={{
                      pathname: "/",
                      state: { from: location }
                    }}
                  />
                )
               }
              />
             );
    }

    return (
      <Router>
        <div className="App">
          <Header
            token={this.state.token}
            setToken={(token, id) => this.setState({ token: token,
                                                     id: id,
                                                   })}
            backend={backend}
          />
        </div>
        <Switch>
          <PrivateRoute path="/class/:classId">
            <Class
              token={this.state.token}
              backend={backend}
            />
          </PrivateRoute>
          <PrivateRoute path="/assignment/:assignmentId">
            <Assignment
              token={this.state.token}
              id={this.state.id}
              backend={backend}
            />
          </PrivateRoute>
          <Route path="/">
            {this.state.token ?
             <Classes
               token={this.state.token}
               backend={backend}
             /> :
             "Hello and welcome to OOOnline Course, your cooourse to success!"
            }
          </Route>
        </Switch>
      </Router>
    );
  }
}

export default App;
