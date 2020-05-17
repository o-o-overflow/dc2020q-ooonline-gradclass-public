import React from 'react';
import { Link, useParams } from "react-router-dom";
import PropTypes from "prop-types";

export default function Class (props) {
  const [assignments, setAssignments] = React.useState([]);
  const { classId } = useParams();

  fetch(`${props.backend}/class/${classId}/assignments`,
                     { method: 'GET',
                       headers: {
                         'X-Auth-Token': props.token,
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
      if (JSON.stringify(body) != JSON.stringify(assignments))
      {
        setAssignments(body);
      }
    });

  const assignment_list = assignments.map((a, idx) => {
    return <li><Link to={`/assignment/${a.id}`}>{`Assignment ${idx+1}`}</Link></li>;
  });

  return <div>
           <h1>Assignments</h1>
           <ul>
             {assignment_list}
           </ul>
         </div>;
  
}

Class.propTypes = {
  token: PropTypes.string,
  backend: PropTypes.string,
};


