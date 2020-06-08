
import { useState, useEffect } from "react";

export const useForm = (callback, validate) => {
  const [values, setValues] = useState({ username: "", email: "", comment: "" });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = event => {
    const { name, value } = event.target;
    setValues({
      ...values,
      [name]: value
    });
  };

  const handleSubmit = event => {
    console.log("handle Submit")
    event.preventDefault();
    setErrors(validate(values));
    setIsSubmitting(true);
  };

  useEffect(() => {
    if (Object.keys(errors).length === 0 && isSubmitting) {
      setIsSubmitting(false)
      callback();
    }
  }, [errors]);

  return {
    handleChange,
    handleSubmit,
    setErrors,
    values,
    errors
  };
};
