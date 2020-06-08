/* This is equivalent to Feedbackform.js but written in class syntax
 */

import React, { Component } from "react";
import { useFeedbackform } from "./usefeedbackform_delete";

const intro_msg = "Not on GitHub? Use the form below to leave us a message. \
 Your comment will be automatically posted on our public Github Page (but not your contact data)."
 const submit_err_msg = "Something went wrong. Please try again later."
const placeholder = "This message will be publicly visible on our GitHub Page."
const url = "https://api.github.com/repos/GitMatze/githubAPI/issues/6/comments"
const token = `Token bef496f37e2f34878f374b349ce8ce0a3d47e057`

const emailRegex = RegExp(
  /^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/
);

const formValid = ({ formErrors, comment }) => {
  let valid = true;

  // validate form errors being empty
  Object.values(formErrors).forEach(val => {
    val.length > 0 && (valid = false);
  });
  
  // validate comment being filled
  comment == null && (valid = false)

  return valid;
};

class Feedbackform extends Component {
  constructor(props) {
    super(props);

    this.state = {
      username: null,
      email: null,
      comment: null,
      formErrors: {
        username: "",
        email: "",
        comment: ""
      },
      submitError: "" ,
      comment_url: "",
      success: false     
    };
  }

  handleSubmit = async(e) => {
    e.preventDefault();

    if (formValid(this.state)) {     
      const result = await this.createComment();
      console.log(result)
      if (result.body == this.state.comment) {
        this.setState({comment_url : result.html_url})
        this.setState( {success: true})
      } else {
        this.setState({submitError : submit_err_msg})        
      }
    }
  };

  handleChange = e => {
    e.preventDefault();
    const { name, value } = e.target;
    let formErrors = { ...this.state.formErrors };

    switch (name) {
      case "username":
        formErrors.username =
          value.length < 0 ? "minimum 3 characaters required" : "";
        break;      
      case "email":
        formErrors.email = emailRegex.test(value)
          ? ""
          : "invalid email address";
        break;
      case "comment":
        formErrors.comment =
          value.length < 20 ? "minimum 20 characaters required" : "";
        break;
      default:
        break;
    }

    this.setState({ formErrors, [name]: value }, () => console.log(this.state));
  };

  async createComment() {

    this.state.submitError = ""
        
    const headers = {
        "Authorization" : token
    }

    const payLoad = {
        body: this.state.comment
    }

    try {
      const response = await fetch(url, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(payLoad)
      })
      const result = await response.json()

      return result

    } catch(error) {
      return None
    }      
  }

  render() {
    const { formErrors } = this.state;

    return (
      <div className="wrapper">
        <p>{intro_msg}  </p> 
        {!this.state.success && (<div  className="form-wrapper">   
          <form onSubmit={this.handleSubmit} noValidate>
            <div className="username">
              <label htmlFor="username">Your Name</label>
              <input
                className={formErrors.username.length > 0 ? "error" : null}
                placeholder="optional"
                type="text"
                name="username"
                noValidate
                onChange={this.handleChange}
              />
              {formErrors.username.length > 0 && (
                <span className="errorMessage">{formErrors.username}</span>
              )}
            </div>          
            <div className="email">
              <label htmlFor="email">Email</label>
              <input
                className={formErrors.email.length > 0 ? "error" : null}
                placeholder="optional"
                type="email"
                name="email"
                noValidate
                onChange={this.handleChange}
              />
              {formErrors.email.length > 0 && (
                <span className="errorMessage">{formErrors.email}</span>
              )}
            </div>
            <div className="comment">
              <label htmlFor="comment">Your comment</label>
              <textarea
                className={formErrors.comment.length > 0 ? "error" : null}
                placeholder="Please enter your comment"
                type="text"
                name="comment"
                rows="6"
                noValidate
                onChange={this.handleChange}
              />
              {formErrors.comment.length > 0 && (
                <span className="errorMessage">{formErrors.comment}</span>
              )}
            </div>
            <div className="submit">
              <button type="submit">Submit</button>
              {this.state.submitError.length > 0 && (
                <span className="errorMessage">{this.state.submitError}</span>)}
            </div>
          </form>          
        </div>) }
        {this.state.success && ( <div className="success">
            <h1>Thank you.</h1>
            <p>You can follow the discussion <a href={this.state.comment_url} target="_blank">here</a>.
            </p>
        </div>)}
      </div>
    );
  }
}

export default Feedbackform;