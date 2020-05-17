import React from 'react';
import { Link } from "react-router-dom";
import PropTypes from "prop-types";

import Modal from '@material-ui/core/Modal';

export default function Header (props) {
  const isLoggedIn = props.token;

  const [openLogin, setOpenLogin] = React.useState(false);
  const [openRegister, setOpenRegister] = React.useState(false);

  const loginName = React.createRef();
  const loginPassword = React.createRef();

  const registerName = React.createRef();

  return <header>
           <h1>OOOnline Course</h1>
           {isLoggedIn ?
            <a href="#" onClick={() => props.setToken(null)}>Log out</a>
            : (<div>
                 <a href="#" onClick={() => setOpenRegister(true)}>Register</a>
                 <br />
                 <a href="#" onClick={() => setOpenLogin(true)}>Login</a>
               </div>)}
           <Modal
             open={openRegister}
             onClose={() => setOpenRegister(false)}
             aria-labelledby="register"
           >
             <form onSubmit={(event) => {
               const username = registerName.current.value;
               fetch(`${props.backend}/user/register`,
                     { method: 'POST',
                       headers: {
                         'Content-Type': 'application/json',
                       },
                       body: JSON.stringify({name: username}),
                     })
                 .then(response =>
                       response.json().then(body => ({ body, status: response.status }))
                      )
                 .then(({ body, status }) => {
                   if (status !== 200) {
                     console.log(status);
                     return;
                   }
                   if ("id" in body)
                   {
                     alert(`Password created for ${body['returning_from_db_name']}: ${body['password']}`);
                   }
                   else
                   {
                     alert('Failed');
                   }
                   setOpenRegister(false);
                 });
             }}>
               <label>username</label>
               <input type="text" ref={registerName}/>
               <input type="submit" value="Register"/>
             </form>
           </Modal>
           <Modal
             open={openLogin}
             onClose={() => setOpenLogin(false)}
             aria-labelledby="login"
           >
             <form onSubmit={(event) => {
               const username = loginName.current.value;
               const password = loginPassword.current.value;
               fetch(`${props.backend}/user/login`,
                     { method: 'POST',
                       headers: {
                         'Content-Type': 'application/json',
                       },
                       body: JSON.stringify({name: username,
                                             passwd: password}),
                     })
                 .then(response =>
                       response.json().then(body => ({ body, status: response.status }))
                      )
                 .then(({ body, status }) => {
                   if (status !== 200) {
                     console.log(status);
                     return;
                   }
                   alert(body.message);
                   if ("token" in body)
                   {
                     props.setToken(body.token, body.id);
                   }
                   setOpenLogin(false);
                 });
               event.preventDefault();
             }}>
               <label>username</label>
               <input type="text" ref={loginName} />
               <label>password</label>
               <input type="password" ref={loginPassword}/>
               <input type="submit" value="Login"/>
             </form>
           </Modal>
         </header>;
}

Header.propTypes = {
  token: PropTypes.string,
  backend: PropTypes.string,
  setToken: PropTypes.func,
};
