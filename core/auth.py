from werkzeug.security import check_password_hash, generate_password_hash
# core/auth.py                                                                                                                                                                           
  # Password hashing and verification using Werkzeug's pbkdf2:sha256 implementation.                                                                                                       
  # Passwords are never stored in plain text — only the hash is saved to the database.                                                                                                     
  #                                                                                                                                                                                        
  # hash_password()   — call when creating or updating a user's password                                                                                                                   
  # verify_password() — call at login to check submitted password against stored hash                                                                                                      
  # Werkzeug automatically handles salting, so two identical passwords produce different hashes.
def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)
