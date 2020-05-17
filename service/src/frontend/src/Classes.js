import React from 'react';
import { Link, useParams } from "react-router-dom";
import PropTypes from "prop-types";

export default function Classes (props) {

  const [classes, setClasses] = React.useState([]);

  fetch(`${props.backend}/classes`,
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
      if (JSON.stringify(body) != JSON.stringify(classes))
      {
        setClasses(body);
      }
    });

  const class_list = classes.map((c) => {
    return <li><Link to={`/class/${c.id}`}>{!c.open ? "🔒" : ""}{c.name}</Link></li>;
  });

  return <div>
           <h1>Available classes</h1>
           <ul>
             {class_list}
           </ul>
         </div>;
}

Classes.propTypes = {
  token: PropTypes.string,
  backend: PropTypes.string,
};
