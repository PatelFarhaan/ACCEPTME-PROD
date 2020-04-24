// Contains validations for the login, signup and forgot password forms

function validateLogin(){

    var userLoginEmail = document.forms["loginForm"]["userEmailID"].value;
    var userLoginPassword = document.forms["loginForm"]["userLoginPassword"].value;

 
    if (userLoginEmail == "" || userLoginEmail== null, userLoginPassword == "" || userLoginPassword== null) {
        document.getElementsByName('userEmailID')[0].placeholder='Please enter a valid Username';
        
        document.getElementsByName('userLoginPassword')[0].placeholder='Please enter a valid Password';
         
        
        return false;       
 

    }
// else if(){

// }
}

function validate_verification_code() {
    var verification_code = document.forms["2fa_form"]["verificationCode"].value;
    var reg = /^\d{6}$/;
    verification_code = verification_code.replace(" ", "");
    var patt = new RegExp(reg);
    return patt.test(verification_code)
}

function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
  }
  
  function validate() {
    var $result = $("#result");
    var email = $("#email").val();
    $result.text("");
  
    if (validateEmail(email)) {
      $result.text(email + " is valid :)");
      $result.css("color", "green");
    } else {
      $result.text(email + " is not valid :(");
      $result.css("color", "red");
    }
    return false;
  }
  
  $("#validate").bind("click", validate);