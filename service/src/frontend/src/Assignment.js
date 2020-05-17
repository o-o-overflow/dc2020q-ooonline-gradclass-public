import React, { Component } from 'react';
import { Link, useParams } from "react-router-dom";
import PropTypes from "prop-types";
import { withRouter } from "react-router";

import ReactMarkdown from "react-markdown";

import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import Input from "@material-ui/core/Input";

class Assignment extends Component {

  constructor(props) {
    super(props);
    this.state = {
      submissions: [],
      submission_results: {},
      text: "",
      assignment_name: "",
      class_name: "",
      uploadDialog: false,
      filename: "No file",
      file_contents: null,
    };
    this.assignment_id = this.props.match.params.assignmentId;
    this.id = props.id;
    this.backend = props.backend;
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  updateAssignment()
  {
    fetch(`${this.backend}/assignment/${this.assignment_id}`,
          { method: 'GET',
            headers: {
              'X-Auth-Token': this.props.token,
            },
          })
      .then(response =>
            response.json().then(body => ({ body, status: response.status }))
           )
      .then(({ body, status }) => {
        if (status !== 200) {
          console.log(status);
          return;
        }
        this.setState({text: body.text,
                       assignment_name: body.name,
                      });
        const class_id = body.class_id;
        fetch(`${this.backend}/classes`,
              { method: 'GET',
                headers: {
                  'X-Auth-Token': this.props.token,
                },
              })
          .then(response =>
                response.json().then(body => ({ body, status: response.status }))
               )
          .then(({ body, status }) => {
            if (status !== 200) {
              console.log(status);
              return;
            }
            body.forEach((c) => {
              if (c.id === class_id)
              {
                this.setState({class_name: c.name});
              }
            });
          });
      });
  }

  updateSubmissions()
  {
    fetch(`${this.backend}/assignment/${this.assignment_id}/submissions`,
          { method: 'GET',
            headers: {
              'X-Auth-Token': this.props.token,
            },
          })
      .then(response =>
            response.json().then(body => ({ body, status: response.status }))
           )
      .then(({ body, status }) => {
        if (status !== 200) {
          console.log(status);
          return;
        }
        this.setState({submissions: body});
        body.forEach((s) => {
          fetch(`${this.backend}/submission/${s.id}/result`,
                { method: 'GET',
                  headers: {
                    'X-Auth-Token': this.props.token,
                  },
                })
            .then(response =>
                  response.json().then(body => ({ body, status: response.status }))
                 )
            .then(({ body, status }) => {
              if (status !== 200) {
                console.log(status);
                return;
              }
              this.setState({submission_results: {...this.state.submission_results, [s.id]: body.message}});
            });
        });
      });
  }
    
  componentDidMount()
  {
    this.updateAssignment();
    this.updateSubmissions();
    this.interval = setInterval(() => this.updateSubmissions(), 10000);
  }

	render () {

    const submission_list = this.state.submissions.map((s) => {
      return <li><a href="#" onClick={() => {
        fetch(`${this.backend}/submission/${s.id}`,
              { method: 'GET',
                headers: {
                  'X-Auth-Token': this.props.token,
                }
              })
          .then(response =>
                response.json().then(body => ({ body, status: response.status }))
               )
          .then(({ body, status }) => {
            if (status !== 200) {
              console.log(status);
              return;
            }
            alert(body.filename);
          });
      }}>Submission id</a> {s.id}: {s.id in this.state.submission_results ? this.state.submission_results[s.id] : "..."}</li>;
    });

    return (<div>
              <h1>Assignment {this.state.assignment_name} for class {this.state.class_name}</h1>
              <p>
                <ReactMarkdown source={this.state.text} />
              </p>
              <h2>Your Submissions</h2>
              <ul>
                {submission_list}
              </ul>
              <Button variant="contained" onClick={() => this.setState({uploadDialog: true})}>Add Submission</Button>
              {this.props.id === 1 ?
               <Button variant="contained" onClick={() => {
                 fetch(`${this.backend}/assignment/${this.assignment_id}/admin`,
                       { method: 'GET',
                         headers: {
                           'X-Auth-Token': this.props.token,
                         },
                       })
                   .then(response =>
                         response.json().then(body => ({ body, status: response.status }))
                        )
                   .then(({ body, status }) => {
                     if (status !== 200) {
                       console.log(status);
                       return;
                     }
                     alert(body.grading_binary);
                   });
                 
               }}>Admin Debug</Button>
               : null}
              <Dialog open={this.state.uploadDialog}
                      onClose={() => this.setState({uploadDialog: false})}
                      aria-labelledby="Upload Submission"
              >
                <DialogTitle>Upload Submission</DialogTitle>
                <DialogContent>                  
                  <Button variant="outlined" color="primary" component="label">
                    Choose File
                    <input type="file" style={{display: "none"}} onChange={(e) => {
                      const reader = new FileReader();
                      const file = e.target.files[0];
                      reader.onloadend = (theFile) => {
                        this.setState({filename: file.name,
                                       file_contents: theFile.target.result});
                      };
                      reader.readAsBinaryString(file);
                      e.preventDefault();
                    }}/>
                  </Button>
                  <Input disabled disableUnderline value={this.state.filename}></Input>
                </DialogContent>
                <DialogActions>
                  <Button onClick={() => this.setState({uploadDialog: false})} color="primary">
                    Cancel
                  </Button>
                  <Button disabled={this.state.file_contents === null} onClick={() => {
                    fetch(`${this.backend}/assignment/${this.assignment_id}/submissions`,
                          { method: 'POST',
                            headers: {
                              'X-Auth-Token': this.props.token,
                              'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({file: this.state.file_contents}),
                          })
                      .then(response =>
                            response.json().then(body => ({ body, status: response.status }))
                           )
                      .then(({ body, status }) => {
                        if (status !== 200) {
                          console.log(status);
                          return;
                        }
                        this.updateSubmissions();
                      });
                    
                    this.setState({filename: "No file",
                                   file_contents: null,
                                   uploadDialog: false});
                  }} color="primary">
                    Upload
                  </Button>
                </DialogActions>
              </Dialog>
            </div>);
  }

}

Assignment.propTypes = {
  token: PropTypes.string,
  id: PropTypes.string,
  backend: PropTypes.string,
};


export default withRouter(Assignment);
