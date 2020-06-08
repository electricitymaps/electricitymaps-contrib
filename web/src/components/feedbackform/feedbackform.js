import React, { useState } from "react";
import { useForm } from "./useFeedbackform";

const Feedbackform = () => {
  const { handleChange, handleSubmit, setErrors, values, errors } = useForm(
    submit,
    validate
  );
  const [success, setSuccess] = useState(false)
  const [comment_url, setComment_url] = useState("")

  
  const intro_msg = "Not on GitHub? Use the form below to leave us a message. \
    Your comment will be automatically posted on our public Github Page (but not your contact data)."
  const token = `Token bef496f37e2f34878f374b349ce8ce0a3d000000`   // Token is not valid! Replace with valid one.
  const url = "https://api.github.com/repos/GitMatze/githubAPI/issues/6/comments"  

  const emailRegex = RegExp(
    /^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/
  );

  function validate(values) {
    let errors = {}
    
    if (values.email && !emailRegex.test(values.email)) {
      errors.email = "invalid email address" 
    }
    if (values.comment.length < 20) {
      errors.comment = "minimum 20 characaters required"
    }

    return errors
  }

  async function submit() {
    const result = await createComment();
    console.log(result)
    if (result.html_url) {
      setComment_url(result.html_url)
      setSuccess(true)
    } else {
      errors.submit="Something went wrong. Please try again later."
      setErrors(errors) // TODO: submit error does not render
    }     
  }
 

  const createComment = async() => {

    const headers = {
        "Authorization" : token
    }

    const payLoad = {
        body: values.comment
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

  return (
        <div className="wrapper">
        <p> {intro_msg} </p> 
        {!success && (<div  className="form-wrapper">   
            <form onSubmit={handleSubmit}noValidate>
            <div className="username">
                <label htmlFor="username">Your Name</label>
                <input
                // className={formErrors.username.length > 0 ? "error" : null}
                placeholder="optional"
                type="text"
                name="username"
                noValidate
                onChange={handleChange}
                />
                {/* {formErrors.username.length > 0 && (
                <span className="errorMessage">{formErrors.username}</span>
                )} */}
            </div>          
            <div className="email">
                <label htmlFor="email">Email</label>
                <input
                className={errors.email ? "error" : null}
                placeholder="optional"
                type="email"
                name="email"
                noValidate
                onChange={handleChange}
                />
                {errors.email && (
                <span className="errorMessage">{errors.email}</span>
                )}
            </div>
            <div className="comment">
                <label htmlFor="comment">Your comment</label>
                <textarea
                className={errors.comment ? "error" : null}
                placeholder="Please enter your comment"
                type="text"
                name="comment"
                rows="6"
                maxLength="1000"
                noValidate
                onChange={handleChange}
                />
                <div className="counterbox">
                {errors.comment && (
                <span className="errorMessage">{errors.comment}</span>
                )}
                <span className="counter">{values.comment.length+"/1000"}</span>
                </div>
            </div>
            <div className="submit">
                <button type="submit">Submit</button>
                {errors.submit && (
                <span className="errorMessage">{errors.submit}</span>)}
            </div>
            </form>          
        </div>) }
        {success && ( <div className="success">
            <h1>Thank you.</h1>
            <p>You can follow the discussion <a href={comment_url} target="_blank">here</a>.</p>
        </div>)}
        </div>
    );
    
};

export default Feedbackform;